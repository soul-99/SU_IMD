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
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/** Same reason as the automatic revert: adbd has to restart and re-advertise first. */
private const val SHIZUKU_START_DELAY_MILLIS = 1_500L

private const val ON = "1"

/**
 * Puts things back without going through a specific app's revert.
 *
 * The ongoing notification is the intended route, but it can be swiped away, and once
 * developer options are off there is no settings screen left to turn them on from. This
 * is the way out of that corner, driven from the Favourites tab.
 *
 * Unlike [RevertAppSettingsUseCase] this is not tied to a target app and does not consult
 * that app's stored settings — the user has said what they want back, so each requested
 * target is written unconditionally.
 */
class ManualRevertUseCase @Inject constructor(
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(targets: Set<ManualRevertTarget>): ManualRevertResult =
        withContext(defaultDispatcher) {
            if (targets.isEmpty()) return@withContext ManualRevertResult()

            // The whole point is undoing state the device is stuck in, so a cancelled
            // caller — switching tabs, closing the dialog — must not leave it half done.
            withContext(NonCancellable) { revert(targets) }
        }

    private suspend fun revert(targets: Set<ManualRevertTarget>): ManualRevertResult {
        val reverted = mutableSetOf<ManualRevertTarget>()

        val failed = mutableSetOf<ManualRevertTarget>()

        // Written in declaration order so the debugging transports are back before
        // Shizuku is asked to reconnect through them.
        for (target in ManualRevertTarget.entries) {
            if (target !in targets) continue

            val key = target.globalSettingKey ?: continue

            val written = try {
                secureSettingsWrapper.canWriteSecureSettings(
                    settingType = SettingType.GLOBAL,
                    key = key,
                    value = ON,
                )
            } catch (_: SecurityException) {
                return ManualRevertResult(reverted = reverted, noPermission = true)
            } catch (_: IllegalArgumentException) {
                false
            }

            if (written) reverted += target else failed += target
        }

        if (ManualRevertTarget.AccessibilityServices in targets) {
            val ok = try {
                enableAccessibilityServices()
            } catch (_: SecurityException) {
                return ManualRevertResult(reverted = reverted, noPermission = true)
            }

            if (ok) {
                reverted += ManualRevertTarget.AccessibilityServices
            } else {
                failed += ManualRevertTarget.AccessibilityServices
            }
        }

        if (ManualRevertTarget.Shizuku in targets) {
            // Only wait when this same run has just switched a transport back on. Asking
            // Shizuku to start when nothing else changed should be immediate.
            val restoredTransport = reverted.any { it.globalSettingKey != null }

            if (startShizuku(waitForAdbd = restoredTransport)) {
                reverted += ManualRevertTarget.Shizuku
            } else {
                failed += ManualRevertTarget.Shizuku
            }
        }

        return ManualRevertResult(reverted = reverted, failed = failed)
    }

    /**
     * Switches on the services picked in Settings, plus anything this app is still holding
     * down for any target app, and forgets the holds.
     *
     * Not a release: a release only puts back what there is a record of switching off, and
     * the reason someone opens this dialog is usually that the record is gone — the
     * notification was swiped away, or the process died mid-revert. So the chosen services
     * are switched on regardless of what state they were last in.
     *
     * The write happens even when there is nothing to add: `accessibility_enabled` can be
     * left at 0 by an interrupted apply, and the wrapper derives that flag from the list,
     * so writing the current list back is what unsticks it.
     */
    private suspend fun enableAccessibilityServices(): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldAccessibilityServices

        val enabledAfter = AccessibilityServicePlan.enable(
            wanted = userData.managedAccessibilityServices + held.values.flatten(),
            currentlyEnabled = accessibilityServicesWrapper.getEnabledAccessibilityServices(),
        )

        if (!accessibilityServicesWrapper.setEnabledAccessibilityServices(enabledAfter)) {
            return false
        }

        if (held.isNotEmpty()) userDataRepository.updateHeldAccessibilityServices(held = emptyMap())

        return true
    }

    /**
     * Deliberately ignores the "Restart Shizuku service" toggle: that governs the
     * automatic restart on revert, whereas pressing this is an explicit instruction. It
     * still needs the auth key, without which there is nothing to send.
     */
    private suspend fun startShizuku(waitForAdbd: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        if (userData.shizukuAuthKey.isBlank()) return false

        if (waitForAdbd) delay(SHIZUKU_START_DELAY_MILLIS)

        return shizukuWrapper.startShizuku(
            packageName = userData.shizukuPackageName,
            action = userData.shizukuStartAction.ifBlank {
                userData.shizukuPackageName + ShizukuWrapper.ACTION_START_SUFFIX
            },
            authKey = userData.shizukuAuthKey,
        )
    }
}
