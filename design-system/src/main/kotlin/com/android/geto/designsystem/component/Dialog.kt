/*
 *
 *   Copyright 2023 Einstein Blanco
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

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.core.MutableTransitionState
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.scaleIn
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.material3.AlertDialogDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.contentColorFor
import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.takeOrElse
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import android.graphics.drawable.ColorDrawable
import android.graphics.drawable.GradientDrawable
import android.os.Build
import android.view.Window
import android.view.WindowManager
import androidx.annotation.RequiresApi
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalView
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogWindowProvider
import com.android.geto.designsystem.theme.LocalOledBackground
import com.android.geto.designsystem.theme.LocalBlurSettings
import com.android.geto.designsystem.theme.WINDOW_RADIUS_FACTOR
import androidx.compose.ui.window.DialogProperties

/**
 * How wide any dialog in this app is allowed to get.
 *
 * A phone in portrait is narrower than this, so on one every dialog fills the width exactly as
 * it is meant to. It is a large screen the number is for: a dialog row is a label on the left
 * and a control on the right, and stretched across a tablet the two stop reading as one row.
 *
 * A flat cap rather than a fraction of the screen, and deliberately. A fraction keeps growing
 * with the display — 60% of a 1280 dp tablet is still 768 dp of line length — whereas what a
 * row of label-plus-control actually wants is a column about as wide as a phone, wherever it
 * is drawn. Expressed as a proportion this is roughly full width on a phone, two thirds of an
 * unfolded foldable, and a third of a large tablet, which is the intent.
 */
private val DIALOG_MAX_WIDTH = 580.dp

/**
 * How much room is left beside a dialog.
 *
 * ⚠ **On a phone this, not [DIALOG_MAX_WIDTH], is what decides a dialog's width.** The cap only
 * bites on a screen wider than 580.dp, so everywhere else a dialog is the screen minus twice
 * this.
 */
private val DIALOG_MARGIN = 16.dp

