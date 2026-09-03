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

import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.AppSettingsRepository
import com.android.geto.domain.repository.UserDataRepository
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withContext
import javax.inject.Inject

/** What a switched-on global setting stores. Matches AppSettingKeys' own `valueOnRevert` test. */
private const val WIRELESS_DEBUGGING_ON = "1"

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
    private val restoreAutoHideServiceUseCase: RestoreAutoHideServiceUseCase,
    private val startShizukuUseCase: StartShizukuUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val settingsWorkTracker: SettingsWorkTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    // A thin wrapper rather than a track { } around the body below, for the same reason as
    // ApplyAppSettingsUseCase: the body is full of return@withContext and does not move.
    suspend operator fun invoke(componentName: String): AppSettingsResult =
        settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {
            revertProfile(componentName = componentName)
        }
            .also { Diagnostics.log(tag = "revert", message = "app $componentName -> $it") }

    private suspend fun revertProfile(componentName: String): AppSettingsResult = withContext(defaultDispatcher) {
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

        // What these settings were really set to before this app's profile was applied, plus
        // the reserved notes the launch left about what it actually did. Empty for a profile
        // applied by an older build, in which case each setting falls back to the configured
        // revert value and behaves exactly as it used to.
        val recorded = userData.settingStateBefore[componentName].orEmpty()

        // Overlay access comes back only when *this* app's launch is the one that took it.
        //
        // The profile saying so is not enough, and neither is a debt existing somewhere. Two
        // apps that both hide overlay access, launched one after the other, leave only the
        // first one having done any withdrawing - the second finds it already gone and hides
        // nothing. Restoring on the second app's revert would hand the permission back while
        // the first app, the one that asked for it to be withheld, is still open. So the
        // launch writes a note when it does the work, and only that note earns the undo.
        //
        // A debt with no note left behind - an outstanding hide from before this rule, or a
        // device-wide one from the tile or an intent - stays the province of Revert to default,
        // which restores from the debt itself and is reachable from the notification, the
        // tile, a shortcut and the services manager.
        val restoresOverlay = AppSettingKeys.restoresOverlayAccess(enabledAppSettings) &&
            userData.heldOverlayPackages.isNotEmpty() &&
            SettingSnapshot.OVERLAY_HIDDEN_ID in recorded

        val settingsToWrite = enabledAppSettings
            .filterNot { managesAccessibility && it.key == AppSettingKeys.ACCESSIBILITY_ENABLED }
            .filterNot { it.key == AppSettingKeys.SYSTEM_ALERT_WINDOW }
            // Both markers, exactly as the apply side drops them. Neither has a settings row
            // behind it, and handing one to the secure settings wrapper would be writing a key
            // Android has never heard of - which on a strict device throws, and would take the
            // rest of this revert down with it.
            .filterNot { it.key == AppSettingKeys.SHIZUKU_SERVICE }
            // ⚠ **Wireless debugging is not switched back on by a memory restore unless the
            // user has asked for it.** A device that comes out of a hide with wireless
            // debugging on is listening on whatever network it is attached to, with nothing
            // on screen saying so, so the author made putting it back opt-in.
            //
            // Only the *on* direction. A record that says it was off before the hide still
            // switches it off here, because that is the direction this rule exists to
            // protect, and refusing it would leave the device more exposed than the record.
            //
            // Under Revert to default this never fires: that framework drives revertDefaults,
            // which carries its own Wireless debugging row and answers this question there.
            .filterNot { setting ->
                userData.unhidingFramework == UnhidingFramework.Memory &&
                    !userData.restoreWirelessDebugging &&
                    setting.key == AppSettingKeys.ADB_WIFI_ENABLED &&
                    SettingSnapshot.revertValue(
                        recorded = recorded,
                        settingType = setting.settingType,
                        key = setting.key,
                        configured = setting.valueOnRevert,
                    ) == WIRELESS_DEBUGGING_ON
            }

        // Overlay first, mirroring the apply side: it is the only part of this revert that
        // needs Shizuku, and the settings writes below are what take its transport away.
        // A failure here is recorded rather than returned, so the rest of the profile is
        // still put back - the retry notification carries the news instead.
        //
        // runCatching is what makes that sentence true rather than merely intended. Both
        // calls in here end in a binder call to a service that can die between the check
        // that it is alive and the call itself, and a dead binder throws; an escaping throw
        // would abandon every setting this profile remembers, none of which needs Shizuku.
        if (restoresOverlay) {
            runCatching {
                if (!getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.Shizuku)) {
                    shizukuStartTracker.beginOverlay(OverlayStart.Restore)

                    try {
                        setManualTargetUseCase(ManualRevertTarget.Shizuku, enabled = true)
                    } finally {
                        shizukuStartTracker.endOverlay(OverlayStart.Restore)
                    }
                }

                withContext(NonCancellable) {
                    setManualTargetUseCase(
                        target = ManualRevertTarget.DisplayOverOtherApps,
                        enabled = true,
                    )
                }
            }
        }

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

                // The Shizuku service comes back on Revert in two cases. First, when this
                // app's profile stopped it outright — the "hide Shizuku service" toggle: its
                // own revert starts it again, and only its own, which is what the per-app
                // record under SHIZUKU_STOPPED_ID is for (another app that found the service
                // already down never recorded a stop, so its revert leaves it alone). Second,
                // when the profile took the service down as a side effect of switching USB
                // debugging back on.
                //
                // ⚠ **The second case is no longer behind a switch.** 'Restart Shizuku
                // service' was the only thing reading it and v3 removed that row from
                // Advanced at the author's own suggestion, so this path now always puts the
                // service back — which is what the switch did when it was on, and what every
                // other Shizuku restart in the app already does unconditionally.
                if (
                    SettingSnapshot.SHIZUKU_STOPPED_ID in recorded ||
                    AppSettingKeys.triggersShizukuRestart(enabledAppSettings)
                ) {
                    restartShizuku(userData = userData)
                }

                // Last, and only if this was the last one owed: IMD's own IMD+ detector.
                releaseAutoHideDetectorIfLast()
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

    /**
     * Puts IMD's own IMD+ detector back, but only once nothing else is hidden.
     *
     * Every launch that hides anything switches the detector off, whatever the profile says
     * about accessibility services — see the matching call in [ApplyAppSettingsUseCase]. Its
     * hold is IMD's own rather than any app's, so a per-app revert must not release it while
     * another app's launch is still outstanding: the detector would come back, see the next
     * watched app open, and start an IMD+ run on top of a device that is already hidden.
     *
     * So it is done here, at the end of the revert that leaves nothing behind. "Revert to
     * default" needs no such test - it puts the whole device into a known state, so it calls
     * the same use case unconditionally.
     *
     * The read is fresh rather than the `userData` from the top of this revert: the writes
     * above are what may have just emptied the record this is testing.
     */
    private suspend fun releaseAutoHideDetectorIfLast() {
        val userData = runCatching { userDataRepository.userData.first() }.getOrNull() ?: return

        // Something is still hidden — this was not the last pending revert.
        if (userData.settingsHidden) return

        restoreAutoHideServiceUseCase()
    }

    /**
     * Starts the service again. Both routes reach it directly now: a user who asked for
     * the service to be stopped for an app plainly wants it back on that app's revert, and
     * the transport-driven case used to sit behind the 'Restart Shizuku service' switch that
     * v3 removed at the author's own suggestion.
     */
    private suspend fun restartShizuku(userData: UserData) {
        if (!userData.isShizukuConfigured) return

        delay(SHIZUKU_START_DELAY_MILLIS)

        // Through the shared use case so this attempt is confirmed and recorded like every
        // other. It is the attempt most in need of it: nobody is looking at the app when a
        // notification's Revert button fires, so a silent failure here used to surface only
        // as Shizuku mysteriously not running later on.
        startShizukuUseCase()
    }
}
