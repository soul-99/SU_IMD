#!/usr/bin/env python3
"""
r17 — the band only appears once the page starts moving, and the blur ships off.

  1. **"only show the shadow fade/blur when user starts to scroll down".** The band was drawn at
     full strength the moment a tab opened, so with the header expanded it sat on top of the first
     rows — which are not under anything and have nothing to hide behind. It now fades in with the
     header's own collapse: nothing at the top of the page, full strength once the title has
     finished collapsing, and every value in between on the way. That is one number the scaffold
     already computes, published beside the header height so the three pages can read it.

  2. **Off for a fresh install.** `progressiveBlurOff` was named for the off state precisely so
     that an unwritten bool would arrive switched *on*; the author now wants the opposite, and the
     name has to move with the meaning or the next reader will trust the comment over the code.
     Field 75 is retired and **reserved** rather than reinterpreted — a proto field number carries
     whatever every existing install already wrote at it, and flipping the sense underneath one
     would turn every current user's "on" into an "off" by accident rather than by decision. The
     new field 79 is `progressiveBlurOn`, and proto3's unwritten `false` is now the answer he
     asked for.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAV = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoFloatingNavigation.kt"

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

APPS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"

FAVS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

PROTO = ROOT / "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"

SOURCE = ROOT / "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

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


# ------------------------------------------------------------ 1. publish the collapse fraction

nav = NAV.read_text(encoding="utf-8")

nav = swap(
    nav,
    "val LocalFloatingHeaderHeight = compositionLocalOf { GetoLargeTopBarHeight }\n",
    """val LocalFloatingHeaderHeight = compositionLocalOf { GetoLargeTopBarHeight }

/**
 * How far the floating header has collapsed: 0 at the top of the page, 1 once the title is small.
 *
 * ⚠ **The edge treatment fades in on this — r17.** Drawn at full strength from the moment a tab
 * opened, the band sat over the first rows of a page that had not been scrolled, which are not
 * under anything and have nothing to hide behind: the author's *"it even shows over the topmost
 * contents when searchbar/header is expanded"*. Tying it to the collapse means the treatment
 * arrives exactly as content starts to disappear beneath the chrome, and is absent while there is
 * nothing beneath it.
 *
 * Provided by `HomeScreen`, which owns the scroll. Zero everywhere else, including in a preview.
 */
