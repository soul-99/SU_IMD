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

import android.graphics.BlendMode as AndroidBlendMode
import android.graphics.LinearGradient
import android.graphics.RenderEffect as AndroidRenderEffect
import android.graphics.Shader
import android.os.Build
import androidx.annotation.ChecksSdkIntAtLeast
import androidx.annotation.RequiresApi
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.drawWithContent
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.RenderEffect
import androidx.compose.ui.graphics.asComposeRenderEffect
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.luminance
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.theme.LocalBlurSettings
import com.android.geto.domain.model.BLUR_FADE_RANGE
import com.android.geto.domain.model.BLUR_RADIUS_RANGE

/**
 * A page whose top and bottom edges are blurred and darkened under the floating chrome, fading out
 * into the untouched middle.
 *
 * ⚠ **Each band is a solid part and a ramp, not a ramp alone — r15.** The solid part runs from the
 * page edge to wherever that tab's chrome ends, and the ramp starts there: the author's *"i want
 * the blur to start graduating where searchbar/header (whichever is the bottom most component of
 * that tab) ends, and same for the bottom start graduating after tab bar ends"*. Everything behind
 * the header, the search field and the tab bar is therefore blurred at full strength, and what
 * emerges below or above them is what fades. A band with no solid part is not drawn at all, which
 * is how a tablet gets no bottom band: there is no tab bar down there to hide anything behind.
 *
 * ⚠ **The fade is unconditional; [blur] only decides whether it is a blur.** The author's *"when
 * progressive ui blur is off / old android devices which doesn't support it, use shadow fade
 * instead of blur"*. There is no state of this modifier that leaves a list running flat into the
 * tab bar.
 *
 * ⚠ **`Modifier.graphicsLayer`, and the four rounds it took to get here.** A blurred copy and a
 * sharp copy of the same pixels can be made three ways — a nested `GraphicsLayer`, a second node
 * carrying `Modifier.blur`, or the content walked twice — and on the author's device all three
 * came out empty. What finally showed a blur was neither: **one chained `RenderEffect` on the
 * node's own layer**, which composes the pair inside the effect graph from a single walk. The
 * standalone `GraphicsLayer` API was the common factor in every failure — r13d proved the page
 * itself could be recorded into one and drawn back out, while a `renderEffect` set on that same
 * layer did nothing — so nothing here touches it.
 *
 *     identity ──────────────────────────────────────┐
 *          └── blur ── DST_IN(gradient mask) ── band ─┴── SRC_OVER ──▶ result
 *
 * ⚠ **The ramp is quadratic, `(1 - f)²`.** A straight line from full to nothing has a visible end:
 * the eye finds the point where the slope stops. The squared curve puts most of it in the first
 * third and tails off into nothing, and the same curve drives the blur's alpha mask and the tint
 * so the two arrive together — the author's *"gradual blur, not a sharp demarcation line"*.
 *
 * ⚠ **On the scrolling node, never on a wrapper around it.** r11 moved this to a wrapper `Box` and
 * nothing reached the author's screen for three rounds; moved back onto the list it worked the
 * same day. In a chain it belongs **outside** `verticalScroll`, so the bands sit at the viewport's
 * edges instead of travelling with the content; a lazy list's own modifier is already outside its
 * scrolling.
 *
 * @param strength how much of the treatment to apply, 0 to 1. The pages pass the header's own
 *  collapse, so the band arrives as content starts to disappear under the chrome and is absent
 *  while the page is at the top and there is nothing beneath it to hide.
 * @param topSolid how far the top band stays at full strength — the bottom edge of that tab's
 *  chrome. Zero means no top band.
 * @param bottomSolid the same along the bottom, measured up from the page edge. Zero means no
 *  bottom band, which is what a tablet passes.
 */
