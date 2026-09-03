#!/usr/bin/env python3
"""
r23 — blur the window and not the page behind it, brighter switches, brighter manager buttons,
and the author's new blur defaults.

## The window blur, and why r22 blurred the whole display

There are **two** platform blur APIs and they are not variants of each other:

  * `LayoutParams.FLAG_BLUR_BEHIND` + `blurBehindRadius` — blurs everything *behind* the window,
    on the same full-display layer that `FLAG_DIM_BEHIND` dims. It is not bounded by the window.
  * `Window.setBackgroundBlurRadius` — blurs only the window's **own** area, clipped to its
    background drawable's outline.

r19 used the first and frosted the whole screen. r20 and r21 used the second and nothing
rendered. r22 kept the first and shrank the window, on the theory that a card-sized window would
confine a blur-behind to the card — and the author's screenshot says it does not: the home screen
behind is blurred edge to edge. Blur-behind is a display-wide layer, so shrinking the window buys
nothing. That is now measured rather than assumed, and it is the answer to
*"can we modify to only blur the window not the background"*: only the second API can do that, so
r23 goes back to it — with the two things r20 and r21 were missing.

  1. **The window has to be the size of the card, and Compose has to be the one that sizes it.**
     `setBackgroundBlurRadius` blurs the window's area; a `usePlatformDefaultWidth = false` dialog
     window is the whole screen, so even a correct call would have blurred the whole screen. r22
     shrank it by calling `setLayout` behind Compose's back, which Compose reverts whenever it
     next reconciles the dialog's parameters. So the frosted path now asks for
     `usePlatformDefaultWidth = true` and lets Compose wrap the window itself — no fight, and the
     card's own `widthIn(max = …)` still decides the width.
  2. **The window properties have to be re-applied after every recomposition, not once.** They
     went on in a `LaunchedEffect`, which runs once per key change; Compose's own dialog effects
     run on every reconciliation and can overwrite them. A `SideEffect` inside the dialog's
     content is registered *after* Compose's, so it lands last, every time.

`FLAG_BLUR_BEHIND` is gone, and so is the dim override that went with it — the page behind a
frosted manager is now exactly the page behind any other dialog, which is the author's *"keep
outside BG as it was"*.

## Whether the S22 Ultra can do this at all

The author asks. The evidence says the device has cross-window blur switched off: the *page*
bands blur on both his phones, and those are `RenderEffect` inside IMD's own layer and need no
system support at all, while only the *window* frost fails — and the window frost is the one thing
gated on `WindowManager.isCrossWindowBlurEnabled`. Rather than have him take that on my word,
the blur dialog now reports what his device answers. If it says unsupported, that is the platform
and there is nothing in this app to fix; if it says supported and the card still does not frost,
then `setBackgroundBlurRadius` is being ignored and we will know that too.

## The rest

* **The checked switch thumb.** r22 took Material's `primary` track / `onPrimary` thumb, which in
  dark mode is a near-black knob — the author's *"the circle of switch is very hard to see (dark
  colour)"*. Inverted: the track is the recess (`primaryContainer`) and the thumb is the bright
  thing (`primary`), which is what an overhanging thumb wants. The rim that r21 drew only around
  an off track is now always drawn, so the thumb and track can never collapse into each other the
  way they did on the S22 Ultra even under a scheme that puts the two tones close together.
* **The manager's buttons.** `All off` / `All on` sat on `surfaceVariant` and the footer pair on
  `secondaryContainer`; against a translucent frosted card in dark mode both are mud. The footer
  pair goes to `primaryContainer` with `onPrimaryContainer` on it — the strongest pairing in the
  scheme, which is right for the two things the dialog is for — and the pill takes the top of the
  neutral ladder plus an `outline` rim, so it stays the neutral the author picked in r2b3d while
  still reading as two buttons at any card opacity.
* **The defaults**, at the author's word: 15 dp, 15 %, 120 dp.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"
TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"
MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"
DEFAULTS = ROOT / "domain/model/src/main/kotlin/com/android/geto/domain/model/BlurDefaults.kt"
BLUR_DIALOG = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/BlurSettingsDialog.kt"
STRINGS = ROOT / "feature/settings/src/main/res/values/strings.xml"

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
    """Just the lines the compiler reads.

    ⚠ Every round of this file so far has had at least one assertion fail because the KDoc I had
    just written named the very thing I was asserting had gone. `"FLAG_BLUR_BEHIND" not in dialog`
    is false the moment a comment explains why blur-behind was dropped. Counting on code lines is
    the fix that keeps working; narrowing the needle is the fix that has to be re-derived each time.
    """
    lines = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith(("//", "*", "/*", "/**")):
            continue

        lines.append(line)

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────────────────────
# 1. BlurDefaults.kt — the author's numbers.
# ─────────────────────────────────────────────────────────────────────────────────────────────

defaults = DEFAULTS.read_text(encoding="utf-8")

defaults = replace_once(
    defaults,
    """/** The author's **P2** — the stronger of the two options on the r10 template. */
