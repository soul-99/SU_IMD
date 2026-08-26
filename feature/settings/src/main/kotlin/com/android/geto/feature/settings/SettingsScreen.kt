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
import androidx.compose.foundation.clickable
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
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
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ColorFilter
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.LinkAnnotation
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextLinkStyles
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.text.withLink
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.PopupProperties
import androidx.core.content.ContextCompat
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import coil.compose.AsyncImage
import com.android.geto.common.AppLocale
import com.android.geto.common.ProjectLinks
import com.android.geto.common.SettingsChangeLog
import com.android.geto.common.openObtainium
import com.android.geto.common.openProjectUri
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.theme.supportsDynamicTheming
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.OverlayPackageData
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.withoutOverlayWhenUnmanaged
import com.android.geto.feature.settings.dialog.AccessibilityServicesDialog
import com.android.geto.feature.settings.dialog.AutoRevertNoticeDialog
import com.android.geto.feature.settings.dialog.LanguageDialog
import com.android.geto.feature.settings.dialog.ManageOverlayNoticeDialog
import com.android.geto.feature.settings.dialog.NotificationFunctionDialog
import com.android.geto.feature.settings.dialog.OverlayPackagesDialog
import com.android.geto.feature.settings.dialog.OverlayUnreadableDialog
import com.android.geto.feature.settings.dialog.RevertDefaultsDialog
import com.android.geto.feature.settings.dialog.SettingsChangeLogDialog
import com.android.geto.feature.settings.dialog.SettingsToHideDialog
import com.android.geto.feature.settings.dialog.SupportDialog
import com.android.geto.feature.settings.dialog.TaskerIntegrationPage
import com.android.geto.feature.settings.dialog.ThemeDialog
import com.android.geto.feature.settings.help.SetupHelpDialog
import com.android.geto.service.SettingsObserverService
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.drop
import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.common.R as commonR

/** How long the Shizuku text fields wait after the last keystroke before persisting. */
private val COMMIT_DEBOUNCE = 500.milliseconds

/** The dark red the author asked for on the Support button; white text keeps AA contrast on it. */
private val SUPPORT_BUTTON_COLOUR = Color(0xFFB71C1C)

private const val AUTHOR_LINK_TAG = "author"
private const val AUTHOR_EMAIL = "utkarshrajput@hotmail.com"
private const val AUTHOR_GITHUB_URL = "https://github.com/soul-99"
private const val CONTRIBUTOR_GITHUB_URL = "https://github.com/RafayGhafoor"
private const val GETO_REPOSITORY_URL = "https://github.com/JackEblan/Geto"
private const val GETO_AUTHOR_GITHUB_URL = "https://github.com/JackEblan"
private const val LICENCE_URL = "https://www.gnu.org/licenses/gpl-3.0"
private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku/releases"
private const val SHIZUKU_SHEVERY_URL = "https://github.com/HmnDev-Tech/shevery/releases"

