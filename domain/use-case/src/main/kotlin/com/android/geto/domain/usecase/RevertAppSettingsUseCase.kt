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
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.repository.AppSettingsRepository
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Wireless debugging does not come back the instant the Global flag is written; adbd has
 * to restart and re-advertise over mDNS. Give it a moment before asking Shizuku to
 * reconnect, otherwise the start attempt lands on a closed port.
 *
 * Shizuku's own start worker waits for the network, so this only has to cover the gap
 * before adbd is listening at all — hence a short, fixed pause rather than a poll.
 */
private const val SHIZUKU_START_DELAY_MILLIS = 1_500L

class RevertAppSettingsUseCase @Inject constructor(
    private val appSettingsRepository: AppSettingsRepository,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
    private val startShizukuUseCase: StartShizukuUseCase,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(componentName: String): AppSettingsResult = withContext(defaultDispatcher) {
        val appSettings =
            appSettingsRepository.getAppSettingsByComponentName(componentName = componentName)

        if (appSettings.isEmpty()) return@withContext AppSettingsResult.EmptyAppSettings

        val enabledAppSettings = appSettings.filter { it.enabled }

        if (enabledAppSettings.isEmpty()) return@withContext AppSettingsResult.DisabledAppSettings

        val userData = userDataRepository.userData.first()

        // Mirror of the apply side: when suIMD owns the services list for this app, the
        // accessibility_enabled row is left out of the plain write loop and the wrapper
        // is the only thing that writes that flag.
        val managesAccessibility = AppSettingKeys.restoresAccessibilityServices(enabledAppSettings) &&
            (
                userData.managedAccessibilityServices.isNotEmpty() ||
                    componentName in userData.heldAccessibilityServices
                )

        val settingsToWrite = if (managesAccessibility) {
            enabledAppSettings.filterNot { it.key == AppSettingKeys.ACCESSIBILITY_ENABLED }
        } else {
            enabledAppSettings
        }

        // What these settings were really set to before this app's profile was applied.
        // Empty for a profile applied by an older build, in which case each setting falls
        // back to the configured revert value and behaves exactly as it used to.
        val recorded = userData.settingStateBefore[componentName].orEmpty()

        try {
            val written = settingsToWrite.map {
                secureSettingsWrapper.canWriteSecureSettings(
                    settingType = it.settingType,
                    key = it.key,
                    value = SettingSnapshot.revertValue(
                        recorded = recorded,
                        settingType = it.settingType,
                        key = it.key,
                        configured = it.valueOnRevert,
                    ),
                )
            }.all { it }

            if (!written) return@withContext AppSettingsResult.Failure

            // Everything below undoes state this app is holding, so it must not be
            // skipped because the caller's scope went away — navigating back from the
            // settings screen cancels the ViewModel scope mid-revert otherwise.
            withContext(NonCancellable) {
                // Dropped only once the writes have gone through. A record left behind
                // after a failed revert is what lets a retry still put the right values
                // back; a record dropped too early would leave the retry guessing again.
                if (recorded.isNotEmpty()) {
                    userDataRepository.updateSettingStateBefore(
                        states = userData.settingStateBefore - componentName,
                    )
                }

                if (managesAccessibility) {
                    releaseHeldAccessibilityServices(
                        componentName = componentName,
                        userData = userData,
                    )
                }

                // Killing developer options / USB debugging / wireless debugging takes the
                // Shizuku service down with it, and turning them back on does not bring it
                // back. Ask Shizuku to start itself again.
                if (AppSettingKeys.triggersShizukuRestart(enabledAppSettings)) {
                    restartShizukuIfEnabled(userData = userData)
                }
            }

            AppSettingsResult.Success
        } catch (_: SecurityException) {
            AppSettingsResult.NoPermission
        } catch (_: IllegalArgumentException) {
            AppSettingsResult.InvalidValues
        }
    }

    /**
     * Re-enables exactly what this app was holding down, skipping anything another app is
     * still holding and anything the user has since re-enabled by hand. The enabled list
     * is never restored wholesale, so a service switched on elsewhere while the target app
     * was open is neither dropped nor duplicated.
     */
    private suspend fun releaseHeldAccessibilityServices(
        componentName: String,
        userData: UserData,
    ) {
        val held = userData.heldAccessibilityServices

        val released = held[componentName].orEmpty()

        val remaining = AccessibilityServicePlan.withHold(
            held = held,
            componentName = componentName,
            services = emptyList(),
        )

        val plan = AccessibilityServicePlan.release(
            released = released,
            stillHeldByOthers = AccessibilityServicePlan.heldByOthers(
                held = held,
                exceptComponentName = componentName,
            ),
            currentlyEnabled = accessibilityServicesWrapper.getEnabledAccessibilityServices(),
        )

        // Written unconditionally, not only when the list changed, so accessibility_enabled
        // is always left consistent with the list it describes.
        if (accessibilityServicesWrapper.setEnabledAccessibilityServices(plan.enabledAfter)) {
            userDataRepository.updateHeldAccessibilityServices(held = remaining)
        }
    }

    private suspend fun restartShizukuIfEnabled(userData: UserData) {
        if (!userData.restartShizuku) return

        if (!userData.isShizukuConfigured) return

        delay(SHIZUKU_START_DELAY_MILLIS)

        // Through the shared use case so this attempt is confirmed and recorded like every
        // other. It is the attempt most in need of it: nobody is looking at the app when a
        // notification's Revert button fires, so a silent failure here used to surface only
        // as Shizuku mysteriously not running later on.
        startShizukuUseCase()
    }
}
