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

import android.app.Activity
import android.content.Intent
import androidx.annotation.VisibleForTesting
import androidx.compose.foundation.Image
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.expandVertically
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkVertically
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.InlineTextContent
import androidx.compose.foundation.text.appendInlineContent
import androidx.compose.foundation.verticalScroll
import com.android.geto.designsystem.component.GetoSwitch
import com.android.geto.designsystem.component.LocalHeaderMetrics
import com.android.geto.designsystem.component.getoFloatingBarInset
import com.android.geto.designsystem.component.getoFloatingHeaderInset
import com.android.geto.designsystem.component.progressiveEdgeBlur
import com.android.geto.designsystem.component.supportsProgressiveBlur
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.graphics.painter.Painter
import androidx.compose.ui.graphics.vector.rememberVectorPainter
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.Placeholder
import androidx.compose.ui.text.PlaceholderVerticalAlign
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.Font
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withLink
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.em
import androidx.compose.ui.window.PopupProperties
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.android.geto.common.AppLocale
import com.android.geto.common.ProjectLinks
import com.android.geto.common.SettingsChangeLog
import com.android.geto.common.openObtainium
import com.android.geto.common.openProjectUri
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.LocalAdvancedSettingsRequest
import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.luminance
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.theme.GetoRed
import com.android.geto.designsystem.theme.supportsDynamicTheming
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.AutoHideRequirements
import com.android.geto.domain.model.AutoUnhideRequirements
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.autoHideBlockedByHide
import com.android.geto.domain.model.autoHideSwitchOn
import com.android.geto.domain.model.autoUnhideSwitchOn
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.accessibilityManageable
import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.domain.model.withoutShizukuWhenNoIntents
import com.android.geto.feature.settings.dialog.AccessibilityServicesDialog
import com.android.geto.feature.settings.dialog.AutoHideAccessibilityBlockedDialog
import com.android.geto.feature.settings.dialog.AutoHideAppsDialog
import com.android.geto.feature.settings.dialog.AutoHideHowItWorksDialog
import com.android.geto.feature.settings.dialog.AutoHidePendingRevertsDialog
import com.android.geto.feature.settings.dialog.AutoHidePage
import com.android.geto.feature.settings.dialog.AutoHideSetupNoticeDialog
import com.android.geto.feature.settings.dialog.AutoRevertNoticeDialog
import com.android.geto.feature.settings.dialog.AutoUnhideAdbCommandDialog
import com.android.geto.feature.settings.dialog.AutoUnhideBlockedDialog
import com.android.geto.feature.settings.dialog.AutoUnhideHowItWorksDialog
import com.android.geto.feature.settings.dialog.AutoUnhideMinutesDialog
import com.android.geto.feature.settings.dialog.AutoUnhidePage
import com.android.geto.feature.settings.dialog.AutoUnhideUsedForBlockedDialog
import com.android.geto.feature.settings.dialog.DiagnosticsDialog
import com.android.geto.feature.settings.dialog.IconStyleDialog
import com.android.geto.feature.settings.dialog.rememberAutoHideSystemChecks
import com.android.geto.feature.settings.dialog.LanguageDialog
import com.android.geto.feature.settings.dialog.AppDrawerShortcutsDialog
import com.android.geto.feature.settings.dialog.ManagerRowsDialog
import com.android.geto.feature.settings.dialog.FrameworkRevertsFailedDialog
import com.android.geto.feature.settings.dialog.HidingFrameworkDialog
import com.android.geto.feature.settings.dialog.UnhidingFrameworkDialog
import com.android.geto.feature.settings.dialog.PendingRevertsDialog
import com.android.geto.feature.settings.dialog.OverlayLoadingDialog
import com.android.geto.feature.settings.dialog.OverlayPackagesDialog
import com.android.geto.feature.settings.dialog.OverlayUnreadableDialog
import com.android.geto.feature.settings.dialog.RevertDefaultsDialog
import com.android.geto.feature.settings.dialog.SettingsChangeLogDialog
import com.android.geto.feature.settings.dialog.ManageShizukuBlockedDialog
import com.android.geto.feature.settings.dialog.SheveryNoticeDialog
import com.android.geto.feature.settings.dialog.ThedjchiSetupDialog
import com.android.geto.feature.settings.dialog.SettingsToHideDialog
import com.android.geto.feature.settings.dialog.SupportDialog
import com.android.geto.feature.settings.dialog.TaskerIntegrationPage
import com.android.geto.feature.settings.dialog.BlurSettingsDialog
import com.android.geto.feature.settings.dialog.ThemeDialog
import com.android.geto.feature.settings.dialog.usageAccessSettingsIntent
import com.android.geto.feature.settings.help.SetupHelpDialog
import com.android.geto.service.SettingsObserverService
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.common.R as commonR
import com.android.geto.designsystem.R as designR

/** How long the Shizuku text fields wait after the last keystroke before persisting. */
private val COMMIT_DEBOUNCE = 500.milliseconds

/**
 * How long the package-refresh spinner may run before it gives up waiting for the read.
 *
 * A backstop and nothing more. The wait normally ends the moment the read reports back, so
 * this only matters if one never does — generous enough that a slow device finishes well
 * inside it, short enough that a hung read does not leave a spinner forever.
 */
private const val REFRESH_CEILING = 10_000L

/**
 * The two shell prefixes, beside the code that colours them rather than in eleven copies of a
 * resource file. Neither is prose: one is a prompt, the other is a program writing its name.
 */
/**
 * The colour the shell block prints its output in.
 *
 * One fixed value in both themes, chosen by the author against rendered previews of both
 * panels. It is not a theme token and must not become one: what changes between light and dark
 * is the panel behind it, not the text.
 *
 * ⚠ On the light panel this measures 1.9:1, well under the 4.5:1 AA threshold. That is known,
 * was rendered at full size before it was chosen, and is the author's call about a decorative
 * easter egg in an About screen. Do not quietly darken it. For the record, darkening the *panel*
 * makes it worse before better - this colour sits almost exactly halfway up the luminance range,
 * and nothing recovers past 4.5:1 until the panel is darker than #444444.
 */
private val SHELL_OUTPUT_COLOUR = Color(0xFFE0A800)

/**
 * The prompt green, pinned rather than read from the scheme.
 *
 * ⚠ **This is a dynamic-colour fix, at the author's request.** The `$` and `su_imd:` prefixes
 * used to take `colorScheme.primary`, which under Material You is the wallpaper's colour — so
 * the one block in the app that is deliberately a terminal came out lilac or orange on half of
 * everyone's phones while the output beside it stayed the fixed amber. These are the app's own
 * light and dark greens, so the whole block now looks the same whatever the theme is doing.
 *
 * The same argument [SHELL_OUTPUT_COLOUR] already carries: the colour of terminal output is not
 * something a theme has an opinion about. Which of the two applies is decided by the same
 * luminance test the panel behind it uses, not by isSystemInDarkTheme() — the app has its own
 * light/dark/follow-system setting, and asking the system would give a light-themed app on a
 * dark-themed phone the wrong one.
 */
/**
 * The bullet before the contributor's name.
 *
 * ⚠ **Its own Text in a Row, and that is what produces the hanging indent the author asked
 * for.** The scope has to start where the *name* starts, not where the bullet does. Given its
 * own column, the second Text wraps within that column, so both of its lines begin at the same
 * x by construction — no measured indent, nothing to drift in a proportional face, and nothing
 * that needs re-tuning in a locale whose bullet renders wider.
 *
 * Padding the second line with spaces inside the string would only line up in a monospace
 * face, and this one is not.
 */
private const val CONTRIBUTOR_BULLET = "\u2022  "

/**
 * Every settings-row mark, at one size.
 *
 * ⚠ **30 dp, up from 24 — r28, the author's *"increase the new icons size"*.** The ceiling is
 * [SETTINGS_TRAILING_WIDTH]: a glyph wider than the box that centres it would push the column back
 * out of line with the switches. It cannot change a row's height either way, because the two lines
 * of text beside it already measure about 45 dp.
 */
private val SETTINGS_ICON_SIZE = 30.dp

/**
 * How wide the trailing slot is, so a mark and a switch share one centre line.
 *
 * 52 dp because that is Material's switch track width. The settings manager writes the same number
 * down for the same reason - see `SWITCH_TRACK_WIDTH` there, which keeps *its* row titles on a
 * centre line. Different file, different module, one fact about one component.
 */
private val SETTINGS_TRAILING_WIDTH = 52.dp

/** The Logics card's illustration. Big enough to read its parts, short enough for two lines. */
private val LOGICS_ICON_SIZE = 56.dp

/**
 * Where a surface stops being light and starts being dark.
 *
 * Halfway, which is what the shell panel below has always used. It is written down here because
 * two unrelated things now ask the question - which prompt colour the terminal block wears, and
 * whether the OLED row is drawn at all - and a second literal 0.5 would be a second definition.
 */
private const val DARK_SURFACE_LUMINANCE = 0.5f

/**
 * How many app-drawer entries the dialog offers.
 *
 * Two, and a constant rather than a literal because the subtitle and the dialog have to agree:
 * a third entry added to one and not the other reads as a lost setting.
 */
private const val DRAWER_SHORTCUT_COUNT = 2

private val SHELL_PROMPT_LIGHT = Color(0xFF4C662B)

private val SHELL_PROMPT_DARK = Color(0xFFB1D18A)

/**
 * The panel under the output in a dark scheme.
 *
 * ⚠ **`#2E2E2E`, up from the `#212121` this used to be — r27, the author's *"brighten it a bit"*.**
 * Grey rather than black and not the app's green, as it always was; the lift is thirteen points,
 * which is enough to read as a panel on the near-black page rather than as a hole in it.
 */
private val SHELL_PANEL_DARK = Color(0xFF2E2E2E)

/** And in a light one: the author's sepia. */
private val SHELL_PANEL_LIGHT = Color(0xFFF2F1E9)

private const val SHELL_COMMAND_PREFIX = "\$ "

private const val SHELL_OUTPUT_PREFIX = "su_imd: "

private const val AUTHOR_LINK_TAG = "author"
private const val AUTHOR_EMAIL = "utkarshrajput@hotmail.com"
private const val AUTHOR_GITHUB_URL = "https://github.com/soul-99"
private const val LICENCE_URL = "https://www.gnu.org/licenses/gpl-3.0"
private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku"

/**
 * ⚠ **The releases page, and only for the red recommendation line.**
 *
 * The author's rule after r4a: *"in the description line thedjchi link should be to it's github
 * release page not repo, i only want repo link for toggles."* The two links answer different
 * questions — the description is telling somebody to go and **download** the fork, while the
 * fork name beside a radio button is answering "which app is that?", and the repo is where that
 * is explained.
 */
private const val SHIZUKU_THEDJCHI_RELEASES_URL =
    "https://github.com/thedjchi/Shizuku/releases"
private const val SHIZUKU_SHEVERY_URL = "https://github.com/HmnDev-Tech/shevery"

@Composable
internal fun SettingsRoute(
    modifier: Modifier = Modifier,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val settingsUiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val isServiceRunning by viewModel.isServiceRunning.collectAsStateWithLifecycle()

    val accessibilityServices by viewModel.accessibilityServices.collectAsStateWithLifecycle()

    val overlayPackages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    val overlayPackagesLoading by viewModel.overlayPackagesLoading.collectAsStateWithLifecycle()

    val installedApps by viewModel.installedApps.collectAsStateWithLifecycle()

    val installedAppsRevision by viewModel.installedAppsRevision.collectAsStateWithLifecycle()

    val frameworkSave by viewModel.frameworkSave.collectAsStateWithLifecycle()

    val autoHideServiceState by viewModel.autoHideServiceState.collectAsStateWithLifecycle()

    val autoHideEnabling by viewModel.autoHideEnabling.collectAsStateWithLifecycle()

    val autoHideBlocked by viewModel.autoHideAccessibilityBlocked.collectAsStateWithLifecycle()

    val autoUnhideChecks by viewModel.autoUnhideChecks.collectAsStateWithLifecycle()

    val diagnosticLog by viewModel.diagnosticLog.collectAsStateWithLifecycle()

    val context = LocalContext.current

    LaunchedEffect(Unit) {
        viewModel.refreshAccessibilityServices()
    }

    val lifecycleOwner = LocalLifecycleOwner.current

    // ⚠ **Both are read on every resume, and auto unhide's were not read here at all.**
    //
    // Each row's switch shows the *live* answer rather than the stored one — see
    // `autoUnhideSwitchOn` — so a requirement that has never been read reads as missing,
    // and a feature the user switched on months ago comes back after an update or a force
    // stop looking as though it was never set up. Auto unhide had exactly that: its three
    // checks were asked for only when its own page opened, so the row was wrong until
    // somebody opened that page and came back out again.
    //
    // On resume rather than once, because none of these is IMD's to grant. The dump
    // permission arrives over adb, usage access from Android's own settings, the battery
    // exemption from a system prompt — every one of them is granted somewhere else, which
    // means the trip back into IMD is precisely when the answer has changed. Adding the
    // observer to a lifecycle already resumed dispatches ON_RESUME straight away, so this
    // also covers arriving on the tab for the first time.
    DisposableEffect(lifecycleOwner) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                viewModel.refreshAutoHideServiceState()

                viewModel.refreshAutoUnhideChecks()
            }
        }

        lifecycleOwner.lifecycle.addObserver(observer)

        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    SettingsScreen(
        modifier = modifier,
        settingsUiState = settingsUiState,
        isServiceRunning = isServiceRunning,
        accessibilityServices = accessibilityServices,
        overlayPackages = overlayPackages,
        installedApps = installedApps,
        autoHide = remember(
            viewModel,
            autoHideServiceState,
            autoHideEnabling,
            autoHideBlocked,
        ) {
            AutoHideHandle(
                serviceState = autoHideServiceState,
                enabling = autoHideEnabling,
                blocked = autoHideBlocked,
                onUpdateEnabled = viewModel::updateAutoHideEnabled,
                onEnableWithDetector = viewModel::enableAutoHideWithDetector,
                onSetService = viewModel::setAutoHideService,
                onRequestShizukuPermission = viewModel::requestShizukuPermission,
                onUpdatePackages = viewModel::updateAutoHidePackages,
                onUpdateNoKillOnLaunch = viewModel::updateAutoHideNoKillOnLaunch,
                onClearBlocked = viewModel::clearAutoHideAccessibilityBlocked,
                onRefresh = viewModel::refreshAutoHideServiceState,
            )
        },
        autoUnhide = remember(viewModel, autoUnhideChecks) {
            AutoUnhideHandle(
                checks = autoUnhideChecks,
                onUpdateEnabled = viewModel::updateAutoUnhideEnabled,
                onUpdateTriggers = viewModel::updateAutoUnhideTriggers,
                onUpdateScreenLockMinutes = viewModel::updateAutoUnhideScreenLockMinutes,
                onUpdateIdleMinutes = viewModel::updateAutoUnhideIdleMinutes,
                onGrantDumpPermission = viewModel::grantAutoUnhideDumpPermission,
                onGrantUsageAccess = viewModel::grantAutoUnhideUsageAccess,
                adbCommand = viewModel::autoUnhideAdbCommand,
                onRefresh = viewModel::refreshAutoUnhideChecks,
                onUpdateUsedFor = viewModel::updateAutoUnhideUsedFor,
            )
        },
        diagnostics = remember(viewModel, settingsUiState, diagnosticLog) {
            DiagnosticsHandle(
                enabled = (settingsUiState as? SettingsUiState.Success)
                    ?.userData?.diagnosticsEnabled == true,
                log = diagnosticLog,
                onOpen = viewModel::refreshDiagnosticLog,
                onSetEnabled = viewModel::setDiagnosticsEnabled,
                onClear = viewModel::clearDiagnosticLog,
                onExport = viewModel::exportDiagnosticLog,
            )
        },
        onUpdateIconStyle = viewModel::updateIconStyle,
        onUpdateTheme = viewModel::updateTheme,
        onUpdateDynamicTheme = viewModel::updateDynamicTheme,
        onUpdateProgressiveBlur = viewModel::updateProgressiveBlur,
        onUpdateBlurSettings = viewModel::updateBlurSettings,
        onUpdateOledBackground = viewModel::updateOledBackground,
        onUpdateDrawerShortcuts = viewModel::updateDrawerShortcuts,
        onUpdateManageShizuku = viewModel::updateManageShizuku,
        onEnsureTaskerAuthKey = viewModel::ensureTaskerAuthKey,
        onRefreshTaskerAuthKey = viewModel::refreshTaskerAuthKey,
        onUpdateTaskerIntegrationEnabled = viewModel::updateTaskerIntegrationEnabled,
        onUpdateAutoRevertOnReturn = viewModel::updateAutoRevertOnReturn,
        onUpdateShizukuForkMode = viewModel::updateShizukuForkMode,
        onUpdateShizukuAuthKey = viewModel::updateShizukuAuthKey,
        onUpdateShizukuPackageName = viewModel::updateShizukuPackageName,
        onUpdateShizukuStartAction = viewModel::updateShizukuStartAction,
        onUpdateManagedAccessibilityServices = viewModel::updateManagedAccessibilityServices,
        onUpdateManagedOverlayPackages = viewModel::updateManagedOverlayPackages,
        onSaveHidingFramework = viewModel::saveHidingFramework,
        onSaveUnhidingFramework = viewModel::saveUnhidingFramework,
        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
        onUpdateManagerRows = viewModel::updateManagerRows,
        onUpdateSettingsToHide = viewModel::updateSettingsToHide,
        onUpdateRestoreWirelessDebugging = viewModel::updateRestoreWirelessDebugging,
        onRefreshAccessibilityServices = viewModel::refreshAccessibilityServices,
        onRefreshOverlayPackages = viewModel::refreshOverlayPackages,
        overlayPackagesLoading = overlayPackagesLoading,
        onRefreshInstalledApps = viewModel::refreshInstalledApps,
        installedAppsRevision = installedAppsRevision,
        frameworkSaved = frameworkSave == FrameworkSave.Saved,
        onFrameworkSaveHandled = viewModel::clearFrameworkSave,
    )

    // Kept here rather than passed down with everything else: a modal that covers whatever
    // the settings list is showing does not belong in the stateless screen below.
    if (frameworkSave == FrameworkSave.Running) PendingRevertsDialog()

    // ⚠ **No re-launch, unlike the mechanism switch this replaces.** That existed because
    // several screens read the mechanism as they composed and a change underneath a running
    // one left parts of it describing the old mechanism. Every one of them now collects a
    // Flow off the same repository and recomposes on its own — the two launch view models,
    // the per-app screen, the apps and favourites lists, and this screen — so the restart
    // bought a blink and nothing else. Verified by reading each reader, not assumed.
    if (frameworkSave == FrameworkSave.Failed) {
        FrameworkRevertsFailedDialog(onDismissRequest = viewModel::clearFrameworkSave)
    }
}

