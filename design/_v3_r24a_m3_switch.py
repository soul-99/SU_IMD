#!/usr/bin/env python3
"""
r24a — the app's switch becomes Material 3's own, with a hand-drawn tick and the manager's spinner
living inside the thumb.

The author: *"please use material 3 toggles like this (m3.material.io/components/switch/overview)
throughout UI, replace old ones, also when turned on show a tick inside the button for 1s when
switch successfully turns on"*, *"for settings manager we sometimes rotating spinner when imd is
trying to switch a toggle … can we update the spinner to show inside the circle of toggle switch?"*,
and, choosing from `design/template_r24_m3_switch.html`: **variant A** — the spec's small 16 dp off
dot — plus *"can we animate tick to appear like it is usually written left to right?"*.

## Why this stops being drawn by hand

r11's KDoc argued the switch had to be drawn because Compose's `Switch` was "still the older shape
at this Material version". That is no longer true at BOM 2026.03.01, and more to the point it was
answering the wrong question: what the author has asked for now is not a *shape* but a **slot**.
Material's `Switch` has a `thumbContent` — the icon-in-the-thumb the spec page shows — and it is
exactly where a tick and a spinner belong. Hand-drawing that would mean re-implementing the thumb's
size animation, its press growth and its four colour states to get at a hole Material already has.

So `GetoSwitch` keeps its name, its call sites and its two app-specific parameters, and delegates
the drawing. Everything that was hard-won stays:

  * **The unchecked track is `surfaceContainerHigh`, not Material's `surfaceContainerHighest`.**
    That override is the whole of r17b → r21: the settings card *is* `surfaceContainerHighest`, so
    the spec's own default makes an off switch the same colour as the thing it sits on. Three rounds
    of the author telling me the off switch was invisible are in that one line.
  * **The 2 dp `outline` rim on the unchecked track** — which is the spec's, and also r21's.
  * **`error`**, the off state in the error palette for a service that failed to start.
  * **`liveWhileDisabled`**, the muted-but-live reading. ⚠ Material's switch has no muted middle
    state and no way to ask for one — but it does not need one: this passes `enabled = true` so the
    *enabled* palette is used, hands that palette colours already reduced in alpha, and drops
    `onCheckedChange` so the control is inert. Same reading, and it avoids overriding all eight of
    Material's `disabled*` colours to get there.

## The tick, drawn rather than iconed

`GetoIcons.Check` in a `thumbContent` would appear all at once. The author asked for it to be
written, so it is two `drawLine`s whose far ends travel: the first stroke grows from the corner to
the elbow, then the second from the elbow to the tip, on one 0 → 1 animation across both. Arithmetic
only — no `PathMeasure`, no trim, nothing that can behave differently on one device.

⚠ **One second is the hold, not the draw.** The author asked for a tick "for 1s"; drawing it over a
second would be a slow smear. It is written in 220 ms, holds, and fades out on the ordinary toggle
curve when the second is up.

⚠ **Only false → true, and only after the fact.** `previous` is seeded from `checked` at first
composition, so a switch that is *already* on when the dialog opens does not tick — the tick means
*this just turned on*, and six of them firing when the settings manager opens would mean nothing.
That is also what makes it honest on the manager's asynchronous rows: their `checked` follows the
live service, so the tick lands when the service actually started rather than when the press
happened.

## The spinner

It moves out of the row's title, where it was a 14 dp ring beside a label, and into the thumb.
While a service is starting the switch still reads as off, so the thumb takes the icon size to hold
the ring — Material grows an unchecked thumb from 16 dp to 24 dp whenever `thumbContent` is
non-null, so that growth comes free and is itself part of the signal.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"
MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

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
    """Just the lines the compiler reads — see the note in `_v3_r23_*.py`."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


# ─────────────────────────────────────────────────────────────────────────────────────────────
# GetoToggles.kt
# ─────────────────────────────────────────────────────────────────────────────────────────────

toggles = TOGGLES.read_text(encoding="utf-8")

SWITCH_START = "/**\n * The app's switch, drawn rather than configured"

SWITCH_END = "/**\n * The app's checkbox:"

