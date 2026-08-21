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
package com.android.geto.feature.apps

import androidx.annotation.VisibleForTesting
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.broadcastreceiver.buildAppliedSettingsNotification
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.FavouriteAppsData
import com.android.geto.domain.model.FavouriteAppsTapAction
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.feature.apps.dialog.FavouriteAppsOptionsDialog
import com.android.geto.feature.apps.dialog.ReorderFavouriteAppsDialog
import com.android.geto.feature.apps.dialog.RevertSettingsDialog
import androidx.compose.ui.platform.LocalContext
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlin.time.Duration.Companion.milliseconds

@Composable
internal fun FavouriteAppsRoute(
    modifier: Modifier = Modifier,
    viewModel: FavouriteAppsViewModel = hiltViewModel(),
    snackbarHostState: SnackbarHostState,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
) {
    val favouriteAppsUiState by viewModel.favouriteAppsUiState.collectAsStateWithLifecycle()

    val appLaunch by viewModel.appLaunch.collectAsStateWithLifecycle()

    val manualRevert by viewModel.manualRevertState.collectAsStateWithLifecycle()

    ApplyThenLaunchEffect(
        appLaunch = appLaunch,
        snackbarHostState = snackbarHostState,
        onConsumed = viewModel::consumeAppLaunch,
    )

    ManualRevertEffect(
        manualRevertState = manualRevert,
        snackbarHostState = snackbarHostState,
        onConsumed = viewModel::consumeManualRevertResult,
    )

    FavouriteAppsScreen(
        modifier = modifier,
        favouriteAppsUiState = favouriteAppsUiState,
        manualRevertState = manualRevert,
        onToggleRevertTarget = viewModel::toggleManualRevertTarget,
        onRevert = viewModel::revertNow,
        onRevertOne = viewModel::revertOneNow,
        onModifyApp = onClickApp,
        onLaunchApp = viewModel::launchApp,
        onSearch = viewModel::search,
        onUpdateSortFavouriteApps = viewModel::updateSortFavouriteApps,
        onUpdateFavouriteAppsView = viewModel::updateFavouriteAppsView,
        onUpdateFavouriteAppsTapAction = viewModel::updateFavouriteAppsTapAction,
        onUpdateFavouriteComponentNames = viewModel::updateFavouriteComponentNames,
    )
}

/**
 * Applies the app's settings, posts the ongoing notification with the Revert action, then
 * opens the app — the same three steps a pinned shortcut performs, so a favourite behaves
 * identically however it is launched.
 *
 * An app with nothing configured is simply opened; there is no point refusing to launch it
 * or nagging about a configuration the user never made.
 */