@Composable
internal fun SettingsRoute(
    modifier: Modifier = Modifier,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val settingsUiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val isServiceRunning by viewModel.isServiceRunning.collectAsStateWithLifecycle()

    val accessibilityServices by viewModel.accessibilityServices.collectAsStateWithLifecycle()

    val overlayPackages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    val installedApps by viewModel.installedApps.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.refreshAccessibilityServices()
    }

    SettingsScreen(
        modifier = modifier,
        settingsUiState = settingsUiState,
        isServiceRunning = isServiceRunning,
        accessibilityServices = accessibilityServices,
        overlayPackages = overlayPackages,
        installedApps = installedApps,
        onUpdateTheme = viewModel::updateTheme,
        onUpdateDynamicTheme = viewModel::updateDynamicTheme,
        onUpdateRestartShizuku = viewModel::updateRestartShizuku,
        onUpdateManageOverlay = viewModel::updateManageOverlay,
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
        onUpdateNotificationFunction = viewModel::updateNotificationFunction,
        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
        onUpdateSettingsToHide = viewModel::updateSettingsToHide,
        onRefreshAccessibilityServices = viewModel::refreshAccessibilityServices,
        onRefreshOverlayPackages = viewModel::refreshOverlayPackages,
        onRefreshInstalledApps = viewModel::refreshInstalledApps,
    )
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
    onUpdateTheme: (Theme) -> Unit,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateManageOverlay: (Boolean) -> Unit,
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
    onUpdateNotificationFunction: (NotificationFunction) -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
    onRefreshOverlayPackages: () -> Unit,
    onRefreshInstalledApps: () -> Unit,
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
                    onUpdateDynamicTheme = onUpdateDynamicTheme,
                    onUpdateTheme = onUpdateTheme,
                    onUpdateRestartShizuku = onUpdateRestartShizuku,
                    onUpdateManageOverlay = onUpdateManageOverlay,
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
                    onUpdateNotificationFunction = onUpdateNotificationFunction,
                    onUpdateRevertDefaults = onUpdateRevertDefaults,
                    onUpdateSettingsToHide = onUpdateSettingsToHide,
                    onRefreshAccessibilityServices = onRefreshAccessibilityServices,
                    onRefreshOverlayPackages = onRefreshOverlayPackages,
                    onRefreshInstalledApps = onRefreshInstalledApps,
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
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateTheme: (Theme) -> Unit,
    onUpdateRestartShizuku: (Boolean) -> Unit,
    onUpdateManageOverlay: (Boolean) -> Unit,
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
    onUpdateNotificationFunction: (NotificationFunction) -> Unit,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onRefreshAccessibilityServices: () -> Unit,
    onRefreshOverlayPackages: () -> Unit,
    onRefreshInstalledApps: () -> Unit,
) {
    val context = LocalContext.current

    var showThemeDialog by remember { mutableStateOf(false) }

    var showLanguageDialog by remember { mutableStateOf(false) }

    // Read from the platform rather than held in state: on Android 13 and up this can also
    // be changed from Android's own per-app language screen, and coming back to a stale
    // copy would show the wrong one until the app was killed.
    var languageTag by remember { mutableStateOf(AppLocale.stored(context)) }

    var showAccessibilityServicesDialog by remember { mutableStateOf(false) }

    var showOverlayPackagesDialog by remember { mutableStateOf(false) }

    var showNotificationFunctionDialog by remember { mutableStateOf(false) }

    var showRevertDefaultsDialog by remember { mutableStateOf(false) }

    // The manager dialog's long press, arriving as a count that only goes up. Keyed on the
    // count rather than seeded once, so the second and every later press opens the dialog
    // too -- seeding only worked while this screen was being composed for the first time,
    // which is exactly once per launch of the app.
    val revertConfigurationRequest = LocalRevertConfigurationRequest.current

    LaunchedEffect(revertConfigurationRequest) {
        if (revertConfigurationRequest > 0) showRevertDefaultsDialog = true
    }

    var showSettingsToHideDialog by remember { mutableStateOf(false) }

    var showSettingsLog by remember { mutableStateOf(false) }

    var showAutoRevertNotice by remember { mutableStateOf(false) }

    var showManageOverlayNotice by remember { mutableStateOf(false) }

    var showTaskerIntegration by remember { mutableStateOf(false) }

    // What the two configuration dialogs show and count. The overlay row is absent from
    // both until overlay management is switched on in Advanced, and the "x of y" summaries
    // have to agree with them - a summary reading "3 of 5" beside a dialog listing four
    // rows is the sort of mismatch that reads as a lost setting.
    val hideStates = userData.settingsToHide.withoutOverlayWhenUnmanaged(userData.manageOverlay)

    val revertStates = userData.revertDefaults
        .withoutOverlayWhenUnmanaged(userData.manageOverlay)

    // Read straight from the shared log rather than through the ViewModel: the writer is a
    // foreground service in another module with no repository of its own, and this is the
    // same arrangement SettingsObservationGate already uses for the running flag.
    val settingsLog by SettingsChangeLog.entries.collectAsStateWithLifecycle()

    var selectedTheme by remember { mutableIntStateOf(Theme.entries.indexOf(userData.theme)) }

    // Plain remember, not rememberSaveable: the sections reset on every visit so the screen
    // always opens the same way rather than in whatever state it was left in last week.
    // Same reasoning as the Shizuku configuration panel.
    //
    // Opens on Default IMD settings rather than on nothing. The two configurations in there
    // are what decides whether launching an app does anything at all, so a screen that
    // opens as five closed headings hides the only part most people ever need. Opening
    // another section closes this one, as before — it is still an accordion.
    var expanded by remember { mutableStateOf<SettingsSection?>(SettingsSection.AppFunctions) }

    val toggleSection = { section: SettingsSection ->
        expanded = if (expanded == section) null else section
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
    ) {
        CollapsibleSection(
            title = stringResource(R.string.section_ui),
            expanded = expanded == SettingsSection.Ui,
            onToggle = { toggleSection(SettingsSection.Ui) },
        ) {
            DynamicThemeSetting(
                dynamicTheme = userData.dynamicTheme,
                onUpdateDynamicTheme = onUpdateDynamicTheme,
            )

            SettingsColumn(
                title = stringResource(R.string.theme),
                subtitle = userData.theme.getTitle(),
                onClick = { showThemeDialog = true },
            )

            SettingsColumn(
                title = stringResource(R.string.language),
                subtitle = languageLabel(languageTag),
                onClick = { showLanguageDialog = true },
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
                title = stringResource(R.string.settings_to_hide),
                subtitle = stringResource(
                    R.string.settings_to_hide_summary,
                    hideStates.count { it.value },
                    hideStates.size,
                ),
                onClick = { showSettingsToHideDialog = true },
            )

            SettingsColumn(
                // Named for what it does here rather than for the dialog it opens: in a
                // list beside "Settings to hide", "Revert to default configuration" says
                // nothing about the relationship between the two.
                title = stringResource(R.string.revert_defaults_entry),
                subtitle = stringResource(
                    R.string.revert_defaults_summary,
                    revertStates.count { it.value },
                    revertStates.size,
                ),
                onClick = { showRevertDefaultsDialog = true },
            )

            // Third, under the two it qualifies. Which services this app may touch is part
            // of what "hide" and "unhide" mean above -- both rows say as much in their own
            // small print -- so a section of its own put one third of one answer somewhere
            // else entirely.
            SettingsColumn(
                title = stringResource(R.string.accessibility_services),
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
            // Present only once overlay management has been switched on in Advanced, along
            // with the overlay rows inside the two dialogs above. All three are what that
            // switch's notice asks the user to come here and fill in.
            if (userData.manageOverlay) {
                SettingsColumn(
                    title = stringResource(R.string.overlay_packages),
                    subtitle = overlayPackagesSubtitle(
                        overlayPackages = overlayPackages,
                        managed = userData.managedOverlayPackages,
                    ),
                    onClick = {
                        onRefreshOverlayPackages()

                        showOverlayPackagesDialog = true
                    },
                )
            }
        }

        CollapsibleSection(
            title = stringResource(R.string.shizuku),
            expanded = expanded == SettingsSection.Shizuku,
            onToggle = { toggleSection(SettingsSection.Shizuku) },
        ) {
            ShizukuSection(
                userData = userData,
                installedApps = installedApps,
                onUpdateShizukuForkMode = onUpdateShizukuForkMode,
                onUpdateShizukuAuthKey = onUpdateShizukuAuthKey,
                onUpdateShizukuPackageName = onUpdateShizukuPackageName,
                onUpdateShizukuStartAction = onUpdateShizukuStartAction,
                onRefreshInstalledApps = onRefreshInstalledApps,
            )
        }

        CollapsibleSection(
            title = stringResource(R.string.section_advanced),
            expanded = expanded == SettingsSection.Advanced,
            onToggle = { toggleSection(SettingsSection.Advanced) },
        ) {
            // First in Advanced, because it is the one switch here that adds and removes
            // settings elsewhere in this screen: three overlay rows under Default IMD
            // settings appear and disappear with it. Off by default, since overlay access
            // is the only thing IMD touches that cannot be written at all without a working
            // Shizuku service - on a device without one those three rows can only fail.
            SwitchSetting(
                title = stringResource(R.string.manage_overlay),
                subtitle = stringResource(R.string.manage_overlay_subtitle),
                checked = userData.manageOverlay,
                onCheckedChange = { wanted ->
                    onUpdateManageOverlay(wanted)

                    // After the switch moves rather than instead of it, and on every
                    // switch-on rather than once: there is nothing to agree to here, only
                    // three rows that have just appeared and do nothing until they are
                    // filled in.
                    if (wanted) showManageOverlayNotice = true
                },
            )

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

            // Advanced because the recommended answer is the default and nobody has to
            // come here: choosing the memory function means taking on a profile per app,
            // which is the opposite of what Default IMD settings above is for.
            SettingsColumn(
                title = stringResource(R.string.notification_function),
                subtitle = userData.notificationFunction.getTitle(),
                onClick = { showNotificationFunctionDialog = true },
            )

            RestartShizukuSetting(
                userData = userData,
                onUpdateRestartShizuku = onUpdateRestartShizuku,
            )

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

        AboutSection()

        Spacer(modifier = Modifier.height(24.dp))

        FossFooter()

        Spacer(modifier = Modifier.height(24.dp))
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

    if (showOverlayPackagesDialog) {
        // Null is "could not read", not "nothing to show". The picker opens on a list and the
        // notice opens on a null, because a picker that opened empty on a device where IMD
        // simply cannot see would tell the user they have nothing to choose from.
        val packages = overlayPackages

        if (packages == null) {
            OverlayUnreadableDialog(onDismissRequest = { showOverlayPackagesDialog = false })
        } else {
            OverlayPackagesDialog(
                overlayPackages = packages,
                selectedPackages = userData.managedOverlayPackages,
                onDismissRequest = { showOverlayPackagesDialog = false },
                onUpdateManagedOverlayPackages = onUpdateManagedOverlayPackages,
            )
        }
    }

    if (showAccessibilityServicesDialog) {
        AccessibilityServicesDialog(
            accessibilityServices = accessibilityServices,
            selectedServices = userData.managedAccessibilityServices,
            onDismissRequest = { showAccessibilityServicesDialog = false },
            onUpdateManagedAccessibilityServices = onUpdateManagedAccessibilityServices,
        )
    }

    if (showNotificationFunctionDialog) {
        NotificationFunctionDialog(
            selected = userData.notificationFunction,
            onDismissRequest = { showNotificationFunctionDialog = false },
            onUpdateNotificationFunction = onUpdateNotificationFunction,
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

    if (showManageOverlayNotice) {
        ManageOverlayNoticeDialog(
            onDismissRequest = { showManageOverlayNotice = false },
        )
    }

    if (showTaskerIntegration) {
        TaskerIntegrationPage(
            authKey = userData.taskerAuthKey,
            notificationFunction = userData.notificationFunction,
            onEnsureAuthKey = onEnsureTaskerAuthKey,
            onRefreshAuthKey = onRefreshTaskerAuthKey,
            onDismissRequest = { showTaskerIntegration = false },
        )
    }

    // Both dialogs are handed the stored map rather than the trimmed one above. They decide
    // for themselves which rows to draw; what they must not do is save back a map with the
    // overlay entry missing, which would clear a choice made while the feature was on.
    if (showRevertDefaultsDialog) {
        RevertDefaultsDialog(
            states = userData.revertDefaults,
            shizukuConfigured = userData.isShizukuConfigured,
            manageOverlay = userData.manageOverlay,
            onDismissRequest = { showRevertDefaultsDialog = false },
            onUpdateRevertDefaults = onUpdateRevertDefaults,
        )
    }

    if (showSettingsToHideDialog) {
        SettingsToHideDialog(
            states = userData.settingsToHide,
            shizukuConfigured = userData.isShizukuConfigured,
            manageOverlay = userData.manageOverlay,
            onDismissRequest = { showSettingsToHideDialog = false },
            onUpdateSettingsToHide = onUpdateSettingsToHide,
        )
    }
}

/**
 * Which section is open.
 *
 * One at a time rather than a flag per section: the screen is a short list of five headings
 * when everything is shut, and that is the state it is most useful in — opening one section
 * should not mean scrolling past another that was left open.
 */
private enum class SettingsSection {
    Ui,
    AppFunctions,
    Shizuku,
    Advanced,
}

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
    Card(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 12.dp, vertical = 4.dp),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = if (expanded) {
                MaterialTheme.colorScheme.surfaceContainer
            } else {
                MaterialTheme.colorScheme.surfaceContainerLow
            },
        ),
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
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

            Icon(
                imageVector = if (expanded) GetoIcons.ExpandLess else GetoIcons.ExpandMore,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }

        if (expanded) {
            HorizontalDivider(color = MaterialTheme.colorScheme.outlineVariant)

            Column(modifier = Modifier.padding(bottom = 8.dp)) {
                content()
            }
        }
    }
}

@OptIn(FlowPreview::class)
/**
 * Whether a revert that puts USB debugging back should also start Shizuku again.
 *
 * Under Advanced rather than beside the Shizuku fields it depends on, because it is a
 * decision about what reverting does — the same kind of thing as the notification function
 * above it — while that section is the connection details it needs in order to work at all.
 *
 * Enablement is read from the stored configuration rather than from the fields' live edit
 * state, which is what the switch used while it sat among them. From another section there
 * is nothing live to read, and by the time anyone has collapsed one section and opened
 * another the debounced write has long since landed.
 */
@Composable
private fun RestartShizukuSetting(
    modifier: Modifier = Modifier,
    userData: UserData,
    onUpdateRestartShizuku: (Boolean) -> Unit,
) {
    var showFillHint by rememberSaveable { mutableStateOf(false) }

    val configured = userData.isShizukuConfigured

    Column(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier
                .clickable {
                    if (configured) {
                        onUpdateRestartShizuku(!userData.restartShizuku)
                    } else {
                        // Rather than a dead switch with no explanation, say what is
                        // missing — and now also where, since the fields it needs are in a
                        // different section from this switch.
                        showFillHint = true
                    }
                }
                .fillMaxWidth()
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            // Title and description in one column, the way every other setting on this
            // screen stacks a title over its subtitle. As a sibling of the row the
            // description was separated from its own title by the row's vertical padding
            // while sitting flush against the next setting, so it read as belonging to
            // the wrong one.
            Column(modifier = Modifier.weight(1f).padding(end = 16.dp)) {
                Text(
                    text = stringResource(R.string.restart_shizuku_service),
                    style = MaterialTheme.typography.bodyLarge,
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = stringResource(R.string.restart_shizuku_service_description),
                    style = MaterialTheme.typography.bodySmall,
                )
            }

            // A null onCheckedChange leaves the switch with no input modifier of its own,
            // so a tap on it falls through to the row above and shows the hint instead of
            // being silently swallowed by a disabled control.
            Switch(
                checked = userData.restartShizuku,
                enabled = configured,
                onCheckedChange = if (configured) onUpdateRestartShizuku else null,
            )
        }

        if (showFillHint && !configured) {
            Text(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 6.dp),
                text = stringResource(R.string.shizuku_fill_advanced),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
            )
        }
    }
}

