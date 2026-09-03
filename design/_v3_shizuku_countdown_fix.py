#!/usr/bin/env python3
"""r4j — the Thedjchi countdown registers without an escape hatch that abandons the write.

⚠ **A defect in `_v3_shizuku_countdown.py`, caught by reading its output before it shipped.**
That script registered the ticker as

    job = ticker ?: return@launch,

inside `viewModelScope.launch`. `ticker` is non-null wherever that line runs — it is guarded by
the same `startingService` — but the compiler cannot know it, and the elvis is not a
formality: `return@launch` would abandon `setManualTargetUseCase` and the wireless settle after
it, so a compiler that ever took that branch would have the switch do nothing at all.

**The lesson, and it is the r4e one in a new shape.** A null-check written to satisfy the type
system rather than to describe a real case is a branch nobody has thought about, placed where
its cost is highest. The fix is to build the job and register it in one place, where it is a
`val` that cannot be null.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")

OLD = """            // ⚠ **The same countdown Shevery uses, because only one start can be running.**
            // The wait comes from the fork rather than being restated here, so Thedjchi's
            // eight seconds and Shevery's forty stay one fact in one place. Registered with a
            // null job: this start is not cancellable from the row - that is Shevery's
            // arrangement, not this one - and `cancel()` on a null job is a no-op.
            val ticker = if (startingService) {
                appScope.launch {
                    var left = shizukuWaitSeconds()

                    while (left > 0 && isActive) {
                        delay(1_000)

                        if (getManualTargetStatesUseCase()
                                .isEnabled(ManualRevertTarget.Shizuku)
                        ) {
                            break
                        }

                        left -= 1

                        sheveryStartTracker.tick(secondsLeft = left)
                    }
                }
            } else {
                null
            }

            if (startingService) {
                sheveryStartTracker.begin(
                    job = ticker ?: return@launch,
                    seconds = shizukuWaitSeconds(),
                    wirelessOn = _targetStates.value
                        .isEnabled(ManualRevertTarget.WirelessDebugging),
                )
            }
"""

NEW = """            // ⚠ **The same countdown Shevery uses, because only one start can be running.**
            // The wait comes from the fork rather than being restated here, so Thedjchi's
            // eight seconds and Shevery's forty stay one fact in one place.
            //
            // Built and registered together, in the one place where the job is a `val` that
            // cannot be null. Splitting the two - a nullable `ticker` up here and a `begin`
            // below it - needs an elvis to satisfy the compiler, and the only thing to put on
            // the right of it is a `return` that would abandon the write below.
            //
            // The tick loop breaks on the service appearing, so a start that comes up in three
            // seconds stops at three rather than counting down at a service already running.
            val ticker = if (startingService) {
                val seconds = shizukuWaitSeconds()

                val job = appScope.launch {
                    var left = seconds

                    while (left > 0 && isActive) {
                        delay(1_000)

                        if (getManualTargetStatesUseCase()
                                .isEnabled(ManualRevertTarget.Shizuku)
                        ) {
                            break
                        }

                        left -= 1

                        sheveryStartTracker.tick(secondsLeft = left)
                    }
                }

                sheveryStartTracker.begin(
                    job = job,
                    seconds = seconds,
                    wirelessOn = _targetStates.value
                        .isEnabled(ManualRevertTarget.WirelessDebugging),
                )

                job
            } else {
                null
            }
"""


def main() -> int:
    path = ROOT / MANAGER_VM

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER_VM}: missing")

        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print("REFUSED, nothing written")
        print(f"  expected 1 of the ticker block, found {found}")

        return 1

    text = text.replace(OLD, NEW, 1)

    problems: list[str] = []

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        # The escape hatch is gone, and nothing else in this function returns early.
        ("return@launch", 0),
        # ⚠ Two, not one: the Shevery path has had this exact shape since r4d, and an earlier
        # draft of these assertions counted only the new one and refused.
        ("val job = appScope.launch {", 2),
        ("job = job,", 2),
        ("val seconds = shizukuWaitSeconds()", 1),
        ("shizukuWaitSeconds()", 2),
        ("sheveryStartTracker.begin(", 2),
        ("ticker?.cancel()", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token!r}, found {text.count(token)}")

    # ⚠ **Position, not presence.** The registration must sit inside the branch that built the
    # job, above the `job` the branch evaluates to.
    branch = text.find("            val ticker = if (startingService) {")
    launch = text.find("                val job = appScope.launch {")
    begin = text.find("                sheveryStartTracker.begin(\n                    job = job,")
    yields = text.find("                job\n            } else {")

    if min(branch, launch, begin, yields) < 0:
        problems.append("cannot locate the branch, the job, its registration or its result")
    elif not branch < launch < begin < yields:
        problems.append("the job is not built, registered and returned in that order")

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

    print(f"  wrote {MANAGER_VM}")
    print("ok - the ticker is built and registered in one place, with no early return")

    return 0


if __name__ == "__main__":
    sys.exit(main())
