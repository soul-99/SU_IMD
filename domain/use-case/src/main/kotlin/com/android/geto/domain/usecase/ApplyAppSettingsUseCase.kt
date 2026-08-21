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
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.AppSettingsRepository
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

class ApplyAppSettingsUseCase @Inject constructor(
    private val appSettingsRepository: AppSettingsRepository,
    private val secureSettingsWrapper: SecureSettingsWrapper,
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(componentName: String): AppSettingsResult = withContext(defaultDispatcher) {
        val appSettings =
            appSettingsRepository.getAppSettingsByComponentName(componentName = componentName)

        if (appSettings.isEmpty()) return@withContext AppSettingsResult.EmptyAppSettings

        // Only ever write the settings the user actually ticked. Upstream wrote every row
        // regardless of its checkbox, which made unticking a setting do nothing.
        val enabledAppSettings = appSettings.filter { it.enabled }

        if (enabledAppSettings.isEmpty()) return@withContext AppSettingsResult.DisabledAppSettings

        val userData = userDataRepository.userData.first()

        // Whether suIMD is going to take the services list into its own hands for this
        // app. When it is, the accessibility_enabled row is left out of the plain write
        // loop below: the wrapper derives that flag from the resulting list, and two
        // writers racing on it produce a state the Settings app renders inconsistently.
        val managesAccessibility = userData.managedAccessibilityServices.isNotEmpty() &&
            AppSettingKeys.hidesAccessibilityServices(enabledAppSettings)

        val settingsToWrite = if (managesAccessibility) {
            enabledAppSettings.filterNot { it.key == AppSettingKeys.ACCESSIBILITY_ENABLED }
        } else {
            enabledAppSettings
        }

        try {
            // Recorded before anything is written, and not cancellable: the record is the
            // only thing that lets revert put the device back the way it actually was
            // rather than the way the profile guessed it would be.
            withContext(NonCancellable) {
                recordCurrentValues(
                    componentName = componentName,
                    settings = settingsToWrite,
                    userData = userData,
                )
            }

            // map before all, so every setting is attempted. A short-circuiting all()
            // leaves the earlier writes committed and the later ones silently skipped.
            val written = settingsToWrite.map {
                secureSettingsWrapper.canWriteSecureSettings(
                    settingType = it.settingType,
                    key = it.key,
                    value = it.valueOnLaunch,
                )
            }.all { it }

            if (!written) return@withContext AppSettingsResult.Failure

            if (managesAccessibility) {
                // Not cancellable: leaving services switched off with no record of it is
                // the one failure this feature must never produce.
                withContext(NonCancellable) {
                    holdManagedAccessibilityServices(
                        componentName = componentName,
                        userData = userData,
                    )
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
     * Notes what every setting about to be written is currently set to.
     *
     * Reverting to the user's configured "value on revert" is a guess made when the
     * profile was written. If developer options were already off and the profile hides
     * them, that guess switches them on — a state the user never asked for and, with
     * developer options being what they are, one they then have no screen to undo from.
     *
     * Only settings with no record yet are read. Launching the same app again without
     * reverting in between — the usual pattern with a pinned shortcut — would otherwise
     * overwrite the original reading with the value this app wrote on the previous launch,
     * and the revert would put back the applied state instead of the real one.
     */
    private suspend fun recordCurrentValues(
        componentName: String,
        settings: List<AppSetting>,
        userData: UserData,
    ) {
        val existing = userData.settingStateBefore[componentName].orEmpty()

        val unrecorded = settings.filterNot { setting ->
            SettingSnapshot.idOf(settingType = setting.settingType, key = setting.key) in existing
        }

        // Nothing new to note. Skipping the write matters: a pinned shortcut applies the
        // same profile every time it is tapped, and this would otherwise rewrite the whole
        // preferences proto on each launch for no change at all.
        if (unrecorded.isEmpty()) return

        val measured = unrecorded.associate { setting ->
            SettingSnapshot.idOf(settingType = setting.settingType, key = setting.key) to
                secureSettingsWrapper.getSecureSettingValue(
                    settingType = setting.settingType,
                    key = setting.key,
                )
        }

        userDataRepository.updateSettingStateBefore(
            states = userData.settingStateBefore +
                (componentName to SettingSnapshot.merge(existing = existing, measured = measured)),
        )
    }

    /**
     * Switches off the services the user picked, and records against this app which ones
     * it is now holding down. Only services that are actually on (or already held by
     * another app) are claimed, so a revert never switches on something the user had
     * disabled themselves.
     */
    private suspend fun holdManagedAccessibilityServices(
        componentName: String,
        userData: UserData,
    ) {
        val held = userData.heldAccessibilityServices

        val plan = AccessibilityServicePlan.hold(
            managed = userData.managedAccessibilityServices,
            currentlyEnabled = accessibilityServicesWrapper.getEnabledAccessibilityServices(),
            heldByOthers = AccessibilityServicePlan.heldByOthers(
                held = held,
                exceptComponentName = componentName,
            ),
        )

        if (plan.held.isEmpty() && !plan.listChanged) return

        // Record the claim before touching the system setting. If the process dies in
        // between, a stale record is harmless — the revert simply finds the services
        // already enabled and skips them — whereas a service switched off with no record
        // could never be switched back on by this app.
        userDataRepository.updateHeldAccessibilityServices(
            held = AccessibilityServicePlan.withHold(
                held = held,
                componentName = componentName,
                services = plan.held,
            ),
        )

        if (!accessibilityServicesWrapper.setEnabledAccessibilityServices(plan.enabledAfter)) {
            // The write was refused, so drop the claim again rather than leaving a record
            // that would make a later revert enable services nobody switched off.
            userDataRepository.updateHeldAccessibilityServices(held = held)
        }
    }
}