@Composable
private fun ShizukuSection(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    onUpdateShizukuForkMode: (ShizukuForkMode) -> Unit,
    onUpdateShizukuAuthKey: (String) -> Unit,
    onUpdateShizukuPackageName: (String) -> Unit,
    onUpdateShizukuStartAction: (String) -> Unit,
    onRefreshInstalledApps: () -> Unit,
) {
    // Seeded once from the stored values and then owned locally. Reading them back out of
    // the preferences flow on every keystroke would fight the cursor.
    var startAction by rememberSaveable { mutableStateOf(userData.shizukuStartAction) }

    var packageName by rememberSaveable { mutableStateOf(userData.shizukuPackageName) }

    var authKey by rememberSaveable { mutableStateOf(userData.shizukuAuthKey) }

    val forkMode = userData.shizukuForkMode

    // Committed on a pause rather than per keystroke: each write is a full proto rewrite
    // plus an emission that recomposes this whole screen. drop(1) skips the seed value so
    // simply opening Settings does not write anything.
    LaunchedEffect(Unit) {
        snapshotFlow { startAction }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuStartAction(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { packageName }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuPackageName(it) }
    }

    LaunchedEffect(Unit) {
        snapshotFlow { authKey }.drop(1).debounce(COMMIT_DEBOUNCE)
            .distinctUntilChanged()
            .collect { onUpdateShizukuAuthKey(it) }
    }

    // The picker needs the installed-app list to be able to preselect anything. Asked for
    // as soon as the section is composed, now that the fields are always on screen rather
    // than behind a panel that had to be opened first.
    LaunchedEffect(Unit) {
        onRefreshInstalledApps()
    }

    Column(modifier = modifier.fillMaxWidth()) {
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
            text = AnnotatedString(stringResource(R.string.shizuku_rikka_warning)),
        )

        WarningLine(text = shizukuRikkaRecommendation())

        Spacer(modifier = Modifier.height(12.dp))

        ForkModeSelector(
            selected = forkMode,
            onSelect = { mode ->
                if (mode != forkMode) {
                    // Picking a family is the only moment the app knows enough to fill
                    // these in, and the two families disagree about every one of them.
                    // Written into the visible fields rather than applied behind the
                    // scenes, so a wrong guess is something the user can see and fix.
                    val suggested = ShizukuForkDefaults.packageFor(
                        mode = mode,
                        apps = installedApps,
                    )

                    packageName = suggested

                    startAction = ShizukuForkDefaults.actionFor(
                        mode = mode,
                        selectedLabel = installedApps.labelOf(suggested),
                    )

                    onUpdateShizukuForkMode(mode)
                }
            },
        )

        if (forkMode != ShizukuForkMode.Unset) {
            Text(
                modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp),
                text = stringResource(
                    if (forkMode == ShizukuForkMode.Thedjchi) {
                        R.string.shizuku_view_intents_hint
                    } else {
                        R.string.shizuku_other_fork_hint
                    },
                ),
                style = MaterialTheme.typography.bodySmall,
            )

            PackageNameField(
                value = packageName,
                installedApps = installedApps,
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

            ShizukuField(
                value = startAction,
                label = stringResource(R.string.shizuku_start_action),
                onValueChange = { startAction = it },
            )

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
) {
    Column(modifier = modifier.selectableGroup()) {
        ForkModeRow(
            label = AnnotatedString(stringResource(R.string.shizuku_fork_mode_thedjchi)),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
        )

        ForkModeRow(
            label = sheveryForkLabel(),
            selected = selected == ShizukuForkMode.Other,
            onSelect = { onSelect(ShizukuForkMode.Other) },
        )
    }
}

@Composable
private fun ForkModeRow(
    modifier: Modifier = Modifier,
    label: AnnotatedString,
    selected: Boolean,
    onSelect: () -> Unit,
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

        Text(
            modifier = Modifier.weight(1f),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )
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
private fun AboutSection(modifier: Modifier = Modifier) {
    var showAuthorDialog by rememberSaveable { mutableStateOf(false) }

    var showHelp by rememberSaveable { mutableStateOf(false) }

    var showSupport by rememberSaveable { mutableStateOf(false) }

    // Every composable read is hoisted out of the builder lambdas: resources and theme
    // colours are resolved once per recomposition rather than once per span.
    val linkStyles = linkStyles()

    val createdBy = stringResource(R.string.about_created_by)

    val authorName = stringResource(R.string.about_author_name)

    val forkOf = stringResource(R.string.about_fork_of)

    val getoApp = stringResource(R.string.about_geto_app)

    val licenceName = stringResource(R.string.about_licence_name)

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

    val contributionsLabel = stringResource(R.string.about_contributions)

    val contributorName = stringResource(R.string.about_contributor_name)

    val contributorScope = stringResource(R.string.about_contributor_scope)

    // Just the contributor now, sitting under the "Contributions;" heading rather than after
    // an inline label. Separators appended here, not typed into the strings: aapt strips
    // leading and trailing whitespace from an unquoted string resource.
    val contributorLine = remember(contributorName, contributorScope, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = CONTRIBUTOR_GITHUB_URL, styles = linkStyles)) {
                append(contributorName)
            }
            append(" ")
            append(contributorScope)
        }
    }

    val forkAuthor = stringResource(R.string.about_fork_author)

    val forkBy = stringResource(R.string.about_fork_by)

    // "Fork of Geto by JackEblan (Blanc)" - two links in one line: Geto to its repository,
    // and the original author's name to his GitHub profile.
    val fork = remember(forkOf, getoApp, forkBy, forkAuthor, linkStyles) {
        buildAnnotatedString {
            append(forkOf)
            append(" ")
            withLink(LinkAnnotation.Url(url = GETO_REPOSITORY_URL, styles = linkStyles)) {
                append(getoApp)
            }
            append(" ")
            append(forkBy)
            append(" ")
            withLink(LinkAnnotation.Url(url = GETO_AUTHOR_GITHUB_URL, styles = linkStyles)) {
                append(forkAuthor)
            }
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
        // First thing in About and a filled button rather than a link, because it is the
        // one item here that does something rather than saying something — and it is the
        // page a confused user needs, not the licence.
        Button(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 16.dp),
            onClick = { showHelp = true },
        ) {
            Text(text = stringResource(R.string.help_button))
        }

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

        // Two lines of air, not one. Everything above this point is about the installed
        // version and where to get the next one; everything below is who wrote it and under
        // what licence. The gap is what separates the two, since neither has a heading.
        Spacer(modifier = Modifier.height(40.dp))

        // Directly above the author line, because it is that line's ask made loud: the person
        // who reads "created by soul_99" is exactly the one this is addressed to. A fixed red
        // rather than a theme colour, at the author's request, with white text so it stays
        // legible in both light and dark; the heart-hands emoji in the label carries the
        // intent, so there is no separate icon to double it.
        Button(
            modifier = Modifier
                .fillMaxWidth()
                .padding(bottom = 20.dp),
            onClick = { showSupport = true },
            colors = ButtonDefaults.buttonColors(
                containerColor = SUPPORT_BUTTON_COLOUR,
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
        Text(text = author, style = MaterialTheme.typography.bodyLarge)

        Spacer(modifier = Modifier.height(14.dp))

        // "Contributions" is a heading now, with the contributor named on the line below it -
        // the semicolon is appended here so translations do not each have to remember it.
        AboutHeading(text = "$contributionsLabel;")

        Spacer(modifier = Modifier.height(2.dp))

        Text(text = contributorLine, style = MaterialTheme.typography.bodyMedium)

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
        SetupHelpDialog(onDismissRequest = { showHelp = false })
    }

    if (showSupport) {
        SupportDialog(onDismissRequest = { showSupport = false })
    }
}

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

    val linkStyles = linkStyles()

    val label = stringResource(R.string.about_version, versionName)

    val version = remember(label, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = ProjectLinks.CHANGELOG, styles = linkStyles)) {
                append(label)
            }
        }
    }

    Text(
        modifier = modifier,
        text = version,
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
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 4.dp),
    ) {
        Icon(
            modifier = Modifier.size(16.dp),
            imageVector = GetoIcons.Info,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.error,
        )

        Spacer(modifier = Modifier.size(8.dp))

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
            withLink(LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_URL, styles = linkStyles)) {
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

    val suffix = stringResource(R.string.shizuku_fork_mode_other_suffix)

    return remember(shevery, suffix, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = SHIZUKU_SHEVERY_URL, styles = linkStyles)) {
                append(shevery)
            }
            append(" ")
            append(suffix)
        }
    }
}

