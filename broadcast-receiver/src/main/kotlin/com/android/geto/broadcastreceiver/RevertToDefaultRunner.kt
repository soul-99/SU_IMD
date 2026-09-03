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
package com.android.geto.broadcastreceiver

import android.content.Context
import android.content.Intent
import com.android.geto.common.SettingsObservationGate
import com.android.geto.common.showRestoredToast
import com.android.geto.common.showRevertedToDefaultToast
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.RevertToDefaultResult
import com.android.geto.domain.model.deviceWideMemoryWanted
import com.android.geto.domain.model.deviceWideRecordAfterRevert
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.RevertToDefaultUseCase
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

/**
 * The one way "Revert to default" is actually run.
 *
 * Five things can trigger it — a Quick Settings tile, a notification button, a launcher
 * shortcut, a button on the Favourites tab and a button in the settings manager — and every
 * one of them has to announce itself and clear the shade as well as doing the work. Three
 * copies of that in three modules is how the per-app notification's request-code bug got
 * written three times; this is the same lesson applied earlier.
 */
@Singleton
class RevertToDefaultRunner @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val revertToDefaultUseCase: RevertToDefaultUseCase,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val userDataRepository: UserDataRepository,
) {
    /**
     * ⚠ **No progress toast any more, and the `auto` parameter went with it.** It existed only
     * to choose between two "..." toasts, and the author has removed both: the toast for this
     * work is the one at the end, which says which framework actually acted. Nothing else ever
     * branched on it — every one of the seven entry points ran identical work — so there is no
     * behaviour left for it to select.
     *
     * [fromMemory] is the device-wide **memory** revert: instead of the configured defaults,
     * every keyed target is driven back to what the hide measured. Only the framework-following
     * routes pass it — the notification, the Hide settings QS toggle and the
     * `Unhide settings and services` intent. The explicit `Revert to default` routes never do,
     * on the author's instruction that Revert to default always means the defaults.
     *
     * [explicit] changes **only what the toast says**, and it is the author's restore/revert
     * exception: the named `Revert to default` function says reverted, every way back from a
     * hide says restored. Three routes set it — the settings manager's button, `RevertActivity`
     * (the tile and the launcher shortcut share it) and Tasker's `ACTION_REVERT_TO_DEFAULT`.
     *
     * ⚠ It is **not** the same question as [fromMemory], and neither implies the other. A
     * framework-following unhide under `UnhidingFramework.RevertToDefault` arrives here with
     * both false and drives the configured defaults — the same work as an explicit revert, but
     * it is undoing a hide, so it says restored.
     */
    suspend operator fun invoke(
        fromMemory: Boolean = false,
        explicit: Boolean = false,
    ): RevertToDefaultResult {
        // Every per-app Revert button now describes a device that no longer exists, and
        // pressing one would write remembered values back over the defaults just applied.
        // The observer service's own notification survives this: the system keeps a
        // foreground service's notification up regardless.
        // Which kind of revert this is, which the log could previously only *infer* — an
        // explicit press has no `unhide memory=... fallback=...` line before it, because it
        // does not come through SettingsHiddenRunner.unhide at all. The distinction has existed
        // since r2e and was simply never written down.
        Diagnostics.log(
            tag = "revert",
            message = "revert to default explicit=$explicit fromMemory=$fromMemory",
        )

        SettingsObservationGate.pause()

        return try {
            notificationManagerWrapper.cancelAll()

            // Read inside the try, after cancelAll, so a record cleared by something else
            // in the meantime cannot have this drive a stale destination.
            val wantedOverride = if (fromMemory) {
                deviceWideMemoryWanted(
                    recorded = userDataRepository.userData.first()
                        .settingStateBefore[AccessibilityServicePlan.DEVICE_WIDE_HOLD]
                        .orEmpty(),
                ).takeIf { it.isNotEmpty() }
            } else {
                null
            }

            revertToDefaultUseCase(wantedOverride = wantedOverride).also { result ->
                // ⚠ **The record this revert restored from is now spent, and nothing else
                // clears it.** Before v3 nothing did at all, so a second device-wide hide
                // reverted to the state measured at the *first* one — `recordDeviceWideValues`
                // skips any key it already holds, so the stale reading simply survived. The
                // debt rule writes into the same record, which is what made this urgent.
                //
                // Failed targets are left recorded, exactly as `RevertAppSettingsUseCase`
                // leaves a failed per-app id: the record is what lets a retry put the right
                // value back.
                if (wantedOverride != null) clearDeviceWideRecord(wanted = wantedOverride, result = result)

                // After cancelAll, so the report is not swept away by the same run that
                // produced it.
                if (result.overlayRestoreFailed) overlayRestoreRunner.report()

                val shizukuFailed = ManualRevertTarget.Shizuku in result.failed

                // ⚠ **Only when nothing went wrong, and there is no failure toast to take
                // its place.** The author removed those, and his reasoning holds: both cases
                // raise a notification below or through `report()` above, which is the copy
                // he can act on. What must not happen is the completion toast standing in for
                // them — a revert that could not put Shizuku back has not finished, and
                // "Settings restored" over it would be the app claiming something untrue.
                //
                // Named for the destination this run actually drove to rather than for the
                // framework stored right now: a framework changed between the press and this
                // line would otherwise have the toast describe a revert that did not run.
                if (!shizukuFailed && !result.overlayRestoreFailed) {
                    if (explicit) {
                        context.showRevertedToDefaultToast()
                    } else {
                        context.showRestoredToast(fromMemory = fromMemory)
                    }
                }

                // v3 spec item 5: a toast is gone in three seconds, and a revert that could
                // not bring Shizuku back is something the user has to act on. A notification
                // that opens the Shizuku app is the only part of this the app cannot do
                // itself.
                //
                // ⚠ **Not when overlay access also failed.** That report is already on screen,
                // already names Shizuku as the cause, and already carries a Try again — a
                // second notification about the same broken service would be the same news
                // twice. The author's rule.
                if (shizukuFailed && !result.overlayRestoreFailed) {
                    notificationManagerWrapper.notify(
                        id = AndroidNotificationManagerWrapper.SHIZUKU_FALLBACK_NOTIFICATION_ID,
                        notification = buildShizukuRevertFailedNotification(
                            context = context,
                            shizukuPackage = userDataRepository.userData.first()
                                .shizukuPackageName,
                        ),
                    )
                }
            }
        } finally {
            SettingsObservationGate.resume()

            // If the optional observer service is running, reset its foreground
            // notification after suppressing IMD's own burst of settings writes. An
            // explicit start to an already-running service only delivers this command.
            if (SettingsObservationGate.isRunning) {
                context.startService(
                    Intent()
                        .setClassName(context, SettingsObservationGate.SERVICE_CLASS_NAME)
                        .setAction(SettingsObservationGate.ACTION_RESET),
                )
            }
        }
    }

    /**
     * Drops the device-wide memory record this revert has just restored from.
     *
     * See [deviceWideRecordAfterRevert] for what survives and why. Best-effort: a revert that
     * put the device back and then failed to tidy its own bookkeeping has still done the thing
     * the user asked for, and throwing here would skip the toast and the notifications below.
     */
    private suspend fun clearDeviceWideRecord(
        wanted: Map<ManualRevertTarget, Boolean>,
        result: RevertToDefaultResult,
    ) {
        runCatching {
            val userData = userDataRepository.userData.first()

            val cleared = deviceWideRecordAfterRevert(
                settingStateBefore = userData.settingStateBefore,
                driven = wanted.keys,
                failed = result.failed,
            )

            if (cleared !== userData.settingStateBefore) {
                userDataRepository.updateSettingStateBefore(states = cleared)
            }
        }
    }
}
