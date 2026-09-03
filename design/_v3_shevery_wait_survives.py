#!/usr/bin/env python3
"""r4d — the Shevery wait outlives the dialog, locks its own switch, and stops holding wireless.

Three instructions, and one bug report that is the reason for most of the code:

    "turning on shevery toggle should block shevery toggle, turn on and block USB debugging,
     keep wireless debugging unlocked and dont turn it on/off kee at previous state, but after
     successfully turning on should put back wireless debugging where it was if changed by
     shevery starting"

    "also if shevery toggle is tried to be turned off turn both off usb and wireless debugging"

    "when sheevry is toggled on, but during the wait time settings manager closed and opened
     again all toggles which were blocked are not blocked, countdown is not shown, just shevery
     toggle spinner showing keep showing everything even if settings maanger closed before
     countdown"

### 1. The bug: the wait died with the dialog

`sheveryWait`, `serviceStarting`, the recorded before-value and the countdown job all lived in
`SettingsManagerViewModel`, which is destroyed when the dialog closes. Reopening built a fresh
one that knew nothing: no countdown, no held rows. The spinner survived because it reads
`ShizukuStartTracker`, which is a `@Singleton` — and that is exactly the shape of the fix.

`SheveryStartTracker` is a new `@Singleton` in `domain/use-case`, holding the seconds left, the
remembered wireless value and the running job. The countdown moves to **`appScope`**, so it goes
on ticking with no dialog on screen, and any later ViewModel collects the same flows and draws
the same wait.

⚠ **In `domain/use-case` rather than beside the ViewModel**, for two reasons: it is where
`ShizukuStartTracker` and `SettingsWorkTracker` already live, and it is one of the five modules
the sandbox actually compiles — so the piece of this round with real state in it is the piece a
build here can check.

⚠ **Seconds counted by the job, not a deadline compared against a clock.** `domain/use-case` is
pure JVM and has no `SystemClock.elapsedRealtime`; `System.currentTimeMillis` would be wrong
across a clock change. The job that owns the countdown is the thing that survives, so it can
simply publish what it has counted.

### 2. The Shevery switch locks, and a press cancels

    "Block it, but a press cancels"

which keeps the r4b escape hatch the author argued for at the time — *somebody who changes their
mind has to be able to say so* — while stopping the accidental double-press. The row is drawn
unusable, so it greys and carries the spinner, and its `onClickWhenUnusable` runs the turn-off.
That is the same wrapping the other unusable rows use, and the reason this screen wraps rather
than disables: a disabled control swallows the press in silence.

⚠ **The cancel branch is tested first.** `onClickWhenUnusable`'s Shevery branch answers "this
fork has no intents", which is true and unhelpful while a start is running.

### 3. Wireless debugging is no longer held, and the user outranks the restore

The 40s hold went in for a real reason — a start writes that row itself — but forty seconds is a
long time to be locked out of a switch the author wants live. It is now free the whole wait, and
still put back afterwards **only if Shevery moved it**.

⚠ **A press during the wait replaces the remembered value** — the author's answer to the race
this opens: *"Your press wins"*. Without it the restore would undo a deliberate press made
thirty seconds earlier, which is the app overruling the person at the one moment they were
being explicit.

⚠ **Thedjchi's hold is untouched.** That start is about eight seconds, the author has not
complained about it, and nothing here is a reason to loosen a lock he asked for.

### 4. Turning Shevery off switches both debugging rows off

    "Every time it goes off"

so this replaces r4b's put-USB-back-where-it-was. Off is now off: the service, USB debugging and
wireless debugging, whether a start is in flight or the service has been up for an hour.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TRACKER = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
           "SheveryStartTracker.kt")
MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")

TRACKER_SOURCE = '''/*
 *
 *   Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.domain.usecase

import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import javax.inject.Inject
import javax.inject.Singleton

/**
 * A Shevery start begun from the settings manager, held where the dialog cannot take it away.
 *
 * ⚠ **Born from a bug report.** *"when sheevry is toggled on, but during the wait time settings
 * manager closed and opened again all toggles which were blocked are not blocked, countdown is
 * not shown, just shevery toggle spinner showing"*. Everything about the wait used to live in
 * `SettingsManagerViewModel`, which dies with the dialog; the spinner survived because it reads
 * [ShizukuStartTracker], which is a singleton. So is this.
 *
 * The forty seconds are not a request. Shevery is never asked to start: the debugging transport
 * goes up, its ErrorProtect watchdog notices, and the server appears on its own cycle. Nothing
 * can shorten that, which is why it is worth surviving a dialog dismissal — someone who closes
 * the manager and reopens it fifteen seconds later should see twenty-five, not a clean slate.
 *
 * ⚠ **Seconds counted, not a deadline compared against a clock.** This module is plain JVM with
 * no `SystemClock.elapsedRealtime`, and `System.currentTimeMillis` is wrong across a clock
 * change or a time-zone hop. The job doing the counting is itself the thing that survives, so it
 * publishes what it has counted and nothing has to be recomputed.
 *
 * ⚠ **Holds the job so a second dialog can cancel the first one's start.** The ViewModel that
 * began the wait may be long gone by the time somebody presses the switch again.
 */
@Singleton
class SheveryStartTracker @Inject constructor() {
    private val _secondsLeft = MutableStateFlow<Int?>(null)

    /** Seconds still to wait, or null when nothing is waiting. Survives the dialog. */
    val secondsLeft = _secondsLeft.asStateFlow()

    private var job: Job? = null

    /**
     * Where wireless debugging was when the start began — or where the user last put it since.
     *
     * ⚠ **A press during the wait replaces this**, which is the author's answer to the race his
     * own instructions open: wireless debugging stays unlocked through the wait *and* is put
     * back after it. Restoring the pre-start value would undo a deliberate press made thirty
     * seconds earlier, so the deliberate press becomes the value to restore.
     */
    var wirelessBefore: Boolean? = null
        private set

    /** Whether a start begun anywhere is still counting down. */
    val waiting: Boolean
        get() = _secondsLeft.value != null

    fun begin(job: Job, seconds: Int, wirelessBefore: Boolean) {
        this.job = job

        this.wirelessBefore = wirelessBefore

        _secondsLeft.value = seconds
    }

    fun tick(secondsLeft: Int) {
        // Only while one is actually running. A tick arriving after a cancel would put the
        // countdown back on screen with nothing behind it.
        if (_secondsLeft.value != null) _secondsLeft.value = secondsLeft
    }

    /** The user moved wireless debugging themselves; that is the value worth putting back. */
    fun noteWirelessChosen(enabled: Boolean) {
        if (waiting) wirelessBefore = enabled
    }

    /**
     * Stops a wait in flight, if there is one, and says whether there was.
     *
     * The caller is expected to do the switching off; this only takes the countdown down and
     * stops the job that would otherwise finish it.
     */
    fun cancel(): Boolean {
        val running = waiting

        job?.cancel()

        clear()

        return running
    }

    fun clear() {
        job = null

        wirelessBefore = null

        _secondsLeft.value = null
    }
}
'''

VM_EDITS: list[tuple[str, str, int]] = [
    # The three pieces of state that used to die with the dialog.
    (
        """    private val _sheveryWait = MutableStateFlow<Int?>(null)
    val sheveryWait = _sheveryWait.asStateFlow()

    private var sheveryWaitJob: Job? = null