@VisibleForTesting
@Composable
internal fun SettingsScreen(
    modifier: Modifier = Modifier,
    settingsUiState: SettingsUiState,
    isServiceRunning: Boolean,
    accessibilityServices: List<AccessibilityServiceData>,
    overlayPackages: List<OverlayPackageData>?,
    installedApps: List<InstalledAppData>,
    autoHide: AutoHideHandle,
    autoUnhide: AutoUnhideHandle,
    diagnostics: DiagnosticsHandle,
    onUpdateIconStyle: (IconStyle) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
    onUpdateBlurSettings: (radiusDp: Int, tintPercent: Int, fadeDp: Int) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateDrawerShortcuts: (manager: Boolean, hideUnhide: Boolean) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onEnsureTaskerAuthKey: () -> Unit,
    onRefreshTaskerAuthKey: () -> Unit,
    onUpdateTaskerIntegrationEnabled: (Boolean) -> Unit,
    onUpdateAutoRevertOnReturn: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
    onSaveHidingFramework: (HidingFramework) -> Unit,
    onSaveUnhidingFramework: (UnhidingFramework) -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateManagerRows: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateRestoreWirelessDebugging: (Boolean) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
    onRefreshOverlayPackages: () -> Unit,
    overlayPackagesLoading: Boolean,
    /** True forces a re-read even when a list is already held - see the redetect button. */
    onRefreshInstalledApps: (Boolean) -> Unit,
    installedAppsRevision: Int,
    /**
     * The last framework save finished and the preference was written.
     *
     * ⚠ Not "the save is over": a save that could not settle the outstanding hides reports
     * [FrameworkSave.Failed] and leaves the preference alone, and the chooser stays open over
     * it so the choice that did not take is still there.
     */
    frameworkSaved: Boolean,
    /** Clears [frameworkSaved], once the choosers above have acted on it. */
    onFrameworkSaveHandled: () -> Unit,
) {
    // The scroll modifier lives on the content column rather than here: a Box that scrolls
    // measures its child with an infinite height, so it would wrap the spinner and centre
    // it inside itself, i.e. at the top of the screen.
    Box(modifier = modifier.fillMaxSize()) {
        when (settingsUiState) {
            SettingsUiState.Loading -> {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            }

            is SettingsUiState.Success -> {
                Success(
                    userData = settingsUiState.userData,
                    isServiceRunning = isServiceRunning,
                    accessibilityServices = accessibilityServices,
                    overlayPackages = overlayPackages,
                    installedApps = installedApps,
                    autoHide = autoHide,
                    autoUnhide = autoUnhide,
                    diagnostics = diagnostics,
                    onUpdateDynamicTheme = onUpdateDynamicTheme,
                    onUpdateProgressiveBlur = onUpdateProgressiveBlur,
                    onUpdateBlurSettings = onUpdateBlurSettings,
                    onUpdateOledBackground = onUpdateOledBackground,
                    onUpdateDrawerShortcuts = onUpdateDrawerShortcuts,
                    onUpdateIconStyle = onUpdateIconStyle,
                    onUpdateTheme = onUpdateTheme,
                    onUpdateManageShizuku = onUpdateManageShizuku,
                    onEnsureTaskerAuthKey = onEnsureTaskerAuthKey,
                    onRefreshTaskerAuthKey = onRefreshTaskerAuthKey,
                    onUpdateTaskerIntegrationEnabled = onUpdateTaskerIntegrationEnabled,
                    onUpdateAutoRevertOnReturn = onUpdateAutoRevertOnReturn,
                    onUpdateShizukuForkMode = onUpdateShizukuForkMode,
                    onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                    onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                    onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                    onUpdateManagedAccessibilityServices = onUpdateManagedAccessibilityServices,
                    onUpdateManagedOverlayPackages = onUpdateManagedOverlayPackages,
                    onSaveHidingFramework = onSaveHidingFramework,
                    onSaveUnhidingFramework = onSaveUnhidingFramework,
                    onUpdateRevertDefaults = onUpdateRevertDefaults,
                    onUpdateManagerRows = onUpdateManagerRows,
                    onUpdateSettingsToHide = onUpdateSettingsToHide,
                    onUpdateRestoreWirelessDebugging = onUpdateRestoreWirelessDebugging,
                    onRefreshAccessibilityServices = onRefreshAccessibilityServices,
                    onRefreshOverlayPackages = onRefreshOverlayPackages,
                    overlayPackagesLoading = overlayPackagesLoading,
                    onRefreshInstalledApps = onRefreshInstalledApps,
                    installedAppsRevision = installedAppsRevision,
                    frameworkSaved = frameworkSaved,
                    onFrameworkSaveHandled = onFrameworkSaveHandled,
                )
            }
        }
    }
}