start = toggles.find(SWITCH_START)

end = toggles.find(SWITCH_END)

NEW_SWITCH = '''/**
 * The app's switch: Material 3's own, with the app's own states and a slot in the thumb.
 *
 * ⚠ **Delegated rather than drawn — r24, and it reverses r11's decision on purpose.** r11 drew
 * this by hand because Compose's `Switch` was the older shape then, and because the author had
 * picked a thumb that overhangs its track. What he has asked for now is the spec switch from
 * m3.material.io, and — more to the point — a **tick and a spinner inside the thumb**. Material's
 * `thumbContent` is that slot. Hand-drawing it would mean re-implementing the thumb's size
 * animation, its press growth and its four colour states to reach a hole Material already has.
 *
 * ⚠ **The unchecked track is `surfaceContainerHigh`, not Material's own default.** That one
 * override is the whole of r17b → r21. Material's default unchecked track is
 * `surfaceContainerHighest`, which is exactly the colour of this app's settings card, so the spec
 * default makes an off switch the same shade as the thing it is sitting on — which the author
 * reported three rounds running. The 2 dp `outline` rim is both the spec's and r21's, and it does
 * the rest.
 *
 * ⚠ **The 48 dp touch target comes from Material**, which floors it internally. The settings
 * manager scales its switches down and relies on the whole row taking the press instead; that is
 * safe *there* and is documented at that call site, not here.
 */
@Composable
fun GetoSwitch(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
    /**
     * Draws the off state in the error palette.
     *
     * The settings manager's own use: a row whose service failed to start is off *and wrong*, and
     * the difference matters more than the switch looking uniform.
     */
    error: Boolean = false,
    /**
     * Keeps a disabled-but-on switch legible instead of inert.
     *
     * ⚠ **One call site, and it is a real distinction.** The manager's rows go unusable for a
     * dozen reasons — the dialog is busy, a Shevery wait is running, Shizuku has no intents
     * configured — while still reporting a service that genuinely *is* running. The ordinary
     * disabled palette makes a true "on" look like a dead control, which is a lie about the
     * device.
     *
     * ⚠ **Implemented through the *enabled* palette, not Material's disabled one.** Material's
     * switch has no muted middle state and no way to ask for one. So this passes `enabled = true`
     * and hands that palette colours already reduced in alpha, with `onCheckedChange` dropped so
     * the control is inert. Same reading, and it avoids restating all eight of Material's
     * `disabled*` colours to get there.
     */
    liveWhileDisabled: Boolean = false,
    /**
     * Puts a spinner in the thumb: this switch has been asked to move and the answer has not
     * arrived.
     *
     * ⚠ **The author's r24 instruction**, replacing a ring that used to sit beside the row's
     * title: *"can we update the spinner to show inside the circle of toggle switch?"*. Inside
     * the thumb it says the thing that is working is the switch, which is what the user pressed.
     * The switch still reads off while a service starts, and Material grows an unchecked thumb to
     * the icon size whenever there is thumb content — so that growth is part of the signal rather
     * than a side effect to design around.
     */
    busy: Boolean = false,
) {
    val scheme = MaterialTheme.colorScheme

    // Disabled, but reporting something true. See [liveWhileDisabled].
    val muted = !enabled && liveWhileDisabled

    val tone: (Color) -> Color = { if (muted) it.copy(alpha = SWITCH_MUTED_ALPHA) else it }

    val offTrack = if (error) scheme.errorContainer else scheme.surfaceContainerHigh

    val offInk = if (error) scheme.error else scheme.outline

    // ⚠ **Seeded from `checked`, so an already-on switch does not tick on first composition.** The
    // tick means *this just turned on*; six of them firing as the settings manager opens would
    // mean nothing at all.
    var previous by remember { mutableStateOf(checked) }

    var ticking by remember { mutableStateOf(false) }

    LaunchedEffect(checked) {
        if (checked && !previous) {
            ticking = true

            delay(SWITCH_TICK_HOLD_MILLIS)

            ticking = false
        }

        previous = checked
    }

    // ⚠ **One number for both strokes, which is what makes it read as handwriting** — the
    // author's *"animate tick to appear like it is usually written left to right"*. Written in
    // 220 ms rather than over the whole second: the second is the hold, and a tick drawn that
    // slowly is a smear.
    val drawn by animateFloatAsState(
        targetValue = if (ticking) 1f else 0f,
        animationSpec = tween(
            durationMillis = if (ticking) SWITCH_TICK_DRAW_MILLIS else TOGGLE_MILLIS,
            easing = ToggleEasing,
        ),
        label = "switchTick",
    )

    // ⚠ **Null when there is nothing to show, and that is deliberate.** Material sizes the thumb
    // from whether this is null: 16 dp off and 24 dp on with no content, 24 dp either way with it.
    // Handing it an empty composable instead would keep the off thumb at 24 dp for ever, which is
    // the variant the author looked at and did not pick.
    val glyph: (@Composable () -> Unit)? = when {
        busy -> {
            {
                CircularProgressIndicator(
                    modifier = Modifier.size(SwitchDefaults.IconSize),
                    color = LocalContentColor.current,
                    strokeWidth = SWITCH_SPINNER_STROKE,
                )
            }
        }

        drawn > 0f -> {
            { WrittenTick(progress = drawn, colour = LocalContentColor.current) }
        }

        else -> null
    }

    Switch(
        modifier = modifier,
        checked = checked,
        // Dropped whenever the control is not operable, which is what makes the muted state
        // inert while still being drawn from the enabled palette.
        onCheckedChange = if (enabled) onCheckedChange else null,
        enabled = enabled || liveWhileDisabled,
        thumbContent = glyph,
        colors = SwitchDefaults.colors(
            checkedThumbColor = tone(scheme.onPrimary),
            checkedTrackColor = tone(scheme.primary),
            // Material draws no visible rim on a filled track, and a checked track needs none:
            // `primary` under `onPrimary` is the one pairing the scheme defines as contrasting.
            checkedBorderColor = tone(scheme.primary),
            checkedIconColor = tone(scheme.onPrimaryContainer),
            uncheckedThumbColor = tone(offInk),
            uncheckedTrackColor = tone(offTrack),
            uncheckedBorderColor = tone(offInk),
            // The ink on an unchecked thumb is the track it came out of, so a spinner in it reads
            // as a hole in the thumb rather than as a second colour nobody chose.
            uncheckedIconColor = tone(offTrack),
        ),
    )
}

/**
 * A tick, written.
 *
 * Two strokes whose far ends travel on one 0 → 1 progress: the first from the corner to the elbow,
 * then the second from the elbow to the tip. `drawLine` and arithmetic only — no `PathMeasure` and
 * no path trimming, so there is nothing here that can behave differently on one device.
 *
 * The three points are fractions of the box rather than dp, so this is correct at whatever size
 * Material hands the thumb content and at whatever scale the settings manager applies to the row.
 */
@Composable
private fun WrittenTick(progress: Float, colour: Color) {
    Canvas(modifier = Modifier.size(SwitchDefaults.IconSize)) {
        val corner = Offset(size.width * 0.22f, size.height * 0.54f)

        val elbow = Offset(size.width * 0.42f, size.height * 0.74f)

        val tip = Offset(size.width * 0.78f, size.height * 0.28f)

        val first = (elbow - corner).getDistance()

        val second = (tip - elbow).getDistance()

        val written = (first + second) * progress.coerceIn(0f, 1f)

        val stroke = size.width * TICK_STROKE_FRACTION

        if (written <= first) {
            drawLine(
                color = colour,
                start = corner,
                end = lerp(corner, elbow, if (first <= 0f) 0f else written / first),
                strokeWidth = stroke,
                cap = StrokeCap.Round,
            )

            return@Canvas
        }

        drawLine(
            color = colour,
            start = corner,
            end = elbow,
            strokeWidth = stroke,
            cap = StrokeCap.Round,
        )

        drawLine(
            color = colour,
            start = elbow,
            end = lerp(elbow, tip, if (second <= 0f) 0f else (written - first) / second),
            strokeWidth = stroke,
            cap = StrokeCap.Round,
        )
    }
}

'''

