/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.ui.res.stringResource
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.domain.model.AutoUnhideRequirements
import com.android.geto.domain.model.accessibilityManageable
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.feature.settings.dialog.AccessibilityServicesDialog
import com.android.geto.feature.settings.dialog.AutoUnhideAdbCommandDialog
import com.android.geto.feature.settings.dialog.AutoUnhideHowItWorksDialog
import com.android.geto.feature.settings.dialog.AutoUnhideMinutesDialog
import com.android.geto.feature.settings.dialog.AutoUnhidePage
import com.android.geto.feature.settings.dialog.AutoUnhideUsedForBlockedDialog
import com.android.geto.feature.settings.dialog.OverlayPackagesDialog
import com.android.geto.feature.settings.dialog.OverlayStepWaiting
import com.android.geto.feature.settings.dialog.ManagerRowsDialog
import com.android.geto.feature.settings.dialog.RevertDefaultsDialog
import com.android.geto.feature.settings.dialog.SettingsPage
import com.android.geto.feature.settings.dialog.SettingsToHideDialog
import com.android.geto.feature.settings.dialog.rememberAutoHideSystemChecks
import com.android.geto.feature.settings.dialog.usageAccessSettingsIntent
import kotlinx.coroutines.delay
import com.android.geto.common.R as commonR

/**
 * The configuration steps of the setup flow.
 *
 * ⚠ **Each one is the dialog Settings already shows, drawn flat.** Not a page built to look like
 * it - the same composable, with `onSkip` and `stepTitle` set. A row added to any of those
 * dialogs appears here without anybody remembering to add it twice.
 *
 * ⚠ **They live here rather than in `:app` because of what they have to derive.**
 * `overlayBlockedPaths`, the own-detector rule and [AutoUnhideRequirements] are all built from
 * state that belongs to the settings screen; a copy of that reasoning in the app module would be
 * a second answer to "is this row blocked", free to drift from the first. This way `:app` needs
 * no new state at all.
 *
 * Every step takes the same pair: [onSkip] moves on without writing, [onNext] moves on after the
 * dialog has written. The dialogs decide which is which - see their `onSkip` parameter.
 */

/** The accessibility services IMD is allowed to manage. */
@Composable
fun AccessibilityStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val services by viewModel.accessibilityServices.collectAsStateWithLifecycle()

    val serviceState by viewModel.autoHideServiceState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    AccessibilityServicesDialog(
        modifier = modifier,
        accessibilityServices = services,
        selectedServices = userData.managedAccessibilityServices,
        // The same rule the settings screen uses: IMD's own detector is only special while
        // IMD+ is on, because that is the only time anything is holding it.
        ownDetector = if (userData.autoHideEnabled) serviceState.ownDetector else "",
        stepTitle = stepTitle,
        onSkip = onSkip,
        onBack = onBack,
        onDismissRequest = onNext,
        onRefresh = viewModel::refreshAccessibilityServices,
        onUpdateManagedAccessibilityServices = viewModel::updateManagedAccessibilityServices,
    )
}

/**
 * The apps whose Display over other apps IMD is allowed to manage.
 *
 * ⚠ **Always drawn, and it waits rather than vanishing.** r4r hid this step twice over - behind a
 * pre-check built from stored Shizuku values, and again behind an auto-skip the moment the read
 * came back empty - and the author saw it disappear on a device where it should have appeared.
 * Both are gone. The step is shown, the list is asked for, and if it does not arrive the page
 * says so and offers Retry.
 *
 * ⚠ **[WAIT_MILLIS] is a floor, not a timeout.** The spinner is held for the whole wait even when
 * the read fails immediately, because a failure notice that appears at the same moment the page
 * does reads as the page refusing to try. Nothing is cancelled at the end of it: a list that
 * arrives late is still drawn.
 */
@Composable
fun OverlayStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val packages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    // Bumped by Retry. Keying the effect on it is what gives each attempt its own read and its
    // own eight seconds, without a second flag saying whether one is in flight.
    var attempt by remember { mutableIntStateOf(0) }

    var waited by remember { mutableStateOf(false) }

    LaunchedEffect(attempt) {
        waited = false

        viewModel.refreshOverlayPackages()

        delay(WAIT_MILLIS)

        waited = true
    }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    val list = packages

    if (list == null) {
        OverlayStepWaiting(
            modifier = modifier,
            stepTitle = stepTitle,
            failed = waited,
            onSkip = onSkip,
            onRetry = { attempt += 1 },
        )

        return
    }

    OverlayPackagesDialog(
        modifier = modifier,
        overlayPackages = list,
        selectedPackages = userData.managedOverlayPackages,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onBack = onBack,
        onDismissRequest = onNext,
        onRefresh = viewModel::refreshOverlayPackages,
        onUpdateManagedOverlayPackages = viewModel::updateManagedOverlayPackages,
    )
}

