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
package com.android.geto.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.common.AutoRevertPending
import com.android.geto.domain.framework.DiagnosticLogStore
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.AutoHideServiceState
import com.android.geto.domain.model.AutoUnhideChecks
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.screenLockAfterTile
import com.android.geto.domain.model.tileAfterScreenLock
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyIconStyleUseCase
import com.android.geto.domain.usecase.DisableAutoHideServiceUseCase
import com.android.geto.domain.usecase.EnableAutoHideServiceUseCase
import com.android.geto.domain.usecase.GetAccessibilityServicesUseCase
import com.android.geto.domain.usecase.GetAutoHideServiceStateUseCase
import com.android.geto.domain.usecase.GetAutoUnhideChecksUseCase
import com.android.geto.domain.usecase.GetInstalledAppsUseCase
import com.android.geto.domain.usecase.GetOverlayPackagesUseCase
import com.android.geto.domain.usecase.GrantAutoUnhideAccessUseCase
import com.android.geto.domain.usecase.RequestShizukuPermissionUseCase
import com.android.geto.domain.usecase.RetireAutoHideServiceUseCase
import com.android.geto.domain.usecase.SyncAutoHideDetectorSelectionUseCase
import com.android.geto.service.SettingsObserverService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted.Companion.WhileSubscribed
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withTimeoutOrNull
import javax.inject.Inject

/**
 * How many times to ask for the overlay list before reporting that it cannot be read, and how
 * long to wait between tries.
 *
 * Sized for a cold start: the read goes through Shizuku's binder, which is commonly not ready
 * for the first second or so after the app opens. Six tries half a second apart covers that
 * without making a genuine "Shizuku is not running" take noticeably long to say so.
 */
private const val OVERLAY_READ_ATTEMPTS = 6

private const val OVERLAY_READ_RETRY_MILLIS = 500L

/**
 * How long the "performing all the pending reverts" spinner is allowed to sit there before
 * the app is re-launched anyway.
 *
 * A ceiling on the *wait*, not on the work. The reverts run on the application scope and
 * refuse cancellation, so the sweep finishes whatever this does; all that expires is the
 * app's willingness to keep the user looking at a spinner.
 *
 * Thirteen seconds because the worst case is a revert that has to start Shizuku, which waits
 * up to ten for a fork to come up, plus the settings writes on either side of it. Anything
 * longer than that has stopped being a wait and become a hang.
 */
private const val PENDING_REVERTS_WAIT_MILLIS = 13_000L

/**
 * Everything the settings list needs in order to draw the Auto-hide settings (IMD+) row and
 * its page, gathered into one object.
 *
 * One parameter rather than nine. The screen is three composables deep and each of them would
 * otherwise carry the same nine arguments — which is how the existing list got to thirty. The
 * requirements themselves are deliberately *not* in here: half of them come from [UserData] and
 * half from Android, and both halves are already in scope where the page is drawn.
 */
internal data class AutoHideHandle(
    val serviceState: AutoHideServiceState,
    val enabling: Boolean,
    val blocked: Boolean,
    val onUpdateEnabled: (Boolean) -> Unit,
    /**
     * Switch IMD+ on by first putting its own detector back.
     *
     * Only for the case where the detector is the single unmet requirement and the user has
     * had IMD+ on before; the row decides that, because it is the one holding the live
     * requirements.
     */
    val onEnableWithDetector: () -> Unit,
    val onSetService: (Boolean) -> Unit,
    val onRequestShizukuPermission: () -> Unit,
    val onUpdatePackages: (List<String>) -> Unit,
    val onUpdateNoKillOnLaunch: (Boolean) -> Unit,
    val onClearBlocked: () -> Unit,
    val onRefresh: () -> Unit,
)

/**
 * Auto unhide's half of the IMD+ section, gathered the way [AutoHideHandle] gathers its own.
 *
 * A handle rather than eleven more parameters on `SettingsScreen`, for the reason the one
 * above exists: the screen already carries thirty, and a feature's worth of callbacks travels
 * better as one object than as a dozen positional arguments nobody can read at the call site.
 */