""",
        """    /**
     * The Shevery countdown, off the singleton rather than out of this ViewModel.
     *
     * ⚠ **The author's bug: closing the manager mid-wait and reopening it lost everything** -
     * no countdown, no held rows, only the spinner, which survived because it reads a
     * singleton. This now reads one too, so a dialog opened fifteen seconds in shows
     * twenty-five and holds what it should.
     */
    val sheveryWait = sheveryStartTracker.secondsLeft.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = sheveryStartTracker.secondsLeft.value,
    )
""",
        1,
    ),
    (
        """    /** Where USB debugging was before a Shevery start moved it, so an early off can put it back. */
    private var usbBeforeSheveryStart: Boolean? = null
""",
        "",
        1,
    ),
    # The turn-off path: both rows off, always.
    (
        """    private fun setSheveryService(enabled: Boolean) {
        if (!enabled) {
            // ⚠ Read before the cancel. Cancelling runs the job's `finally`, which clears this.
            val before = usbBeforeSheveryStart

            usbBeforeSheveryStart = null

            sheveryWaitJob?.cancel()
            sheveryWaitJob = null

            _sheveryWait.value = null

            viewModelScope.launch {
                setManualTargetUseCase(
                    target = ManualRevertTarget.Shizuku,
                    enabled = false,
                    manual = true,
                )

                // Only what this start moved, and only back to where it was. A user who had USB
                // debugging on before pressing Shevery keeps it on.
                if (before != null) {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.UsbDebugging,
                        enabled = before,
                        manual = true,
                    )
                }

                _targetStates.value = getManualTargetStatesUseCase()
            }

            return
        }

        usbBeforeSheveryStart = _targetStates.value.isEnabled(ManualRevertTarget.UsbDebugging)

        val wirelessBefore =
            _targetStates.value.isEnabled(ManualRevertTarget.WirelessDebugging)

        sheveryWaitJob = viewModelScope.launch {
            _serviceStarting.value = true

            try {
""",
        """    private fun setSheveryService(enabled: Boolean) {
        if (!enabled) {
            sheveryStartTracker.cancel()

            // ⚠ **Both debugging rows off, whether or not a start was running** - the author's
            // rule, and it replaces r4b's put-USB-back-where-it-was. Off means off: the
            // service, and the two transports that were only ever up to carry it.
            //
            // On the application scope, because the press that gets here can be the one that
            // dismisses the dialog and takes this ViewModel with it.
            appScope.launch {
                setManualTargetUseCase(
                    target = ManualRevertTarget.Shizuku,
                    enabled = false,
                    manual = true,
                )

                for (transport in DEBUGGING_TRANSPORTS) {
                    setManualTargetUseCase(
                        target = transport,
                        enabled = false,
                        manual = true,
                    )
                }
            }

            return
        }

        val wirelessBefore =
            _targetStates.value.isEnabled(ManualRevertTarget.WirelessDebugging)

        // ⚠ **appScope, not viewModelScope** — the whole point of the fix. The wait has to keep
        // counting with the dialog shut, and the restore at the end of it has to happen whether
        // or not anybody is looking.
        val job = appScope.launch {
            try {
""",
        1,
    ),
    # The countdown publishes through the tracker.
    (
        """                var left = SHEVERY_WAIT_SECONDS

                _sheveryWait.value = left
""",
        """                var left = SHEVERY_WAIT_SECONDS
""",
        1,
    ),
    (
        """                    left -= 1

                    _sheveryWait.value = left
                }
""",
        """                    left -= 1

                    sheveryStartTracker.tick(secondsLeft = left)
                }
""",
        1,
    ),
    (
        """                withContext(NonCancellable) {
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
        """                //
                // ⚠ **The tracker's value, not the local one.** A press on wireless debugging
                // during the wait replaces it, and that press is what should be put back - the
                // author's `"Your press wins"`. Falls back to the local reading only if the
                // tracker has been cleared underneath, which means a cancel got here first.
                withContext(NonCancellable) {
                    settleWirelessAfterStart(
                        before = sheveryStartTracker.wirelessBefore ?: wirelessBefore,
                    )
                }
            } finally {
                sheveryStartTracker.clear()

                _targetStates.value = getManualTargetStatesUseCase()
            }
""",
        1,
    ),
    (
        """        }
    }

    fun markInfoShown() {
""",
        """        }

        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessBefore = wirelessBefore,
        )
    }

    /**
     * A press on the Shevery switch while it is locked mid-wait.
     *
     * ⚠ **Locked, but not inert** - the author's *"Block it, but a press cancels"*, which keeps
     * the r4b escape hatch he argued for at the time while stopping the accidental second
     * press. The row is wrapped rather than disabled for the reason this whole screen wraps:
     * a disabled control swallows the press in silence.
     *
     * Straight to the turn-off path, so cancelling a start and switching the service off are
     * one behaviour with one implementation rather than two that could drift.
     */
    fun cancelSheveryService() {
        setSheveryService(enabled = false)
    }

    fun markInfoShown() {
""",
        1,
    ),
    # A wireless press during the wait is the value worth restoring.
    (
        """        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
""",
        """        // ⚠ **The user outranks the restore.** Wireless debugging stays unlocked through a
        // Shevery wait, and is also put back when that wait ends; without this the restore
        // would undo a deliberate press made thirty seconds earlier. The author's answer to
        // his own race: the press becomes the value to put back.
        if (target == ManualRevertTarget.WirelessDebugging) {
            sheveryStartTracker.noteWirelessChosen(enabled = enabled)
        }

        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
""",
        1,
    ),
    # Injection, and the pair of transports the turn-off switches off.
    (
        """    private val shizukuStartTracker: ShizukuStartTracker,
""",
        """    private val shizukuStartTracker: ShizukuStartTracker,
    private val sheveryStartTracker: SheveryStartTracker,
""",
        1,
    ),
    (
        """import com.android.geto.domain.usecase.SetManualTargetUseCase
""",
        """import com.android.geto.domain.usecase.SetManualTargetUseCase
import com.android.geto.domain.usecase.SheveryStartTracker
""",
        1,
    ),
]

VM_TAIL = """
/**
 * The two rows a Shevery start puts up and a Shevery stop takes down together.
 *
 * Named once rather than written twice: the author's rule is that turning the service off turns
 * both off, and a list is harder to half-apply than two calls in a row.
 */
private val DEBUGGING_TRANSPORTS = listOf(
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.WirelessDebugging,
)
"""

MANAGER_EDITS: list[tuple[str, str, int]] = [
    (
        """                // ⚠ **USB debugging is the row that goes dead during a Shevery wait, and the
                // Shevery row is not.** The author's asymmetry: the transport is what is
                // holding the service up, so touching it mid-wait would undo the very thing
                // being waited for - while somebody who has changed their mind has to be able
                // to say so, and saying so is what puts USB debugging back.
                val heldBySheveryWait = sheveryWait != null &&
                    target == ManualRevertTarget.UsbDebugging
""",
        """                // ⚠ **USB debugging and the Shevery row itself, and wireless debugging not
                // at all.** r4b had this the other way round on both counts; the author
                // reversed it after using it. The transport is what is holding the service
                // up, so touching USB mid-wait would undo the very thing being waited for,
                // and the service row goes with it so a second press cannot queue a second
                // start - but that row is *wrapped* rather than disabled, and its press
                // cancels, which is the escape hatch he asked for in r4b kept intact.
                //
                // Wireless debugging is free the whole wait: forty seconds is a long time to
                // be locked out of a switch, and it is put back afterwards only if Shevery
                // moved it.
                val heldBySheveryWait = sheveryWait != null &&
                    (
                        target == ManualRevertTarget.UsbDebugging ||
                            target == ManualRevertTarget.Shizuku
                        )
""",
        1,
    ),
    (
        """                                    // Shevery has no intents and does not need any: the row
                                    // writes the debugging transport instead. Nor is it held
                                    // by a start in flight - that start is its own wait.
                                    (isShevery || states.shizukuSupportsIntents) &&
                                    (isShevery || !shizukuStarting)
""",
        """                                    // Shevery has no intents and does not need any: the row
                                    // writes the debugging transport instead. It is held by
                                    // its own wait rather than by `shizukuStarting`, above.
                                    (isShevery || states.shizukuSupportsIntents) &&
                                    (isShevery || !shizukuStarting)
""",
        1,
    ),
    (
        """                    onClickWhenUnusable = when {
                        // Shevery first, because it is the permanent one: the switch is
""",
        """                    onClickWhenUnusable = when {
                        // ⚠ **Before every other Shevery branch.** Those answer "this fork has
                        // no intents", which is true and useless while a start is running.
                        // The author asked for the switch to look blocked and still cancel.
                        isShizuku && isShevery && sheveryWait != null -> onCancelShevery

                        // Shevery first, because it is the permanent one: the switch is
""",
        1,
    ),
    (
        """    onUnhideSettings: () -> Unit,
    onHideSettings: () -> Unit,
""",
        """    onUnhideSettings: () -> Unit,
    onHideSettings: () -> Unit,
    /**
     * A press on the Shevery switch while its own start has it locked.
     *
     * The switch is drawn unusable so it greys and carries the spinner, but the press still
     * arrives here and stops the start — *"Block it, but a press cancels"*.
     */
    onCancelShevery: () -> Unit = {},
""",
        1,
    ),
]

ROUTE_EDITS: list[tuple[str, str, int]] = [
    (
        """        onHideSettings = viewModel::hideSettings,
""",
        """        onHideSettings = viewModel::hideSettings,
        // Straight to the turn-off path: cancelling a start and switching the service off are
        // the same behaviour, so they are the same call.
        onCancelShevery = viewModel::cancelSheveryService,
""",
        1,
    ),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in (
        (MANAGER_VM, VM_EDITS),
        (MANAGER, MANAGER_EDITS),
        (ROUTE, ROUTE_EDITS),
    ):
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

    if view_model and not view_model.endswith(VM_TAIL):
        staged[ROOT / MANAGER_VM] = view_model.rstrip("\n") + "\n" + VM_TAIL
        view_model = staged[ROOT / MANAGER_VM]

    manager = staged.get(ROOT / MANAGER, "")

    # ⚠ Asserted against code, never against the prose around it — the third-instance trap.
    for rel, text, token, expected in (
        (MANAGER_VM, view_model, "_sheveryWait", 0),
        (MANAGER_VM, view_model, "sheveryWaitJob", 0),
        (MANAGER_VM, view_model, "usbBeforeSheveryStart", 0),
        (MANAGER_VM, view_model, "sheveryStartTracker.", 8),
        (MANAGER_VM, view_model, "appScope.launch", 8),
        (MANAGER_VM, view_model, "DEBUGGING_TRANSPORTS", 2),
        (MANAGER_VM, view_model, "fun cancelSheveryService()", 1),
        (MANAGER, manager, "onCancelShevery", 2),
        (MANAGER, manager, "target == ManualRevertTarget.Shizuku\n", 3),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # Wireless debugging must no longer be held by a Shevery wait, only by a Thedjchi start.
    if "heldByServiceStart = serviceStarting &&" not in manager:
        problems.append(f"{MANAGER}: the Thedjchi hold on wireless debugging has gone missing")

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

    for line in TRACKER_SOURCE.splitlines():
        if len(line) > 120:
            problems.append(f"{TRACKER}: line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    (ROOT / TRACKER).write_text(TRACKER_SOURCE, encoding="utf-8")
    print(f"  wrote {TRACKER}")

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - the wait survives the dialog, locks its own switch, and leaves wireless alone")

    return 0


if __name__ == "__main__":
    sys.exit(main())