@Composable
private fun ApplyThenLaunchEffect(
    appLaunch: FavouriteAppLaunch?,
    snackbarHostState: SnackbarHostState,
    onConsumed: () -> Unit,
) {
    val context = LocalContext.current

    val launcherApps = LocalLauncherApps.current

    val notificationManager = LocalNotificationManager.current

    val title = stringResource(R.string.applied_settings_title)

    val successText = stringResource(R.string.applied_settings_success)

    val failureText = stringResource(R.string.applied_settings_failure)

    val invalidText = stringResource(R.string.applied_settings_invalid)

    val noPermissionText = stringResource(R.string.applied_settings_no_permission)

    LaunchedEffect(appLaunch) {
        val launch = appLaunch ?: return@LaunchedEffect

        // showSnackbar suspends until the snackbar is dismissed. Switching tabs in that
        // window cancels this effect, and without the finally the launch would never be
        // consumed — coming back would replay the snackbar.
        try {
            when (launch.result) {
                AppSettingsResult.Success -> {
                    // Keyed on the component name so each target app owns its own
                    // notification and its own Revert action.
                    val notificationId = launch.componentName.hashCode()

                    notificationManager.notify(
                        id = notificationId,
                        notification = buildAppliedSettingsNotification(
                            context = context,
                            notificationId = notificationId,
                            componentName = launch.componentName,
                            icon = launch.icon,
                            contentTitle = title,
                            contentText = successText,
                        ),
                    )

                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                AppSettingsResult.EmptyAppSettings,
                AppSettingsResult.DisabledAppSettings,
                -> {
                    launcherApps.startMainActivity(componentName = launch.componentName)
                }

                AppSettingsResult.Failure -> snackbarHostState.showSnackbar(message = failureText)

                AppSettingsResult.InvalidValues -> snackbarHostState.showSnackbar(message = invalidText)

                AppSettingsResult.NoPermission -> snackbarHostState.showSnackbar(message = noPermissionText)
            }
        } finally {
            onConsumed()
        }
    }
}

@VisibleForTesting
@Composable
internal fun FavouriteAppsScreen(
    modifier: Modifier = Modifier,
    favouriteAppsUiState: FavouriteAppsUiState,
    manualRevertState: ManualRevertState,
    onToggleRevertTarget: (ManualRevertTarget, Set<ManualRevertTarget>) -> Unit,
    onRevert: (Set<ManualRevertTarget>) -> Unit,
    onRevertOne: (ManualRevertTarget) -> Unit,
    onModifyApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLaunchApp: (componentName: String) -> Unit,
    onSearch: (String) -> Unit,
    onUpdateSortFavouriteApps: (SortFavouriteApps) -> Unit,
    onUpdateFavouriteAppsView: (FavouriteAppsView) -> Unit,
    onUpdateFavouriteAppsTapAction: (FavouriteAppsTapAction) -> Unit,
    onUpdateFavouriteComponentNames: (List<String>) -> Unit,
) {
    var showRevertDialog by rememberSaveable { mutableStateOf(false) }

    // Read from the persisted preferences, so the ticks survive closing the dialog, the
    // app, and the device. Before they have loaded the dialog cannot be opened anyway.
    val selectedTargets = (favouriteAppsUiState as? FavouriteAppsUiState.Success)
        ?.favouriteAppsData?.userData?.manualRevertTargets

    Box(modifier = modifier.fillMaxSize()) {
        when (favouriteAppsUiState) {
            FavouriteAppsUiState.Loading -> {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            }

            is FavouriteAppsUiState.Success -> {
                Success(
                    favouriteAppsData = favouriteAppsUiState.favouriteAppsData,
                    onModifyApp = onModifyApp,
                    onLaunchApp = onLaunchApp,
                    onSearch = onSearch,
                    onUpdateSortFavouriteApps = onUpdateSortFavouriteApps,
                    onUpdateFavouriteAppsView = onUpdateFavouriteAppsView,
                    onUpdateFavouriteAppsTapAction = onUpdateFavouriteAppsTapAction,
                    onUpdateFavouriteComponentNames = onUpdateFavouriteComponentNames,
                )
            }
        }

        if (selectedTargets != null) {
            FloatingActionButton(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp),
                onClick = { showRevertDialog = true },
            ) {
                Icon(
                    imageVector = GetoIcons.Restore,
                    contentDescription = stringResource(R.string.revert_settings),
                )
            }
        }
    }

    if (showRevertDialog && selectedTargets != null) {
        RevertSettingsDialog(
            selected = selectedTargets,
            busy = manualRevertState.busy,
            onDismissRequest = { showRevertDialog = false },
            onToggle = { onToggleRevertTarget(it, selectedTargets) },
            onRevertOne = onRevertOne,
            onRevert = {
                onRevert(selectedTargets)

                // Closed straight away: the work continues in the ViewModel and reports
                // itself through the snackbar, so holding the dialog open would only hide
                // the list the user is about to go back to.
                showRevertDialog = false
            },
        )
    }
}

/**
 * Reports what a manual revert actually managed to do. Partial results are named rather
 * than rounded up to "done": being told everything is back when Shizuku is still down is
 * worse than being told nothing at all.
 */
