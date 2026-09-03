#!/usr/bin/env python3
"""
r29c — the header's collapse stops recomposing the settings screen, and the blur's effect graph
stops being rebuilt every frame.

## What was actually costing frames

`HomeScreen` reads `headerOffsets[selectedIndex]` — snapshot state written by the nested-scroll
connection — turns it into `collapsedFraction`, and hands it down through
`compositionLocalOf { 0f }`. `SettingsScreen` reads it in `Success`'s body:

    .progressiveEdgeBlur(
        topSolid = LocalFloatingHeaderHeight.current,
        strength = LocalHeaderCollapse.current,
    )

A CompositionLocal read invalidates the nearest enclosing restartable scope, and that scope is
`Success` — **1,150 lines, 81 composable calls and 32 remembered slots.** So one drag of the
settings page re-executed the whole settings body at the scroll frame rate. Nothing about that is
fixed by splitting the file; it is fixed by not reading the value during composition.

⚠ **The fix is a stable holder behind a *static* local, not a smaller value behind the old one.**
`staticCompositionLocalOf` does not track reads, so providing it never invalidates anything; the
object's identity is fixed by a `remember` in `HomeScreen`, and the two numbers inside it are
snapshot state. Readers take the object in composition once and read the numbers **inside the draw
lambdas**, where a change invalidates draw alone.

`topSolid` and `strength` therefore become `() -> Dp` and `() -> Float`. That is the whole of the
churn in `SettingsScreen.kt`: two lines.

⚠ **The two app tabs keep their own per-frame recomposition, on purpose.** `AppsScreen` and
`FavouriteAppsScreen` also read `LocalFloatingHeaderHeight.current` for
`.padding(top = …)` on the search field, which genuinely has to move with the title — r11's bug was
pinning it. That is a layout read and it stays one. Their blur reads move anyway, so the two are
independent from here on and the padding can be deferred separately later without touching this.

⚠ **`LocalHeaderCollapse` is deleted, not left in place.** After this its reader count is zero, and
a live CompositionLocal that nothing reads is the next round's trap.

## The effect graph

`bandedBlurEffect` builds five `RenderEffect` nodes and a `LinearGradient` shader, and the comment
above it says it is *"built per draw … a handful of allocations against a frame that is about to
blur a screen"*. The allocations were never the point: handing the RenderNode a **new** effect
makes Skia rebuild the `ImageFilter` DAG and discard any cached filter result, so the blur is
recomputed from scratch instead of reused.

⚠ **The cache is exact-match, with no quantising of the radius, so the output is byte-identical.**
That is deliberate: rounding the radius would have raised the hit rate during the collapse itself
and changed pixels, and this file is not allowed to change pixels. It does not need to — `amount`
reaches 1 after the first ~88 dp of scroll and stays there, so radius is *constant* for the whole
rest of a scroll and every frame of it hits. The collapse frames miss and cost exactly what they
cost today. `bandStops` and the tint `Brush` are cached on the same principle.

## One behavioural difference, stated rather than hidden

The old code had `if (topSolid <= 0.dp && bottomSolid <= 0.dp) return this`, which needed
`topSolid` at composition time. With a lambda it cannot, so the guard moved inside the draw and
layer blocks: a caller passing neither band now gets a modifier node that draws nothing, where
before it got no node. **No call site passes neither band** — all three pass a header-derived
`topSolid` — so this is reachable only through the defaults.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAV = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoFloatingNavigation.kt"
BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"
HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"
SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
APPS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"
FAVOURITES = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def code(text: str) -> str:
    """The file with its comment lines removed — handover §8, the comment trap."""
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


def body_without_imports(text: str) -> str:
    """Counting a symbol to decide whether its import is needed counts the import — §8 again."""
    return "\n".join(
        line for line in code(text).splitlines() if not line.startswith("import ")
    )


# ================================================================ GetoFloatingNavigation.kt

nav = NAV.read_text(encoding="utf-8")

nav = replace_once(
    nav,
    "val LocalFloatingHeaderHeight = compositionLocalOf { GetoLargeTopBarHeight }\n",
    "val LocalFloatingHeaderHeight = compositionLocalOf { GetoLargeTopBarHeight }\n"
    "\n"
    "/**\n"
    " * The floating header's live geometry, as an object whose identity never changes.\n"
    " *\n"
    " * ⚠ **This exists so that a scroll does not recompose a page — r29.** Both numbers change on\n"
    " * every frame of a collapse. Handed down as values through `compositionLocalOf`, every reader\n"
    " * is invalidated every frame, and on the settings tab that reader was `Success`: eleven hundred\n"
    " * lines, eighty-one composable calls and thirty-two remembered slots, re-executed per frame for\n"
    " * two floats. Handed down as *this*, behind a [staticCompositionLocalOf] and pinned by a\n"
    " * `remember` in `HomeScreen`, nothing is invalidated by providing it at all; a page reads the\n"
    " * numbers inside its draw lambdas, where a change costs a redraw and not a recomposition.\n"
    " *\n"
    " * ⚠ **Read these inside a draw or layout lambda, never in a composable body.** Reading\n"
    " * [fraction] during composition puts the per-frame invalidation straight back, which is the\n"
    " * whole thing this replaced.\n"
    " */\n"
    "@Stable\n"
    "class HeaderMetrics {\n"
    "    /** How far the header has collapsed: 0 at the top of the page, 1 once the title is small. */\n"
    "    var fraction: Float by mutableFloatStateOf(0f)\n"
    "\n"
    "    /** How tall the header is right now, status bar included. */\n"
    "    var height: Dp by mutableStateOf(GetoLargeTopBarHeight)\n"
    "}\n"
    "\n"
    "/**\n"
    " * The one [HeaderMetrics] for the window, provided by `HomeScreen`, which owns the scroll.\n"
    " *\n"
    " * ⚠ **Static on purpose.** A non-static local would track every read and undo the point.\n"
    " */\n"
    "val LocalHeaderMetrics = staticCompositionLocalOf { HeaderMetrics() }\n",
    "nav: the holder after LocalFloatingHeaderHeight",
)

# The old value-carrying local, and its doc comment, go together.
nav = replace_once(
    nav,
    "/**\n"
    " * How far the floating header has collapsed: 0 at the top of the page, 1 once the title is small.\n"
    " *\n"
    " * ⚠ **The edge treatment fades in on this — r17.** Drawn at full strength from the moment a tab\n"
    " * opened, the band sat over the first rows of a page that had not been scrolled, which are not\n"
    " * under anything and have nothing to hide behind: the author's *\"it even shows over the topmost\n"
    " * contents when searchbar/header is expanded\"*. Tying it to the collapse means the treatment\n"
    " * arrives exactly as content starts to disappear beneath the chrome, and is absent while there is\n"
    " * nothing beneath it.\n"
    " *\n"
    " * Provided by `HomeScreen`, which owns the scroll. Zero everywhere else, including in a preview.\n"
    " */\n"
    "val LocalHeaderCollapse = compositionLocalOf { 0f }\n"
    "\n",
    "",
    "nav: LocalHeaderCollapse and its comment",
)

check(
    "LocalHeaderCollapse" not in nav,
    "nav: LocalHeaderCollapse survived",
)

for needed, symbol in (
    ("import androidx.compose.runtime.Stable\n", "Stable"),
    ("import androidx.compose.runtime.getValue\n", "getValue"),
    ("import androidx.compose.runtime.mutableFloatStateOf\n", "mutableFloatStateOf"),
    ("import androidx.compose.runtime.mutableStateOf\n", "mutableStateOf"),
    ("import androidx.compose.runtime.setValue\n", "setValue"),
    ("import androidx.compose.runtime.staticCompositionLocalOf\n", "staticCompositionLocalOf"),
):
    if needed not in nav:
        nav = replace_once(
            nav,
            "import androidx.compose.runtime.Composable\n",
            "import androidx.compose.runtime.Composable\n" + needed,
            f"nav: inserting the {symbol} import",
        )

# ⚠ getValue/setValue are required by `var x by mutableStateOf(…)` and never appear in the body —
# handover §8's delegate-imports trap. They are asserted as present, never as used.
for needed in (
    "import androidx.compose.runtime.Stable\n",
    "import androidx.compose.runtime.getValue\n",
    "import androidx.compose.runtime.mutableFloatStateOf\n",
    "import androidx.compose.runtime.mutableStateOf\n",
    "import androidx.compose.runtime.setValue\n",
    "import androidx.compose.runtime.staticCompositionLocalOf\n",
):
    check(nav.count(needed) == 1, f"nav: {needed.strip()} is not imported exactly once")

check(
    code(nav).count("class HeaderMetrics") == 1,
    "nav: HeaderMetrics did not land exactly once",
)

check(
    code(nav).count("val LocalHeaderMetrics = staticCompositionLocalOf { HeaderMetrics() }") == 1,
    "nav: LocalHeaderMetrics did not land exactly once",
)

# compositionLocalOf still has exactly one user here: the header height, which two pages read for
# layout and which is deliberately left alone.
check(
    body_without_imports(nav).count("compositionLocalOf { GetoLargeTopBarHeight }") == 1,
    "nav: LocalFloatingHeaderHeight was disturbed",
)

# ================================================================ ProgressiveBlur.kt

blur = BLUR.read_text(encoding="utf-8")

blur = replace_once(
    blur,
    "fun Modifier.progressiveEdgeBlur(\n"
    "    blur: Boolean,\n"
    "    topSolid: Dp = 0.dp,\n"
    "    bottomSolid: Dp = 0.dp,\n"
    "    strength: Float = 1f,\n"
    "): Modifier {\n",
    "fun Modifier.progressiveEdgeBlur(\n"
    "    blur: Boolean,\n"
    "    topSolid: () -> Dp = { 0.dp },\n"
    "    bottomSolid: Dp = 0.dp,\n"
    "    strength: () -> Float = { 1f },\n"
    "): Modifier {\n",
    "blur: the signature",
)

blur = replace_once(
    blur,
    "    if (topSolid <= 0.dp && bottomSolid <= 0.dp) return this\n"
    "\n"
    "    // ⚠ **Clamped, never branched on — r17.** The chain's *shape* stays the same at every value,\n"
    "    // so scrolling off the top does not add and remove a layer node on the frame the page starts\n"
    "    // moving. At zero the gradient is transparent and the render effect is null: present, and\n"
    "    // doing nothing.\n"
    "    val amount = strength.coerceIn(0f, 1f)\n"
    "\n",
    "    // ⚠ **Kept between frames — r29.** `bandStops`, the tint brush and the effect graph are all\n"
    "    // pure functions of numbers that stop moving the moment the header finishes collapsing, and\n"
    "    // the effect graph is the expensive one: handing the RenderNode a new `RenderEffect` makes\n"
    "    // Skia rebuild the filter DAG and throw away the result it had cached. Exact-match keys, no\n"
    "    // rounding of the radius — this file may not change a pixel — which is enough, because\n"
    "    // `amount` is 1 for every frame after the first ~88 dp of scroll.\n"
    "    val cache = remember { BandCache() }\n"
    "\n",
    "blur: the zero guard and the clamp",
)

blur = replace_once(
    blur,
    "    val faded = drawWithContent {\n"
    "        drawContent()\n"
    "\n"
    "        val height = size.height\n"
    "\n"
    "        if (height <= 0f) return@drawWithContent\n"
    "\n"
    "        val stops = bandStops(\n"
    "            topSolid = topSolid.toPx(),\n"
    "            bottomSolid = bottomSolid.toPx(),\n"
    "            fade = fadeLength.toPx(),\n"
    "            height = height,\n"
    "        )\n"
    "\n"
    "        drawRect(\n"
    "            brush = Brush.verticalGradient(\n"
    "                colorStops = Array(stops.size) { index ->\n"
    "                    val (position, strength) = stops[index]\n"
    "\n"
    "                    position to fade.copy(alpha = fade.alpha * strength * amount)\n"
    "                },\n"
    "                startY = 0f,\n"
    "                endY = height,\n"
    "            ),\n"
    "        )\n"
    "    }\n",
    "    val faded = drawWithContent {\n"
    "        drawContent()\n"
    "\n"
    "        val height = size.height\n"
    "\n"
    "        if (height <= 0f) return@drawWithContent\n"
    "\n"
    "        // ⚠ **Read here, not in the composable body — r29.** This is the deferral: the two\n"
    "        // numbers change every frame of a collapse, and reading them at this depth costs a\n"
    "        // redraw where reading them above cost the whole page a recomposition.\n"
    "        val top = topSolid().toPx()\n"
    "\n"
    "        val bottom = bottomSolid.toPx()\n"
    "\n"
    "        // The guard that used to sit above `faded` and return the chain unchanged. It cannot\n"
    "        // live there any more — `topSolid` is not a value until it is called — so it draws\n"
    "        // nothing instead of not existing. No caller passes neither band.\n"
    "        if (top <= 0f && bottom <= 0f) return@drawWithContent\n"
    "\n"
    "        // ⚠ **Clamped, never branched on — r17.** The chain's *shape* stays the same at every\n"
    "        // value, so scrolling off the top does not add and remove a layer node on the frame the\n"
    "        // page starts moving. At zero the gradient is transparent and the render effect is\n"
    "        // null: present, and doing nothing.\n"
    "        val amount = strength().coerceIn(0f, 1f)\n"
    "\n"
    "        val stops = cache.stops(\n"
    "            topSolid = top,\n"
    "            bottomSolid = bottom,\n"
    "            fade = fadeLength.toPx(),\n"
    "            height = height,\n"
    "        )\n"
    "\n"
    "        drawRect(brush = cache.brush(stops = stops, height = height, fade = fade, amount = amount))\n"
    "    }\n",
    "blur: the tint draw",
)

blur = replace_once(
    blur,
    "    return faded.graphicsLayer {\n"
    "        val height = size.height\n"
    "\n"
    "        val radius = blurRadius.toPx() * amount\n"
    "\n"
    "        // A zero-radius blur is not a no-op on every driver; some report an error rather than\n"
    "        // drawing the source unchanged, so below half a pixel there is simply no effect at all.\n"
    "        if (height <= 0f || radius < MINIMUM_BLUR_PX) {\n"
    "            renderEffect = null\n"
    "\n"
    "            return@graphicsLayer\n"
    "        }\n"
    "\n"
    "        renderEffect = bandedBlurEffect(\n"
    "            radius = radius,\n"
    "            stops = bandStops(\n"
    "                topSolid = topSolid.toPx(),\n"
    "                bottomSolid = bottomSolid.toPx(),\n"
    "                fade = fadeLength.toPx(),\n"
    "                height = height,\n"
    "            ),\n"
    "            height = height,\n"
    "        )\n"
    "\n"
    "        // The blur samples past the node's edges; clipping would put a hard line back.\n"
    "        clip = false\n"
    "    }\n",
    "    return faded.graphicsLayer {\n"
    "        val height = size.height\n"
    "\n"
    "        val top = topSolid().toPx()\n"
    "\n"
    "        val bottom = bottomSolid.toPx()\n"
    "\n"
    "        val amount = strength().coerceIn(0f, 1f)\n"
    "\n"
    "        val radius = blurRadius.toPx() * amount\n"
    "\n"
    "        // A zero-radius blur is not a no-op on every driver; some report an error rather than\n"
    "        // drawing the source unchanged, so below half a pixel there is simply no effect at all.\n"
    "        if (height <= 0f || radius < MINIMUM_BLUR_PX || (top <= 0f && bottom <= 0f)) {\n"
    "            renderEffect = null\n"
    "\n"
    "            return@graphicsLayer\n"
    "        }\n"
    "\n"
    "        renderEffect = cache.effect(\n"
    "            radius = radius,\n"
    "            stops = cache.stops(\n"
    "                topSolid = top,\n"
    "                bottomSolid = bottom,\n"
    "                fade = fadeLength.toPx(),\n"
    "                height = height,\n"
    "            ),\n"
    "            height = height,\n"
    "        )\n"
    "\n"
    "        // The blur samples past the node's edges; clipping would put a hard line back.\n"
    "        clip = false\n"
    "    }\n",
    "blur: the layer",
)

# The cache itself, immediately above the function that builds what it keeps.
blur = replace_once(
    blur,
    "/** Black at the given alpha, as the packed ARGB int a `LinearGradient` wants. */\n",
    "/**\n"
    " * What the last frame worked out, kept for the next one.\n"
    " *\n"
    " * ⚠ **One of these per modifier instance**, held by a `remember` inside\n"
    " * [progressiveEdgeBlur], and touched only from the draw and layer lambdas — which is to say\n"
    " * from the UI thread, one at a time. It is not thread-safe and does not need to be.\n"
    " *\n"
    " * ⚠ **Exact-match keys.** Rounding the radius would raise the hit rate through the collapse and\n"
    " * change what is drawn; nothing here is allowed to change what is drawn. It costs nothing to\n"
    " * refuse: past the collapse `amount` is 1, so the radius is constant and every frame hits, and\n"
    " * the geometry keys stop moving as soon as the page is laid out.\n"
    " *\n"
    " * ⚠ **`stops` is keyed by identity, not by value.** [stops] hands back the same list until its\n"
    " * inputs move, so `===` is both the cheap test and the correct one — a deep comparison of a\n"
    " * ten-element list of boxed pairs every frame would be most of what this is trying to save.\n"
    " */\n"
    "private class BandCache {\n"
    "    private var stopsTop = Float.NaN\n"
    "\n"
    "    private var stopsBottom = Float.NaN\n"
    "\n"
    "    private var stopsFade = Float.NaN\n"
    "\n"
    "    private var stopsHeight = Float.NaN\n"
    "\n"
    "    private var stopsValue: List<Pair<Float, Float>> = emptyList()\n"
    "\n"
    "    // NaN never equals itself, so the first call through each of these always misses.\n"
    "    fun stops(\n"
    "        topSolid: Float,\n"
    "        bottomSolid: Float,\n"
    "        fade: Float,\n"
    "        height: Float,\n"
    "    ): List<Pair<Float, Float>> {\n"
    "        if (topSolid != stopsTop || bottomSolid != stopsBottom ||\n"
    "            fade != stopsFade || height != stopsHeight\n"
    "        ) {\n"
    "            stopsTop = topSolid\n"
    "\n"
    "            stopsBottom = bottomSolid\n"
    "\n"
    "            stopsFade = fade\n"
    "\n"
    "            stopsHeight = height\n"
    "\n"
    "            stopsValue = bandStops(\n"
    "                topSolid = topSolid,\n"
    "                bottomSolid = bottomSolid,\n"
    "                fade = fade,\n"
    "                height = height,\n"
    "            )\n"
    "        }\n"
    "\n"
    "        return stopsValue\n"
    "    }\n"
    "\n"
    "    private var brushStops: List<Pair<Float, Float>>? = null\n"
    "\n"
    "    private var brushHeight = Float.NaN\n"
    "\n"
    "    private var brushAmount = Float.NaN\n"
    "\n"
    "    private var brushFade = Color.Unspecified\n"
    "\n"
    "    private var brushValue: Brush? = null\n"
    "\n"
    "    fun brush(\n"
    "        stops: List<Pair<Float, Float>>,\n"
    "        height: Float,\n"
    "        fade: Color,\n"
    "        amount: Float,\n"
    "    ): Brush {\n"
    "        val held = brushValue\n"
    "\n"
    "        if (held != null && stops === brushStops && height == brushHeight &&\n"
    "            amount == brushAmount && fade == brushFade\n"
    "        ) {\n"
    "            return held\n"
    "        }\n"
    "\n"
    "        brushStops = stops\n"
    "\n"
    "        brushHeight = height\n"
    "\n"
    "        brushAmount = amount\n"
    "\n"
    "        brushFade = fade\n"
    "\n"
    "        val built = Brush.verticalGradient(\n"
    "            colorStops = Array(stops.size) { index ->\n"
    "                val (position, strength) = stops[index]\n"
    "\n"
    "                position to fade.copy(alpha = fade.alpha * strength * amount)\n"
    "            },\n"
    "            startY = 0f,\n"
    "            endY = height,\n"
    "        )\n"
    "\n"
    "        brushValue = built\n"
    "\n"
    "        return built\n"
    "    }\n"
    "\n"
    "    private var effectRadius = Float.NaN\n"
    "\n"
    "    private var effectStops: List<Pair<Float, Float>>? = null\n"
    "\n"
    "    private var effectHeight = Float.NaN\n"
    "\n"
    "    private var effectValue: RenderEffect? = null\n"
    "\n"
    "    @RequiresApi(Build.VERSION_CODES.S)\n"
    "    fun effect(\n"
    "        radius: Float,\n"
    "        stops: List<Pair<Float, Float>>,\n"
    "        height: Float,\n"
    "    ): RenderEffect {\n"
    "        val held = effectValue\n"
    "\n"
    "        if (held != null && radius == effectRadius && stops === effectStops &&\n"
    "            height == effectHeight\n"
    "        ) {\n"
    "            return held\n"
    "        }\n"
    "\n"
    "        effectRadius = radius\n"
    "\n"
    "        effectStops = stops\n"
    "\n"
    "        effectHeight = height\n"
    "\n"
    "        val built = bandedBlurEffect(radius = radius, stops = stops, height = height)\n"
    "\n"
    "        effectValue = built\n"
    "\n"
    "        return built\n"
    "    }\n"
    "}\n"
    "\n"
    "/** Black at the given alpha, as the packed ARGB int a `LinearGradient` wants. */\n",
    "blur: the cache class",
)

# The old comment on bandedBlurEffect claimed it was built per draw on purpose. It is not any more.
blur = replace_once(
    blur,
    " * Built per draw rather than cached, because it depends on the node's height and on both bands; it\n"
    " * is a handful of allocations against a frame that is about to blur a screen.\n",
    " * ⚠ **Cached by [BandCache] since r29, and the allocations were never the reason.** Handing the\n"
    " * RenderNode a new `RenderEffect` makes Skia rebuild the filter DAG and discard the result it had\n"
    " * cached, so an identical graph rebuilt every frame is a screen-sized blur recomputed every frame.\n"
    " * Everything below is still a pure function of its three arguments, which is what makes it\n"
    " * cacheable at all — keep it that way.\n",
    "blur: the bandedBlurEffect comment",
)

for needed, anchor in (
    ("import androidx.compose.runtime.remember\n", "import androidx.compose.runtime.Composable\n"),
    ("import androidx.compose.ui.graphics.Color\n", "import androidx.compose.ui.graphics.Brush\n"),
):
    if needed not in blur:
        blur = replace_once(blur, anchor, anchor + needed, f"blur: inserting {needed.strip()}")

for needed in (
    "import androidx.compose.runtime.remember\n",
    "import androidx.compose.ui.graphics.Color\n",
):
    check(blur.count(needed) == 1, f"blur: {needed.strip()} is not imported exactly once")

blur_body = body_without_imports(blur)

check(
    blur_body.count("bandedBlurEffect(") == 2,
    f"blur: bandedBlurEffect referenced {blur_body.count('bandedBlurEffect(')}x, expected 2 "
    "(the declaration and the one call inside the cache)",
)

check(
    blur_body.count("bandStops(") == 2,
    f"blur: bandStops referenced {blur_body.count('bandStops(')}x, expected 2 "
    "(the declaration and the one call inside the cache)",
)

check(
    blur_body.count("topSolid()") == 2 and blur_body.count("strength()") == 2,
    "blur: topSolid()/strength() are not each called exactly twice — once per lambda",
)

check(
    "val amount = strength.coerceIn" not in blur_body,
    "blur: the composition-time clamp survived",
)

check(
    "if (topSolid <= 0.dp" not in blur_body,
    "blur: the composition-time zero guard survived",
)

check(
    blur_body.count("class BandCache") == 1 and blur_body.count("remember { BandCache() }") == 1,
    "blur: the cache is not declared once and remembered once",
)

# ================================================================ HomeScreen.kt

home = HOME.read_text(encoding="utf-8")

home = replace_once(
    home,
    "    CompositionLocalProvider(\n"
    "        LocalFloatingHeaderHeight provides headerHeight,\n"
    "        LocalHeaderCollapse provides collapsedFraction,\n"
    "    ) {\n",
    "    // ⚠ **Pinned by `remember`, written in a `SideEffect` — r29.** The object must outlive every\n"
    "    // recomposition or a page's reference goes stale, and the two numbers must be written after\n"
    "    // the composition that produced them rather than during it. Writing them here rather than\n"
    "    // providing them as values is what stops a scroll invalidating every page that reads them.\n"
    "    val headerMetrics = remember { HeaderMetrics() }\n"
    "\n"
    "    SideEffect {\n"
    "        headerMetrics.fraction = collapsedFraction\n"
    "\n"
    "        headerMetrics.height = headerHeight\n"
    "    }\n"
    "\n"
    "    CompositionLocalProvider(\n"
    "        // Still a value, and still read during composition by the two app tabs: their search\n"
    "        // field is laid out against it and has to move with the title. That is a layout read,\n"
    "        // not a draw one, and it is left alone.\n"
    "        LocalFloatingHeaderHeight provides headerHeight,\n"
    "        LocalHeaderMetrics provides headerMetrics,\n"
    "    ) {\n",
    "home: the provider",
)

home = replace_once(
    home,
    "import com.android.geto.designsystem.component.LocalHeaderCollapse\n",
    "import com.android.geto.designsystem.component.HeaderMetrics\n"
    "import com.android.geto.designsystem.component.LocalHeaderMetrics\n",
    "home: the LocalHeaderCollapse import",
)

# ⚠ After the import edit, not before — handover §8, ordering. Checked first, this passes only
# because the import line itself is still there to be found.
check(
    "LocalHeaderCollapse" not in home,
    "home: LocalHeaderCollapse survived",
)

for needed, anchor in (
    ("import androidx.compose.runtime.SideEffect\n", "import androidx.compose.runtime.Composable\n"),
    ("import androidx.compose.runtime.remember\n", "import androidx.compose.runtime.Composable\n"),
):
    if needed not in home:
        home = replace_once(home, anchor, anchor + needed, f"home: inserting {needed.strip()}")

for needed in (
    "import androidx.compose.runtime.SideEffect\n",
    "import androidx.compose.runtime.remember\n",
    "import com.android.geto.designsystem.component.HeaderMetrics\n",
    "import com.android.geto.designsystem.component.LocalHeaderMetrics\n",
):
    check(home.count(needed) == 1, f"home: {needed.strip()} is not imported exactly once")

# collapsedFraction still drives the title itself; only the way it is handed onward changed.
# The title still animates off it; only the way it is handed to other pages changed. Eight, not
# seven: `collapsedFraction = collapsedFraction,` at the CollapsingTitle call is two of them.
check(
    body_without_imports(home).count("collapsedFraction") == 8,
    f"home: collapsedFraction used {body_without_imports(home).count('collapsedFraction')}x, expected 8",
)

# ================================================================ the three call sites

settings = SETTINGS.read_text(encoding="utf-8")

settings = replace_once(
    settings,
    "            .progressiveEdgeBlur(\n"
    "                blur = userData.progressiveBlur,\n"
    "                topSolid = LocalFloatingHeaderHeight.current,\n"
    "                strength = LocalHeaderCollapse.current,\n"
    "            )\n",
    "            // ⚠ **Lambdas, and that is the whole of r29's change to this file.** Read as values\n"
    "            // here, the header's collapse invalidated `Success` on every frame of a scroll.\n"
    "            .progressiveEdgeBlur(\n"
    "                blur = userData.progressiveBlur,\n"
    "                topSolid = { headerMetrics.height },\n"
    "                strength = { headerMetrics.fraction },\n"
    "            )\n",
    "settings: the blur call",
)

# ⚠ Declared where the old locals were read, not at the top of `Success`: this is the object, so
# reading it in composition is free, but it still has to be in scope at the call.
settings = replace_once(
    settings,
    "    // ⚠ **The Column below is not re-indented, and that is deliberate.** It is four hundred lines\n",
    "    // Free to read here: `LocalHeaderMetrics` is static, so this line is not a subscription to\n"
    "    // anything — the numbers inside it are read in the draw lambdas below.\n"
    "    val headerMetrics = LocalHeaderMetrics.current\n"
    "\n"
    "    // ⚠ **The Column below is not re-indented, and that is deliberate.** It is four hundred lines\n",
    "settings: the metrics read",
)

settings = replace_once(
    settings,
    "import com.android.geto.designsystem.component.LocalHeaderCollapse\n",
    "import com.android.geto.designsystem.component.LocalHeaderMetrics\n",
    "settings: the LocalHeaderCollapse import",
)

check("LocalHeaderCollapse" not in settings, "settings: LocalHeaderCollapse survived")

check(
    body_without_imports(settings).count("LocalHeaderMetrics.current") == 1,
    "settings: LocalHeaderMetrics is not read exactly once",
)

check(
    body_without_imports(settings).count("headerMetrics") == 3,
    "settings: headerMetrics is not used 3x (the read, topSolid, strength)",
)

# ⚠ Asserted after the edit that orphaned it, not before — handover §8, ordering. The settings tab
# has no search field, so nothing else on it wanted the header height.
check(
    "LocalFloatingHeaderHeight" not in body_without_imports(settings),
    "settings: something still reads LocalFloatingHeaderHeight during composition",
)

settings = replace_once(
    settings,
    "import com.android.geto.designsystem.component.LocalFloatingHeaderHeight\n",
    "",
    "settings: the now-orphaned LocalFloatingHeaderHeight import",
)

for path, label in ((APPS, "apps"), (FAVOURITES, "favourites")):
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "            topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,\n"
        "            strength = LocalHeaderCollapse.current,\n"
        if label == "favourites" else
        "                    topSolid = LocalFloatingHeaderHeight.current + GetoSearchFieldHeight,\n"
        "                    strength = LocalHeaderCollapse.current,\n",
        "            topSolid = { headerMetrics.height + GetoSearchFieldHeight },\n"
        "            strength = { headerMetrics.fraction },\n"
        if label == "favourites" else
        "                    topSolid = { headerMetrics.height + GetoSearchFieldHeight },\n"
        "                    strength = { headerMetrics.fraction },\n",
        f"{label}: the blur call",
    )

    text = replace_once(
        text,
        "import com.android.geto.designsystem.component.LocalHeaderCollapse\n",
        "import com.android.geto.designsystem.component.LocalHeaderMetrics\n",
        f"{label}: the LocalHeaderCollapse import",
    )

    # ⚠ **The object has to be declared, and it is easy to forget it is not.** Swapping
    # `LocalHeaderCollapse.current` for `headerMetrics.fraction` at the call site reads like a
    # rename, but the old spelling carried its own lookup and the new one does not — without this
    # line `headerMetrics` resolves to nothing and the module does not compile. Neither
    # check_symbol_imports nor check_local_scope catches it: the first looks for cross-package
    # names with no import, the second for names used outside the function that declares them, and
    # a name declared *nowhere* is neither. Caught by the orphaned `LocalHeaderMetrics` import it
    # leaves behind.
    text = replace_once(
        text,
        "    val headerInset = getoFloatingHeaderInset()\n",
        "    // Free to read here: LocalHeaderMetrics is static, so this is not a subscription to\n"
        "    // anything — the numbers inside it are read in the blur's draw lambdas below.\n"
        "    val headerMetrics = LocalHeaderMetrics.current\n"
        "\n"
        "    val headerInset = getoFloatingHeaderInset()\n",
        f"{label}: the metrics read",
    )

    check(
        body_without_imports(text).count("LocalHeaderMetrics.current") == 1,
        f"{label}: LocalHeaderMetrics is not read exactly once",
    )

    check(
        body_without_imports(text).count("headerMetrics") == 3,
        f"{label}: headerMetrics used "
        f"{body_without_imports(text).count('headerMetrics')}x, expected 3 "
        "(the declaration, topSolid, strength)",
    )

    check(f"LocalHeaderCollapse" not in text, f"{label}: LocalHeaderCollapse survived")

    # ⚠ Left in place on purpose: the search field's padding is a layout read of the live height,
    # which is r11's fix and must stay a composition read.
    check(
        body_without_imports(text).count("LocalFloatingHeaderHeight.current") == 1,
        f"{label}: the search field's header-height read was disturbed",
    )

    globals()[f"_{label}_text"] = text

# ================================================================ write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in (
    (NAV, nav),
    (BLUR, blur),
    (HOME, home),
    (SETTINGS, settings),
    (APPS, globals()["_apps_text"]),
    (FAVOURITES, globals()["_favourites_text"]),
):
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
