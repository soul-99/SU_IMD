#!/usr/bin/env python3
"""
r14 — the clipped title, the scroll-up rule, and the section colours as Material 3 roles.

  1. **The collapsed title cut off at the bottom.** Not the search field at all: `Box` measures its
     children with its own maximum, so a 32 dp header measured a 36 dp line of `headlineMedium`
     with `maxHeight = 32 dp` and the `Text` clipped its own line. `wrapContentHeight(unbounded)`
     measures it at its natural height and lets it hang out of the box, which is what a title
     scaled about its bottom edge is supposed to do.

  2. **"the header should only move when i reach the top of the page".** r13c coupled the header to
     `consumed` in both directions, so any upward drag re-expanded it mid-list. Collapsing still
     follows `consumed` — that is what makes the header travel with the page — but expanding now
     follows `available`, which is only non-zero once the list has nothing left to give. So it
     re-opens at the top of the page and nowhere else, and the pull that opens it is consumed so
     the overscroll stretch does not fight it.

  3. **The settings sections on Material 3's surface roles.** The three tints were the theme's
     primary composited at 8 %, 12 % and 34 % — numbers arrived at by asking him twice how green
     was too green. M3 already answers this: elevation is expressed as tonal *containers*, one
     role per step, generated correctly for light and dark by the same scheme. Collapsed card →
     `surfaceContainerLow`, open body → `surfaceContainer`, heading strip → `surfaceContainerHigh`.
     The ordering the sections rely on is the ladder's own, so it cannot drift.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

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


# ------------------------------------------------------------ 0. the blur moved off the layer API

blur = BLUR.read_text(encoding="utf-8")

blur_code = "\n".join(
    line for line in blur.splitlines() if not line.lstrip().startswith(("*", "//", "/*"))
)

check("rememberGraphicsLayer" not in blur_code, "the standalone GraphicsLayer API is still used")

check("graphicsLayer {" in blur_code, "the node's own layer is not being used")

check(blur_code.count("drawContent()") == 1, "drawContent() is called more than once")

# ------------------------------------------------------------ 1. the title, un-clipped

home = HOME.read_text(encoding="utf-8")

home = swap(
    home,
    """        Text(
            modifier = Modifier
                .align(Alignment.BottomStart)
                .padding(start = TITLE_START_PADDING, bottom = TITLE_BOTTOM_PADDING)""",
    """        Text(
            // ⚠ **`unbounded`, and this is what was cutting the title — r14.** A `Box` measures
            // its children against its own maximum, so once the header collapsed to 32 dp the
            // 36 dp line of `headlineMedium` was measured with `maxHeight = 32 dp` and the `Text`
            // clipped its own glyphs — the author's *"tab header font is cut from bottom"*.
            // Nothing was drawing over it; it was never drawn. Measured unbounded it takes its
            // natural height and hangs out of the box, which is exactly what a title scaled about
            // its own bottom edge is meant to do.
            modifier = Modifier
                .align(Alignment.BottomStart)
                .wrapContentHeight(align = Alignment.Bottom, unbounded = true)
                .padding(start = TITLE_START_PADDING, bottom = TITLE_BOTTOM_PADDING)""",
    "home: title wrapContentHeight",
)

home = swap(
    home,
    "import androidx.compose.foundation.layout.statusBarsPadding\n",
    "import androidx.compose.foundation.layout.statusBarsPadding\n"
    "import androidx.compose.foundation.layout.wrapContentHeight\n",
    "home: wrapContentHeight import",
)

# ------------------------------------------------------------ 2. the scroll-up rule

home = swap(
    home,
    """    // This consumes nothing and reads `onPostScroll`, which reports what the list actually took.
    // The header then moves by that same amount, so the two travel together at 1:1 — and when the
    // list has nothing left to give, at either end, the header stops with it.""",
    """    // Collapsing reads `consumed` — what the list actually took — so the header travels with the
    // page rather than ahead of it. **Expanding reads `available` instead, which r14 changed:**
    // `available` is what is left over after the list has taken its share, and mid-list that is
    // zero, so an upward drag moves only the page. It becomes non-zero exactly when the list has
    // run out of room, which is the author's *"the header and search bar should only move when i
    // reach the top of the page"*. That leftover is consumed while the header is opening, so the
    // overscroll stretch does not start until the header is fully out.""",
    "home: scroll rule comment",
)

home = swap(
    home,
    """            ): Offset {
                headerOffset = (headerOffset + consumed.y).coerceIn(-collapseRange, 0f)

                // Nothing taken. That is the whole point of this object.
                return Offset.Zero
            }""",
    """            ): Offset {
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
            }""",
    "home: scroll rule body",
)

pending.append((HOME, home))

# ------------------------------------------------------------ 3. the sections, as M3 roles

settings = SETTINGS.read_text(encoding="utf-8")

OLD_TINTS = """    // ⚠ **The body alone came down in r12** — the author's "make settings under expanded setting
    // section less green less bright", and then, having seen both: *"just change body only, to
    // 8%"*. The heading strip and the collapsed card keep the values they had, so the ordering
    // page < collapsed < open body < heading still holds and still says which section is open;
    // what changes is that the rows inside an open section now sit much closer to the page. In
    // the dark scheme the body goes from #262E1E to #1A1F14.
    val bodyTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.08f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)

    val headingTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.34f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)

    val collapsedTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.12f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)
"""

NEW_TINTS = """    // ⚠ **Material 3's surface roles rather than three alphas of the theme's primary — r14, at
    // the author's instruction to put these on the M3 expressive guidelines in both schemes.**
    //
    // The old values were 8 %, 12 % and 34 % of `primary` composited over the lowest container:
    // numbers arrived at by asking him twice how green was too green, correct in the dark scheme
    // he was looking at and never checked in the light one. M3 answers this question already, and
    // answers it per-scheme: raising a surface is expressed as a step up the **tonal container
    // ladder**, one named role per step, generated for light and dark by the same scheme so the
    // relationship survives a theme change and a dynamic palette alike.
    //
    // The ordering the sections depend on — page below the collapsed card, below the open body,
    // below the heading strip — is now the ladder's own ordering rather than three numbers that
    // have to be kept in the right sequence by hand.
    val bodyTint = MaterialTheme.colorScheme.surfaceContainer

    val headingTint = MaterialTheme.colorScheme.surfaceContainerHigh

    val collapsedTint = MaterialTheme.colorScheme.surfaceContainerLow
"""

settings = swap(settings, OLD_TINTS, NEW_TINTS, "settings: section tints")

pending.append((SETTINGS, settings))

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
