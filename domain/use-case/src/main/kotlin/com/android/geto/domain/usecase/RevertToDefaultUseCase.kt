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

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.RevertToDefaultResult
import com.android.geto.domain.model.effectiveRevertDefaults
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
    private val shizukuStartTracker: ShizukuStartTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): RevertToDefaultResult = withContext(defaultDispatcher) {
        // A half-applied revert is worse than none — developer options on with USB debugging
        // still off is a state the user did not ask for and cannot see. A tile press whose
        // service is torn down mid-run must not be able to leave that behind.
        withContext(NonCancellable) { revert() }
    }

    private suspend fun revert(): RevertToDefaultResult {
        val userData = userDataRepository.userData.first()
        // Effective rather than stored: with "Manage Display over other apps" off in
        // Advanced the overlay entry is absent unless a debt is outstanding, in which case
        // it reads true. Turning the feature off stops IMD taking overlay access away; it
        // does not abandon access already taken.
        val wanted = userData.effectiveRevertDefaults

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
        val overlayNeedsWrite = overlayEnabled == false ||
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
            if (shizukuStartRefused && enabled) {
                failed += ManualRevertTarget.Shizuku
            } else {
                applyTarget(ManualRevertTarget.Shizuku, enabled)
            }
        }

        return RevertToDefaultResult(
            changed = changed,
            failed = failed,
            unchanged = unchanged,
            overlayRestoreFailed = overlayRestoreFailed,
        )
    }
}
