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
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.RevertToDefaultResult
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.deviceWideSnapshotId
import com.android.geto.domain.model.effectiveRevertDefaults
import com.android.geto.domain.model.memoryHeldComponents
import com.android.geto.domain.model.settingsOutsideRevertDefaults
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Drives every target to the state saved in the "Revert to default" configuration.
 *
 * Where [RevertAppSettingsUseCase] undoes what one app changed, this one ignores apps
 * entirely and puts the device into the state the user nominated as normal. That makes it
 * the answer to "I do not know what is switched off any more" — which is a different
 * question from "undo that app", and one the per-app revert cannot answer once its
 * notification has been swiped away.
 *
 * Targets already in the wanted state are left alone rather than written again. That is not
 * only about avoiding pointless writes: re-broadcasting a start to a Shizuku that is already
 * running is the kind of thing that shows up as a mystery service restart later.
 *
 * **Every target is attempted, whatever the ones before it did.** Overlay access is written
 * first because it is the only step that needs Shizuku running, and it is also the only step
 * that can fail for reasons outside this app - the service is not running, the permission was
 * revoked, the binder died. None of that says anything about the four settings this app can
 * write itself, so a failed overlay step records itself and the revert carries on. The result
 * reports what worked, what did not, and whether overlay access is still owed, and the caller
 * raises the failure notification from that - after the revert, never instead of it.
 *
 * The one thing that is *not* attempted twice is starting Shizuku. If the overlay step asked
 * for it and it did not come up, the final settle-Shizuku step does not ask again: the answer
 * arrived ten seconds ago and nothing in between can have changed it. That start is recorded
 * as failed instead, so one refusal is reported as one problem rather than as two.
 */
class RevertToDefaultUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val restoreAutoHideServiceUseCase: RestoreAutoHideServiceUseCase,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val settingsWorkTracker: SettingsWorkTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    // Tracked from the outside in, so the Hide settings tile is unavailable for the whole
    // of this. A revert is the longest thing this app does; it is also the one a stray tile
    // press would most like to interrupt. See SettingsWorkTracker.
    /**
     * [wantedOverride] replaces the configured *Revert to default configuration* as the state
     * every target is driven to.
     *
     * The one caller that passes it is the device-wide **memory** revert: under
     * [UnhidingFramework.Memory] a device-wide hide has to be put back to what was actually
     * there, not to a configuration the user may never have looked at. Everything else about
     * a revert is identical — the same order, the same overlay restore, the same Shizuku
     * settling last — so this supplies a different destination rather than duplicating a
     * hundred lines that already get that ordering right.
     *
     * ⚠ **The explicit `Revert to default` routes must never pass it.** The tile, the
     * shortcut, the settings manager, the Favourites button and the intent are a named
     * function that always drives the configured defaults, on the author's instruction.
     */
    suspend operator fun invoke(
        wantedOverride: Map<ManualRevertTarget, Boolean>? = null,
    ): RevertToDefaultResult = settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {
        withContext(defaultDispatcher) {
            // A half-applied revert is worse than none — developer options on with USB
            // debugging still off is a state the user did not ask for and cannot see. A tile
            // press whose service is torn down mid-run must not be able to leave that behind.
            withContext(NonCancellable) { revert(wantedOverride = wantedOverride) }
        }
    }.also { Diagnostics.log(tag = "revert", message = "device-wide -> $it") }

    private suspend fun revert(
        wantedOverride: Map<ManualRevertTarget, Boolean>?,
    ): RevertToDefaultResult {
        val userData = userDataRepository.userData.first()
        // Effective rather than stored: with "Manage Display over other apps" off in
        // Advanced the overlay entry is absent unless a debt is outstanding, in which case
        // it reads true. Turning the feature off stops IMD taking overlay access away; it
        // does not abandon access already taken.
        // ⚠ **The override speaks only for what it can measure.** `deviceWideMemoryWanted`
        // builds it by walking the targets and skipping any without a `deviceWideSnapshotId`,
        // so it can only ever carry Developer settings, USB debugging and Wireless debugging.
        // Accessibility services and Shizuku keep holds of their own and overlay access has no
        // "before" value at all, because switching it off is a broadcast.
        //
        // Until r4g the override was used as the whole destination, so those three fell out of
        // every read below - `wanted[target] ?: continue` in the ordinary loop, a null
        // `overlayEnabled` that skips the overlay block *and* its `unchanged` branch, and a
        // `wanted[Shizuku]?.let` that never runs. The author's log: a device-wide memory revert
        // reporting `changed=[DeveloperSettings, UsbDebugging, WirelessDebugging]` and nothing
        // else, on a device that had all six hidden.
        //
        // ⚠ **Filtered by "can this target be recorded at all", not by "was it recorded this
        // time".** A keyed target absent from the record is a setting the hide never touched,
        // and driving that to a configuration the user may never have looked at is the thing
        // the memory framework exists to avoid. A target with no snapshot id is absent because
        // it *cannot* be present, and the configured default is the only answer there is.
        val configured = if (wantedOverride != null) {
            userData.effectiveRevertDefaults
                .filterKeys { deviceWideSnapshotId(target = it) == null } + wantedOverride
        } else {
            userData.effectiveRevertDefaults
        }

        // ⚠ **A memory restore does not switch wireless debugging back on unless asked to.**
        // The author's rule, and the device-wide half of it — the per-app half is the same
        // filter in RevertAppSettingsUseCase.
        //
        // `wantedOverride != null` is the memory test rather than the stored framework, and
        // deliberately: that parameter has exactly one caller, the device-wide memory revert,
        // while an explicit `Revert to default` never passes it and must keep driving its own
        // configuration whatever framework happens to be selected.
        //
        // Dropped from the map rather than forced false: the loop below reads
        // `wanted[target] ?: continue`, so an absent entry is left exactly as the device has
        // it. Only the *on* direction is dropped — a memory record asking for it to be
        // switched off still switches it off.
        val wanted = if (
            wantedOverride != null &&
            !userData.restoreWirelessDebugging &&
            configured[ManualRevertTarget.WirelessDebugging] == true
        ) {
            configured - ManualRevertTarget.WirelessDebugging
        } else {
            configured
        }

        // ⚠ **The extras, and they go first.** A per-app profile can hide any setting by key,
        // while this revert drives only the six ManualRevertTargets — three of which name a
        // global setting at all. Anything a profile hid outside those is invisible to
        // everything below and would be left switched off with nothing that clears it.
        //
        // Restoring only what the defaults cannot reach, rather than flushing every pending
        // revert and then driving the defaults, is the author's design and the better one:
        // the two sets are disjoint by construction, so no setting is written twice — and
        // adb_enabled is one of the three, so the flush-then-drive version would have a
        // Shizuku user watch the service start on the restore and stop again on the defaults,
        // twice over the fork's start wait.
        //
        // First rather than last because the block below deliberately ends by settling
        // Shizuku and debugging into their configured state, and appending ordinary secure
        // writes after the step designed to be last is how ordering bugs start.
        restoreSettingsOutsideDefaults(userData = userData)

        var before = getManualTargetStatesUseCase()

        // The state the device was actually in when the user asked for a revert. Kept
        // separately because starting Shizuku moves the debugging settings on its own, and
        // reporting that as a change the user asked for would be a lie.
        val initial = before

        val changed = mutableSetOf<ManualRevertTarget>()
        val failed = mutableSetOf<ManualRevertTarget>()
        val unchanged = mutableSetOf<ManualRevertTarget>()

        var overlayRestoreFailed = false

        /**
         * Whether the overlay step asked Shizuku to start and it did not come up.
         *
         * The overlay step is the only thing in a revert that starts Shizuku, so it is the
         * only place that can find out a start does not work on this device today. What it
         * learns is worth carrying to the end: the last thing a revert does is settle Shizuku
         * to its configured state, and starting it there after this has already failed is a
         * second ten second wait for the same answer.
         */
        var shizukuStartRefused = false

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

        suspend fun applyTarget(target: ManualRevertTarget, enabled: Boolean) {
            if (before.isEnabled(target) == enabled) {
                if (target !in changed) unchanged += target

                return
            }

            if (setManualTargetUseCase(target = target, enabled = enabled)) {
                changed += target
                failed -= target
                unchanged -= target
            } else {
                failed += target
            }
        }

        val ordinaryTargets = listOf(
            ManualRevertTarget.DeveloperSettings,
            ManualRevertTarget.UsbDebugging,
            ManualRevertTarget.WirelessDebugging,
            ManualRevertTarget.AccessibilityServices,
        )

        val overlayTarget = ManualRevertTarget.DisplayOverOtherApps
        val overlayEnabled = wanted[overlayTarget]
        val hasOverlayDebt = userData.heldOverlayPackages.isNotEmpty()
        // Disabling is always attempted: a failed Shizuku query reads as off in the live
        // state, and treating that as authoritative would silently leave overlays allowed.
        // Enabling only restores IMD's persisted debt and cannot grant anything new.
        //
        // Except with nothing selected, where "keep it hidden" has nobody to hide it from.
        // The write itself is a no-op there, but reaching it costs up to ten seconds of
        // starting Shizuku - on every revert, on a device that has never used the feature.
        // A debt still owed is a different matter and always restored, however the selection
        // has changed since.
        val overlayNeedsWrite =
            (overlayEnabled == false && userData.managedOverlayPackages.isNotEmpty()) ||
                (overlayEnabled == true && hasOverlayDebt)

        // Start Shizuku, write overlay access, write everything else, settle Shizuku last.
        //
        // Overlay AppOps can only be written while Shizuku is running, so the start comes
        // first. Nothing is done to the debugging settings to make that possible: a Shizuku
        // fork brings its own transport up when it starts, using its own
        // WRITE_SECURE_SETTINGS, so forcing developer options and debugging on here would
        // only be switching things the user did not ask for and then switching them back.
        //
        // Everything else is written after that start, not before, because the start does
        // move the debugging settings. Writing them last is what makes the user's configured
        // state the final word rather than something a fork overrode on its way up.
        if (overlayNeedsWrite) {
            // Wrapped whole, and this is the point of the wrapping: everything below this
            // block is the rest of the revert, and it has to happen whether or not overlay
            // access could be dealt with. Overlay is the one step that depends on a service
            // outside this app, so it is the one step that can fail in ways nothing here
            // predicts - and a throw escaping it would abandon four settings the app could
            // perfectly well have put back, and skip the notification too, since the caller
            // never reaches the line that raises one.
            //
            // A throw is treated exactly like a refusal, because to the user they are the
            // same event: overlay access did not come back.
            val restored = runCatching {
                if (!before.isEnabled(ManualRevertTarget.Shizuku)) {
                    // A revert usually gives overlay access back, but a configuration that
                    // wants it hidden makes this the same wait in the other direction - and
                    // the spinner says whichever it is.
                    val reason = if (overlayEnabled == true) {
                        OverlayStart.Restore
                    } else {
                        OverlayStart.Hide
                    }

                    shizukuStartTracker.beginOverlay(reason)

                    try {
                        setManualTargetUseCase(ManualRevertTarget.Shizuku, enabled = true)
                    } finally {
                        shizukuStartTracker.endOverlay(reason)
                    }

                    before = getManualTargetStatesUseCase()

                    // Asked, waited, and it is still not there. Read from the device rather
                    // than from what the start returned, because a fork that comes up late
                    // is a success as far as this revert is concerned.
                    shizukuStartRefused = !before.isEnabled(ManualRevertTarget.Shizuku)
                }

                before.isEnabled(ManualRevertTarget.Shizuku) &&
                    setManualTargetUseCase(overlayTarget, enabled = overlayEnabled)
            }.getOrDefault(false)

            if (restored) {
                changed += overlayTarget
            } else {
                failed += overlayTarget

                // Only a failed *restore* leaves the device in a state the user has to be
                // told about: overlay access is still withdrawn from apps that had it, and
                // nothing else in this revert will put it back.
                if (overlayEnabled == true) {
                    overlayRestoreFailed = true

                    // Also best-effort. The flag decides whether a notification is raised
                    // later; failing to store it must not cost the user the settings writes
                    // that come after this block.
                    runCatching { userDataRepository.updateOverlayRestoreFailed(failed = true) }
                }
            }
        } else if (overlayEnabled != null) {
            unchanged += overlayTarget
        }

        before = getManualTargetStatesUseCase()

        // Everything backed by WRITE_SECURE_SETTINGS, now that the overlay work is done and
        // Shizuku is no longer needed. Starting Shizuku turns the debugging transport on
        // behind our back, so these have to be written after it rather than before, or the
        // start silently overrides the configuration the user actually asked for.
        for (target in ordinaryTargets) {
            val enabled = wanted[target] ?: continue

            if (before.isEnabled(target) != enabled &&
                !setManualTargetUseCase(target = target, enabled = enabled)
            ) {
                failed += target

                continue
            }

            if (initial.isEnabled(target) == enabled) {
                if (target !in changed) unchanged += target
            } else {
                changed += target
                failed -= target
                unchanged -= target
            }
        }

        // Shizuku last: whether it is left running is a decision about the end state, and
        // making it before the settings above are written would mean stopping a service the
        // overlay step may still have been using, then writing settings around the gap.
        before = getManualTargetStatesUseCase()

        wanted[ManualRevertTarget.Shizuku]?.let { enabled ->
            // A start that already failed once in this same revert is not attempted again.
            // The overlay step asked less than a minute ago and waited the full ten seconds
            // for an answer; nothing between then and here can have changed it, so a second
            // attempt only makes the user wait twice as long to be told the same thing.
            //
            // It is recorded as a failure rather than quietly skipped, and that is the point
            // of doing this at all: one failed start is one failure, and the user hears about
            // it once, in the toast that names both Shizuku and overlay access. Left to run,
            // the retry would have failed on its own account and reported a second problem
            // that was really the first one over again.
            //
            // Only when the configuration wants it *on*. "Leave Shizuku off" is satisfied by
            // a Shizuku that would not start, so that is an end state reached rather than a
            // failure, and applyTarget below records it as unchanged.
            if (!before.shizukuAvailable) {
                // The row now reports a service that is genuinely running even when IMD has
                // no Shizuku configuration, which is the common state for stock Shizuku - it
                // has no start or stop broadcasts to configure. Starting and stopping are
                // exactly what this step does, so with nothing to send there is no work here
                // and no failure either: reporting one would put a Shizuku error toast on
                // every revert for a service this app was never able to drive.
                unchanged += ManualRevertTarget.Shizuku
            } else if (shizukuStartRefused && enabled) {
                failed += ManualRevertTarget.Shizuku
            } else if (enabled && !before.isEnabled(ManualRevertTarget.Shizuku)) {
                // The one wait in a revert that nothing was announcing. Starting the service
                // takes the fork's whole budget, and when overlay access was never part of
                // this revert the overlay block above never ran - so the ten seconds passed
                // with no spinner at all, or, on a device that did write overlay AppOps, under
                // a spinner naming a setting this step is not touching. StartShizuku says the
                // plain thing: the service is coming up.
                shizukuStartTracker.beginOverlay(OverlayStart.StartShizuku)

                // Attempted, not succeeded: a fork that writes the transport on its way up and
                // then dies has still switched wireless debugging off.
                settleStartedShizuku = true

                try {
                    applyTarget(ManualRevertTarget.Shizuku, enabled)
                } finally {
                    shizukuStartTracker.endOverlay(OverlayStart.StartShizuku)
                }
            } else {
                applyTarget(ManualRevertTarget.Shizuku, enabled)
            }
        }

        // ⚠ **Wireless debugging once more, because the step above may have taken it away.**
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
        // attempted and each one that could be driven to its configured state now is, so
        // there is nothing left here for a later revert to put back - a failed target failed
        // because something outside this app refused, and repeating the same revert would
        // meet the same refusal. The failures are reported to the caller, which raises the
        // notification for them; leaving the flag set as a second way of saying so would
        // only leave the tile stuck on with no press able to clear it.
        //
        // Set here rather than in the callers because this use case has many: the
        // notification's button, the tile, the home-screen shortcut, an automation intent and
        // the services manager all end up here, and the tile has to follow every one of them.
        runCatching { userDataRepository.updateSettingsHiddenDeviceWide(hidden = false) }

        // Last of all: IMD's own IMD+ detector, which every hide switches off whatever the
        // accessibility target says. Switched back *on* rather than merely released when IMD+
        // is configured on - see RestoreAutoHideServiceUseCase. After the accessibility target
        // above, so the user's own services are back first and this cannot be undone by the
        // list that step writes.
        restoreAutoHideServiceUseCase()

        return RevertToDefaultResult(
            changed = changed,
            failed = failed,
            unchanged = unchanged,
            overlayRestoreFailed = overlayRestoreFailed,
        )
    }

    /**
     * Puts back the recorded settings this revert's own targets cannot reach.
     *
     * Walks every per-app record, keeps the ids [settingsOutsideRevertDefaults] says are
     * outside the six targets, and writes each one back to the value the hide measured.
     *
     * ⚠ **The ids that survive the filter are dropped from the record, and only those.** The
     * rest of each record is left exactly as it was, because it describes settings this revert
     * is about to drive and is cleared by whatever normally clears it. Dropping the whole
     * record here would take the accessibility and overlay claims with it, which have their
     * own lifecycle and are not this method's to end.
     *
     * A failed write is left recorded rather than dropped, on the same reasoning as
     * `RevertAppSettingsUseCase`: a record left behind after a failed revert is what lets a
     * retry still put the right value back.
     */
    private suspend fun restoreSettingsOutsideDefaults(userData: UserData) {
        val components = memoryHeldComponents(
            settingStateBefore = userData.settingStateBefore,
            heldAccessibilityServices = userData.heldAccessibilityServices,
        )

        var records = userData.settingStateBefore

        for (component in components) {
            val recorded = records[component] ?: continue

            val extras = settingsOutsideRevertDefaults(recorded = recorded)

            if (extras.isEmpty()) continue

            val restored = mutableSetOf<String>()

            for (id in extras.keys) {
                val setting = SettingSnapshot.settingOf(id = id) ?: continue

                // ⚠ **A null recording means the setting was *unset* before the hide, and
                // there is nothing to write back.** Secure settings cannot be un-set through
                // this API, and inventing a value would be the app switching on something the
                // user never had on — the exact thing the memory function exists to avoid.
                // Left recorded, so a future release that can unset one still has the fact.
                val value = extras[id] ?: continue

                val written = secureSettingsWrapper.canWriteSecureSettings(
                    settingType = setting.first,
                    key = setting.second,
                    value = value,
                )

                if (written) restored += id
            }

            if (restored.isEmpty()) continue

            records = records + (component to recorded.filterKeys { it !in restored })
        }

        if (records !== userData.settingStateBefore) {
            userDataRepository.updateSettingStateBefore(states = records)
        }
    }
}