const val DEFAULT_RADIUS_DP = 14""",
    """/** The author's own number, r23, after living with the sliders. */
const val DEFAULT_RADIUS_DP = 15""",
    "defaults: radius",
)

defaults = replace_once(
    defaults,
    """/**
 * Above ObtainX's own 34 %, at the author's word once he had seen both: a band that is only
 * blurred reads as a smudge, and the tint is what says *the page ends here*.
 */
const val DEFAULT_TINT_PERCENT = 50""",
    """/**
 * ⚠ **Down from 50 to 15 in r23, at the author's word, and it is a change of mind worth keeping
 * a note of.** r20 argued the tint upward because a band that is only blurred reads as a smudge.
 * With the frosted manager window taking the same number, a heavy tint is a card you cannot see
 * through — and once the window existed the author wanted the glass, not the paint.
 */
const val DEFAULT_TINT_PERCENT = 15""",
    "defaults: tint",
)

defaults = replace_once(
    defaults,
    """/**
 * Long enough that the eye cannot find where the ramp stops, short enough that the untouched
 * middle of a phone screen is still most of it.
 */
const val DEFAULT_FADE_DP = 72""",
    """/**
 * Long enough that the eye cannot find where the ramp stops, short enough that the untouched
 * middle of a phone screen is still most of it. The author's own 120 dp, r23 — a longer ramp
 * than r20 chose, which is the right direction now the tint is light.
 */
