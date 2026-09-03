#!/usr/bin/env python3
"""
v3-r10 — the two app tabs: the blurred band, room for the floating bar, and the star on the
empty Favourites tab.

Three changes, one per instruction:

  * *"progressive blur ... at the bottom edge of the fav tab(excluding the two buttons) and all
    apps tab"* — the band goes on the **inner** Column of each tab, which is everything below the
    search field. The two floating buttons are drawn by the *outer* Box afterwards, so they sit
    over the band untouched. That is not a happy accident; it is why the band is attached here
    rather than to the outer Box.

  * The floating bar covers the bottom of the window now, so each scrolling list gains room at its
    end. ⚠ **Content padding, not layout padding** — the list must still scroll *under* the bar,
    because a band with nothing behind it to blur is just a rectangle.

  * *"on fav tab with no apps we display a fav icon on BG make it solid"*, *"and curvy"*. His pick
    from the ladder was **200 dp at 12%, behind the words** — one step short of the full watermark.

⚠ **The star is `GetoIcons.Star`, which is the rounded one as of r10.** Nothing here chooses a
shape: `design/_v3_rounded_star.py` decided that for the whole app, and this only stops asking for
the *outline* - the author's "make it solid".

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FAV = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"

# --- Favourites: imports ------------------------------------------------------------------

FAV_IMPORT_OLD = '''import androidx.compose.foundation.layout.Arrangement
'''

FAV_IMPORT_NEW = '''import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.PaddingValues
'''

FAV_IMPORT2_OLD = '''import androidx.compose.material3.MaterialTheme
'''

FAV_IMPORT2_NEW = '''import androidx.compose.material3.MaterialTheme
import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

# --- Favourites: the band --------------------------------------------------------------------

FAV_BAND_OLD = '''    Column(modifier = modifier.fillMaxSize()) {
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
'''

FAV_BAND_NEW = '''    Column(
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
'''

# --- Favourites: room at the end of both views ------------------------------------------------

FAV_LIST_OLD = '''                FavouriteAppsView.List -> {
                    LazyColumn(modifier = Modifier.fillMaxSize()) {
'''

FAV_LIST_NEW = '''                FavouriteAppsView.List -> {
                    LazyColumn(
                        modifier = Modifier.fillMaxSize(),
                        // ⚠ **Content padding, so the list still scrolls under the bar.** Layout
                        // padding would end the viewport above it, and then the band would have
                        // nothing behind it to blur.
                        contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
                    ) {
'''

FAV_GRID_OLD = '''                FavouriteAppsView.Grid -> {
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(96.dp),
                        modifier = Modifier.fillMaxSize(),
                    ) {
'''

FAV_GRID_NEW = '''                FavouriteAppsView.Grid -> {
                    LazyVerticalGrid(
                        columns = GridCells.Adaptive(96.dp),
                        modifier = Modifier.fillMaxSize(),
                        contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
                    ) {
'''

# --- Favourites: the empty tab ----------------------------------------------------------------

FAV_EMPTY_OLD = '''    Column(
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
'''

FAV_EMPTY_NEW = '''    Box(
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
'''

# --- All apps ---------------------------------------------------------------------------------

APPS_IMPORT_OLD = '''import androidx.compose.foundation.layout.Box
'''

APPS_IMPORT_NEW = '''import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
'''

APPS_IMPORT2_OLD = '''import androidx.compose.material3.MaterialTheme
'''

APPS_IMPORT2_NEW = '''import androidx.compose.material3.MaterialTheme
import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

APPS_BAND_OLD = '''    Column(modifier = modifier.fillMaxSize()) {
        AppsSearchField(
            query = query,
            onQueryChange = { query = it },
            trailingIcon = {
                IconButton(
                    onClick = {
                        showSortLauncherAppsActivityInfoDialog = true
                    },
                ) {
'''

APPS_BAND_NEW = '''    Column(
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
'''

APPS_GRID_OLD = '''        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier.fillMaxSize(),
        ) {
'''

APPS_GRID_NEW = '''        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier.fillMaxSize(),
            // Room for the floating bar at the end of the list, added as content padding so the
            // list still scrolls under it. See the same note on Favourites.
            contentPadding = PaddingValues(bottom = GetoNavBarReservedHeight),
        ) {
'''

EDITS = [
    (FAV, FAV_IMPORT_OLD, FAV_IMPORT_NEW),
    (FAV, FAV_IMPORT2_OLD, FAV_IMPORT2_NEW),
    (FAV, FAV_BAND_OLD, FAV_BAND_NEW),
    (FAV, FAV_LIST_OLD, FAV_LIST_NEW),
    (FAV, FAV_GRID_OLD, FAV_GRID_NEW),
    (FAV, FAV_EMPTY_OLD, FAV_EMPTY_NEW),
    (APPS, APPS_IMPORT_OLD, APPS_IMPORT_NEW),
    (APPS, APPS_IMPORT2_OLD, APPS_IMPORT2_NEW),
    (APPS, APPS_BAND_OLD, APPS_BAND_NEW),
    (APPS, APPS_GRID_OLD, APPS_GRID_NEW),
]

CHECKS = [
    (FAV, ".progressiveBottomBlur(", 1, "one band on Favourites"),
    (FAV, "GetoNavBarReservedHeight", 3, "imported, and room at the end of both views"),
    (FAV, "GetoIcons.StarBorder", 0, "the empty tab no longer asks for an outline"),
    (FAV, "EMPTY_STAR_SIZE", 2, "declared and used"),
    (FAV, "EMPTY_STAR_ALPHA", 2, "the same for the alpha"),
    (APPS, ".progressiveBottomBlur(", 1, "one band on All apps"),
    (APPS, "GetoNavBarReservedHeight", 2, "imported and used once"),
    # ⚠ The ★/☆ on each row is untouched: r10 changed the shape both of them draw, not which
    # of the two a row picks. A zero here would mean this script had eaten that logic.
    (APPS, "if (checked) GetoIcons.Star else GetoIcons.StarBorder", 1, "the row toggle is intact"),
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
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip().splitlines()[0][:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already carries the replacement")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:26s} {old.strip().splitlines()[0][:46]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:46]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:26s} x{got}  {token[:42]!r}")

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

    print(f"\n  ok  wrote {len(planned)} file(s) — two bands, three lists, one backdrop star")

    return 0


if __name__ == "__main__":
    sys.exit(main())
