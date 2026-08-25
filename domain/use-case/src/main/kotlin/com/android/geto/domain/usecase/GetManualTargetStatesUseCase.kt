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
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

private const val ON = "1"

/**
 * What each row of the settings manager is actually set to, right now.
 *
 * Read rather than remembered. Every one of these can be changed from outside this app —
 * from the system settings screens the dialog itself links to, from another app, or by
 * Shizuku dying on its own — so a cached answer would go stale in exactly the situations
 * the dialog exists to sort out.
 *
 * Nothing here throws. A read that fails reports "off", because the dialog's job is to
 * offer to switch things on and an unreadable setting is one worth offering.
 */
class GetManualTargetStatesUseCase @Inject constructor(
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): ManualTargetStates = withContext(ioDispatcher) {
        val userData = userDataRepository.userData.first()

        // Asked before anything is read from Shizuku, and the answer gates that read.
        // Shizuku's client keeps a binder handle, and uninstalling the app does not
        // reliably invalidate it — pingBinder can go on answering "alive" for a service
        // that is gone. Checking the package first is the only reading that survives an
        // uninstall, which is exactly the case the switch was getting wrong.
        val shizukuAvailable = userData.isShizukuConfigured &&
            runCatching {
                packageManagerWrapper.isInstalled(packageName = userData.shizukuPackageName)
            }.getOrDefault(false)

        val enabled = ManualRevertTarget.entries.associateWith { target ->
            when (target) {
                ManualRevertTarget.AccessibilityServices -> {
                    if (
                        AccessibilityServicePlan.DEVICE_WIDE_HOLD in
                        userData.heldAccessibilityServices
                    ) {
                        return@associateWith false
                    }

                    // The row stands for the whole managed set, so it only reads "on" when
                    // every one of them is on — see AccessibilityServicePlan.allEnabled.
                    runCatching {
                        AccessibilityServicePlan.allEnabled(
                            wanted = userData.managedAccessibilityServices,
                            currentlyEnabled = accessibilityServicesWrapper
                                .getEnabledAccessibilityServices(),
                        )
                    }.getOrDefault(false)
                }

                ManualRevertTarget.Shizuku -> {
                    shizukuAvailable &&
                        runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)
                }

                ManualRevertTarget.DisplayOverOtherApps -> {
                    runCatching {
                        shizukuWrapper.getAllowedOverlayPackages()
                    }.getOrNull()?.isNotEmpty() == true
                }

                else -> {
                    val key = target.globalSettingKey ?: return@associateWith false

                    runCatching {
                        secureSettingsWrapper.getSecureSettingValue(
                            settingType = SettingType.GLOBAL,
                            key = key,
                        ) == ON
                    }.getOrDefault(false)
                }
            }
        }

        ManualTargetStates(enabled = enabled, shizukuAvailable = shizukuAvailable)
    }
}
