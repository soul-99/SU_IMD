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
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.feature.appsettings.shortcut.ShortcutRoute
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.LauncherAppsActivityInfoData
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.feature.apps.dialog.SortLauncherAppsActivityInfoDialog
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlin.time.Duration.Companion.milliseconds

@Composable
internal fun AppsRoute(
    modifier: Modifier = Modifier,
    viewModel: AppsViewModel = hiltViewModel(),
    snackbarHostState: SnackbarHostState,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
) {
    val appListUiState by viewModel.appsUiState.collectAsStateWithLifecycle()

    val appLaunch by viewModel.appLaunch.collectAsStateWithLifecycle()

    val notificationFunction by viewModel.notificationFunction.collectAsStateWithLifecycle()

    var notConfigured by rememberSaveable { mutableStateOf(false) }

    var shortcutFor by remember { mutableStateOf<LauncherAppsActivityInfo?>(null) }

    ApplyThenLaunchEffect(
        appLaunch = appLaunch,
        snackbarHostState = snackbarHostState,
        onNotConfigured = { notConfigured = true },
        onConsumed = viewModel::consumeAppLaunch,
    )

    if (notConfigured) {
        NotConfiguredDialog(onDismissRequest = { notConfigured = false })
    }

    shortcutFor?.let { info ->
        ShortcutRoute(
            componentName = info.componentName,
            activityLabel = info.activityLabel,
            onDismissRequest = { shortcutFor = null },
        )
    }

    AppsScreen(
        modifier = modifier,
        appsUiState = appListUiState,
        // A tap always launches. The long press reaches whichever thing decides what that
        // launch does: the app's own profile under the memory function, and otherwise a
        // shortcut, since there is no per-app profile to edit.
        onClickApp = { componentName, _ -> viewModel.launchApp(componentName) },
        onLongPressApp = { info ->
            if (notificationFunction == NotificationFunction.Memory) {
                onClickApp(info.componentName, info.activityLabel)
            } else {
                shortcutFor = info
            }
        },
        onSearch = viewModel::search,
        onUpdateSortLauncherAppsActivityInfo = viewModel::updateSortLauncherAppsActivityInfo,
        onUpdateSortOrderLauncherAppsActivityInfo = viewModel::updateSortOrderLauncherAppsActivityInfo,
        onUpdateShowSystem = viewModel::updateShowSystem,
        onUpdateFavourite = viewModel::updateFavourite,
    )
}

@VisibleForTesting
@Composable
internal fun AppsScreen(
    modifier: Modifier = Modifier,
    appsUiState: AppsUiState,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLongPressApp: (LauncherAppsActivityInfo) -> Unit,
    onSearch: (String) -> Unit,
    onUpdateSortLauncherAppsActivityInfo: (SortLauncherAppsActivityInfo) -> Unit,
    onUpdateSortOrderLauncherAppsActivityInfo: (SortOrderLauncherAppsActivityInfo) -> Unit,
    onUpdateShowSystem: (Boolean) -> Unit,
    onUpdateFavourite: (componentName: String, favourite: Boolean) -> Unit,
) {
    Box(modifier = modifier.fillMaxSize()) {
        when (appsUiState) {
            AppsUiState.Loading -> {
                CircularProgressIndicator(modifier = Modifier.align(Alignment.Center))
            }

            is AppsUiState.Success -> {
                Success(
                    launcherAppsActivityInfoData = appsUiState.launcherAppsActivityInfoData,
                    onClickApp = onClickApp,
                    onLongPressApp = onLongPressApp,
                    onSearch = onSearch,
                    onUpdateSortLauncherAppsActivityInfo = onUpdateSortLauncherAppsActivityInfo,
                    onUpdateSortOrderLauncherAppsActivityInfo = onUpdateSortOrderLauncherAppsActivityInfo,
                    onUpdateShowSystem = onUpdateShowSystem,
                    onUpdateFavourite = onUpdateFavourite,
                )
            }
        }
    }
}

