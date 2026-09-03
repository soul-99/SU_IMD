#!/usr/bin/env python3
"""
r16 — one collapse state per tab, and a much stronger shadow fade.

  1. **"keep the headers of both the tabs not related to each other in terms of collapse".** The
     header offset was a single number for the whole scaffold, so scrolling All apps collapsed the
     header that Favourites came back to — and Favourites, being a short list with nothing to
     scroll, had no way to give it back. It is a list now, one entry per tab, and the connection
     writes to the entry for whichever tab is showing. Each tab's header is where that tab left it.

     The block moves down the function, because it now needs `selectedIndex`, which is worked out
     from the current back-stack entry a few lines further on.

  2. **The shadow fade "very strong and dark".** It shared the blur's tint at 0.50/0.45; on its own
     that is not enough to say where a page ends. Fade-only goes to 0.88 dark and 0.80 light, and
     the blur keeps its own pair — the two are doing different amounts of work and no longer share
     a number.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

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


# ------------------------------------------------------------ 1. one collapse per tab

home = HOME.read_text(encoding="utf-8")

OLD_BLOCK = """    val density = LocalDensity.current

    val collapseRange = with(density) { (GetoLargeTopBarHeight - COLLAPSED_TITLE_HEIGHT).toPx() }

    var headerOffset by rememberSaveable { mutableFloatStateOf(0f) }

    val headerScroll = remember(collapseRange) {
        object : NestedScrollConnection {
            override fun onPostScroll(
                consumed: Offset,
                available: Offset,
                source: NestedScrollSource,
            ): Offset {
                // Downwards, follow the page. Upwards, follow only what the page could not use.
                val delta = if (consumed.y < 0f) consumed.y else available.y

                if (delta == 0f) return Offset.Zero

                val before = headerOffset

                headerOffset = (headerOffset + delta).coerceIn(-collapseRange, 0f)

                val moved = headerOffset - before

                // Collapsing takes nothing: the page has already scrolled by that much and the
                // header is only keeping pace. Opening takes what it used, so the list's
                // overscroll does not stretch at the same time.
                return if (delta > 0f) Offset(0f, moved) else Offset.Zero
            }
        }
    }

    val collapsedFraction = if (collapseRange > 0f) -headerOffset / collapseRange else 0f

"""

home = swap(home, OLD_BLOCK, "", "home: old header block")

# The comment above it stays where it is only if the whole thing moves together, so take that too.
OLD_NOTE = """    // ⚠ **Material's scroll behaviours are gone — r13c, and the author's video is why.** Both of
    // them *consume* the drag in `onPreScroll`: the bar helps itself to the first 120 dp of every
    // downward gesture and passes on what is left, so the header moves, finishes, and only then
    // does the list start. He described it exactly: *"when i first scroll up the header and
    // search bar moves first then the page contents, can't they all move together?"*
    //
    // Collapsing reads `consumed` — what the list actually took — so the header travels with the
    // page rather than ahead of it. **Expanding reads `available` instead, which r14 changed:**
    // `available` is what is left over after the list has taken its share, and mid-list that is
    // zero, so an upward drag moves only the page. It becomes non-zero exactly when the list has
    // run out of room, which is the author's *"the header and search bar should only move when i
    // reach the top of the page"*. That leftover is consumed while the header is opening, so the
    // overscroll stretch does not start until the header is fully out.
"""

home = swap(home, OLD_NOTE, "", "home: old header note")

ANCHOR = """    // Which tab is showing, as a position in the bar rather than a route. The swipe needs a
    // number to add one to; nothing else does.
    val selectedIndex = topLevelDestinations.indexOfFirst { destination ->
        currentDestination.isTopLevelDestinationInHierarchy(destination.route)
    }