val LocalHeaderCollapse = compositionLocalOf { 0f }
""",
    "nav: LocalHeaderCollapse",
)

pending.append((NAV, nav))

home = HOME.read_text(encoding="utf-8")

home = swap(
    home,
    "    CompositionLocalProvider(LocalFloatingHeaderHeight provides headerHeight) {\n",
    """    CompositionLocalProvider(
        LocalFloatingHeaderHeight provides headerHeight,
        LocalHeaderCollapse provides collapsedFraction,
    ) {
""",
    "home: provider",
)

home = swap(
    home,
    "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n",
    "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n"
    "import com.android.geto.designsystem.component.LocalHeaderCollapse\n",
    "home: LocalHeaderCollapse import",
)

pending.append((HOME, home))

# ------------------------------------------------------------ 2. the modifier takes a strength

blur = BLUR.read_text(encoding="utf-8")

blur = swap(
    blur,
    """    fadeLength: Dp = ProgressiveBlurDefaults.FadeLength,
    blurRadius: Dp = ProgressiveBlurDefaults.BlurRadius,
): Modifier {""",
    """    strength: Float = 1f,
    fadeLength: Dp = ProgressiveBlurDefaults.FadeLength,
    blurRadius: Dp = ProgressiveBlurDefaults.BlurRadius,
): Modifier {""",
    "blur: strength parameter",
)

blur = swap(
    blur,
    """    if (topSolid <= 0.dp && bottomSolid <= 0.dp) return this""",
    """    if (topSolid <= 0.dp && bottomSolid <= 0.dp) return this

    // ⚠ **Clamped, never branched on — r17.** The chain's *shape* stays the same at every value,
    // so scrolling off the top does not add and remove a layer node on the frame the page starts
    // moving. At zero the gradient is transparent and the render effect is null: present, and
    // doing nothing.
    val amount = strength.coerceIn(0f, 1f)""",
    "blur: strength clamp",
)

blur = swap(
    blur,
    "                    position to fade.copy(alpha = fade.alpha * strength)",
    "                    position to fade.copy(alpha = fade.alpha * strength * amount)",
    "blur: fade alpha",
)

blur = swap(
    blur,
    """    return faded.graphicsLayer {
        val height = size.height

        if (height <= 0f) return@graphicsLayer

        renderEffect = bandedBlurEffect(
            radius = blurRadius.toPx(),""",
    """    return faded.graphicsLayer {
        val height = size.height

        val radius = blurRadius.toPx() * amount

        // A zero-radius blur is not a no-op on every driver; some report an error rather than
        // drawing the source unchanged, so below half a pixel there is simply no effect at all.
        if (height <= 0f || radius < MINIMUM_BLUR_PX) {
            renderEffect = null

            return@graphicsLayer
        }

        renderEffect = bandedBlurEffect(
            radius = radius,""",
    "blur: radius scaling",
)

check("MINIMUM_BLUR_PX" in blur, "MINIMUM_BLUR_PX is referenced but not declared")

if "private const val MINIMUM_BLUR_PX" not in blur:
    blur = swap(
        blur,
        "/** Full alpha as a gradient colour channel",
        "/** Below this the blur is skipped rather than asked for. */\nprivate const val MINIMUM_BLUR_PX = 0.5f\n\n/** Full alpha as a gradient colour channel",
        "blur: MINIMUM_BLUR_PX",
    )

blur = swap(
    blur,
    """ * @param topSolid how far the top band stays at full strength""",
    """ * @param strength how much of the treatment to apply, 0 to 1. The pages pass the header's own
 *  collapse, so the band arrives as content starts to disappear under the chrome and is absent
 *  while the page is at the top and there is nothing beneath it to hide.
 * @param topSolid how far the top band stays at full strength""",
    "blur: strength doc",
)

pending.append((BLUR, blur))

# ------------------------------------------------------------ 3. the three pages pass it

for path, anchor, label in (
    (APPS, "                    topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,\n", "AppsScreen"),
    (FAVS, "            topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,\n", "FavouriteAppsScreen"),
    (SETTINGS, "                topSolid = LocalFloatingHeaderHeight.current,\n", "SettingsScreen"),
):
    text = path.read_text(encoding="utf-8")

    indent = anchor[: len(anchor) - len(anchor.lstrip())]

    text = swap(
        text,
        anchor,
        anchor + f"{indent}strength = LocalHeaderCollapse.current,\n",
        f"{label}: strength argument",
    )

    text = swap(
        text,
        "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n",
        "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n"
        "import com.android.geto.designsystem.component.LocalHeaderCollapse\n",
        f"{label}: LocalHeaderCollapse import",
    )

    pending.append((path, text))

# ------------------------------------------------------------ 4. off by default

proto = PROTO.read_text(encoding="utf-8")

proto = swap(
    proto,
    """  // Whether the bottom-edge blur is switched OFF - the author's "Progressive UI blur", which he
  // asked for enabled by default.
  //
  // Named for the off state on purpose. proto3 decodes an unwritten bool to false, so a field
  // named for the on state would arrive off on every fresh install and on every upgrade into
  // this build, which is the opposite of what was asked for. UserData.progressiveBlur is the
  // positive reading and is what the app uses; this spelling exists only here.
  bool progressiveBlurOff = 75;
""",
    """  // 75 was progressiveBlurOff. See progressiveBlurOn on 79.
""",
    "proto: retire 75",
)

proto = swap(
    proto,
    "  bool drawerShortcutHideUnhideOn = 78;\n",
    """  bool drawerShortcutHideUnhideOn = 78;

  // Whether the edge blur is switched ON - the author's "Progressive UI blur".
  //
  // ⚠ Named the other way round from the field it replaces, because the default reversed: r17's
  // "make the blur toggle off by default for new installs". proto3 decodes an unwritten bool to
  // false, so a field named for the ON state is off until something writes it, which is now what
  // was asked for.
  //
  // ⚠ A new number rather than the old one with its meaning flipped. Field 75 already holds a
  // written value on every install that has run r10 or later, and reinterpreting it would turn
  // each of those into its opposite by accident rather than by decision. 75 is reserved below.
  bool progressiveBlurOn = 79;
""",
    "proto: add 79",
)

proto = swap(
    proto,
    "  reserved 9, 14, 46, 55;",
    "  reserved 9, 14, 46, 55, 75;",
    "proto: reserve 75",
)

proto = swap(
    proto,
    "  // same reasoning as progressiveBlurOff on 75.\n",
    "  // same reasoning progressiveBlurOn on 79 uses, in the other direction.\n",
    "proto: cross-reference",
)

# ⚠ Declarations only. The retirement note names the old field on purpose — a `reserved`
# number is only useful next to a sentence saying what used to be there.
check(
    "bool progressiveBlurOff" not in proto,
    "the retired field is still declared in the proto",
)

pending.append((PROTO, proto))

source = SOURCE.read_text(encoding="utf-8")

source = swap(
    source,
    """            // ⚠ The one inversion in this file, and the proto comment on field 75 is why:
            // the stored field is "off" so that an install which has never touched the switch
            // gets the blur. Everything above this line reads the positive.
            progressiveBlur = !it.progressiveBlurOff,""",
    """            // ⚠ **Read straight, since r17.** It used to be the one inversion in this file:
            // the field was named for the off state so that an install which had never touched
            // the switch got the blur. The author reversed that default, so the field is named
            // for the on state and there is nothing left to invert.
            progressiveBlur = it.progressiveBlurOn,""",
    "source: read",
)

source = swap(
    source,
    """            // Inverted here to match, and nowhere else. See the proto comment on field 75.
            it.copy { progressiveBlurOff = !enabled }""",
    "            it.copy { progressiveBlurOn = enabled }",
    "source: write",
)

check("progressiveBlurOff" not in source, "the retired field name survived in the data source")

pending.append((SOURCE, source))

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
