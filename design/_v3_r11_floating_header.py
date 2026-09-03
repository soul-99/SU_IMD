#!/usr/bin/env python3
"""
v3-r11 — the header floats and the list runs under it.

The author: *"when i swipe down on any tab can the tab header float on top of blur also on top ...
in all apps the All apps header and search bar, instead of a background can we display swiped up
app list behind them with the header and search bar floating on top of it."* He picked **H2** from
the r11 template: the large title still collapses on scroll, exactly as it does now.

Three moves, and they only work together:

  * ⚠ **The top bar comes out of the scaffold's `topBar` slot and is drawn as an overlay.** The
    slot is a *layout* position - anything put there pushes the content down, which is the
    background the author is asking to remove. As a sibling drawn after the scaffold it covers the
    page instead of displacing it, exactly as the floating tab bar already does at the other end.

  * ⚠ **`contentWindowInsets = WindowInsets(0)`**, so the scaffold stops reserving the status bar
    as well. The top app bar applies that inset itself and the tab bar applies the navigation-bar
    one, so the insets are still honoured - by the two things that float, which is where they
    belong now.

  * The room the page has lost is given back as **content padding** inside each tab, so the list
    scrolls *under* the header rather than starting below it. `getoFloatingHeaderInset()` is the
    expanded height, deliberately: an inset that shrank with the collapsing bar would drag the list
    under the finger.

⚠ **The search field is a sibling of the list, not the first row of a column.** It has to be drawn
after the list to sit over it, and it has to be outside the list to stay put while the list moves.
The band that keeps it readable is on the list, so the field itself stays sharp.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

FAV = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"

SETTINGS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

# --- HomeScreen ---------------------------------------------------------------------------

HOME_IMPORT_OLD = '''import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
'''

HOME_IMPORT_NEW = '''import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
'''

HOME_IMPORT2_OLD = '''import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior
'''

HOME_IMPORT2_NEW = '''import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior
'''

HOME_IMPORT3_OLD = '''import androidx.compose.ui.input.pointer.pointerInput
'''

HOME_IMPORT3_NEW = '''import androidx.compose.ui.graphics.Color
import androidx.compose.ui.input.pointer.pointerInput
'''

HOME_BODY_OLD = '''    Box(modifier = Modifier.fillMaxSize()) {
        Scaffold(
            // ⚠ **The rail floats over the window, so the page is indented to make room.**
            // GetoNavRailReservedWidth is the rail's own cap, exported for exactly this: the
            // two numbers have to agree and there is only one of them.
            modifier = if (sideRail) {
                Modifier.padding(start = GetoNavRailReservedWidth)
            } else {
                Modifier
            },
            topBar = {
                LargeTopAppBar(
                    title = {
                        Text(
                            text = stringResource(id = topBarTitleStringResource),
                        )
                    },
                    scrollBehavior = topAppBarScrollBehavior,
                )
            },
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
'''

HOME_BODY_NEW = '''    Box(modifier = Modifier.fillMaxSize()) {
        // The page, indented on a tablet so the rail has somewhere to float. ⚠ **The rail floats
        // over the window rather than displacing it**, so this indent and
        // GetoNavRailReservedWidth are two numbers that have to agree - which is why there is
        // only one of them.
        Box(
            modifier = if (sideRail) {
                Modifier
                    .fillMaxSize()
                    .padding(start = GetoNavRailReservedWidth)
            } else {
                Modifier.fillMaxSize()
            },
        ) {
        Scaffold(
            // ⚠ **No topBar slot, and no window insets — r11.** Both of those are *layout*: the
            // slot pushes the content down and the insets pad it in, and between them they are
            // the background the author asked to remove from behind the title. The bar is drawn
            // below as an overlay instead, and it applies the status-bar inset itself; the tab
            // bar applies the navigation-bar one. Nothing is lost except the displacement.
            contentWindowInsets = WindowInsets(0, 0, 0, 0),
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
'''

HOME_TAIL_OLD = '''                builder = builder,
            )
        }

        // Drawn after the scaffold and so over it, which is what makes it float. On a phone that
        // is the whole reason the blurred band beneath it has anything to blur.
'''

HOME_TAIL_NEW = '''                builder = builder,
            )
        }

        // ⚠ **Transparent, and drawn over the page rather than above it.** The list runs
        // underneath, which is the author's "display swiped up app list behind them"; what keeps
        // the title readable is the blurred band each tab draws at its own top edge, not a
        // container colour here. It still collapses on scroll - his H2 - because it is the same
        // LargeTopAppBar on the same scroll behaviour it always had.
        LargeTopAppBar(
            modifier = Modifier.align(Alignment.TopCenter),
            title = {
                Text(
                    text = stringResource(id = topBarTitleStringResource),
                )
            },
            scrollBehavior = topAppBarScrollBehavior,
            colors = TopAppBarDefaults.largeTopAppBarColors(
                containerColor = Color.Transparent,
                scrolledContainerColor = Color.Transparent,
            ),
        )
        }

        // Drawn after the scaffold and so over it, which is what makes it float. On a phone that
        // is the whole reason the blurred band beneath it has anything to blur.
'''

# --- Favourites ---------------------------------------------------------------------------

FAV_IMPORT_OLD = '''import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

FAV_IMPORT_NEW = '''import com.android.geto.designsystem.component.GetoSearchFieldHeight
import com.android.geto.designsystem.component.ProgressiveBlurDefaults
import com.android.geto.designsystem.component.getoFloatingBarInset
import com.android.geto.designsystem.component.getoFloatingHeaderInset
import com.android.geto.designsystem.component.progressiveBlur
'''

FAV_BODY_OLD = '''    Column(
        modifier = modifier
            .fillMaxSize()
            // ⚠ **Here rather than on the Box above, and that is what keeps the buttons sharp.**
            // This Column is the search field and the list; the two floating buttons are siblings
            // of it in the outer Box and are drawn after it, so the band passes under them - the
            // author's "excluding the two buttons".
            .progressiveBottomBlur(enabled = userData.progressiveBlur),
    ) {
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
'''

FAV_BODY_NEW = '''    // The room the page gives up at each end now that the header and the tab bar float over it.
    val headerInset = getoFloatingHeaderInset()

    val barInset = getoFloatingBarInset()

    // ⚠ **A Box, not a Column, and the order inside it is the whole point.** The list is drawn
    // first and the search field after, so the field sits over the list rather than above it -
    // the author's "the header and search bar floating on top of it". The band is on the list
    // alone, which is what keeps the field, the two floating buttons and the title sharp.
    Box(
        modifier = modifier
            .fillMaxSize()
            .progressiveBlur(
                enabled = userData.progressiveBlur,
                topHeight = ProgressiveBlurDefaults.HeaderHeight,
                bottomHeight = ProgressiveBlurDefaults.Height,
            ),
    ) {
        val listPadding = PaddingValues(
            top = headerInset + GetoSearchFieldHeight,
            bottom = barInset,
        )

        if (favouriteAppsData.launcherAppsActivityInfos.isEmpty()) {
'''

FAV_EMPTY_OLD = '''            EmptyFavourites(searching = query.isNotEmpty())
'''

FAV_EMPTY_NEW = '''            EmptyFavourites(
                modifier = Modifier.padding(listPadding),
                searching = query.isNotEmpty(),
            )
'''

FAV_LIST_OLD = '''                FavouriteAppsView.List -> {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        // ⚠ **Content padding, so the list still scrolls under the bar.** Layout
                        // padding would end the viewport above it, and then the band would have
                        // nothing behind it to blur.
                        contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
                    ) {
'''

FAV_LIST_NEW = '''                FavouriteAppsView.List -> {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        // ⚠ **Content padding at both ends, so the list scrolls under both.**
                        // Layout padding would end the viewport at the header and the bar, and
                        // then neither band would have anything behind it to blur.
                        contentPadding = listPadding,
                    ) {
'''

FAV_GRID_OLD = '''                        columns = GridCells.Adaptive(96.dp),
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
                    ) {
'''

FAV_GRID_NEW = '''                        columns = GridCells.Adaptive(96.dp),
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = listPadding,
                    ) {
'''

FAV_CLOSE_OLD = '''                }
            }
        }
    }

    shortcutFor?.let { (componentName, activityLabel) ->
'''

FAV_CLOSE_NEW = '''                }
            }
        }

        // Last inside the Box and so on top of the list, pinned under the floating title.
        AppsSearchField(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = headerInset),
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
'''

# --- All apps -------------------------------------------------------------------------------

APPS_IMPORT_OLD = '''import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

APPS_IMPORT_NEW = '''import com.android.geto.designsystem.component.GetoSearchFieldHeight
import com.android.geto.designsystem.component.ProgressiveBlurDefaults
import com.android.geto.designsystem.component.getoFloatingBarInset
import com.android.geto.designsystem.component.getoFloatingHeaderInset
import com.android.geto.designsystem.component.progressiveBlur
'''

APPS_BODY_OLD = '''    Column(
        modifier = modifier
            .fillMaxSize()
            .progressiveBottomBlur(
                enabled = launcherAppsActivityInfoData.userData.progressiveBlur,
            ),
    ) {
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
            // Room for the floating bar at the end of the list, added as content padding so the
            // list still scrolls under it. See the same note on Favourites.
            contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
        ) {
'''

APPS_BODY_NEW = '''    val headerInset = getoFloatingHeaderInset()

    val barInset = getoFloatingBarInset()

    // A Box rather than a Column, and the search field drawn last: see the same note on
    // Favourites. The list runs under both the header and the tab bar.
    Box(
        modifier = modifier
            .fillMaxSize()
            .progressiveBlur(
                enabled = launcherAppsActivityInfoData.userData.progressiveBlur,
                topHeight = ProgressiveBlurDefaults.HeaderHeight,
                bottomHeight = ProgressiveBlurDefaults.Height,
            ),
    ) {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier.fillMaxSize(),
            contentPadding = PaddingValues(
                top = headerInset + GetoSearchFieldHeight,
                bottom = barInset,
            ),
        ) {
'''

APPS_CLOSE_OLD = '''                    onUpdateFavourite = onUpdateFavourite,
                )
            }
        }
    }

    if (showSortLauncherAppsActivityInfoDialog) {
'''

APPS_CLOSE_NEW = '''                    onUpdateFavourite = onUpdateFavourite,
                )
            }
        }

        AppsSearchField(
            modifier = Modifier
                .align(Alignment.TopCenter)
                .padding(top = headerInset),
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
'''

# --- Settings -------------------------------------------------------------------------------

SET_IMPORT_OLD = '''import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.ProgressiveBlurDefaults
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

SET_IMPORT_NEW = '''import com.android.geto.designsystem.component.ProgressiveBlurDefaults
import com.android.geto.designsystem.component.getoFloatingBarInset
import com.android.geto.designsystem.component.getoFloatingHeaderInset
import com.android.geto.designsystem.component.progressiveBlur
'''

SET_BODY_OLD = '''            .progressiveBottomBlur(
                enabled = userData.progressiveBlur,
                height = ProgressiveBlurDefaults.SettingsHeight,
            )
            .verticalScroll(rememberScrollState())
            // Room at the end for the floating bar to rest over nothing. The bar is drawn over
            // this page rather than beside it, which is what gives the band something to blur.
            .padding(bottom = GetoNavBarReservedHeight),
'''

SET_BODY_NEW = '''            .progressiveBlur(
                enabled = userData.progressiveBlur,
                topHeight = ProgressiveBlurDefaults.HeaderHeight,
                bottomHeight = ProgressiveBlurDefaults.SettingsHeight,
            )
            .verticalScroll(rememberScrollState())
            // Room at both ends for the header and the bar to rest over nothing. Both are drawn
            // over this page rather than beside it, which is what gives the bands something to
            // blur. This tab has no search field, so its top inset is the header alone.
            .padding(top = getoFloatingHeaderInset(), bottom = getoFloatingBarInset()),
'''

EDITS = [
    (HOME, HOME_IMPORT_OLD, HOME_IMPORT_NEW),
    (HOME, HOME_IMPORT2_OLD, HOME_IMPORT2_NEW),
    (HOME, HOME_IMPORT3_OLD, HOME_IMPORT3_NEW),
    (HOME, HOME_BODY_OLD, HOME_BODY_NEW),
    (HOME, HOME_TAIL_OLD, HOME_TAIL_NEW),
    (FAV, FAV_IMPORT_OLD, FAV_IMPORT_NEW),
    (FAV, FAV_BODY_OLD, FAV_BODY_NEW),
    (FAV, FAV_EMPTY_OLD, FAV_EMPTY_NEW),
    (FAV, FAV_LIST_OLD, FAV_LIST_NEW),
    (FAV, FAV_GRID_OLD, FAV_GRID_NEW),
    (FAV, FAV_CLOSE_OLD, FAV_CLOSE_NEW),
    (APPS, APPS_IMPORT_OLD, APPS_IMPORT_NEW),
    (APPS, APPS_BODY_OLD, APPS_BODY_NEW),
    (APPS, APPS_CLOSE_OLD, APPS_CLOSE_NEW),
    (SETTINGS, SET_IMPORT_OLD, SET_IMPORT_NEW),
    (SETTINGS, SET_BODY_OLD, SET_BODY_NEW),
]

CHECKS = [
    (HOME, "topBar = {", 0, "nothing is left in the scaffold's top-bar slot"),
    (HOME, "LargeTopAppBar(", 1, "one top bar, drawn as an overlay"),
    (HOME, "contentWindowInsets = WindowInsets(0, 0, 0, 0)", 1, "the scaffold reserves nothing"),
    (HOME, "containerColor = Color.Transparent", 1, "and the bar paints nothing"),
    (FAV, "AppsSearchField(", 1, "one search field on Favourites"),
    (FAV, ".progressiveBlur(", 1, "one band pair"),
    (FAV, "progressiveBottomBlur", 0, "the r10 spelling is gone"),
    (FAV, "GetoNavBarReservedHeight", 0, "replaced by the inset helper"),
    (FAV, "getoFloatingHeaderInset()", 1, "called once; the import has no parentheses"),
    (APPS, "AppsSearchField(", 1, "one search field on All apps"),
    (APPS, ".progressiveBlur(", 1, "one band pair"),
    (APPS, "progressiveBottomBlur", 0, "the r10 spelling is gone"),
    (SETTINGS, ".progressiveBlur(", 1, "one band pair on Settings"),
    (SETTINGS, "progressiveBottomBlur", 0, "the r10 spelling is gone"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip().splitlines()[0][:70]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:24s} {old.strip().splitlines()[0][:46]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:44]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:24s} x{got}  {token[:40]!r}")

    for path, text in planned.items():
        if text.count("{") != text.count("}"):
            print(
                f"REFUSED: {path.name} braces do not balance — "
                f"{text.count('{')} open, {text.count('}')} close",
            )
            return 1

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, text in planned.items():
        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s) — the header floats on all three tabs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