internal data class AutoUnhideHandle(
    val checks: AutoUnhideChecks,
    val onUpdateEnabled: (Boolean) -> Unit,
    val onUpdateTriggers: (onSwipe: Boolean, onScreenLock: Boolean, onIdle: Boolean) -> Unit,
    val onUpdateScreenLockMinutes: (Int) -> Unit,
    val onUpdateIdleMinutes: (Int) -> Unit,
    val onGrantDumpPermission: () -> Unit,
    val onGrantUsageAccess: () -> Unit,
    val adbCommand: () -> String,
    val onRefresh: () -> Unit,
    val onUpdateUsedFor: (onAppLaunch: Boolean, onTile: Boolean) -> Boolean,
)

/**
 * The diagnostic log, as the About section needs it.
 *
 * A handle for the reason the two beside it are: the About section is one composable and this
 * is five callbacks, which travel better together than as five more parameters on a screen
 * that already carries thirty.
 */
internal data class DiagnosticsHandle(
    val enabled: Boolean,
    val log: String,
    val onOpen: () -> Unit,
    val onSetEnabled: (Boolean) -> Unit,
    val onClear: () -> Unit,
    val onExport: (String) -> Unit,
)

/**
 * Where a change of Hiding or Unhiding framework has got to.
 *
 * ⚠ Declared at file level, not nested: `check16_when` cannot parse an indented enum — it
 * needs the closing brace at column 0.
 */
enum class FrameworkSave {
    Idle,

    /**
     * The sweep cleared and the preference was written.
     *
     * Rests here until [SettingsViewModel.clearFrameworkSave], which is what lets the framework
     * choosers close themselves on a save that worked and stay open on one that did not.
     */
    Saved,

    /** Settling the outstanding debts, behind a spinner. The preference has not moved yet. */
    Running,