@OptIn(FlowPreview::class)
@Composable
private fun Success(
    modifier: Modifier = Modifier,
    launcherAppsActivityInfoData: LauncherAppsActivityInfoData,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLongPressApp: (LauncherAppsActivityInfo) -> Unit,
    onSearch: (String) -> Unit,
    onUpdateSortLauncherAppsActivityInfo: (SortLauncherAppsActivityInfo) -> Unit,
    onUpdateSortOrderLauncherAppsActivityInfo: (SortOrderLauncherAppsActivityInfo) -> Unit,
    onUpdateShowSystem: (Boolean) -> Unit,
    onUpdateFavourite: (componentName: String, favourite: Boolean) -> Unit,
) {
    var query by rememberSaveable { mutableStateOf("") }

    var showSortLauncherAppsActivityInfoDialog by remember { mutableStateOf(false) }

    val favourites = remember(launcherAppsActivityInfoData.userData.favouriteComponentNames) {
        launcherAppsActivityInfoData.userData.favouriteComponentNames.toSet()
    }

    LaunchedEffect(Unit) {
        snapshotFlow { query }.debounce(300.milliseconds)
            .distinctUntilChanged()
            .collect { onSearch(it) }
    }

    Column(modifier = modifier.fillMaxSize()) {
        AppsSearchField(
            query = query,
            onQueryChange = { query = it },
            trailingIcon = {
                IconButton(
                    onClick = {
                        showSortLauncherAppsActivityInfoDialog = true
                    },
                ) {
                    Icon(
                        imageVector = GetoIcons.Sort,
                        contentDescription = stringResource(R.string.sort),
                    )
                }
            },
        )

        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier.fillMaxSize(),
        ) {
            items(
                items = launcherAppsActivityInfoData.launcherAppsActivityInfos,
                key = { it.componentName },
            ) { launcherAppsActivityInfo ->
                AppItem(
                    launcherAppsActivityInfo = launcherAppsActivityInfo,
                    favourite = launcherAppsActivityInfo.componentName in favourites,
                    onClickApp = onClickApp,
                    onLongPressApp = onLongPressApp,
                    onUpdateFavourite = onUpdateFavourite,
                )
            }
        }
    }

    if (showSortLauncherAppsActivityInfoDialog) {
        SortLauncherAppsActivityInfoDialog(
            sortLauncherAppsActivityInfo = launcherAppsActivityInfoData.userData.sortLauncherAppsActivityInfo,
            sortOrderLauncherAppsActivityInfo = launcherAppsActivityInfoData.userData.sortOrderLauncherAppsActivityInfo,
            showSystem = launcherAppsActivityInfoData.userData.showSystem,
            onDismissRequest = {
                showSortLauncherAppsActivityInfoDialog = false
            },
            onUpdateSortLauncherAppsActivityInfo = onUpdateSortLauncherAppsActivityInfo,
            onUpdateSortOrderLauncherAppsActivityInfo = onUpdateSortOrderLauncherAppsActivityInfo,
            onUpdateShowSystem = onUpdateShowSystem,
        )
    }
}

@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun AppItem(
    modifier: Modifier = Modifier,
    launcherAppsActivityInfo: LauncherAppsActivityInfo,
    favourite: Boolean,
    onClickApp: (
        componentName: String,
        activityLabel: String,
    ) -> Unit,
    onLongPressApp: (LauncherAppsActivityInfo) -> Unit,
    onUpdateFavourite: (componentName: String, favourite: Boolean) -> Unit,
) {
    ListItem(
        modifier = modifier
            .combinedClickable(
                onClick = {
                    onClickApp(
                        launcherAppsActivityInfo.componentName,
                        launcherAppsActivityInfo.activityLabel,
                    )
                },
                onLongClick = { onLongPressApp(launcherAppsActivityInfo) },
            ),
        headlineContent = {
            Text(
                text = launcherAppsActivityInfo.activityLabel,
            )
        },
        supportingContent = {
            Text(
                text = launcherAppsActivityInfo.packageName,
            )
        },
        leadingContent = {
            AppIcon(launcherAppsActivityInfo = launcherAppsActivityInfo, size = 50.dp)
        },
        trailingContent = {
            FavouriteIconButton(
                favourite = favourite,
                onClick = {
                    onUpdateFavourite(launcherAppsActivityInfo.componentName, !favourite)
                },
            )
        },
    )
}

/**
 * Star toggle that flips the moment it is tapped rather than waiting for the write.
 *
 * Persisting a favourite is a DataStore round trip — serialise, write, fsync, re-emit —
 * and driving the icon straight from the persisted value made every tap feel like it had
 * been missed. The local state is keyed on [favourite], so once the write lands the
 * persisted value takes over again and any failed write corrects itself.
 */
@Composable
internal fun FavouriteIconButton(
    modifier: Modifier = Modifier,
    favourite: Boolean,
    onClick: () -> Unit,
) {
    var checked by remember(favourite) { mutableStateOf(favourite) }

    IconButton(
        modifier = modifier,
        onClick = {
            checked = !checked

            onClick()
        },
    ) {
        Icon(
            imageVector = if (checked) GetoIcons.Star else GetoIcons.StarBorder,
            contentDescription = if (checked) {
                stringResource(R.string.remove_from_favourites)
            } else {
                stringResource(R.string.add_to_favourites)
            },
            tint = if (checked) {
                MaterialTheme.colorScheme.primary
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        )
    }
}
