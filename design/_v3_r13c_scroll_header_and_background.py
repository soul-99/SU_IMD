#!/usr/bin/env python3
"""
r13c — the header follows the page instead of leading it, the collapsed title clears the search
field, and the dark theme's page is lifted off near-black.

  1. **"the header and search bar moves first then the page contents — can't they all move
     together?"** Material's `exitUntilCollapsedScrollBehavior` consumes the drag in `onPreScroll`:
     the bar takes the first 120 dp of every downward gesture and only hands what is left to the
     list, which is exactly the two-stage motion in his video. Replaced with a connection that
     consumes nothing and reads `onPostScroll` — the list scrolls first and the header moves by
     the amount the list actually took, so the two travel together at 1:1 in both directions.

  2. **The collapsed title clipped by the search field.** The title is scaled about its own bottom
     edge, so a bigger bottom padding lifts it; r13 cut that padding to 4 dp and put it into the
     field. Back to 10 dp, and the collapsed type drops from 22 sp to 20 sp so the extra lift does
     not push it into the status bar. The header height — and so the search field — does not move,
     which is what he asked for.

  3. **The dark page, less dark.** #12140E is Material's own generated surface for this scheme and
     the author finds it too close to black with OLED mode off. The whole surface ladder moves up
     about nine points, keeping every step's ordering and its distance from its neighbours. OLED
     mode is unaffected: it overrides these to true black.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

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


# ------------------------------------------------------------ 0. the blur rewrite landed

blur = BLUR.read_text(encoding="utf-8")

check("private fun bandedBlurEffect(" in blur, "the RenderEffect chain is missing")

blur_code = "\n".join(
    line for line in blur.splitlines() if not line.lstrip().startswith(("*", "//", "/*"))
)

check("saveLayer" not in blur_code, "a saveLayer survived in the blur path")

# Three: the zero-height guard, the one walk inside `record`, and the no-blur path.
check(blur_code.count("drawContent()") == 3, "drawContent() is called on more paths than expected")

check(blur_code.count("drawLayer(layer)") == 1, "the layer is drawn more than once")

# ------------------------------------------------------------ 1. HomeScreen: scroll coupling

home = HOME.read_text(encoding="utf-8")

OLD_BEHAVIOUR = """    // exitUntilCollapsed, not enterAlways. enterAlways re-expands the bar on *any* upward
    // drag, so every change of direction shifts the whole page by the bar's collapse
    // distance on top of the finger movement -- and on a LargeTopAppBar that distance is
    // most of a title. On the two lazy lists it is lost in a long list; the settings tab is
    // a plain column barely taller than the screen, so the same shift is a large fraction
    // of its whole scroll range and reads as the page moving faster than the finger.
    //
    // enterAlways is meant for the small top app bar. A large one is paired with this.
    val topAppBarScrollBehavior = exitUntilCollapsedScrollBehavior()
"""

NEW_BEHAVIOUR = """    // ⚠ **Material's scroll behaviours are gone — r13c, and the author's video is why.** Both of
    // them *consume* the drag in `onPreScroll`: the bar helps itself to the first 120 dp of every
    // downward gesture and passes on what is left, so the header moves, finishes, and only then
    // does the list start. He described it exactly: *"when i first scroll up the header and
    // search bar moves first then the page contents, can't they all move together?"*
    //
    // This consumes nothing and reads `onPostScroll`, which reports what the list actually took.
    // The header then moves by that same amount, so the two travel together at 1:1 — and when the
    // list has nothing left to give, at either end, the header stops with it.
    val density = LocalDensity.current

    val collapseRange = with(density) { (GetoLargeTopBarHeight - COLLAPSED_TITLE_HEIGHT).toPx() }

    var headerOffset by rememberSaveable { mutableFloatStateOf(0f) }

    val headerScroll = remember(collapseRange) {
        object : NestedScrollConnection {
            override fun onPostScroll(
                consumed: Offset,
                available: Offset,
                source: NestedScrollSource,
            ): Offset {
                headerOffset = (headerOffset + consumed.y).coerceIn(-collapseRange, 0f)

                // Nothing taken. That is the whole point of this object.
                return Offset.Zero
            }
        }
    }

    val collapsedFraction = if (collapseRange > 0f) -headerOffset / collapseRange else 0f
"""

home = swap(home, OLD_BEHAVIOUR, NEW_BEHAVIOUR, "home: scroll behaviour")

OLD_LIMIT = """    // ⚠ **The scroll behaviour has no app bar to tell it how far to collapse**, now that the
    // header is drawn by hand: `heightOffsetLimit` is normally set by `LargeTopAppBar` during
    // its own layout, and left at zero nothing moves at all. Set here, in pixels, once per
    // density change.
    val density = LocalDensity.current

    val collapseRange = with(density) { (GetoLargeTopBarHeight - COLLAPSED_TITLE_HEIGHT).toPx() }

    SideEffect {
        if (topAppBarScrollBehavior.state.heightOffsetLimit != -collapseRange) {
            topAppBarScrollBehavior.state.heightOffsetLimit = -collapseRange
        }
    }

    val collapsedFraction = topAppBarScrollBehavior.state.collapsedFraction

