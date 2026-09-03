#!/usr/bin/env python3
"""r3 — host assertions for `manageShizukuEffective`.

The switch's whole behaviour is one expression in `:domain:model`, and `:domain:model` is the
only module the host runner compiles — so this is the one place the author's rule can be
guarded rather than merely commented:

    "It can only be toggled on if all the fields below are filled and gets automatically
     toggled off if any field below is blank (but remembers the previous state in case a
     field below is emptied and filled again)."

⚠ **The remembering is the assertion that matters.** Three of the six below take a `UserData`
whose stored answer is on and whose configuration is incomplete, check the switch reads off,
then complete the configuration and check it reads on again — with nothing written in between.
A build that "fixed" this by storing the forced-off value would pass the first half and fail
the second.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

BLOCK = """    // 2b. 'Manage Shizuku' — the stored answer AND a configuration complete enough to act
    //     on. The second half is what makes the switch drop when a field is emptied; the
    //     stored answer is what makes it come back when the field is filled again.
    val managedThedjchi = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageShizuku = true)

    check("manage shizuku on with everything filled", managedThedjchi.manageShizukuEffective)

    check(
        "manage shizuku off when the answer is off",
        !managedThedjchi.copy(manageShizuku = false).manageShizukuEffective,
    )

    // Emptied, then filled again, with the stored answer untouched throughout.
    val blanked = managedThedjchi.copy(shizukuPackageName = "")

    check("manage shizuku drops when a field is blank", !blanked.manageShizukuEffective)

    check("the stored answer survives the blank", blanked.manageShizuku)

    check(
        "manage shizuku comes back when the field is filled again",
        blanked.copy(shizukuPackageName = "moe.shizuku.privileged.api").manageShizukuEffective,
    )

    // The auth key is only required where the fork reads it, so Shevery stays on without one.
    check(
        "shevery needs no auth key to be manageable",
        userData(ShizukuForkMode.Other, authKey = "", manageShizuku = true)
            .manageShizukuEffective,
    )

    check(
        "thedjchi without an auth key is not manageable",
        !userData(ShizukuForkMode.Thedjchi, authKey = "", manageShizuku = true)
            .manageShizukuEffective,
    )

"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (TESTS, [
        (
            """import com.android.geto.domain.model.withoutOverlayWhenUnmanaged
""",
            """import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.domain.model.withoutOverlayWhenUnmanaged
""",
            1,
        ),
        (
            """    checkEquals("unset never waits", 0L, ShizukuForkMode.Unset.serviceWaitMillis)

""",
            """    checkEquals("unset never waits", 0L, ShizukuForkMode.Unset.serviceWaitMillis)

""" + BLOCK,
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    # The builder has to accept the parameter these assertions pass.
    tests = staged.get(ROOT / TESTS, "")

    if tests.count("    manageShizuku: Boolean = true,") != 1:
        problems.append(f"{TESTS}: the userData builder has no manageShizuku parameter")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - seven assertions on manageShizukuEffective, three of them on the remembering")

    return 0


if __name__ == "__main__":
    sys.exit(main())