const val DEFAULT_FADE_DP = 120""",
    "defaults: fade",
)

# The new defaults must sit inside the ranges the store clamps to, or a fresh install resolves to
# a number the slider cannot represent.
for name, value, low, high in (
    ("radius", 15, 2, 40),
    ("tint", 15, 0, 90),
    ("fade", 120, 16, 200),
):
    check(low <= value <= high, f"defaults: {name} {value} is outside {low}..{high}")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 2. Dialog.kt — window-local blur, sized by Compose, re-applied every recomposition.
# ─────────────────────────────────────────────────────────────────────────────────────────────

dialog = DIALOG.read_text(encoding="utf-8")

# ⚠ **Imports last, at the bottom of this section.** r22's own version of this script asserted an
# import was unused *before* the edit that stopped using it, and reported five cascading failures
# for one ordering mistake. The body changes first; what is orphaned is then a fact rather than a
# prediction.

# ── the capped branch: compute the frost before the window exists, so its width can be asked for
CAPPED_OLD = """    Dialog(
        onDismissRequest = onDismissRequest,
        properties = DialogProperties(
            usePlatformDefaultWidth = false,
            // dismissOnClickOutside is left honest even though this window has no outside:
            // it costs nothing, and a future change that restores the platform width should
            // not have to remember to come back here.
            dismissOnBackPress = dismissible,
            dismissOnClickOutside = dismissible,
        ),
    ) {"""

CAPPED_NEW = """    // ⚠ **Decided out here, before the `Dialog`, because the answer changes the window's own
    // size — r23.** `usePlatformDefaultWidth` is a `DialogProperties` field, so it has to be
    // known before the window is created; and it has to be `true` on the frosted path, because
    // `Window.setBackgroundBlurRadius` blurs *the window's own area* and a
    // `usePlatformDefaultWidth = false` window is the whole screen. r22 shrank the window by
    // hand instead and Compose put it back — see [rememberFrostedWindow].
    val frost = rememberFrostedWindow(
        frostedWindow,
        containerColour = containerColor,
        shape = shape,
    )

    Dialog(
        onDismissRequest = onDismissRequest,
        properties = DialogProperties(
            // ⚠ **The one place this app lets the platform decide a dialog's width**, and only
            // because the window has to wrap the card for the blur to be confined to it. The
            // card still caps itself below, so what the platform decides is an upper bound that
            // the cap normally binds inside.
            usePlatformDefaultWidth = frost.frosted,
            // dismissOnClickOutside is left honest even though this window has no outside:
            // it costs nothing, and a future change that restores the platform width should
            // not have to remember to come back here.
            dismissOnBackPress = dismissible,
            dismissOnClickOutside = dismissible,
        ),
    ) {
        FrostedWindowEffect(frost)"""

dialog = replace_once(dialog, CAPPED_OLD, CAPPED_NEW, "dialog: capped Dialog properties")

# The old in-lambda call goes; the value now comes from outside.
dialog = replace_once(
    dialog,
    """        val frost = rememberFrostedWindow(
            frostedWindow,
            containerColour = containerColor,
            shape = shape,
        )

        if (frost.frosted) {""",
    """        if (frost.frosted) {""",
    "dialog: capped in-lambda frost call",
)

# ── the compact branch: same split, and it already wraps its window ──────────────────────────
COMPACT_OLD = """            val frost = rememberFrostedWindow(
                frostedWindow,
                containerColour = containerColor,
                shape = shape,
            )

            Surface(
                modifier = modifier,"""

COMPACT_NEW = """            FrostedWindowEffect(compactFrost)

            Surface(
                modifier = modifier,"""

dialog = replace_once(dialog, COMPACT_OLD, COMPACT_NEW, "dialog: compact frost call")

dialog = replace_once(
    dialog,
    """    if (compact) {
        Dialog(""",
    """    if (compact) {
        // Outside the `Dialog` for the same reason the capped branch below computes it there —
        // though this branch already wrapped its window, so the answer changes nothing here
        // beyond where the value is read.
        val compactFrost = rememberFrostedWindow(
            frostedWindow,
            containerColour = containerColor,
            shape = shape,
        )

        Dialog(""",
    "dialog: compact frost declaration",
)

# ── the frost itself: state in composition, window properties in a SideEffect ────────────────
FROST_OLD_START = "    LaunchedEffect(view, active, radius, corner, fill) {"

FROST_OLD_END = """    return FrostedWindow(frosted = active, content = contentColour)
}"""

start = dialog.find(FROST_OLD_START)

end = dialog.find(FROST_OLD_END)

if check(start != -1 and end != -1 and start < end, "dialog: the frost effect block was not found"):
    FROST_NEW = """    return FrostedWindow(
        frosted = active,
        content = contentColour,
        requested = enabled,
        corner = corner,
        fill = fill.toArgb(),
        radius = radius,
    )
}

/**
 * Puts [FrostedWindow]'s numbers onto the real window, and keeps putting them there.
 *
 * ⚠ **A `SideEffect`, not a `LaunchedEffect`, and that is the r22 bug.** A `LaunchedEffect` runs
 * once per key change. Compose's own dialog code reconciles the window's parameters whenever the
 * `Dialog` composable recomposes — which for the settings manager is every time a switch moves —
 * and anything set from outside that reconciliation is liable to be overwritten by it. A
 * `SideEffect` registered *inside* the dialog's content is registered after Compose's own, and
 * effects run in registration order, so this one lands last on every pass.
 *
 * ⚠ **Nothing happens at all unless the caller asked for a frosted window.** Every other dialog
 * in the app goes through here too, and a window whose background drawable and blur radius are
 * being reset by us — even to the values it already had — is a window we have taken responsibility
 * for without being asked.
 */
@Composable
private fun FrostedWindowEffect(frost: FrostedWindow) {
    val view = LocalView.current

    SideEffect {
        if (!frost.requested) return@SideEffect

        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return@SideEffect

        // Null on the flat path, which draws into the page rather than into a window of its own.
        val window = (view.parent as? DialogWindowProvider)?.window ?: return@SideEffect

        applyWindowFrost(
            window = window,
            active = frost.frosted,
            corner = frost.corner,
            fill = frost.fill,
            radius = frost.radius,
        )
    }
}"""

    dialog = dialog[:start] + FROST_NEW + dialog[end + len(FROST_OLD_END):]

# ── what the holder carries ──────────────────────────────────────────────────────────────────
HOLDER_OLD = """/** What [rememberFrostedWindow] hands back: whether the window is the card, and the ink on it. */
private class FrostedWindow(
    // Plain `val`s, no `private`: `private` on a constructor property of a private class buys
    // nothing, and it confused tools/check9_arity into reading the constructor as taking one.
    val frosted: Boolean,
    val content: Color,
) {"""

HOLDER_NEW = """/**
 * What [rememberFrostedWindow] hands back: whether the window is the card, the ink on it, and the
 * numbers [FrostedWindowEffect] puts on the window.
 *
 * The window properties travel through here rather than being applied where they are computed
 * because they are computed *outside* the `Dialog` — that is what lets the frost decide the
 * window's width — and there is no window out there to put them on yet.
 */
private class FrostedWindow(
    // Plain `val`s, no `private`: `private` on a constructor property of a private class buys
    // nothing, and it confused tools/check9_arity into reading the constructor as taking one.
    val frosted: Boolean,
    val content: Color,
    /** Whether the caller asked for a frosted window at all, however the device answered. */
    val requested: Boolean,
    val corner: Float,
    /** Already an ARGB int: the effect has no composition to read a `Color` in. */
    val fill: Int,
    val radius: Int,
) {"""

dialog = replace_once(dialog, HOLDER_OLD, HOLDER_NEW, "dialog: FrostedWindow holder")

# ── the window properties themselves ─────────────────────────────────────────────────────────
APPLY_OLD_START = """@RequiresApi(Build.VERSION_CODES.S)
private fun applyWindowFrost("""

APPLY_OLD_END = """    // Material's dialog dim is 0.32 and exists to push the page back; the blur has already done
    // that, and both at once turns the backdrop into a grey slab.
    window.setDimAmount(DIALOG_FROSTED_DIM)
}"""

start = dialog.find(APPLY_OLD_START)

end = dialog.find(APPLY_OLD_END)

if check(start != -1 and end != -1 and start < end, "dialog: applyWindowFrost was not found"):
    APPLY_NEW = """@RequiresApi(Build.VERSION_CODES.S)
private fun applyWindowFrost(
    window: Window,
    active: Boolean,
    corner: Float,
    fill: Int,
    radius: Int,
) {
    if (!active) {
        // Reachable while the dialog is open: the author can turn Progressive UI blur off from
        // the settings page with the manager still on screen.
        window.setBackgroundBlurRadius(0)

        window.setBackgroundDrawable(ColorDrawable(Color.Transparent.toArgb()))

        return
    }

    // ⚠ **The card is painted by the *window*, and the drawable is doing two jobs.** It is the
    // fill the content sits on, and its outline is the shape the blur is clipped to — that second
    // job is why this is a `GradientDrawable` with a corner radius rather than a `ColorDrawable`.
    // It has to be partly transparent or there is nothing to see the blur through.
    window.setBackgroundDrawable(
        GradientDrawable().apply {
            // `this.` spelled out: `DialogContainer` a few hundred lines up also has a `shape`,
            // and a bare one here reads as that even though it cannot be — this is a top-level
            // function.
            this.shape = GradientDrawable.RECTANGLE

            cornerRadius = corner

            setColor(fill)
        },
    )

    // ⚠ **`setBackgroundBlurRadius`, not `FLAG_BLUR_BEHIND` — r23, and this is the whole point of
    // the round.** They are different features: blur-behind runs on the display-wide layer that
    // also does dim-behind and frosts *everything* behind the window, which is what the author saw
    // in r19 and again in r22 and asked twice to be rid of; this one blurs the window's own area,
    // clipped to the drawable's outline above. Nothing else on the screen is touched, which is the
    // author's *"only blur the window not the background"*.
    //
    // No `setDimAmount` either, for the same reason: the page behind a frosted manager should look
    // exactly like the page behind any other dialog in the app.
    window.setBackgroundBlurRadius(radius)
}"""

    dialog = dialog[:start] + APPLY_NEW + dialog[end + len(APPLY_OLD_END):]

dialog = replace_once(
    dialog,
    """/** How much scrim is left once the card is frosted. */
private const val DIALOG_FROSTED_DIM = 0.20f
""",
    "",
    "dialog: DIALOG_FROSTED_DIM",
)

# ── the readout the settings page shows ──────────────────────────────────────────────────────
dialog = replace_once(
    dialog,
    """/** When the shape is not a rounded rectangle, which no dialog in this app currently uses. */
private val FROSTED_FALLBACK_CORNER: Dp = 28.dp""",
    """/**
 * Whether this device will frost a window at all, for the settings page to say out loud.
 *
 * ⚠ **Shown rather than inferred, at the author's question** — *"works only on razr fold, not s22
 * ultra but i think bcz it doesnt support it?? u tell??"*. His reading is almost certainly right:
 * the *page* bands blur on both phones and those are a `RenderEffect` inside IMD's own layer,
 * needing nothing from the system, while the window frost is the one thing gated on
 * `isCrossWindowBlurEnabled` — which the platform turns off under battery saver, under some
 * accessibility settings, and permanently on devices whose compositor cannot afford it. Rather
 * than have him take that on trust, the dialog reports what his device answers.
 */
@Composable
fun supportsWindowBlur(): Boolean {
    val view = LocalView.current

    return remember(view) {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            view.context.getSystemService(WindowManager::class.java)?.isCrossWindowBlurEnabled == true
    }
}

/** When the shape is not a rounded rectangle, which no dialog in this app currently uses. */
private val FROSTED_FALLBACK_CORNER: Dp = 28.dp""",
    "dialog: supportsWindowBlur",
)

# The frost's own check is now that function, so there is one definition of "can this device", and
# its `view` goes with it — nothing else in `rememberFrostedWindow` reads one.
dialog = replace_once(
    dialog,
    """    val view = LocalView.current

    val density = LocalDensity.current

    val supported = remember(view) {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
            view.context.getSystemService(WindowManager::class.java)?.isCrossWindowBlurEnabled == true
    }

    val active = enabled && settings.enabled && supported""",
    """    val density = LocalDensity.current

    val active = enabled && settings.enabled && supportsWindowBlur()""",
    "dialog: frost support check",
)

# ── the KDoc that described the r22 mechanism ────────────────────────────────────────────────
DOC_OLD_START = " * ⚠ **`FLAG_BLUR_BEHIND` on a window sized to the card — r22, and the reasoning is the elimination"

DOC_OLD_END = """ * battery-saver toggle behind.
 */"""

start = dialog.find(DOC_OLD_START)

end = dialog.find(DOC_OLD_END)

if check(start != -1 and end != -1 and start < end, "dialog: the r22 frost KDoc was not found"):
    DOC_NEW = """ * ⚠ **`Window.setBackgroundBlurRadius` on a window Compose has wrapped — r23, and the round
 * before it is what proves the shape.** There are two platform blur APIs and they are different
 * features, not settings of one: `FLAG_BLUR_BEHIND` frosts everything behind the window, on the
 * display-wide layer that also does dim-behind, and is not bounded by the window at any size;
 * `setBackgroundBlurRadius` frosts the window's own area, clipped to its background drawable's
 * outline. r19 used the first and the author asked twice to be rid of the frosted page it gives.
 * r22 kept it and shrank the window on the theory that a card-sized window would confine it — the
 * author's screenshot shows the home screen blurred edge to edge, so it does not. The second API
 * is the only one that can do what he asked for, which is why it is back.
 *
 * ⚠ **And the window has to be wrapped by Compose, not by us.** `setBackgroundBlurRadius` blurs
 * the window's area, and a `usePlatformDefaultWidth = false` dialog window is the whole screen —
 * so this is the one dialog in the app that asks for the platform width, and `DialogContainer`
 * reads [FrostedWindow.frosted] *before* opening the window in order to ask for it. r22 instead
 * called `setLayout` by hand from inside the window, which Compose reverts whenever it next
 * reconciles the dialog's parameters; the settings manager reconciles on every switch it moves.
 *
 * ⚠ **Checked against `isCrossWindowBlurEnabled` *before* composing**, not after — see
 * [supportsWindowBlur]. The system turns cross-window blur off under battery saver and on devices
 * that cannot afford it; asking anyway would leave a window made translucent for a frost that
 * never arrives. Read once per opening, because a dialog that re-laid itself out mid-gesture would
 * be worse than one that is a battery-saver toggle behind.
 */"""

    dialog = dialog[:start] + DOC_NEW + dialog[end + len(DOC_OLD_END):]

# ── imports, now that the body is settled ────────────────────────────────────────────────────
body = code(dialog)

GRAVITY = "import android.view.Gravity\n"

check("Gravity" not in code(dialog.replace(GRAVITY, "")), "dialog: Gravity is still used")

dialog = replace_once(dialog, GRAVITY, "", "dialog: Gravity import")

dialog = replace_once(
    dialog,
    "import androidx.compose.runtime.LaunchedEffect\n",
    "import androidx.compose.runtime.SideEffect\n",
    "dialog: SideEffect import",
)

# ── and the final state, counted on code lines only ──────────────────────────────────────────
body = code(dialog)

check("FLAG_BLUR_BEHIND" not in body, "dialog: FLAG_BLUR_BEHIND should be gone from the code")

check("blurBehindRadius" not in body, "dialog: blurBehindRadius should be gone from the code")

check("LaunchedEffect" not in body, "dialog: LaunchedEffect should be gone from the code")

check("setDimAmount" not in body, "dialog: setDimAmount should be gone from the code")

check(body.count("setBackgroundBlurRadius") == 2, "dialog: expected the set and the clear")

# `view` is read by supportsWindowBlur and by the effect, and nowhere else.
check(
    body.count("val view = LocalView.current") == 2,
    "dialog: expected LocalView in supportsWindowBlur and in the effect only",
)

# Every `AndroidRenderEffect`-style trap in reverse: the two window APIs must not both be present.
check(
    body.count("usePlatformDefaultWidth = frost.frosted") == 1,
    "dialog: the frosted path should be the one asking for the platform width",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 3. GetoToggles.kt — a bright thumb in a dark slot, and a rim that always runs.
# ─────────────────────────────────────────────────────────────────────────────────────────────

toggles = TOGGLES.read_text(encoding="utf-8")

TRACK_OLD = """        // ⚠ **`primary`, not `primaryContainer` — r22.** A container tone is a *background*
        // colour: the scheme guarantees text is legible on it, and guarantees nothing at all
        // about another accent sitting on top. Under dynamic colour the pair happened to work —
        // the author's razr — and under the static scheme both tones landed mid-range and the
        // thumb dissolved into the track, which is the "weird" he saw on the S22 Ultra. `primary`
        // with `onPrimary` on it is the one pairing the scheme *defines* as contrasting, so it
        // holds under every scheme rather than under the lucky ones.
        checked && enabled -> scheme.primary
        checked -> scheme.primary.copy(alpha = if (live) 0.45f else 0.28f)
"""

TRACK_NEW = """        // ⚠ **The track is the recess and the thumb is the bright thing — r23, and r22 had it
        // the other way round.** r22 took Material's own `primary` track with an `onPrimary`
        // thumb, which is a contrasty pair by construction but puts the *dark* half in the knob:
        // in dark mode that is a near-black circle, the author's *"the circle of switch is very
        // hard to see"*. This switch's thumb overhangs its track by eight dp — it is drawn as a
        // knob standing proud of a slot, not as a dot inside a pill — and a knob that is darker
        // than the thing it sits on reads as a hole punched through it.
        //
        // So `primaryContainer` under `primary`, which is dark-under-bright in dark mode and
        // bright-under-dark in light mode: in both the thumb is the one that catches the eye. The
        // r21 objection to this pair still stands — under some dynamic schemes the two tones land
        // close together, which is what made the S22 Ultra's switch mush — and it is answered by
        // the rim below, which now runs whether the switch is on or off.
        checked && enabled -> scheme.primaryContainer
        checked -> scheme.primaryContainer.copy(alpha = if (live) 0.45f else 0.28f)
"""

toggles = replace_once(toggles, TRACK_OLD, TRACK_NEW, "toggles: checked track")

THUMB_OLD = """        checked && enabled -> scheme.onPrimary
        checked -> scheme.onPrimary.copy(alpha = if (live) 0.55f else 0.38f)
"""

THUMB_NEW = """        checked && enabled -> scheme.primary
        checked -> scheme.primary.copy(alpha = if (live) 0.55f else 0.38f)
"""

toggles = replace_once(toggles, THUMB_OLD, THUMB_NEW, "toggles: checked thumb")

RIM_OLD = """                // ⚠ **Only while off.** A checked track is a filled `primary` and needs
                // no rim; an unchecked one is a dark slot on a dark card, and the rim is most of
                // what makes it a slot at all.
                .border(
                    width = SWITCH_TRACK_BORDER,
                    color = if (checked) Color.Transparent else border,
                    shape = CircleShape,
                ),
"""

RIM_NEW = """                // ⚠ **On in both states now — r23.** It used to be drawn only while off, on
                // the reasoning that a filled track needs no help; what that missed is that the
                // rim is also the only thing guaranteeing the thumb and the track are separable
                // when a scheme puts their two tones close together, which is exactly how the
                // S22 Ultra's switch turned to mush in r21. A neutral hairline contrasts with
                // both accents under every scheme, because it is not derived from either.
                .border(
                    width = SWITCH_TRACK_BORDER,
                    color = border,
                    shape = CircleShape,
                ),
"""

toggles = replace_once(toggles, RIM_OLD, RIM_NEW, "toggles: track rim")

# ⚠ `Color` was imported for `Color.Transparent` in the rim. The file uses it elsewhere too, so
# this is a check that it is still needed rather than a removal.
check("Color." in toggles, "toggles: Color is unexpectedly unused")

check(
    toggles.count("        checked && enabled -> scheme.primary\n") == 2,
    "toggles: the switch thumb and the checkbox should be the two users of primary",
)

check("scheme.onPrimary.copy" not in toggles, "toggles: the onPrimary thumb should be gone")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 4. AndroidSettingsManagerDialog.kt — the two button treatments the author annotated.
# ─────────────────────────────────────────────────────────────────────────────────────────────

manager = MANAGER.read_text(encoding="utf-8")

PILL_OLD = """    val container = if (enabled) {
        MaterialTheme.colorScheme.surfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    }

    val content = if (enabled) {
        MaterialTheme.colorScheme.onSurfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }
"""

PILL_NEW = """    // ⚠ **Top of the neutral ladder plus a rim — r23, from the author's annotated screenshot.**
    // `surfaceVariant` is a mid neutral, and this row sits on a card that is now translucent: in
    // dark mode the two were within a few points of each other and the pill all but disappeared.
    // The shade stays neutral, because the author's r2b3d pick was that this row belongs to the
    // switches beside it rather than to the filled pair at the foot of the dialog — so it climbs
    // the ladder rather than borrowing an accent, and the rim does the rest. A hairline reads at
    // any card opacity, which a fill by itself cannot.
    val container = if (enabled) {
        MaterialTheme.colorScheme.surfaceContainerHighest
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    }

    val content = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }

    val rim = if (enabled) {
        MaterialTheme.colorScheme.outline
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }
"""

manager = replace_once(manager, PILL_OLD, PILL_NEW, "manager: pill colours")

for half, label in (("off", "All off"), ("on", "All on")):
    manager = replace_once(
        manager,
        f"""            label = stringResource(R.string.settings_manager_all_{half}),
            shape = PILL_{'START' if half == 'off' else 'END'}_SHAPE,
            container = container,
            content = content,
""",
        f"""            label = stringResource(R.string.settings_manager_all_{half}),
            shape = PILL_{'START' if half == 'off' else 'END'}_SHAPE,
            container = container,
            content = content,
            rim = rim,
""",
        f"manager: {label} rim argument",
    )

manager = replace_once(
    manager,
    """    label: String,
    shape: Shape,
    container: Color,
    content: Color,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxHeight(),
        shape = shape,
        color = container,
        contentColor = content,
    ) {""",
    """    label: String,
    shape: Shape,
    container: Color,
    content: Color,
    /** The hairline that makes this read as a button on a translucent card — see [MasterPill]. */
    rim: Color,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxHeight(),
        shape = shape,
        color = container,
        contentColor = content,
        border = BorderStroke(width = PILL_RIM, color = rim),
    ) {""",
    "manager: PillHalf rim",
)

ACTION_OLD = """    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.secondaryContainer
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onSecondaryContainer
    }
"""

ACTION_NEW = """    // ⚠ **`primaryContainer`, up from `secondaryContainer` — r23, from the author's annotated
    // screenshot.** The secondary container is a muted olive in the dark scheme, and against a
    // translucent frosted card it stopped reading as a button at all. These two are what the
    // dialog is *for*, so they take the strongest container the scheme has and the ink that goes
    // with it. The red pending state is untouched: it is not competing with these, it replaces
    // one of them.
    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.primaryContainer
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onPrimaryContainer
    }
"""

manager = replace_once(manager, ACTION_OLD, ACTION_NEW, "manager: action button colours")

manager = replace_once(
    manager,
    "private val PILL_HEIGHT = 28.dp",
    """/** The hairline around each half of [MasterPill]. One dp: a rim, not a frame. */
private val PILL_RIM = 1.dp

private val PILL_HEIGHT = 28.dp""",
    "manager: PILL_RIM",
)

if "import androidx.compose.foundation.BorderStroke\n" not in manager:
    manager = replace_once(
        manager,
        "import androidx.compose.foundation.ExperimentalFoundationApi\n",
        "import androidx.compose.foundation.BorderStroke\nimport androidx.compose.foundation.ExperimentalFoundationApi\n",
        "manager: BorderStroke import",
    )

check(
    "MaterialTheme.colorScheme.secondaryContainer" not in manager,
    "manager: secondaryContainer should no longer be used",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 5. BlurSettingsDialog.kt + strings — say what the device can do.
# ─────────────────────────────────────────────────────────────────────────────────────────────

blur = BLUR_DIALOG.read_text(encoding="utf-8")

blur = replace_once(
    blur,
    """            Spacer(modifier = Modifier.height(16.dp))

            BlurSlider(
                label = stringResource(R.string.blur_settings_radius),""",
    """            Spacer(modifier = Modifier.height(8.dp))

            // ⚠ **A readout, not a warning — r23.** The author asked whether his S22 Ultra simply
            // cannot frost a window. It is the platform's answer to give, not this app's guess, so
            // the dialog asks and prints it. The page bands do not depend on this and keep working
            // either way, which is what the second line says.
            Text(
                text = if (supportsWindowBlur()) {
                    stringResource(R.string.blur_settings_window_supported)
                } else {
                    stringResource(R.string.blur_settings_window_unsupported)
                },
                style = MaterialTheme.typography.bodySmall,
                color = if (supportsWindowBlur()) {
                    MaterialTheme.colorScheme.primary
                } else {
                    MaterialTheme.colorScheme.onSurfaceVariant
                },
            )

            Spacer(modifier = Modifier.height(16.dp))

            BlurSlider(
                label = stringResource(R.string.blur_settings_radius),""",
    "blur dialog: support readout",
)

blur = replace_once(
    blur,
    "import com.android.geto.designsystem.component.DialogContainer\n",
    "import com.android.geto.designsystem.component.DialogContainer\nimport com.android.geto.designsystem.component.supportsWindowBlur\n",
    "blur dialog: supportsWindowBlur import",
)

strings = STRINGS.read_text(encoding="utf-8")

strings = replace_once(
    strings,
    """    <string name="blur_settings_reset">Reset</string>""",
    """    <string name="blur_settings_window_supported">This device can frost the settings manager\\'s window.</string>
    <string name="blur_settings_window_unsupported">This device will not frost the settings manager\\'s window — the system has cross-window blur switched off. Page blur is unaffected.</string>
    <string name="blur_settings_reset">Reset</string>""",
    "strings: window support",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in (
    (DEFAULTS, defaults),
    (DIALOG, dialog),
    (TOGGLES, toggles),
    (MANAGER, manager),
    (BLUR_DIALOG, blur),
    (STRINGS, strings),
):
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