@Composable
private fun Success(
    modifier: Modifier = Modifier,
    userData: UserData,
    isServiceRunning: Boolean,
    accessibilityServices: List<AccessibilityServiceData>,
    overlayPackages: List<OverlayPackageData>?,
    installedApps: List<InstalledAppData>,
    autoHide: AutoHideHandle,
    autoUnhide: AutoUnhideHandle,
    diagnostics: DiagnosticsHandle,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
    onUpdateBlurSettings: (radiusDp: Int, tintPercent: Int, fadeDp: Int) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateDrawerShortcuts: (manager: Boolean, hideUnhide: Boolean) -> Unit,
    onUpdateIconStyle: (IconStyle) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onEnsureTaskerAuthKey: () -> Unit,
    onRefreshTaskerAuthKey: () -> Unit,
    onUpdateTaskerIntegrationEnabled: (Boolean) -> Unit,
    onUpdateAutoRevertOnReturn: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
    onSaveHidingFramework: (HidingFramework) -> Unit,
    onSaveUnhidingFramework: (UnhidingFramework) -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateManagerRows: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateRestoreWirelessDebugging: (Boolean) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
    onRefreshOverlayPackages: () -> Unit,
    overlayPackagesLoading: Boolean,
    onRefreshInstalledApps: (Boolean) -> Unit,
    installedAppsRevision: Int,
    /**
     * The last framework save finished and the preference was written.
     *
     * ⚠ Not "the save is over": a save that could not settle the outstanding hides reports
     * [FrameworkSave.Failed] and leaves the preference alone, and the chooser stays open over
     * it so the choice that did not take is still there.
     */
    frameworkSaved: Boolean,
    /** Clears [frameworkSaved], once the choosers above have acted on it. */
    onFrameworkSaveHandled: () -> Unit,
) {
    val context = LocalContext.current

    var showIconStyleDialog by rememberSaveable { mutableStateOf(false) }

    var showManagerRowsDialog by rememberSaveable { mutableStateOf(false) }

    var showDrawerShortcutsDialog by rememberSaveable { mutableStateOf(false) }

    var showLanguageDialog by rememberSaveable { mutableStateOf(false) }

    // Read from the platform rather than held in state: on Android 13 and up this can also
    // be changed from Android's own per-app language screen, and coming back to a stale
    // copy would show the wrong one until the app was killed.
    var languageTag by remember { mutableStateOf(AppLocale.stored(context)) }

    var showAccessibilityServicesDialog by rememberSaveable { mutableStateOf(false) }

    var showOverlayPackagesDialog by rememberSaveable { mutableStateOf(false) }

    // r4n: raised instead of the picker on a fork that cannot write overlay AppOps.
    var showOverlayForkBlocked by rememberSaveable { mutableStateOf(false) }

    var showHidingFrameworkDialog by rememberSaveable { mutableStateOf(false) }

    var showUnhidingFrameworkDialog by rememberSaveable { mutableStateOf(false) }

    var showRevertDefaultsDialog by rememberSaveable { mutableStateOf(false) }

    // ⚠ **Closed by the save landing, never by the press** - the author's "if all goes
    // sucessful after save button press, close the dialog". A save that cannot settle the
    // outstanding hides leaves the preference unwritten, so closing on the press would take
    // the chooser away having changed nothing.
    //
    // Both flags are cleared without asking which chooser was open: only one can be, and a
    // false on a flag that is already false is not a recomposition.
    LaunchedEffect(frameworkSaved) {
        if (!frameworkSaved) return@LaunchedEffect

        showHidingFrameworkDialog = false

        showUnhidingFrameworkDialog = false

        onFrameworkSaveHandled()
    }

    // The manager dialog's long press, arriving as a count that only goes up. Keyed on the
    // count rather than seeded once, so the second and every later press opens the dialog
    // too -- seeding only worked while this screen was being composed for the first time,
    // which is exactly once per launch of the app.
    val revertConfigurationRequest = LocalRevertConfigurationRequest.current

    // A high-water mark, not a plain "greater than zero". This screen leaves composition
    // whenever another tab or the per-app configuration page is opened, so a fresh
    // LaunchedEffect is built on the way back - and against a standing count that would
    // re-open the configuration dialog on every return, long after the press that asked for
    // it. Saved rather than remembered, so it survives that round trip as the count does.
    var handledRevertConfiguration by rememberSaveable { mutableIntStateOf(0) }

    LaunchedEffect(revertConfigurationRequest) {
        if (revertConfigurationRequest > handledRevertConfiguration) {
            handledRevertConfiguration = revertConfigurationRequest

            showRevertDefaultsDialog = true
        }
    }

    // The other request that lands on this tab: the re-launch after a change of
    // hiding-unhiding mechanism, which puts the user back at the section the row lives in
    // rather than at the top of a screen they now have to find their way down again.
    val advancedSettingsRequest = LocalAdvancedSettingsRequest.current

    var showSettingsToHideDialog by rememberSaveable { mutableStateOf(false) }

    var showAutoHidePage by rememberSaveable { mutableStateOf(false) }

    var showAutoHideApps by rememberSaveable { mutableStateOf(false) }

    var showAutoHideHowItWorks by rememberSaveable { mutableStateOf(false) }

    var showAutoUnhidePage by rememberSaveable { mutableStateOf(false) }

    var showAutoUnhideHowItWorks by rememberSaveable { mutableStateOf(false) }

    var showAutoUnhideScreenLockMinutes by rememberSaveable { mutableStateOf(false) }

    var showAutoUnhideIdleMinutes by rememberSaveable { mutableStateOf(false) }

    var showAutoUnhideAdbCommand by rememberSaveable { mutableStateOf(false) }

    // Raised when the switch is moved on while a requirement is still missing, rather than
    // letting it snap silently back to off and leave the user guessing which one.
    var showAutoUnhideBlocked by rememberSaveable { mutableStateOf(false) }

    // Raised when unticking would leave neither "used for" box ticked.
    var showAutoUnhideUsedForBlocked by rememberSaveable { mutableStateOf(false) }

    // Battery exemption and notification permission, re-read every time this screen comes back
    // to the front - both are switched on from a system screen the user has to leave IMD for.
    val autoHideSystemChecks = rememberAutoHideSystemChecks()

    // Assembled here because this is the one place all three sources are in scope: the user's
    // stored answers, the two live system reads, and the two the ViewModel asks for. Every one
    // of them is read fresh rather than stored - see AutoHideRequirements.
    val autoHideRequirements = AutoHideRequirements(
        shizukuPermission = autoHide.serviceState.shizukuPermission,
        // A Shizuku that is asleep cannot answer the permission question at all, and must not
        // read as having refused - that would switch IMD+ off on every device whose fork is
        // not currently up, for a permission IMD starts Shizuku to use anyway.
        shizukuUnreachable = !autoHide.serviceState.shizukuRunning,
        // ⚠ **manageShizukuEffective, not isShizukuConfigured.** The master switch is part of
        // the question now - r4n item 2 - and this is the expression every other gate reads.
        shizukuManageable = userData.manageShizukuEffective,
        // Thedjchi only: IMD+ has to be able to bring the service up on demand, and a fork
        // with no start intent cannot be.
        forkSupported = userData.shizukuForkMode.supportsIntents,
        accessibilityEnabled = autoHide.serviceState.accessibilityRunning,
        batteryUnrestricted = autoHideSystemChecks.batteryUnrestricted,
        notificationsAllowed = autoHideSystemChecks.notificationsAllowed,
        appsChosen = userData.autoHidePackages.isNotEmpty(),
        noKillOnLaunch = userData.autoHideNoKillOnLaunch,
    )

    // The same three sources as above, and the same rule: nothing here is stored. Both
    // permissions are granted by shell, so they arrive and leave without IMD being told.
    val autoUnhideRequirements = AutoUnhideRequirements(
        dumpPermission = autoUnhide.checks.dumpPermission,
        exitReasonsSupported = autoUnhide.checks.exitReasonsSupported,
        usageAccess = autoUnhide.checks.usageAccess,
        batteryUnrestricted = autoHideSystemChecks.batteryUnrestricted,
        notificationsAllowed = autoHideSystemChecks.notificationsAllowed,
        // r4n: the two conditions are part of the question now - see anyUsedFor.
        onAppLaunch = userData.autoUnhideOnAppLaunch,
        onTile = userData.autoUnhideOnTile,
        onSwipe = userData.autoUnhideOnSwipe,
        onScreenLock = userData.autoUnhideOnScreenLock,
        onIdle = userData.autoUnhideOnIdle,
    )

    var showMemoryHideNotice by rememberSaveable { mutableStateOf(false) }

    var showSettingsLog by rememberSaveable { mutableStateOf(false) }

    // Raised when either half of the IMD+ row is tapped while a revert is outstanding.
    var showAutoHideBlockedNotice by rememberSaveable { mutableStateOf(false) }

    var showAutoHideSetupNotice by rememberSaveable { mutableStateOf(false) }

    var showAutoRevertNotice by rememberSaveable { mutableStateOf(false) }

    var showTaskerIntegration by rememberSaveable { mutableStateOf(false) }

    // What the two configuration dialogs show and count. The overlay row is absent from
    // both until overlay management is switched on in Advanced, and the "x of y" summaries
    // have to agree with them - a summary reading "3 of 5" beside a dialog listing four
    // rows is the sort of mismatch that reads as a lost setting.
    // The Shizuku row is absent too on a fork with no start/stop intents, for the same
    // reason: Shevery's service follows the debugging transport, so the row is not drawn and
    // must not be counted either.
    // ⚠ **Every row the dialog draws is counted, and only the rows that will run are ticked.**
    // The author's rule for the summary. `withoutOverlayWhenUnmanaged` used to drop Display
    // over other apps out of both numbers, which was right while that row was hidden - it has
    // been drawn for everyone since r4, so the summary had been reading one row short.
    //
    // `effectiveSettingsToHide` is the map the launch paths actually read, so `x` is the
    // number of settings that will really be hidden rather than the number ticked. A row
    // greyed because it cannot work therefore leaves the count and stays in the total.
    val hideStates = userData.effectiveSettingsToHide

    // ⚠ **The stored ticks, not the effective map, and the asymmetry is deliberate.** Reverts
    // are not gated: a revert hands back anything IMD already took, whatever the row says. So
    // every drawn row here can still run - and `effectiveRevertDefaults` would be the wrong
    // thing to count anyway, since it forces the overlay entry true while a debt is
    // outstanding, which is a debt rather than a configuration.
    // ⚠ **The stored ticks, whole, since r4n.** This used to drop the Shizuku entry on a
    // fork with no intents, which did two things: it shortened the "x of y" line, and — because
    // this map is the dialog's draft and the draft is what Save writes — **a Save on Shevery
    // deleted the user's stored Shizuku answer.** That is the opposite of the memory-preserving
    // behaviour the author asked for. The row is drawn and greyed on every fork now, so it is
    // counted too: the number under the row matches the rows on screen, which is his answer.
    //
    // The engine is unaffected: `effectiveRevertDefaults` still applies
    // `withoutShizukuWhenNoIntents`, so no revert broadcasts a start it has no intent for.
    val revertStates = userData.revertDefaults

    // Read straight from the shared log rather than through the ViewModel: the writer is a
    // foreground service in another module with no repository of its own, and this is the
    // same arrangement SettingsObservationGate already uses for the running flag.
    val settingsLog by SettingsChangeLog.entries.collectAsStateWithLifecycle()

    // ⚠ **Saveable, not a plain remember — r4z, and this is the author's report.** Expand a
    // section, switch tab, come back: it was collapsed again. The tab host tears this screen
    // down the moment another tab is selected and composes it afresh on the way back, so a
    // plain `remember` cannot survive the trip. The bar navigates with `saveState` and
    // `restoreState` — see `navigateToSettings` and its two siblings — which is what keeps a
    // *saveable* alive across it, and is what every `rememberSaveable` dialog flag above
    // already relies on. A fresh launch still opens the screen the way it always did; only
    // the trip to another tab and back is remembered.
    //
    // ⚠ **An ordinal because a nullable enum is not a saveable type.** [SECTION_NONE] is all
    // closed, and reading it back through `getOrNull` means a stale index can only ever come
    // back as closed rather than as the wrong section.
    //
    // Opens on Default IMD settings rather than on nothing. The two configurations in there
    // are what decides whether launching an app does anything at all, so a screen that
    // opens as five closed headings hides the only part most people ever need. Opening
    // another section closes this one, as before — it is still an accordion.
    var expandedOrdinal by rememberSaveable {
        mutableIntStateOf(SettingsSection.AppFunctions.ordinal)
    }

    val expanded = SettingsSection.entries.getOrNull(expandedOrdinal)

    // Advanced instead when the app was re-launched to come back here, which is the one
    // thing that asks for a section by name.
    //
    // ⚠ **An effect now, and it has to be one.** r4y read the request into the initial value,
    // which worked only because that initial value was recomputed on every single visit. It
    // is not any more — that is the whole point of the change above — so a request arriving
    // at a screen whose saved state already exists would never be seen.
    //
    // The high-water mark is what stops it fighting the accordion, and it is the same mark
    // HomeScreen keeps for these same two requests: this expands Advanced once per re-launch
    // and then leaves the sections to whoever is pressing them.
    var handledAdvancedRequest by rememberSaveable { mutableIntStateOf(0) }

    LaunchedEffect(advancedSettingsRequest) {
        if (advancedSettingsRequest > handledAdvancedRequest) {
            handledAdvancedRequest = advancedSettingsRequest

            expandedOrdinal = SettingsSection.Advanced.ordinal
        }
    }

    val toggleSection = { section: SettingsSection ->
        expandedOrdinal = if (expandedOrdinal == section.ordinal) {
            SECTION_NONE
        } else {
            section.ordinal
        }
    }


    // ⚠ **A shorter bottom band than the two app tabs get** — the author's "also apply blur to
    // settings but keep it lowered on height". This tab is a column of rows rather than a
    // scrolling wall of artwork, and the full 150 dp swallows most of the last row instead of
    // fading it.
    //
    // Free to read here: `LocalHeaderMetrics` is static, so this line is not a subscription to
    // anything — the numbers inside it are read in the draw lambdas below.
    val headerMetrics = LocalHeaderMetrics.current

    // ⚠ **The Column below is not re-indented, and that is deliberate.** It is four hundred lines
    // of settings; moving all of them one level to the right would bury this round's real changes
    // in whitespace, and an earlier attempt at exactly that closed the wrapper in the wrong place.
    Box(modifier = Modifier.fillMaxSize()) {
    Column(
        modifier = modifier
            .fillMaxSize()
            // ⚠ **Before `verticalScroll`, which puts it outside the scrolling.** After it, the
            // bands would be part of the scrolled content and would travel up the page with it
            // instead of staying at the viewport's two edges.
            // ⚠ **The header alone up top — r15.** This tab has no search field, so the
            // bottom-most floating thing above the page is the title itself, and the fade starts
            // where it ends. Nothing along the bottom, on any device — r15b.
            // ⚠ **Lambdas, and that is the whole of r29's change to this file.** Read as values
            // here, the header's collapse invalidated `Success` on every frame of a scroll.
            .progressiveEdgeBlur(
                blur = userData.progressiveBlur,
                topSolid = { headerMetrics.height },
                strength = { headerMetrics.fraction },
            )
            .verticalScroll(rememberScrollState())
            // Room at both ends for the header and the bar to rest over nothing. Both are drawn
            // over this page rather than beside it, which is what gives the bands something to
            // blur. This tab has no search field, so its top inset is the header alone.
            .padding(top = getoFloatingHeaderInset(), bottom = getoFloatingBarInset()),
    ) {
        CollapsibleSection(
            title = stringResource(R.string.section_ui),
            expanded = expanded == SettingsSection.Ui,
            onToggle = { toggleSection(SettingsSection.Ui) },
        ) {
            // ⚠ **The four look rows are a composable now — r19b.** The setup flow's Customise
            // UI page draws exactly these, and the way this app builds a setup step is to draw
            // the thing Settings already draws rather than a copy of it. See
            // [UserInterfaceLookRows].
            UserInterfaceLookRows(
                userData = userData,
                onUpdateDynamicTheme = onUpdateDynamicTheme,
                onUpdateTheme = onUpdateTheme,
                onUpdateOledBackground = onUpdateOledBackground,
                onUpdateProgressiveBlur = onUpdateProgressiveBlur,
                onUpdateBlurSettings = onUpdateBlurSettings,
            )

            SettingsRowDivider()

            SettingsColumn(
                icon = painterResource(designR.drawable.ic_language),
                title = stringResource(R.string.language),
                subtitle = languageLabel(languageTag),
                onClick = { showLanguageDialog = true },
            )

            SettingsRowDivider()

            // The subtitle is the chosen option's own label, as Theme's is: the row says what
            // it is set to, so the pop-up is for changing it rather than for finding out.
            SettingsColumn(
                icon = painterResource(designR.drawable.ic_icon_style),
                title = stringResource(R.string.icon_style),
                subtitle = stringResource(
                    if (userData.iconStyle == IconStyle.SmartAdaptive) {
                        R.string.icon_style_smart
                    } else {
                        R.string.icon_style_system
                    },
                ),
                onClick = { showIconStyleDialog = true },
            )

            SettingsRowDivider()

            // Which rows the settings manager draws. In User interface rather than beside the
            // manager's own configuration in App functions, and deliberately: nothing here
            // changes what IMD does to the device, only what is on one card - which is what
            // every other row in this section is about.
            //
            // The subtitle counts, as Theme's and Icon style's name their current value.
            SettingsColumn(
                icon = painterResource(designR.drawable.ic_services_glyph),
                title = stringResource(R.string.manager_rows_entry),
                subtitle = stringResource(
                    R.string.manager_rows_summary,
                    userData.managerRows.count { it.value },
                    userData.managerRows.size,
                ),
                onClick = { showManagerRowsDialog = true },
            )

            SettingsRowDivider()

            // ⚠ **Directly under the manager's own row, at the author's instruction** — "add a
            // new setting under settings manager options". It belongs here for the same reason
            // that one does: nothing in this section changes what IMD does to the device, only
            // where the user finds it.
            //
            // The subtitle counts, as the row above it does.
            SettingsColumn(
                icon = rememberVectorPainter(GetoIcons.AppGrid),
                title = stringResource(R.string.drawer_shortcuts_entry),
                subtitle = stringResource(
                    R.string.drawer_shortcuts_summary,
                    listOf(userData.drawerShortcutManager, userData.drawerShortcutHideUnhide)
                        .count { it },
                    DRAWER_SHORTCUT_COUNT,
                ),
                onClick = { showDrawerShortcutsDialog = true },
            )
        }

        CollapsibleSection(
            title = stringResource(R.string.section_app_functions),
            expanded = expanded == SettingsSection.AppFunctions,
            onToggle = { toggleSection(SettingsSection.AppFunctions) },
        ) {
            // Hide first, unhide second — the order the two run in when an app is opened
            // and then left. Reading them the other way round makes the revert
            // configuration look like the primary one, which it no longer is.
            SettingsColumn(
                icon = painterResource(designR.drawable.ic_settings_hidden),
                // ⚠ **Driven by the *unhiding* framework, which is not the obvious half.**
                // Under the memory function this list is also the unhide list, because
                // memory restores exactly what was hidden from it; under Revert to default a
                // separate list drives the unhide and this one is hide-only. The author's
                // rule, and it holds up.
                title = if (userData.unhidingFramework == UnhidingFramework.Memory) {
                    stringResource(R.string.settings_to_hide_both_label)
                } else {
                    stringResource(R.string.settings_to_hide_defaults_label)
                },
                subtitle = stringResource(
                    R.string.settings_to_hide_summary,
                    hideStates.count { it.value },
                    hideStates.size,
                ),
                onClick = { showSettingsToHideDialog = true },
                // The mark is the *hiding* half, and independent of the label above: under
                // Per app configuration this row is mostly not what a launch reads, because
                // the per-app profile is. It says so rather than the row being hidden, since
                // the two things it still drives - the tile and the intents - are real and
                // are configured here.
                trailing = if (userData.hidingFramework == HidingFramework.PerApp) {
                    { MemoryHideNoticeButton(onClick = { showMemoryHideNotice = true }) }
                } else {
                    null
                },
            )

            SettingsRowDivider()

            SettingsColumn(
                icon = painterResource(designR.drawable.ic_revert_glyph),
                // Two lines under Revert to default, one under the memory function. Named
                // for what it does here as well as for the dialog it opens: in a list beside
                // the hide row, "Revert to default configuration" alone says nothing about
                // the relationship between the two, and under the memory function there is
                // no relationship left to describe.
                title = if (userData.unhidingFramework == UnhidingFramework.Memory) {
                    stringResource(R.string.revert_defaults)
                } else {
                    stringResource(R.string.revert_defaults_entry_both)
                },
                subtitle = stringResource(
                    R.string.revert_defaults_summary,
                    revertStates.count { it.value },
                    revertStates.size,
                ),
                onClick = { showRevertDefaultsDialog = true },
            )

            SettingsRowDivider()

            // Third, under the two it qualifies. Which services this app may touch is part
            // of what "hide" and "unhide" mean above -- both rows say as much in their own
            // small print -- so a section of its own put one third of one answer somewhere
            // else entirely.
            SettingsColumn(
                icon = painterResource(designR.drawable.ic_accessibility),
                // The row's own label, not the dialog's heading. Both said "… to hide" until
                // r4g; the author retitled the rows and left the dialogs alone.
                title = stringResource(R.string.accessibility_services_row),
                subtitle = accessibilityServicesSubtitle(
                    accessibilityServices = accessibilityServices,
                    managed = userData.managedAccessibilityServices,
                ),
                onClick = {
                    onRefreshAccessibilityServices()

                    showAccessibilityServicesDialog = true
                },
            )

            // The same row for overlay access, and it opens the same way. The difference is
            // that this list can only be read through a running Shizuku, so the refresh has
            // to land before anything can be shown - see the dialog below.
            //
            // ⚠ **Shown to everybody since v3**, where it used to appear only once overlay
            // management had been switched on in Advanced. That switch is gone: the DOOA
            // toggles are offered to everyone now and gated on whether they can work, and
            // this picker is one of the three things that decides whether they can.
            //
            // ⚠ **Gated on the fork, and deliberately not on `overlayManageable` — the two
            // are not the same gate.** `overlayManageable` includes "this picker is not
            // empty", so gating the picker on it would hide the only way to fill it: that is
            // the circle this comment used to warn about, and it still stands. The fork is a
            // fact about the device that cannot be changed from this screen, so gating on it
            // traps nobody. The author's instruction, v3 spec: the picker opens on Thedjchi
            // only.
            SettingsRowDivider()

            SettingsColumn(
                icon = painterResource(designR.drawable.ic_overlay),
                title = stringResource(R.string.overlay_packages_row),
                subtitle = overlayPackagesSubtitle(
                    overlayPackages = overlayPackages,
                    managed = userData.managedOverlayPackages,
                ),
                // Greyed, not disabled. The row keeps its own clickable so the press below
                // can explain itself; a disabled row would swallow it in silence.
                enabled = userData.shizukuForkMode.supportsIntents,
                onClick = {
                    if (userData.shizukuForkMode.supportsIntents) {
                        onRefreshOverlayPackages()

                        showOverlayPackagesDialog = true
                    } else {
                        showOverlayForkBlocked = true
                    }
                },
            )

            // Auto unhide sits here rather than beside IMD+, at the author's request: it is a
            // property of every hide these settings describe, not of IMD+ alone. The rule
            // above it is deliberately stronger than the ones between the rows - what follows
            // is a different kind of thing, and a divider of the same weight as the five above
            // would read as one more row rather than as a break.
            SettingsSectionDivider()
            SplitToggleSetting(
                title = stringResource(R.string.auto_unhide),
                subtitle = stringResource(R.string.auto_unhide_setup),
                checked = autoUnhideSwitchOn(
                    userData = userData,
                    requirements = autoUnhideRequirements,
                ),
                onClick = {
                    autoUnhide.onRefresh()

                    showAutoUnhidePage = true
                },
                onCheckedChange = { checked ->
                    // Saying which way it will not go is more use than a switch that moves
                    // and springs back - the requirements are on the page behind the label.
                    if (checked && !autoUnhideRequirements.satisfied) {
                        showAutoUnhideBlocked = true
                    } else {
                        autoUnhide.onUpdateEnabled(checked)
                    }
                },
            )
        }

        // A section of its own rather than a last row under Default IMD settings, because it
        // is the only thing in these settings that is a feature rather than a setting:
        // everything above says *what* is hidden, this says that IMD may decide *when* on its
        // own.
        //
        // The heading's bracket names what IMD+ *costs* — a background service — because
        // that is what a reader decides on before opening the section at all. The
        // EXPERIMENTAL warning that r2b3c put in the row's subtitle below is gone at the
        // author's instruction: the bracket now carries the whole of what this heading has to
        // say, and the subtitle says only what a tap does.
        CollapsibleSection(
            title = stringResource(R.string.section_imd_plus),
            expanded = expanded == SettingsSection.ImdPlus,
            onToggle = { toggleSection(SettingsSection.ImdPlus) },
        ) {
            // ⚠ **The section's own warning, above the first row rather than inside it.** The
            // author asked for it here and said where it must not be — "not auto hide toggle
            // description" — because a subtitle says what a tap does, and this is about the
            // whole feature. It was in that subtitle once, and was taken out on purpose.
            Text(
                modifier = Modifier.padding(
                    start = 16.dp,
                    end = 16.dp,
                    top = 12.dp,
                    bottom = 4.dp,
                ),
                text = stringResource(R.string.imd_plus_experimental),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.error,
            )

            // A split row: the label opens the page, the switch on the right turns IMD+ on
            // and off without going in. The divider between them is what stops a tap near the
            // switch being a coin toss between the two.
            SplitToggleSetting(
                title = stringResource(R.string.auto_hide),
                subtitle = stringResource(R.string.auto_hide_setup),
                checked = autoHideSwitchOn(
                    userData = userData,
                    requirements = autoHideRequirements,
                ),
                // Nothing here can be managed while a revert is outstanding: IMD+ is deaf for
                // exactly that period, so both opening the page and moving the switch would
                // only write an answer the next revert has to undo. Both halves say so
                // instead of doing nothing.
                enabled = !userData.autoHideBlockedByHide,
                onBlockedClick = { showAutoHideBlockedNotice = true },
                onClick = {
                    // The app list is what the picker inside the page needs, and enumerating
                    // every installed package takes a moment - so it is asked for on the way
                    // in rather than when the picker itself opens.
                    onRefreshInstalledApps(false)

                    autoHide.onRefresh()

                    showAutoHidePage = true
                },
                onCheckedChange = { checked ->
                    when {
                        // Off is always allowed: nothing has to be in place to stop.
                        !checked -> autoHide.onUpdateEnabled(false)

                        autoHideRequirements.satisfied -> autoHide.onUpdateEnabled(true)

                        // The one unmet requirement IMD can fix on its own, for somebody who
                        // has had IMD+ on before. A detector switched off by the services
                        // manager, an OEM cleaner or a restore leaves exactly this shape, and
                        // making the user find the page to press one more switch would be
                        // asking them to work out what IMD already knows.
                        autoHideRequirements.onlyAccessibilityMissing &&
                            userData.autoHideEverEnabled -> autoHide.onEnableWithDetector()

                        // Saying which way it will not go, rather than moving and springing
                        // back — the same reason the auto unhide row above does it.
                        else -> showAutoHideSetupNotice = true
                    }
                },
            )
        }

        CollapsibleSection(
            title = stringResource(R.string.shizuku),
            expanded = expanded == SettingsSection.Shizuku,
            onToggle = { toggleSection(SettingsSection.Shizuku) },
        ) {
            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateManageShizuku = onUpdateManageShizuku,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
                onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                onRefreshInstalledApps = onRefreshInstalledApps,
                installedAppsRevision = installedAppsRevision,
                showManageRow = true,
                commitDelay = COMMIT_DEBOUNCE,
            )
        }

        CollapsibleSection(
            title = stringResource(R.string.section_advanced),
            expanded = expanded == SettingsSection.Advanced,
            onToggle = { toggleSection(SettingsSection.Advanced) },
        ) {
            // ⚠ **The two frameworks come first, at the author's instruction, stated
            // twice in the v3 spec.** They outrank the overlay switch below not because they
            // add rows to this screen but because they decide what every other row on it
            // means: which list a launch reads, and which revert puts it back.
            SettingsColumn(
                icon = painterResource(designR.drawable.ic_hiding_framework),
                title = stringResource(R.string.hiding_framework),
                subtitle = stringResource(
                    R.string.framework_using,
                    userData.hidingFramework.getTitle(),
                ),
                onClick = { showHidingFrameworkDialog = true },
            )

            SettingsRowDivider()

            SettingsColumn(
                icon = painterResource(designR.drawable.ic_unhiding_framework),
                title = stringResource(R.string.unhiding_framework),
                subtitle = stringResource(
                    R.string.framework_using,
                    userData.unhidingFramework.getShortTitle(),
                ),
                onClick = { showUnhidingFrameworkDialog = true },
            )

            SettingsRowDivider()

            // The only setting in the app that changes what happens without anybody
            // pressing anything - which is why switching it on has to be read and agreed
            // to rather than just tapped.
            SwitchSetting(
                title = stringResource(R.string.auto_revert),
                subtitle = stringResource(R.string.auto_revert_subtitle),
                checked = userData.autoRevertOnReturn,
                onCheckedChange = { wanted ->
                    // Switching off needs no explanation and takes effect immediately.
                    // Switching on goes through the notice, and the switch only moves if the
                    // user says yes to it.
                    if (wanted) {
                        showAutoRevertNotice = true
                    } else {
                        onUpdateAutoRevertOnReturn(false)
                    }
                },
            )

            SettingsRowDivider()

            // Above the observer, because it is the one thing here another app might drive and
            // so the one most worth finding. Experimental in the title, not as a subtitle, so
            // the word travels with it wherever the row is read.
            //
            // A split row, not a plain one: the text opens the values screen, the switch on the
            // right turns the whole integration on or off, and a rule between them says they are
            // two controls rather than one. Off by default - nothing external works until it is
            // deliberately turned on.
            SplitToggleSetting(
                title = stringResource(R.string.tasker_integration),
                subtitle = stringResource(R.string.tasker_integration_subtitle),
                checked = userData.taskerIntegrationEnabled,
                onClick = { showTaskerIntegration = true },
                onCheckedChange = onUpdateTaskerIntegrationEnabled,
            )

            SettingsRowDivider()

            // A foreground service that watches every settings change. Useful for working
            // out what an app is actually reading, and of no interest to anyone who is not
            // doing that — which is what makes it advanced rather than an app function.
            SwitchSetting(
                title = stringResource(R.string.settings_observer_service),
                subtitle = if (isServiceRunning) {
                    stringResource(R.string.stop_service)
                } else {
                    stringResource(R.string.start_service)
                },
                checked = isServiceRunning,
                onCheckedChange = { wanted ->
                    val intent = Intent(context, SettingsObserverService::class.java)

                    if (wanted) {
                        ContextCompat.startForegroundService(context, intent)
                    } else {
                        context.stopService(intent)
                    }
                },
            )

            // Directly under the row they belong to, and on one line, because neither is a
            // setting: they read and empty the record the service above keeps. Text buttons
            // rather than another SettingsColumn for the same reason - a row that looks like
            // its neighbours would read as a third thing to switch on.
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 8.dp),
                horizontalArrangement = Arrangement.Start,
            ) {
                TextButton(onClick = { showSettingsLog = true }) {
                    Text(text = stringResource(R.string.settings_log_view))
                }

                TextButton(
                    enabled = settingsLog.isNotEmpty(),
                    onClick = SettingsChangeLog::clear,
                ) {
                    Text(text = stringResource(R.string.settings_log_clear))
                }
            }
        }

        // Not collapsible, unlike the five above. There is nothing to configure in it, and
        // the version line is what someone opens this screen to read when reporting a bug.
        SectionDivider(title = stringResource(R.string.about))

        Spacer(modifier = Modifier.height(60.dp))

        AboutSection(
            unhidingFramework = userData.unhidingFramework,
            diagnostics = diagnostics,
        )

        Spacer(modifier = Modifier.height(24.dp))

        FossFooter()

        Spacer(modifier = Modifier.height(24.dp))
    }
    }

    if (showLanguageDialog) {
        LanguageDialog(
            selectedTag = languageTag,
            onDismissRequest = { showLanguageDialog = false },
            onSelect = { tag ->
                showLanguageDialog = false

                if (tag != languageTag) {
                    languageTag = tag

                    // Below Android 13 nothing else is going to redraw the screen in the
                    // new language; from 13 up the platform recreates the activity itself
                    // as part of applying the locale, and doing it twice is a visible flash.
                    if (AppLocale.set(context, tag)) {
                        (context as? Activity)?.recreate()
                    }
                }
            },
        )
    }

    if (showIconStyleDialog) {
        IconStyleDialog(
            selected = userData.iconStyle,
            onSave = onUpdateIconStyle,
            onDismissRequest = { showIconStyleDialog = false },
        )
    }

    // ⚠ **No path line, exactly like the DOOA toggles on this fork.** `ConfigureFirstDialog`
    // takes an empty list here because there is nothing to go and set: Shevery has no
    // start-stop intent, so IMD cannot bring a shell up to write an overlay AppOp at all.
    if (showOverlayForkBlocked) {
        ConfigureFirstDialog(
            message = stringResource(R.string.dooa_thedjchi_only),
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { showOverlayForkBlocked = false },
        )
    }

    if (showOverlayPackagesDialog) {
        // Null is "could not read", not "nothing to show". The picker opens on a list and the
        // notice opens on a null, because a picker that opened empty on a device where IMD
        // simply cannot see would tell the user they have nothing to choose from.
        val packages = overlayPackages

        if (packages != null) {
            // Straight to the picker on a list already in hand, refresh or no refresh. Every
            // open kicks off a re-read, and waiting for it before showing anything meant the
            // second and every later open sat behind a spinner for a list that was already
            // there. The rows update themselves when the read lands.
            OverlayPackagesDialog(
                overlayPackages = packages,
                selectedPackages = userData.managedOverlayPackages,
                onDismissRequest = { showOverlayPackagesDialog = false },
                onUpdateManagedOverlayPackages = onUpdateManagedOverlayPackages,
                onRefresh = onRefreshOverlayPackages,
            )
        } else if (overlayPackagesLoading) {
            // The state that was missing: nothing read yet and a read in flight. It used to
            // fall through to the notice below, so a cold start reported "Shizuku is not
            // running" about a Shizuku that was simply still waking up.
            OverlayLoadingDialog()
        } else {
            OverlayUnreadableDialog(onDismissRequest = { showOverlayPackagesDialog = false })
        }
    }

    if (showAccessibilityServicesDialog) {
        AccessibilityServicesDialog(
            accessibilityServices = accessibilityServices,
            selectedServices = userData.managedAccessibilityServices,
            // Only while IMD+ is on. With it off, IMD's own detector is not running and is
            // not hidden by anything, so a row locked on would be claiming a rule that is not
            // in force.
            ownDetector = if (userData.autoHideEnabled) {
                autoHide.serviceState.ownDetector
            } else {
                ""
            },
            onDismissRequest = { showAccessibilityServicesDialog = false },
            onUpdateManagedAccessibilityServices = onUpdateManagedAccessibilityServices,
            onRefresh = onRefreshAccessibilityServices,
        )
    }

    if (showHidingFrameworkDialog) {
        HidingFrameworkDialog(
            selected = userData.hidingFramework,
            onDismissRequest = { showHidingFrameworkDialog = false },
            // Deliberately left open by the Save button itself. The spinner that may
            // follow is raised by the route above this screen, and closing this first would
            // show the settings list for a frame in between.
            //
            // ⚠ It is closed by the effect above instead, once the save reports Saved - which
            // is after the spinner has come and gone, so there is no frame to show the list in,
            // and a save that failed leaves it open.
            onSave = onSaveHidingFramework,
        )
    }

    if (showUnhidingFrameworkDialog) {
        UnhidingFrameworkDialog(
            selected = userData.unhidingFramework,
            onDismissRequest = { showUnhidingFrameworkDialog = false },
            onSave = onSaveUnhidingFramework,
        )
    }

    if (showAutoHideSetupNotice) {
        AutoHideSetupNoticeDialog(
            onDismissRequest = { showAutoHideSetupNotice = false },
        )
    }

    if (showAutoHideBlockedNotice) {
        AutoHidePendingRevertsDialog(
            onDismissRequest = { showAutoHideBlockedNotice = false },
        )
    }

    if (showAutoRevertNotice) {
        AutoRevertNoticeDialog(
            onConfirm = {
                onUpdateAutoRevertOnReturn(true)

                showAutoRevertNotice = false
            },
            onDismissRequest = { showAutoRevertNotice = false },
        )
    }

    if (showSettingsLog) {
        SettingsChangeLogDialog(
            entries = settingsLog,
            onClear = SettingsChangeLog::clear,
            onDismissRequest = { showSettingsLog = false },
        )
    }

    if (showTaskerIntegration) {
        TaskerIntegrationPage(
            authKey = userData.taskerAuthKey,
            onEnsureAuthKey = onEnsureTaskerAuthKey,
            onRefreshAuthKey = onRefreshTaskerAuthKey,
            onDismissRequest = { showTaskerIntegration = false },
        )
    }

    // Both dialogs are handed the stored map rather than the trimmed one above. They decide
    // for themselves which rows to draw; what they must not do is save back a map with the
    // overlay entry missing, which would clear a choice made while the feature was on.
    if (showManagerRowsDialog) {
        ManagerRowsDialog(
            states = userData.managerRows,
            shizukuForkMode = userData.shizukuForkMode,
            onDismissRequest = { showManagerRowsDialog = false },
            onUpdateManagerRows = onUpdateManagerRows,
        )
    }

    if (showDrawerShortcutsDialog) {
        AppDrawerShortcutsDialog(
            manager = userData.drawerShortcutManager,
            hideUnhide = userData.drawerShortcutHideUnhide,
            onDismissRequest = { showDrawerShortcutsDialog = false },
            onUpdateDrawerShortcuts = onUpdateDrawerShortcuts,
        )
    }

    if (showRevertDefaultsDialog) {
        RevertDefaultsDialog(
            states = userData.revertDefaults,
            overlayBlockedPaths = overlayBlockedPaths(userData = userData),
            accessibilityManageable = userData.accessibilityManageable,
            manageShizukuEffective = userData.manageShizukuEffective,
            shizukuForkMode = userData.shizukuForkMode,
            unhidingFramework = userData.unhidingFramework,
            onDismissRequest = { showRevertDefaultsDialog = false },
            onUpdateRevertDefaults = onUpdateRevertDefaults,
        )
    }

    if (showAutoHidePage) {
        AutoHidePage(
            userData = userData,
            requirements = autoHideRequirements,
            enabling = autoHide.enabling,
            onDismissRequest = { showAutoHidePage = false },
            onUpdateAutoHideEnabled = autoHide.onUpdateEnabled,
            onSetAutoHideService = autoHide.onSetService,
            onRequestShizukuPermission = autoHide.onRequestShizukuPermission,
            onUpdateNoKillOnLaunch = autoHide.onUpdateNoKillOnLaunch,
            onOpenApps = { showAutoHideApps = true },
            onOpenHowItWorks = { showAutoHideHowItWorks = true },
            // The Shizuku fields are a section of this same screen, so the way there is to
            // close this page onto it rather than to open a second copy of it on top.
            onOpenShizukuSettings = {
                showAutoHidePage = false

                toggleSection(SettingsSection.Shizuku)
            },
            onRefreshSystemChecks = autoHideSystemChecks::refresh,
        )
    }

    // Above the page rather than inside it, so both draw over it rather than replacing it -
    // dismissing either one puts the user back where they were.
    if (showAutoHideApps) {
        AutoHideAppsDialog(
            installedApps = installedApps,
            selectedPackages = userData.autoHidePackages,
            onDismissRequest = { showAutoHideApps = false },
            onUpdateAutoHidePackages = autoHide.onUpdatePackages,
        )
    }

    if (showAutoUnhidePage) {
        AutoUnhidePage(
            userData = userData,
            requirements = autoUnhideRequirements,
            onDismissRequest = { showAutoUnhidePage = false },
            onUpdateAutoUnhideEnabled = { checked ->
                if (checked && !autoUnhideRequirements.satisfied) {
                    showAutoUnhideBlocked = true
                } else {
                    autoUnhide.onUpdateEnabled(checked)
                }
            },
            onUpdateTriggers = autoUnhide.onUpdateTriggers,
            onUpdateUsedFor = { onAppLaunch, onTile ->
                // Refused rather than silently ignored: the checkbox will not move, and a
                // control that will not move has to say why.
                if (!autoUnhide.onUpdateUsedFor(onAppLaunch, onTile)) {
                    showAutoUnhideUsedForBlocked = true
                }
            },
            onOpenScreenLockMinutes = { showAutoUnhideScreenLockMinutes = true },
            onOpenIdleMinutes = { showAutoUnhideIdleMinutes = true },
            onGrantDumpPermission = autoUnhide.onGrantDumpPermission,
            onShowAdbCommand = { showAutoUnhideAdbCommand = true },
            onGrantUsageAccess = autoUnhide.onGrantUsageAccess,
            onOpenUsageSettings = { context.startActivity(usageAccessSettingsIntent()) },
            onOpenHowItWorks = { showAutoUnhideHowItWorks = true },
            onRefreshSystemChecks = {
                autoHideSystemChecks.refresh()

                autoUnhide.onRefresh()
            },
        )
    }

    if (showAutoUnhideHowItWorks) {
        AutoUnhideHowItWorksDialog(onDismissRequest = { showAutoUnhideHowItWorks = false })
    }

    if (showAutoUnhideScreenLockMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_lock),
            selected = userData.autoUnhideScreenLockMinutes,
            onSelect = autoUnhide.onUpdateScreenLockMinutes,
            onDismissRequest = { showAutoUnhideScreenLockMinutes = false },
        )
    }

    if (showAutoUnhideIdleMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_idle),
            selected = userData.autoUnhideIdleMinutes,
            onSelect = autoUnhide.onUpdateIdleMinutes,
            onDismissRequest = { showAutoUnhideIdleMinutes = false },
        )
    }

    if (showAutoUnhideAdbCommand) {
        AutoUnhideAdbCommandDialog(
            command = autoUnhide.adbCommand(),
            onDismissRequest = { showAutoUnhideAdbCommand = false },
        )
    }

    if (showAutoUnhideUsedForBlocked) {
        AutoUnhideUsedForBlockedDialog(
            onDismissRequest = { showAutoUnhideUsedForBlocked = false },
        )
    }

    if (showAutoUnhideBlocked) {
        AutoUnhideBlockedDialog(
            // ⚠ **Read at the moment it is drawn, not at the moment it was raised.** The page
            // behind this polls the requirements every second, so a permission granted while
            // the pop-up is up would otherwise leave it still naming the permission.
            permissionsMissing = !autoUnhideRequirements.permissionsSatisfied,
            onDismissRequest = { showAutoUnhideBlocked = false },
        )
    }

    if (showAutoHideHowItWorks) {
        AutoHideHowItWorksDialog(onDismissRequest = { showAutoHideHowItWorks = false })
    }

    // Raised by the ViewModel when every automatic route to switching the detector on has
    // failed, so it survives the page being closed underneath it.
    if (autoHide.blocked) {
        AutoHideAccessibilityBlockedDialog(onDismissRequest = autoHide.onClearBlocked)
    }

    if (showSettingsToHideDialog) {
        SettingsToHideDialog(
            states = userData.settingsToHide,
            overlayBlockedPaths = overlayBlockedPaths(userData = userData),
            accessibilityManageable = userData.accessibilityManageable,
            manageShizukuEffective = userData.manageShizukuEffective,
            shizukuForkMode = userData.shizukuForkMode,
            hidingFramework = userData.hidingFramework,
            unhidingFramework = userData.unhidingFramework,
            restoreWirelessDebugging = userData.restoreWirelessDebugging,
            onDismissRequest = { showSettingsToHideDialog = false },
            onUpdateSettingsToHide = onUpdateSettingsToHide,
            onUpdateRestoreWirelessDebugging = onUpdateRestoreWirelessDebugging,
        )
    }

    if (showMemoryHideNotice) {
        MemoryHideNoticeDialog(onDismissRequest = { showMemoryHideNotice = false })
    }
}