@Composable
fun Modifier.progressiveEdgeBlur(
    blur: Boolean,
    topSolid: () -> Dp = { 0.dp },
    bottomSolid: Dp = 0.dp,
    strength: () -> Float = { 1f },
): Modifier {
    val surface = MaterialTheme.colorScheme.surface

    val blurring = blur && supportsProgressiveBlur()

    val dark = surface.luminance() < DARK_SURFACE_LUMINANCE

    // ⚠ **The three numbers come from the theme now — r20.** They used to be constants tuned in
    // this file; the author asked for sliders, and the point of the sliders is that the page
    // bands and the settings manager's frosted window move together on one set of them.
    val settings = LocalBlurSettings.current

    val fadeLength = settings.fadeDp.coerceIn(BLUR_FADE_RANGE).dp

    val blurRadius = settings.radiusDp.coerceIn(BLUR_RADIUS_RANGE).dp

    // ⚠ **Two strengths again — r16 — but not the pair r15 removed.** r15's mistake was making the
    // *blurred* band's tint the weaker one; it is now 0.50/0.45 either way, at the author's
    // *"the blur in dark mode should also have a dark tint"*. What r16 adds back is the other
    // direction: a band with **no** blur behind it is carrying the whole job alone, and he asked
    // for it *"very strong and dark"*. So fade-only is close to opaque where the chrome sits, and
    // still lands on the same quadratic ramp on its way out.
    // ⚠ **The slider governs the blurred band only.** With no blur under it the band is the
    // whole treatment and has a different job — the author asked for that one *"very strong and
    // dark"* — so it keeps its own pair rather than inheriting a number chosen for a different
    // situation. Light and dark stop differing under the slider for the same reason: a value the
    // user set is not a value this file may adjust behind them.
    val fade = surface.copy(
        alpha = when {
            blurring -> settings.tintAlpha
            dark -> SHADOW_DARK
            else -> SHADOW_LIGHT
        },
    )

    // ⚠ **Kept between frames — r29.** `bandStops`, the tint brush and the effect graph are all
    // pure functions of numbers that stop moving the moment the header finishes collapsing, and
    // the effect graph is the expensive one: handing the RenderNode a new `RenderEffect` makes
    // Skia rebuild the filter DAG and throw away the result it had cached. Exact-match keys, no
    // rounding of the radius — this file may not change a pixel — which is enough, because
    // `amount` is 1 for every frame after the first ~88 dp of scroll.
    val cache = remember { BandCache() }

    // ⚠ **Outer, so the tint is painted over the layer's output rather than into it.** Modifiers
    // apply outside-in: this node's `drawContent()` draws everything after it in the chain — the
    // blurred, composited page — and the gradient then goes on top of that, sharp.
    val faded = drawWithContent {
        drawContent()

        val height = size.height

        if (height <= 0f) return@drawWithContent

        // ⚠ **Read here, not in the composable body — r29.** This is the deferral: the two
        // numbers change every frame of a collapse, and reading them at this depth costs a
        // redraw where reading them above cost the whole page a recomposition.
        val top = topSolid().toPx()

        val bottom = bottomSolid.toPx()

        // The guard that used to sit above `faded` and return the chain unchanged. It cannot
        // live there any more — `topSolid` is not a value until it is called — so it draws
        // nothing instead of not existing. No caller passes neither band.
        if (top <= 0f && bottom <= 0f) return@drawWithContent

        // ⚠ **Clamped, never branched on — r17.** The chain's *shape* stays the same at every
        // value, so scrolling off the top does not add and remove a layer node on the frame the
        // page starts moving. At zero the gradient is transparent and the render effect is
        // null: present, and doing nothing.
        val amount = strength().coerceIn(0f, 1f)

        val stops = cache.stops(
            topSolid = top,
            bottomSolid = bottom,
            fade = fadeLength.toPx(),
            height = height,
        )

        drawRect(brush = cache.brush(stops = stops, height = height, fade = fade, amount = amount))
    }

    if (!blurring) return faded

    return faded.graphicsLayer {
        val height = size.height

        val top = topSolid().toPx()

        val bottom = bottomSolid.toPx()

        val amount = strength().coerceIn(0f, 1f)

        val radius = blurRadius.toPx() * amount

        // A zero-radius blur is not a no-op on every driver; some report an error rather than
        // drawing the source unchanged, so below half a pixel there is simply no effect at all.
        if (height <= 0f || radius < MINIMUM_BLUR_PX || (top <= 0f && bottom <= 0f)) {
            renderEffect = null

            return@graphicsLayer
        }

        renderEffect = cache.effect(
            radius = radius,
            stops = cache.stops(
                topSolid = top,
                bottomSolid = bottom,
                fade = fadeLength.toPx(),
                height = height,
            ),
            height = height,
        )

        // The blur samples past the node's edges; clipping would put a hard line back.
        clip = false
    }
}

/**
 * Whether this device can blur at all.
 *
 * `RenderEffect.createBlurEffect` arrived in API 31 and this app runs back to 24. Public because
 * the settings screen asks it too: the author's *"old android devices which doesn't support it —
 * in that case don't give the option in settings also"*.
 *
 * ⚠ **`@ChecksSdkIntAtLeast` is not decoration.** Without it lint cannot see that a call guarded by
 * this function is guarded at all, and every use of the API-31 effect graph below becomes a
 * `NewApi` error — which AGP treats as fatal.
 */