/** Which settings a launch hides. */
@Composable
fun SettingsToHideStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    SettingsToHideDialog(
        modifier = modifier,
        states = userData.settingsToHide,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onBack = onBack,
        overlayBlockedPaths = overlayBlockedPaths(userData = userData),
        accessibilityManageable = userData.accessibilityManageable,
        manageShizukuEffective = userData.manageShizukuEffective,
        shizukuForkMode = userData.shizukuForkMode,
        hidingFramework = userData.hidingFramework,
        unhidingFramework = userData.unhidingFramework,
        restoreWirelessDebugging = userData.restoreWirelessDebugging,
        onDismissRequest = onNext,
        onUpdateSettingsToHide = viewModel::updateSettingsToHide,
        onUpdateRestoreWirelessDebugging = viewModel::updateRestoreWirelessDebugging,
    )
}

/**
 * What a revert puts back.
 *
 * ⚠ **Placed after [SettingsToHideStep] in the flow**: that page says what a launch takes away,
 * this one says what comes back, and the other order asks the user to configure a recovery from
 * a state they have not chosen yet.
 *
 * ⚠ **No `stepTitle`**, unlike the three steps above. The page's own title changes with the
 * unhiding framework — see `RevertDefaultsDialog` — so a heading handed in from the flow would be
 * wrong under one of the two.
 */
@Composable
fun RevertDefaultsStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    RevertDefaultsDialog(
        modifier = modifier,
        states = userData.revertDefaults,
        overlayBlockedPaths = overlayBlockedPaths(userData = userData),
        accessibilityManageable = userData.accessibilityManageable,
        manageShizukuEffective = userData.manageShizukuEffective,
        shizukuForkMode = userData.shizukuForkMode,
        unhidingFramework = userData.unhidingFramework,
        onSkip = onSkip,
        onBack = onBack,
        onDismissRequest = onNext,
        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
    )
}

/**
 * Auto unhide, whole.
 *
 * ⚠ **No longer part of the setup flow** — the author took it out in r4t. Kept rather than
 * deleted: it is the one place the whole page and all five of its satellites are wired together
 * for a flat step, and rebuilding that from scratch is the cost of removing it. `AutoUnhidePage`
 * itself is untouched and is what Settings opens.
 *
 * ⚠ **With all five of its satellites.** The minutes pickers, the ADB command, the how-it-works
 * dialog and the used-for refusal belong to this page rather than to the settings screen that
 * hosts it today, and a step without them is a page whose rows open nothing.
 */
