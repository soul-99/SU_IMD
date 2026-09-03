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
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.AccessibilityServicesWrapper
import com.android.geto.domain.framework.SecureSettingsWrapper
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.hideOwnsRevert
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.autoHideCoversProfile
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.overlayAlreadyWithdrawn
import com.android.geto.domain.model.overlayManageable
import com.android.geto.domain.model.profileHiddenTargets
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
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val stopShizukuServiceUseCase: StopShizukuServiceUseCase,
    private val disableAutoHideServiceUseCase: DisableAutoHideServiceUseCase,
    private val shizukuStartTracker: ShizukuStartTracker,
    private val settingsWorkTracker: SettingsWorkTracker,
    @param:Dispatcher(GetoDispatchers.Default) private val defaultDispatcher: CoroutineDispatcher,
) {
    // A thin wrapper rather than a track { } around the body below, and deliberately: that
    // body is a few hundred lines of return@withContext, which would all have had to be
    // re-indented and re-labelled. This way the tile is held unavailable for the whole
    // launch and not one line of the logic moves. See SettingsWorkTracker.
    suspend operator fun invoke(componentName: String): AppSettingsResult =
        settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
            applyProfile(componentName = componentName)
        }
            .also { Diagnostics.log(tag = "hide", message = "app $componentName -> $it") }
            // Only a hide that actually landed marks the process. A refused one leaves the
            // question open, which is right: nothing about the device changed.
            .also { if (it == AppSettingsResult.Success) PriorHide.markHidden() }

    private suspend fun applyProfile(componentName: String): AppSettingsResult = withContext(defaultDispatcher) {
        val appSettings =
            appSettingsRepository.getAppSettingsByComponentName(componentName = componentName)

        if (appSettings.isEmpty()) return@withContext AppSettingsResult.EmptyAppSettings

        // Only ever write the settings the user actually ticked. Upstream wrote every row
        // regardless of its checkbox, which made unticking a setting do nothing.
        val enabledAppSettings = appSettings.filter { it.enabled }

        if (enabledAppSettings.isEmpty()) return@withContext AppSettingsResult.DisabledAppSettings

        val userData = userDataRepository.userData.first()

        // Auto-hide settings (IMD+) is holding the device down. Two outcomes, and neither of
        // them is an ordinary launch:
        //
        //  - The profile asks for nothing IMD+ has not already hidden, so there is nothing to
        //    do and the app is simply opened, with no notification - see AlreadyHidden.
        //  - The profile asks for something more. Hiding it would leave a device that neither
        //    mechanism's revert puts back: IMD+'s revert restores what IMD+ hid, this app's
        //    restores what this app hid, and nothing owns the overlap. Refused, and said.
        if (userData.autoHideRunning) {
            val covered = autoHideCoversProfile(
                profileTargets = profileHiddenTargets(appSettings = enabledAppSettings),
                hiddenTargets = userData.effectiveSettingsToHide,
            )

            return@withContext if (covered) {
                AppSettingsResult.AlreadyHidden
            } else {
                AppSettingsResult.AutoHideConflict
            }
        }

        // ⚠ **The grant, before anything is touched.** The catch further down already turns a
        // refused write into NoPermission, and it is kept — but it only fires once the run has
        // begun, and by then it may have withdrawn Display over other apps through Shizuku,
        // which does not use this permission and so would still be sitting withdrawn. Asking
        // first means the ordinary case stops before it can change anything at all. Same
        // reasoning, same position, as ApplySettingsToHideUseCase.

        // ⚠ **The force-close gate.** Settings are down and no hide in this process put them
        // there, so the process that did is gone and its revert notification went with it.
        // Nothing is written and nothing is launched — the caller shows the popup, and the
        // user chooses between putting the old state back and letting go of it.
        //
        // Suppressed here rather than by each caller: IMD+ draws its dialog over the app the
        // user just opened, which is itself a window change its detector sees, so a dialog
        // nobody has answered yet would put another one up behind it.
        if (PriorHide.shouldWarn(settingsHidden = userData.settingsHidden)) {
            PriorHide.suppress()

            return@withContext AppSettingsResult.HiddenFromPreviousUse
        }

        if (!secureSettingsWrapper.hasWriteSecureSettingsPermission()) {
            return@withContext AppSettingsResult.NoPermission
        }

        // Whether suIMD is going to take the services list into its own hands for this
        // app. When it is, the accessibility_enabled row is left out of the plain write
        // loop below: the wrapper derives that flag from the resulting list, and two
        // writers racing on it produce a state the Settings app renders inconsistently.
        val managesAccessibility = userData.managedAccessibilityServices.isNotEmpty() &&
            AppSettingKeys.hidesAccessibilityServices(enabledAppSettings)

        // Whether this profile withdraws overlay access. Unlike accessibility_enabled there
        // is no real settings row behind the marker, so it comes out of the write loop
        // whether or not the overlay work then happens.
        //
        // Gated on the master switch in Advanced as well as on the marker: a profile
        // written while overlay management was on must stop hiding when it is switched off,
        // or the one place the feature could still fire would be the one place it cannot be
        // seen. Reverting such a profile is not gated - see RevertAppSettingsUseCase.
        val managesOverlay = userData.overlayManageable &&
            AppSettingKeys.hidesOverlayAccess(enabledAppSettings)

        // Whether that work is already done - the same repeat-launch fail-safe the
        // device-wide path uses, and for the same reason: a second launch with overlay access
        // already withdrawn would otherwise spend ten seconds starting Shizuku to write a
        // withdrawal that withdraws nothing, then stop it again.
        //
        // The holder is device-wide even here. Overlay holds are not kept per app - both
        // paths go through the same SetManualTargetUseCase - so one profile's hide is visible
        // to the next launch whichever mechanism made it, which is exactly what has to be
        // true for this to be safe.
        val overlayAlreadyWithdrawn = overlayAlreadyWithdrawn(
            managedOverlayPackages = userData.managedOverlayPackages,
            heldOverlayPackages = userData.heldOverlayPackages,
        )

        // Whether this profile stops the Shizuku service. Like the overlay marker it is not a
        // real settings row, so it comes out of the write loop below and is acted on
        // separately — after the writes are recorded, before they are applied.
        val stoppingShizuku = AppSettingKeys.stopsShizukuService(enabledAppSettings)

        // Read before the overlay step below starts a fork, which brings the debugging
        // transport up with it. It decides whether the Shizuku fallback may put USB debugging
        // back: a profile that never mentions adb_enabled must not end a launch with debugging
        // switched on, and nothing would record that this app had done it.
        val usbInitiallyOn = stoppingShizuku &&
            getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.UsbDebugging)

        // The same reading for wireless debugging: spec item 7's stop drops both transports,
        // so both have to be put back only where they were.
        val wirelessInitiallyOn = stoppingShizuku &&
            getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.WirelessDebugging)

        val settingsToWrite = enabledAppSettings
            .filterNot { managesAccessibility && it.key == AppSettingKeys.ACCESSIBILITY_ENABLED }
            .filterNot { it.key == AppSettingKeys.SYSTEM_ALERT_WINDOW }
            .filterNot { it.key == AppSettingKeys.SHIZUKU_SERVICE }

        // Before the settings writes, for the same reason the device-wide path does it
        // first: overlay AppOps need Shizuku, and Shizuku needs the debugging transport this
        // profile is probably about to switch off.
        if (managesOverlay && !overlayAlreadyWithdrawn) {
            if (!getManualTargetStatesUseCase().isEnabled(ManualRevertTarget.Shizuku)) {
                shizukuStartTracker.beginOverlay(OverlayStart.Hide)

                val started = try {
                    setManualTargetUseCase(ManualRevertTarget.Shizuku, enabled = true)
                } finally {
                    shizukuStartTracker.endOverlay(OverlayStart.Hide)
                }

                if (!started) return@withContext AppSettingsResult.OverlayFailure
            }

            val hidden = withContext(NonCancellable) {
                setManualTargetUseCase(
                    target = ManualRevertTarget.DisplayOverOtherApps,
                    enabled = false,
                )
            }

            if (!hidden) return@withContext AppSettingsResult.OverlayFailure
        }

        // Whether *this* launch is the one that took overlay access away. Recorded further
        // down, once recordCurrentValues has written the snapshot it would otherwise
        // overwrite; held here because that is where it is known.
        //
        // False when the step was skipped because the access was already withdrawn, and that
        // is the point: an app that found the work already done has no claim on undoing it,
        // so its revert leaves overlay access alone rather than handing it back while the app
        // that actually hid it is still open.
        val withdrewOverlay = managesOverlay && !overlayAlreadyWithdrawn

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

            // Against this app, and only when this launch did the withdrawing - the same
            // bargain the Shizuku note below makes, for the same reason. After
            // recordCurrentValues, which writes the per-app record from the snapshot taken at
            // the top of the launch and would otherwise overwrite this.
            if (withdrewOverlay) {
                withContext(NonCancellable) { recordOverlayHidden(componentName = componentName) }
            }

            // Stop the Shizuku service if this profile asks for it, before the writes below
            // switch off the transport it rides on. Done after recordCurrentValues so the USB
            // debugging reading the fallback might disturb is captured first, and recorded
            // against this app — only when a running service was actually taken down — so that
            // this app's revert, and no other's, starts it again.
            if (stoppingShizuku) {
                // Not cancellable: half-stopping the service — or cycling USB debugging and
                // not putting it back — is exactly the partial state that launching the app
                // could otherwise interrupt this into.
                val outcome = withContext(NonCancellable) {
                    stopShizukuServiceUseCase(
                        // Put back only if it was on to start with and this profile is not
                        // hiding it itself.
                        usbFinalEnabled = usbInitiallyOn &&
                            !hidesUsbDebugging(enabledAppSettings),
                        // ⚠ **Its own answer since spec item 7**, which drops both transports.
                        // A profile that never mentions adb_wifi_enabled must end the launch
                        // with wireless debugging exactly where it found it.
                        wirelessFinalEnabled = wirelessInitiallyOn &&
                            !hidesWirelessDebugging(enabledAppSettings),
                    )
                }

                if (outcome.stopped) {
                    withContext(NonCancellable) { recordShizukuStopped(componentName = componentName) }
                }
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

            // IMD's own IMD+ detector, off with every launch that actually hides something,
            // whatever this profile says about accessibility services - see the same call in
            // ApplySettingsToHideUseCase. Its hold is device-wide rather than this app's, so
            // one app's revert leaves it alone; the last pending revert is what puts it back.
            withContext(NonCancellable) { runCatching { disableAutoHideServiceUseCase() } }

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

        // ⚠ **The first-owner rule.** A setting already at the value this profile is about
        // to write is one somebody else is holding down — another app's launch, a device-wide
        // hide, or the user themselves — so this hide is not the one that owes putting it back
        // and records nothing for it. See [hideOwnsRevert] for what went wrong without it.
        //
        // mapNotNull rather than associate + filter: the read is a binder call each, and there
        // is no reason to make one for a key whose answer cannot be recorded anyway — it is
        // needed to *decide* that, but the pair is dropped in the same pass rather than built
        // and thrown away.
        val measured = unrecorded.mapNotNull { setting ->
            val current = secureSettingsWrapper.getSecureSettingValue(
                settingType = setting.settingType,
                key = setting.key,
            )

            if (!hideOwnsRevert(currentValue = current, valueOnLaunch = setting.valueOnLaunch)) {
                return@mapNotNull null
            }

            SettingSnapshot.idOf(settingType = setting.settingType, key = setting.key) to current
        }.toMap()

        // Everything this profile hides was already down. Nothing is owed, and the write is
        // skipped for the same reason as the one above it: a proto rewrite for no change.
        if (measured.isEmpty()) return

        userDataRepository.updateSettingStateBefore(
            states = userData.settingStateBefore +
                (componentName to SettingSnapshot.merge(existing = existing, measured = measured)),
        )
    }

    /**
     * Whether this profile switches USB debugging off itself, in which case the Shizuku
     * fallback must leave it off rather than putting it back. Pinned to the Global table: the
     * template dialog will accept any setting type, and a row keyed `adb_enabled` under Secure
     * writes somewhere else entirely, so it says nothing about the flag this asks about.
     */
    private fun hidesUsbDebugging(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.settingType == SettingType.GLOBAL &&
            it.key == AppSettingKeys.ADB_ENABLED &&
            it.valueOnLaunch == "0"
    }

    /** The wireless half of the question above, asked since spec item 7 drops both. */
    private fun hidesWirelessDebugging(appSettings: List<AppSetting>): Boolean = appSettings.any {
        it.enabled &&
            it.settingType == SettingType.GLOBAL &&
            it.key == AppSettingKeys.ADB_WIFI_ENABLED &&
            it.valueOnLaunch == "0"
    }

    /**
     * Notes, non-cumulatively, that this app stopped a running Shizuku service — so its revert
     * starts the service again and another app's revert does not.
     *
     * Re-reads the record first: [recordCurrentValues] has just written to it, so the copy on
     * the [UserData] captured at the top of the launch is stale. Kept in the same per-app map
     * as the settings snapshots, under a reserved id, so it is cleared together with them on
     * revert; and skipped when the note is already there, so a shortcut tapped twice does not
     * rewrite the proto for nothing.
     */
    private suspend fun recordShizukuStopped(componentName: String) {
        val current = userDataRepository.userData.first().settingStateBefore

        val forApp = current[componentName].orEmpty()

        if (SettingSnapshot.SHIZUKU_STOPPED_ID in forApp) return

        userDataRepository.updateSettingStateBefore(
            states = current + (componentName to forApp + (SettingSnapshot.SHIZUKU_STOPPED_ID to "1")),
        )
    }

    /**
     * Notes, non-cumulatively, that this app's launch withdrew overlay access — so its revert
     * gives it back and another app's revert does not.
     *
     * The same shape as [recordShizukuStopped], and the same reasons: re-read first because
     * `recordCurrentValues` has just written to this map, kept under a reserved id in the
     * per-app record so it is cleared together with the snapshots on revert, and skipped when
     * the note is already there.
     */
    private suspend fun recordOverlayHidden(componentName: String) {
        val current = userDataRepository.userData.first().settingStateBefore

        val forApp = current[componentName].orEmpty()

        if (SettingSnapshot.OVERLAY_HIDDEN_ID in forApp) return

        userDataRepository.updateSettingStateBefore(
            states = current + (componentName to forApp + (SettingSnapshot.OVERLAY_HIDDEN_ID to "1")),
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
