/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.feature.apps.manager

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.OverlayRestoreRunner
import com.android.geto.broadcastreceiver.SheveryStartFailureNotification
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.ManagerRows
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.model.masterPillOrder
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.GetManualTargetStatesUseCase
import com.android.geto.domain.usecase.RecordManualChangeUseCase
import com.android.geto.domain.usecase.SetManualTargetUseCase
import com.android.geto.domain.usecase.SheveryStartTracker
import com.android.geto.domain.usecase.SettingsWorkKind
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Short enough to read as live, long enough that it is not doing anything expensive: the
 * reads behind it are in-process setting lookups and a binder ping, and it only runs while
 * the manager is on screen.
 */
private const val TARGET_POLL_MILLIS = 500L

/**
 * The Shevery countdown, in seconds.
 *
 * ⚠ **Derived, not typed again.** Forty is the author's number for how long Shevery's watchdog
 * may take, and it already lives on the fork mode as the wait `StartShizukuUseCase` actually
 * spends. A countdown that could disagree with the wait it is counting would be worse than no
 * countdown at all.
 */
private val SHEVERY_WAIT_SECONDS =
    (ShizukuForkMode.Other.serviceWaitMillis / 1_000L).toInt()

/**
 * Everything the settings manager needs, independent of where it is being shown from.
 *
 * Lifted out of the Favourites screen because the manager now has three front doors — that
 * tab, a Quick Settings tile, and a long-press shortcut — and two of them open it with no
 * app UI behind it at all. One owner for the polling and the writes means the tile cannot
 * drift away from the in-app dialog.
 */
