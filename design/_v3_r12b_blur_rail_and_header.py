#!/usr/bin/env python3
"""
r12b — the three the author asked for after device-testing r12a.

  1. **Zero visible blur, top or bottom.** Traced rather than guessed: measuring his screenshot,
     the app-name text peaks at exactly 227 and the package name at exactly 199 on *every* row —
     inside the top band, in the middle of the page and inside the bottom band alike. So not even
     the 34 % tint reached the screen. r12's overlay `Box`es did not draw at all. The rewrite is
     in ProgressiveBlur.kt; this script only restores the strength number and leaves the call
     sites alone, because the wrapper's signature has not changed.

  2. **The floating buttons on a tablet.** `getoFloatingBarInset()` reserved the tab bar's 96 dp
     at the foot of every window, including the ones where the bar is standing down the left edge
     and there is nothing at the foot to clear. The breakpoint moves into :design-system so the
     buttons, the lists and the home scaffold all read one answer.

  3. **The collapsed header, further up.** COLLAPSED_TITLE_HEIGHT 64 → 40 dp and the title's
     bottom padding 16 → 8 dp, which lifts the search field by 24 dp once the title has collapsed.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAV = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoFloatingNavigation.kt"

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

HOST = ROOT / "app/src/main/kotlin/com/android/geto/navigation/GetoNavHost.kt"

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    if check(text.count(old) == count, f"{label}: found {text.count(old)}x, expected {count}"):
        return text.replace(old, new, count)

    return text


# ------------------------------------------------------------ 0. the rewrite landed

blur = BLUR.read_text(encoding="utf-8")

check("private fun Modifier.edgeBands(" in blur, "ProgressiveBlur.kt is not the r12b rewrite")

# Counted on code lines only: the KDoc names `matchParentSize` while recounting the r12 failure,
# and prose about a mistake is not the mistake. Same comment trap as r11's `SwitchDefaults`.
blur_code = "\n".join(
    line for line in blur.splitlines() if not line.lstrip().startswith(("*", "//", "/*"))
)

check("matchParentSize" not in blur_code, "ProgressiveBlur.kt still has an overlay Box")

check(blur_code.count("drawBehind") == 0, "ProgressiveBlur.kt still draws from a sibling node")

check(blur_code.count("drawLayer(layer)") == 1, "the layer is drawn more than once per frame")

check("val BlurRadius: Dp = 14.dp" in blur, "the blur radius is not back at the author's P2")

# ------------------------------------------------------------ 1. GetoFloatingNavigation.kt

nav = NAV.read_text(encoding="utf-8")

nav = swap(
    nav,
    "import androidx.compose.ui.graphics.Color\n",
    "import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.platform.LocalConfiguration\n",
    "nav: LocalConfiguration import",
)

OLD_BAR_INSET = """/** The same for the bottom: the system navigation bar and the floating tab bar above it. */
@Composable
fun getoFloatingBarInset(): Dp =
    WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding() + GetoNavBarReservedHeight
"""

NEW_BAR_INSET = '''/**
 * Which way the tab bar reads: along the bottom of the window, or standing on its left edge.
 *
 * ⚠ **One answer, and since r12b three callers read it.** `HomeScreen` draws the bar from it and
 * decides which way a tab change slides and whether a sideways drag changes tab at all; the two
 * insets below decide how much room a page leaves at its foot; and the app's floating buttons sit
 * on the second of those. It lived in `:feature:home` as a private pair of numbers until the
 * buttons needed the same answer, and two copies of a breakpoint are two answers that can
 * disagree.
 *
 * The breakpoints are the ones the navigation suite used before r10 replaced it, kept rather than
 * re-chosen so that a device which showed a rail in r9 still shows one now.
 */
@Composable
fun getoUsesSideRail(): Boolean {
    val configuration = LocalConfiguration.current

    return configuration.screenWidthDp >= NAVIGATION_RAIL_MIN_WIDTH_DP &&
        configuration.screenHeightDp >= NAVIGATION_RAIL_MIN_HEIGHT_DP
}

/**
 * The same for the bottom: the system navigation bar, and the floating tab bar above it when
 * there is one.
 *
 * ⚠ **Nothing is reserved for the bar on a tablet — r12b.** The bar stands down the left edge
 * there, so a page that still held [GetoNavBarReservedHeight] clear at its foot was holding it
 * clear of nothing, and the author saw the two floating buttons hovering a bar's height above the
 * bottom of the screen with empty space beneath them.
 */
@Composable
fun getoFloatingBarInset(): Dp =
    WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding() +
        if (getoUsesSideRail()) 0.dp else GetoNavBarReservedHeight

/**
 * Where the floating buttons rest above the bottom edge.
 *
 * On a phone that is exactly [getoFloatingBarInset] — flush with the top of the tab bar, which is
 * where the author put them in r12. On a tablet there is no bar underneath them, so they take the
 * ordinary margin off the window edge instead: *"keep the unhide and settings manager button at
 * bottom as previously"*.
 */
@Composable
fun getoFloatingActionInset(): Dp = getoFloatingBarInset() +
    if (getoUsesSideRail()) FLOATING_ACTION_EDGE_MARGIN else 0.dp

/** The window a navigation rail needs before the bar is stood on its left edge. */
private const val NAVIGATION_RAIL_MIN_WIDTH_DP = 600

/**
 * And the height below which it stays at the bottom however wide the window is.
 *
 * A phone in landscape is wide and short: there is room beside the content for a rail but not
 * enough above and below it to give up any, so the bar stays where it is. Without this test a
 * rotated phone would get a rail down the side of a 400 dp-tall window, animate vertically
 * against it, and lose the swipe it had a moment earlier in portrait.
 */
private const val NAVIGATION_RAIL_MIN_HEIGHT_DP = 480

/** The same margin the buttons already keep from the right-hand edge. */
private val FLOATING_ACTION_EDGE_MARGIN: Dp = 16.dp
'''

nav = swap(nav, OLD_BAR_INSET, NEW_BAR_INSET, "nav: bar inset block")

pending.append((NAV, nav))

# ------------------------------------------------------------ 2. HomeScreen.kt

home = HOME.read_text(encoding="utf-8")

OLD_RAIL = """    // The breakpoints are the ones the suite used, kept deliberately: a rail wants 600 dp of
    // width, and a window shorter than 480 dp keeps the bar at the bottom however wide it is -
    // which is what a phone held in landscape is, and why width alone is not the test.
    val configuration = LocalConfiguration.current

    val sideRail = configuration.screenWidthDp >= NAVIGATION_RAIL_MIN_WIDTH_DP &&
        configuration.screenHeightDp >= NAVIGATION_RAIL_MIN_HEIGHT_DP