@Composable
private fun ManualRevertEffect(
    manualRevertState: ManualRevertState,
    snackbarHostState: SnackbarHostState,
    onConsumed: () -> Unit,
) {
    val doneText = stringResource(R.string.revert_done)

    val failedText = stringResource(R.string.revert_failed)

    val noPermissionText = stringResource(R.string.revert_no_permission)

    val result = manualRevertState.result

    val partialText = stringResource(
        R.string.revert_partial,
        result?.reverted?.size ?: 0,
        manualRevertState.requested,
    )

    LaunchedEffect(result) {
        if (result == null) return@LaunchedEffect

        try {
            val message = when {
                result.noPermission -> noPermissionText
                result.reverted.isEmpty() -> failedText
                result.failed.isEmpty() -> doneText
                else -> partialText
            }

            snackbarHostState.showSnackbar(message = message)
        } finally {
            onConsumed()
        }
    }
}

@OptIn(FlowPreview::class)
@Composable
private fun Success(
    modifier: Modifier = Modifier,
    favouriteAppsData: FavouriteAppsData,
    onModifyApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLaunchApp: (componentName: String) -> Unit,
    onSearch: (String) -> Unit,
    onUpdateSortFavouriteApps: (SortFavouriteApps) -> Unit,
    onUpdateFavouriteAppsView: (FavouriteAppsView) -> Unit,
    onUpdateFavouriteAppsTapAction: (FavouriteAppsTapAction) -> Unit,
    onUpdateFavouriteComponentNames: (List<String>) -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }

    var showOptionsDialog by remember { mutableStateOf(false) }

    var showReorderDialog by remember { mutableStateOf(false) }

    val userData = favouriteAppsData.userData

    LaunchedEffect(Unit) {
        snapshotFlow { query }.debounce(300.milliseconds)
            .distinctUntilChanged()
            .collect { onSearch(it) }
    }

    // A plain tap does one of the two things and the long press does the other, so
    // both handlers are derived from the single stored preference.
    val tapToLaunch = userData.favouriteAppsTapAction == FavouriteAppsTapAction.TapToLaunch

    val onTap: (LauncherAppsActivityInfo) -> Unit = { info ->
        if (tapToLaunch) {
            onLaunchApp(info.componentName)
        } else {
            onModifyApp(info.componentName, info.activityLabel)
        }
    }

    val onLongPress: (LauncherAppsActivityInfo) -> Unit = { info ->
        if (tapToLaunch) {
            onModifyApp(info.componentName, info.activityLabel)
        } else {
            onLaunchApp(info.componentName)
        }
    }

    Column(modifier = modifier.fillMaxSize()) {
        AppsSearchField(
            query = query,
            onQueryChange = { query = it },
            trailingIcon = {
                IconButton(
                    onClick = {
                        showOptionsDialog = true
                    },
                ) {
                    Icon(
                        imageVector = GetoIcons.Tune,
                        contentDescription = stringResource(R.string.favourite_apps_options),
                    )
                }
            },
        )

        if (favouriteAppsData.launcherAppsActivityInfos.isEmpty()) {
            // Distinguishes "you have no favourites" from "your search matched none of
            // them", which are very different things to be told.
            EmptyFavourites(searching = query.isNotEmpty())
        } else {
            when (userData.favouriteAppsView) {
                FavouriteAppsView.List -> {
                    LazyColumn(modifier = Modifier.fillMaxSize()) {
                        items(
                            items = favouriteAppsData.launcherAppsActivityInfos,
                            key = { it.componentName },
                        ) { info ->
                            FavouriteAppListItem(
                                launcherAppsActivityInfo = info,
                                onTap = { onTap(info) },
                                onLongPress = { onLongPress(info) },
                            )
                        }
                    }
                }

                FavouriteAppsView.Grid -> {
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(96.dp),
                        modifier = Modifier.fillMaxSize(),
                    ) {
                        items(
                            items = favouriteAppsData.launcherAppsActivityInfos,
                            key = { it.componentName },
                        ) { info ->
                            FavouriteAppGridItem(
                                launcherAppsActivityInfo = info,
                                onTap = { onTap(info) },
                                onLongPress = { onLongPress(info) },
                            )
                        }
                    }
                }
            }
        }
    }

    if (showOptionsDialog) {
        FavouriteAppsOptionsDialog(
            sortFavouriteApps = userData.sortFavouriteApps,
            favouriteAppsView = userData.favouriteAppsView,
            favouriteAppsTapAction = userData.favouriteAppsTapAction,
            canReorder = favouriteAppsData.allFavouriteApps.size > 1,
            onDismissRequest = {
                showOptionsDialog = false
            },
            onUpdateSortFavouriteApps = onUpdateSortFavouriteApps,
            onUpdateFavouriteAppsView = onUpdateFavouriteAppsView,
            onUpdateFavouriteAppsTapAction = onUpdateFavouriteAppsTapAction,
            onReorderClick = {
                showOptionsDialog = false
                showReorderDialog = true
            },
        )
    }

    if (showReorderDialog) {
        ReorderFavouriteAppsDialog(
            favouriteApps = favouriteAppsData.allFavouriteApps,
            savedComponentNames = userData.favouriteComponentNames,
            onDismissRequest = {
                showReorderDialog = false
            },
            onUpdateFavouriteComponentNames = { componentNames ->
                onUpdateFavouriteComponentNames(componentNames)

                // Reordering only makes sense against the custom order, so switch to it
                // rather than saving an order the user cannot see.
                onUpdateSortFavouriteApps(SortFavouriteApps.Custom)

                showReorderDialog = false
            },
        )
    }
}