/**
 * Which section is open.
 *
 * One at a time rather than a flag per section: the screen is a short list of five headings
 * when everything is shut, and that is the state it is most useful in — opening one section
 * should not mean scrolling past another that was left open.
 */
/**
 * The stored value for "no section is open".
 *
 * The open section is saved as an ordinal rather than as the enum — a nullable enum is not a
 * saveable type — so the closed state needs an index no member can have. Any negative number
 * would do; -1 is the one `getOrNull` already answers `null` for.
 */
private const val SECTION_NONE = -1

private enum class SettingsSection {
    Ui,
    AppFunctions,
    ImdPlus,
    Shizuku,
    Advanced,
}

/**
 * The rule between two settings inside a section.
 *
 * Inset from the left so it starts under the text rather than under the card edge: a full-bleed
 * rule cuts the section into pieces, an inset one reads as a list of separate rows, which is
 * what these are.
 */
@Composable
private fun SettingsRowDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(
        modifier = modifier.padding(start = 16.dp),
        // A hairline at low alpha rather than outlineVariant at full strength. These rules sit
        // between every pair of rows in every section, so a dozen are on screen at once - at
        // the weight a single divider wants, a dozen of them stripe the page and pull the eye
        // away from the settings they are only meant to separate. Just findable when looked
        // for is the whole job.
        thickness = Dp.Hairline,
        color = MaterialTheme.colorScheme.outlineVariant.copy(alpha = ROW_DIVIDER_ALPHA),
    )
}

/**
 * The stronger rule that separates a *kind* of row from the one before it.
 *
 * A full pixel in `outline` rather than a hairline in `outlineVariant`, because it has a
 * different job: the rules above it separate five settings that are all the same sort of
 * thing, and this one says the next row is not. At the same weight it would read as a sixth
 * separator and the break would be invisible.
 */
@Composable
private fun SettingsSectionDivider(modifier: Modifier = Modifier) {
    HorizontalDivider(
        modifier = modifier.padding(start = 16.dp),
        thickness = SECTION_DIVIDER_THICKNESS,
        color = MaterialTheme.colorScheme.outline,
    )
}

/**
 * How visible the rules between rows are.
 *
 * Raised from 0.28 at the author's request. r4 had pulled it down to 0.28 after 0.5-ish read
 * as "too distracting" — this is a deliberate move back up, chosen off a rendered ladder, and
 * is not a regression of that decision.
 */
private const val ROW_DIVIDER_ALPHA = 0.60f

private val SECTION_DIVIDER_THICKNESS = 1.5.dp

/**
 * A section heading that opens and closes, wrapping its own contents.
 *
 * A Material 3 card rather than a rule and a row: with everything collapsed this screen is a
 * list of five headings, and containers are what make that read as five choices rather than
 * five pieces of one long page. The tonal surface also separates a closed section from an
 * open one without needing a second colour.
 */