"""

home = swap(home, OLD_LIMIT, "", "home: heightOffsetLimit block")

home = swap(
    home,
    "                    .nestedScroll(topAppBarScrollBehavior.nestedScrollConnection)\n",
    "                    .nestedScroll(headerScroll)\n",
    "home: nestedScroll",
)

check(
    "topAppBarScrollBehavior" not in home,
    "a reference to the old scroll behaviour survived",
)

home = swap(
    home,
    "import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior\n",
    "",
    "home: exitUntilCollapsedScrollBehavior import",
)

home = swap(home, "import androidx.compose.runtime.SideEffect\n", "", "home: SideEffect import")

home = swap(
    home,
    "import androidx.compose.runtime.mutableIntStateOf\n",
    "import androidx.compose.runtime.mutableFloatStateOf\n"
    "import androidx.compose.runtime.mutableIntStateOf\n"
    "import androidx.compose.runtime.remember\n",
    "home: state imports",
)

home = swap(
    home,
    "import androidx.compose.ui.input.nestedscroll.nestedScroll\n",
    "import androidx.compose.ui.input.nestedscroll.NestedScrollConnection\n"
    "import androidx.compose.ui.input.nestedscroll.NestedScrollSource\n"
    "import androidx.compose.ui.input.nestedscroll.nestedScroll\n",
    "home: nested-scroll imports",
)

home = swap(
    home,
    "import androidx.compose.ui.graphics.TransformOrigin\n",
    "import androidx.compose.ui.geometry.Offset\nimport androidx.compose.ui.graphics.TransformOrigin\n",
    "home: Offset import",
)

# ------------------------------------------------------------ 2. HomeScreen: the title metrics

home = swap(
    home,
    """ * Material's two type scales for a large bar are `headlineMedium` at 28 sp expanded and
 * `titleLarge` at 22 sp collapsed; 22/28 is this. Expressed as a ratio rather than as a second
 * text style because the point is that it is continuous — every value between the two is drawn.
 */
private const val COLLAPSED_TITLE_SCALE = 22f / 28f
""",
    """ * Material's two type scales for a large bar are `headlineMedium` at 28 sp expanded and
 * `titleLarge` at 22 sp collapsed. This goes one step further, to 20 sp, and r13c is why: the
 * author found the collapsed title clipped by the search field, and it is lifted clear by giving
 * it more room below rather than by moving the field — which he said was where he wanted it. A
 * title that lifts without shrinking would reach the status bar instead. Expressed as a ratio
 * rather than as a second text style because the point is that it is continuous — every value
 * between the two is drawn.
 */
private const val COLLAPSED_TITLE_SCALE = 20f / 28f
""",
    "home: collapsed title scale",
)

home = swap(
    home,
    """/** Cut with the collapsed height in r12b; 16 dp under a 40 dp bar leaves the title no room. */
private val TITLE_BOTTOM_PADDING: Dp = 4.dp
""",
    """/**
 * How far the title sits above the bottom of the header.
 *
 * ⚠ **This is what lifts the collapsed title, because it is scaled about its own bottom edge.**
 * r13 cut it to 4 dp along with the header height and put the title into the search field; 10 dp
 * takes it back out with the field left where it is.
 */
private val TITLE_BOTTOM_PADDING: Dp = 10.dp
""",
    "home: title bottom padding",
)

pending.append((HOME, home))

# ------------------------------------------------------------ 3. the dark page, lifted

theme = THEME.read_text(encoding="utf-8")

# ⚠ **Anchored on the property name, not on the hex.** #1A1C16 is also the light scheme's
# `onBackground` and `onSurface`, and #33362E is its `inverseSurface`; replacing by colour alone
# would have repainted the light theme's ink.
LIFTS = (
    ("background", "0xFF12140E", "0xFF1B1E16"),
    ("surface", "0xFF12140E", "0xFF1B1E16"),
    ("surfaceDim", "0xFF12140E", "0xFF1B1E16"),
    ("surfaceContainerLowest", "0xFF0C0F09", "0xFF14160E"),
    ("surfaceContainerLow", "0xFF1A1C16", "0xFF21241C"),
    ("surfaceContainer", "0xFF1E201A", "0xFF262920"),
    ("surfaceContainerHigh", "0xFF282B24", "0xFF31352B"),
    ("surfaceContainerHighest", "0xFF33362E", "0xFF3C4036"),
)

for name, old, new in LIFTS:
    theme = swap(
        theme,
        f"    {name} = Color({old}),\n",
        f"    {name} = Color({new}),\n",
        f"theme: {name}",
    )

theme = swap(
    theme,
    "    background = Color(0xFF1B1E16),",
    """    // ⚠ **Lifted about nine points off Material's own #12140E — r13c.** The generated scheme's
    // page is very close to black, which the author reported as too dark with OLED mode off. The
    // whole surface ladder moves with it so that every container keeps its distance from the page
    // and from its neighbours; OLED mode overrides all of it to true black regardless.
    background = Color(0xFF1B1E16),""",
    "theme: dark surface note",
)

pending.append((THEME, theme))

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
