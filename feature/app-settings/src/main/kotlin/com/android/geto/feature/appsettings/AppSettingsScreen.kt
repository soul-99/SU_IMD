/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.feature.appsettings

import androidx.annotation.VisibleForTesting
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyItemScope
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.BottomAppBar
import androidx.compose.material3.BottomAppBarDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.FloatingActionButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.component.GetoCheckbox
import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.common.showRestoredToast
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.AddAppSettingResult
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingTemplate
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.GetPinShortcutResult
import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.RequestPinShortcutResult
import com.android.geto.domain.model.SecureSetting
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.UpdatePinShortcutResult
import com.android.geto.feature.appsettings.dialog.AppSettingDialog
import com.android.geto.feature.appsettings.dialog.RequestPinShortcutDialog
import com.android.geto.feature.appsettings.dialog.TemplateDialog
import com.android.geto.feature.appsettings.dialog.UpdatePinShortcutDialog
import com.android.geto.feature.appsettings.dialog.WriteSecureSettingsDialog
import com.android.geto.feature.appsettings.navigation.AppSettingsRouteData
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import kotlinx.coroutines.FlowPreview
import com.android.geto.common.R as commonR

@Composable
internal fun AppSettingsRoute(
    modifier: Modifier = Modifier,
    viewModel: AppSettingsViewModel = hiltViewModel(),
    appSettingsRouteData: AppSettingsRouteData,
    onNavigationIconClick: () -> Unit,
) {
    val appSettingsUiState by viewModel.appSettingsUiState.collectAsStateWithLifecycle()

    val secureSettings by viewModel.secureSettings.collectAsStateWithLifecycle()

    val applyAppSettingsResult by viewModel.applyAppSettingsResult.collectAsStateWithLifecycle()

    val revertAppSettingsResult by viewModel.revertAppSettingsResult.collectAsStateWithLifecycle()

    val addAppSettingResult by viewModel.addAppSettingsResult.collectAsStateWithLifecycle()

    val activityIcon by viewModel.activityIcon.collectAsStateWithLifecycle()

    val requestPinShortcutResult by viewModel.requestPinShortcutResult.collectAsStateWithLifecycle()

    val appSettingTemplates by viewModel.appSettingTemplates.collectAsStateWithLifecycle()

    val blockedAppSettings by viewModel.blockedAppSettings.collectAsStateWithLifecycle()

    val getPinShortcutResult by viewModel.getPinShortcutResult.collectAsStateWithLifecycle()

    val updatePinShortcutResult by viewModel.updatePinShortcutResult.collectAsStateWithLifecycle()

    val isFavourite by viewModel.isFavourite.collectAsStateWithLifecycle()

    val context = LocalContext.current

    AppSettingsScreen(
        modifier = modifier,
        appSettingsRouteData = appSettingsRouteData,
        appSettingsUiState = appSettingsUiState,
        activityIcon = activityIcon,
        secureSettings = secureSettings,
        addAppSettingResult = addAppSettingResult,
        applyAppSettingsResult = applyAppSettingsResult,
        revertAppSettingsResult = revertAppSettingsResult,
        requestPinShortcutResult = requestPinShortcutResult,
        appSettingTemplates = appSettingTemplates,
        blockedAppSettings = blockedAppSettings,
        updatePinShortcutResult = updatePinShortcutResult,
        isFavourite = isFavourite,
        onUpdateFavourite = viewModel::updateFavourite,
        onApplyAppSettings = viewModel::applyAppSettings,
        onRestoreThenApply = viewModel::restoreThenApply,
        onDiscardThenApply = viewModel::discardThenApply,
        onRevertAppSettings = {
            // Said on the press rather than on the result. This is the memory revert, and
            // the only thing distinguishing it from "Revert to default" from the user's
            // side is which button was pressed — so the answer has to arrive with the press.
            context.showRestoredToast(
                fromMemory = true,
                appName = appSettingsRouteData.activityLabel,
            )

            viewModel.revertAppSettings()
        },
        onCheckAppSetting = viewModel::checkAppSetting,
        onDeleteAppSetting = viewModel::deleteAppSetting,
        onAddAppSetting = viewModel::addAppSetting,
        onRequestPinShortcut = viewModel::requestPinShortcut,
        onGetSecureSettingsByName = viewModel::getSecureSettingsByName,
        onResetApplyAppSettingsResult = viewModel::resetApplyAppSettingsResult,
        onResetRequestPinShortcutResult = viewModel::resetRequestPinShortcutResult,
        onResetRevertAppSettingsResult = viewModel::resetRevertAppSettingsResult,
        onResetAddAppSettingResult = viewModel::resetAddAppSettingResult,
        onNavigationIconClick = onNavigationIconClick,
        getPinShortcutResult = getPinShortcutResult,
        onGetPinShortcut = viewModel::getPinShorcut,
        onResetGetPinShortcutResult = viewModel::resetGetPinShortcutResult,
        onUpdatePinShortcut = viewModel::updatePinShorcut,
        onResetUpdatePinShortcutResult = viewModel::resetUpdatePinShortcutResult,
    )
}