if check(start != -1 and end != -1 and start < end, "toggles: the switch region was not found"):
    toggles = toggles[:start] + NEW_SWITCH + toggles[end:]

# ── the geometry constants the drawn switch owned ────────────────────────────────────────────
toggles = replace_once(
    toggles,
    """/** The author's W1: a 48 × 22 track under a 30 dp thumb. */
private val SWITCH_TRACK_WIDTH: Dp = 48.dp

private val SWITCH_TRACK_HEIGHT: Dp = 22.dp

/** The rim around an unchecked track. */
private val SWITCH_TRACK_BORDER: Dp = 2.dp

private val SWITCH_THUMB_SIZE: Dp = 30.dp

private val SWITCH_THUMB_ELEVATION: Dp = 2.dp
""",
    """/**
 * How far a muted-but-live switch is faded. See [GetoSwitch]'s `liveWhileDisabled`.
 *
 * Reduced enough to say *not pressable*, not so far as to say *dead* — the difference the whole
 * parameter exists for.
 */
private const val SWITCH_MUTED_ALPHA = 0.55f

/** How long the tick stays once written. The author asked for a second, and this is that second. */
private const val SWITCH_TICK_HOLD_MILLIS = 1000L

/** How long the tick takes to write itself. Not the same number as the hold — see [GetoSwitch]. */
private const val SWITCH_TICK_DRAW_MILLIS = 220

/** The spinner in the thumb, at 16 dp. Two dp reads as a ring; three fills the middle in. */
private val SWITCH_SPINNER_STROKE: Dp = 2.dp

/** The tick's stroke, as a fraction of the box, so it scales with whatever size it is given. */
private const val TICK_STROKE_FRACTION = 0.14f
""",
    "toggles: switch constants",
)

