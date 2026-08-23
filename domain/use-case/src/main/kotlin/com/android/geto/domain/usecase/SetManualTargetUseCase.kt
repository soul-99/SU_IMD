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
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext

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
            else -> false
        }
    }

    private suspend fun setAccessibilityServices(enabled: Boolean): Boolean {
        val userData = userDataRepository.userData.first()

        val held = userData.heldAccessibilityServices

        val currentlyEnabled = runCatching {
            accessibilityServicesWrapper.getEnabledAccessibilityServices()
        }.getOrNull() ?: return false

        // Switching on covers anything still held for a target app as well as the chosen
        // set, so one press cannot leave a service down with no record of why.
        val after = if (enabled) {
            AccessibilityServicePlan.enable(
                wanted = userData.managedAccessibilityServices + held.values.flatten(),
                currentlyEnabled = currentlyEnabled,
            )
        } else {
            AccessibilityServicePlan.disable(
                unwanted = userData.managedAccessibilityServices,
                currentlyEnabled = currentlyEnabled,
            )
        }

        val written = runCatching {
            accessibilityServicesWrapper.setEnabledAccessibilityServices(after)
        }.getOrDefault(false)

        if (!written) return false

        // The holds describe services this app switched off on some app's behalf. Turning
        // them all back on here discharges that debt; turning them off by hand does not
        // create one, because nothing is waiting to put them back.
        if (enabled && held.isNotEmpty()) {
            userDataRepository.updateHeldAccessibilityServices(held = emptyMap())
        }

        return true
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
