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
import androidx.compose.foundation.layout.Row
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
import androidx.compose.material3.SmallFloatingActionButton
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.FavouriteAppsData
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.feature.apps.dialog.FavouriteAppsOptionsDialog
import com.android.geto.feature.apps.dialog.ReorderFavouriteAppsDialog
import com.android.geto.feature.apps.manager.SettingsManagerRoute
import com.android.geto.feature.appsettings.shortcut.ShortcutRoute
import com.android.geto.ui.local.LocalLauncherApps
import com.android.geto.ui.local.LocalNotificationManager
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.designsystem.R as designR

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

    var notConfigured by rememberSaveable { mutableStateOf(false) }

    ApplyThenLaunchEffect(
        appLaunch = appLaunch,
        snackbarHostState = snackbarHostState,
        onNotConfigured = { notConfigured = true },
        onConsumed = viewModel::consumeAppLaunch,
    )

    if (notConfigured) {
        NotConfiguredDialog(onDismissRequest = { notConfigured = false })
    }

    FavouriteAppsScreen(
        modifier = modifier,
        favouriteAppsUiState = favouriteAppsUiState,
        onModifyApp = onClickApp,
        onLaunchApp = viewModel::launchApp,
        onSearch = viewModel::search,
        onUpdateSortFavouriteApps = viewModel::updateSortFavouriteApps,
        onUpdateFavouriteAppsView = viewModel::updateFavouriteAppsView,
        onUpdateFavouriteComponentNames = viewModel::updateFavouriteComponentNames,
        onRevertToDefault = viewModel::revertToDefault,
    )
}

@VisibleForTesting
@Composable
internal fun FavouriteAppsScreen(
    modifier: Modifier = Modifier,
    favouriteAppsUiState: FavouriteAppsUiState,
    onModifyApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLaunchApp: (componentName: String) -> Unit,
    onSearch: (String) -> Unit,
    onUpdateSortFavouriteApps: (SortFavouriteApps) -> Unit,
    onUpdateFavouriteAppsView: (FavouriteAppsView) -> Unit,
    onUpdateFavouriteComponentNames: (List<String>) -> Unit,
    onRevertToDefault: () -> Unit,
) {
    var showRevertDialog by rememberSaveable { mutableStateOf(false) }

    // Read from the persisted preferences, so the ticks survive closing the dialog, the
    // app, and the device. Before they have loaded the dialog cannot be opened anyway.
    // The manager is not tied to any selection any more, so it is offered whenever the
    // screen has something to show.
    val managerAvailable = favouriteAppsUiState is FavouriteAppsUiState.Success

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
                    onUpdateFavouriteComponentNames = onUpdateFavouriteComponentNames,
                )
            }
        }

        if (managerAvailable) {
            Row(
                modifier = Modifier
                    .align(Alignment.BottomEnd)
                    .padding(16.dp),
                horizontalArrangement = Arrangement.spacedBy(12.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // Left of the manager, and visibly secondary to it: this one acts, the
                // other one opens something. A tonal container rather than the primary one
                // keeps a one-press device-wide change from being the loudest thing on the
                // screen.
                SmallFloatingActionButton(
                    onClick = onRevertToDefault,
                    containerColor = MaterialTheme.colorScheme.secondaryContainer,
                    contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
                ) {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_revert_glyph),
                        contentDescription = stringResource(R.string.revert_to_default),
                    )
                }

                FloatingActionButton(onClick = { showRevertDialog = true }) {
                    // The Quick Settings tile artwork rather than two stacked Material
                    // icons: the tile, the launcher shortcut and this button all open the
                    // same dialog, and looking like each other is how that reads as one
                    // thing rather than three. Tinted by the FAB, so it keeps the colours
                    // the composed pair had.
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_services_glyph),
                        contentDescription = stringResource(R.string.settings_manager_title),
                    )
                }
            }
        }
    }

    if (showRevertDialog && managerAvailable) {
        SettingsManagerRoute(onDismissRequest = { showRevertDialog = false })
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

    // Which app the create-shortcut dialog is for, or null for closed. Held here rather
    // than navigated to, because the shortcut is made for the row that was held and the
    // list behind it is the context for that.
    var shortcutFor by remember { mutableStateOf<LauncherAppsActivityInfo?>(null) }

    // A tap always launches. What a long press does depends on the notification function,
    // because the two modes need different things behind it: with Revert to default the
    // settings to hide are device-wide and there is no per-app profile to edit, so the
    // useful thing is a shortcut; with the memory function the per-app profile is the only
    // thing that decides what a launch does, so that is what a long press has to reach.
    val perApp = userData.notificationFunction == NotificationFunction.Memory

    val onTap: (LauncherAppsActivityInfo) -> Unit = { info ->
        onLaunchApp(info.componentName)
    }

    val onLongPress: (LauncherAppsActivityInfo) -> Unit = { info ->
        if (perApp) {
            onModifyApp(info.componentName, info.activityLabel)
        } else {
            shortcutFor = info
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

    shortcutFor?.let { info ->
        ShortcutRoute(
            componentName = info.componentName,
            activityLabel = info.activityLabel,
            onDismissRequest = { shortcutFor = null },
        )
    }

    if (showOptionsDialog) {
        FavouriteAppsOptionsDialog(
            sortFavouriteApps = userData.sortFavouriteApps,
            favouriteAppsView = userData.favouriteAppsView,
            // One is enough now: with a remove button in there, the dialog is worth
            // opening for a single favourite you want rid of, where reordering alone
            // needed two.
            canReorder = favouriteAppsData.allFavouriteApps.isNotEmpty(),
            onDismissRequest = {
                showOptionsDialog = false
            },
            onUpdateSortFavouriteApps = onUpdateSortFavouriteApps,
            onUpdateFavouriteAppsView = onUpdateFavouriteAppsView,
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