# ── imports ──────────────────────────────────────────────────────────────────────────────────
body = code(toggles)

for gone in (
    "import androidx.compose.animation.core.animateDpAsState\n",
    "import androidx.compose.foundation.layout.offset\n",
    "import androidx.compose.ui.draw.shadow\n",
    "import androidx.compose.foundation.shape.CircleShape\n",
):
    symbol = gone.rsplit(".", 1)[1].strip()

    check(
        symbol not in code(toggles.replace(gone, "")),
        f"toggles: {symbol} is still used, so its import cannot be removed",
    )

    toggles = replace_once(toggles, gone, "", f"toggles: import {symbol}")

ADDED = (
    "import androidx.compose.animation.core.animateFloatAsState\n",
    "import androidx.compose.foundation.Canvas\n",
    "import androidx.compose.material3.CircularProgressIndicator\n",
    "import androidx.compose.material3.LocalContentColor\n",
    "import androidx.compose.material3.Switch\n",
    "import androidx.compose.material3.SwitchDefaults\n",
    "import androidx.compose.runtime.LaunchedEffect\n",
    "import androidx.compose.runtime.mutableStateOf\n",
    "import androidx.compose.runtime.remember\n",
    "import androidx.compose.runtime.setValue\n",
    "import androidx.compose.ui.geometry.Offset\n",
    "import androidx.compose.ui.geometry.lerp\n",
    "import androidx.compose.ui.graphics.StrokeCap\n",
    "import kotlinx.coroutines.delay\n",
)

ANCHOR = "import com.android.geto.designsystem.icon.GetoIcons\n"

if check(toggles.count(ANCHOR) == 1, "toggles: the import anchor was not found"):
    toggles = toggles.replace(ANCHOR, ANCHOR + "".join(ADDED), 1)

body = code(toggles)

for symbol in (
    "SWITCH_TRACK_WIDTH",
    "SWITCH_TRACK_HEIGHT",
    "SWITCH_TRACK_BORDER",
    "SWITCH_THUMB_SIZE",
    "SWITCH_THUMB_ELEVATION",
):
    check(symbol not in body, f"toggles: {symbol} should be gone from the code")

# Every import added must actually be used, and every symbol used must be imported. The second
# half is what `tools/check_symbol_imports.py` does across the repo; this is the first half.
#
# ⚠ `getValue` and `setValue` are exempt, and not as a convenience. They are the operators behind
# `var x by remember { mutableStateOf(…) }`: the import is required and the name is never written,
# so a usage count is exactly the wrong test for them — the first draft of this script failed on
# `setValue` for that reason.
DELEGATES = ("getValue", "setValue")

