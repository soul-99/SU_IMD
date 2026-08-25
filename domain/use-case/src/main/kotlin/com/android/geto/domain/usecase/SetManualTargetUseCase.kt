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
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

private const val ON = "1"

private const val OFF = "0"

/**
 * Switches one row of the settings manager on or off.
 *
 * The manager dialog's per-row switches, and the only path that writes these settings by
 * hand. An earlier version could only ever put things back — one direction, behind a batch
 * button — which meant the dialog could rescue a device but never simply manage it.
 *
 * Switching **off** is deliberately narrow. Accessibility services removes only the
 * components this app manages, and Shizuku sends the fork's own stop action rather than
 * killing anything — neither reaches beyond what the app put in place itself.
 */
class SetManualTargetUseCase @Inject constructor(
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val shizukuWrapper: ShizukuWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val startShizukuUseCase: StartShizukuUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(
        target: ManualRevertTarget,
        enabled: Boolean,
    ): Boolean = withContext(defaultDispatcher) {
        // Same reasoning as the manual revert: a half-applied change to developer options
        // is worse than none, so navigating away must not cancel it mid-write.
        withContext(NonCancellable) { set(target = target, enabled = enabled) }
    }

    private suspend fun set(target: ManualRevertTarget, enabled: Boolean): Boolean {
        target.globalSettingKey?.let { key ->
            return runCatching {
                secureSettingsWrapper.canWriteSecureSettings(
                    settingType = SettingType.GLOBAL,
                    key = key,
                    value = if (enabled) ON else OFF,
                )
            }.getOrDefault(false)
        }

        return when (target) {
            ManualRevertTarget.AccessibilityServices -> setAccessibilityServices(enabled = enabled)
            ManualRevertTarget.Shizuku -> setShizuku(running = enabled)
            ManualRevertTarget.DisplayOverOtherApps -> setOverlayPermission(enabled = enabled)
            else -> false
        }
    }

    private suspend fun setOverlayPermission(enabled: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        if (enabled) {
            val held = userData.heldOverlayPackages

            if (held.isEmpty()) return true

            val requestingPackages = packageManagerWrapper.getPackageIdentities(held.keys)
            val toRestore = held.filter { (packageName, identity) ->
                requestingPackages[packageName] == identity
            }.keys

            // An uninstalled app, or one updated to stop requesting the permission, no
            // longer has an AppOp to restore. A replacement with a different installation
            // identity is also dropped rather than inheriting the previous app's access.
            val restored = shizukuWrapper.setOverlayPermission(
                packages = toRestore,
                allowed = true,
            ) ?: emptySet()
            val remaining = held.filter { (packageName, identity) ->
                requestingPackages[packageName] == identity && packageName !in restored
            }

            if (remaining != held) {
                userDataRepository.updateHeldOverlayPackages(remaining)
            }

            return remaining.isEmpty()
        }

        val allowedPackages = shizukuWrapper.getAllowedOverlayPackages() ?: return false
        val requestingPackages = packageManagerWrapper.getPackageIdentities(allowedPackages)
        val toDisable = requestingPackages.keys

        if (toDisable.isEmpty()) return true

        // Record the debt before the shell command. A multi-package command can fail after
        // changing an earlier package, and retaining the full set makes a later restore safe.
        userDataRepository.updateHeldOverlayPackages(
            userData.heldOverlayPackages + requestingPackages.filterKeys { it in toDisable },
        )

        val disabled = shizukuWrapper.setOverlayPermission(
            packages = toDisable,
            allowed = false,
        ) ?: emptySet()

        // Narrow the crash-safe provisional debt to what the shell actually changed.
        // Every candidate was allowed before this attempt, so a process death before this
        // cleanup can only re-allow something that never stopped being allowed.
        userDataRepository.updateHeldOverlayPackages(
            userData.heldOverlayPackages + requestingPackages.filterKeys { it in disabled },
        )

        return disabled == toDisable
    }

    private suspend fun setAccessibilityServices(enabled: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldAccessibilityServices
        val holdKey = AccessibilityServicePlan.DEVICE_WIDE_HOLD

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        if (enabled) {
            val released = held[holdKey].orEmpty()
            val remaining = AccessibilityServicePlan.withHold(
                held = held,
                componentName = holdKey,
                services = emptyList(),
            )
            val plan = AccessibilityServicePlan.release(
                released = released,
                stillHeldByOthers = AccessibilityServicePlan.heldByOthers(
                    held = held,
                    exceptComponentName = holdKey,
                ),
                currentlyEnabled = currentlyEnabled,
            )

            val written = runCatching {
                accessibilityServicesWrapper.setEnabledAccessibilityServices(plan.enabledAfter)
            }.getOrDefault(false)

            if (written && remaining != held) {
                userDataRepository.updateHeldAccessibilityServices(held = remaining)
            }

            return written
        }

        val heldByOthers = AccessibilityServicePlan.heldByOthers(
            held = held,
            exceptComponentName = holdKey,
        )
        val plan = AccessibilityServicePlan.hold(
            // Claim services already held by a per-app profile as well as everything
            // currently enabled. That prevents the profile's Revert from bringing one
            // back while the device-wide restricted app is still open.
            managed = held[holdKey].orEmpty() + currentlyEnabled + heldByOthers,
            currentlyEnabled = currentlyEnabled,
            heldByOthers = heldByOthers,
        )

        if (plan.held.isEmpty() && !plan.listChanged) return true

        val updatedHeld = AccessibilityServicePlan.withHold(
            held = held,
            componentName = holdKey,
            // A second device-wide launch must extend the existing debt rather than
            // replacing it. Services from the first launch are already off, so hold()
            // cannot rediscover them from the live enabled list.
            services = held[holdKey].orEmpty() + plan.held,
        )

        // Persist before writing so process death cannot leave a service disabled with no
        // record capable of restoring it.
        userDataRepository.updateHeldAccessibilityServices(held = updatedHeld)

        val written = runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(
                plan.enabledAfter,
            )
        }.getOrDefault(false)

        if (!written) {
            userDataRepository.updateHeldAccessibilityServices(held = held)
        }

        return written
    }

    private suspend fun setShizuku(running: Boolean): Boolean {
        // Starting goes through the shared use case, which waits to find out whether Shizuku
        // actually came up. Sending the broadcast and reporting success was the old
        // behaviour, and it is why a switch could report "on" for a service that never
        // started.
        if (running) return startShizukuUseCase()

        val userData = userDataRepository.userData.first()

        if (!userData.isShizukuConfigured) return false

        val startAction = userData.shizukuStartAction.ifBlank {
            userData.shizukuPackageName + ShizukuWrapper.ACTION_START_SUFFIX
        }

        // No stop action can be derived from a start action with no "START" in it. Better
        // to report failure than to broadcast something invented.
        val stopAction = ShizukuForkDefaults.stopActionFor(startAction = startAction)

        if (stopAction.isBlank()) return false

        return shizukuWrapper.stopShizuku(
            packageName = userData.shizukuPackageName,
            action = stopAction,
            authKey = userData.shizukuAuthKey,
        )
    }
}
