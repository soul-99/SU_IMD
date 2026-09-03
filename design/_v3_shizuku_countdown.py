#!/usr/bin/env python3
"""r4j — the Shizuku start gets the countdown Shevery has, and a start stops explaining itself.

Two reports:

    "shizuku is not showing count down line"

    "during wait time for shizuku/shevery if toggle/toggle label is clicked again it opens this
     dialog … this should only be shown when shizuku is not configured in imd"

### 1. The countdown, shared rather than duplicated

Only one fork start can be in flight at a time, so there is one countdown and one tracker. The
Thedjchi path now publishes into the same `SheveryStartTracker` the Shevery path does, and the
two differ in exactly the two ways they actually differ:

* **the duration**, which is `ShizukuForkMode.serviceWaitMillis` — 8s for Thedjchi, 40s for
  Shevery — read from the fork rather than restated here;
* **the string**, which the dialog picks from `isShevery`, the same value that already renames
  the row itself.

⚠ **A second flow was the obvious move and the wrong one.** Two countdowns that can never both
run are two states that can disagree, and the dialog would have had to decide which to draw. One
value, one owner.

⚠ **The tick loop watches for the service, exactly as Shevery's does**, so an 8s wait that ends
in 3 stops at 3 rather than counting down to a service that is already up.

⚠ **On `appScope`, so it survives the dialog** — which also closes the r4d leftover about
`serviceStarting` dying with the manager, because the countdown is now what the row is held by.

### 2. A start is not a configuration problem

The author's screenshot is *Shizuku service unavailable*, whose first line is *"make sure the
Shizuku app is installed, registered in ADB, and configured correctly"*. It fires from
`onClickWhenUnusable` because `states.shizukuAvailable` is false — and during a start it can be
false transiently, since it is a package query that `runCatching` turns into `false` when the
platform declines to answer.

Either way the dialog is wrong there: nothing about the configuration has changed, the row is
simply busy. One branch above the explanations, and pressing a starting row now does nothing on
Thedjchi and still cancels on Shevery.

⚠ **This got louder in r4i, not newer.** Making the whole row tappable meant the label reached
the same handler the switch did; the branch was always reachable.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
STRINGS = "feature/apps/src/main/res/values/strings.xml"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            """    <string name="shevery_wait_countdown">Waiting for Shevery service to run...(%1$d)</string>
""",
            """    <string name="shevery_wait_countdown">Waiting for Shevery service to run...(%1$d)</string>
    <string name="shizuku_wait_countdown">Waiting for Shizuku service to run...(%1$d)</string>