@Suppress("unused")
@Composable
fun AutoUnhideStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val checks by viewModel.autoUnhideChecks.collectAsStateWithLifecycle()

    val systemChecks = rememberAutoHideSystemChecks()

    var showHowItWorks by rememberSaveable { mutableStateOf(false) }

    var showScreenLockMinutes by rememberSaveable { mutableStateOf(false) }

    var showIdleMinutes by rememberSaveable { mutableStateOf(false) }

    var showAdbCommand by rememberSaveable { mutableStateOf(false) }

    var showUsedForBlocked by rememberSaveable { mutableStateOf(false) }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    // The same assembly the settings screen makes, from the same three sources. Nothing here is
    // stored: both permissions are granted by shell and arrive without IMD being told.
    val requirements = remember(checks, systemChecks, userData) {
        AutoUnhideRequirements(
            dumpPermission = checks.dumpPermission,
            exitReasonsSupported = checks.exitReasonsSupported,
            usageAccess = checks.usageAccess,
            batteryUnrestricted = systemChecks.batteryUnrestricted,
            notificationsAllowed = systemChecks.notificationsAllowed,
            onAppLaunch = userData.autoUnhideOnAppLaunch,
            onTile = userData.autoUnhideOnTile,
            onSwipe = userData.autoUnhideOnSwipe,
            onScreenLock = userData.autoUnhideOnScreenLock,
            onIdle = userData.autoUnhideOnIdle,
        )
    }

    AutoUnhidePage(
        modifier = modifier,
        userData = userData,
        requirements = requirements,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onUpdateAutoUnhideEnabled = viewModel::updateAutoUnhideEnabled,
        onUpdateTriggers = viewModel::updateAutoUnhideTriggers,
        onUpdateUsedFor = { onAppLaunch, onTile ->
            // Refused rather than silently ignored, exactly as on the settings screen: the
            // checkbox will not move, and a control that will not move has to say why.
            if (!viewModel.updateAutoUnhideUsedFor(onAppLaunch, onTile)) {
                showUsedForBlocked = true
            }
        },
        onOpenScreenLockMinutes = { showScreenLockMinutes = true },
        onOpenIdleMinutes = { showIdleMinutes = true },
        onGrantDumpPermission = viewModel::grantAutoUnhideDumpPermission,
        onShowAdbCommand = { showAdbCommand = true },
        onGrantUsageAccess = viewModel::grantAutoUnhideUsageAccess,
        onOpenUsageSettings = { context.startActivity(usageAccessSettingsIntent()) },
        onOpenHowItWorks = { showHowItWorks = true },
        onRefreshSystemChecks = {
            systemChecks.refresh()

            viewModel.refreshAutoUnhideChecks()
        },
    )

    if (showHowItWorks) {
        AutoUnhideHowItWorksDialog(onDismissRequest = { showHowItWorks = false })
    }

    if (showScreenLockMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_lock),
            selected = userData.autoUnhideScreenLockMinutes,
            onSelect = viewModel::updateAutoUnhideScreenLockMinutes,
            onDismissRequest = { showScreenLockMinutes = false },
        )
    }

    if (showIdleMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_idle),
            selected = userData.autoUnhideIdleMinutes,
            onSelect = viewModel::updateAutoUnhideIdleMinutes,
            onDismissRequest = { showIdleMinutes = false },
        )
    }

    if (showAdbCommand) {
        AutoUnhideAdbCommandDialog(
            command = viewModel.autoUnhideAdbCommand(),
            onDismissRequest = { showAdbCommand = false },
        )
    }

    if (showUsedForBlocked) {
        AutoUnhideUsedForBlockedDialog(onDismissRequest = { showUsedForBlocked = false })
    }
}

/**
 * How long the Display over other apps step holds its spinner before offering a way out.
 *
 * The author's eight seconds. Long enough that a slow but working Shizuku is not accused of
 * failing, short enough that a dead one does not look like a hung app.
 */
private const val WAIT_MILLIS = 8_000L

/**
 * Which rows the settings manager draws.
 *
 * ⚠ **Placed after [RevertDefaultsStep] and before the reminders, at the author's instruction.**
 * Everything before it decides what the app *does*; this and the page after it decide what the
 * user *sees*, which is the right way round to be asked.
 */
@Composable
fun ManagerRowsStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    ManagerRowsDialog(
        modifier = modifier,
        states = userData.managerRows,
        shizukuForkMode = userData.shizukuForkMode,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onBack = onBack,
        onDismissRequest = onNext,
        onUpdateManagerRows = viewModel::updateManagerRows,
    )
}

/**
 * How the app looks: the four rows at the top of the User interface section.
 *
 * ⚠ **The last page before the reminders, and the only optional one that changes nothing about
 * the device.** It is here because the author asked for it here, and the position is right for a
 * second reason: it is the one step whose answers the user can see the effect of immediately,
 * which is a better note to finish the flow on than another list of services.
 *
 * ⚠ **[UserInterfaceLookRows] rather than four rows written out again.** See that composable.
 */
@Composable
fun CustomiseUiStep(
    modifier: Modifier = Modifier,
    /** Null on a step with nothing behind it; see previousBefore in SetupScreen. */
    onBack: (() -> Unit)? = null,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    SettingsPage(
        modifier = modifier,
        title = stepTitle,
        flat = true,
        onDismissRequest = onNext,
        actions = {
            TextButton(onClick = onSkip) {
                Text(text = stringResource(commonR.string.skip))
            }

            SetupNextButtons(onBack = onBack, onNext = onNext)
        },
    ) {
        // ⚠ **Every row writes as it is touched**, unlike the four steps before this one, which
        // hold a draft until Next. These are preferences with no invalid combination and an
        // instantly visible effect: a theme that only applied after Next would look broken while
        // the user was still on the page.
        UserInterfaceLookRows(
            userData = userData,
            onUpdateDynamicTheme = viewModel::updateDynamicTheme,
            onUpdateTheme = viewModel::updateTheme,
            onUpdateOledBackground = viewModel::updateOledBackground,
            onUpdateProgressiveBlur = viewModel::updateProgressiveBlur,
            onUpdateBlurSettings = viewModel::updateBlurSettings,
        )
    }
}
