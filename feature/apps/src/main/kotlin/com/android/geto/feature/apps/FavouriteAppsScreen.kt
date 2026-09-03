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
import androidx.compose.foundation.layout.PaddingValues
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
import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.FavouriteAppsData
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.feature.apps.dialog.FavouriteAppsOptionsDialog
import com.android.geto.feature.apps.dialog.AutoHideConflictDialog
import com.android.geto.feature.apps.dialog.OverlayFailureDialog
import com.android.geto.feature.apps.dialog.ReorderFavouriteAppsDialog
import com.android.geto.feature.apps.dialog.ShizukuStartingDialog
import com.android.geto.feature.appsettings.shortcut.ShortcutRoute
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.debounce
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlin.time.Duration.Companion.milliseconds
import com.android.geto.common.R as commonR

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

    FavouriteAppsScreen(
        modifier = modifier,
        favouriteAppsUiState = favouriteAppsUiState,
        onModifyApp = onClickApp,
        onLaunchApp = viewModel::launchApp,
        onSearch = viewModel::search,
        onUpdateSortFavouriteApps = viewModel::updateSortFavouriteApps,
        onUpdateFavouriteAppsView = viewModel::updateFavouriteAppsView,
        onUpdateFavouriteComponentNames = viewModel::updateFavouriteComponentNames,
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
) {
    // ⚠ **The two floating buttons left this screen in r12.** They are drawn by the home
    // scaffold now — see `AppsFloatingActions` — so that they appear over All apps as well and
    // do not travel with a tab change. Nothing about them was ever per-tab.
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

    var showOptionsDialog by rememberSaveable { mutableStateOf(false) }

    var showReorderDialog by rememberSaveable { mutableStateOf(false) }

    val userData = favouriteAppsData.userData

    LaunchedEffect(Unit) {
        snapshotFlow { query }.debounce(300.milliseconds)
            .distinctUntilChanged()
            .collect { onSearch(it) }
    }

    // Which app the create-shortcut dialog is for, or null for closed. Held here rather
    // than navigated to, because the shortcut is made for the row that was held and the
    // list behind it is the context for that.
    //
    // The component name and the label, which is all the dialog asks for, rather than the
    // LauncherAppsActivityInfo they came from. Saved, so a rotation with the dialog open does
    // not close it - and it is the pair rather than the whole object precisely so that it
    // *can* be: that object carries the app's rendered icon, a few hundred kilobytes of PNG
    // that would go into the saved-state bundle on every rotation to be thrown away unread.
    var shortcutFor by rememberSaveable { mutableStateOf<Pair<String, String>?>(null) }

    // A tap always launches. What a long press does depends on the notification function,
    // because the two modes need different things behind it: with Revert to default the
    // settings to hide are device-wide and there is no per-app profile to edit, so the
    // useful thing is a shortcut; with the memory function the per-app profile is the only
    // thing that decides what a launch does, so that is what a long press has to reach.
    val perApp = userData.hidingFramework == HidingFramework.PerApp

    val onTap: (LauncherAppsActivityInfo) -> Unit = { info ->
        onLaunchApp(info.componentName)
    }

    val onLongPress: (LauncherAppsActivityInfo) -> Unit = { info ->
        if (perApp) {
            onModifyApp(info.componentName, info.activityLabel)
        } else {
            shortcutFor = info.componentName to info.activityLabel
        }
    }

    // The room the page gives up at each end now that the header and the tab bar float over it.
    // Free to read here: LocalHeaderMetrics is static, so this is not a subscription to
    // anything — the numbers inside it are read in the blur's draw lambdas below.
    val headerMetrics = LocalHeaderMetrics.current

    val headerInset = getoFloatingHeaderInset()

    val barInset = getoFloatingBarInset()

    // ⚠ **A Box, not a Column, and the order inside it is the whole point.** The list is drawn
    // first and the search field after, so the field sits over the list rather than above it -
    // the author's "the header and search bar floating on top of it". The band is on the list
    // alone, which is what keeps the field, the two floating buttons and the title sharp.
    Box(modifier = modifier.fillMaxSize()) {
        val listPadding = PaddingValues(
            top = headerInset + GetoSearchFieldHeight,
            bottom = barInset,
        )

        // ⚠ **Only the list goes inside.** The search field below is a sibling drawn afterwards,
        // so it sits over the list and stays sharp — the author's "the header and search bar
        // floating on top of it".
        // ⚠ **Built once and applied to whichever list is showing — r13b.** The treatment
        // hangs off the scrolling node now rather than off a wrapper; there are two lists here
        // and an empty state, so the chain is named instead of repeated. The empty state gets
        // none: a centred star and one line of text have no edge to fade into.
        // ⚠ **The same anchor All apps uses — r15b**: full strength behind the search field
        // and fading out below it, and nothing along the bottom on any device.
        val edgeBlur = Modifier.progressiveEdgeBlur(
            blur = userData.progressiveBlur,
            topSolid = { headerMetrics.height + GetoSearchFieldHeight },
            strength = { headerMetrics.fraction },
        )

        Box(modifier = Modifier.matchParentSize()) {
            if (favouriteAppsData.launcherAppsActivityInfos.isEmpty()) {
                // Distinguishes "you have no favourites" from "your search matched none of
                // them", which are very different things to be told.
                EmptyFavourites(
                    modifier = Modifier.padding(listPadding),
                    searching = query.isNotEmpty(),
                )
            } else {
                when (userData.favouriteAppsView) {
                    FavouriteAppsView.List -> {
                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .then(edgeBlur),
                            // ⚠ **Content padding at both ends, so the list scrolls under both.**
                            // Layout padding would end the viewport at the header and the bar, and
                            // then neither band would have anything behind it to blur.
                            contentPadding = listPadding,
                        ) {
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
                            modifier = Modifier
                                .fillMaxSize()
                                .then(edgeBlur),
                            contentPadding = listPadding,
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

        // Last inside the Box and so on top of the list, pinned under the floating title.
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
    }

    shortcutFor?.let { (componentName, activityLabel) ->
        ShortcutRoute(
            componentName = componentName,
            activityLabel = activityLabel,
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
    Box(
        modifier = modifier.fillMaxSize(),
        contentAlignment = Alignment.Center,
    ) {
        // ⚠ **Behind the words rather than above them, solid rather than outlined, and dim** —
        // the author's "on fav tab with no apps we display a fav icon on BG make it solid", and
        // his pick of 200 dp at 12% from the r10 ladder. The words sit on top of it and stay the
        // thing being read; the star is the backdrop that says which tab this is.
        //
        // The shape is whatever GetoIcons.Star is, which since r10 is the rounded star - his
        // "curvy" and "less pointy". Nothing is decided here.
        Icon(
            modifier = Modifier.size(EMPTY_STAR_SIZE),
            imageVector = GetoIcons.Star,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.primary.copy(alpha = EMPTY_STAR_ALPHA),
        )

        Column(
            modifier = Modifier.padding(24.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
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
}

/** The author's pick from the r10 ladder: big enough to read as a backdrop, not as an icon. */
private val EMPTY_STAR_SIZE = 200.dp

/**
 * And how faint it is.
 *
 * ⚠ **Low on purpose, and it is `primary` rather than `onSurface`.** At 12% the app's green is
 * present without competing with the two lines of text drawn over it; a neutral ink at the same
 * alpha reads as a smudge on the page rather than as a star.
 */
private const val EMPTY_STAR_ALPHA = 0.12f

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
