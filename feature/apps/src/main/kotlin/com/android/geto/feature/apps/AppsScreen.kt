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
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import com.android.geto.designsystem.component.GetoSearchFieldHeight
import com.android.geto.designsystem.component.LocalFloatingHeaderHeight
import com.android.geto.designsystem.component.LocalHeaderMetrics
import com.android.geto.designsystem.component.getoFloatingBarInset
import com.android.geto.designsystem.component.getoFloatingHeaderInset
import com.android.geto.designsystem.component.progressiveEdgeBlur
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
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.LauncherAppsActivityInfoData
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.feature.apps.dialog.AutoHideConflictDialog
import com.android.geto.feature.apps.dialog.OverlayFailureDialog
import com.android.geto.feature.apps.dialog.ShizukuStartingDialog
import com.android.geto.feature.apps.dialog.SortLauncherAppsActivityInfoDialog
import com.android.geto.feature.appsettings.shortcut.ShortcutRoute
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.common.R as commonR

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

    val hidingFramework by viewModel.hidingFramework.collectAsStateWithLifecycle()

    var notConfigured by rememberSaveable { mutableStateOf(false) }

    var nothingToHide by rememberSaveable { mutableStateOf(false) }

    var overlayFailure by rememberSaveable { mutableStateOf(false) }

    // The WRITE_SECURE_SETTINGS grant has gone, so nothing this app writes can land.
    // Saved like the others: it is the only explanation the user is given, and losing it
    // to a rotation would leave a launch that simply did nothing.
    var permissionsLost by rememberSaveable { mutableStateOf(false) }

    // Auto-hide settings (IMD+) is holding the device down with a list this app's
    // profile does not fit inside. Saved like the two above, so rotating the device
    // while it is up does not lose the only explanation the user was given.
    var autoHideConflict by rememberSaveable { mutableStateOf(false) }

    // Which app was being launched when IMD noticed that the settings already down belong to a
    // run of itself that is no longer alive. The component name rather than a flag, because
    // both answers end in launching that same app. Saved for the same reason as the rest.
    var priorHide by rememberSaveable { mutableStateOf<String?>(null) }

    // Survives the launch that raised it: the wait runs in a NonCancellable scope
    // that outlives this composition, and the spinner has to still be there when it
    // returns.
    val overlayStart by viewModel.overlayStart
        .collectAsStateWithLifecycle(initialValue = null)

    // Which app the create-shortcut dialog is for, as the two strings that dialog actually
    // asks for, rather than as the LauncherAppsActivityInfo they came from. Saved, so a
    // rotation with the dialog open does not close it - and it is the pair rather than the
    // whole object precisely so that it *can* be: that object carries the app's rendered icon,
    // a few hundred kilobytes of PNG that would go into the saved-state bundle on every
    // rotation to be thrown away unread.
    var shortcutFor by rememberSaveable { mutableStateOf<Pair<String, String>?>(null) }

    ApplyThenLaunchEffect(
        appLaunch = appLaunch,
        snackbarHostState = snackbarHostState,
        onNotConfigured = { notConfigured = true },
        onNothingToHide = { nothingToHide = true },
        onOverlayFailure = { overlayFailure = true },
        onAutoHideConflict = { autoHideConflict = true },
        onPermissionsLost = { permissionsLost = true },
        onPriorHide = { priorHide = it },
        onConsumed = viewModel::consumeAppLaunch,
    )

    if (notConfigured) {
        NotConfiguredDialog(onDismissRequest = { notConfigured = false })
    }

    if (nothingToHide) {
        NothingToHideDialog(onDismissRequest = { nothingToHide = false })
    }

    overlayStart?.let { ShizukuStartingDialog(reason = it) }

    if (autoHideConflict) {
        AutoHideConflictDialog(onDismissRequest = { autoHideConflict = false })
    }

    if (overlayFailure) {
        OverlayFailureDialog(onDismissRequest = { overlayFailure = false })
    }

    if (permissionsLost) {
        PermissionsLostDialog(onDismissRequest = { permissionsLost = false })
    }

    // Cleared before either call, so the Shizuku spinner underneath is visible for the wait
    // rather than hidden behind a dialog nobody can answer any more.
    priorHide?.let { componentName ->
        PriorHideDialog(
            title = stringResource(commonR.string.prior_hide_title),
            restoreLabel = stringResource(commonR.string.prior_hide_restore),
            ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
            onRestore = {
                priorHide = null

                viewModel.restoreThenLaunch(componentName = componentName)
            },
            onIgnore = {
                priorHide = null

                viewModel.discardThenLaunch(componentName = componentName)
            },
        )
    }

    shortcutFor?.let { (componentName, activityLabel) ->
        ShortcutRoute(
            componentName = componentName,
            activityLabel = activityLabel,
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
            if (hidingFramework == HidingFramework.PerApp) {
                onClickApp(info.componentName, info.activityLabel)
            } else {
                shortcutFor = info.componentName to info.activityLabel
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

    var showSortLauncherAppsActivityInfoDialog by rememberSaveable { mutableStateOf(false) }

    val favourites = remember(launcherAppsActivityInfoData.userData.favouriteComponentNames) {
        launcherAppsActivityInfoData.userData.favouriteComponentNames.toSet()
    }

    LaunchedEffect(Unit) {
        snapshotFlow { query }.debounce(300.milliseconds)
            .distinctUntilChanged()
            .collect { onSearch(it) }
    }

    // Free to read here: LocalHeaderMetrics is static, so this is not a subscription to
    // anything — the numbers inside it are read in the blur's draw lambdas below.
    val headerMetrics = LocalHeaderMetrics.current

    val headerInset = getoFloatingHeaderInset()

    val barInset = getoFloatingBarInset()

    // A Box rather than a Column, and the search field drawn last: see the same note on
    // Favourites. The list runs under both the header and the tab bar.
    Box(modifier = modifier.fillMaxSize()) {
        // Only the grid goes inside; the search field below is a sibling drawn afterwards, so it
        // sits over the grid and stays sharp. Same shape as Favourites.
        // ⚠ **A plain Box now, and the treatment is on the grid — r13b.** The layout is
        // identical to r12b's; the only thing that moved is which node draws the bands. See
        // ProgressiveBlur.kt for why that is the change worth making.
        Box(modifier = Modifier.matchParentSize()) {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier
                .fillMaxSize()
                // ⚠ **Anchored on the two floating things, not on fixed heights — r15.** The
                // top stays at full strength down to the bottom of the search field and starts
                // fading there; because the field rides on the collapsing header, so does this.
                // ⚠ **No bottom band at all — r15b.** The tab bar is a small floating pill with
                // page either side of it, so a strip across the full width read as a smear under
                // it rather than as an edge. The header and the field do span the window, which
                // is why the top one stays.
                .progressiveEdgeBlur(
                    blur = launcherAppsActivityInfoData.userData.progressiveBlur,
                    topSolid = { headerMetrics.height + GetoSearchFieldHeight },
                    strength = { headerMetrics.fraction },
                ),
            contentPadding = PaddingValues(
                top = headerInset + GetoSearchFieldHeight,
                bottom = barInset,
            ),
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

        // ⚠ **The *current* header height, not the expanded one.** r11 pinned the field at the
        // expanded height, so when the title collapsed the field stayed where it was and left the
        // gap the author reported. The list's content padding still uses the expanded height —
        // an inset that moved would drag the list under the finger — but the field is drawn, not
        // laid out, so it can and must follow the title.
        AppsSearchField(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = LocalFloatingHeaderHeight.current),
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