@Composable
private fun CollapsibleSection(
    modifier: Modifier = Modifier,
    title: String,
    expanded: Boolean,
    onToggle: () -> Unit,
    content: @Composable () -> Unit,
) {
    // Two strengths of one tint - the theme's own green composited over the darkest surface -
    // and both of them belong to the section that is open.
    //
    // The muted one is the body: every setting inside the expanded section sits on it, which is
    // what marks out where the open section starts and ends. The stronger one is the heading
    // strip above them. A collapsed section's *heading* is still left untinted, for the reason
    // it always was: tinting all six headings meant the colour said "this is a heading", which
    // the type already said, and the one thing worth pointing at - which section is open - was
    // left to a difference of two steps in the same shade.
    //
    // ⚠ **Its body is not, since r4p, and that is a different question.** A collapsed card was
    // surfaceContainerLow, which in the light scheme is #F3F4E9 against a #F9FAEF page - six in
    // each channel, so the card was not visible as a card at all. A third, weaker step of the
    // same tint separates it from the page while staying below the open body, so the ordering
    // page < collapsed < open body < heading still says which section is open.
    //
    // An alpha of primary rather than a colour, because with Dynamic Theme on the scheme below
    // is not the one in use - the author's "theme colour tint (if dynamic theme is on)".
    // Half a turn, so the chevron ends up pointing the other way rather than snapping to a
    // different icon.
    val chevronTurn by animateFloatAsState(
        targetValue = if (expanded) 180f else 0f,
        label = "sectionChevron",
    )

    // ⚠ **Material 3's surface roles rather than three alphas of the theme's primary — r14, at
    // the author's instruction to put these on the M3 expressive guidelines in both schemes.**
    //
    // The old values were 8 %, 12 % and 34 % of `primary` composited over the lowest container:
    // numbers arrived at by asking him twice how green was too green, correct in the dark scheme
    // he was looking at and never checked in the light one. M3 answers this question already, and
    // answers it per-scheme: raising a surface is expressed as a step up the **tonal container
    // ladder**, one named role per step, generated for light and dark by the same scheme so the
    // relationship survives a theme change and a dynamic palette alike.
    //
    // The ordering the sections depend on — page below the collapsed card, below the open body,
    // below the heading strip — is now the ladder's own ordering rather than three numbers that
    // have to be kept in the right sequence by hand.
    // ⚠ **One rung higher than r14 put them — r17b.** The roles were right and the starting
    // point was too quiet: on a page this dark, `surfaceContainerLow` against `surface` is a
    // couple of points, and the author could barely see the cards. Same ladder, same ordering,
    // three steps further up — and the open heading takes a real tonal colour rather than a
    // fourth shade of grey, because that strip is the thing that says *this section is open*.
    val bodyTint = MaterialTheme.colorScheme.surfaceContainerHighest

    val headingTint = MaterialTheme.colorScheme.secondaryContainer

    val collapsedTint = MaterialTheme.colorScheme.surfaceContainerHigh

    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            // The card's own colour is what shows behind the rows, so the body tint is set
            // here rather than painted on a box inside it - that way it reaches the corners
            // and the padding as well as the rows themselves.
            // Animated for the same reason as the height: a card that changes colour in one
            // frame while its contents slide open reads as two separate things happening.
            containerColor = animateColorAsState(
                targetValue = if (expanded) {
                    bodyTint
                } else {
                    collapsedTint
                },
                label = "sectionBody",
            ).value,
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(
                    animateColorAsState(
                        targetValue = if (expanded) headingTint else Color.Transparent,
                        label = "sectionHeading",
                    ).value,
                )
                .clickable(onClick = onToggle)
                .padding(horizontal = 16.dp, vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                modifier = Modifier.weight(1f),
                text = title,
                style = MaterialTheme.typography.titleMedium,
                color = MaterialTheme.colorScheme.onSurface,
            )

            // One chevron turned rather than two swapped. Swapping the glyph cannot be
            // animated - the shape simply changes between frames - and it is the turn that
            // says "this opened", so the arrow that points down is the arrow that points up.
            Icon(
                modifier = Modifier.rotate(chevronTurn),
                imageVector = GetoIcons.ExpandMore,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        // Height and opacity together. Height alone reads as the rows being shoved out of the
        // way; the fade is what makes them look like they arrived rather than were pushed.
        AnimatedVisibility(
            visible = expanded,
            enter = expandVertically() + fadeIn(),
            exit = shrinkVertically() + fadeOut(),
        ) {
            Column {
                HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

                Column(modifier = Modifier.padding(bottom = 8.dp)) {
                    content()
                }
            }
        }
    }
}

/**
 * The whole Shizuku configuration, drawn in Settings and again during setup.
 *
 * ⚠ **Public because the setup page draws this one rather than a copy of it.** r4o's page was a
 * re-implementation and lost fifteen things this has - the links, both ⓘ buttons, the *supported,
 * but not recommended* caution, the app picker and its ⟳, the masked auth key, the fields that
 * stay hidden until a fork is picked, and the Shevery choice being held until its notice is
 * acknowledged. The author's *"keep everything from the original config page"* is only true for
 * as long as there is one of it.
 *
 * ⚠ **Nothing here writes anything itself.** Every value leaves through a callback, which is what
 * lets the setup page point them at a draft and leave the install untouched until its Manage
 * button is pressed. [commitDelay] is the one thing that has to differ - see below.
 *
 * @param showManageRow draws the **Manage Shizuku** switch with its recommendation. The setup
 *   page passes `false` and gets the recommendation alone, because its Manage button is what
 *   turns the switch on.
 * @param commitDelay how long the three text fields wait after the last keystroke before
 *   reporting. `COMMIT_DEBOUNCE` in Settings, where each write is a full proto rewrite;
 *   `Duration.ZERO` on the setup page, whose Manage button reads the draft and would otherwise
 *   meet a full form with *"Please fill all fields first"*.
 */
@OptIn(FlowPreview::class)
@Composable
fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateManageShizuku: (Boolean) -> Unit,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onRefreshInstalledApps: (Boolean) -> Unit,
    installedAppsRevision: Int,
    showManageRow: Boolean,
    commitDelay: Duration,
) {
    // Seeded once from the stored values and then owned locally. Reading them back out of
    // the preferences flow on every keystroke would fight the cursor.
    //
    // Blank is shown as the family's own action rather than as an empty box - for the
    // recommended family, moe.shizuku.privileged.api.START. It is written down as well as
    // shown, by the effect below; a field the app shows filled in has to be a field the app
    // has actually stored.
    var startAction by rememberSaveable {
        mutableStateOf(
            userData.shizukuStartAction.ifBlank {
                ShizukuForkDefaults.actionFor(
                    mode = userData.shizukuForkMode,
                    selectedLabel = null,
                )
            },
        )
    }

    var packageName by rememberSaveable { mutableStateOf(userData.shizukuPackageName) }

    var authKey by rememberSaveable { mutableStateOf(userData.shizukuAuthKey) }

    val forkMode = userData.shizukuForkMode

    // A refresh is a round trip to the package manager for a few hundred apps, which is long
    // enough to look like nothing happened. The button becomes a spinner for the duration and
    // the detected package is written back when it finishes.
    var refreshing by remember { mutableStateOf(false) }

    var refreshTick by remember { mutableIntStateOf(0) }

    // ⚠ **Which of the two started the refresh in flight.** The ⟳ button and picking a fork run
    // the same search, and they must not do the same thing with a blank result: an empty field
    // after a press the user made says "nothing found", and an empty field after a search they
    // did not ask for is the app deleting their answer.
    var refreshIsAuto by remember { mutableStateOf(false) }

    // rememberUpdatedState so the snapshotFlow below observes the *current* values: both are
    // plain parameters, and a flow built over one directly would capture a single value
    // forever.
    val latestApps by rememberUpdatedState(installedApps)

    val latestRevision by rememberUpdatedState(installedAppsRevision)

    // ⚠ Live rather than captured, for the same reason. The effect below waits on a package
    // manager round trip — long enough for the user to pick the other family — and a search that
    // lands afterwards must fill in for the family they are now looking at.
    val latestForkMode by rememberUpdatedState(forkMode)

    LaunchedEffect(refreshTick) {
        if (refreshTick == 0) return@LaunchedEffect

        refreshing = true

        // Noted before the request, so the wait below can only be ended by a read that
        // finished after it.
        val revisionBefore = latestRevision

        onRefreshInstalledApps(true)

        // Waits for the read itself to land, not for a fixed slice of time. It used to wait
        // 1.5 seconds for the list to *change*, and lost that race on the first press of a
        // cold screen every time: enumerating a few hundred apps and rasterising an icon each
        // takes longer than that, so the guess was made against the empty list still in hand
        // and the field came back blank - "no app found". Pressing again, with the list by
        // then loaded, worked, which is exactly the symptom that was reported.
        //
        // The ceiling is only a backstop against a read that never lands at all.
        withTimeoutOrNull(REFRESH_CEILING) {
            snapshotFlow { latestRevision }.first { it != revisionBefore }
        }

        val suggested = ShizukuForkDefaults.packageFor(
            mode = latestForkMode,
            apps = latestApps,
        )

        // ⚠ The automatic pass writes only what it found; the button writes whatever it got,
        // blank included, because that is how it reports "nothing found".
        if (suggested.isNotBlank() || !refreshIsAuto) {
            packageName = suggested
        }

        // ⚠ And only the automatic pass touches the action. The first attempt decided it without
        // a package to look at, which for the Other family is the difference between Shevery's
        // action and Shizuku's. The button has never written this and still does not.
        if (refreshIsAuto && suggested.isNotBlank()) {
            startAction = ShizukuForkDefaults.actionFor(
                mode = latestForkMode,
                selectedLabel = latestApps.labelOf(suggested),
            )
        }

        refreshIsAuto = false

        refreshing = false
    }

    // Opened from the caution beside the Shevery option, and again every time that option is
    // picked. Saved rather than remembered: it used to be dropped on rotation on the grounds
    // that losing an uncommitted choice is the safe direction, which is true and is not the
    // point - a dialog that vanishes when the phone turns reads as the app having crashed,
    // whether or not it took anything with it. pendingFork below is saved for the same reason
    // and has to be, or the dialog would come back asking about a choice that no longer exists.
    var showSheveryNotice by rememberSaveable { mutableStateOf(false) }

    // The Thedjchi checklist. Raised by picking that option and by its own ⓘ, and unlike the
    // Shevery one it gates nothing - see ThedjchiSetupDialog.
    var showThedjchiNotice by rememberSaveable { mutableStateOf(false) }

    // Why the master switch will not move yet.
    var showManageBlocked by rememberSaveable { mutableStateOf(false) }

    // The Shevery choice waits here until it is acknowledged. Picking the option used to
    // commit immediately and only then explain itself, so dismissing the dialog by tapping
    // outside left the radio on Shevery with the fields still describing the old fork - an
    // install that looked switched over and behaved as though it had not been.
    var pendingFork by rememberSaveable { mutableStateOf<ShizukuForkMode?>(null) }

    // Picking a family is the only moment the app knows enough to fill these in, and the two
    // families disagree about every one of them. Written into the visible fields rather than
    // applied behind the scenes, so a wrong guess is something the user can see and fix.
    val commitFork = { mode: ShizukuForkMode ->
        val suggested = ShizukuForkDefaults.packageFor(mode = mode, apps = installedApps)

        packageName = suggested

        startAction = ShizukuForkDefaults.actionFor(
            mode = mode,
            selectedLabel = installedApps.labelOf(suggested),
        )

        onUpdateShizukuForkMode(mode)

        // ⚠ **Nothing found, which during setup usually means nothing was searched.** Settings
        // has the installed list already; the setup page has not read it by the time the user
        // picks a family on page two, so the guess above ran against an empty list. This is the
        // author's *"start to autosearch"*: the same request the ⟳ button makes, through the
        // same effect and the same spinner, so a search is visibly happening rather than a box
        // being silently blank.
        if (suggested.isBlank()) {
            refreshIsAuto = true

            refreshTick += 1
        }
    }

    if (showThedjchiNotice) {
        ThedjchiSetupDialog(onDismissRequest = { showThedjchiNotice = false })
    }

    if (showManageBlocked) {
        ManageShizukuBlockedDialog(onDismissRequest = { showManageBlocked = false })
    }

    if (showSheveryNotice) {
        SheveryNoticeDialog(
            // Dismissed without acknowledging: the pending choice is dropped and the picker
            // stays exactly where it was.
            onDismissRequest = {
                showSheveryNotice = false

                pendingFork = null
            },
            onUnderstood = {
                pendingFork?.let { commitFork(it) }

                pendingFork = null

                showSheveryNotice = false
            },
        )
    }

    // Stores the derived start action the field is showing, when nothing was stored.
    //
    // The commits below deliberately skip their seed, so a value nobody edits is never
    // written - and a user who filled in every other field and left this one as it came
    // would have an install that looked completely configured and reported itself as
    // unconfigured, because isShizukuConfigured wants a start action. That is what made the
    // "you need to configure Shizuku first" appear over full fields, and why typing a
    // character into each box and deleting it again fixed it: the edit was the only thing
    // that ever committed anything.
    //
    // Once, on entry, and only into a blank. An action already stored is somebody's answer.
    LaunchedEffect(Unit) {
        if (userData.shizukuStartAction.isBlank() && startAction.isNotBlank()) {
            onUpdateShizukuStartAction(startAction)
        }
    }

    // Committed on a pause rather than per keystroke: each write is a full proto rewrite
    // plus an emission that recomposes this whole screen. drop(1) skips the seed value so
    // simply opening Settings does not write anything.
    LaunchedEffect(Unit) {
        snapshotFlow { startAction }.drop(1).debounce(commitDelay)
            .distinctUntilChanged()
            .collect { onUpdateShizukuStartAction(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { packageName }.drop(1).debounce(commitDelay)
            .distinctUntilChanged()
            .collect { onUpdateShizukuPackageName(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { authKey }.drop(1).debounce(commitDelay)
            .distinctUntilChanged()
            .collect { onUpdateShizukuAuthKey(it) }
    }

    // The picker needs the installed-app list to be able to preselect anything. Asked for
    // as soon as the section is composed, now that the fields are always on screen rather
    // than behind a panel that had to be opened first. Not forced: a list already read this
    // session is kept, and re-reading it on every recomposition of this section would be
    // hundreds of icons for nothing.
    LaunchedEffect(Unit) {
        onRefreshInstalledApps(false)
    }

    Column(modifier = modifier.fillMaxWidth()) {
        // ⚠ **Above everything, descriptions included** - the author's placement. It is the
        // switch the whole section is a precondition for, so it reads first and the red lines
        // below it explain which forks it can ever be pointed at.
        if (showManageRow) {
            ManageShizukuRow(
                checked = userData.manageShizukuEffective,
                configured = userData.isShizukuConfigured,
                onCheckedChange = onUpdateManageShizuku,
                onBlocked = { showManageBlocked = true },
            )
        } else {
            // ⚠ **The recommendation without the switch it belongs to** - the author's
            // *"show the RECOMMENDED ON... line in the new shizuku page at the top from the
            // original manage shizuku toggle"*. The same resource and the same full bold, so
            // the two pages cannot end up wording it differently.
            Text(
                modifier = Modifier.padding(horizontal = 16.dp),
                text = stringResource(R.string.manage_shizuku_recommended),
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
            )
        }

        Spacer(modifier = Modifier.height(4.dp))

        // No heading of its own any more: the section is called "Shizuku configuration",
        // so a "Configuration" title one line under it said the same word twice.
        //
        // Which forks this can drive at all. It belongs here rather than under the
        // restart switch, where it used to be: it is a precondition for everything in
        // this panel, not a footnote about one option.
        //
        // In the error colour because it is a dead end rather than a caveat: someone who
        // installed Shizuku from the Play Store has the one build none of this works with,
        // and no amount of filling in the fields below will change that. The second line
        // is the way out, which is why it carries the link.
        WarningLine(
            text = emphasised(
                text = stringResource(R.string.shizuku_rikka_warning),
                // ⚠ **Shevery is no longer in this sentence**, so its name leaves the
                // list with it: a phrase handed to `emphasised` that does not occur matches
                // nothing, silently, which is exactly the kind of bold that goes missing
                // without anything failing.
                names = listOf(
                    stringResource(R.string.shizuku_rikka_name_rikka),
                    stringResource(R.string.shizuku_rikka_name_unsupported),
                ),
            ),
            showIcon = false,
        )

        WarningLine(text = shizukuRikkaRecommendation(), showIcon = false)

        Spacer(modifier = Modifier.height(12.dp))

        ForkModeSelector(
            selected = forkMode,
            onShowSheveryNotice = { showSheveryNotice = true },
            onShowThedjchiNotice = { showThedjchiNotice = true },
            onSelect = { mode ->
                if (mode != forkMode) {
                    if (mode.isShevery) {
                        // Held, not applied. What Shevery costs is the whole reason this
                        // option carries a warning, so the choice is only made once that
                        // has actually been read - every time, not just the first.
                        pendingFork = mode

                        showSheveryNotice = true
                    } else {
                        commitFork(mode)

                        // Committed first, then explained. Unlike Shevery's, this pop-up is a
                        // setup checklist rather than the cost of a choice, so it does not
                        // hold the fork hostage - and that is what lets the ⓘ beside the name
                        // open the same dialog at any time without changing anything.
                        showThedjchiNotice = true
                    }
                }
            },
        )

        if (forkMode != ShizukuForkMode.Unset) {
            // Only where there is an intent to go and find. Shevery has none, so a line
            // telling the user to hunt for a start action would send them looking for
            // something that does not exist.
            if (forkMode.supportsIntents) {
                Text(
                    modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                    text = stringResource(R.string.shizuku_view_intents_hint),
                    style = MaterialTheme.typography.bodySmall,
                )
            }

            PackageNameField(
                value = packageName,
                installedApps = installedApps,
                refreshing = refreshing,
                onRedetect = { refreshTick += 1 },
                onValueChange = { packageName = it },
                onSelectApp = { app ->
                    packageName = app.packageName

                    // Only the "other forks" family derives its action from which app
                    // was picked; thedjchi's is the same string whatever the package
                    // has been renamed to.
                    if (forkMode == ShizukuForkMode.Other) {
                        startAction = ShizukuForkDefaults.actionFor(
                            mode = forkMode,
                            selectedLabel = app.label,
                        )
                    }
                },
            )

            // Said plainly rather than left as an empty field: nothing on the device matches
            // this family by label or by its stock package name, and no amount of tapping
            // refresh will change that until the fork is installed.
            if (packageName.isBlank()) {
                WarningLine(
                    text = AnnotatedString(stringResource(R.string.shizuku_app_not_found)),
                )
            }

            // Hidden for Shevery: there is no start intent to type in, and the field would
            // invite editing a value that is never broadcast. The selector still writes the
            // stored action when the family is chosen, which is what keeps Shizuku reading
            // as configured.
            if (forkMode.supportsIntents) {
                ShizukuField(
                    value = startAction,
                    label = stringResource(R.string.shizuku_start_action),
                    onValueChange = { startAction = it },
                )
            }

            if (forkMode.requiresAuthKey) {
                ShizukuField(
                    value = authKey,
                    label = stringResource(R.string.shizuku_auth_key),
                    secret = true,
                    onValueChange = { authKey = it },
                )
            }
        }

    }
}

/**
 * The two fork families, as a mandatory single choice.
 *
 * Radio rows rather than a segmented button: the labels are long enough that a segmented
 * control would truncate them, and truncating "Shevery / other forks of Shizuku" hides the
 * only word that tells someone which row is theirs.
 */
@Composable
private fun ForkModeSelector(
    modifier: Modifier = Modifier,
    selected: ShizukuForkMode,
    onSelect: (ShizukuForkMode) -> Unit,
    onShowSheveryNotice: () -> Unit,
    onShowThedjchiNotice: () -> Unit,
) {
    Column(modifier = modifier.selectableGroup()) {
        ForkModeRow(
            label = thedjchiForkLabel(),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
            inlineContent = forkInfoInline(onClick = onShowThedjchiNotice),
        )

        ForkModeRow(
            label = sheveryForkLabel(),
            selected = selected == ShizukuForkMode.Other,
            onSelect = { onSelect(ShizukuForkMode.Other) },
            trailing = { SheveryCaution(onClick = onShowSheveryNotice) },
        )
    }
}

@Composable
private fun ForkModeRow(
    modifier: Modifier = Modifier,
    label: AnnotatedString,
    selected: Boolean,
    onSelect: () -> Unit,
    /**
     * Filled into any placeholder [label] carries.
     *
     * Used by the Thedjchi row for its ⓘ, which has to sit after the last word of a label that
     * wraps - see [thedjchiForkLabel]. Empty for a label with no placeholder.
     */
    inlineContent: Map<String, InlineTextContent> = emptyMap(),
    trailing: (@Composable () -> Unit)? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onSelect)
            .padding(horizontal = 16.dp, vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // The row owns the click, so the button itself must not also be clickable or
        // TalkBack announces two separate controls for one choice.
        RadioButton(selected = selected, onClick = null)

        Spacer(modifier = Modifier.size(12.dp))

        // weight(1f, fill = false) so the label takes only the width it needs: the caution
        // beside it reads as a continuation of the name, not as something pushed to the far
        // edge of the row, while a long label can still shrink and wrap rather than overflow.
        Text(
            modifier = Modifier.weight(1f, fill = false),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            inlineContent = inlineContent,
        )

        // Its own tap target, outside the row's selectable: tapping the caution explains
        // the option rather than choosing it.
        trailing?.invoke()
    }
}

/**
 * A package name that can be typed or picked.
 *
 * Typed as well as picked because the list is only as good as what the device will admit
 * to having installed: a Shizuku build hiding itself may not show up at all, and its
 * package name still has to be enterable by hand.
 */
@Composable
private fun PackageNameField(
    modifier: Modifier = Modifier,
    value: String,
    installedApps: List<InstalledAppData>,
    onValueChange: (String) -> Unit,
    onSelectApp: (InstalledAppData) -> Unit,
    refreshing: Boolean,
    onRedetect: () -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }

    // Typing filters the list rather than just replacing it, so the field doubles as a
    // search box over a few hundred packages.
    val matches = remember(installedApps, value) {
        if (value.isBlank()) {
            installedApps
        } else {
            installedApps.filter {
                it.label.contains(value, ignoreCase = true) ||
                    it.packageName.contains(value, ignoreCase = true)
            }
        }
    }

    Box(modifier = modifier) {
        OutlinedTextField(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 6.dp),
            value = value,
            onValueChange = {
                onValueChange(it)

                // Typing is a search, so the results open on the first keystroke rather
                // than only when the chevron is tapped.
                expanded = true
            },
            label = { Text(text = stringResource(R.string.shizuku_package_name)) },
            singleLine = true,
            textStyle = MaterialTheme.typography.bodyMedium.copy(
                fontFamily = FontFamily.Monospace,
            ),
            trailingIcon = {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    // Re-reads the installed apps and fills the field in again from what is
                    // actually on the device. The one control that recovers a wrong or empty
                    // package without the user having to know what to type.
                    // The spinner replaces the icon in place rather than sitting beside it,
                    // so the row does not change width mid-refresh.
                    IconButton(onClick = onRedetect, enabled = !refreshing) {
                        if (refreshing) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(18.dp),
                                strokeWidth = 2.dp,
                            )
                        } else {
                            Icon(
                                imageVector = GetoIcons.Refresh,
                                contentDescription = stringResource(
                                    R.string.shizuku_refresh_apps,
                                ),
                            )
                        }
                    }

                    IconButton(onClick = { expanded = !expanded }) {
                        Icon(
                            imageVector = if (expanded) {
                                GetoIcons.ExpandLess
                            } else {
                                GetoIcons.ExpandMore
                            },
                            contentDescription = stringResource(R.string.shizuku_choose_app),
                        )
                    }
                }
            },
        )

        // focusable = false is the whole fix for a list that would not stay open. A
        // DropdownMenu's popup takes focus by default, which pulls it off the text field
        // underneath: the keyboard closes, and the next keystroke has nowhere to land. Left
        // unfocusable, the field keeps focus and the keyboard, and the list filters live
        // underneath it. The cost is that the menu no longer dismisses on a back press, so
        // the chevron and an outside tap are the ways out.
        DropdownMenu(
            modifier = Modifier.heightIn(max = 360.dp),
            expanded = expanded && matches.isNotEmpty(),
            onDismissRequest = { expanded = false },
            properties = PopupProperties(focusable = false),
        ) {
            matches.forEach { app ->
                DropdownMenuItem(
                    text = {
                        Column {
                            Text(
                                text = app.label,
                                style = MaterialTheme.typography.bodyMedium,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )

                            Text(
                                text = app.packageName,
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = FontFamily.Monospace,
                                color = MaterialTheme.colorScheme.onSurfaceVariant,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis,
                            )
                        }
                    },
                    leadingIcon = {
                        AsyncImage(
                            modifier = Modifier.size(36.dp),
                            model = app.icon,
                            contentDescription = null,
                        )
                    },
                    onClick = {
                        onSelectApp(app)

                        expanded = false
                    },
                )
            }
        }
    }
}

