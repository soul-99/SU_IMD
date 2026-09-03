#!/usr/bin/env python3
"""r4b — the manager puts wireless debugging back after a fork start, and holds it meanwhile.

The author, on a real symptom:

    "Whenever shizuku service comes alive it turn off wireless debugging after coming alive, so
     to rectify this ... same for IMD settings manager, whenever shizuku/shevery toggle is
     turned on by user after it turning on successfully put wireless debugging where it was
     before and for the time shizuku/shevery toggle waits keep wireless debugging toggle also
     unselectable by user"

This script is the **settings manager** half of that. The other half — settling wireless
debugging after *every* start, as the unhiding mechanism says — belongs with spec item 7, and
why is in §4 below.

### What changes

* Starting the service from the manager, **on either fork**, records where wireless debugging
  was, waits for the start, and puts it back. A fork brings the debugging transport up with its
  own `WRITE_SECURE_SETTINGS` and leaves wireless debugging wherever that left it; the user did
  not ask for that and it is not what they will see next time they look.
* **Wireless debugging is unselectable for the whole wait, on either fork.** It is about to be
  moved by something other than the user, so a press in that window races a write it cannot see.
* USB debugging stays held on **Shevery only**, and the countdown text stays Shevery's, because
  those were the author's words and Thedjchi's start does not touch USB debugging at all.

⚠ **One wait, two forks, and the Shizuku row is only exempt from it on Shevery.** Thedjchi is
asked by broadcast and must not be asked twice while it is answering — `shizukuStarting` has
always held that row. Shevery is not being asked at all, so the author's *"keep shevery service
toggle unblocked for user even during the wait"* applies there and only there.

⚠ **Restored to where it was, not to what the configuration says.** This is a manual press in
the manager, not a revert: the honest answer is the state the user had a moment ago. What the
unhiding mechanism wants is the revert path's question, and the revert path is where it is
asked.

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

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (MANAGER_VM, [
        # One wait for both forks, so the hold and the restore do not have to be written twice.
        (
            """    private var sheveryWaitJob: Job? = null

    /** Where USB debugging was before a Shevery start moved it, so an early off can put it back. */
    private var usbBeforeSheveryStart: Boolean? = null
""",
            """    private var sheveryWaitJob: Job? = null

    /** Where USB debugging was before a Shevery start moved it, so an early off can put it back. */
    private var usbBeforeSheveryStart: Boolean? = null

    /**
     * Whether a fork start begun from this dialog is still in flight, on **either** fork.
     *
     * ⚠ **Wireless debugging is unselectable for the whole of it**, which is the author's rule
     * after seeing a start move it: a fork brings the debugging transport up with its own
     * `WRITE_SECURE_SETTINGS`, so in this window that row is about to be written by something
     * other than the user and a press would race a write it cannot see.
     *
     * Separate from [sheveryWait], which is Shevery's countdown and holds **USB** debugging as
     * well. Thedjchi's start touches USB debugging not at all.
     */
    private val _serviceStarting = MutableStateFlow(false)
    val serviceStarting = _serviceStarting.asStateFlow()

    /**
     * Puts wireless debugging back where the user had it, after a start moved it.
     *
     * ⚠ **Where it was, not what the configuration says.** This is a manual press in the
     * manager rather than a revert: the honest destination is the state of a moment ago. What
     * the *unhiding mechanism* wants is the revert path's question and is asked there.
     *
     * Only when it actually moved. A start that left it alone writes nothing, so a user who
     * has wireless debugging off and wants it off is not handed a write they did not ask for.
     */
    private suspend fun settleWirelessAfterStart(before: Boolean) {
        val now = getManualTargetStatesUseCase()

        if (now.isEnabled(ManualRevertTarget.WirelessDebugging) == before) return

        setManualTargetUseCase(
            target = ManualRevertTarget.WirelessDebugging,
            enabled = before,
            manual = true,
        )
    }
