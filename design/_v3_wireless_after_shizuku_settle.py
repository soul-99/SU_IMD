#!/usr/bin/env python3
"""r4h — a revert writes wireless debugging again after the Shizuku step, not before it.

The author:

    "for every unhide/restore in whole imd restore wireless debugging after shizuku service
     either have started successfully or failed to start as shizuku service if successfully
     starts turns off wireless dubugging which makes the imd set value flase"

This is the r4b leftover — *"wireless debugging settled after every Shizuku start, as per the
unhiding mechanism"* — and it turns out to be one place, not six.

### Where the gap actually is

A revert already knows a fork start moves the debugging transport, and orders itself around it.
The **overlay** step starts Shizuku first, and the ordinary loop writes dev/usb/wifi/a11y
afterwards for exactly that reason; its comment says so. `RevertAppSettingsUseCase` does the same
— overlay first, settings after.

But the revert ends by settling Shizuku, **after** that loop, and that step can start the service
too. A start there switches wireless debugging off underneath a value written seconds earlier,
and nothing runs after it. The author's logs show the shape: `changed=[DeveloperSettings,
UsbDebugging]`, `unchanged=[WirelessDebugging]`, and the device left with `wifi=off`.

### The fix

One re-settle, immediately after the Shizuku block: read the device again and write wireless
debugging to its destination if the two now disagree.

⚠ **Only when this step actually attempted a start.** A settle that stopped Shizuku, or left it
alone, or was skipped because the fork had already refused, has moved nothing — and a revert
should not do a read and a write per run for a case that cannot arise. The one branch that
attempts a start sets the flag.

⚠ **Attempted, not succeeded** — the author's *"either have started successfully or failed to
start"*. A fork that writes the transport on its way up and then dies has still switched wireless
debugging off, and the value IMD wrote is just as wrong as if it had come up.

⚠ **Nothing to do on the other paths.** The overlay start is already followed by the ordinary
loop, and the per-app revert already writes its settings after its own start. This is the only
start in the codebase with no write behind it.

⚠ **The accounting is redone, not appended to.** Wireless debugging has already been recorded by
the loop; a second write to the same destination must not leave it in two sets at once, so the
result is recomputed against `initial` exactly as the loop does — which is also what makes the
report honest, since the user asked for one state and got it, whatever the fork did in between.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USE_CASE = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
            "RevertToDefaultUseCase.kt")

FLAG_OLD = """        var shizukuStartRefused = false
"""

FLAG_NEW = """        var shizukuStartRefused = false

        /**
         * Whether the final Shizuku settle asked the service to start.
         *
         * ⚠ **The one start in a revert with no settings write behind it.** The overlay step
         * starts Shizuku before the ordinary loop, so that loop puts the debugging transport
         * back; this one runs after everything, and a fork brings the transport up — and
         * wireless debugging down — on its way. Without a re-settle the value written seconds
         * earlier is simply lost, which is the author's report.
         */
        var settleStartedShizuku = false
"""

START_OLD = """                shizukuStartTracker.beginOverlay(OverlayStart.StartShizuku)

                try {
                    applyTarget(ManualRevertTarget.Shizuku, enabled)
                } finally {
                    shizukuStartTracker.endOverlay(OverlayStart.StartShizuku)
                }
"""

START_NEW = """                shizukuStartTracker.beginOverlay(OverlayStart.StartShizuku)

                // Attempted, not succeeded: a fork that writes the transport on its way up and
                // then dies has still switched wireless debugging off.
                settleStartedShizuku = true

                try {
                    applyTarget(ManualRevertTarget.Shizuku, enabled)
                } finally {
                    shizukuStartTracker.endOverlay(OverlayStart.StartShizuku)
                }
"""

SETTLE_OLD = """        // The device-wide debt is discharged whatever else happened. Every target was
"""

SETTLE_NEW = """        // ⚠ **Wireless debugging once more, because the step above may have taken it away.**
        // The author: *"if shizuku service successfully starts it turns off wireless debugging
        // which makes the imd set value false"*. Everything else in this revert is already
        // ordered around that — the overlay start comes before the ordinary loop precisely so
        // the loop can put the transport back — but the settle above runs last, and until r4h
        // nothing ran after it.
        //
        // Only when a start was actually attempted. A settle that stopped the service, left it
        // alone, or was skipped because the fork had already refused has moved nothing, and a
        // read plus a write on every revert for a case that cannot arise is not free.
        //
        // The result is recomputed against `initial` rather than added to what the loop
        // recorded: the row must not end up in two of the three sets, and the honest report is
        // still "the user asked for this state and got it", whatever the fork did in between.
        if (settleStartedShizuku) {
            wanted[ManualRevertTarget.WirelessDebugging]?.let { enabled ->
                val target = ManualRevertTarget.WirelessDebugging

                val now = getManualTargetStatesUseCase()

                if (now.isEnabled(target) != enabled) {
                    if (setManualTargetUseCase(target = target, enabled = enabled)) {
                        failed -= target

                        if (initial.isEnabled(target) == enabled) {
                            changed -= target

                            unchanged += target
                        } else {
                            changed += target

                            unchanged -= target
                        }
                    } else {
                        changed -= target

                        unchanged -= target

                        failed += target
                    }
                }
            }
        }

        // The device-wide debt is discharged whatever else happened. Every target was
"""


def main() -> int:
    path = ROOT / USE_CASE

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {USE_CASE}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in (
        (FLAG_OLD, FLAG_NEW, 1),
        (START_OLD, START_NEW, 1),
        (SETTLE_OLD, SETTLE_NEW, 1),
    ):
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

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        ("var settleStartedShizuku = false", 1),
        ("settleStartedShizuku = true", 1),
        ("if (settleStartedShizuku) {", 1),
        ("wanted[ManualRevertTarget.WirelessDebugging]?.let { enabled ->", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token!r}, found {text.count(token)}")

    # ⚠ **Position, not presence** — the whole point of the change is that this runs *after*
    # the Shizuku settle and before the debt is discharged. Anywhere else and it is the bug.
    loop = text.find("        for (target in ordinaryTargets) {")
    settle = text.find("        wanted[ManualRevertTarget.Shizuku]?.let { enabled ->")
    resettle = text.find("        if (settleStartedShizuku) {")
    debt = text.find("        // The device-wide debt is discharged whatever else happened.")

    if min(loop, settle, resettle, debt) < 0:
        problems.append("cannot locate the loop, the settle, the re-settle or the debt block")
    elif not loop < settle < resettle < debt:
        problems.append(
            "the re-settle is not between the Shizuku settle and the debt discharge — "
            f"loop {loop}, settle {settle}, re-settle {resettle}, debt {debt}",
        )

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

    print(f"  wrote {USE_CASE}")
    print("ok - wireless debugging is written again after a settle that started Shizuku")

    return 0


if __name__ == "__main__":
    sys.exit(main())