""",
            1,
        ),
    ]),

    (MANAGER, [
        # The line names the fork it is waiting for.
        (
            """                if (isShizuku && sheveryWait != null) {
                    Text(
                        modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
                        text = stringResource(R.string.shevery_wait_countdown, sheveryWait),
""",
            """                if (isShizuku && sheveryWait != null) {
                    Text(
                        modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
                        // One countdown, two names. Only one fork start can be in flight, so
                        // the value has a single owner; which service it is waiting for is the
                        // same question that renames the row above it.
                        text = stringResource(
                            if (isShevery) {
                                R.string.shevery_wait_countdown
                            } else {
                                R.string.shizuku_wait_countdown
                            },
                            sheveryWait,
                        ),
""",
            1,
        ),
        # A start in flight is not a configuration failure.
        (
            """                        isShizuku && isShevery && sheveryWait != null -> onCancelShevery

""",
            """                        isShizuku && isShevery && sheveryWait != null -> onCancelShevery

                        // ⚠ **Above every explanation below, and the author's report.** With a
                        // start in flight the row is busy, not misconfigured - but
                        // `states.shizukuAvailable` is a package query that `runCatching`
                        // turns into false when the platform declines to answer, so the
                        // *unavailable* dialog could fire mid-start and tell somebody to go
                        // and check a configuration that is perfectly correct.
                        //
                        // Nothing, rather than a different dialog: the countdown under the row
                        // already says what is happening, and a pop-up repeating it would be
                        // the same news twice. Shevery keeps its cancel, one branch above.
                        isShizuku && shizukuStarting -> null

""",
            1,
        ),
    ]),

    (MANAGER_VM, [
        # The Thedjchi start publishes the same countdown Shevery's does.
        (
            """            if (startingService) _serviceStarting.value = true
""",
            """            if (startingService) _serviceStarting.value = true

            // ⚠ **The same countdown Shevery uses, because only one start can be running.**
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
""",
            1,
        ),
        (
            """                if (startingService) {
                    withContext(NonCancellable) {
                        settleWirelessAfterStart(before = wirelessBefore)
                    }

                    _serviceStarting.value = false
                }
""",
            """                if (startingService) {
                    ticker?.cancel()

                    sheveryStartTracker.clear()

                    withContext(NonCancellable) {
                        settleWirelessAfterStart(before = wirelessBefore)
                    }

                    _serviceStarting.value = false
                }
""",
            1,
        ),
        # The wait, from the fork rather than a second copy of the number.
        (
            """    fun cancelSheveryService() {
""",
            """    /**
     * How long this device's fork takes to come up, in whole seconds.
     *
     * From [ShizukuForkMode.serviceWaitMillis] rather than a constant here, so Thedjchi's eight
     * seconds and Shevery's forty stay one fact. [SHEVERY_WAIT_SECONDS] is the same value read
     * at the top of the file for the one path that is always Shevery.
     */
    private suspend fun shizukuWaitSeconds(): Int =
        (userDataRepository.userData.first().shizukuForkMode.serviceWaitMillis / 1_000L).toInt()

    fun cancelSheveryService() {
""",
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

    manager = staged.get(ROOT / MANAGER, "")
    view_model = staged.get(ROOT / MANAGER_VM, "")
    strings = staged.get(ROOT / STRINGS, "")

    if "import com.android.geto.domain.model.ShizukuForkMode\n" not in view_model:
        anchor = "import com.android.geto.domain.model.ManualRevertTarget\n"

        if view_model.count(anchor) != 1:
            problems.append(f"{MANAGER_VM}: cannot place the ShizukuForkMode import")
        else:
            staged[ROOT / MANAGER_VM] = view_model.replace(
                anchor,
                anchor + "import com.android.geto.domain.model.ShizukuForkMode\n",
                1,
            )
            view_model = staged[ROOT / MANAGER_VM]

    # ⚠ Asserted against code, never the prose around it.
    for rel, text, token, expected in (
        (STRINGS, strings, 'name="shizuku_wait_countdown"', 1),
        (MANAGER, manager, "R.string.shizuku_wait_countdown", 1),
        (MANAGER, manager, "R.string.shevery_wait_countdown", 1),
        (MANAGER, manager, "isShizuku && shizukuStarting -> null", 1),
        (MANAGER_VM, view_model, "private suspend fun shizukuWaitSeconds(): Int", 1),
        (MANAGER_VM, view_model, "shizukuWaitSeconds()", 3),
        (MANAGER_VM, view_model, "ticker?.cancel()", 1),
        # One tracker, so `begin` is called on both start paths and nowhere else.
        (MANAGER_VM, view_model, "sheveryStartTracker.begin(", 2),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # ⚠ **Position, not presence.** The busy branch must come above the two that explain a
    # configuration, or it never runs.
    cancel = manager.find("                        isShizuku && isShevery && sheveryWait != null")
    busy = manager.find("                        isShizuku && shizukuStarting -> null")
    unavailable = manager.find("                        isShizuku && !states.shizukuAvailable ->")

    if min(cancel, busy, unavailable) < 0:
        problems.append(f"{MANAGER}: cannot locate the cancel, busy or unavailable branch")
    elif not cancel < busy < unavailable:
        problems.append(f"{MANAGER}: the busy branch is not above the explanations")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and path.suffix != ".xml":
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

    print("ok - one countdown for both forks, and a starting row no longer blames the config")

    return 0


if __name__ == "__main__":
    sys.exit(main())