for added in ADDED:
    symbol = added.rsplit(".", 1)[1].strip()

    if symbol in DELEGATES:
        check(" by remember" in code(toggles), f"toggles: {symbol} imported with no delegation")

        continue

    uses = code(toggles.replace(added, "")).count(symbol)

    check(uses >= 1, f"toggles: the new import of {symbol} is unused")

check(body.count("SwitchDefaults.colors(") == 1, "toggles: expected one colours block")

check(body.count("fun GetoSwitch(") == 1, "toggles: expected one GetoSwitch")

check(body.count("fun GetoCheckbox(") == 1, "toggles: the checkbox was disturbed")

check("scheme.surfaceContainerHigh" in body, "toggles: the r21 off-track override was lost")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# AndroidSettingsManagerDialog.kt — the spinner moves into the thumb.
# ─────────────────────────────────────────────────────────────────────────────────────────────

manager = MANAGER.read_text(encoding="utf-8")

manager = replace_once(
    manager,
    """                if (starting) {
                    Spacer(modifier = Modifier.width(8.dp))

                    // The only moving thing on the row, and the only honest answer while the
                    // app is waiting: it has asked Shizuku to start and cannot know yet.
                    CircularProgressIndicator(
                        modifier = Modifier.size(14.dp),
                        strokeWidth = 2.dp,
                    )
                }

""",
    """                // ⚠ **The spinner used to be here — r24 moved it into the switch's thumb**, at
                // the author's instruction. It said the same thing either way, but beside the
                // title it was a ring next to a label and the user had pressed a switch. See
                // `GetoSwitch`'s `busy`.

""",
    "manager: row spinner",
)

for label, old, new in (
    (
        "usable switch",
        """                checked = enabled,
                // ⚠ **The off state in the error palette when the service failed to start.**
                // Was three colour overrides on the Material switch; the drawn one takes the
                // decision rather than the palette, which is the same reading with nothing to
                // keep in step.
                error = failed,
                onCheckedChange = onSetEnabled,""",
        """                checked = enabled,
                // ⚠ **The off state in the error palette when the service failed to start.**
                // One flag rather than the three colour overrides this used to be: the switch
                // takes the decision and derives the palette, so there is nothing to keep in
                // step when the scheme changes.
                error = failed,
                // r24: the ring that used to sit beside the title above.
                busy = starting,
                onCheckedChange = onSetEnabled,""",
    ),
    (
        "unusable switch",
        """                    checked = enabled,
                    error = failed,
                    // Disabled, but not greyed into nothing: this row is still reporting a
                    // real state - a Shevery service that is genuinely running - and the
                    // stock disabled palette makes a true "on" look like a dead control.
                    // Muted rather than grey keeps the reading legible while staying inert.
                    liveWhileDisabled = true,
                    enabled = false,
                    onCheckedChange = null,""",
        """                    checked = enabled,
                    error = failed,
                    busy = starting,
                    // Disabled, but not greyed into nothing: this row is still reporting a
                    // real state - a Shevery service that is genuinely running - and the
                    // stock disabled palette makes a true "on" look like a dead control.
                    // Muted rather than grey keeps the reading legible while staying inert.
                    liveWhileDisabled = true,
                    enabled = false,
                    onCheckedChange = null,""",
    ),
):
    manager = replace_once(manager, old, new, f"manager: {label}")

# ⚠ The import stays only if something else in this 1900-line file still spins. It does — the
# dialog has its own blocking spinner — so this is a check rather than a removal.
check(
    code(manager).count("CircularProgressIndicator") >= 1,
    "manager: CircularProgressIndicator is now unused and its import should be removed",
)

check(code(manager).count("busy = starting") == 2, "manager: both switches should take the spinner")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

TOGGLES.write_text(toggles, encoding="utf-8")

MANAGER.write_text(manager, encoding="utf-8")

for path in (TOGGLES, MANAGER):
    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
