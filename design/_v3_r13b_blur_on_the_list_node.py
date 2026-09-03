#!/usr/bin/env python3
"""
r13b — the edge treatment moves from a wrapper `Box` back onto the scrolling node itself.

⚠ **The one variable never changed across four failed rounds.** r10 hung this on the list and its
tint reached the author's screen; r11 turned it into a wrapper `Box` and nothing has reached his
screen since, through three completely different drawing mechanisms — nested layer (r10), sibling
overlays (r12), one node walked twice (r12b) — and with the switch now confirmed **on**, which was
the last remaining explanation that did not involve the drawing at all. Replacing the mechanism a
fourth time would be repeating the experiment; putting the node back is the experiment that has
not been run.

⚠ **The wrapper `Box` stays as a plain `Box`, and the indentation with it.** Layout is unchanged —
same node, same `matchParentSize`, same everything — so this is an honest A/B: the only difference
between this build and r12b is which node carries the draw. It also avoids re-indenting a
four-hundred-line settings column, which an earlier attempt at exactly that got wrong.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

APPS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"

FAVS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


IMPORT_OLD = "import com.android.geto.designsystem.component.ProgressiveEdgeBlur\n"

IMPORT_NEW = "import com.android.geto.designsystem.component.progressiveEdgeBlur\n"

# ------------------------------------------------------------ 0. the modifier exists

blur = BLUR.read_text(encoding="utf-8")

check("fun Modifier.progressiveEdgeBlur(" in blur, "ProgressiveBlur.kt is still a wrapper")

check(
    "\nfun ProgressiveEdgeBlur(" not in blur,
    "the wrapper composable is still declared",
)

# ------------------------------------------------------------ 1. All apps

apps = APPS.read_text(encoding="utf-8")

apps = swap(apps, IMPORT_OLD, IMPORT_NEW, "AppsScreen: import")

apps = swap(
    apps,
    """        ProgressiveEdgeBlur(
            blur = launcherAppsActivityInfoData.userData.progressiveBlur,
            modifier = Modifier.matchParentSize(),
            topHeight = ProgressiveBlurDefaults.HeaderHeight,
            bottomHeight = ProgressiveBlurDefaults.Height,
        ) {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier.fillMaxSize(),""",
    """        // ⚠ **A plain Box now, and the treatment is on the grid — r13b.** The layout is
        // identical to r12b's; the only thing that moved is which node draws the bands. See
        // ProgressiveBlur.kt for why that is the change worth making.
        Box(modifier = Modifier.matchParentSize()) {
        LazyVerticalGrid(
            columns = GridCells.Adaptive(300.dp),
            modifier = Modifier
                .fillMaxSize()
                .progressiveEdgeBlur(
                    blur = launcherAppsActivityInfoData.userData.progressiveBlur,
                    topHeight = ProgressiveBlurDefaults.HeaderHeight,
                    bottomHeight = ProgressiveBlurDefaults.Height,
                ),""",
    "AppsScreen: grid",
)

pending.append((APPS, apps))

# ------------------------------------------------------------ 2. Favourites

favs = FAVS.read_text(encoding="utf-8")

favs = swap(favs, IMPORT_OLD, IMPORT_NEW, "FavouriteAppsScreen: import")

favs = swap(
    favs,
    """        ProgressiveEdgeBlur(
            blur = userData.progressiveBlur,
            modifier = Modifier.matchParentSize(),
            topHeight = ProgressiveBlurDefaults.HeaderHeight,
            bottomHeight = ProgressiveBlurDefaults.Height,
        ) {""",
    """        // ⚠ **Built once and applied to whichever list is showing — r13b.** The treatment
        // hangs off the scrolling node now rather than off a wrapper; there are two lists here
        // and an empty state, so the chain is named instead of repeated. The empty state gets
        // none: a centred star and one line of text have no edge to fade into.
        val edgeBlur = Modifier.progressiveEdgeBlur(
            blur = userData.progressiveBlur,
            topHeight = ProgressiveBlurDefaults.HeaderHeight,
            bottomHeight = ProgressiveBlurDefaults.Height,
        )

        Box(modifier = Modifier.matchParentSize()) {""",
    "FavouriteAppsScreen: wrapper",
)

favs = swap(
    favs,
    """                        LazyColumn(
                            modifier = Modifier.fillMaxSize(),""",
    """                        LazyColumn(
                            modifier = Modifier
                                .fillMaxSize()
                                .then(edgeBlur),""",
    "FavouriteAppsScreen: list view",
)

favs = swap(
    favs,
    """                        LazyVerticalGrid(
                            columns = GridCells.Adaptive(96.dp),
                            modifier = Modifier.fillMaxSize(),""",
    """                        LazyVerticalGrid(
                            columns = GridCells.Adaptive(96.dp),
                            modifier = Modifier
                                .fillMaxSize()
                                .then(edgeBlur),""",
    "FavouriteAppsScreen: grid view",
)

pending.append((FAVS, favs))

# ------------------------------------------------------------ 3. Settings

settings = SETTINGS.read_text(encoding="utf-8")

settings = swap(settings, IMPORT_OLD, IMPORT_NEW, "SettingsScreen: import")

settings = swap(
    settings,
    """    ProgressiveEdgeBlur(
        blur = userData.progressiveBlur,
        modifier = Modifier.fillMaxSize(),
        topHeight = ProgressiveBlurDefaults.HeaderHeight,
        bottomHeight = ProgressiveBlurDefaults.SettingsHeight,
    ) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())""",
    """    Box(modifier = Modifier.fillMaxSize()) {
    Column(
        modifier = modifier
            .fillMaxSize()
            // ⚠ **Before `verticalScroll`, which puts it outside the scrolling.** After it, the
            // bands would be part of the scrolled content and would travel up the page with it
            // instead of staying at the viewport's two edges.
            .progressiveEdgeBlur(
                blur = userData.progressiveBlur,
                topHeight = ProgressiveBlurDefaults.HeaderHeight,
                bottomHeight = ProgressiveBlurDefaults.SettingsHeight,
            )
            .verticalScroll(rememberScrollState())""",
    "SettingsScreen: column",
)

pending.append((SETTINGS, settings))

# ------------------------------------------------------------ commit

for path, text in pending:
    check(
        "ProgressiveEdgeBlur" not in text,
        f"{path.name}: a reference to the old wrapper survived",
    )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