@VisibleForTesting
@Composable
internal fun AppSettingsScreen(
    modifier: Modifier = Modifier,
    appSettingsRouteData: AppSettingsRouteData,
    appSettingsUiState: AppSettingsUiState,
    activityIcon: ByteArray?,
    secureSettings: List<SecureSetting>,
    addAppSettingResult: AddAppSettingResult?,
    applyAppSettingsResult: AppSettingsResult?,
    revertAppSettingsResult: AppSettingsResult?,
    requestPinShortcutResult: RequestPinShortcutResult?,
    appSettingTemplates: List<AppSettingTemplate>,
    /** Which drawn keys are greyed, and why the Display over other apps one is. */
    blockedAppSettings: BlockedAppSettings,
    getPinShortcutResult: GetPinShortcutResult?,
    updatePinShortcutResult: UpdatePinShortcutResult?,
    isFavourite: Boolean,
    onUpdateFavourite: (Boolean) -> Unit,
    onApplyAppSettings: () -> Unit,
    /**
     * The force-close popup's two answers, both of which end in this screen's launch running
     * again. See `SettingsHiddenRunner.discardPendingReverts` — the second one is permanent.
     */
    onRestoreThenApply: () -> Unit,
    onDiscardThenApply: () -> Unit,
    onRevertAppSettings: () -> Unit,
    onCheckAppSetting: (appSetting: AppSetting) -> Unit,
    onDeleteAppSetting: (appSetting: AppSetting) -> Unit,
    onAddAppSetting: (AppSetting) -> Unit,
    onRequestPinShortcut: (
        icon: ByteArray?,
        shortLabel: String,
        longLabel: String,
    ) -> Unit,
    onGetSecureSettingsByName: (settingType: SettingType, text: String) -> Unit,
    onResetApplyAppSettingsResult: () -> Unit,
    onResetRequestPinShortcutResult: () -> Unit,
    onResetRevertAppSettingsResult: () -> Unit,
    onResetAddAppSettingResult: () -> Unit,
    onNavigationIconClick: () -> Unit,
    onGetPinShortcut: () -> Unit,
    onResetGetPinShortcutResult: () -> Unit,
    onUpdatePinShortcut: (
        icon: ByteArray?,
        shortLabel: String,
        longLabel: String,
    ) -> Unit,
    onResetUpdatePinShortcutResult: () -> Unit,
) {
    var showAppSettingDialog by rememberSaveable { mutableStateOf(false) }

    var showTemplateDialog by rememberSaveable { mutableStateOf(false) }

    // Null while nothing is refusing; a list of location trees otherwise, empty for the one
    // case with nothing to point at - Shevery, where Display over other apps is unsupported
    // rather than unconfigured. The empty list is what picks the fork sentence over the
    // configure-first one. Same convention as the two configuration dialogs.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val dooaPath = stringResource(R.string.help_path_dooa)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    // ⚠ **The decision is not repeated here, only the wording.** `overlayBlockReasons` in
    // `:domain:model` is the single answer to why the overlay row will not move; this module
    // cannot see the other two modules' resources, so what is duplicated is five strings
    // rather than a rule.
    val pathsFor = { key: String ->
        when (key) {
            AppSettingKeys.SYSTEM_ALERT_WINDOW -> blockedAppSettings.overlayReasons.mapNotNull {
                when (it) {
                    OverlayBlockReason.ForkUnsupported -> null

                    OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

                    OverlayBlockReason.NothingSelected -> dooaPath
                }
            }

            AppSettingKeys.SHIZUKU_SERVICE -> listOf(manageShizukuPath)

            else -> listOf(accessibilityPath)
        }
    }

    var showWriteSecureSettingsDialog by rememberSaveable { mutableStateOf(false) }

    // Settings are down from a run of IMD that is no longer alive. Saved like its neighbours:
    // losing it to a rotation would leave a launch that simply did nothing, with the only
    // explanation gone.
    var showPriorHideDialog by rememberSaveable { mutableStateOf(false) }

    val snackbarHostState = remember { SnackbarHostState() }

    AppSettingsLaunchedEffects(
        appSettingsRouteData = appSettingsRouteData,
        snackbarHostState = snackbarHostState,
        activityIcon = activityIcon,
        addAppSettingResult = addAppSettingResult,
        applyAppSettingsResult = applyAppSettingsResult,
        revertAppSettingsResult = revertAppSettingsResult,
        requestPinShortcutResult = requestPinShortcutResult,
        getPinShortcutResult = getPinShortcutResult,
        updatePinShortcutResult = updatePinShortcutResult,
        onResetApplyAppSettingsResult = onResetApplyAppSettingsResult,
        onResetRevertAppSettingsResult = onResetRevertAppSettingsResult,
        onResetRequestPinShortcutResult = onResetRequestPinShortcutResult,
        onResetAddAppSettingResult = onResetAddAppSettingResult,
        onShowWriteSecureSettingsDialog = {
            showWriteSecureSettingsDialog = true
        },
        onShowPriorHideDialog = {
            showPriorHideDialog = true
        },
        onResetGetPinShortcutResult = onResetGetPinShortcutResult,
        onResetUpdatePinShortcutResult = onResetUpdatePinShortcutResult,
    )

    Scaffold(
        topBar = {
            AppSettingsTopAppBar(
                title = appSettingsRouteData.activityLabel,
                onNavigationIconClick = onNavigationIconClick,
            )
        },
        bottomBar = {
            AppSettingsBottomAppBar(
                isFavourite = isFavourite,
                onFavouriteIconClick = {
                    onUpdateFavourite(!isFavourite)
                },
                onRefreshIconClick = onRevertAppSettings,
                onSettingsIconClick = {
                    showAppSettingDialog = true
                },
                onShortcutIconClick = onGetPinShortcut,
                onSettingsSuggestIconClick = {
                    showTemplateDialog = true
                },
                onFloatingActionButtonClick = onApplyAppSettings,
            )
        },
        snackbarHost = {
            SnackbarHost(hostState = snackbarHostState)
        },
    ) { innerPadding ->
        Box(
            modifier = modifier
                .fillMaxSize()
                .padding(innerPadding),
        ) {
            when (appSettingsUiState) {
                AppSettingsUiState.Loading -> {
                    CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
                }

                is AppSettingsUiState.Success -> {
                    if (appSettingsUiState.appSettings.isNotEmpty()) {
                        Success(
                            appSettingsUiState = appSettingsUiState,
                            blockedKeys = blockedAppSettings.keys,
                            onBlockedClick = { blockedPaths = pathsFor(it) },
                            onCheckAppSetting = onCheckAppSetting,
                            onDeleteAppSettingsItem = onDeleteAppSetting,
                        )
                    } else {
                        Empty(
                            title = stringResource(R.string.no_settings_found),
                            subtitle = stringResource(R.string.add_your_first_settings),
                        )
                    }
                }
            }
        }
    }

    if (showAppSettingDialog) {
        AppSettingDialog(
            componentName = appSettingsRouteData.componentName,
            secureSettings = secureSettings,
            onAddAppSetting = onAddAppSetting,
            onDismissRequest = {
                showAppSettingDialog = false
            },
            onGetSecureSettingsByName = onGetSecureSettingsByName,
        )
    }

    blockedPaths?.let { paths ->
        ConfigureFirstDialog(
            message = if (paths.isEmpty()) {
                stringResource(R.string.dooa_thedjchi_only)
            } else {
                stringResource(R.string.configure_first)
            },
            paths = paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blockedPaths = null },
        )
    }

    if (showTemplateDialog) {
        TemplateDialog(
            appSettingTemplates = appSettingTemplates,
            componentName = appSettingsRouteData.componentName,
            blockedKeys = blockedAppSettings.keys,
            onBlockedClick = { blockedPaths = pathsFor(it) },
            onAddAppSetting = onAddAppSetting,
            onDismissRequest = {
                showTemplateDialog = false
            },
        )
    }

    if (showWriteSecureSettingsDialog) {
        WriteSecureSettingsDialog(
            onDismissRequest = {
                showWriteSecureSettingsDialog = false
            },
        )
    }

    // Dismissed before either call, so the Shizuku spinner a restore may need is not hidden
    // behind a dialog that has already been answered.
    if (showPriorHideDialog) {
        PriorHideDialog(
            title = stringResource(commonR.string.prior_hide_title),
            restoreLabel = stringResource(commonR.string.prior_hide_restore),
            ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
            onRestore = {
                showPriorHideDialog = false

                onRestoreThenApply()
            },
            onIgnore = {
                showPriorHideDialog = false

                onDiscardThenApply()
            },
        )
    }

    when (getPinShortcutResult) {
        GetPinShortcutResult.RequestPinShortcut -> {
            RequestPinShortcutDialog(
                icon = activityIcon,
                activityLabel = appSettingsRouteData.activityLabel,
                onDismissRequest = onResetGetPinShortcutResult,
                onRequestPinShortcut = onRequestPinShortcut,
            )
        }

        is GetPinShortcutResult.UpdatePinShortcut -> {
            UpdatePinShortcutDialog(
                icon = activityIcon,
                getoShortcutInfoCompat = getPinShortcutResult.getoShortcutInfoCompat,
                onDismissRequest = onResetGetPinShortcutResult,
                onUpdatePinShortcut = onUpdatePinShortcut,
            )
        }

        GetPinShortcutResult.UnsupportedLauncher, null -> Unit
    }
}