@Composable
private fun AuthorDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    val context = LocalContext.current

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                modifier = Modifier.padding(bottom = 8.dp),
                text = stringResource(R.string.about_author_name),
                style = MaterialTheme.typography.titleLarge,
            )

            LinkRow(
                text = stringResource(R.string.about_view_github),
                onClick = { context.openProjectUri(AUTHOR_GITHUB_URL) },
            )

            LinkRow(
                text = AUTHOR_EMAIL,
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

@Composable
private fun LinkRow(
    modifier: Modifier = Modifier,
    text: String,
    onClick: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            modifier = Modifier.weight(1f),
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        Icon(
            modifier = Modifier.size(16.dp),
            imageVector = GetoIcons.Link,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary,
        )
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

        Switch(checked = checked, onCheckedChange = onCheckedChange)
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
                .clickable(onClick = onClick)
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

        Box(modifier = Modifier.padding(horizontal = 16.dp)) {
            Switch(checked = checked, onCheckedChange = onCheckedChange)
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
    onClick: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(horizontal = 16.dp, vertical = 12.dp),
    ) {
        Text(text = title, style = MaterialTheme.typography.bodyLarge)

        Spacer(modifier = Modifier.height(6.dp))

        Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
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
internal fun NotificationFunction.getTitle() = when (this) {
    NotificationFunction.Memory -> stringResource(R.string.notification_function_memory)
    NotificationFunction.RevertToDefault -> stringResource(R.string.notification_function_revert)
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