private fun List<InstalledAppData>.labelOf(packageName: String): String? = firstOrNull { it.packageName == packageName }?.label

/**
 * [secret] masks the value like a password and adds a reveal toggle. The auth key is the
 * one field here that is worth hiding: it is the token that lets anything start Shizuku,
 * and this screen gets opened in front of other people while explaining the app.
 */
@Composable
private fun ShizukuField(
    modifier: Modifier = Modifier,
    value: String,
    label: String,
    secret: Boolean = false,
    onValueChange: (String) -> Unit,
) {
    var revealed by remember { mutableStateOf(false) }

    OutlinedTextField(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 6.dp),
        value = value,
        onValueChange = onValueChange,
        label = { Text(text = label) },
        singleLine = true,
        textStyle = MaterialTheme.typography.bodyMedium.copy(fontFamily = FontFamily.Monospace),
        visualTransformation = if (secret && !revealed) {
            PasswordVisualTransformation()
        } else {
            VisualTransformation.None
        },
        trailingIcon = if (!secret) {
            null
        } else {
            {
                IconButton(onClick = { revealed = !revealed }) {
                    Icon(
                        imageVector = if (revealed) GetoIcons.Hidden else GetoIcons.Visible,
                        contentDescription = stringResource(
                            if (revealed) R.string.hide_value else R.string.show_value,
                        ),
                    )
                }
            }
        },
    )
}

@Composable
private fun AboutSection(
    modifier: Modifier = Modifier,
    /**
     * Only for the Help page this section opens: two of the paths on it name a row whose label
     * follows this setting — see `SetupHelpContent`.
     *
     * One enum rather than the whole of `userData`, which this section otherwise has no use for
     * and should not start looking like it depends on.
     */
    unhidingFramework: UnhidingFramework,
    diagnostics: DiagnosticsHandle,
) {
    var showAuthorDialog by rememberSaveable { mutableStateOf(false) }

    var showHelp by rememberSaveable { mutableStateOf(false) }

    var showSupport by rememberSaveable { mutableStateOf(false) }

    var showDiagnostics by rememberSaveable { mutableStateOf(false) }

    // Every composable read is hoisted out of the builder lambdas: resources and theme
    // colours are resolved once per recomposition rather than once per span.
    val linkStyles = linkStyles()

    val createdBy = stringResource(R.string.about_created_by)

    val authorName = stringResource(R.string.about_author_name)

    val forkOf = stringResource(R.string.about_fork_of)

    val getoApp = stringResource(R.string.about_geto_app)

    val licenceName = stringResource(R.string.about_licence_name)

    val logicsText = stringResource(R.string.about_logics)

    val author = remember(createdBy, authorName, linkStyles) {
        buildAnnotatedString {
            append(createdBy)
            append(" ")
            withLink(
                LinkAnnotation.Clickable(
                    tag = AUTHOR_LINK_TAG,
                    styles = linkStyles,
                    linkInteractionListener = { showAuthorDialog = true },
                ),
            ) {
                append(authorName)
            }
        }
    }

    val shellCommand = stringResource(R.string.about_shell_command)

    val shellLines = listOf(
        stringResource(R.string.about_shell_emoji),
        stringResource(R.string.about_shell_sanity),
        stringResource(R.string.about_shell_creating),
    )

    val shellDark = MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE

    // ⚠ **Both back — r27, and they move together or not at all.** r25 pinned the panel to the
    // author's sepia in both themes and collapsed this pair into one, which was right while there
    // was one panel. He has since asked for the dark panel back, brighter; leaving the prompt
    // pinned would have put the dark green `#4C662B` on `#2E2E2E`, which is the one combination
    // worse than either of the two this file has shipped.
    val shellPrompt = if (shellDark) SHELL_PROMPT_DARK else SHELL_PROMPT_LIGHT

    // One fixed colour, the same in both themes, and deliberately not routed through the
    // scheme: it is the colour of terminal output, which is not something a theme has an
    // opinion about. Only the panel behind it changes.
    val shellOutput = SHELL_OUTPUT_COLOUR

    // Which panel goes behind it, read from the scheme that is actually in force rather than
    // from isSystemInDarkTheme(). The app has a user-selectable theme - FOLLOW_SYSTEM, LIGHT,
    // DARK - so asking the *system* would give a user on LIGHT with a dark system a grey panel
    // inside a light app, and the reverse. This is also the only form that stays right under
    // dynamic colour, where the scheme is neither of the two the app declares.
    val shellPanel = if (shellDark) SHELL_PANEL_DARK else SHELL_PANEL_LIGHT

    // Built here rather than typed into four resources, because the only thing that varies
    // between the lines is which of two colours each span takes - and a resource per span
    // would put the colouring in eleven files instead of one place.
    val shell = remember(shellCommand, shellLines, shellPrompt, shellOutput) {
        buildAnnotatedString {
            withStyle(SpanStyle(color = shellPrompt)) { append(SHELL_COMMAND_PREFIX) }

            withStyle(SpanStyle(color = shellOutput)) { append(shellCommand) }

            shellLines.forEach { line ->
                append("\n")

                withStyle(SpanStyle(color = shellPrompt)) { append(SHELL_OUTPUT_PREFIX) }

                withStyle(SpanStyle(color = shellOutput)) { append(line) }
            }
        }
    }

    val contributionsLabel = stringResource(R.string.about_contributions)

    val contributorName = stringResource(R.string.about_contributor_name)

    val contributorScope = stringResource(R.string.about_contributor_scope)

    // Just the contributor now, sitting under the "Contributions:" heading rather than after
    // an inline label. Separators appended here, not typed into the strings: aapt strips
    // leading and trailing whitespace from an unquoted string resource.
    // Plain text now, all of it. These are credits rather than destinations: a reader who
    // wants the contributor's profile can find it from the repository, and three links in two
    // lines made the section look like a set of things to press.
    val contributorLine = remember(contributorName, contributorScope) {
        buildAnnotatedString {
            append(contributorName)
            // A line break rather than a space: the scope is a sentence now rather than a
            // two-word aside, and it no longer fits beside the name on a phone.
            append("\n")
            append(contributorScope)
        }
    }


    val forkAuthor = stringResource(R.string.about_fork_author)

    val forkBy = stringResource(R.string.about_fork_by)

    // "Fork of Geto by JackEblan (Blanc)" - two links in one line: Geto to its repository,
    // and the original author's name to his GitHub profile.
    // "Fork of Geto app by JackEblan", as one plain sentence. It was two links; naming the
    // upstream project and its author is an acknowledgement, and an acknowledgement that is
    // also a button invites a tap that leaves the app for no reason the reader asked for.
    val fork = remember(forkOf, getoApp, forkBy, forkAuthor) {
        buildAnnotatedString {
            append(forkOf)
            append(" ")
            append(getoApp)
            append(" ")
            append(forkBy)
            append(" ")
            append(forkAuthor)
        }
    }

    val licence = remember(licenceName, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = LICENCE_URL, styles = linkStyles)) {
                append(licenceName)
            }
        }
    }

    val context = LocalContext.current

    Column(modifier = modifier.padding(horizontal = 16.dp)) {
        VersionRow()

        Spacer(modifier = Modifier.height(4.dp))

        // Both routes out are offered rather than one: Obtainium is the answer for anyone
        // who wants this kept current automatically, and the releases page is the answer
        // for everyone else. An offline app has no third option.
        LinkRow(
            text = stringResource(R.string.about_check_releases),
            onClick = { context.openProjectUri(ProjectLinks.RELEASES) },
        )

        LinkRow(
            text = stringResource(R.string.about_add_to_obtainium),
            onClick = { context.openObtainium() },
        )

        // Plain text, not part of the link: it says what Obtainium is for, and underlining
        // it would make the explanation look like a second place to tap.
        Text(
            text = stringResource(R.string.about_obtainium_note),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )

        Spacer(modifier = Modifier.height(22.dp))

        // Help and Diagnostics share a row where there is room for two and stack where there
        // is not. The breakpoint is replicated from LocalConfiguration rather than asked of a
        // layout API, for the reason HomeScreen's rail test gives: the sandbox cannot compile
        // this, and a wrong API name is a build error on a machine that is not ours.
        if (LocalConfiguration.current.screenWidthDp >= WIDE_BUTTONS_MIN_WIDTH_DP) {
            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                HelpButton(modifier = Modifier.weight(1f), onClick = { showHelp = true })

                DiagnosticsButton(
                    modifier = Modifier.weight(1f),
                    onClick = {
                        diagnostics.onOpen()

                        showDiagnostics = true
                    },
                )
            }
        } else {
            HelpButton(modifier = Modifier.fillMaxWidth(), onClick = { showHelp = true })

            Spacer(modifier = Modifier.height(10.dp))

            DiagnosticsButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = {
                    diagnostics.onOpen()

                    showDiagnostics = true
                },
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        // Never paired with anything, at the author's request: it is the one button here that
        // asks for something rather than offering it, and half a row would make it look like
        // one of a set. A fixed red rather than a theme colour, with white text so it stays
        // legible in both light and dark; the heart-hands emoji carries the intent, so there
        // is no separate icon to double it.
        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = { showSupport = true },
            colors = ButtonDefaults.buttonColors(
                containerColor = GetoRed,
                contentColor = Color.White,
            ),
        ) {
            Text(
                text = stringResource(R.string.support_button),
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
            )
        }

        // A little bigger than the lines under it, so the name a reader is looking for when
        // they open About is the first thing they land on.
        // Everything above is about the app - what version, where to get it, where to get
        // help. Everything below is who wrote it. The gap is what separates the two, since
        // neither half has a heading.
        Spacer(modifier = Modifier.height(32.dp))

        Text(text = author, style = MaterialTheme.typography.bodyLarge)

        // A smaller gap than the one above, and deliberately: the logics box belongs *to* the
        // author line rather than following it, so it is set apart without being cut off.
        Spacer(modifier = Modifier.height(16.dp))

        // Straight under the author line, because it is the same person saying it - and the
        // heading inside is at the same size, so the two read as one block by the same hand
        // rather than as a line and its footnote.
        //
        // The outer container is what makes the heading and the transcript one thing. Before
        // it they were two siblings on the plain surface with a gap between them, which read
        // as a link that happened to have some monospace text after it.
        // fillMaxWidth on this and on the panel inside it, neither of which would otherwise:
        // a Box wraps its content, and the transcript's horizontal scroll reports the width it
        // was *given* rather than the width it wants - so without these the card would hug the
        // longest line and sit as a narrow slab on the left of a tablet's About page.
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .border(
                    width = 1.dp,
                    color = MaterialTheme.colorScheme.outlineVariant,
                    shape = RoundedCornerShape(12.dp),
                )
                .background(MaterialTheme.colorScheme.surfaceContainerLowest)
                // The whole box, at the author's request. After clip(), so the ripple stops
                // at the rounded corner rather than running square over it.
                .clickable { context.openProjectUri(ProjectLinks.LOGICS) }
                .padding(12.dp),
        ) {
            Column {
                // Icon and words inside one clickable, so they are one target rather than a
                // link with a decoration beside it. The icon takes the same colour and is
                // sized to the text it sits in front of.
                // No clickable of its own any more: the whole box below is the target, so a
                // tap anywhere in it - including on the shell block - opens the same page.
                // Top rather than CenterVertically, because the label is two lines now and a
                // centred icon would float between them instead of marking the first.
                Row(verticalAlignment = Alignment.Top) {
                    Icon(
                        modifier = Modifier
                            .padding(top = 3.dp)
                            .size(18.dp),
                        imageVector = GetoIcons.Link,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.primary,
                    )

                    Spacer(modifier = Modifier.width(6.dp))

                    // A Column so the second line starts where the first one does, under the
                    // "I" of IMD rather than under the chain icon.
                    //
                    // ⚠ **Weighted since r26**, because there is something to its right now. Two
                    // underlined lines would otherwise measure to their own width and leave the
                    // illustration wherever that happened to end.
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            text = logicsText,
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )

                        Text(
                            text = stringResource(R.string.about_logics_how),
                            style = MaterialTheme.typography.bodyLarge,
                            color = MaterialTheme.colorScheme.primary,
                            textDecoration = TextDecoration.Underline,
                        )
                    }

                    Spacer(modifier = Modifier.width(10.dp))

                    // ⚠ **`Image`, not `Icon`, and that is the author's *"no logics icon stay
                    // coloured"*.** `Icon` replaces every non-transparent pixel with a tint, which
                    // would flatten this to a grey silhouette — the same treatment the settings
                    // rows are getting, and precisely what he ruled out for this one.
                    //
                    // No contentDescription: the two underlined lines beside it already name the
                    // link, and a reader hearing the destination twice learns nothing the second
                    // time.
                    Image(
                        modifier = Modifier.size(LOGICS_ICON_SIZE),
                        painter = painterResource(R.drawable.ic_logics),
                        contentDescription = null,
                    )
                }

                Spacer(modifier = Modifier.height(10.dp))

                // The panel. Its own background and its own smaller radius, so it reads as a
                // window inside the box rather than as the box's own lining.
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(8.dp))
                        .background(shellPanel)
                        .padding(horizontal = 12.dp, vertical = 10.dp),
                ) {
                    // Monospace, and one size down from the lines above it. The block is 36
                    // characters at its widest; in a monospace face at bodyLarge that is wider
                    // than a phone's content column, and a line that wrapped would put the dot
                    // leader in the wrong place, which is the one thing this layout cannot
                    // survive. bodyMedium fits a 360 dp phone with room to spare - and now has
                    // the panel's own 12 dp either side to clear as well, which is why the
                    // scroll below matters more than it did.
                    //
                    // softWrap off with a horizontal scroll rather than trusting that: a
                    // long-press on a large display font, or a narrower device than any of us
                    // has, then scrolls the block instead of breaking its alignment. That is
                    // also how a terminal behaves.
                    Text(
                        modifier = Modifier.horizontalScroll(rememberScrollState()),
                        text = shell,
                        style = MaterialTheme.typography.bodyMedium,
                        fontFamily = SHELL_FONT,
                        softWrap = false,
                    )
                }
            }
        }

        // Wider than the gaps inside a block, because this one separates two blocks: what the
        // author has to say, and who else worked on it.
        Spacer(modifier = Modifier.height(28.dp))

        // "Contributions" is a heading now, with the contributor named on the line below it -
        // the semicolon is appended here so translations do not each have to remember it.
        AboutHeading(text = "$contributionsLabel:")

        Spacer(modifier = Modifier.height(2.dp))

        Row {
            Text(
                text = CONTRIBUTOR_BULLET,
                style = MaterialTheme.typography.bodyMedium,
            )

            Text(text = contributorLine, style = MaterialTheme.typography.bodyMedium)
        }

        Spacer(modifier = Modifier.height(14.dp))

        Text(text = fork, style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.height(14.dp))

        // The one heading with its content on the same line, because a licence name is a value
        // more than a paragraph: "License:" then the name, which carries the link.
        Row(verticalAlignment = Alignment.CenterVertically) {
            AboutHeading(text = stringResource(R.string.about_license_heading))

            Spacer(modifier = Modifier.width(6.dp))

            Text(text = licence, style = MaterialTheme.typography.bodyMedium)
        }
    }

    if (showAuthorDialog) {
        AuthorDialog(onDismissRequest = { showAuthorDialog = false })
    }

    if (showHelp) {
        SetupHelpDialog(
            unhidingFramework = unhidingFramework,
            onDismissRequest = { showHelp = false },
        )
    }

    if (showDiagnostics) {
        DiagnosticsDialog(
            enabled = diagnostics.enabled,
            log = diagnostics.log,
            onSetEnabled = diagnostics.onSetEnabled,
            onClear = diagnostics.onClear,
            onExport = diagnostics.onExport,
            onDismissRequest = { showDiagnostics = false },
        )
    }

    if (showSupport) {
        SupportDialog(onDismissRequest = { showSupport = false })
    }
}