@Composable
fun DialogContainer(
    modifier: Modifier = Modifier,
    shape: Shape = AlertDialogDefaults.shape,
    /**
     * The card itself.
     *
     * ⚠ **True black under OLED background mode — r13.** Material's default is
     * `surfaceContainerHigh`, which the mode leaves alone on purpose so that a card still
     * separates from the page; the author wants the separation to come from the scrim and the
     * shadow instead, so that a dialog over a black page is black. Read from the theme rather
     * than passed in by each dialog, because he asked for it *"Everywhere"*.
     */
    containerColor: Color = if (LocalOledBackground.current) {
        Color.Black
    } else {
        AlertDialogDefaults.containerColor
    },
    tonalElevation: Dp = AlertDialogDefaults.TonalElevation,
    fullScreen: Boolean = false,
    /**
     * Draw the body straight into the page instead of into a dialog window.
     *
     * ⚠ **For the setup flow, and nothing else so far.** A configuration step during
     * initialisation is a page the user is walking through, not a popup over something they
     * were already doing - so there is no scrim, no card and no outside to tap. The body is the
     * same composable either way, which is the whole reason this is a flag rather than a second
     * copy of each dialog.
     *
     * [shape] is ignored here on purpose: a surface that fills the screen has no corners, and
     * rounding them would show the page behind through four notches.
     */
    flat: Boolean = false,
    /**
     * Keep the platform's own dialog width instead of filling toward [maxWidth].
     *
     * For the dialogs that are a short list of switches rather than a page: the services
     * manager above all, which is opened over somebody else's app from a tile and should stay
     * a small card in the middle of the screen on every device, phones included.
     */
    compact: Boolean = false,
    /**
     * Whether a back press or a tap beside the card closes this dialog.
     *
     * ⚠ **False is for a dialog whose dismissal would *do* something**, and there is exactly one:
     * the force-close popup, whose two answers are "restore everything" and "forget everything".
     * It had `onDismissRequest` wired to the second, so a stray tap beside the card silently
     * discarded a device's worth of pending reverts. A dialog with no harmless way out has no
     * business having an accidental one.
     *
     * Turns off **both** routes, because they are two different mechanisms: the platform's, via
     * [DialogProperties], and this file's own tap handler below — which exists because
     * `usePlatformDefaultWidth = false` leaves the platform nothing to call "outside".
     */
    dismissible: Boolean = true,
    /**
     * Make this dialog's card frosted glass while the Progressive UI blur switch is on: the page
     * shows through it, blurred, and the page **around** it is left exactly as it was.
     *
     * ⚠ **Opt-in, and so far one dialog opts in** — the settings manager, at the author's
     * request. Off elsewhere because a frosted card is a statement that *this* window is the
     * subject and the app behind it is not, which is true of the manager and not of, say, a sort
     * order picker.
     */
    frostedWindow: Boolean = false,
    /**
     * How wide this dialog is allowed to get.
     *
     * Capped for every dialog rather than only the full-screen pages, because the platform's
     * own cap is a fraction of the screen: on a tablet it leaves a two-line dialog spread
     * across most of the width with its buttons a hand's width from its text.
     */
    maxWidth: Dp = DIALOG_MAX_WIDTH,
    /**
     * How much room to leave at each side.
     *
     * The default is what every dialog in the app has always had. The settings manager asks for
     * more, at the author's request — it opens over somebody else's app and was reaching almost
     * to the edges of a phone.
     */
    horizontalMargin: Dp = DIALOG_MARGIN,
    onDismissRequest: () -> Unit,
    content: @Composable () -> Unit,
) {
    // A compact dialog keeps usePlatformDefaultWidth, which is the platform's own inset card -
    // exactly what these dialogs looked like before any of this width work, and what the
    // services manager is meant to look like on every screen.
    //
    // **And no DialogEntrance here**, which is the one thing about this branch worth reading.
    // See that composable for why the others need it: their window is the size of the screen
    // and transparent, so the platform's own window animation has nothing visible to move.
    // This window is not. usePlatformDefaultWidth makes it wrap its content, so the window *is*
    // the card, and the platform is already animating precisely the thing DialogEntrance would
    // animate a second time.
    //
    // Animating it anyway is what put a visible stutter on the services manager. AnimatedVisibility
    // does not compose its content until the transition starts, so for one frame this window had
    // nothing in it and was laid out at nothing - and then the card appeared and the window had
    // to grow to its real size and be re-centred underneath it, while the card was separately
    // scaling up from 0.92. Opened from the tile, over the launcher's own launch animation, the
    // card arrived, snapped smaller, and grew back. Measured off the recording: the card's bottom
    // edge jumped 669 -> 609 -> 561 px in two frames and then crept back to 595 over the next
    // 180 ms.
    //
    // The fix is not a better animation. It is that this dialog never needed one.
    // ⚠ **Before every other branch, because it is the one that is not a dialog at all.**
    // No window, no scrim, no dismissal: a setup step ends by pressing Skip or Next, and both
    // of those are the caller's business rather than this container's.
    if (flat) {
        // ⚠ **Centred and capped, exactly as the dialog branch below.** Without this a setup
        // step was the width of the display, so on a tablet a line of body text ran the whole
        // way across - the author's "on wider/tablet displays they take up the whole screen".
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.TopCenter,
        ) {
            // ⚠ **`frostedWindow` is ignored here, and it has to be.** Frosting is a property
            // of a *window*: it is the window that carries `FLAG_BLUR_BEHIND` and paints the
            // card. A setup step has no window — it draws into the page it is part of — so
            // honouring the flag would mean turning this Surface transparent in exchange for a
            // blur that nothing can apply, and the step would lose its card for nothing.
            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize(),
                color = containerColor,
                tonalElevation = tonalElevation,
            ) {
                // ⚠ **The insets go here, inside the Surface, and that is deliberate.** On the
                // Surface itself the page's own background would stop at the status bar and
                // leave a strip of nothing above it. Inside, the colour reaches the edges and
                // the content starts below the clock - which is the author's "the new
                // initialisation pages take up the position of status bar position so unable to
                // clearly read the text there".
                //
                // safeDrawing rather than statusBars: the screenshots show the footer buttons
                // on the gesture bar as well as the title under the clock, and it covers the
                // cutout too.
                Box(modifier = Modifier.windowInsetsPadding(WindowInsets.safeDrawing)) {
                    content()
                }
            }
        }

        return
    }

    if (compact) {
        // Outside the `Dialog` for the same reason the capped branch below computes it there —
        // though this branch already wrapped its window, so the answer changes nothing here
        // beyond where the value is read.
        val compactFrost = rememberFrostedWindow(
            frostedWindow,
            containerColour = containerColor,
            shape = shape,
        )

        Dialog(
            onDismissRequest = onDismissRequest,
            properties = DialogProperties(
                dismissOnBackPress = dismissible,
                dismissOnClickOutside = dismissible,
            ),
        ) {
            FrostedWindowEffect(compactFrost)

            Surface(
                modifier = modifier,
                shape = shape,
                color = compactFrost.colour(containerColor),
                contentColor = compactFrost.content,
                tonalElevation = tonalElevation,
                content = content,
            )
        }

        return
    }

    // usePlatformDefaultWidth is off for everything else. On a phone it was capping dialogs
    // below the screen width; on a tablet it was letting them grow with the screen. Both are
    // the wrong way round, so the width is decided here: fill what is available, up to
    // maxWidth, centred in the window.
    // ⚠ **Decided out here, before the `Dialog`, because the answer changes the window's own
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
        // The box is what centres it. Capping the surface alone leaves it wherever the
        // filled node happens to place it, which is against one edge.
        //
        // It also has to dismiss on a tap, and that is not decoration either. Turning
        // usePlatformDefaultWidth off makes the dialog window the size of the screen, so this
        // box *is* the whole window: there is no longer any area "outside" the dialog for the
        // platform's own dismissOnClickOutside to fire on, and every ordinary dialog in the
        // app silently stopped closing when tapped beside. Handling the tap here gives that
        // back. Full-screen pages are left alone - they carry a back arrow, and an edge tap
        // that threw away a half-filled configuration page would be a worse bug than the one
        // being fixed.
        FrostedWindowEffect(frost)

        if (frost.frosted) {
            // ⚠ **No box behind it, and that is not a shortcut.** The window is the card here, so
            // a full-screen Box would stretch the window straight back to the whole screen and
            // take the blur's confinement with it. There is a real outside again, which is why
            // the hand-rolled tap-to-dismiss is not needed either: `dismissOnClickOutside` has
            // something to fire on.
            //
            // ⚠ **And no `DialogEntrance` either, for the reason the `compact` branch above
            // gives.** AnimatedVisibility does not compose its content until the transition
            // starts, so there is one frame in which this window has nothing in it — and this
            // window is `WRAP_CONTENT`, so that frame lays it out at nothing and the regrow is
            // the visible snap that was measured off the services manager in r13. The platform
            // animates a wrapped window itself; there is nothing left here to add.
            //
            // ⚠ **The margin is taken off the display, not applied around the card.** The box
            // that used to pad this away is gone with the full-screen window, and padding
            // *inside* a wrapped window would only make the window bigger and let its own
            // background drawable paint the margin. So the cap absorbs it: the card stops short
            // of both edges by the same amount it did before.
            val display = LocalConfiguration.current.screenWidthDp.dp

            val frostedWidth = minOf(maxWidth, display - horizontalMargin * 2)

            Surface(
                modifier = Modifier
                    .widthIn(max = frostedWidth)
                    .fillMaxWidth()
                    .then(modifier),
                shape = shape,
                color = frost.colour(containerColor),
                contentColor = frost.content,
                tonalElevation = tonalElevation,
                content = content,
            )

            return@Dialog
        }

        Box(
            modifier = if (fullScreen) {
                // The page supplies its own insets - it is meant to reach the edges of what
                // is left after them.
                Modifier.fillMaxSize()
            } else if (!dismissible) {
                // Same box, same padding, no tap handler: the card still centres and still
                // caps its width, and the space around it simply does nothing.
                Modifier
                    .fillMaxSize()
                    .padding(horizontal = horizontalMargin, vertical = 24.dp)
            } else {
                Modifier
                    .fillMaxSize()
                    .pointerInput(onDismissRequest) {
                        detectTapGestures { onDismissRequest() }
                    }
                    // ⚠ Both branches, always. They differ only in whether a tap beside the
                    // dialog closes it; a margin applied to one of them would give the same
                    // dialog two widths depending on whether it happened to be dismissible.
                    .padding(horizontal = horizontalMargin, vertical = 24.dp)
            },
            contentAlignment = Alignment.Center,
        ) {
            DialogEntrance {
                Surface(
                    // **The cap goes first, and that is the whole fix.** Modifiers constrain
                    // from the outside in, so `fillMaxWidth().widthIn(max = X)` fixes the width
                    // to the full screen and *then* asks for a smaller maximum - which cannot be
                    // honoured, because a maximum below an already-fixed minimum is coerced back
                    // up to it. The cap was silently doing nothing and every dialog was
                    // full-bleed on every screen. Capping first leaves the fill to spend
                    // whatever is left, so a phone still fills and a tablet stops at maxWidth.
                    //
                    // The caller's own modifier is applied last for the same reason: a page
                    // that passes fillMaxSize() would otherwise fix the width before the cap
                    // is read.
                    modifier = if (fullScreen) {
                        Modifier
                            .widthIn(max = maxWidth)
                            .then(modifier)
                    } else {
                        // Without the fill an ordinary dialog shrinks to its content and a
                        // one-word confirmation ends up a chip in the middle of the screen.
                        //
                        // The empty tap handler is what stops a tap *inside* the dialog
                        // reaching the box behind it and dismissing it. Controls within the
                        // surface are hit first and consume their own taps, so this only ever
                        // catches the gaps between them.
                        Modifier
                            .widthIn(max = maxWidth)
                            .fillMaxWidth()
                            .pointerInput(Unit) { detectTapGestures { } }
                            .then(modifier)
                    },
                    shape = shape,
                    color = frost.colour(containerColor),
                    contentColor = frost.content,
                    tonalElevation = tonalElevation,
                    content = content,
                )
            }
        }
    }
}