"""

NEW_BLOCK = ANCHOR + """
    // ⚠ **Material's scroll behaviours are gone — r13c, and the author's video is why.** Both of
    // them *consume* the drag in `onPreScroll`: the bar helps itself to the first 120 dp of every
    // downward gesture and passes on what is left, so the header moves, finishes, and only then
    // does the list start. He described it exactly: *"when i first scroll up the header and
    // search bar moves first then the page contents, can't they all move together?"*
    //
    // Collapsing reads `consumed` — what the list actually took — so the header travels with the
    // page rather than ahead of it. **Expanding reads `available`, which r14 changed:** that is
    // what is left over after the list has taken its share, and mid-list it is zero, so an upward
    // drag moves only the page. It becomes non-zero exactly when the list has run out of room —
    // the author's *"the header and search bar should only move when i reach the top of the
    // page"*. The leftover is consumed while the header opens, so the overscroll stretch does not
    // start until the header is fully out.
    //
    // ⚠ **One offset per tab — r16.** It was a single number for the whole scaffold, so scrolling
    // All apps collapsed the header that Favourites came back to, and Favourites — a short list
    // with nothing to scroll — had no way to give it back: *"i cannot scroll it up to uncollapse
    // it"*. A tab's header is now its own, remembered while the other tabs move.
    val density = LocalDensity.current

    val collapseRange = with(density) { (GetoLargeTopBarHeight - COLLAPSED_TITLE_HEIGHT).toPx() }

    val headerOffsets = rememberSaveable(
        topLevelDestinations.size,
        saver = listSaver(
            save = { it.toList() },
            restore = { it.toMutableStateList() },
        ),
    ) {
        List(topLevelDestinations.size) { 0f }.toMutableStateList()
    }

    // -1 while the back stack settles on a destination; the scaffold still draws, so it needs an
    // answer rather than a crash.
    val headerOffset = headerOffsets.getOrElse(selectedIndex) { 0f }

    val headerScroll = remember(collapseRange, selectedIndex) {
        object : NestedScrollConnection {
            override fun onPostScroll(
                consumed: Offset,
                available: Offset,
                source: NestedScrollSource,
            ): Offset {
                if (selectedIndex !in headerOffsets.indices) return Offset.Zero

                // Downwards, follow the page. Upwards, follow only what the page could not use.
                val delta = if (consumed.y < 0f) consumed.y else available.y

                if (delta == 0f) return Offset.Zero

                val before = headerOffsets[selectedIndex]

                val after = (before + delta).coerceIn(-collapseRange, 0f)

                headerOffsets[selectedIndex] = after

                // Collapsing takes nothing: the page has already scrolled by that much and the
                // header is only keeping pace. Opening takes what it used, so the list's
                // overscroll does not stretch at the same time.
                return if (delta > 0f) Offset(0f, after - before) else Offset.Zero
            }
        }
    }

    val collapsedFraction = if (collapseRange > 0f) -headerOffset / collapseRange else 0f
"""

home = swap(home, ANCHOR, NEW_BLOCK, "home: new header block")

home = swap(
    home,
    "import androidx.compose.runtime.mutableFloatStateOf\n",
    "",
    "home: mutableFloatStateOf import",
)

home = swap(
    home,
    "import androidx.compose.runtime.saveable.rememberSaveable\n",
    "import androidx.compose.runtime.saveable.listSaver\n"
    "import androidx.compose.runtime.saveable.rememberSaveable\n"
    "import androidx.compose.runtime.toMutableStateList\n",
    "home: saver imports",
)

check("mutableFloatStateOf" not in home, "mutableFloatStateOf still referenced")

check(home.count("val collapsedFraction") == 1, "collapsedFraction is declared more than once")

check(home.count("val headerScroll") == 1, "headerScroll is declared more than once")

check(home.count("val selectedIndex") == 1, "selectedIndex is declared more than once")

# The block must now come after selectedIndex, or it would not compile.
check(
    home.index("val headerScroll") > home.index("val selectedIndex"),
    "the header block is still above selectedIndex",
)

pending.append((HOME, home))

# ------------------------------------------------------------ 2. the fade-only strength

blur = BLUR.read_text(encoding="utf-8")

blur = swap(
    blur,
    """    // ⚠ **One strength for both modes, and it is the darker one — r15.** It used to drop to
    // ObtainX's 0.34 whenever the blur was carrying some of the load; the author saw the result
    // and asked for *"the blur in dark mode should also have a dark tint"*. A blurred band with a
    // pale tint reads as a smear rather than as an edge, so the tint no longer depends on it.
    val fade = surface.copy(
        alpha = if (surface.luminance() < DARK_SURFACE_LUMINANCE) FADE_DARK else FADE_LIGHT,
    )""",
    """    val dark = surface.luminance() < DARK_SURFACE_LUMINANCE

    // ⚠ **Two strengths again — r16 — but not the pair r15 removed.** r15's mistake was making the
    // *blurred* band's tint the weaker one; it is now 0.50/0.45 either way, at the author's
    // *"the blur in dark mode should also have a dark tint"*. What r16 adds back is the other
    // direction: a band with **no** blur behind it is carrying the whole job alone, and he asked
    // for it *"very strong and dark"*. So fade-only is close to opaque where the chrome sits, and
    // still lands on the same quadratic ramp on its way out.
    val fade = surface.copy(
        alpha = when {
            blurring && dark -> FADE_DARK
            blurring -> FADE_LIGHT
            dark -> SHADOW_DARK
            else -> SHADOW_LIGHT
        },
    )""",
    "blur: fade strength",
)

blur = swap(
    blur,
    """private const val FADE_DARK = 0.50f

private const val FADE_LIGHT = 0.45f""",
    """private const val FADE_DARK = 0.50f

private const val FADE_LIGHT = 0.45f

/**
 * And the same band with no blur under it, which has to do the whole job on its own.
 *
 * Nearly opaque at the chrome's edge, at the author's word: *"make it very strong and dark"*. It
 * is not as heavy as it sounds — the solid part sits behind the header and the search field, where
 * there is nothing to read anyway, and 72 dp of quadratic ramp is all that shows.
 */
private const val SHADOW_DARK = 0.88f

private const val SHADOW_LIGHT = 0.80f""",
    "blur: shadow constants",
)

pending.append((BLUR, blur))

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