@HiltViewModel
class SettingsManagerViewModel @Inject constructor(
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val recordManualChangeUseCase: RecordManualChangeUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val sheveryStartTracker: SheveryStartTracker,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val settingsWorkTracker: SettingsWorkTracker,
    // r4n: the forty-second Shevery timeout raises the author's alerting notification, and
    // the notification wrapper does not reach this module. Depends on no runner, so no cycle.
    private val sheveryStartFailureNotification: SheveryStartFailureNotification,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    private val _targetStates = MutableStateFlow(ManualTargetStates())
    val targetStates = _targetStates.asStateFlow()

    private val _shizukuLaunchPackage = MutableStateFlow<String?>(null)
    val shizukuLaunchPackage = _shizukuLaunchPackage.asStateFlow()

    /**
     * Whether an attempt to start Shizuku is in flight, from anywhere.
     *
     * Off the shared tracker rather than a local flag, because the attempt is often not this
     * dialog's: a revert from the tile or a notification can begin one while the dialog is
     * shut, and opening it mid-attempt has to show what is actually happening.
     */
    val shizukuStarting = shizukuStartTracker.starting.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = false,
    )

    /**
     * Which way settings work in flight is going, or null when nothing is running.
     *
     * Off the shared tracker for the same reason [shizukuStarting] is: the work is very often
     * not this dialog's. IMD+ noticing a watched app, a launch from inside IMD, the revert
     * notification, a Tasker intent — any of them can be mid-change while this is open, and
     * every row here writes the same settings they do. A toggle pressed in the middle starts a
     * second change over the top of the first, which is the bug this closes.
     *
     * Null covers both "nothing is happening" and the moment before a press has decided which
     * way it is going; the dialog holds its rows disabled either way and only names the
     * direction once there is one. See [SettingsWorkTracker.work].
     */
    val settingsWork = settingsWorkTracker.work.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null,
    )

    /**
     * Whether anything is writing settings right now, whoever asked.
     *
     * Separate from [settingsWork] because the rows go dead the instant work starts, which is
     * before there is a direction to name.
     */
    val settingsWorkInFlight = settingsWorkTracker.inFlight.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = false,
    )

    /**
     * Whether the last attempt timed out. Persisted, so a failure during a revert with no UI
     * on screen is still there to report when the dialog is next opened.
     */
    val shizukuStartFailed = userDataRepository.userData
        .map { it.shizukuStartFailed }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Whether a revert could not put overlay access back.
     *
     * Persisted, like [shizukuStartFailed], and for the same reason: the failure usually
     * happens during a revert with no UI on screen at all. Unlike that one it is not cleared
     * when the dialog closes - it describes apps that are still missing a permission, and it
     * stays until a restore actually succeeds.
     */
    val overlayRestoreFailed = userDataRepository.userData
        .map { it.overlayRestoreFailed }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Whether IMD manages overlay access at all - the master switch in Advanced settings.
     *
     * With it off the overlay row is not drawn here either, matching the three rows it
     * already removes from Settings. What replaces it is the revert failure notification:
     * it is ongoing, it survives the tap that opens this dialog, and its **Try again**
     * button runs the same restore the row would have. Reaching that restore therefore
     * never depends on a row that is not on screen.
     *
     * The "Revert to default" button below the rows is the other way back: a debt taken
     * while the switch was on is still owed after it is switched off, so a revert still
     * hands overlay access back - see UserData.effectiveRevertDefaults.
     */
    /**
     * Whether the Shizuku row is drawn at all.
     *
     * ⚠ **Hidden rather than greyed, on the author's instruction** — *"Hide/remove the shizuku
     * toggle completely in IMD services manager"* when 'Manage Shizuku' is off. Every other
     * unusable row in this dialog greys and explains itself; this one goes, because with the
     * master switch off IMD is not managing that service at all and a greyed row would be
     * offering something the user has said no to.
     */
    val manageShizuku = userDataRepository.userData
        .map { it.manageShizukuEffective }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Which rows the user chose to see, from "Settings manager options" in Settings.
     *
     * ⚠ **Drawing only, exactly like [manageShizuku] above** — and unlike it, not a statement
     * about whether IMD manages the target at all. A row hidden here is still hidden by a hide,
     * still restored by a revert, and still counted by everything in the engine; it is simply not
     * on this card.
     *
     * ⚠ **Starts as every row.** The initial value is what the manager has always drawn, so the
     * frame before the store answers looks like the card the user knows rather than an empty one
     * that fills in.
     */
    val managerRows = userDataRepository.userData
        .map { it.managerRows }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ManagerRows.Default,
        )

    /**
     * Why the Display over other apps row will not move, or empty while it will.
     *
     * The domain decides; this only carries the answer. See `overlayBlockReasons`.
     */
    val overlayBlocked = userDataRepository.userData
        .map { overlayBlockReasons(userData = it) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = emptyList(),
        )

    /**
     * Whether Shevery is the selected fork, which changes what three rows of this dialog do.
     *
     * Read here rather than asked per press: the label, the usability of two rows and the whole
     * countdown below all turn on it, and a press that read it separately could disagree with
     * the row it was pressed on.
     */
    val isShevery = userDataRepository.userData
        .map { it.shizukuForkMode.isShevery && it.manageShizukuEffective }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Seconds left of the Shevery wait, or null when nothing is waiting.
     *
     * ⚠ **The clock is the deadline, not the answer.** What actually knows whether Shevery came
     * up is the poll behind [targetStates]; this counts down beside it so the user has
     * something to read, and stops the moment the service is seen.
     */
    /**
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
    /**
     * Put wireless debugging back **on** after a Shevery start that came up.
     *
     * ⚠ **One direction, deliberately, and separate from [settleWirelessAfterStart].** That one
     * drives the row to whatever it was and is what the Thedjchi path still wants; this one only
     * ever switches it on, because the author's rule for Shevery is *"put wireless debugging to
     * on if it was on"* and says nothing about the other case. Two behaviours under one name
     * with a flag would be the version of this that gets misread later.
     *
     * Writes nothing if the start left the row alone, so a device that never lost wireless
     * debugging is not handed a write it did not need.
     */
    private suspend fun raiseWirelessAfterSheveryStart() {
        val now = getManualTargetStatesUseCase()

        if (now.isEnabled(ManualRevertTarget.WirelessDebugging)) return

        setManualTargetUseCase(
            target = ManualRevertTarget.WirelessDebugging,
            enabled = true,
            manual = true,
        )
    }

    private suspend fun settleWirelessAfterStart(before: Boolean) {
        val now = getManualTargetStatesUseCase()

        if (now.isEnabled(ManualRevertTarget.WirelessDebugging) == before) return

        setManualTargetUseCase(
            target = ManualRevertTarget.WirelessDebugging,
            enabled = before,
            manual = true,
        )
    }

    /**
     * The Shevery half of [setTargetEnabled], which is a different operation from the Thedjchi
     * one despite wearing the same switch.
     *
     * Thedjchi is asked, by broadcast, and answers in about eight seconds. Shevery is not asked
     * at all: the debugging transport goes up, and Shevery's own ErrorProtect watchdog notices
     * and starts the server on its own cycle — which is why the wait is forty seconds and why
     * the row that must not be touched meanwhile is **USB debugging**, not this one.
     *
     * ⚠ **The author's asymmetry, and it is deliberate**: *"blocks USB debugging toggle for 40s
     * ... in this period keep shevery service toggle unblocked for user even during the wait"*.
     * Somebody who changes their mind has to be able to say so, and saying so is what puts USB
     * debugging back.
     */
    private fun setSheveryService(enabled: Boolean) {
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
                var left = SHEVERY_WAIT_SECONDS

                // The start writes the transport and then polls for the same forty seconds
                // inside StartShizukuUseCase. Launched rather than awaited so the countdown
                // below runs beside it rather than after it.
                val starting = launch {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.Shizuku,
                        enabled = true,
                        manual = true,
                    )
                }

                // ⚠ **Read once and kept.** The write below happens only on a start that
                // actually came up, and asking the same question a second time afterwards
                // would be asking it of a device the join may have changed underneath.
                var came = false

                while (left > 0 && isActive) {
                    delay(1_000)

                    _targetStates.value = getManualTargetStatesUseCase()

                    if (_targetStates.value.isEnabled(ManualRevertTarget.Shizuku)) {
                        came = true

                        break
                    }

                    left -= 1

                    sheveryStartTracker.tick(secondsLeft = left)
                }

                starting.join()

                // ⚠ **Only on a start that came up, and only in the on direction.** The
                // author's rule, and both halves of it are narrower than r4e's: a start that
                // timed out has moved nothing worth putting back, and a device that had
                // wireless debugging off before the press is left wherever the start put it.
                // `do not manage wireless debugging toggle` governs everything this does not
                // do.
                //
                // ⚠ **After the start, not during it.** Shevery writes the transport on its
                // way up, so anything written before that lands is written over.
                // NonCancellable because turning the row off mid-wait cancels this job, and
                // the value below would otherwise be lost between the check and the write.
                if (came && sheveryStartTracker.wirelessWanted) {
                    withContext(NonCancellable) {
                        raiseWirelessAfterSheveryStart()
                    }
                }

                // ⚠ **The forty seconds ran out, and the author asked to be told out of band.**
                // The inline row failure in the dialog is not enough on its own: a Shevery
                // start is long enough that the manager is very often closed by the time it
                // gives up, and the one thing that fixes it - opening Shevery and starting the
                // service by hand - is what the notification's tap does.
                //
                // NonCancellable for the same reason as the wireless settle above: closing the
                // row cancels this job, and the news is about what already happened.
                if (!came && isActive) {
                    withContext(NonCancellable) {
                        sheveryStartFailureNotification.warnStartFailed()
                    }
                }
            } finally {
                sheveryStartTracker.clear()

                _targetStates.value = getManualTargetStatesUseCase()
            }
        }

        // ⚠ **After the launch, because the job is what is being registered.** The countdown
        // starts at its first `delay`, so the tracker is published well before the first tick,
        // and a later dialog can cancel this start without ever having met the ViewModel that
        // began it.
        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessOn = wirelessBefore,
        )
    }

    /**
     * Whether a row refused to move because `WRITE_SECURE_SETTINGS` has gone.
     *
     * Before this, a lost grant here looked like a dead switch: it moved under the
     * finger, the re-read below put it straight back, and nothing said why. The author's
     * rule is that this one failure is reported the same way on every route that hides
     * settings, and this screen is one of them.
     */
    private val _permissionsLost = MutableStateFlow(false)
    val permissionsLost = _permissionsLost.asStateFlow()

    private val _overlayWriteInFlight = MutableStateFlow(false)

    /**
     * Whether a restore started from this dialog is running.
     *
     * Restoring overlay access needs Shizuku, and starting a Shizuku fork switches the
     * debugging settings on by itself. Those rows are therefore locked for the duration and
     * put back afterwards, because otherwise the user watches three switches they did not
     * touch move on their own, and any press they make in that window races the restore.
     */
    val overlayWriteInFlight = _overlayWriteInFlight.asStateFlow()

    /**
     * Whether the manager has already explained itself, or null while that is still being
     * read.
     *
     * Nullable on purpose. A plain false as the initial value would mean every open of this
     * dialog flashes the information popup for the moment before the stored answer arrives,
     * including for people who dismissed it months ago.
     */
    val infoShown: StateFlow<Boolean?> = userDataRepository.userData
        .map<UserData, Boolean?> { it.settingsManagerInfoShown }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = null,
        )

    /**
     * Whether anything IMD did is still outstanding, by any of the three routes it can owe on.
     *
     * ⚠ **The same three questions `unhidePending` asks**, and derived from the same stored
     * values rather than from a flag of its own — `UserData.settingsHidden` is
     * `settingsHiddenDeviceWide || memoryHoldsSettings`, which is exactly what
     * `GetSettingsHiddenUseCase` returns. A separate test here could disagree with the one
     * doing the work, and the way it would show is a live button that says there is nothing
     * to restore, or a greyed one that would have restored something.
     */
    val anythingHidden: StateFlow<Boolean> = userDataRepository.userData
        .map { it.autoHideRunning || it.settingsHidden }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Settle every debt that actually exists, or say there is none.
     *
     * ⚠ **`unhidePending`, not `unhide` and not a revert.** `unhide` is the Hide settings
     * tile's behaviour and falls back to the configured defaults on a device with nothing
     * hidden, because a tile that did nothing reads as broken; the author asked this button
     * for the opposite — `'IMD: No hidden settings to restore'`, and no setting touched.
     *
     * On the application scope for the reason [revertToDefault] is: opened from the tile or
     * the shortcut, this dialog's dismissal finishes the activity and takes this ViewModel
     * with it, and the work must outlive that.
     */
    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }

    /**
     * Hide, from the same button that unhides.
     *
     * ⚠ **`hide()` rather than the tile's `toggle()`.** `toggle()` reads `settingsHidden` and
     * picks a direction from it; the button's label is picked from [anythingHidden], which is
     * `autoHideRunning || settingsHidden` and can be true where that is false. Two tests would
     * eventually disagree, and the way it would show is a button reading `Unhide settings`
     * that hides. The screen decides the direction once and calls the matching half.
     *
     * ⚠ **Claimed as [SettingsWorkKind.Hiding] for the whole press**, because
     * [SettingsHiddenRunner.hide] does not claim the tracker for itself — `toggle()` wraps it.
     * Without this the manager's own busy state and the tile would flicker between the use
     * cases underneath, which is exactly what `revertToDefault` claims to avoid.
     *
     * The runner posts the revert notification and says `'Settings hidden'` itself, on the one
     * test that means the device may actually have changed. Nothing to add here.
     *
     * On the application scope for the reason [unhideSettings] is: opened from the tile or the
     * shortcut, this dialog's dismissal finishes the activity and takes this ViewModel with
     * it, and the work must outlive that.
     */
    fun hideSettings() {
        appScope.launch {
            settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
                settingsHiddenRunner.hide()
            }
        }
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
    /**
     * How long this device's fork takes to come up, in whole seconds.
     *
     * From [ShizukuForkMode.serviceWaitMillis] rather than a constant here, so Thedjchi's eight
     * seconds and Shevery's forty stay one fact. [SHEVERY_WAIT_SECONDS] is the same value read
     * at the top of the file for the one path that is always Shevery.
     */
    private suspend fun shizukuWaitSeconds(): Int =
        (userDataRepository.userData.first().shizukuForkMode.serviceWaitMillis / 1_000L).toInt()

    fun cancelSheveryService() {
        setSheveryService(enabled = false)
    }

    fun markInfoShown() {
        viewModelScope.launch {
            userDataRepository.updateSettingsManagerInfoShown(shown = true)
        }
    }

    private var watchJob: Job? = null

    /**
     * Starts re-reading every row's real state while the manager is on screen.
     *
     * Polled rather than observed because there is nothing to observe: `Settings.Global`
     * has a content observer but Shizuku's liveness does not, and a row that updated on a
     * different schedule from its neighbours would look broken. Every one of these can be
     * changed from outside the app — including from the system screens the manager links
     * out to — so the reads have to keep happening while it is open.
     */
    fun startWatching() {
        if (watchJob?.isActive == true) return

        watchJob = viewModelScope.launch {
            _shizukuLaunchPackage.value = resolveShizukuLaunchPackage()

            while (isActive) {
                _targetStates.value = getManualTargetStatesUseCase()

                delay(TARGET_POLL_MILLIS)
            }
        }
    }

    fun stopWatching() {
        watchJob?.cancel()

        watchJob = null
    }

    /**
     * The per-row switch. Writes, then re-reads immediately rather than waiting for the
     * next poll, so the switch settles on what actually happened instead of springing back
     * a moment later.
     */
    fun setTargetEnabled(target: ManualRevertTarget, enabled: Boolean) {
        // Shevery's service is not asked for, it is induced - see setSheveryService.
        if (target == ManualRevertTarget.Shizuku && isShevery.value) {
            setSheveryService(enabled = enabled)

            return
        }

        if (target == ManualRevertTarget.DisplayOverOtherApps) {
            setOverlayAccess(enabled = enabled)

            return
        }

        // ⚠ **Switching wireless debugging on mid-wait is a yes.** The latch it sets is what
        // decides whether the row goes back on once Shevery comes up, and it combines with the
        // reading taken when Shevery was pressed rather than replacing it. Only the on
        // direction: Shevery switches that row off itself on the way up, and nothing here can
        // tell its write from a person's.
        if (target == ManualRevertTarget.WirelessDebugging && enabled) {
            sheveryStartTracker.noteWirelessTurnedOn()
        }

        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
            recordManualChangeUseCase(
                target = target,
                currentlyEnabled = _targetStates.value.isEnabled(target),
            )

            // ⚠ **A fork start moves wireless debugging on its way up**, whichever fork it
            // is, because it brings the debugging transport with it. Recorded before the write
            // and put back after, and the row is held meanwhile - the author's rule after
            // watching a start switch it off underneath him.
            val startingService = target == ManualRevertTarget.Shizuku && enabled

            val wirelessBefore =
                _targetStates.value.isEnabled(ManualRevertTarget.WirelessDebugging)

            if (startingService) _serviceStarting.value = true

            // ⚠ **The same countdown Shevery uses, because only one start can be running.**
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
                    ticker?.cancel()

                    sheveryStartTracker.clear()

                    withContext(NonCancellable) {
                        settleWirelessAfterStart(before = wirelessBefore)
                    }

                    _serviceStarting.value = false
                }
            }

            // Only for a switch being turned *off*, which is this screen hiding a
            // setting — the direction the author's rule is about. A row that will not
            // come back on has its own causes, and the revert paths already report them.
            if (!written && !enabled &&
                !secureSettingsWrapper.hasWriteSecureSettingsPermission()
            ) {
                _permissionsLost.value = true
            }

            _targetStates.value = getManualTargetStatesUseCase()
        }
    }

    /**
     * The master pill: every row the dialog says is usable, moved together.
     *
     * ⚠ **The dialog supplies [targets], and that is deliberate.** It is the thing that knows
     * which rows are operable right now — an unconfigured Shizuku, an unmanaged accessibility
     * selection, an overlay write in flight — and the pill's whole promise is that it moves
     * exactly the rows the user could have moved by hand. Recomputing that test here would be
     * a second answer to a question that already has one.
     *
     * ⚠ **Wireless debugging is written last on the way on, and first on the way off.**
     * Starting a Shizuku fork brings the debugging transport up using its own
     * WRITE_SECURE_SETTINGS, so a wireless debugging value settled before that start is one
     * the fork can overrule; settling it afterwards makes the user's press the final word.
     * The rest of the order follows the same dependency: developer options before USB
     * debugging, Shizuku before Display over other apps whose AppOps can only be written
     * while it is alive, and the exact reverse on the way off.
     *
     * ⚠ **`All on` leaves wireless debugging alone unless the user has asked for it back.**
     * `restoreWirelessDebugging` is read under both unhiding frameworks here, on the author's
     * instruction: this is the one press that could otherwise put wireless debugging back
     * without going anywhere near the setting that governs it.
     *
     * On the application scope, like every other write here: this dialog is often shown from
     * a tile or a shortcut, where dismissing it takes the ViewModel with it.
     */
    fun setAllTargets(enabled: Boolean, targets: List<ManualRevertTarget>) {
        if (targets.isEmpty()) return

        appScope.launch {
            val userData = userDataRepository.userData.first()

            // In :domain:model, where the host tests can assert it still covers every
            // target - see masterPillOnOrder for why the order is what it is.
            val ordered = masterPillOrder(enabled = enabled, usable = targets)

            for (target in ordered) {
                if (enabled &&
                    target == ManualRevertTarget.WirelessDebugging &&
                    !userData.restoreWirelessDebugging
                ) {
                    continue
                }

                // Read per target rather than once, because the writes above this one move
                // the device — starting Shizuku most of all — and a stale reading would
                // record a value that was already gone.
                val before = getManualTargetStatesUseCase()

                recordManualChangeUseCase(
                    target = target,
                    currentlyEnabled = before.isEnabled(target),
                )

                if (before.isEnabled(target) == enabled) continue

                setManualTargetUseCase(target = target, enabled = enabled, manual = enabled)
            }

            _targetStates.value = getManualTargetStatesUseCase()
        }
    }

    fun dismissPermissionsLost() {
        _permissionsLost.value = false
    }

    /**
     * Moves overlay access from the manager, and leaves nothing else moved.
     *
     * Either direction is one write, but neither can happen without Shizuku running, and
     * starting a fork turns the debugging transport on as a side effect. So the states of
     * everything a start disturbs are read first and written back afterwards: the user pressed
     * one switch, and one switch is all that should end up different.
     *
     * Both directions, not only the restore. This row now reads "on" whenever nothing is being
     * held - which is the honest answer, since a failed Shizuku query says nothing about
     * whether apps hold the permission - so a user with Shizuku stopped is far more likely to
     * press it *off*. Without the start, that press would fail silently and spring back.
     *
     * On the application scope rather than [viewModelScope]: this dialog is often opened from
     * a tile or a shortcut, where dismissing it finishes the activity and takes the ViewModel
     * with it, and a half-finished write is the one outcome worth avoiding here.
     */
    private fun setOverlayAccess(enabled: Boolean) {
        if (_overlayWriteInFlight.value) return

        appScope.launch {
            _overlayWriteInFlight.value = true

            try {
                val before = getManualTargetStatesUseCase()

                val disturbed = listOf(
                    ManualRevertTarget.DeveloperSettings,
                    ManualRevertTarget.UsbDebugging,
                    ManualRevertTarget.WirelessDebugging,
                    ManualRevertTarget.Shizuku,
                )

                val previous = disturbed.associateWith { before.isEnabled(it) }

                if (!before.isEnabled(ManualRevertTarget.Shizuku)) {
                    setManualTargetUseCase(ManualRevertTarget.Shizuku, enabled = true)
                }

                // The runner on the way back, because it also clears or reposts the retry
                // notification; a plain write on the way out, which has no notification.
                if (enabled) {
                    overlayRestoreRunner.retry(manual = true)
                } else {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.DisplayOverOtherApps,
                        enabled = false,
                    )
                }

                val after = getManualTargetStatesUseCase()

                // Reverse order, so Shizuku is stopped before the transport it rode in on is
                // taken away, and developer options goes last for the same reason it does
                // everywhere else in the app.
                for (target in disturbed.reversed()) {
                    val wanted = previous.getValue(target)

                    if (after.isEnabled(target) != wanted) {
                        setManualTargetUseCase(target = target, enabled = wanted)
                    }
                }

                _targetStates.value = getManualTargetStatesUseCase()
            } finally {
                _overlayWriteInFlight.value = false
            }
        }
    }

    /**
     * Puts the device back into the configured default, then closes.
     *
     * On the application scope, not [viewModelScope]: the dialog dismisses itself on the
     * press — and when it was opened from the tile or the shortcut, dismissing finishes the
     * activity and takes this ViewModel with it.
     */
    fun revertToDefault() {
        // Through the hidden runner, which settles every outstanding debt and ends the auto
        // unhide session before driving the defaults. It is the one that passes `explicit`, so
        // the toast still says "reverted" rather than "restored".
        appScope.launch { settingsHiddenRunner.revertToDefault() }
    }

    /**
     * Clears the recorded failure when the dialog closes.
     *
     * The red switch is a report on the last attempt, and it has now been delivered — the
     * user has seen it and can act on it. Leaving it set would greet them with the same red
     * switch every time they opened the dialog until they happened to retry, long after it
     * described anything current.
     *
     * On the application scope because this runs as the dialog is being dismissed, which for
     * the tile and the shortcut also finishes the activity holding this ViewModel.
     */
    fun acknowledgeShizukuFailure() {
        appScope.launch {
            if (shizukuStartFailed.value) {
                userDataRepository.updateShizukuStartFailed(failed = false)
            }
        }
    }

    private suspend fun resolveShizukuLaunchPackage(): String? {
        val userData = userDataRepository.userData.first()

        return packageManagerWrapper.findLaunchablePackage(
            preferredPackage = userData.shizukuPackageName,
            labels = listOf(
                ShizukuForkDefaults.SHIZUKU_LABEL,
                ShizukuForkDefaults.SHEVERY_LABEL,
            ),
        )
    }

    override fun onCleared() {
        stopWatching()

        super.onCleared()
    }
}

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