@Composable
private fun EmptyFavourites(
    modifier: Modifier = Modifier,
    searching: Boolean,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            modifier = Modifier.size(100.dp),
            imageVector = GetoIcons.StarBorder,
            contentDescription = null,
        )

        Spacer(modifier = Modifier.height(10.dp))

        Text(
            text = if (searching) {
                stringResource(R.string.no_matching_favourite_apps)
            } else {
                stringResource(R.string.no_favourite_apps)
            },
            style = MaterialTheme.typography.titleLarge,
            textAlign = TextAlign.Center,
        )

        if (!searching) {
            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.no_favourite_apps_subtitle),
                style = MaterialTheme.typography.bodyLarge,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun FavouriteAppListItem(
    modifier: Modifier = Modifier,
    launcherAppsActivityInfo: LauncherAppsActivityInfo,
    onTap: () -> Unit,
    onLongPress: () -> Unit,
) {
    ListItem(
        modifier = modifier.combinedClickable(
            onClick = onTap,
            onLongClick = onLongPress,
        ),
        headlineContent = {
            Text(text = launcherAppsActivityInfo.activityLabel)
        },
        leadingContent = {
            AppIcon(launcherAppsActivityInfo = launcherAppsActivityInfo, size = 50.dp)
        },
    )
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun FavouriteAppGridItem(
    modifier: Modifier = Modifier,
    launcherAppsActivityInfo: LauncherAppsActivityInfo,
    onTap: () -> Unit,
    onLongPress: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .combinedClickable(
                onClick = onTap,
                onLongClick = onLongPress,
            )
            .padding(horizontal = 4.dp, vertical = 10.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        AppIcon(launcherAppsActivityInfo = launcherAppsActivityInfo, size = 56.dp)

        Spacer(modifier = Modifier.height(6.dp))

        Text(
            text = launcherAppsActivityInfo.activityLabel,
            style = MaterialTheme.typography.labelMedium,
            textAlign = TextAlign.Center,
            maxLines = 2,
            overflow = TextOverflow.Ellipsis,
        )
    }
}