@ChecksSdkIntAtLeast(api = Build.VERSION_CODES.S)
fun supportsProgressiveBlur(): Boolean = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S

/**
 * Both bands as one list of *page*-relative stops: position down the whole node, and how much of
 * the treatment survives there.
 *
 * ⚠ **One list, used twice.** The tint paints it as a colour gradient and the blur's mask paints it
 * as an alpha gradient, so the two cannot drift apart — they are the same numbers. Positions never
 * decrease, which every gradient implementation requires, and the middle of the page is covered by
 * the two zero-strength stops that end each band.
 */
private fun bandStops(
    topSolid: Float,
    bottomSolid: Float,
    fade: Float,
    height: Float,
): List<Pair<Float, Float>> {
    val out = ArrayList<Pair<Float, Float>>()

    val top = topSolid.coerceIn(0f, height)

    val bottom = bottomSolid.coerceIn(0f, height - top)

    // Neither ramp may reach into the other, however short the window.
    val room = ((height - top - bottom) / 2f).coerceAtLeast(0f)

    val ramp = fade.coerceIn(0f, room)

    if (top > 0f) {
        out.add(0f to 1f)

        out.add(top / height to 1f)

        for (step in 1..RAMP_STEPS) {
            val along = step.toFloat() / RAMP_STEPS

            out.add((top + ramp * along) / height to strengthAt(along))
        }
    } else {
        out.add(0f to 0f)
    }

    if (bottom > 0f) {
        val start = height - bottom - ramp

        for (step in 0 until RAMP_STEPS) {
            val along = step.toFloat() / RAMP_STEPS

            out.add((start + ramp * along) / height to strengthAt(1f - along))
        }

        out.add((height - bottom) / height to 1f)

        out.add(1f to 1f)
    } else {
        out.add(1f to 0f)
    }

    return out
}

/**
 * How much of the treatment survives [along] of the way across a ramp.
 *
 * Squared rather than straight: a linear fade has a visible end, because the eye finds the point
 * where the slope stops. This puts most of it in the first third and tails off into nothing.
 */
private fun strengthAt(along: Float): Float = (1f - along) * (1f - along)

/**
 * The effect graph: the node's content, plus a blurred copy of it masked to the bands, laid over.
 *
 * ⚠ **Cached by [BandCache] since r29, and the allocations were never the reason.** Handing the
 * RenderNode a new `RenderEffect` makes Skia rebuild the filter DAG and discard the result it had
 * cached, so an identical graph rebuilt every frame is a screen-sized blur recomputed every frame.
 * Everything below is still a pure function of its three arguments, which is what makes it
 * cacheable at all — keep it that way.
 */
@RequiresApi(Build.VERSION_CODES.S)
private fun bandedBlurEffect(
    radius: Float,
    stops: List<Pair<Float, Float>>,
    height: Float,
): RenderEffect {
    // The node's own content, unchanged. `createOffsetEffect(0, 0)` is the identity effect, and it
    // is needed twice: as the blur's input, and as the thing the band is laid over.
    val identity = AndroidRenderEffect.createOffsetEffect(0f, 0f)

    // ⚠ **Clamp, not Decal.** Decal treats everything outside the source as transparent, which
    // under SRC_OVER is a hole in the strongest part of the band rather than a fade. Clamp's smear
    // is covered by the tint, which is at its darkest in exactly that place.
    val blurred = AndroidRenderEffect.createBlurEffect(
        radius,
        radius,
        identity,
        Shader.TileMode.CLAMP,
    )

    val mask = AndroidRenderEffect.createShaderEffect(
        LinearGradient(
            0f,
            0f,
            0f,
            height,
            IntArray(stops.size) { maskColour(stops[it].second) },
            FloatArray(stops.size) { stops[it].first },
            Shader.TileMode.CLAMP,
        ),
    )

    // Keep the blurred copy only where the mask is opaque: the two bands.
    val band = AndroidRenderEffect.createBlendModeEffect(
        blurred,
        mask,
        AndroidBlendMode.DST_IN,
    )

    return AndroidRenderEffect.createBlendModeEffect(
        identity,
        band,
        AndroidBlendMode.SRC_OVER,
    ).asComposeRenderEffect()
}