/**
 * The grow-and-fade a dialog arrives with.
 *
 * Needed because these dialogs turn `usePlatformDefaultWidth` off, which makes the dialog
 * *window* the size of the screen. The platform still animates that window - it just has
 * nothing visible to animate, since the window is transparent and only the card inside it is
 * drawn. So the card used to appear between one frame and the next. This animates the card.
 *
 * **Only for those.** A `compact` dialog keeps the platform width, so its window wraps the card
 * and the platform's own animation already moves it; this one is deliberately not applied there.
 * The window-sizing reason is also why it cannot be: with the window fitted to its content,
 * AnimatedVisibility's one uncomposed frame is a window laid out at nothing, and the regrow is
 * visible. See the `compact` branch above.
 *
 * A [MutableTransitionState] seeded false and flipped true on first composition, rather than
 * `visible = true`: AnimatedVisibility with a plain true has nothing to animate *from* and
 * shows its content immediately.
 *
 * **Entering only, and deliberately.** Animating the exit would mean keeping the dialog
 * composed while it faded, which is the caller's state to decide, not this composable's -
 * every one of the forty call sites removes the dialog the moment its own flag clears. Faking
 * it here by holding the dismissal back would strand the dialogs that pass an empty
 * `onDismissRequest` - the blocking spinners - faded to nothing but still on top of the screen
 * and still swallowing every touch. A close that is instant is a smaller fault than that.
 */