/**
 * "Help (readme)", with the question mark between the word and the bracket.
 *
 * Three pieces rather than one string with an inline icon: an inline placeholder would have to
 * be typed into all eleven translations and would be silently wrong in any that lost it, where
 * two short strings either side of an icon cannot be got wrong at all.
 */
@Composable
private fun HelpButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Button(modifier = modifier, onClick = onClick) {
        Text(text = stringResource(R.string.help_button_label))

        Spacer(modifier = Modifier.width(6.dp))

        Icon(
            modifier = Modifier.size(18.dp),
            imageVector = GetoIcons.Help,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.width(6.dp))

        Text(text = stringResource(R.string.help_button_scope))
    }
}

/** Its neighbour, themed the same, because they are the same kind of offer. */
@Composable
private fun DiagnosticsButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Button(modifier = modifier, onClick = onClick) {
        Icon(
            modifier = Modifier.size(18.dp),
            imageVector = GetoIcons.Diagnostics,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.width(6.dp))

        Text(text = stringResource(R.string.diagnostics_title))
    }
}

/**
 * Where Help and Diagnostics stop stacking and share a row.
 *
 * The same 600dp the navigation rail uses, and replicated the same way and for the same
 * reason — see HomeScreen. Support is never part of this: it takes the full width on every
 * screen, at the author's request.
 */
private const val WIDE_BUTTONS_MIN_WIDTH_DP = 600

/**
 * DejaVu Sans Mono, bundled, and used by the About screen's shell block alone.
 *
 * `FontFamily.Monospace` is Roboto Mono on Android — a fine modern face that reads nothing
 * like a terminal. This is the console face instead, at the author's choice. The other
 * monospace text on this screen keeps the system font: those are values and keys being read,
 * not a transcript being enjoyed.
 *
 * ⚠ **Its advance width is what makes this swap safe.** The block's leader is 22 dots, counted
 * by the author's own eye off a rendered preview rather than by arithmetic, because the emoji
 * on the line above takes its width from the *system emoji* font and not from this one — see
 * handover_2 §4.7. Changing the monospace face changes the width of a dot while leaving the
 * emoji alone, so the count survives only if the two faces are near-identical in width. They
 * are: DejaVu is 0.6021 em against Roboto Mono's 0.6001, a fifth of one percent, which comes
 * to a twentieth of one character across the whole 28-cell line. **Any future change of this
 * font must redo that arithmetic, or have the dots re-counted.**
 *
 * Bitstream Vera Fonts Licence — GPL-compatible, and asks only that its copyright notice
 * travels with the font.
 */
private val SHELL_FONT = FontFamily(Font(R.font.dejavu_sans_mono))

/**
 * The installed version, linking to what changed in it.
 *
 * Read from the package manager rather than from `BuildConfig`: this module has its own
 * `BuildConfig` with its own version, which is not the one the user installed.
 */
@Composable
private fun VersionRow(modifier: Modifier = Modifier) {
    val context = LocalContext.current

    val versionName = remember(context) {
        runCatching {
            context.packageManager.getPackageInfo(context.packageName, 0).versionName
        }.getOrNull().orEmpty()
    }

    // Plain text, not a link. It used to open the changelog, which made the one line on
    // this screen that is purely a fact look like somewhere to go - and the two rows
    // directly below it are the places to go.
    Text(
        modifier = modifier,
        text = stringResource(R.string.about_version, versionName),
        style = MaterialTheme.typography.bodyMedium,
    )
}

/**
 * "Needs thedjchi / shevery / other forks ...", with each named fork linked to its own
 * release page.
 *
 * Two links rather than one because the choice between them is the whole point of the
 * section below, and a reader who has only heard of one of the two forks needs to be able
 * to go and look at the other.
 *
 * Built as one annotated string rather than assembled from separate Text composables so the
 * sentence wraps as a sentence; two of its words happen to be links, which is a property of
 * the words rather than of the layout.
 */
/**
 * A red note with an information icon, for the two lines opening the Shizuku section.
 *
 * The icon carries the same weight as the colour and is why both lines have one: red alone
 * is invisible to a red-green colour blind reader, and this is the part of the screen most
 * worth not missing. Matches the notes in the Settings to hide dialog, which is the other
 * place the app says "careful" in this shape.
 */
@Composable
private fun WarningLine(
    modifier: Modifier = Modifier,
    text: AnnotatedString,
    /**
     * Off where the line is one of a run of them. Two of these open the Shizuku panel, one
     * under the other, and an icon on each turned a two-line note into a column of markers.
     */
    showIcon: Boolean = true,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
    ) {
        if (showIcon) {
            Icon(
                modifier = Modifier.size(16.dp),
                imageVector = GetoIcons.Info,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.error,
            )

            Spacer(modifier = Modifier.size(8.dp))
        }

        Text(
            text = text,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.error,
        )
    }
}

@Composable
private fun shizukuRikkaRecommendation(): AnnotatedString {
    val linkStyles = linkStyles()

    val prefix = stringResource(R.string.shizuku_rikka_recommend_prefix)

    val link = stringResource(R.string.shizuku_rikka_recommend_link)

    return remember(prefix, link, linkStyles) {
        buildAnnotatedString {
            // The separator is appended here because aapt strips trailing whitespace from
            // an unquoted string resource, so a space typed at the end of the prefix never
            // reaches the screen.
            append(prefix)
            append(" ")
            withLink(
                LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_RELEASES_URL, styles = linkStyles),
            ) {
                append(link)
            }
        }
    }
}

/**
 * The second fork option, with its name carrying the link to its releases.
 *
 * The word is the link rather than a separate "releases" link after the label, because the
 * question this row answers is "which app is that?" and the name is what the reader is
 * looking at when they ask it.
 */
@Composable
private fun sheveryForkLabel(): AnnotatedString {
    val linkStyles = linkStyles()

    val shevery = stringResource(R.string.shizuku_fork_shevery)

    return remember(shevery, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = SHIZUKU_SHEVERY_URL, styles = linkStyles)) {
                append(shevery)
            }
        }
    }
}

/**
 * The linked fork name, what the family covers, and the ⓘ after the last word of it.
 *
 * ⚠ **The ⓘ is a placeholder in the string, not a sibling of it** - the author's *"move it to
 * where the toggle text ends i.e. after '...intents'"*. This label wraps to two or three lines,
 * and an icon drawn beside the `Text` is centred against the whole block; only inline content is
 * carried by the text layout to the end of the last line.
 */
@Composable
private fun thedjchiForkLabel(): AnnotatedString {
    val linkStyles = linkStyles()

    val thedjchi = stringResource(R.string.shizuku_fork_thedjchi)

    val suffix = stringResource(R.string.shizuku_fork_mode_thedjchi_suffix)

    return remember(thedjchi, suffix, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_URL, styles = linkStyles)) {
                append(thedjchi)
            }
            append(" ")
            append(suffix)
            // The space is part of the run rather than padding on the icon, so a line that
            // breaks here breaks between the words and the ⓘ rather than orphaning it.
            append(" ")
            appendInlineContent(FORK_INFO_ID, "\u24d8")
        }
    }
}

/**
 * The id the placeholder above and the composable below agree on.
 *
 * ⚠ A placeholder whose id is not in the `inlineContent` map is drawn as its alternate text -
 * here the ⓘ character itself, which would look almost right and do nothing when tapped. The
 * constant is what stops the two from being spelled differently.
 */
private const val FORK_INFO_ID = "forkInfo"

/**
 * The warning beside the Shevery option.
 *
 * In the error colour and carrying the info icon, because this is not a preference between
 * equals: Shevery works, but only indirectly and slowly, and the dialog behind this is where
 * that is spelled out.
 *
 * No brackets. They were tried and read as clutter - the icon and the colour already mark
 * this off from the option's name, and a parenthesis on either side of a line that is not a
 * sentence only added punctuation to look at.
 */
/**
 * How large a fork row's ⓘ is, as a multiple of the label's own type size.
 *
 * ⚠ **One number for both rows, at the author's instruction** — *"match that of thedjchi i button
 * size"*. The Thedjchi ⓘ is an inline placeholder inside its label and measures in `em`; the
 * Shevery one is a separate control beside its label and measures in `Dp`. Deriving both from
 * this and from `bodyMedium` is what makes them the same size at every font scale, rather than
 * the same size on one device.
 */
private const val FORK_INFO_EM = 1.2f

@Composable
private fun SheveryCaution(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    // The Thedjchi row's ⓘ in dp: the same multiple of the same type style, resolved through
    // the current density so the two stay identical when the user changes their font size.
    val infoSize = with(LocalDensity.current) {
        (MaterialTheme.typography.bodyMedium.fontSize * FORK_INFO_EM).toDp()
    }

    Row(
        // A small gap after the option's name - close enough to read as a continuation of it
        // rather than as a separate control at the end of the row.
        modifier = modifier
            .padding(start = 6.dp)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(infoSize),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.error,
        )

        // Underlined, because nothing else about a line of red text says "this opens
        // something" - and what it opens is the whole explanation of the option.
        Text(
            modifier = Modifier.padding(start = 3.dp),
            text = stringResource(R.string.shizuku_fork_shevery_caution),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.error,
            textDecoration = TextDecoration.Underline,
        )
    }
}

/**
 * Why the default hide list is only half in use under Per app configuration.
 *
 * The row still configures something real — the Hide settings tile and the IMD intents both
 * read it — but a launch does not, and a row that looks like it governs every launch while
 * governing none of them is the misreading this exists to prevent.
 *
 * ⚠ **A hiding question, and v3 is where that stopped being obvious.** Before the split this
 * appeared under the memory function, which was both halves at once. It now appears under
 * Per app configuration and says so, because the memory function no longer implies per-app
 * hiding and a notice naming the wrong framework is worse than none.
 *
 * Two blocks, not one: the closing sentence is the consequence and is the only part in the
 * error colour, so it does not read as more of the list above it.
 */
@Composable
private fun MemoryHideNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.per_app_hide_notice),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.per_app_hide_notice_red),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.error,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

@Composable
private fun AuthorDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    val context = LocalContext.current

    // Narrower than the platform dialog width. There are only two short rows in here, and at
    // full width each one was a word on the left with a hand's width of nothing after it.
    DialogContainer(
        modifier = modifier.widthIn(max = AUTHOR_DIALOG_WIDTH),
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            // ⚠ **Two lines, and the second is not a new string.** `support_signature_real_name`
            // already carries exactly "(Dr. Utkarsh Rajput)" for the signature at the foot of the
            // support dialog, and it is untranslatable there for the same reason it is here: it is
            // a name. One resource, two places, nothing to keep in step.
            Text(
                text = stringResource(R.string.about_author_name),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(bottom = 8.dp),
                text = stringResource(R.string.support_signature_real_name),
                style = MaterialTheme.typography.titleLarge,
            )

            LinkRow(
                text = stringResource(R.string.about_view_github),
                badge = { AboutBadgeGithub() },
                onClick = { context.openProjectUri(AUTHOR_GITHUB_URL) },
            )

            LinkRow(
                // The word rather than the address: it sits beside "View GitHub", which is
                // also what the row does rather than where it goes, and a raw address reads
                // as something to copy when it is really a button.
                text = stringResource(R.string.about_email),
                badge = { AboutBadgeIcon(icon = GetoIcons.Email) },
                onClick = { context.openProjectUri("mailto:$AUTHOR_EMAIL") },
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }
}

/** A small heading inside About - "Contributions;" and "License:" - one step below a title. */
@Composable
private fun AboutHeading(
    modifier: Modifier = Modifier,
    text: String,
) {
    Text(
        modifier = modifier,
        text = text,
        style = MaterialTheme.typography.titleSmall,
        fontWeight = FontWeight.Bold,
        color = MaterialTheme.colorScheme.primary,
    )
}

@Composable
private fun linkStyles(): TextLinkStyles {
    val colour = MaterialTheme.colorScheme.primary

    return remember(colour) {
        TextLinkStyles(
            style = SpanStyle(color = colour, textDecoration = TextDecoration.Underline),
        )
    }
}

@Composable
private fun FossFooter(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .alpha(0.38f)
            .padding(16.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center,
    ) {
        Image(
            modifier = Modifier.size(96.dp),
            painter = painterResource(R.drawable.ic_foss),
            contentDescription = null,
            colorFilter = ColorFilter.tint(MaterialTheme.colorScheme.onSurface),
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = stringResource(R.string.long_live_foss),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )

        // The expansion on its own line rather than inside the sentence, at the author's word.
        // Two Texts, not one string with a \n: only this half is the parenthetical, and a
        // translation is free to break it differently.
        Text(
            text = stringResource(R.string.long_live_foss_expansion),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )
    }
}

@Composable
private fun SectionDivider(
    modifier: Modifier = Modifier,
    title: String,
) {
    Column(modifier = modifier.fillMaxWidth()) {
        Spacer(modifier = Modifier.height(12.dp))

        HorizontalDivider()

        Text(
            modifier = Modifier.padding(start = 16.dp, top = 12.dp, bottom = 4.dp),
            text = title,
            style = MaterialTheme.typography.titleSmall,
            color = MaterialTheme.colorScheme.primary,
        )
    }
}

/**
 * The width the author dialog is capped at - narrower than the platform default, which is what
 * a dialog holding two short rows and a Close button wants.
 */
private val AUTHOR_DIALOG_WIDTH = 260.dp

/** The size a mark beside a row's label is drawn at: level with the body text next to it. */
private val ABOUT_BADGE_SIZE = 14.dp

/** GitHub's own mark, for the row that leads to GitHub. */
@Composable
private fun AboutBadgeGithub(tint: Color = MaterialTheme.colorScheme.primary) {
    Icon(
        modifier = Modifier.size(ABOUT_BADGE_SIZE),
        painter = painterResource(designR.drawable.ic_github),
        contentDescription = null,
        tint = tint,
    )
}

@Composable
private fun AboutBadgeIcon(
    icon: ImageVector,
    tint: Color = MaterialTheme.colorScheme.primary,
) {
    Icon(
        modifier = Modifier.size(ABOUT_BADGE_SIZE),
        imageVector = icon,
        contentDescription = null,
        tint = tint,
    )
}

