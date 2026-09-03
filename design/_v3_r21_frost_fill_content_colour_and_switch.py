#!/usr/bin/env python3
"""
r21 — three faults from r20, all of them mine.

  1. **Black text on the manager when it is opened over another app.** `Surface` derives its
     content colour from its container colour with `contentColorFor`, which only knows the scheme's
     own tokens. r20 started passing `containerColor.copy(alpha = …)` — a colour no longer in the
     scheme — so the lookup returned Unspecified, `Surface` fell back to `LocalContentColor`, and
     outside a themed host that is black. The content colour is now derived from the **unmodified**
     container colour and passed explicitly, which is what should have happened the moment the
     colour started being adjusted.

  2. **The card went translucent but never frosted.** Two reasons, and the second is the one that
     mattered:

       * The window background was painted at an alpha of 1/255 on the theory that the blur only
         needs the region to be *painted*. It needs more than that: the blur region is taken from
         the background drawable's **outline**, and `GradientDrawable` reports its outline alpha
         from its own fill — so a 0.4 %-opaque fill asks for a 0.4 %-strength blur. The drawable
         now carries the card's whole fill at the tint the slider sets, and the Compose `Surface`
         goes transparent instead of painting over it. One layer, not two.
       * The card was made translucent on the strength of *asking* for a blur rather than of
         getting one. On a device or in a battery mode where cross-window blur is off, that left a
         see-through card with nothing behind it. The colour now follows what actually applied.

  3. **The off switch was invisible in OLED mode.** r18 put its track on
     `surfaceContainerLowest`, which the OLED transform takes to pure black — on a black page an
     off switch became a hole. `surfaceContainerHigh` is a rung the OLED mode leaves alone and one
     below the settings card it sits on, so it reads as a recess against every background the app
     has.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"

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


# ------------------------------------------------------------ 1 & 2. the dialog

dialog = DIALOG.read_text(encoding="utf-8")

dialog = swap(
    dialog,
    """    var bounds by remember { mutableStateOf(IntRect.Zero) }
""",
    """    var bounds by remember { mutableStateOf(IntRect.Zero) }

    // ⚠ **What actually happened, not what was asked for.** The system turns cross-window blur off
    // under battery saver and on devices that cannot afford it, and a request made then is ignored
    // rather than refused. r20 made the card translucent on the strength of the request, which on
    // such a device left a see-through card with nothing behind it.
    var applied by remember { mutableStateOf(false) }