@Composable
private fun DialogEntrance(content: @Composable () -> Unit) {
    val state = remember { MutableTransitionState(false) }

    state.targetState = true

    AnimatedVisibility(
        visibleState = state,
        // From 92%, not from nothing: a dialog that grows from a point reads as being thrown
        // at the user. This is the Material entrance - a short rise from just under full size,
        // with the fade carrying most of the effect.
        enter = fadeIn(animationSpec = tween(durationMillis = DIALOG_ENTER_MILLIS)) +
            scaleIn(
                initialScale = DIALOG_ENTER_SCALE,
                animationSpec = tween(durationMillis = DIALOG_ENTER_MILLIS),
            ),
        content = { content() },
    )
}

/** Short: a dialog that takes its time is a dialog in the way. */
private const val DIALOG_ENTER_MILLIS = 180

private const val DIALOG_ENTER_SCALE = 0.92f

/**
 * The frosted-card state: whether the window may become the card, and what colour to draw in.
 *
 * ⚠ **`Window.setBackgroundBlurRadius` on a window Compose has wrapped — r23, and the round
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
 */
@Composable
private fun rememberFrostedWindow(
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

    val settings = LocalBlurSettings.current

    val density = LocalDensity.current

    val active = enabled && settings.enabled && supportsWindowBlur()

    // The card, painted by the *window*, so the blurred region behind it shows through. The
    // Compose Surface on top is transparent — two translucent layers over each other is a colour
    // nobody can predict.
    val fill = containerColour.copy(
        alpha = FROSTED_MIN_ALPHA + (1f - FROSTED_MIN_ALPHA) * settings.tintAlpha,
    )

    val radius = with(density) { (settings.radiusDp * WINDOW_RADIUS_FACTOR).dp.roundToPx() }

    // ⚠ `Size.Zero` is honest here: every shape this app uses is a `RoundedCornerShape` built from
    // dp, and a dp corner ignores the size it is asked about.
    val corner = with(density) {
        (shape as? RoundedCornerShape)?.topStart?.toPx(Size.Zero, density)
            ?: FROSTED_FALLBACK_CORNER.toPx()
    }

    return FrostedWindow(
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
}

/**
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
) {
    /** Transparent while frosted, because the fill is the window's own background drawable. */
    fun colour(container: Color): Color = if (frosted) Color.Transparent else container
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
}

/**
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
private val FROSTED_FALLBACK_CORNER: Dp = 28.dp

/** The floor on a frosted card's opacity — the author's "we need the contents to be legible". */
private const val FROSTED_MIN_ALPHA = 0.55f

