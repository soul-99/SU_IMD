/*
 *
 *   Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.designsystem.component

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.selection.toggleable
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.minimumInteractiveComponentSize
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.icon.GetoIcons
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.Canvas
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.runtime.setValue
import androidx.compose.runtime.snapshotFlow
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.lerp
import androidx.compose.ui.graphics.StrokeCap
import kotlinx.coroutines.delay

/**
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
    /**
     * A turn-on this switch did not hear about is outstanding.
     *
     * ⚠ **For callers whose press does not arrive through [onCheckedChange] — r25.** The settings
     * manager makes the *whole row* clickable and calls its own handler directly, so a switch
     * watching only its own callback never sees the press the author actually makes. This is that
     * press: the last thing the user asked this control for.
     *
     * Left false by every other call site, which arm themselves by being pressed.
     */
    armed: Boolean = false,
) {
    val scheme = MaterialTheme.colorScheme

    // Disabled, but reporting something true. See [liveWhileDisabled].
    val muted = !enabled && liveWhileDisabled

    val tone: (Color) -> Color = { if (muted) it.copy(alpha = SWITCH_MUTED_ALPHA) else it }

    val offTrack = if (error) scheme.errorContainer else scheme.surfaceContainerHigh

    val offInk = if (error) scheme.error else scheme.outline

    var ticking by remember { mutableStateOf(false) }

    // ⚠ **Armed by a request, not inferred from an edge — r25, and r24 got this wrong.** r24
    // ticked whenever `checked` went false → true, which is not the same question as *did this
    // just turn on*. Opening the settings manager over another app composes its rows before the
    // live states have been read, so every setting that is already on arrives false and then
    // becomes true: three switches ticked on open for a transition nobody caused.
    //
    // A request is the honest trigger. Nothing arms a switch that is merely reading its initial
    // value, so that cannot happen; and `rememberSaveable` means an arm survives the trip to a
    // system settings screen and back, which is what `Display over other apps` does every time it
    // is pressed.
    var awaiting by rememberSaveable { mutableStateOf(false) }

    // ⚠ **One long-lived collector rather than an effect keyed on the values — r26, and r25's
    // shape could not have worked for a bulk action.** `LaunchedEffect(checked)` only restarts
    // when `checked` changes, so an arm that arrives *after* a switch is already on — which is
    // exactly what `All on`, `Unhide settings` and `Revert to default` produce — has nothing left
    // to fire on. Adding `armed` and `busy` to the keys is not the fix either: the effect would
    // then restart in the middle of the one-second hold every time either of them moved, and cut
    // the tick short.
    //
    // Keyed on `Unit` and fed by `rememberUpdatedState`, this sees every change to either value
    // and is interrupted by none of them.
    val liveChecked by rememberUpdatedState(checked)

    // Three routes into one flag, because they are the same event reaching the switch differently:
    // pressed here (below), pressed on a row that owns the press, or already in flight.
    val liveWanted by rememberUpdatedState(armed || busy)

    LaunchedEffect(Unit) {
        snapshotFlow { liveChecked to liveWanted }.collect { (isOn, wanted) ->
            if (wanted) awaiting = true

            // A request that ended up off is a request that failed, and there is nothing to
            // celebrate later. Unless one is still outstanding, in which case it is not over.
            if (!isOn && !wanted) awaiting = false

            if (isOn && awaiting) {
                awaiting = false

                ticking = true

                delay(SWITCH_TICK_HOLD_MILLIS)

                ticking = false
            }
        }
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
        // ⚠ **Wrapped so that pressing the switch arms its own tick**, which is how every
        // caller outside the settings manager gets one without passing anything. Dropped
        // entirely whenever the control is not operable, which is what makes the muted state
        // inert while still being drawn from the enabled palette.
        onCheckedChange = if (enabled && onCheckedChange != null) {
            { want ->
                if (want) awaiting = true

                // `?.invoke` rather than a smart cast: the null check above is a few lines and a
                // lambda boundary away, and this asks the compiler for nothing.
                onCheckedChange?.invoke(want)
            }
        } else {
            null
        },
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

/**
 * The app's checkbox: the author's **C2** — 5 dp corners rather than Material's 2.
 *
 * ⚠ **Drawn rather than themed for one reason only: the corner radius.** Material 3's `Checkbox`
 * has no shape parameter, so *"checkboxes with slightly curved corners"* cannot be asked of it.
 * Everything else here is Material's own behaviour: the 48 dp touch target, the toggleable role,
 * and a tick that appears only when checked.
 */
@Composable
fun GetoCheckbox(
    checked: Boolean,
    onCheckedChange: ((Boolean) -> Unit)?,
    modifier: Modifier = Modifier,
    enabled: Boolean = true,
) {
    val scheme = MaterialTheme.colorScheme

    val fillTarget = when {
        checked && enabled -> scheme.primary
        checked -> scheme.onSurface.copy(alpha = 0.38f)
        else -> Color.Transparent
    }

    val fill by animateColorAsState(
        targetValue = fillTarget,
        animationSpec = tween(durationMillis = TOGGLE_MILLIS, easing = ToggleEasing),
        label = "checkboxFill",
    )

    val outline = when {
        // ⚠ **Full ink — r17b.** An unticked box is nothing but its outline, so a dimmed one is
        // the whole control being hard to see.
        enabled -> scheme.onSurface
        else -> scheme.onSurface.copy(alpha = 0.38f)
    }

    Box(
        modifier = modifier
            .minimumInteractiveComponentSize()
            .then(
                if (onCheckedChange != null) {
                    Modifier.toggleable(
                        value = checked,
                        enabled = enabled,
                        role = Role.Checkbox,
                        onValueChange = onCheckedChange,
                    )
                } else {
                    Modifier
                },
            )
            .size(CHECKBOX_SIZE),
        contentAlignment = Alignment.Center,
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .clip(RoundedCornerShape(CHECKBOX_CORNER))
                .background(fill)
                .then(
                    // Only the empty box is outlined. A border under a filled box shows as a
                    // darker rim wherever the two colours differ by a shade, which at 5 dp of
                    // corner is exactly where the eye goes.
                    if (checked) {
                        Modifier
                    } else {
                        Modifier.border(
                            width = CHECKBOX_STROKE,
                            color = outline,
                            shape = RoundedCornerShape(CHECKBOX_CORNER),
                        )
                    },
                ),
        )

        if (checked) {
            Icon(
                modifier = Modifier.size(CHECKBOX_TICK_SIZE),
                imageVector = GetoIcons.Check,
                contentDescription = null,
                tint = if (enabled) scheme.onPrimary else scheme.surface,
            )
        }
    }
}

/** Material's emphasised easing, the same curve the floating tab bar animates on. */
private val ToggleEasing = CubicBezierEasing(0.2f, 0f, 0f, 1f)

private const val TOGGLE_MILLIS = 200

/**
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

private val CHECKBOX_SIZE: Dp = 20.dp

/** The author's C2. */
private val CHECKBOX_CORNER: Dp = 5.dp

private val CHECKBOX_STROKE: Dp = 2.dp

private val CHECKBOX_TICK_SIZE: Dp = 16.dp