/**
 * A line of text that opens something outside this screen.
 *
 * The tap target is the text itself and nothing else. It used to be the full width of the
 * column, with a link icon parked at the far right to explain why the empty space was
 * pressable - which put the icon a whole screen away from the words it belonged to. Coloured
 * text is already the universal sign of a link, so the icon is gone and the row now ends
 * where the words do.
 */
@Composable
private fun LinkRow(
    modifier: Modifier = Modifier,
    text: String,
    /** A small mark drawn immediately after the label, saying what the row leads to. */
    badge: (@Composable () -> Unit)? = null,
    onClick: () -> Unit,
) {
    Row(
        // No fillMaxWidth: the Row wraps its content, so the clickable area is the text and
        // its mark. The vertical padding is inside the clickable, which keeps the target a
        // comfortable height without widening it.
        modifier = modifier
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        badge?.let {
            Spacer(modifier = Modifier.width(5.dp))

            it()
        }
    }
}

@Composable
private fun SwitchSetting(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .clickable { onCheckedChange(!checked) }
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
        }

        GetoSwitch(checked = checked, onCheckedChange = onCheckedChange)
    }
}

/**
 * A row split into two controls: the title and subtitle open something on tap, and a switch on
 * the right toggles a state, with a vertical rule between them so the two do not read as one.
 *
 * The Android pattern for a row that both opens a detail screen and has its own on/off - the
 * old Wi-Fi and Bluetooth rows worked this way. The divider is the whole point: without it a
 * tap near the switch is a coin toss between opening the screen and flipping the switch.
 */
@Composable
private fun SplitToggleSetting(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    checked: Boolean,
    /**
     * False when neither half of the row may be used.
     *
     * Both halves still take the tap and hand it to [onBlockedClick], because a control that
     * is merely inert teaches nobody why. See the Switch below for how that is arranged.
     */
    enabled: Boolean = true,
    onBlockedClick: () -> Unit = {},
    onClick: () -> Unit,
    onCheckedChange: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(IntrinsicSize.Min),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .clickable(onClick = if (enabled) onClick else onBlockedClick)
                .padding(horizontal = 16.dp, vertical = 12.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
        }

        VerticalDivider(
            modifier = Modifier.padding(vertical = 10.dp),
            color = MaterialTheme.colorScheme.outlineVariant,
        )

        Box(
            modifier = Modifier
                .clickable(enabled = !enabled, onClick = onBlockedClick)
                .padding(horizontal = 16.dp),
        ) {
            // onCheckedChange = null when blocked, and that is the point rather than a
            // shortcut: a Switch given a null handler installs no input modifier at all, so
            // the tap falls through to the Box above and reaches onBlockedClick. A Switch
            // with enabled = false and a real handler would swallow the tap instead, and the
            // row would look broken rather than explain itself.
            GetoSwitch(
                checked = checked,
                enabled = enabled,
                onCheckedChange = if (enabled) onCheckedChange else null,
            )
        }
    }
}

@Composable
private fun DynamicThemeSetting(
    modifier: Modifier = Modifier,
    dynamicTheme: Boolean,
    onUpdateDynamicTheme: (Boolean) -> Unit,
) {
    if (supportsDynamicTheming()) {
        SwitchSetting(
            modifier = modifier,
            title = stringResource(R.string.dynamic_theme),
            subtitle = stringResource(R.string.available_on_android_12),
            checked = dynamicTheme,
            onCheckedChange = onUpdateDynamicTheme,
        )
    }
}

@Composable
private fun SettingsColumn(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    /**
     * Whether the row leads anywhere.
     *
     * ⚠ **Appearance only — the row stays clickable.** A greyed row that refuses has to be
     * able to say why, and a `clickable(enabled = false)` would eat the press. Callers that
     * pass false are expected to branch in [onClick] and raise an explanation.
     */
    enabled: Boolean = true,
    /**
     * The row's mark, drawn where a switch would be.
     *
     * ⚠ **At the far end, not the near one — r27, and it is the author's whole point:** *"I want
     * all the icon we generated to show in the same place switches are shown"*. The settings list
     * mixes rows that toggle with rows that open something, and putting these on the leading edge
     * would have given it two ragged columns instead of one tidy one.
     *
     * A `Painter` rather than a drawable id because one of the eleven is an `ImageVector` — see
     * `GetoIcons.AppGrid`.
     */
    icon: Painter? = null,
    onClick: () -> Unit,
    /**
     * A control at the far end of the row, with its own tap target - so it can say
     * something about the row without a press on it opening the row's dialog.
     */
    trailing: (@Composable () -> Unit)? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        val contentColour = if (enabled) {
            MaterialTheme.colorScheme.onSurface
        } else {
            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        trailing?.let {
            Spacer(modifier = Modifier.width(12.dp))

            it()
        }

        // ⚠ **After `trailing`, so the icon is always the last thing on the row.** One row — the
        // hide list under the memory function — carries both, and a mark that sometimes sat
        // outside the notice and sometimes inside it would break the very column this exists to
        // make.
        icon?.let {
            Spacer(modifier = Modifier.width(12.dp))

            // ⚠ **A switch-width box, not a nudge — r28.** Both the icon and a switch are flush to
            // the row's trailing padding, which is exactly why they did not line up: a switch is
            // 52 dp wide so its centre lands 42 dp from the edge, and a 24 dp icon's landed at 28.
            // The 14 dp between them was never about the drawings.
            //
            // Padding the difference away would have fixed it at one pair of sizes and broken it
            // again the moment either changed - which is the same breath the author asked in,
            // since the icons got bigger too. Centred inside a box the width of a switch, the two
            // centre lines coincide by construction at any glyph size.
            Box(
                modifier = Modifier.width(SETTINGS_TRAILING_WIDTH),
                contentAlignment = Alignment.Center,
            ) {
                Icon(
                    modifier = Modifier.size(SETTINGS_ICON_SIZE),
                    painter = it,
                    contentDescription = null,
                    // The off-switch rim, at the author's word. Dimmed with the row, because a row
                    // that greys its words and keeps a full-strength mark reads as half disabled.
                    tint = if (enabled) {
                        MaterialTheme.colorScheme.outline
                    } else {
                        MaterialTheme.colorScheme.outline.copy(alpha = 0.38f)
                    },
                )
            }
        }
    }
}

/**
 * The red mark beside "Settings to hide" while the memory function is chosen.
 *
 * Its own clickable rather than part of the row: pressing it explains why the row is only
 * half in use, and pressing the row still opens the configuration. One target that did both
 * would make the explanation reachable only by accident.
 */
@Composable
private fun MemoryHideNoticeButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    IconButton(modifier = modifier, onClick = onClick) {
        Icon(
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.error,
        )
    }
}

@Composable
private fun accessibilityServicesSubtitle(
    accessibilityServices: List<AccessibilityServiceData>,
    managed: List<String>,
): String {
    val enabledCount = accessibilityServices.count { it.enabled }

    return if (managed.isEmpty()) {
        stringResource(R.string.accessibility_services_none_selected, enabledCount)
    } else {
        stringResource(R.string.accessibility_services_selected, managed.size, enabledCount)
    }
}

/**
 * The same subtitle for overlay access, counting what is currently allowed.
 *
 * A null list has not been read yet - the row is tapped to read it - so the count falls back
 * to what IMD already knows it selected rather than showing a zero it has not verified.
 */
@Composable
private fun overlayPackagesSubtitle(
    overlayPackages: List<OverlayPackageData>?,
    managed: List<String>,
): String {
    val allowedCount = overlayPackages?.count { it.allowed } ?: managed.size

    return if (managed.isEmpty()) {
        stringResource(R.string.overlay_packages_none_selected, allowedCount)
    } else {
        stringResource(R.string.overlay_packages_selected, managed.size, allowedCount)
    }
}

@Composable
internal fun HidingFramework.getTitle() = when (this) {
    HidingFramework.ImdDefaults -> stringResource(R.string.hiding_framework_defaults)
    HidingFramework.PerApp -> stringResource(R.string.hiding_framework_per_app)
}

/**
 * The short form, for the "using X" subtitle.
 *
 * Trimmed of the bracketed half the picker carries — "Memory function", not "Memory function
 * (Revert to what was actually hidden)" — at the author's instruction, and confirmed
 * deliberate. A settings row's second line is one line; the parenthesis is for the dialog,
 * where there is room to explain.
 */
@Composable
internal fun UnhidingFramework.getShortTitle() = when (this) {
    UnhidingFramework.Memory -> stringResource(R.string.notification_function_memory)
    UnhidingFramework.RevertToDefault -> stringResource(R.string.unhiding_framework_revert)
}

@Composable
internal fun Theme.getTitle() = when (this) {
    Theme.FOLLOW_SYSTEM -> stringResource(R.string.follow_system)
    Theme.LIGHT -> stringResource(R.string.light)
    Theme.DARK -> stringResource(R.string.dark)
}

/**
 * What the settings row shows underneath "Language".
 *
 * The name of the chosen language written in that language, matching the picker. A tag with
 * no entry falls back to the system label rather than showing a bare code: that can only
 * happen if the platform hands back a locale this app no longer ships, and "System /
 * automatic" is what the app is doing at that point anyway.
 */
@Composable
private fun languageLabel(tag: String): String =
    AppLocale.LANGUAGES.firstOrNull { it.first == tag }?.second
        ?: stringResource(commonR.string.language_system)

/**
 * The master switch for the whole Shizuku section.
 *
 * [configured] is `isShizukuConfigured` — every field below filled. The author's rule is that
 * the switch "can only be toggled on if all the fields below are filled and gets automatically
 * toggled off if any field below is blank (but remembers the previous state in case a field
 * below is emptied and filled again)", which is why [checked] is the *effective* value while
 * the stored answer is left exactly where the user put it.
 *
 * ⚠ **The Switch is wrapped rather than merely disabled.** A disabled Switch swallows the
 * press, and a master control that does nothing at all when tapped reads as a broken app —
 * the same argument the settings manager's `TargetRow` makes, and the same shape.
 */
@Composable
private fun ManageShizukuRow(
    modifier: Modifier = Modifier,
    checked: Boolean,
    configured: Boolean,
    onCheckedChange: (Boolean) -> Unit,
    onBlocked: () -> Unit,
) {
    val contentColour = if (configured) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
    }

    Row(
        modifier = modifier
            .clickable { if (configured) onCheckedChange(!checked) else onBlocked() }
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = stringResource(R.string.manage_shizuku),
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Bold in full, which is how the author wrote it.
            Text(
                text = stringResource(R.string.manage_shizuku_recommended),
                style = MaterialTheme.typography.bodySmall,
                fontWeight = FontWeight.Bold,
            )
        }

        Box(modifier = Modifier.clickable(enabled = !configured, onClick = onBlocked)) {
            GetoSwitch(
                checked = checked,
                enabled = configured,
                onCheckedChange = if (configured) onCheckedChange else null,
            )
        }
    }
}

/**
 * The ⓘ that sits *inside* the Thedjchi label, after its last word.
 *
 * ⚠ **Sized in `em`, not `dp`.** The placeholder is a hole in a line of text, so it has to scale
 * with the text - a fixed size would leave the icon too large or too small the moment the reader
 * changes their font size, and would knock the line height about while doing it.
 *
 * Still its own tap target, outside nothing: the composable filling a placeholder is a real
 * composable, so its `clickable` takes the press before the row's `selectable` sees it, and
 * tapping the ⓘ explains the option rather than choosing it - the arrangement the sibling button
 * had, kept.
 */
@Composable
private fun forkInfoInline(onClick: () -> Unit): Map<String, InlineTextContent> {
    val tint = MaterialTheme.colorScheme.primary

    return mapOf(
        FORK_INFO_ID to InlineTextContent(
            placeholder = Placeholder(
                width = FORK_INFO_EM.em,
                height = FORK_INFO_EM.em,
                placeholderVerticalAlign = PlaceholderVerticalAlign.TextCenter,
            ),
        ) {
            Icon(
                modifier = Modifier
                    .fillMaxSize()
                    .clickable(onClick = onClick),
                imageVector = GetoIcons.Info,
                contentDescription = null,
                tint = tint,
            )
        },
    )
}

/**
 * The ⓘ beside a fork's name, opening that fork's setup pop-up.
 *
 * Always visible, on the author's instruction, and outside the row's `selectable` so that
 * tapping it explains the option rather than choosing it — the same arrangement
 * [SheveryCaution] already has.
 *
 * ⚠ Unused since r4q on the Thedjchi row, which now carries its ⓘ inline - see
 * [forkInfoInline]. Kept because the Shevery row's caution is built the same way and a future
 * row with a one-line label wants exactly this.
 */
@Suppress("unused")
@Composable
private fun ForkInfoButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .padding(start = 6.dp)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(15.dp),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/**
 * Why a greyed Display over other apps row will not move, as the paths that put it right.
 *
 * ⚠ **The three terms of [overlayManageable], asked separately.** That property collapses them
 * into one boolean, which is the right answer to "may this run" and the wrong answer to "where
 * do I go" — the fix is somewhere different for each of the three.
 *
 * Null means the row is usable and there is nothing to explain. An **empty** list means
 * Shevery: there Display over other apps is not unconfigured but unsupported, so the caller
 * says so and offers no path rather than sending somebody to a picker that can never help.
 *
 * Decided once here and handed to both dialogs, so the two cannot disagree about why the same
 * row is grey.
 */
@Composable
internal fun overlayBlockedPaths(userData: UserData): List<String>? {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    val reasons = overlayBlockReasons(userData = userData)

    if (reasons.isEmpty()) return null

    return reasons.mapNotNull { reason ->
        when (reason) {
            // Nothing to point at. The empty list this leaves is what tells the dialog to say
            // the fork sentence instead of the configure-first one.
            OverlayBlockReason.ForkUnsupported -> null

            OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

            OverlayBlockReason.NothingSelected -> dooaPath
        }
    }
}

/**
 * The four rows that decide how the app *looks*: Dynamic Theme, Theme, OLED background mode and
 * Progressive UI blur.
 *
 * ⚠ **Lifted out of the User interface section in r19b so the setup flow can draw the same
 * thing.** The author asked for a Customise UI page *"which shows these settings (first 4 ones of
 * user interface section)"*, and every other setup step in this app is the settings composable
 * itself rather than a page that resembles it — which is what keeps a row added later from
 * appearing in one place and not the other.
 *
 * ⚠ **It owns the theme picker.** The dialog used to live at the bottom of `SettingsScreen`, four
 * hundred lines from the row that opens it; a page drawing these rows without it would have had a
 * Theme row that did nothing. State that belongs to a row belongs with it.
 *
 * ⚠ **Two of the four are conditional, and the conditions are not this composable's opinion.**
 * OLED background mode is absent while the app is light — the mode blacks out a dark scheme's page
 * and returns a light one untouched, so the row would be a switch that visibly does nothing — and
 * Progressive UI blur is absent below API 31, where `RenderEffect.createBlurEffect` does not
 * exist and the edges get the shadow fade whatever a switch says.
 */
@Composable
internal fun UserInterfaceLookRows(
    userData: UserData,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
    onUpdateBlurSettings: (radiusDp: Int, tintPercent: Int, fadeDp: Int) -> Unit,
) {
    var showThemeDialog by rememberSaveable { mutableStateOf(false) }

    var showBlurSettingsDialog by rememberSaveable { mutableStateOf(false) }

    var selectedTheme by rememberSaveable(userData.theme) {
        mutableIntStateOf(userData.theme.ordinal)
    }

    DynamicThemeSetting(
        dynamicTheme = userData.dynamicTheme,
        onUpdateDynamicTheme = onUpdateDynamicTheme,
    )

    SettingsRowDivider()

    SettingsColumn(
        icon = painterResource(designR.drawable.ic_theme),
        title = stringResource(R.string.theme),
        subtitle = userData.theme.getTitle(),
        onClick = { showThemeDialog = true },
    )

    // Asked by luminance rather than isSystemInDarkTheme(): the app has its own
    // light/dark/follow-system setting, and the system's answer is the wrong one for a
    // light-themed app on a dark-themed phone. It also
    // survives dynamic colour, where there is no scheme of ours to consult, and it stays true
    // once the mode is on - black is darker still.
    if (MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE) {
        SettingsRowDivider()

        SwitchSetting(
            title = stringResource(R.string.oled_background_mode),
            subtitle = stringResource(R.string.oled_background_mode_summary),
            checked = userData.oledBackground,
            onCheckedChange = onUpdateOledBackground,
        )
    }

    // The divider goes inside the test with it, or the section shows two rules with nothing
    // between them.
    // ⚠ **Split in two — r20.** The switch still turns the blur on and off; the title and
    // subtitle now open the sliders behind it, with the vertical rule between them that every
    // other both-a-switch-and-a-screen row in this app has. See [SplitToggleSetting] for why
    // that rule is not decoration.
    if (supportsProgressiveBlur()) {
        SettingsRowDivider()

        SplitToggleSetting(
            title = stringResource(R.string.progressive_ui_blur),
            subtitle = stringResource(R.string.progressive_ui_blur_summary),
            checked = userData.progressiveBlur,
            onClick = { showBlurSettingsDialog = true },
            onCheckedChange = onUpdateProgressiveBlur,
        )
    }

    if (showThemeDialog) {
        ThemeDialog(
            onDismissRequest = { showThemeDialog = false },
            selected = selectedTheme,
            onSelect = { selectedTheme = it },
            onChangeClick = {
                onUpdateTheme(Theme.entries[selectedTheme])

                showThemeDialog = false
            },
        )
    }

    if (showBlurSettingsDialog) {
        BlurSettingsDialog(
            radiusDp = userData.blurRadiusDp,
            tintPercent = userData.blurTintPercent,
            fadeDp = userData.blurFadeDp,
            onDismissRequest = { showBlurSettingsDialog = false },
            onUpdateBlurSettings = onUpdateBlurSettings,
        )
    }
}