/**
 * What the last frame worked out, kept for the next one.
 *
 * ⚠ **One of these per modifier instance**, held by a `remember` inside
 * [progressiveEdgeBlur], and touched only from the draw and layer lambdas — which is to say
 * from the UI thread, one at a time. It is not thread-safe and does not need to be.
 *
 * ⚠ **Exact-match keys.** Rounding the radius would raise the hit rate through the collapse and
 * change what is drawn; nothing here is allowed to change what is drawn. It costs nothing to
 * refuse: past the collapse `amount` is 1, so the radius is constant and every frame hits, and
 * the geometry keys stop moving as soon as the page is laid out.
 *
 * ⚠ **`stops` is keyed by identity, not by value.** [stops] hands back the same list until its
 * inputs move, so `===` is both the cheap test and the correct one — a deep comparison of a
 * ten-element list of boxed pairs every frame would be most of what this is trying to save.
 */
private class BandCache {
    private var stopsTop = Float.NaN

    private var stopsBottom = Float.NaN

    private var stopsFade = Float.NaN

    private var stopsHeight = Float.NaN

    private var stopsValue: List<Pair<Float, Float>> = emptyList()

    // NaN never equals itself, so the first call through each of these always misses.
    fun stops(
        topSolid: Float,
        bottomSolid: Float,
        fade: Float,
        height: Float,
    ): List<Pair<Float, Float>> {
        if (topSolid != stopsTop || bottomSolid != stopsBottom ||
            fade != stopsFade || height != stopsHeight
        ) {
            stopsTop = topSolid

            stopsBottom = bottomSolid

            stopsFade = fade

            stopsHeight = height

            stopsValue = bandStops(
                topSolid = topSolid,
                bottomSolid = bottomSolid,
                fade = fade,
                height = height,
            )
        }

        return stopsValue
    }

    private var brushStops: List<Pair<Float, Float>>? = null

    private var brushHeight = Float.NaN

    private var brushAmount = Float.NaN

    private var brushFade = Color.Unspecified

    private var brushValue: Brush? = null

    fun brush(
        stops: List<Pair<Float, Float>>,
        height: Float,
        fade: Color,
        amount: Float,
    ): Brush {
        val held = brushValue

        if (held != null && stops === brushStops && height == brushHeight &&
            amount == brushAmount && fade == brushFade
        ) {
            return held
        }

        brushStops = stops

        brushHeight = height

        brushAmount = amount

        brushFade = fade

        val built = Brush.verticalGradient(
            colorStops = Array(stops.size) { index ->
                val (position, weight) = stops[index]

                position to fade.copy(alpha = fade.alpha * weight * amount)
            },
            startY = 0f,
            endY = height,
        )

        brushValue = built

        return built
    }

    private var effectRadius = Float.NaN

    private var effectStops: List<Pair<Float, Float>>? = null

    private var effectHeight = Float.NaN

    private var effectValue: RenderEffect? = null

    @RequiresApi(Build.VERSION_CODES.S)
    fun effect(
        radius: Float,
        stops: List<Pair<Float, Float>>,
        height: Float,
    ): RenderEffect {
        val held = effectValue

        if (held != null && radius == effectRadius && stops === effectStops &&
            height == effectHeight
        ) {
            return held
        }

        effectRadius = radius

        effectStops = stops

        effectHeight = height

        val built = bandedBlurEffect(radius = radius, stops = stops, height = height)

        effectValue = built

        return built
    }
}

/** Black at the given alpha, as the packed ARGB int a `LinearGradient` wants. */
private fun maskColour(alpha: Float): Int = (alpha.coerceIn(0f, 1f) * OPAQUE).toInt() shl ALPHA_SHIFT

/**
 * And the same band with no blur under it, which has to do the whole job on its own.
 *
 * Nearly opaque at the chrome's edge, at the author's word: *"make it very strong and dark"*. It
 * is not as heavy as it sounds — the solid part sits behind the header and the search field, where
 * there is nothing to read anyway, and 72 dp of quadratic ramp is all that shows.
 */
private const val SHADOW_DARK = 0.88f

private const val SHADOW_LIGHT = 0.80f

/** Where a surface stops being light and starts being dark. */
private const val DARK_SURFACE_LUMINANCE = 0.5f

/** Below this the blur is skipped rather than asked for. */
private const val MINIMUM_BLUR_PX = 0.5f

/** Full alpha as a gradient colour channel, and where that channel sits in a packed ARGB int. */
private const val OPAQUE = 255f

private const val ALPHA_SHIFT = 24

/** How finely the quadratic ramp is sampled. Five stops; a gradient interpolates between. */
private const val RAMP_STEPS = 4
