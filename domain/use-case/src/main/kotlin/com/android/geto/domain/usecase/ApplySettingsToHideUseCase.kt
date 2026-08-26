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
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.effectiveSettingsToHide
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
 * disabled. A configuration with nothing ticked is [AppSettingsResult.Success] with
 * nothing written, not a failure — the user has said they want nothing hidden, and
 * refusing to launch the app would be disobeying that rather than reporting a problem.
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
    private val shizukuStartTracker: ShizukuStartTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): AppSettingsResult = withContext(defaultDispatcher) {
        // Half-hidden is the worst outcome available: the app still detects whatever is
        // left on and refuses to run, while the user's device has been changed anyway.
        // Launching an activity is exactly the sort of thing that tears this scope down.
        withContext(NonCancellable) { hide() }
    }

    private suspend fun hide(): AppSettingsResult {
        // Effective rather than stored: with "Manage Display over other apps" off in
        // Advanced the overlay entry reads false whatever was ticked while it was on, so
        // neither the Shizuku pre-start below nor the hide loop can act on it.
        val wanted = userDataRepository.userData.first().effectiveSettingsToHide

        var before = getManualTargetStatesUseCase()

        val hidingOverlay = wanted[ManualRevertTarget.DisplayOverOtherApps] == true

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
        if (hidingOverlay) {
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

                if (!started) return AppSettingsResult.OverlayFailure
            }

            // Attempted even when the live state says overlay access is already withdrawn.
            // That reading comes from a Shizuku query, and a query that could not be
            // answered reads as "nothing is allowed" - so trusting it would skip the write
            // and leave overlays on while reporting success.
            val hidden = setManualTargetUseCase(
                target = ManualRevertTarget.DisplayOverOtherApps,
                enabled = false,
            )

            if (!hidden) return AppSettingsResult.OverlayFailure

            // Starting a fork brings the debugging transport up with it, so the snapshot
            // taken above has stopped describing the device. Read again before deciding
            // which of the remaining targets are "already off": against the stale copy,
            // developer options and USB debugging that Shizuku had just switched on still
            // read as off, were skipped as nothing to do, and the app opened with both of
            // them plainly visible to it.
            before = getManualTargetStatesUseCase()
        }

        var failed = false

        for (target in SettingsToHide.HideOrder) {
            // Done above, on its own terms.
            if (target == ManualRevertTarget.DisplayOverOtherApps) continue

            if (wanted[target] != true) continue

            // Already off. Writing it again is not harmless: for the accessibility
            // services target a second disable would record a fresh hold over services
            // that are already held, and nothing would ever discharge the duplicate.
            if (target != ManualRevertTarget.AccessibilityServices &&
                !before.isEnabled(target)
            ) {
                continue
            }

            if (!setManualTargetUseCase(target = target, enabled = false)) failed = true
        }

        return if (failed) AppSettingsResult.Failure else AppSettingsResult.Success
    }
}
