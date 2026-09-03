#!/usr/bin/env python3
"""r4h — a Shizuku start holds USB debugging instead of wireless debugging.

The author:

    "also when shizuku toggle is turned on in settings manager no need to block access to
     wireless debugging settings, instead block usb debugging toggle until shizuku starts"

r4b held wireless debugging for the length of a Thedjchi start, on his instruction at the time.
This swaps that hold to USB debugging, which makes the two forks the same shape: **whichever fork
is starting, USB debugging is held and wireless debugging is free.**

⚠ **The hold moves; it does not multiply.** One row is held per start, and the two branches of
`usableOf` that name it — `heldBySheveryWait` for the forty-second wait, `heldByServiceStart` for
Thedjchi's — now name the same target for different reasons and different durations. Kept as two
tests rather than merged into one, because they *are* two things: the Shevery wait also holds the
service row itself and shows a countdown, and Thedjchi's does neither.

⚠ **The wireless restore after a Thedjchi start is deliberately left alone.** The author asked
about *blocking*, not about putting the row back, and `settleWirelessAfterStart` still runs on
that path in both directions. That is now the one asymmetry left between the forks — Shevery
raises wireless only if it was on, from a latch, while Thedjchi drives it either way from a value
read at the press. Flagged rather than changed: it is a behaviour question, not a consequence of
this one.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

OLD = """                // Either fork. The start is about to move this row itself; a press here would
                // race a write the user cannot see.
                val heldByServiceStart = serviceStarting &&
                    target == ManualRevertTarget.WirelessDebugging
"""

NEW = """                // ⚠ **USB debugging, not wireless debugging** — the author reversed r4b's
                // choice: *"when shizuku toggle is turned on in settings manager no need to
                // block access to wireless debugging settings, instead block usb debugging
                // toggle until shizuku starts"*. Both forks now hold the same row while a
                // start is in flight, which is also the transport the start actually depends
                // on: switching it off mid-start would undo the thing being waited for.
                //
                // Separate from [heldBySheveryWait] above even though they now name the same
                // target, because they are two different things: that one runs for forty
                // seconds, shows a countdown, and holds the service row as well.
                val heldByServiceStart = serviceStarting &&
                    target == ManualRevertTarget.UsbDebugging
"""

DOC_OLD = """    /**
     * Whether a fork start begun from this dialog is in flight, on either fork.
     *
     * Holds the wireless debugging row for the whole of it: a start brings the debugging
     * transport up with it, so that row is about to be written by something other than the
     * user. Separate from [sheveryWait], which also holds **USB** debugging and only exists on
     * Shevery.
     */
    serviceStarting: Boolean = false,
"""

DOC_NEW = """    /**
     * Whether a fork start begun from this dialog is in flight.
     *
     * Holds the **USB debugging** row for the whole of it, at the author's instruction: that is
     * the transport the start depends on, so switching it off mid-start would undo the thing
     * being waited for. Wireless debugging is free throughout — r4b held that one instead, and
     * he reversed it.
     *
     * Separate from [sheveryWait], which holds the same row but for forty seconds, with a
     * countdown, and holds the service row with it.
     */
    serviceStarting: Boolean = false,
"""


def main() -> int:
    path = ROOT / MANAGER

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in ((OLD, NEW, 1), (DOC_OLD, DOC_NEW, 1)):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # ⚠ Asserted against code, never the prose around it: both hold tests now name USB
    # debugging, and nothing in `usableOf` holds wireless debugging any more.
    for token, expected in (
        ("val heldByServiceStart = serviceStarting &&\n                    "
         "target == ManualRevertTarget.UsbDebugging", 1),
        ("val heldBySheveryWait = sheveryWait != null &&", 1),
        ("!heldByServiceStart &&", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token.splitlines()[0][:58]!r}, "
                            f"found {text.count(token)}")

    # The hold block must sit inside `usableOf`, above the expression that reads it.
    usable = text.find("            val usableOf = { target: ManualRevertTarget ->")
    held = text.find("                val heldByServiceStart = serviceStarting")
    reads = text.find("                    !heldByServiceStart &&")

    if usable < 0 or held < 0 or reads < 0:
        problems.append("cannot locate usableOf, the hold, or the test that reads it")
    elif not usable < held < reads:
        problems.append("the hold is not declared inside usableOf before it is read")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  wrote {MANAGER}")
    print("ok - a start holds USB debugging on either fork, and wireless debugging is free")

    return 0


if __name__ == "__main__":
    sys.exit(main())