    /**
     * The sweep could not clear everything, so the preference was **not** written.
     *
     * Leaving it unwritten is the point: a framework that changed anyway would leave the
     * outstanding hide readable only by the framework no longer selected, which is the
     * stranded debt the sweep exists to prevent, reached by a different road.
     */
    Failed,
}

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val applyIconStyleUseCase: ApplyIconStyleUseCase,
    private val getAutoUnhideChecksUseCase: GetAutoUnhideChecksUseCase,
    private val retireAutoHideServiceUseCase: RetireAutoHideServiceUseCase,
    private val syncAutoHideDetectorSelectionUseCase: SyncAutoHideDetectorSelectionUseCase,
    private val grantAutoUnhideAccessUseCase: GrantAutoUnhideAccessUseCase,
    private val diagnosticLogStore: DiagnosticLogStore,
    private val getAccessibilityServicesUseCase: GetAccessibilityServicesUseCase,
    private val getOverlayPackagesUseCase: GetOverlayPackagesUseCase,
    private val getInstalledAppsUseCase: GetInstalledAppsUseCase,
    private val getAutoHideServiceStateUseCase: GetAutoHideServiceStateUseCase,
    private val enableAutoHideServiceUseCase: EnableAutoHideServiceUseCase,
    private val disableAutoHideServiceUseCase: DisableAutoHideServiceUseCase,
    private val requestShizukuPermissionUseCase: RequestShizukuPermissionUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    val settingsUiState = userDataRepository.userData.map(SettingsUiState::Success).stateIn(
        scope = viewModelScope,
        started = WhileSubscribed(5_000),
        initialValue = SettingsUiState.Loading,
    )

    val isServiceRunning = SettingsObserverService.isRunning.stateIn(
        scope = viewModelScope,
        started = WhileSubscribed(5_000),
        initialValue = false,
    )

    private val _accessibilityServices =
        MutableStateFlow<List<AccessibilityServiceData>>(emptyList())
    val accessibilityServices = _accessibilityServices.asStateFlow()

    private val _installedApps = MutableStateFlow<List<InstalledAppData>>(emptyList())
    val installedApps = _installedApps.asStateFlow()

    /**
     * Whether a change of framework is in progress, and whether it could not be made.
     *
     * Read by the settings screen to put a blocking spinner up and, on [FrameworkSave.Failed],
     * to say why nothing changed.
     */
    private val _frameworkSave = MutableStateFlow(FrameworkSave.Idle)
    val frameworkSave = _frameworkSave.asStateFlow()

    fun clearFrameworkSave() {
        _frameworkSave.update { FrameworkSave.Idle }
    }

    fun updateTheme(theme: Theme) {
        viewModelScope.launch {
            userDataRepository.updateTheme(theme = theme)
        }
    }

    fun updateDynamicTheme(dynamicTheme: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateDynamicTheme(dynamicTheme = dynamicTheme)
        }
    }

    /** The bottom-edge band, on or off. Stored as its negation - see the proto comment on 75. */
    fun updateProgressiveBlur(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateProgressiveBlur(enabled = enabled)
        }
    }

    /** Pure black backgrounds in a dark scheme. */
    fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        viewModelScope.launch {
            userDataRepository.updateBlurSettings(
                radiusDp = radiusDp,
                tintPercent = tintPercent,
                fadeDp = fadeDp,
            )
        }
    }

    fun updateOledBackground(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateOledBackground(enabled = enabled)
        }
    }

    /** Which app-drawer entries IMD publishes. `DrawerShortcuts` in :app does the rest. */
    fun updateDrawerShortcuts(manager: Boolean, hideUnhide: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateDrawerShortcuts(manager = manager, hideUnhide = hideUnhide)
        }
    }

    /** Generates the Tasker auth key if there is not one yet; a no-op once there is. */
    fun ensureTaskerAuthKey() {
        viewModelScope.launch {
            userDataRepository.ensureTaskerAuthKey()
        }
    }

    /** Rotates the Tasker auth key, retiring every macro built on the old one. */
    fun refreshTaskerAuthKey() {
        viewModelScope.launch {
            userDataRepository.refreshTaskerAuthKey()
        }
    }

    /** The master switch for the Tasker integration; enabling also generates a key if none. */
    fun updateTaskerIntegrationEnabled(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateTaskerIntegrationEnabled(enabled = enabled)
        }
    }

    /**
     * The master switch for overlay management.
     *
     * Nothing is undone here on the way off. A debt taken while it was on is still repaid
     * by the next revert - see UserData.effectiveRevertDefaults - and the stored overlay
     * ticks are left alone so switching the feature back on returns it as it was left.
     */
    /**
     * Whether a memory restore may switch wireless debugging back on.
     *
     * Written from the Settings to hide/unhide dialog's Save, alongside the map, so both
     * halves of that dialog commit on the same press.
     */
    fun updateRestoreWirelessDebugging(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateRestoreWirelessDebugging(enabled = enabled)
        }
    }

    fun updateManageShizuku(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateManageShizuku(enabled = enabled)
        }
    }

    /**
     * Switching off also drops any marker already armed, so a launch made while it was on
     * cannot revert after the user has turned it off.
     */
    fun updateAutoRevertOnReturn(enabled: Boolean) {
        if (!enabled) AutoRevertPending.clear()

        viewModelScope.launch {
            userDataRepository.updateAutoRevertOnReturn(enabled = enabled)
        }
    }

    /**
     * Saves the Icon style and redraws everything that has already rendered an icon.
     *
     * Through a use case rather than written here, because "redraw everything" reaches three
     * places this ViewModel has no business knowing about — see [ApplyIconStyleUseCase].
     */
    fun updateIconStyle(iconStyle: IconStyle) {
        viewModelScope.launch {
            applyIconStyleUseCase(iconStyle = iconStyle)
        }
    }

    fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {
        viewModelScope.launch {
            userDataRepository.updateShizukuForkMode(shizukuForkMode = shizukuForkMode)
        }
    }

    fun updateShizukuAuthKey(shizukuAuthKey: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuAuthKey(shizukuAuthKey = shizukuAuthKey)
        }
    }

    fun updateShizukuPackageName(shizukuPackageName: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuPackageName(shizukuPackageName = shizukuPackageName)
        }
    }

    fun updateShizukuStartAction(shizukuStartAction: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuStartAction(shizukuStartAction = shizukuStartAction)
        }
    }

    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        viewModelScope.launch {
            userDataRepository.updateManagerRows(states = states)
        }
    }

    fun updateManagedAccessibilityServices(components: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateManagedAccessibilityServices(components = components)
        }
    }

    fun saveHidingFramework(hidingFramework: HidingFramework) {
        saveFramework { userDataRepository.updateHidingFramework(hidingFramework = hidingFramework) }
    }

    fun saveUnhidingFramework(unhidingFramework: UnhidingFramework) {
        saveFramework {
            userDataRepository.updateUnhidingFramework(unhidingFramework = unhidingFramework)
        }
    }

    /**
     * Settles every outstanding debt, then stores the new framework — and only then.
     *
     * ⚠ **The order is the reverse of the mechanism switch this replaces, at the author's
     * instruction, and the swap needs its own guard.** Storing first used to be deliberate:
     * nothing started afterwards could add to the debt about to be cleared. Sweeping first
     * re-opens that window — a launch landing mid-sweep records a debt under the framework
     * that is about to stop reading it — so the state is re-read after the sweep and the
     * preference is written only if the device is genuinely clear. Anything left, whether it
     * survived the sweep or arrived during it, is [FrameworkSave.Failed] and changes nothing.
     *
     * The sweep runs on the application scope and is only *waited* for here: it writes secure
     * settings and can spend ten seconds starting Shizuku, so it must not be tied to this
     * ViewModel or to the wait that gives up on it.
     */
    private fun saveFramework(store: suspend () -> Unit) {
        if (_frameworkSave.value == FrameworkSave.Running) return

        _frameworkSave.update { FrameworkSave.Running }

        viewModelScope.launch {
            if (userDataRepository.userData.first().settingsHidden) {
                val sweep = appScope.launch { settingsHiddenRunner.flushPendingReverts() }

                withTimeoutOrNull(PENDING_REVERTS_WAIT_MILLIS) { sweep.join() }

                if (userDataRepository.userData.first().settingsHidden) {
                    _frameworkSave.update { FrameworkSave.Failed }

                    return@launch
                }
            }

            store()

            // ⚠ **Saved rather than back to Idle.** Idle cannot tell "finished" from "never
            // started", and a StateFlow would conflate Running and Idle away entirely if both
            // landed between two recompositions - so a screen waiting for the save to finish
            // could legitimately observe neither. Saved rests here until the screen clears it,
            // the same shape Failed already has.
            _frameworkSave.update { FrameworkSave.Saved }
        }
    }

    fun updateSettingsToHide(states: Map<ManualRevertTarget, Boolean>) {
        viewModelScope.launch {
            userDataRepository.updateSettingsToHide(states = states)
        }
    }

    fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        viewModelScope.launch {
            userDataRepository.updateRevertDefaults(states = states)
        }
    }

    /**
     * Read on demand rather than observed. There is no content observer for the
     * installed-services list, and re-reading when the picker opens is both cheaper and
     * more accurate than a stale cached copy.
     */
    /**
     * Null until asked, and null again whenever the list could not be read - which is the
     * whole reason this is nullable rather than an empty list. The screen opens the picker on
     * a list and the "needs Shizuku" notice on a null.
     */
    private val _overlayPackages = MutableStateFlow<List<OverlayPackageData>?>(null)
    val overlayPackages = _overlayPackages.asStateFlow()

    /**
     * True while the list is being read, which is a third state the screen needs and did not
     * have. Without it "not read yet" and "could not be read" were the same null, so opening
     * the picker on a cold start showed the needs-Shizuku notice while the read was still in
     * flight - dismiss it, tap again, and two or three tries later the list appeared.
     */
    private val _overlayPackagesLoading = MutableStateFlow(false)
    val overlayPackagesLoading = _overlayPackagesLoading.asStateFlow()

    fun updateManagedOverlayPackages(packages: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateManagedOverlayPackages(packages = packages)
        }
    }

    /**
     * Reads the overlay list, retrying while Shizuku comes up.
     *
     * The list can only be read through a running Shizuku, and on a cold start the binder is
     * often not ready for the first second or two - which is exactly the window in which
     * somebody taps this. Retrying inside one call is what turns "an error, twice, then it
     * works" into a spinner that resolves on its own.
     */
    fun refreshOverlayPackages() {
        viewModelScope.launch {
            _overlayPackagesLoading.update { true }

            try {
                var packages: List<OverlayPackageData>? = null

                // A `for` with a real `break`. This was a `repeat { … return@repeat }`, and
                // `return@repeat` returns from that one iteration - it is `continue`, not
                // `break` - so a read that succeeded immediately was still followed by five
                // more, each one a full trip through Shizuku and the package manager. That
                // is where the ten to fifteen seconds came from.
                for (attempt in 0 until OVERLAY_READ_ATTEMPTS) {
                    packages = getOverlayPackagesUseCase()

                    if (packages != null) break

                    // No delay after the last attempt: it would be a pause with nothing left
                    // to wait for.
                    if (attempt < OVERLAY_READ_ATTEMPTS - 1) delay(OVERLAY_READ_RETRY_MILLIS)
                }

                _overlayPackages.update { packages }
            } finally {
                // In a finally so a throw out of the use case cannot leave the spinner up
                // forever with no way back.
                _overlayPackagesLoading.update { false }
            }
        }
    }

    fun refreshAccessibilityServices() {
        viewModelScope.launch {
            _accessibilityServices.update { getAccessibilityServicesUseCase() }
        }
    }

    // ---- Auto-hide settings (IMD+) ----

    /**
     * The two IMD+ requirements that have to be asked for: is the detector actually bound, and
     * has Shizuku granted its permission.
     *
     * Re-read whenever the page resumes, because both are things somebody else can take away
     * while the user is off in Android's settings switching them on.
     */
    private val _autoHideServiceState = MutableStateFlow(AutoHideServiceState())
    val autoHideServiceState = _autoHideServiceState.asStateFlow()

    fun refreshAutoHideServiceState() {
        viewModelScope.launch {
            _autoHideServiceState.update { getAutoHideServiceStateUseCase() }
        }
    }

    /**
     * Auto unhide's own three answers from Android: the two shell-granted permissions and
     * whether this version has the exit-reasons API at all.
     *
     * Re-read on the same one-second poll the IMD+ requirements use, because a `pm grant` run
     * from a computer lands without IMD being told — the dot has to go green on its own or the
     * user is left wondering whether the command worked.
     */
    private val _autoUnhideChecks = MutableStateFlow(AutoUnhideChecks())
    val autoUnhideChecks = _autoUnhideChecks.asStateFlow()

    fun refreshAutoUnhideChecks() {
        viewModelScope.launch {
            _autoUnhideChecks.update { getAutoUnhideChecksUseCase() }
        }
    }

    /**
     * The master switch, and the trigger it cannot run without.
     *
     * ⚠ **Switching auto unhide on ticks the screen-lock trigger**, the author's failsafe — the
     * same shape as [screenLockAfterTile], and for the same reason: a control whose promise rests
     * on that backup ticks it rather than refusing until the user goes and finds it.
     *
     * Only ever on. Switching auto unhide *off* says nothing about a trigger the user may want
     * for its own sake, so the stored answer is left where they put it.
     */
    fun updateAutoUnhideEnabled(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideEnabled(enabled = enabled)

            if (!enabled) return@launch

            val userData = userDataRepository.userData.first()

            if (userData.autoUnhideOnScreenLock) return@launch

            userDataRepository.updateAutoUnhideTriggers(
                onSwipe = userData.autoUnhideOnSwipe,
                onScreenLock = true,
                onIdle = userData.autoUnhideOnIdle,
            )
        }
    }

    /** All three at once — see the data source for why they cannot be written apart. */
    /**
     * The three triggers, and the tile condition that depends on one of them.
     *
     * ⚠ **Unticking the screen-lock trigger unticks the Hide settings tile condition with it**
     * — [tileAfterScreenLock], the author's rule. Applied here rather than in the page so it
     * holds however the call arrives, which is the same reasoning
     * [updateAutoUnhideUsedFor] already uses for its own refusal.
     *
     * If that leaves neither condition ticked, nothing else happens and nothing else has to:
     * `autoUnhideSwitchOn` reads `satisfied`, which needs one of each, so the switch goes off
     * on its own and the user's stored answer is left where they put it.
     */
    fun updateAutoUnhideTriggers(onSwipe: Boolean, onScreenLock: Boolean, onIdle: Boolean) {
        viewModelScope.launch {
            val userData = userDataRepository.userData.first()

            userDataRepository.updateAutoUnhideTriggers(
                onSwipe = onSwipe,
                onScreenLock = onScreenLock,
                onIdle = onIdle,
            )

            val onTile = tileAfterScreenLock(
                onTile = userData.autoUnhideOnTile,
                onScreenLock = onScreenLock,
            )

            if (onTile != userData.autoUnhideOnTile) {
                userDataRepository.updateAutoUnhideUsedFor(
                    onAppLaunch = userData.autoUnhideOnAppLaunch,
                    onTile = onTile,
                )
            }
        }
    }

    fun updateAutoUnhideScreenLockMinutes(minutes: Int) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideScreenLockMinutes(minutes = minutes)
        }
    }

    /**
     * Both "used for" answers, refusing the write that would clear the last one.
     *
     * Refused here rather than prevented in the UI, so the rule holds however the call
     * arrives: a feature switched on with neither box ticked can never act, and a user
     * waiting for settings that are not coming is worse off than one who knows it is off.
     */
    fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean): Boolean {
        if (!onAppLaunch && !onTile) return false

        viewModelScope.launch {
            val userData = userDataRepository.userData.first()

            userDataRepository.updateAutoUnhideUsedFor(
                onAppLaunch = onAppLaunch,
                onTile = onTile,
            )

            // ⚠ **Ticking the tile condition ticks the screen-lock trigger** -
            // [screenLockAfterTile], the other half of the author's rule. Only ever on: he
            // asked for the tile to *check* it, and unticking the tile is not a statement
            // about a trigger the user may want for its own sake.
            val onScreenLock = screenLockAfterTile(
                onScreenLock = userData.autoUnhideOnScreenLock,
                onTile = onTile,
            )

            if (onScreenLock != userData.autoUnhideOnScreenLock) {
                userDataRepository.updateAutoUnhideTriggers(
                    onSwipe = userData.autoUnhideOnSwipe,
                    onScreenLock = onScreenLock,
                    onIdle = userData.autoUnhideOnIdle,
                )
            }
        }

        return true
    }

    fun updateAutoUnhideIdleMinutes(minutes: Int) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideIdleMinutes(minutes = minutes)
        }
    }

    /**
     * Asks Shizuku to grant the dump permission, then re-reads rather than trusting it.
     *
     * The grant's own answer says the command was accepted, not that the permission is held —
     * and the dot beside the button is the thing the user is actually looking at.
     */
    fun grantAutoUnhideDumpPermission() {
        viewModelScope.launch {
            grantAutoUnhideAccessUseCase.grantDumpPermission()

            _autoUnhideChecks.update { getAutoUnhideChecksUseCase() }
        }
    }

    fun grantAutoUnhideUsageAccess() {
        viewModelScope.launch {
            grantAutoUnhideAccessUseCase.grantUsageAccess()

            _autoUnhideChecks.update { getAutoUnhideChecksUseCase() }
        }
    }

    /** The copyable command for the adb route, built from this app's own package name. */
    fun autoUnhideAdbCommand(): String = grantAutoUnhideAccessUseCase.adbCommand()

    /**
     * What the diagnostics viewer is showing.
     *
     * Read on demand rather than observed: the log is a file that only changes when something
     * else in the app happens, and a flow watching it would be the background work this
     * feature is specifically built not to do.
     */
    private val _diagnosticLog = MutableStateFlow("")
    val diagnosticLog = _diagnosticLog.asStateFlow()

    fun refreshDiagnosticLog() {
        viewModelScope.launch {
            _diagnosticLog.update { diagnosticLogStore.read() }
        }
    }

    fun setDiagnosticsEnabled(enabled: Boolean) {
        viewModelScope.launch {
            diagnosticLogStore.setEnabled(enabled = enabled)

            _diagnosticLog.update { diagnosticLogStore.read() }
        }
    }

    fun clearDiagnosticLog() {
        viewModelScope.launch {
            diagnosticLogStore.clear()

            _diagnosticLog.update { "" }
        }
    }

    fun exportDiagnosticLog(destinationUri: String) {
        viewModelScope.launch {
            diagnosticLogStore.export(destinationUri = destinationUri)
        }
    }

    /**
     * True while the detector is being switched on, so the row can say something during the
     * two and a half seconds it may spend waiting for the system to bind it.
     */
    private val _autoHideEnabling = MutableStateFlow(false)
    val autoHideEnabling = _autoHideEnabling.asStateFlow()

    /**
     * Set when every automatic route to switching the detector on has failed, which is what
     * raises the popup naming the two things the user can do by hand. Cleared by the screen
     * when the popup is dismissed.
     */
    private val _autoHideAccessibilityBlocked = MutableStateFlow(false)
    val autoHideAccessibilityBlocked = _autoHideAccessibilityBlocked.asStateFlow()

    fun clearAutoHideAccessibilityBlocked() {
        _autoHideAccessibilityBlocked.update { false }
    }

    /**
     * Moves IMD's own accessibility service, and reports what actually happened.
     *
     * On the way on this is the whole documented flow — secure settings first, the Shizuku
     * restricted-settings AppOp second, the popup only if both come to nothing. On the way off
     * it is the plain disable, recorded as a hold like any other so a revert puts it back.
     *
     * Runs on the application scope: switching a service on waits for the system to bind it,
     * and closing the page part-way through would leave the wait abandoned with the state
     * already half written.
     */
    fun setAutoHideService(enabled: Boolean) {
        if (_autoHideEnabling.value) return

        _autoHideEnabling.update { true }

        viewModelScope.launch {
            try {
                val ok = appScope.async {
                    if (enabled) {
                        enableAutoHideServiceUseCase()
                    } else {
                        disableAutoHideServiceUseCase()
                    }
                }.await()

                // Only switching *on* has anything to explain. A disable that fails leaves the
                // detector running, which the refreshed row below shows for itself.
                if (enabled && !ok) _autoHideAccessibilityBlocked.update { true }
            } finally {
                _autoHideEnabling.update { false }

                refreshAutoHideServiceState()
            }
        }
    }

    /** Asks Shizuku for its permission, showing its own prompt, then re-reads the answer. */
    fun requestShizukuPermission() {
        viewModelScope.launch {
            appScope.async { requestShizukuPermissionUseCase() }.await()

            refreshAutoHideServiceState()
        }
    }

    /**
     * Switches IMD+ on when the only thing standing in the way is IMD's own detector.
     *
     * The caller has already established that everything else is in place and that the user
     * has had IMD+ on before — see [AutoHideRequirements.onlyAccessibilityMissing] and
     * `autoHideEverEnabled`. Somebody who set this up once should not have to work out that a
     * manager toggle or an OEM cleaner is what switched their detector off.
     *
     * The detector goes on first and the preference only follows if it actually bound: writing
     * `autoHideEnabled` for a detector that never came up would leave the switch reading on
     * with nothing listening, which is the one state IMD+ must never be in.
     * [setAutoHideService] raises its own blocked dialog when the bind fails.
     */
    fun enableAutoHideWithDetector() {
        if (_autoHideEnabling.value) return

        _autoHideEnabling.update { true }

        viewModelScope.launch {
            try {
                val bound = appScope.async { enableAutoHideServiceUseCase() }.await()

                if (bound) {
                    updateAutoHideEnabledNow(enabled = true)
                } else {
                    _autoHideAccessibilityBlocked.update { true }
                }
            } finally {
                _autoHideEnabling.update { false }

                refreshAutoHideServiceState()
            }
        }
    }

    fun updateAutoHideEnabled(enabled: Boolean) {
        viewModelScope.launch {
            updateAutoHideEnabledNow(enabled = enabled)
        }
    }

    private suspend fun updateAutoHideEnabledNow(enabled: Boolean) {
        userDataRepository.updateAutoHideEnabled(enabled = enabled)

        // ⚠ **After the write, never before — r9.** The sync reads `autoHideEnabled` to decide
        // whether IMD+'s detector belongs in the managed accessibility list, so running it first
        // would sync it to the value being replaced.
        //
        // This is the single door onto that preference - `updateAutoHideEnabled` and the
        // detector-granting path above both come through here - so one call covers both
        // directions. See SyncAutoHideDetectorSelectionUseCase for why the selection has to
        // exist at all: without it the settings manager's Accessibility row greys itself while
        // the picker shows the detector ticked.
        syncAutoHideDetectorSelectionUseCase()

        // Consent, recorded the first time and never cleared. It is what lets a later attempt
        // to switch IMD+ on put the detector back by itself instead of only refusing — see
        // [enableAutoHideWithDetector].
        //
        // Not cleared on the way off: switching IMD+ off already retires the detector, which
        // is the whole of what off means, so forgetting this as well would only make the next
        // setup ask again for nothing.
        if (enabled) userDataRepository.markAutoHideEverEnabled()

        // Switching IMD+ off retires its detector rather than leaving it running for a
        // feature that is no longer on. Written first, because retiring reads the
        // preference to decide there is nothing left to owe.
        if (!enabled) {
            retireAutoHideServiceUseCase()

            _autoHideServiceState.update { getAutoHideServiceStateUseCase() }
        }
    }

    fun updateAutoHidePackages(packages: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateAutoHidePackages(packages = packages)
        }
    }

    fun updateAutoHideNoKillOnLaunch(noKill: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateAutoHideNoKillOnLaunch(noKill = noKill)
        }
    }


    /**
     * Counts completed reads of the installed-app list, whatever each one returned.
     *
     * A caller that starts a read needs to know when it has finished, and "the list changed"
     * cannot tell it: a re-read that finds exactly the same apps produces an equal list and
     * therefore no emission at all. A "loading" boolean cannot tell it either - the flag is
     * observed through a collector, so a waiter could still see the old `false` on the line
     * after asking for the read and conclude it was already done.
     *
     * A counter has neither problem. Read it before asking, wait for it to differ, and the
     * only thing that can end the wait is a read that actually completed. It is bumped after
     * the list itself is published, so a waiter woken by it is looking at the new list.
     */
    private val _installedAppsRevision = MutableStateFlow(0)
    val installedAppsRevision = _installedAppsRevision.asStateFlow()

    /** Guards against two enumerations running at once; only ever touched from the main thread. */
    private val installedAppsInFlight = MutableStateFlow(false)

    /**
     * Enumerating every installed package and rasterising an icon each is far too heavy to do
     * on the way into Settings, so the picker asks for it when it is first opened and the
     * answer is kept for the rest of the screen's life.
     *
     * [force] is the redetect button: kept means kept, so without it a second call is a no-op
     * and someone who installed the fork while Settings was open would never see it appear.
     * A read already in flight is joined rather than duplicated either way - two concurrent
     * enumerations only make both slower, and the revision below still ends the caller's wait
     * when the one already running lands.
     */
    fun refreshInstalledApps(force: Boolean = false) {
        if (installedAppsInFlight.value) return

        if (!force && _installedApps.value.isNotEmpty()) return

        installedAppsInFlight.update { true }

        viewModelScope.launch {
            try {
                _installedApps.update { getInstalledAppsUseCase() }
            } finally {
                installedAppsInFlight.update { false }

                // Last, and after the list: whoever is waiting on this wakes to find the
                // apps already published.
                _installedAppsRevision.update { it + 1 }
            }
        }
    }
}