@OptIn(FlowPreview::class)
@Composable
private fun AppSettingsLaunchedEffects(
    appSettingsRouteData: AppSettingsRouteData,
    snackbarHostState: SnackbarHostState,
    activityIcon: ByteArray?,
    addAppSettingResult: AddAppSettingResult?,
    applyAppSettingsResult: AppSettingsResult?,
    revertAppSettingsResult: AppSettingsResult?,
    requestPinShortcutResult: RequestPinShortcutResult?,
    getPinShortcutResult: GetPinShortcutResult?,
    updatePinShortcutResult: UpdatePinShortcutResult?,
    onResetApplyAppSettingsResult: () -> Unit,
    onResetRevertAppSettingsResult: () -> Unit,
    onResetRequestPinShortcutResult: () -> Unit,
    onResetAddAppSettingResult: () -> Unit,
    onShowWriteSecureSettingsDialog: () -> Unit,
    onShowPriorHideDialog: () -> Unit,
    onResetGetPinShortcutResult: () -> Unit,
    onResetUpdatePinShortcutResult: () -> Unit,
) {
    val context = LocalContext.current

    val androidLauncherAppsWrapper = LocalLauncherApps.current

    val androidNotificationManagerWrapper = LocalNotificationManager.current

    val appSettingsDisabled = stringResource(id = R.string.app_settings_disabled)

    val emptyAppSettingsList = stringResource(id = R.string.empty_app_settings_list)

    val applyFailure = stringResource(id = R.string.apply_failure)

    val revertFailure = stringResource(id = R.string.revert_failure)

    val revertSuccess = stringResource(id = R.string.revert_success)

    val shortcutUpdateImmutableShortcuts =
        stringResource(id = R.string.shortcut_update_immutable_shortcuts)

    val shortcutUpdateFailed = stringResource(id = R.string.shortcut_update_failed)

    val shortcutUpdateSuccess = stringResource(id = R.string.shortcut_update_success)

    val supportedLauncher = stringResource(id = R.string.supported_launcher)

    val unsupportedLauncher = stringResource(id = R.string.unsupported_launcher)

    val invalidValues = stringResource(R.string.settings_has_invalid_values)

    val appSettingAddSuccess = stringResource(R.string.app_setting_added_successfully)

    val appSettingAddFailed = stringResource(R.string.app_setting_already_exists)

    val autoHideConflict = stringResource(R.string.auto_hide_conflict_snackbar)

    LaunchedEffect(key1 = applyAppSettingsResult) {
        when (applyAppSettingsResult) {
            AppSettingsResult.DisabledAppSettings -> {
                snackbarHostState.showSnackbar(message = appSettingsDisabled)

                onResetApplyAppSettingsResult()
            }

            AppSettingsResult.EmptyAppSettings -> {
                snackbarHostState.showSnackbar(message = emptyAppSettingsList)

                onResetApplyAppSettingsResult()
            }

            AppSettingsResult.Failure -> {
                snackbarHostState.showSnackbar(message = applyFailure)

                onResetApplyAppSettingsResult()
            }

            // Per-app profiles do not touch overlay access, so this cannot arise here; the
            // generic failure text is still the honest thing to show if it ever does.
            AppSettingsResult.OverlayFailure -> {
                snackbarHostState.showSnackbar(message = applyFailure)

                onResetApplyAppSettingsResult()
            }

            AppSettingsResult.NoPermission -> {
                onShowWriteSecureSettingsDialog()

                onResetApplyAppSettingsResult()
            }

            // Nothing was written and the app is not opening. The dialog below is the only
            // surface this screen has for it, and both of its answers come back here.
            AppSettingsResult.HiddenFromPreviousUse -> {
                onShowPriorHideDialog()

                onResetApplyAppSettingsResult()
            }

            AppSettingsResult.Success -> {
                postAppliedSettingsNotification(
                    context = context,
                    notificationManager = androidNotificationManagerWrapper,
                )

                androidLauncherAppsWrapper.startMainActivity(componentName = appSettingsRouteData.componentName)

                onResetApplyAppSettingsResult()
            }

            AppSettingsResult.InvalidValues -> {
                snackbarHostState.showSnackbar(message = invalidValues)

                onResetApplyAppSettingsResult()
            }

            // Only the device-wide configuration can be empty, and this screen never applies
            // it - it applies the profile for one app. Reset and say nothing rather than show
            // a message about a screen this one has nothing to do with.
            AppSettingsResult.NothingToHide -> onResetApplyAppSettingsResult()

            // Applied from this screen rather than from a launch, so there is no app to open
            // and nothing to say: the settings this profile asks for are already off.
            AppSettingsResult.AlreadyHidden -> onResetApplyAppSettingsResult()

            // Auto-hide settings (IMD+) is holding the device down with a different list, and
            // this profile cannot be applied on top of it without leaving settings that
            // neither revert puts back.
            AppSettingsResult.AutoHideConflict -> {
                snackbarHostState.showSnackbar(message = autoHideConflict)

                onResetApplyAppSettingsResult()
            }

            null -> Unit
        }
    }

    LaunchedEffect(key1 = revertAppSettingsResult) {
        when (revertAppSettingsResult) {
            AppSettingsResult.DisabledAppSettings -> {
                snackbarHostState.showSnackbar(message = appSettingsDisabled)

                // Without this reset the StateFlow keeps the same value, so every later
                // tap of revert produces no emission and the button looks dead.
                onResetRevertAppSettingsResult()
            }

            // A revert cannot produce it — the gate is on the hide — but the `when` is
            // exhaustive over the same enum and silence here would be a compile error rather
            // than a decision.
            AppSettingsResult.HiddenFromPreviousUse -> onResetRevertAppSettingsResult()

            AppSettingsResult.EmptyAppSettings -> {
                snackbarHostState.showSnackbar(message = emptyAppSettingsList)

                onResetRevertAppSettingsResult()
            }

            AppSettingsResult.Failure -> {
                snackbarHostState.showSnackbar(message = revertFailure)

                onResetRevertAppSettingsResult()
            }

            AppSettingsResult.OverlayFailure -> {
                snackbarHostState.showSnackbar(message = revertFailure)

                onResetRevertAppSettingsResult()
            }

            AppSettingsResult.NoPermission -> {
                onShowWriteSecureSettingsDialog()

                onResetRevertAppSettingsResult()
            }

            AppSettingsResult.Success -> {
                snackbarHostState.showSnackbar(message = revertSuccess)

                onResetRevertAppSettingsResult()
            }

            AppSettingsResult.InvalidValues -> {
                snackbarHostState.showSnackbar(message = invalidValues)

                onResetRevertAppSettingsResult()
            }

            // Reverting a per-app profile never reads the device-wide configuration, so this
            // cannot arise here either. Nor can the two IMD+ outcomes: both are decided on the
            // way in, by the apply, and a revert is asked for after that decision was made.
            AppSettingsResult.NothingToHide,
            AppSettingsResult.AlreadyHidden,
            AppSettingsResult.AutoHideConflict,
            -> onResetRevertAppSettingsResult()

            null -> Unit
        }
    }

    LaunchedEffect(key1 = requestPinShortcutResult) {
        when (requestPinShortcutResult) {
            RequestPinShortcutResult.SupportedLauncher -> {
                snackbarHostState.showSnackbar(message = supportedLauncher)

                onResetRequestPinShortcutResult()
            }

            RequestPinShortcutResult.UnsupportedLauncher -> {
                snackbarHostState.showSnackbar(message = unsupportedLauncher)

                onResetRequestPinShortcutResult()
            }

            null -> Unit
        }
    }

    LaunchedEffect(key1 = addAppSettingResult) {
        when (addAppSettingResult) {
            AddAppSettingResult.Success -> {
                snackbarHostState.showSnackbar(message = appSettingAddSuccess)

                onResetAddAppSettingResult()
            }

            AddAppSettingResult.Failed -> {
                snackbarHostState.showSnackbar(message = appSettingAddFailed)

                onResetAddAppSettingResult()
            }

            null -> Unit
        }
    }

    LaunchedEffect(key1 = getPinShortcutResult) {
        if (getPinShortcutResult == GetPinShortcutResult.UnsupportedLauncher) {
            snackbarHostState.showSnackbar(message = unsupportedLauncher)

            onResetGetPinShortcutResult()
        }
    }

    LaunchedEffect(key1 = updatePinShortcutResult) {
        when (updatePinShortcutResult) {
            UpdatePinShortcutResult.UnsupportedLauncher -> {
                snackbarHostState.showSnackbar(message = unsupportedLauncher)

                onResetUpdatePinShortcutResult()
            }

            UpdatePinShortcutResult.UpdateSuccess -> {
                snackbarHostState.showSnackbar(message = shortcutUpdateSuccess)

                onResetUpdatePinShortcutResult()
            }

            UpdatePinShortcutResult.UpdateFailure -> {
                snackbarHostState.showSnackbar(message = shortcutUpdateFailed)

                onResetUpdatePinShortcutResult()
            }

            UpdatePinShortcutResult.UpdateImmutableShortcuts -> {
                snackbarHostState.showSnackbar(message = shortcutUpdateImmutableShortcuts)

                onResetUpdatePinShortcutResult()
            }

            null -> Unit
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun AppSettingsTopAppBar(
    modifier: Modifier = Modifier,
    title: String,
    onNavigationIconClick: () -> Unit,
) {
    TopAppBar(
        modifier = modifier,
        title = {
            Text(text = title, maxLines = 1)
        },
        navigationIcon = {
            IconButton(onClick = onNavigationIconClick) {
                Icon(
                    imageVector = GetoIcons.Back,
                    contentDescription = null,
                )
            }
        },
    )
}

@Composable
private fun AppSettingsBottomAppBar(
    isFavourite: Boolean,
    onFavouriteIconClick: () -> Unit,
    onRefreshIconClick: () -> Unit,
    onSettingsIconClick: () -> Unit,
    onShortcutIconClick: () -> Unit,
    onSettingsSuggestIconClick: () -> Unit,
    onFloatingActionButtonClick: () -> Unit,
) {
    BottomAppBar(
        actions = {
            AppSettingsBottomAppBarActions(
                isFavourite = isFavourite,
                onFavouriteIconClick = onFavouriteIconClick,
                onRefreshIconClick = onRefreshIconClick,
                onSettingsIconClick = onSettingsIconClick,
                onShortcutIconClick = onShortcutIconClick,
                onSettingsSuggestIconClick = onSettingsSuggestIconClick,
            )
        },
        floatingActionButton = {
            AppSettingsFloatingActionButton(
                onClick = onFloatingActionButtonClick,
            )
        },
    )
}

@Composable
private fun AppSettingsFloatingActionButton(onClick: () -> Unit) {
    FloatingActionButton(
        onClick = onClick,
        containerColor = BottomAppBarDefaults.bottomAppBarFabColor,
        elevation = FloatingActionButtonDefaults.bottomAppBarFabElevation(),
    ) {
        Icon(
            imageVector = GetoIcons.ArrowForward,
            contentDescription = null,
        )
    }
}

@Composable
private fun RowScope.AppSettingsBottomAppBarActions(
    isFavourite: Boolean,
    onFavouriteIconClick: () -> Unit,
    onRefreshIconClick: () -> Unit,
    onSettingsIconClick: () -> Unit,
    onShortcutIconClick: () -> Unit,
    onSettingsSuggestIconClick: () -> Unit,
) {
    // Every action shares the row equally rather than sitting at its natural width. Four
    // captions plus the star will not fit side by side at their natural widths on a normal
    // phone, and equal columns keep the labels centred under their icons on every screen.
    LabelledAction(
        modifier = Modifier.weight(1f),
        icon = GetoIcons.Refresh,
        label = stringResource(R.string.action_revert),
        onClick = onRefreshIconClick,
    )

    LabelledAction(
        modifier = Modifier.weight(1f),
        icon = GetoIcons.Settings,
        label = stringResource(R.string.action_app_setting),
        onClick = onSettingsIconClick,
    )

    LabelledAction(
        modifier = Modifier.weight(1f),
        icon = GetoIcons.SettingsSuggest,
        label = stringResource(R.string.action_setting_template),
        onClick = onSettingsSuggestIconClick,
    )

    LabelledAction(
        modifier = Modifier.weight(1f),
        icon = GetoIcons.Shortcut,
        label = stringResource(R.string.action_create_shortcut),
        onClick = onShortcutIconClick,
    )

    // Left unlabelled: a star needs no caption, and it keeps its place immediately before
    // the launch button.
    IconButton(onClick = onFavouriteIconClick) {
        Icon(
            imageVector = if (isFavourite) GetoIcons.Star else GetoIcons.StarBorder,
            contentDescription = if (isFavourite) {
                stringResource(R.string.remove_from_favourites)
            } else {
                stringResource(R.string.add_to_favourites)
            },
            tint = if (isFavourite) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        )
    }
}

/** An icon with its name underneath, sized to sit inside a bottom app bar. */
@Composable
private fun LabelledAction(
    modifier: Modifier = Modifier,
    icon: ImageVector,
    label: String,
    onClick: () -> Unit,
) {
    Column(
        modifier = modifier
            .clip(MaterialTheme.shapes.small)
            .clickable(onClick = onClick)
            .padding(vertical = 4.dp, horizontal = 2.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            modifier = Modifier.size(22.dp),
            imageVector = icon,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.height(2.dp))

        Text(
            text = label,
            style = MaterialTheme.typography.labelSmall,
            textAlign = TextAlign.Center,
            // Two lines so "Setting template" and "Create shortcut" break rather than
            // being clipped on a narrow screen.
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
            lineHeight = 12.sp,
        )
    }
}

@Composable
private fun Empty(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
) {
    Column(
        modifier = modifier
            .fillMaxSize(),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            modifier = Modifier.size(100.dp),
            imageVector = GetoIcons.Android,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text(text = title, style = MaterialTheme.typography.titleLarge)

        Spacer(modifier = Modifier.height(10.dp))

        Text(text = subtitle, style = MaterialTheme.typography.bodyLarge)
    }
}

@Composable
private fun Success(
    modifier: Modifier = Modifier,
    appSettingsUiState: AppSettingsUiState.Success,
    blockedKeys: Set<String>,
    onBlockedClick: (String) -> Unit,
    onCheckAppSetting: (AppSetting) -> Unit,
    onDeleteAppSettingsItem: (AppSetting) -> Unit,
) {
    LazyColumn(modifier = modifier) {
        items(items = appSettingsUiState.appSettings, key = { it.id }) { appSettings ->
            AppSettingItem(
                appSetting = appSettings,
                enabled = appSettings.key !in blockedKeys,
                onBlockedClick = { onBlockedClick(appSettings.key) },
                onCheckedChange = { check ->
                    onCheckAppSetting(
                        appSettings.copy(enabled = check),
                    )
                },
                onDeleteClick = {
                    onDeleteAppSettingsItem(appSettings)
                },
            )
        }
    }
}

@Composable
private fun LazyItemScope.AppSettingItem(
    modifier: Modifier = Modifier,
    appSetting: AppSetting,
    enabled: Boolean,
    onBlockedClick: () -> Unit,
    onCheckedChange: (Boolean) -> Unit,
    onDeleteClick: () -> Unit,
) {
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    ListItem(
        modifier = modifier
            .animateItem()
            .then(if (enabled) Modifier else Modifier.clickable(onClick = onBlockedClick)),
        headlineContent = {
            Text(
                text = appSetting.label,
                color = contentColour,
            )
        },
        overlineContent = {
            Text(
                text = appSetting.key,
                color = contentColour,
            )
        },
        supportingContent = {
            Text(
                text = appSetting.settingType.getSettingTypeTitle(),
                color = contentColour,
            )
        },
        leadingContent = {
            // ⚠ **Unticked while blocked, and only in the drawing.** The stored row is not
            // touched - `onCheckedChange` cannot be reached from here - so the tick comes
            // straight back when the thing this row needs is configured again. The author:
            // "shown unchecked and unclickable with the checkbox position remembered".
            //
            // ⚠ **Wrapped in a Box, not merely disabled.** A disabled Checkbox swallows the
            // press inside its own bounds, so the ListItem's clickable above would never see
            // a tap on the one control the user is aiming at.
            Box(
                modifier = if (enabled) {
                    Modifier
                } else {
                    Modifier.clickable(onClick = onBlockedClick)
                },
            ) {
                GetoCheckbox(
                    checked = enabled && appSetting.enabled,
                    enabled = enabled,
                    onCheckedChange = onCheckedChange,
                )
            }
        },
        trailingContent = {
            IconButton(onClick = onDeleteClick) {
                Icon(
                    imageVector = Icons.Default.Delete,
                    contentDescription = null,
                )
            }
        },
    )
}

/** Material's disabled content alpha, restated where a row draws its own colours. */
private const val DISABLED_CONTENT_ALPHA = 0.38f

@Composable
internal fun SettingType.getSettingTypeTitle() = when (this) {
    SettingType.SYSTEM -> stringResource(commonR.string.system)
    SettingType.SECURE -> stringResource(commonR.string.secure)
    SettingType.GLOBAL -> stringResource(commonR.string.global)
}
