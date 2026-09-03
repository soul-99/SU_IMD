#!/usr/bin/env python3
"""v3-r4s — host assertions for the mandatory screen-lock trigger.

The rule change passed all 468 existing assertions untouched, which sounds reassuring and is not:
it means **nothing covered it**. The one existing case that unticks screen lock also unticks the
only other trigger, so it passed under the old rule and the new one alike.

Three assertions, written so each fails if the rule is reverted:

* the idle trigger alone no longer satisfies it, where it used to;
* the swipe trigger alone no longer satisfies it, where it used to (with `DUMP` and exit reasons
  present, so that the refusal is the new rule and not a missing permission);
* screen lock alone still does, which is what makes it the failsafe rather than merely one more
  thing to tick.

⚠ **Both negative cases are measured against the old rule as well**, by asserting `anyTrigger` is
true in exactly those cases: if `satisfied` were still `anyTrigger`, they would pass, so the check
is that the two now disagree.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

OLD = """    check(
        "the tile alone is a condition too",
        ready.copy(onAppLaunch = false, onTile = true).satisfied,
    )
}"""

NEW = """    check(
        "the tile alone is a condition too",
        ready.copy(onAppLaunch = false, onTile = true).satisfied,
    )

    // r4s: screen lock is *the* trigger, not one of three — the author's failsafe. Each of
    // these fails if that is reverted, and the anyTrigger line beside each one is what proves
    // it: under the old rule these cases were satisfied precisely because anyTrigger was true.
    val idleOnly = ready.copy(onScreenLock = false, onIdle = true, usageAccess = true)

    check("the idle trigger alone would once have satisfied it", idleOnly.anyTrigger)

    check("but screen lock is mandatory, so it does not", !idleOnly.satisfied)

    val swipeOnly = ready.copy(
        onScreenLock = false,
        onSwipe = true,
        exitReasonsSupported = true,
        dumpPermission = true,
    )

    check("the swipe trigger alone would once have satisfied it", swipeOnly.anyTrigger)

    check("and it does not either, with DUMP granted", !swipeOnly.satisfied)

    check("screen lock on its own is enough", ready.satisfied)
}"""


def main() -> int:
    path = ROOT / TESTS

    if not path.is_file():
        print(f"REFUSED: missing {TESTS}")
        return 1

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: {TESTS}\n  the auto unhide block matched {original.count(OLD)} time(s)")
        return 1

    text = original.replace(OLD, NEW, 1)

    for token, expected in (
        ("idleOnly", 3),
        ("swipeOnly", 3),
        ("!idleOnly.satisfied", 1),
        ("!swipeOnly.satisfied", 1),
    ):
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {TESTS}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    path.write_text(text, encoding="utf-8")

    # ⚠ Written, then run. A test file that does not compile is worse than no test file, and the
    # tree is put back if it does not pass.
    result = subprocess.run(
        ["bash", "tools/host-tests/run.sh"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env={"PATH": "/tmp/kotlinc/bin:/usr/bin:/bin", "HOME": "/root"},
    )

    out = result.stdout + result.stderr

    if "ALL HOST ASSERTIONS PASSED" not in out:
        path.write_text(original, encoding="utf-8")

        print(f"REFUSED: the host tests did not pass:\n{out[-2000:]}")
        return 1

    passed = next((line for line in out.splitlines() if line.startswith("passed:")), "")

    print(f"  ok        {TESTS}  :: 5 new assertions, {passed}")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
