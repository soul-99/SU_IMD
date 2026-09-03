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
package com.android.geto.domain.usecase

import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.deviceWideSnapshotId
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.overlayAlreadyWithdrawn
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Switches off whatever the "Settings to hide" configuration names, for any app.
 *
 * The counterpart to [ApplyAppSettingsUseCase], which reads a profile written for one
 * specific app. This one reads a single device-wide configuration, so an app that has
 * never been configured can still be launched — which is the whole reason it exists.
 *
 * Returns an [AppSettingsResult] rather than a type of its own so it can be dropped into
 * the launch paths that already exist. Two of that type's cases cannot arise here and are
 * never returned: there is no per-app profile to be empty, and no per-app row to be
 * disabled. A configuration with nothing ticked is [AppSettingsResult.NothingToHide] and
 * the launch does not happen: since v2.1 that is the state a fresh install starts in, so
 * treating it as "the user wants nothing hidden" would silently turn the app into a
 * launcher for everybody who had not configured it yet.
 *
 * **A failed overlay step leaves the device alone.** Overlay access is the only target here
 * whose failure cancels the launch, and it is dealt with before anything else is touched, so
 * a failure returns with nothing hidden. Half-hidden is the worst outcome available on this
 * side: the app still detects whatever is left on and refuses to run, while the user's device
 * has been changed anyway — and when the launch is cancelled outright they are left in front
 * of a dialog with their settings switched off for an app that never opened.
 *
 * The revert direction takes the opposite rule for the same reason, and [RevertToDefaultUseCase]
 * says so: on the way out, putting four settings of five back is strictly better than none.
 */
class ApplySettingsToHideUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val stopShizukuServiceUseCase: StopShizukuServiceUseCase,
    private val disableAutoHideServiceUseCase: DisableAutoHideServiceUseCase,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    // Tracked from the outside in, so the Hide settings tile is unavailable for the whole
    // of this and not only for the part that writes - the Shizuku start inside a hide is
    // ten seconds during which a second press must not land. See SettingsWorkTracker.
    suspend operator fun invoke(): AppSettingsResult = settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
        withContext(defaultDispatcher) {
            // Half-hidden is the worst outcome available: the app still detects whatever is
            // left on and refuses to run, while the user's device has been changed anyway.
            // Launching an activity is exactly the sort of thing that tears this scope down.
            withContext(NonCancellable) { hide() }
        }
    }.also { Diagnostics.log(tag = "hide", message = "device-wide -> $it") }
        // See ApplyAppSettingsUseCase: only a hide that landed marks the process.
        .also { if (it == AppSettingsResult.Success) PriorHide.markHidden() }

    private suspend fun hide(): AppSettingsResult {
        val userData = userDataRepository.userData.first()

        // Effective rather than stored: with "Manage Display over other apps" off in
        // Advanced the overlay entry reads false whatever was ticked while it was on, so
        // neither the Shizuku pre-start below nor the hide loop can act on it.
        val wanted = userData.effectiveSettingsToHide

        // Nothing ticked. Since v2.1 that is where every fresh install starts, so this is the
        // ordinary state of an app nobody has configured rather than an exotic one - and
        // launching from here would open the app with everything it objects to still on,
        // which reads as this app being broken. Reported instead, so the launch paths can say
        // what is missing and where to set it.
        if (wanted.none { it.value }) return AppSettingsResult.NothingToHide

        // Auto-hide settings (IMD+) is already holding the device down with this very list, so
        // there is nothing left for this launch to hide. Reported apart from Success because
        // the difference is the notification: this launch creates no debt, and posting "settings
        // hidden, tap to revert" would offer to undo IMD+'s run from a button that does not
        // know how - while IMD+'s own notification, which does, is already on screen.
        if (userData.autoHideRunning) return AppSettingsResult.AlreadyHidden

        // ⚠ **The force-close gate.** Settings are down and no hide in this process put them
        // there, so the process that did is gone and its revert notification went with it.
        // Nothing is written and nothing is launched — the caller shows the popup, and the user
        // chooses between putting the old state back and letting go of it.
        //
        // Suppressed here rather than by each caller: IMD+ draws its dialog over the app the
        // user just opened, which is itself a window change its detector sees, so a dialog
        // nobody has answered yet would put another one up behind it.
        if (PriorHide.shouldWarn(settingsHidden = userData.settingsHidden)) {
            PriorHide.suppress()

            return AppSettingsResult.HiddenFromPreviousUse
        }

        // ⚠ **The grant is checked before anything is touched, and that ordering is the whole
        // design.** Without `WRITE_SECURE_SETTINGS` not one of the writes below can land, and
        // the permission that switches a setting off is the same one needed to switch it back
        // on — so a hide that discovers the loss halfway can undo almost nothing it has done.
        // Asking first means the ordinary case never gets into that state: nothing is hidden,
        // nothing needs reverting, and the caller has an outcome it can name out loud.
        //
        // Below the two checks above on purpose. With nothing ticked, or with IMD+ already
        // holding the device down, the permission is beside the point and those are the truer
        // answers.
        //
        // The loop still re-checks, for the grant that goes away *during* a run. That is rare
        // enough to be nearly theoretical and is handled where it can be handled properly.
        if (!secureSettingsWrapper.hasWriteSecureSettingsPermission()) {
            return AppSettingsResult.NoPermission
        }

        var before = getManualTargetStatesUseCase()

        // Read now, before the overlay step below starts a fork - which brings the debugging
        // transport up with it and would make this read "on" for a device the user had left
        // with USB debugging off. It decides whether the Shizuku fallback is allowed to put
        // USB debugging back at all: restoring a setting that was never on would be this app
        // enabling debugging by itself, with nothing recording that it did.
        val usbInitiallyOn = before.isEnabled(ManualRevertTarget.UsbDebugging)

        // ⚠ **And the same reading for wireless debugging, for the same reason** — since spec
        // item 7 the stop drops both transports, so both have to be put back only where they
        // were. Taken from the same snapshot, before anything below moves either of them.
        val wirelessInitiallyOn = before.isEnabled(ManualRevertTarget.WirelessDebugging)

        // ⚠ **The device-wide memory record, and it has to be taken here.** Under
        // UnhidingFramework.Memory a device-wide hide is put back to what was actually there
        // rather than to the configured defaults, so the "actually there" has to be measured
        // before anything below moves it — and in particular before the overlay step starts a
        // fork, which brings the debugging transport up and would have this record every
        // debugging setting as though the user had left it on.
        //
        // Kept in settingStateBefore under DEVICE_WIDE_HOLD rather than in a proto field of
        // its own: the map already exists, already survives a force close, and already has a
        // reserved key for exactly this holder — see deviceWideMemoryWanted, and MemoryHolds
        // for why that key must stay out of the per-app sweep.
        if (userData.unhidingFramework == UnhidingFramework.Memory) {
            recordDeviceWideValues(wanted = wanted, before = before, userData = userData)
        }

        val hidingOverlay = wanted[ManualRevertTarget.DisplayOverOtherApps] == true

        // What this particular run has changed, so that a grant lost partway through can be
        // undone rather than left standing. Only what *this* run did: a device that was
        // already part-hidden by something else owes its debt to whatever hid it.
        var overlayWithdrawnHere = false

        var shizukuStoppedHere = false

        val switchedOffHere = mutableListOf<ManualRevertTarget>()

        // The repeat-launch fail-safe - see overlayAlreadyWithdrawn for why it reads this
        // app's own record rather than asking Shizuku. Without it a second launch, with the
        // device already hidden, spends up to ten seconds starting Shizuku to write a
        // withdrawal that withdraws nothing, then stops it again - which can fall back to
        // cycling USB debugging and raise a warning about it. Twenty seconds and an alarming
        // notification, for no change to the device.
        val overlayAlreadyWithdrawn = overlayAlreadyWithdrawn(
            managedOverlayPackages = userData.managedOverlayPackages,
            heldOverlayPackages = userData.heldOverlayPackages,
        )

        // The whole overlay step, before any other setting is touched, and every way it can
        // fail returns here rather than falling through to the loop.
        //
        // That is the point of pulling it out. Overlay access is the only target whose
        // failure cancels the launch, so once it has failed the app is not opening - and
        // every setting the loop would have gone on to switch off is then a change to the
        // user's device made for an app that never appeared. They are left looking at a
        // dialog with developer options, debugging and their accessibility services all
        // switched off and nothing obviously connecting the two.
        //
        // It used to be the loop's first item, which came to the same thing on the way in
        // but not on the way out. Doing it here also stops the guarantee resting on
        // SettingsToHide.HideOrder happening to list it first.
        if (hidingOverlay && !overlayAlreadyWithdrawn) {
            // Started while the debugging transport is still available; the hide loop below
            // is what switches that transport, and therefore Shizuku, back off.
            //
            // The start is announced to the tracker so the launch can put a spinner over
            // itself: StartShizukuUseCase waits up to ten seconds for a fork to come up, and
            // ten silent seconds between tapping an app and it opening reads as a hang.
            if (!before.isEnabled(ManualRevertTarget.Shizuku)) {
                shizukuStartTracker.beginOverlay(OverlayStart.Hide)

                val started = try {
                    setManualTargetUseCase(target = ManualRevertTarget.Shizuku, enabled = true)
                } finally {
                    shizukuStartTracker.endOverlay(OverlayStart.Hide)
                }

                // A fork that will not come up because the grant went away in the last few
                // seconds is not a Shizuku problem, and saying "Shizuku would not start" would
                // send the user to fix the wrong thing: starting one needs the debugging
                // transport, and writing that needs the permission. Nothing has changed at
                // this point — the start failed — so there is nothing to put back.
                if (!started) {
                    return if (secureSettingsWrapper.hasWriteSecureSettingsPermission()) {
                        AppSettingsResult.OverlayFailure
                    } else {
                        AppSettingsResult.NoPermission
                    }
                }
            }

            // Attempted even when the live state says overlay access is already withdrawn.
            // That reading comes from a Shizuku query, and a query that could not be
            // answered reads as "nothing is allowed" - so trusting it would skip the write
            // and leave overlays on while reporting success.
            val hidden = setManualTargetUseCase(
                target = ManualRevertTarget.DisplayOverOtherApps,
                enabled = false,
            )

            if (!hidden) {
                return if (secureSettingsWrapper.hasWriteSecureSettingsPermission()) {
                    AppSettingsResult.OverlayFailure
                } else {
                    AppSettingsResult.NoPermission
                }
            }

            overlayWithdrawnHere = true

            // Starting a fork brings the debugging transport up with it, so the snapshot
            // taken above has stopped describing the device. Read again before deciding
            // which of the remaining targets are "already off": against the stale copy,
            // developer options and USB debugging that Shizuku had just switched on still
            // read as off, were skipped as nothing to do, and the app opened with both of
            // them plainly visible to it.
            before = getManualTargetStatesUseCase()
        }

        // Stop the Shizuku service if the configuration asks for it, before the loop below
        // starts switching off the transport it rides on. The overlay step above may have
        // just started it to hide Display over other apps; either way, once that is done its
        // work here is over. Handled on its own terms — a graceful stop first, USB debugging
        // cycled as a fallback — and then skipped in the loop, exactly like the overlay.
        if (wanted[ManualRevertTarget.Shizuku] == true) {
            stopShizukuServiceUseCase(
                // Put back only if it was on to start with and this run is not hiding it.
                usbFinalEnabled = usbInitiallyOn &&
                    wanted[ManualRevertTarget.UsbDebugging] != true,
                // ⚠ **The same question for wireless debugging, and it needs its own answer.**
                // Spec item 7 drops both transports, so both have to be put back deliberately
                // — and IMD's own rule is that it does not restore wireless debugging unless
                // asked, which `restoreWirelessDebugging` is. A hide that is not hiding
                // wireless debugging must still leave it exactly as it found it.
                wirelessFinalEnabled = wirelessInitiallyOn &&
                    wanted[ManualRevertTarget.WirelessDebugging] != true,
            )

            shizukuStoppedHere = true

            // Stopping Shizuku changed the device again — and may have cycled USB debugging —
            // so the snapshot the loop reads "already off" from has to be taken afresh.
            before = getManualTargetStatesUseCase()
        }

        var failed = false

        for (target in SettingsToHide.HideOrder) {
            // Done above, each on its own terms.
            if (target == ManualRevertTarget.DisplayOverOtherApps) continue
            if (target == ManualRevertTarget.Shizuku) continue

            if (wanted[target] != true) continue

            // Already off. Writing it again is not harmless: for the accessibility
            // services target a second disable would record a fresh hold over services
            // that are already held, and nothing would ever discharge the duplicate.
            if (target != ManualRevertTarget.AccessibilityServices &&
                !before.isEnabled(target)
            ) {
                continue
            }

            if (setManualTargetUseCase(target = target, enabled = false)) {
                switchedOffHere += target

                continue
            }

            // A refused write is the moment to ask whether the grant is still there. It is
            // the difference between "this one row would not move" — which is a partial hide,
            // and leaves a debt a revert can settle — and "nothing can be written any more",
            // which is not a hide at all and has to be undone rather than recorded.
            if (!secureSettingsWrapper.hasWriteSecureSettingsPermission()) {
                revertPartialHide(
                    overlayWithdrawnHere = overlayWithdrawnHere,
                    shizukuStoppedHere = shizukuStoppedHere,
                    switchedOffHere = switchedOffHere,
                )

                return AppSettingsResult.NoPermission
            }

            failed = true
        }

        // IMD's own IMD+ detector goes off with every hide, whatever the accessibility
        // target says. It is not one of the services the user picks from: a detector left
        // listening while settings are hidden would be the one accessibility service still
        // reading the device that the hide exists to quieten, and on a launch it would react
        // to the very app IMD is about to open. Recorded as an ordinary hold, so a revert to
        // default - or the last of the pending memory reverts - puts it back with the rest.
        //
        // Below the early returns on purpose: a hide that found nothing to do, or gave up at
        // the overlay step, has changed nothing and owes nothing.
        runCatching { disableAutoHideServiceUseCase() }

        // Recorded here rather than by whatever asked for the hide, so that a launch, an
        // automation intent and the tile all leave the same mark - and so the tile can show
        // "hidden" for a hide it had nothing to do with. Written on a partial failure too:
        // some of it landed, there is a debt outstanding, and a revert is still owed.
        //
        // Every early return above is a run that changed nothing, and none of them reach
        // this line: an overlay failure gives up before touching anything else, and nothing
        // ticked never had anything to do.
        runCatching { userDataRepository.updateSettingsHiddenDeviceWide(hidden = true) }

        return if (failed) AppSettingsResult.Failure else AppSettingsResult.Success
    }

    /**
     * Measures what the keyed targets held before this hide, for a device-wide memory revert.
     *
     * Merge-preserving, the same discipline as the per-app `recordCurrentValues`: an id that is
     * already recorded is left alone, so a second device-wide hide taken while the first is
     * still outstanding cannot overwrite the original reading with the value this app wrote.
     * Without that, the tile pressed twice would record "off" as the state to restore.
     *
     * Only targets this run is actually going to switch off are measured. A target the user
     * has not ticked is not this hide's business, and recording it would have the revert drive
     * a setting the hide never touched.
     */
    private suspend fun recordDeviceWideValues(
        wanted: Map<ManualRevertTarget, Boolean>,
        before: ManualTargetStates,
        userData: UserData,
    ) {
        val existing = userData.settingStateBefore[AccessibilityServicePlan.DEVICE_WIDE_HOLD]
            .orEmpty()

        val measured = mutableMapOf<String, String?>()

        for (target in ManualRevertTarget.entries) {
            if (wanted[target] != true) continue

            val id = deviceWideSnapshotId(target = target) ?: continue

            if (id in existing) continue

            // ⚠ **The first-owner rule**, in its device-wide shape. A device-wide hide always
            // drives its targets off, so "not already at the value about to be written" reads
            // here as "not already off" — and a target that is already off is one somebody else
            // is holding down, or one the user never had on. Either way this hide does not owe
            // putting it back. See `hideOwnsRevert`.
            if (!before.isEnabled(target)) continue

            measured[id] = "1"
        }

        if (measured.isEmpty()) return

        userDataRepository.updateSettingStateBefore(
            states = userData.settingStateBefore +
                (
                    AccessibilityServicePlan.DEVICE_WIDE_HOLD to
                        SettingSnapshot.merge(existing = existing, measured = measured)
                    ),
        )
    }

    /**
     * Puts back what this run had already switched off when the grant went away underneath it.
     *
     * **The rare half of a rare case.** The permission is checked before the hide begins, so
     * the only way to arrive here is for it to be revoked in the second or two the hide takes.
     * What makes it worth writing anyway is what would otherwise be left behind: nothing
     * records the hide — `settingsHiddenDeviceWide` is written after the loop and this returns
     * before it — so the tile would go on reading "Settings visible" over a device with
     * Display over other apps withdrawn and no button anywhere offering to put it back. That
     * is the one outcome this app is built to never produce.
     *
     * **In the reverse of the order it hid them**, which is [SettingsToHide.HideOrder] read
     * backwards: developer options went off last and so comes back first, because everything
     * underneath it is meaningless while it is off.
     *
     * The settings writes here will almost certainly fail — they need the very permission that
     * has just gone — and they are attempted regardless, because "almost certainly" is not
     * "certainly" and a write that is refused changes nothing. The two that can genuinely
     * succeed are the ones that do not use it: Shizuku and, through Shizuku, Display over other
     * apps. Restarting a fork costs up to ten seconds and is spent without hesitation — the
     * alternative is leaving overlay access withdrawn with nothing left that knows to restore
     * it.
     *
     * ⚠ **One known imprecision, left deliberately.** Restoring [ManualRevertTarget
     * .AccessibilityServices] releases *every* hold on the services rather than only the one
     * this run took, so on a device that some earlier hide had already part-hidden this hands
     * back more than it took. That is the safe direction to be wrong in — it errs towards the
     * user's services being switched back on rather than left off with nothing left running
     * that knows to restore them — and unpicking one run's hold from another's would be real
     * machinery built for a case that needs a permission to vanish inside a two-second window.
     */
    private suspend fun revertPartialHide(
        overlayWithdrawnHere: Boolean,
        shizukuStoppedHere: Boolean,
        switchedOffHere: List<ManualRevertTarget>,
    ) {
        Diagnostics.log(
            tag = "hide",
            message = "grant lost mid-run, undoing overlay=$overlayWithdrawnHere " +
                "shizuku=$shizukuStoppedHere targets=${switchedOffHere.map { it.name }}",
        )

        for (target in SettingsToHide.HideOrder.reversed()) {
            if (target !in switchedOffHere) continue

            runCatching { setManualTargetUseCase(target = target, enabled = true) }
        }

        // Before the overlay, not after: withdrawing it went through Shizuku, so putting it
        // back needs Shizuku running again. Skipped when this run left it alone, so a device
        // whose owner keeps Shizuku stopped is not handed a running one by a failed hide.
        if (shizukuStoppedHere) {
            runCatching {
                setManualTargetUseCase(target = ManualRevertTarget.Shizuku, enabled = true)
            }
        }

        if (overlayWithdrawnHere) {
            runCatching {
                setManualTargetUseCase(
                    target = ManualRevertTarget.DisplayOverOtherApps,
                    enabled = true,
                )
            }
        }
    }
}