"""

NEW_RAIL = """    // ⚠ **The breakpoints moved to :design-system in r12b.** The floating buttons need this same
    // answer — a window with no bar along its foot must not keep the bar's height clear of one —
    // and a second copy of a breakpoint is a second answer that can disagree with this one.
    val sideRail = getoUsesSideRail()
"""

home = swap(home, OLD_RAIL, NEW_RAIL, "home: sideRail block")

home = swap(
    home,
    "import androidx.compose.ui.platform.LocalConfiguration\n",
    "",
    "home: LocalConfiguration import",
)

home = swap(
    home,
    "import com.android.geto.designsystem.component.GetoNavRailReservedWidth\n",
    "import com.android.geto.designsystem.component.GetoNavRailReservedWidth\n"
    "import com.android.geto.designsystem.component.getoUsesSideRail\n",
    "home: getoUsesSideRail import",
)

OLD_CONSTS = """/**
 * The window a navigation rail needs before the bar is stood on its left edge.
 *
 * The compact/medium width breakpoint - Material's own, and the one the navigation suite used
 * before r10 replaced it. Kept rather than re-chosen so that a device which showed a rail in r9
 * still shows one now.
 */
private const val NAVIGATION_RAIL_MIN_WIDTH_DP = 600

/**
 * And the height below which it stays at the bottom however wide the window is.
 *
 * A phone in landscape is wide and short: there is room beside the content for a rail but not
 * enough above and below it to give up any, so the bar stays where it is. Without this test a
 * rotated phone would get a rail down the side of a 400 dp-tall window, animate vertically
 * against it, and lose the swipe it had a moment earlier in portrait.
 */
private const val NAVIGATION_RAIL_MIN_HEIGHT_DP = 480

"""

home = swap(home, OLD_CONSTS, "", "home: rail breakpoint constants")

check(
    "NAVIGATION_RAIL_MIN" not in home,
    "a NAVIGATION_RAIL_MIN reference survived in HomeScreen",
)

check("LocalConfiguration" not in home, "a LocalConfiguration reference survived in HomeScreen")

# The collapsed header, further up.
home = swap(
    home,
    """/** What the header collapses to: Material's own small top-bar height. */
private val COLLAPSED_TITLE_HEIGHT: Dp = 64.dp
""",
    """/**
 * What the header collapses to.
 *
 * ⚠ **40 dp rather than Material's 64 — the author's r12b *"i need header and searchbar to be
 * more up after scrolling down"*.** Material's small top bar is 64 dp because it holds a row of
 * icon buttons; this one holds a single 22 sp line and nothing else, so most of that height was
 * air. With [TITLE_BOTTOM_PADDING] below it the collapsed title still clears its own line box,
 * and the search field — which is drawn at the header's current height — rises by the same 24 dp.
 */
private val COLLAPSED_TITLE_HEIGHT: Dp = 40.dp
""",
    "home: collapsed title height",
)

home = swap(
    home,
    "private val TITLE_BOTTOM_PADDING: Dp = 16.dp\n",
    """/** Cut with the collapsed height in r12b; 16 dp under a 40 dp bar leaves the title no room. */
private val TITLE_BOTTOM_PADDING: Dp = 8.dp
""",
    "home: title bottom padding",
)

pending.append((HOME, home))

# ------------------------------------------------------------ 3. GetoNavHost.kt

host = HOST.read_text(encoding="utf-8")

host = swap(
    host,
    "import com.android.geto.designsystem.component.getoFloatingBarInset\n",
    "import com.android.geto.designsystem.component.getoFloatingActionInset\n",
    "host: inset import",
)

host = swap(
    host,
    """                            // Clear of the floating tab bar, which the author found them
                            // overlapping. getoFloatingBarInset() is the bar's own reserved
                            // height plus the system navigation bar.
                            .padding(end = 16.dp, bottom = getoFloatingBarInset()),""",
    """                            // Clear of the floating tab bar on a phone, which the author
                            // found them overlapping; on a tablet the bar is down the left edge
                            // and this is the plain bottom margin instead, which is where he
                            // asked for them back in r12b.
                            .padding(end = 16.dp, bottom = getoFloatingActionInset()),""",
    "host: FAB bottom padding",
)

check("getoFloatingBarInset" not in host, "a getoFloatingBarInset reference survived in GetoNavHost")

pending.append((HOST, host))

# ------------------------------------------------------------ commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