""",
            1,
        ),
        # Shevery's own path records and settles wireless around its wait.
        (
            """        usbBeforeSheveryStart = _targetStates.value.isEnabled(ManualRevertTarget.UsbDebugging)

        sheveryWaitJob = viewModelScope.launch {
            try {
                var left = SHEVERY_WAIT_SECONDS
""",
            """        usbBeforeSheveryStart = _targetStates.value.isEnabled(ManualRevertTarget.UsbDebugging)

        val wirelessBefore =
            _targetStates.value.isEnabled(ManualRevertTarget.WirelessDebugging)

        sheveryWaitJob = viewModelScope.launch {
            _serviceStarting.value = true

            try {
                var left = SHEVERY_WAIT_SECONDS
""",
            1,
        ),
        (
            """                starting.join()
            } finally {
                _sheveryWait.value = null

                sheveryWaitJob = null

                usbBeforeSheveryStart = null
            }
""",
            """                starting.join()

                // ⚠ **After the start, not during it.** Shevery's own start writes the
                // transport on the way up, so anything written before it lands is written
                // over. NonCancellable because turning the row off mid-wait cancels this job,
                // and the off branch has its own USB restore to do - leaving wireless
                // debugging where a start put it would be the app changing a setting nobody
                // asked it to.
                withContext(NonCancellable) {
                    settleWirelessAfterStart(before = wirelessBefore)
                }
            } finally {
                _sheveryWait.value = null

                sheveryWaitJob = null

                usbBeforeSheveryStart = null

                _serviceStarting.value = false

                _targetStates.value = getManualTargetStatesUseCase()
            }
""",
            1,
        ),
        # Thedjchi's start goes through the ordinary path, and gets the same treatment there.
        (
            """            // manual, because this is the one caller that is a person pressing the switch.
            // It changes nothing in the off direction; on, it means the row can put the user's
            // selection back even when IMD holds no debt for it.
            val written = setManualTargetUseCase(
                target = target,
                enabled = enabled,
                manual = true,
            )
""",
            """            // ⚠ **A fork start moves wireless debugging on its way up**, whichever fork it
            // is, because it brings the debugging transport with it. Recorded before the write
            // and put back after, and the row is held meanwhile - the author's rule after
            // watching a start switch it off underneath him.
            val startingService = target == ManualRevertTarget.Shizuku && enabled

            val wirelessBefore =
                _targetStates.value.isEnabled(ManualRevertTarget.WirelessDebugging)

            if (startingService) _serviceStarting.value = true

            // manual, because this is the one caller that is a person pressing the switch.
            // It changes nothing in the off direction; on, it means the row can put the user's
            // selection back even when IMD holds no debt for it.
            val written = try {
                setManualTargetUseCase(
                    target = target,
                    enabled = enabled,
                    manual = true,
                )
            } finally {
                if (startingService) {
                    withContext(NonCancellable) {
                        settleWirelessAfterStart(before = wirelessBefore)
                    }

                    _serviceStarting.value = false
                }
            }
""",
            1,
        ),
        (
            """import kotlinx.coroutines.Job
""",
            """import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
""",
            1,
        ),
        (
            """import kotlinx.coroutines.launch
""",
            """import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
""",
            1,
        ),
    ]),
    (MANAGER, [
        (
            """    /** Seconds left of the Shevery wait, or null when nothing is waiting. */
    sheveryWait: Int? = null,
""",
            """    /** Seconds left of the Shevery wait, or null when nothing is waiting. */
    sheveryWait: Int? = null,
    /**
     * Whether a fork start begun from this dialog is in flight, on either fork.
     *
     * Holds the wireless debugging row for the whole of it: a start brings the debugging
     * transport up with it, so that row is about to be written by something other than the
     * user. Separate from [sheveryWait], which also holds **USB** debugging and only exists on
     * Shevery.
     */
    serviceStarting: Boolean = false,
""",
            1,
        ),
        (
            """                val heldBySheveryWait = sheveryWait != null &&
                    target == ManualRevertTarget.UsbDebugging
""",
            """                val heldBySheveryWait = sheveryWait != null &&
                    target == ManualRevertTarget.UsbDebugging

                // Either fork. The start is about to move this row itself; a press here would
                // race a write the user cannot see.
                val heldByServiceStart = serviceStarting &&
                    target == ManualRevertTarget.WirelessDebugging
""",
            1,
        ),
        (
            """                !busy && !disturbedByOverlayWrite && !heldBySheveryWait &&
""",
            """                !busy && !disturbedByOverlayWrite && !heldBySheveryWait &&
                    !heldByServiceStart &&
""",
            1,
        ),
    ]),
]

ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")

ROUTE_EDITS = [
    (
        """    val sheveryWait by viewModel.sheveryWait.collectAsStateWithLifecycle()
""",
        """    val sheveryWait by viewModel.sheveryWait.collectAsStateWithLifecycle()

    val serviceStarting by viewModel.serviceStarting.collectAsStateWithLifecycle()
""",
        1,
    ),
    (
        """        sheveryWait = sheveryWait,
""",
        """        sheveryWait = sheveryWait,
        serviceStarting = serviceStarting,
""",
        1,
    ),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS + [(ROUTE, ROUTE_EDITS)]:
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

    view_model = staged.get(ROOT / MANAGER_VM, "")

    # Both start routes must settle, and neither may do it twice.
    if view_model.count("settleWirelessAfterStart(before = ") != 2:
        problems.append(f"{MANAGER_VM}: expected exactly two settle sites, one per fork route")

    if view_model.count("_serviceStarting.value = true") != 2:
        problems.append(f"{MANAGER_VM}: the hold is not raised on both start routes")

    if view_model.count("_serviceStarting.value = false") != 2:
        problems.append(f"{MANAGER_VM}: the hold is not released on both start routes")

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

    print("ok - wireless debugging held during a start and put back after, on both forks")

    return 0


if __name__ == "__main__":
    sys.exit(main())
