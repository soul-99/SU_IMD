#!/usr/bin/env python3
"""
r15 — each band now begins where that tab's chrome ends, and a tablet gets no bottom band.

The modifier stopped taking a band *height* and started taking the solid part: how far the full
strength runs before the ramp starts. Each screen passes its own, because only the screen knows
what its bottom-most floating thing is.

  * **Favourites and All apps** — the search field, which rides on the collapsing header, so the
    anchor is `LocalFloatingHeaderHeight.current + GetoSearchFieldHeight` and it follows the title
    up and down.
  * **Settings** — the header alone; that tab has no search field.
  * **Both, along the bottom** — `getoFloatingBarInset()`, the tab bar's own reserved height plus
    the system navigation bar. On a tablet that bar is down the left edge, so the anchor is zero
    and the band is not drawn at all: the author's *"in tablets as there is no tab bar at bottom no
    need to display blur in bottom section"*.

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


# ------------------------------------------------------------ 0. the modifier changed shape

blur = BLUR.read_text(encoding="utf-8")

check("    topSolid: Dp = 0.dp,\n" in blur, "the modifier does not take topSolid")

check("    bottomSolid: Dp = 0.dp,\n" in blur, "the modifier does not take bottomSolid")

check("ProgressiveBlurDefaults.HeaderHeight" not in blur, "an old band height survived")

check("val FadeLength: Dp" in blur, "the ramp length is missing")

# The bottom band is skipped entirely when its anchor is zero — the tablet case.
check(
    "if (topSolid <= 0.dp && bottomSolid <= 0.dp) return this" in blur,
    "the no-band shortcut is missing",
)

# ------------------------------------------------------------ 1. All apps

apps = APPS.read_text(encoding="utf-8")

apps = swap(
    apps,
    """                .progressiveEdgeBlur(
                    blur = launcherAppsActivityInfoData.userData.progressiveBlur,
                    topHeight = ProgressiveBlurDefaults.HeaderHeight,
                    bottomHeight = ProgressiveBlurDefaults.Height,
                ),""",
    """                // ⚠ **Anchored on the two floating things, not on fixed heights — r15.** The
                // top stays at full strength down to the bottom of the search field and starts
                // fading there; because the field rides on the collapsing header, so does this.
                // The bottom is anchored on the tab bar, and is zero on a tablet, where the bar
                // is down the left edge and there is nothing along the foot to hide behind.
                .progressiveEdgeBlur(
                    blur = launcherAppsActivityInfoData.userData.progressiveBlur,
                    topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,
                    bottomSolid = if (getoUsesSideRail()) 0.dp else barInset,
                ),""",
    "AppsScreen: band anchors",
)

apps = swap(
    apps,
    "import com.android.geto.designsystem.component.ProgressiveBlurDefaults\n",
    "import com.android.geto.designsystem.component.getoUsesSideRail\n",
    "AppsScreen: imports",
)

pending.append((APPS, apps))

# ------------------------------------------------------------ 2. Favourites

favs = FAVS.read_text(encoding="utf-8")

favs = swap(
    favs,
    """        val edgeBlur = Modifier.progressiveEdgeBlur(
            blur = userData.progressiveBlur,
            topHeight = ProgressiveBlurDefaults.HeaderHeight,
            bottomHeight = ProgressiveBlurDefaults.Height,
        )""",
    """        // ⚠ **The same two anchors All apps uses — r15**: full strength behind the search
        // field and behind the tab bar, fading out of each. Zero along the bottom on a tablet,
        // where the bar is a rail down the left edge.
        val edgeBlur = Modifier.progressiveEdgeBlur(
            blur = userData.progressiveBlur,
            topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,
            bottomSolid = if (getoUsesSideRail()) 0.dp else barInset,
        )""",
    "FavouriteAppsScreen: band anchors",
)

favs = swap(
    favs,
    "import com.android.geto.designsystem.component.ProgressiveBlurDefaults\n",
    "import com.android.geto.designsystem.component.getoUsesSideRail\n",
    "FavouriteAppsScreen: imports",
)

pending.append((FAVS, favs))

# ------------------------------------------------------------ 3. Settings

settings = SETTINGS.read_text(encoding="utf-8")

settings = swap(
    settings,
    """            .progressiveEdgeBlur(
                blur = userData.progressiveBlur,
                topHeight = ProgressiveBlurDefaults.HeaderHeight,
                bottomHeight = ProgressiveBlurDefaults.SettingsHeight,
            )""",
    """            // ⚠ **The header alone up top — r15.** This tab has no search field, so the
            // bottom-most floating thing above the page is the title itself, and the fade starts
            // where it ends. Along the bottom it is the tab bar, and nothing at all on a tablet.
            .progressiveEdgeBlur(
                blur = userData.progressiveBlur,
                topSolid = LocalFloatingHeaderHeight.current,
                bottomSolid = if (getoUsesSideRail()) 0.dp else getoFloatingBarInset(),
            )""",
    "SettingsScreen: band anchors",
)

settings = swap(
    settings,
    "import com.android.geto.designsystem.component.ProgressiveBlurDefaults\n",
    "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n"
    "import com.android.geto.designsystem.component.getoUsesSideRail\n",
    "SettingsScreen: imports",
)

pending.append((SETTINGS, settings))

# ------------------------------------------------------------ commit

for path, text in pending:
    check(
        "ProgressiveBlurDefaults" not in text,
        f"{path.name}: still names ProgressiveBlurDefaults",
    )

    check("topHeight" not in text, f"{path.name}: an old topHeight argument survived")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
