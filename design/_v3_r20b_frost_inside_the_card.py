#!/usr/bin/env python3
"""
r20b — the frost moves inside the settings manager's own card.

r19 used `FLAG_BLUR_BEHIND`, which blurs everything behind the *window* — and a Compose dialog's
window is the whole screen, so the whole screen frosted. The author's answer: *"i need the blur
inside within the settings manager window BG, keep outside BG as it was"*.

The right API is the other one: **`Window.setBackgroundBlurRadius`**, which blurs only where the
window's own *background drawable* is drawn, and respects that drawable's outline. So the window
background stops being a transparent nothing and becomes a rounded rectangle the exact size and
shape of the card — an `InsetDrawable` whose insets are computed from the card's measured bounds —
and the blur lands inside it and nowhere else. The card's own Compose `Surface` goes translucent
in the same breath, or it would paint over the very thing it is meant to be showing.

⚠ **Three things have to agree or this looks broken rather than frosted**: the drawable's corner
radius and the Surface's shape, the drawable's alpha and the Surface's alpha, and the insets and
the card's position. All three are derived from one measurement here rather than written down
twice.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


dialog = DIALOG.read_text(encoding="utf-8")

# ------------------------------------------------------------ 1. the parameter says what it does

dialog = swap(
    dialog,
    """    /**
     * Frost the page behind this window while the Progressive UI blur switch is on.
     *
     * ⚠ **Opt-in, and so far one dialog opts in** — the settings manager, at the author's
     * request. Off elsewhere because a frosted backdrop is a statement that *this* window is the
     * subject and the app behind it is not, which is true of the manager and not of, say, a sort
     * order picker.
     */
    frostedBackdrop: Boolean = false,""",
    """    /**
     * Make this dialog's card frosted glass while the Progressive UI blur switch is on: the page
     * shows through it, blurred, and the page **around** it is left exactly as it was.
     *
     * ⚠ **Opt-in, and so far one dialog opts in** — the settings manager, at the author's
     * request. Off elsewhere because a frosted card is a statement that *this* window is the
     * subject and the app behind it is not, which is true of the manager and not of, say, a sort
     * order picker.
     */
    frostedWindow: Boolean = false,""",
    "dialog: parameter",
)

# ------------------------------------------------------------ 2. every Surface takes the frost

dialog = swap(
    dialog,
    "            FrostedBackdrop(enabled = frostedBackdrop && LocalProgressiveBlur.current)\n\n"
    """            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize(),
                color = containerColor,
                tonalElevation = tonalElevation,
            ) {""",
    """            val frost = rememberFrostedWindow(frostedWindow)

            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize()
                    .then(frost.measure),
                color = frost.colour(containerColor),
                tonalElevation = tonalElevation,
            ) {""",
    "dialog: full-screen surface",
)

dialog = swap(
    dialog,
    "            FrostedBackdrop(enabled = frostedBackdrop && LocalProgressiveBlur.current)\n\n"
    """            Surface(
                modifier = modifier,
                shape = shape,
                color = containerColor,
                tonalElevation = tonalElevation,
                content = content,
            )""",
    """            val frost = rememberFrostedWindow(frostedWindow, shape = shape)

            Surface(
                modifier = modifier.then(frost.measure),
                shape = shape,
                color = frost.colour(containerColor),
                tonalElevation = tonalElevation,
                content = content,
            )""",
    "dialog: flat surface",
)

dialog = swap(
    dialog,
    "                FrostedBackdrop(enabled = frostedBackdrop && LocalProgressiveBlur.current)\n\n                Surface(",
    "                val frost = rememberFrostedWindow(frostedWindow, shape = shape)\n\n                Surface(",
    "dialog: capped surface",
)

# The capped Surface's own colour and modifier, which the swap above deliberately left alone so
# that its long comment did not have to be repeated here.
dialog = swap(
    dialog,
    """                    shape = shape,
                    color = containerColor,
                    tonalElevation = tonalElevation,""",
    """                    shape = shape,
                    color = frost.colour(containerColor),
                    tonalElevation = tonalElevation,""",
    "dialog: capped surface colour",
)

check(
    "frostedBackdrop" not in dialog,
    "a frostedBackdrop reference survived",
)

# ------------------------------------------------------------ 3. the mechanism

OLD_MECHANISM_START = "/**\n * Blurs whatever is behind this dialog's window."

start = dialog.index(OLD_MECHANISM_START)

dialog = dialog[:start].rstrip() + "\n"

dialog += '''
/**
 * The frosted-card state: a modifier that measures the card, and the colour it should be drawn in.
 *
 * ⚠ **`setBackgroundBlurRadius`, not `FLAG_BLUR_BEHIND` — r20b, and the difference is the whole
 * point.** Blur-behind frosts everything behind the *window*, and a Compose dialog's window is the
 * whole screen, which is what r19 shipped and what the author asked to be taken back:
 * *"keep outside BG as it was"*. Background blur frosts only where the window's own background
 * drawable is painted, and respects that drawable's outline — so a drawable shaped and placed like
 * the card confines the blur to the card.
 *
 * ⚠ **The drawable is an [InsetDrawable] built from the card's measured bounds**, because the
 * window stays full-screen. Insetting a rounded rectangle to the card's rect is what turns a
 * screen-sized background into a card-sized one without touching the window's layout — and the
 * window's layout is not something to touch, having already cost two rounds of width bugs.
 *
 * ⚠ **The card goes translucent at the same time**, at the tint the user's slider sets. An opaque
 * Surface would paint over the blurred pixels the drawable is there to reveal; that is why the
 * colour and the measurement come back together from one call rather than being arranged twice.
 * The alpha runs the other way from the slider on purpose — more tint is a more solid card — and
 * it never reaches transparent, which is the author's *"we need the contents to be legible"*.
 */
@Composable
private fun rememberFrostedWindow(
    enabled: Boolean,
    shape: Shape = AlertDialogDefaults.shape,
): FrostedWindow {
    val settings = LocalBlurSettings.current

    val active = enabled && settings.enabled && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S

    val view = LocalView.current

    val density = LocalDensity.current

    var bounds by remember { mutableStateOf(IntRect.Zero) }

    val radius = (settings.radiusDp * WINDOW_RADIUS_FACTOR)

    val corner = with(density) {
        (shape as? RoundedCornerShape)
            ?.topStart
            ?.toPx(Size(bounds.width.toFloat(), bounds.height.toFloat()), density)
            ?: FROSTED_FALLBACK_CORNER.toPx()
    }

    LaunchedEffect(view, active, bounds, radius, corner) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return@LaunchedEffect

        // Null on the flat path, which draws into the page rather than into a window of its own.
        val window = (view.parent as? DialogWindowProvider)?.window ?: return@LaunchedEffect

        applyWindowFrost(
            window = window,
            context = view.context,
            card = bounds,
            windowWidth = view.width,
            windowHeight = view.height,
            corner = corner,
            radius = with(density) { radius.dp.roundToPx() },
            active = active && !bounds.isEmpty,
        )
    }

    return FrostedWindow(
        active = active,
        tintAlpha = settings.tintAlpha,
        measure = if (active) {
            Modifier.onGloballyPositioned { bounds = it.boundsInWindow().roundToIntRect() }
        } else {
            Modifier
        },
    )
}

/** What [rememberFrostedWindow] hands back: how to measure the card, and how to paint it. */
@Immutable
private class FrostedWindow(
    private val active: Boolean,
    private val tintAlpha: Float,
    val measure: Modifier,
) {
    /**
     * The card's colour, translucent while frosted.
     *
     * Between [FROSTED_MIN_ALPHA] and 1: the slider decides where in that range, and the floor is
     * what keeps a settings card readable over somebody else's app.
     */
    fun colour(container: Color): Color = if (active) {
        container.copy(alpha = FROSTED_MIN_ALPHA + (1f - FROSTED_MIN_ALPHA) * tintAlpha)
    } else {
        container
    }
}

/**
 * The window properties, once somebody else has established there is a window and the API exists.
 *
 * ⚠ **Checked for API 31 by its annotation and by the caller**, because lint's `NewApi` analysis
 * does not carry a guard across a lambda boundary and these are all API-31 calls.
 */
@RequiresApi(Build.VERSION_CODES.S)
private fun applyWindowFrost(
    window: Window,
    context: Context,
    card: IntRect,
    windowWidth: Int,
    windowHeight: Int,
    corner: Float,
    radius: Int,
    active: Boolean,
) {
    val supported = context.getSystemService(WindowManager::class.java)
        ?.isCrossWindowBlurEnabled == true

    if (!active || !supported || windowWidth <= 0 || windowHeight <= 0) {
        window.setBackgroundBlurRadius(0)

        window.setBackgroundDrawable(ColorDrawable(Color.Transparent.toArgb()))

        return
    }

    val card = GradientDrawable().apply {
        shape = GradientDrawable.RECTANGLE

        cornerRadius = corner

        // ⚠ **Nearly transparent, not transparent.** The blur is only drawn where the background
        // is painted, and a fully transparent pixel is not painted at all — so this is the
        // smallest alpha that still counts as paint. The card's real colour is the Compose
        // Surface on top of it.
        setColor(FROSTED_DRAWABLE_ALPHA shl ALPHA_SHIFT)
    }

    window.setBackgroundDrawable(
        InsetDrawable(
            card,
            bounds.left,
            bounds.top,
            windowWidth - bounds.right,
            windowHeight - bounds.bottom,
        ),
    )

    window.setBackgroundBlurRadius(radius)
}

/** When the shape is not a rounded rectangle, which no dialog in this app currently uses. */
private val FROSTED_FALLBACK_CORNER: Dp = 28.dp

/** The floor on a frosted card's opacity — see [FrostedWindow.colour]. */
private const val FROSTED_MIN_ALPHA = 0.55f

/** See the comment beside it: the least paint that still counts as painted. */
private const val FROSTED_DRAWABLE_ALPHA = 1

private const val ALPHA_SHIFT = 24
'''

# The helper builds its drawable from `card` and reads `bounds`; one name for one thing.
dialog = swap(
    dialog,
    """    val card = GradientDrawable().apply {""",
    """    val rounded = GradientDrawable().apply {""",
    "dialog: drawable name",
)

dialog = swap(
    dialog,
    """        InsetDrawable(
            card,
            bounds.left,
            bounds.top,
            windowWidth - bounds.right,
            windowHeight - bounds.bottom,
        ),""",
    """        InsetDrawable(
            rounded,
            card.left,
            card.top,
            windowWidth - card.right,
            windowHeight - card.bottom,
        ),""",
    "dialog: inset drawable",
)

dialog = swap(
    dialog,
    "import android.content.Context\n",
    "import android.content.Context\n"
    "import android.graphics.drawable.ColorDrawable\n"
    "import android.graphics.drawable.GradientDrawable\n"
    "import android.graphics.drawable.InsetDrawable\n",
    "dialog: drawable imports",
)

dialog = swap(
    dialog,
    "import androidx.compose.runtime.LaunchedEffect\n",
    "import androidx.compose.foundation.shape.RoundedCornerShape\n"
    "import androidx.compose.runtime.Immutable\n"
    "import androidx.compose.runtime.LaunchedEffect\n"
    "import androidx.compose.runtime.getValue\n"
    "import androidx.compose.runtime.mutableStateOf\n"
    "import androidx.compose.runtime.setValue\n"
    "import androidx.compose.ui.geometry.Size\n"
    "import androidx.compose.ui.graphics.toArgb\n"
    "import androidx.compose.ui.layout.boundsInWindow\n"
    "import androidx.compose.ui.layout.onGloballyPositioned\n"
    "import androidx.compose.ui.unit.IntRect\n"
    "import androidx.compose.ui.unit.roundToIntRect\n",
    "dialog: compose imports",
)

dialog = swap(
    dialog,
    "import com.android.geto.designsystem.theme.LocalProgressiveBlur\n",
    "import com.android.geto.designsystem.theme.LocalBlurSettings\n"
    "import com.android.geto.designsystem.theme.WINDOW_RADIUS_FACTOR\n",
    "dialog: settings imports",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

DIALOG.write_text(dialog, encoding="utf-8")

print(f"wrote {DIALOG.relative_to(ROOT).as_posix()}")

print("ok")