""",
    "dialog: applied state",
)

dialog = swap(
    dialog,
    """        applyWindowFrost(
            window = window,
            context = view.context,
            card = bounds,
            windowWidth = view.width,
            windowHeight = view.height,
            corner = corner,
            radius = with(density) { radius.dp.roundToPx() },
            active = active && !bounds.isEmpty,
        )""",
    """        applied = applyWindowFrost(
            window = window,
            context = view.context,
            card = bounds,
            windowWidth = view.width,
            windowHeight = view.height,
            corner = corner,
            fill = fill.toArgb(),
            radius = with(density) { radius.dp.roundToPx() },
            active = active && !bounds.isEmpty,
        )""",
    "dialog: apply call",
)

dialog = swap(
    dialog,
    """    return FrostedWindow(
        active = active,
        tintAlpha = settings.tintAlpha,
        measure = if (active) {
            Modifier.onGloballyPositioned { bounds = it.boundsInWindow().roundToIntRect() }
        } else {
            Modifier
        },
    )
}""",
    """    return FrostedWindow(
        frosted = applied,
        content = contentColour,
        measure = if (active) {
            Modifier.onGloballyPositioned { bounds = it.boundsInWindow().roundToIntRect() }
        } else {
            Modifier
        },
    )
}""",
    "dialog: return",
)

dialog = swap(
    dialog,
    """    val corner = with(density) {""",
    """    // ⚠ **The card's whole fill, and it lives in the *drawable* now.** The blur region comes from
    // the background drawable's outline, and `GradientDrawable` reports that outline's alpha from
    // its own fill — so r20's 1/255 asked for a blur at 0.4 % strength. This is the card, painted
    // once, with the blurred page behind it; the Compose Surface on top goes transparent rather
    // than painting over the thing it is meant to be showing.
    val fill = containerColour.copy(
        alpha = FROSTED_MIN_ALPHA + (1f - FROSTED_MIN_ALPHA) * settings.tintAlpha,
    )

    val corner = with(density) {""",
    "dialog: fill",
)

dialog = swap(
    dialog,
    """private fun rememberFrostedWindow(
    enabled: Boolean,
    shape: Shape = AlertDialogDefaults.shape,
): FrostedWindow {""",
    """private fun rememberFrostedWindow(
    enabled: Boolean,
    containerColour: Color,
    shape: Shape = AlertDialogDefaults.shape,
): FrostedWindow {
    // ⚠ **Derived from the *unmodified* container colour, and passed on explicitly.** `Surface`
    // works its content colour out with `contentColorFor`, which only recognises the scheme's own
    // tokens; hand it an adjusted one — which r20 did — and it answers Unspecified, falls back to
    // `LocalContentColor`, and outside a themed host that is black. Which is exactly what the
    // author saw the moment he opened the manager over somebody else's app.
    val contentColour = MaterialTheme.colorScheme.contentColorFor(containerColour)
        .takeOrElse { MaterialTheme.colorScheme.onSurface }
""",
    "dialog: content colour",
)

# ⚠ **A leading newline on every anchor.** The flat and capped calls are the same words at two
# indents, and the shallower one is a *substring* of the deeper one — twelve spaces plus the text
# appear inside sixteen spaces plus the text. Anchoring from the line break is what makes each of
# them match only itself.
for old, new, label in (
    ("\n            val frost = rememberFrostedWindow(frostedWindow)",
     "\n            val frost = rememberFrostedWindow(\n"
     "                frostedWindow,\n"
     "                containerColour = containerColor,\n"
     "            )",
     "dialog: full-screen call"),
    ("\n            val frost = rememberFrostedWindow(frostedWindow, shape = shape)",
     "\n            val frost = rememberFrostedWindow(\n"
     "                frostedWindow,\n"
     "                containerColour = containerColor,\n"
     "                shape = shape,\n"
     "            )",
     "dialog: flat call"),
    ("\n                val frost = rememberFrostedWindow(frostedWindow, shape = shape)",
     "\n                val frost = rememberFrostedWindow(\n"
     "                    frostedWindow,\n"
     "                    containerColour = containerColor,\n"
     "                    shape = shape,\n"
     "                )",
     "dialog: capped call"),
):
    dialog = swap(dialog, old, new, label)

dialog = swap(
    dialog,
    """private class FrostedWindow(
    // ⚠ **Plain `val`s, no `private`, no `@Immutable`.** `private` on a constructor property of a
    // private class buys nothing, and `@Immutable` on a class holding a `Modifier` is a promise
    // this cannot keep. Both also confused tools/check9_arity into reading the constructor as
    // taking one parameter.
    val active: Boolean,
    val tintAlpha: Float,
    val measure: Modifier,
) {""",
    """private class FrostedWindow(
    // ⚠ **Plain `val`s, no `private`.** `private` on a constructor property of a private class
    // buys nothing, and it confused tools/check9_arity into reading the constructor as taking one
    // parameter.
    val frosted: Boolean,
    val content: Color,
    val measure: Modifier,
) {""",
    "dialog: holder",
)

dialog = swap(
    dialog,
    """    /**
     * The card's colour, translucent while frosted.
     *
     * Between [FROSTED_MIN_ALPHA] and 1: the slider decides where in that range, and the floor is
     * what keeps a settings card readable over somebody else's app.
     */
    fun colour(container: Color): Color = if (active) {
        container.copy(alpha = FROSTED_MIN_ALPHA + (1f - FROSTED_MIN_ALPHA) * tintAlpha)
    } else {
        container
    }""",
    """    /**
     * The card's colour.
     *
     * ⚠ **Transparent while frosted, because the fill is the window's background drawable.** Two
     * translucent layers over each other is a colour nobody can predict; one is the card.
     */
    fun colour(container: Color): Color = if (frosted) Color.Transparent else container""",
    "dialog: colour",
)

dialog = swap(
    dialog,
    """    corner: Float,
    radius: Int,
    active: Boolean,
) {
    val supported = context.getSystemService(WindowManager::class.java)
        ?.isCrossWindowBlurEnabled == true

    if (!active || !supported || windowWidth <= 0 || windowHeight <= 0) {
        window.setBackgroundBlurRadius(0)

        window.setBackgroundDrawable(ColorDrawable(Color.Transparent.toArgb()))

        return
    }""",
    """    corner: Float,
    fill: Int,
    radius: Int,
    active: Boolean,
): Boolean {
    val supported = context.getSystemService(WindowManager::class.java)
        ?.isCrossWindowBlurEnabled == true

    if (!active || !supported || windowWidth <= 0 || windowHeight <= 0) {
        window.setBackgroundBlurRadius(0)

        window.setBackgroundDrawable(ColorDrawable(Color.Transparent.toArgb()))

        return false
    }""",
    "dialog: apply signature",
)

dialog = swap(
    dialog,
    """        // ⚠ **Nearly transparent, not transparent.** The blur is only drawn where the background
        // is painted, and a fully transparent pixel is not painted at all — so this is the
        // smallest alpha that still counts as paint. The card's real colour is the Compose
        // Surface on top of it.
        setColor(FROSTED_DRAWABLE_ALPHA shl ALPHA_SHIFT)""",
    """        // The card itself. See the note beside `fill` for why this is not a hairline alpha.
        setColor(fill)""",
    "dialog: drawable fill",
)

dialog = swap(
    dialog,
    """    window.setBackgroundBlurRadius(radius)
}""",
    """    window.setBackgroundBlurRadius(radius)

    return true
}""",
    "dialog: apply return",
)

dialog = swap(
    dialog,
    """/** See the comment beside it: the least paint that still counts as painted. */
private const val FROSTED_DRAWABLE_ALPHA = 1

private const val ALPHA_SHIFT = 24
""",
    "",
    "dialog: dead constants",
)

for old, new, label in (
    ("color = frost.colour(containerColor),\n                tonalElevation = tonalElevation,\n            ) {",
     "color = frost.colour(containerColor),\n                contentColor = frost.content,\n                tonalElevation = tonalElevation,\n            ) {",
     "dialog: full-screen content colour"),
    ("color = frost.colour(containerColor),\n                tonalElevation = tonalElevation,\n                content = content,",
     "color = frost.colour(containerColor),\n                contentColor = frost.content,\n                tonalElevation = tonalElevation,\n                content = content,",
     "dialog: flat content colour"),
    ("                    color = frost.colour(containerColor),\n                    tonalElevation = tonalElevation,",
     "                    color = frost.colour(containerColor),\n                    contentColor = frost.content,\n                    tonalElevation = tonalElevation,",
     "dialog: capped content colour"),
):
    dialog = swap(dialog, old, new, label)

dialog = swap(
    dialog,
    "import androidx.compose.material3.AlertDialogDefaults\n",
    "import androidx.compose.material3.AlertDialogDefaults\n"
    "import androidx.compose.material3.MaterialTheme\n"
    "import androidx.compose.material3.contentColorFor\n",
    "dialog: material imports",
)

dialog = swap(
    dialog,
    "import androidx.compose.ui.graphics.Color\n",
    "import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.graphics.takeOrElse\n",
    "dialog: takeOrElse import",
)

check("FROSTED_DRAWABLE_ALPHA" not in dialog, "the hairline-alpha constant survived")

check("ALPHA_SHIFT" not in dialog, "ALPHA_SHIFT survived in the dialog")

pending.append((DIALOG, dialog))

# ------------------------------------------------------------ 3. the off switch

toggles = TOGGLES.read_text(encoding="utf-8")

toggles = swap(
    toggles,
    """        // ⚠ **The *darkest* container, with a rim — r18, undoing r17b.** r17b reached for
        // `surfaceContainerHighest` in the same round that made the settings card
        // `surfaceContainerHighest`, so an off switch and the card behind it became the same
        // colour and the track disappeared: the author was left looking at a pale disc floating
        // on a card. An off track reads as a recess, not a raised patch, so it goes below
        // whatever it sits on and takes an outline — which is Material's own answer too.
        enabled -> scheme.surfaceContainerLowest
        else -> scheme.surfaceContainerLowest.copy(alpha = 0.45f)""",
    """        // ⚠ **One rung below the card, not the bottom of the ladder — r21.** An off track has to
        // read as a recess, which is why it goes below whatever it sits on; but r18 sent it to
        // `surfaceContainerLowest`, and the OLED transform takes that one to pure black. On a
        // black page an off switch stopped being a recess and became a hole — the author's
        // *"they become see through"*. `surfaceContainerHigh` is a rung OLED mode leaves alone
        // and still sits under the `surfaceContainerHighest` settings card, with the rim below
        // doing the rest.
        enabled -> scheme.surfaceContainerHigh
        else -> scheme.surfaceContainerHigh.copy(alpha = 0.45f)""",
    "toggles: off track",
)

pending.append((TOGGLES, toggles))

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
