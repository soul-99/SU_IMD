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
import com.android.geto.domain.model.overlayManageableInManager
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
        // Falls back to the stock package name when nothing is configured, so an installed
        // Shizuku can still be recognised by someone who has not filled in IMD's own Shizuku
        // section yet. That is the only reading the check has to survive; the point of it is
        // the uninstall case above, not identifying which fork is present.
        val shizukuInstalled = runCatching {
            packageManagerWrapper.isInstalled(
                packageName = userData.shizukuPackageName
                    .ifBlank { ShizukuWrapper.DEFAULT_SHIZUKU_PACKAGE_NAME },
            )
        }.getOrDefault(false)

        // Whether the service is up, which is a fact about the device and true or false
        // regardless of what IMD has been told about Shizuku. The manager shows this on the
        // switch so a running service never reads as stopped - it just cannot be operated
        // from there without a configuration to send start and stop intents through.
        val shizukuRunning = shizukuInstalled &&
            runCatching { shizukuWrapper.isShizukuRunning() }.getOrDefault(false)

        // Whether IMD can *operate* that service: starting and stopping go out as the fork's
        // own broadcasts, and there is no action to send without a configuration. Kept apart
        // from the reading above so "running" and "manageable" cannot be confused - the row is
        // shown live either way, and only usability turns on this.
        val shizukuAvailable = userData.isShizukuConfigured && shizukuInstalled

        val enabled = ManualRevertTarget.entries.associateWith { target ->
            when (target) {
                ManualRevertTarget.AccessibilityServices -> {
                    // Nothing selected means nothing for this row to stand for. Reading "on"
                    // there was describing the device - no managed service is off, because
                    // there are none - when the row's whole subject is what IMD is holding
                    // down. Off, and the dialog refuses to move it and says why.
                    if (userData.managedAccessibilityServices.isEmpty()) {
                        return@associateWith false
                    }

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

                ManualRevertTarget.Shizuku -> shizukuRunning

                ManualRevertTarget.DisplayOverOtherApps -> {
                    // This app's own record comes first, and it is the only reading that is
                    // true whether or not Shizuku can be reached: a device-wide hold means
                    // IMD took overlay access away and has not given it back yet.
                    if (
                        AccessibilityServicePlan.DEVICE_WIDE_HOLD in userData.heldOverlayPackages
                    ) {
                        return@associateWith false
                    }

                    // The row stands for the chosen set, exactly as the accessibility row
                    // does, so it only reads "on" when every selected app still holds the
                    // permission.
                    val selected = userData.managedOverlayPackages

                    // Nothing selected means nothing for this row to stand for - the same
                    // answer the accessibility row gives above, and for the same reason. It
                    // used to read "on", which described the device rather than anything IMD
                    // was doing, on a switch that could not do anything about it either way.
                    if (selected.isEmpty()) return@associateWith false

                    // A failed query falls back to "on" rather than "off": it only fails when
                    // Shizuku is out of reach, and Shizuku being out of reach says nothing
                    // about what apps hold.
                    runCatching {
                        shizukuWrapper.getAllowedOverlayPackages()
                    }.getOrNull()?.let { allowed -> selected.all { it in allowed } } ?: true
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

        ManualTargetStates(
            enabled = enabled,
            shizukuAvailable = shizukuAvailable,
            shizukuSupportsIntents = userData.shizukuForkMode.supportsIntents,
            accessibilityManaged = userData.managedAccessibilityServices.isNotEmpty(),
            // ⚠ **The manager's rule, not the hiding one, and this field has no other
            // reader.** `overlayManageable` is Thedjchi-only because a *launch* must be able to
            // bring the shell up on demand; here the user has just started the service by hand,
            // so a running Shevery can write the AppOp after all. See the author's two new
            // points in the Shevery pop-up, which are exactly this distinction.
            overlayManaged = overlayManageableInManager(
                userData = userData,
                shizukuRunning = shizukuRunning,
            ),
        )
    }
}
