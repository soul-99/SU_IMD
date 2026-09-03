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
package com.android.geto.framework.drawable

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.drawable.AdaptiveIconDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import androidx.annotation.RequiresApi
import kotlin.math.roundToInt

/**
 * Gives a legacy (non-adaptive) icon the shape the launcher gives everything else.
 *
 * ⚠ **Legacy only, and that is the whole of it.** An [AdaptiveIconDrawable] is already shaped -
 * by the launcher on the home screen, and by whatever treatment `LauncherActivityInfo.getIcon`
 * carries in the app - and [DefaultDrawableWrapper]'s KDoc records what happened the last time
 * everything was masked alike. Both of its reasons are about icons that already arrive shaped,
 * so neither applies to one that does not, and [isLegacy] is where that line is drawn.
 *
 * ⚠ **The shape is asked for, not chosen.** [maskPath] reads
 * `AdaptiveIconDrawable(null, null).iconMask`, which is the device's own icon mask - the thing
 * an OEM overrides - so a launcher that draws teardrops gets teardrops. The reverted version
 * hard-coded a squircle, which is why it could only ever be right on some devices.
 *
 * Below API 26 there is no icon mask to ask for and no adaptive icons to match, so nothing here
 * runs and legacy icons stay exactly as they are.
 */
object LegacyIconShaping {
    /**
     * How much of an adaptive icon's canvas is ever visible: 72 of 108.
     *
     * The artwork is scaled to fill *this*, not the canvas, so what the launcher shows after its
     * own inset is the artwork edge to edge.
     */
    private const val SAFE_ZONE = 72f / 108f

    /** The plate behind a trimmed icon, filling whatever its own margin used to cover. */
    private const val PLATE = Color.WHITE

    /**
     * How far the artwork is drawn past its own box, in pixels.
     *
     * One, and it is a seam-killer rather than a size: see [drawFilling]. Both callers draw into
     * a canvas or under a mask that swallows it.
     */
    private const val BLEED = 1

    /**
     * The alpha below which a pixel is the artwork's anti-aliasing rather than the artwork.
     *
     * ⚠ **Trimming at zero is what left a hairline on the dark icons.** A legacy icon whose own
     * background is a rounded square drawn onto transparency carries a ring of nearly-transparent
     * edge pixels in the background's own colour. At `alpha == 0` that ring counts as artwork, so
     * the trim keeps it, the fill puts it on the outermost row of the square, and the mask draws
     * it over the white plate — where a pixel that was invisible against nothing is a grey-black
     * line against white. On a dark icon that is the author's *"thin black line around margins"*,
     * and it is exactly why only some icons showed it.
     *
     * Sixteen of 255 is about six percent: below anything drawn deliberately, above every
     * anti-aliasing ring.
     */
    private const val ALPHA_FLOOR = 16

    /** Whether this drawable is one nothing has shaped. */
    fun isLegacy(drawable: Drawable): Boolean =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.O && drawable !is AdaptiveIconDrawable

    /**
     * The artwork without its transparent margin.
     *
     * ⚠ **This is the step that separates the author's column C from column B.** A legacy icon
     * is a finished 48dp picture with padding baked into it, so scaling the *bitmap* to fill the
     * shape leaves the *artwork* short of the edge and the plate shows as a ring.
     *
     * Returns the bitmap unchanged when it has no transparent margin, or none that can be found -
     * a fully transparent bitmap has no bounds to trim to and is left alone rather than reduced
     * to nothing.
     */
    fun trimmed(bitmap: Bitmap): Bitmap {
        val bounds = opaqueBounds(bitmap) ?: return bitmap

        if (bounds.width() == bitmap.width && bounds.height() == bitmap.height) return bitmap

        return Bitmap.createBitmap(bitmap, bounds.left, bounds.top, bounds.width(), bounds.height())
    }

    /**
     * A full-bleed square for `IconCompat.createWithAdaptiveBitmap`: plate everywhere, artwork
     * filling the safe zone.
     *
     * ⚠ **Not masked.** The launcher masks and insets this itself, which is exactly why adaptive
     * shortcuts already match the icons beside them, and masking here would be a second mask
     * over the launcher's.
     */
    fun adaptiveCanvas(source: Bitmap, size: Int): Bitmap {
        val canvasBitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)

        val canvas = Canvas(canvasBitmap)

        canvas.drawColor(PLATE)

        drawFilling(canvas, trimmed(source), size, SAFE_ZONE)

        return canvasBitmap
    }

    /**
     * The same artwork, clipped to the platform's icon mask, for drawing inside the app.
     *
     * The mask has to be applied here because there is no launcher in this loop - these bytes go
     * straight to an `AsyncImage` in a list row.
     *
     * The artwork fills the whole square rather than the safe zone: the mask is applied to this
     * bitmap directly, so its edge *is* the visible edge, and insetting as well would draw the
     * icon smaller than every adaptive one beside it.
     */
    @RequiresApi(Build.VERSION_CODES.O)
    fun maskedInApp(source: Bitmap, size: Int): Bitmap {
        val canvasBitmap = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)

        val canvas = Canvas(canvasBitmap)

        val path = maskPath(size)

        canvas.save()

        canvas.clipPath(path)

        canvas.drawColor(PLATE)

        drawFilling(canvas, trimmed(source), size, fraction = 1f)

        canvas.restore()

        return canvasBitmap
    }

    /** The device's own icon mask, scaled to [size]. */
    @RequiresApi(Build.VERSION_CODES.O)
    private fun maskPath(size: Int) = AdaptiveIconDrawable(null, null).apply {
        setBounds(0, 0, size, size)
    }.iconMask

    /**
     * Draws [source] centred, scaled so its longer side fills [fraction] of [size].
     *
     * Aspect ratio is kept: a wide logo stays wide. It is the *longer* side that is filled, so
     * nothing is cropped by this - only by the mask, which is what shapes it.
     *
     * ⚠ **An integer [Rect], not a float one, and this is the author's hairline.** A float
     * rectangle whose edges fall on half-pixels is rounded outward at the top and left and
     * inward at the bottom and right, so the artwork covered its box on two sides and stopped a
     * fraction short on the other two - and the white plate showed through there. *"a very thin
     * white line ... bottom and right edges only"*. Integers cannot round two ways.
     *
     * ⚠ **Plus one pixel of bleed.** Rounding is not the only way a hairline appears: the
     * launcher anti-aliases its own mask against whatever is under the edge, which on the
     * shortcut path is the plate. Drawing one pixel past the box puts artwork there instead. The
     * bleed is clipped by the canvas in the app and hidden under the mask on a shortcut, so it
     * is never visible as artwork.
     */
    private fun drawFilling(canvas: Canvas, source: Bitmap, size: Int, fraction: Float) {
        val target = size * fraction

        val scale = target / maxOf(source.width, source.height).toFloat()

        val width = (source.width * scale).roundToInt()

        val height = (source.height * scale).roundToInt()

        val left = (size - width) / 2

        val top = (size - height) / 2

        canvas.drawBitmap(
            source,
            null,
            Rect(left - BLEED, top - BLEED, left + width + BLEED, top + height + BLEED),
            Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG),
        )
    }

    /**
     * The smallest rectangle containing every pixel that is not fully transparent.
     *
     * "Not fully transparent" is [ALPHA_FLOOR], not zero — see that constant for the hairline
     * that comes of using zero.
     *
     * Read once into an `IntArray` rather than pixel by pixel through `getPixel`, which is a
     * JNI call each time and is the difference between a list that scrolls and one that does
     * not when a device has four hundred apps on it.
     */
    private fun opaqueBounds(bitmap: Bitmap): Rect? {
        val width = bitmap.width

        val height = bitmap.height

        if (width == 0 || height == 0) return null

        val pixels = IntArray(width * height)

        bitmap.getPixels(pixels, 0, width, 0, 0, width, height)

        var left = width
        var top = height
        var right = -1
        var bottom = -1

        for (y in 0 until height) {
            val row = y * width

            for (x in 0 until width) {
                if (pixels[row + x] ushr 24 < ALPHA_FLOOR) continue

                if (x < left) left = x
                if (x > right) right = x
                if (y < top) top = y
                if (y > bottom) bottom = y
            }
        }

        if (right < left || bottom < top) return null

        return Rect(left, top, right + 1, bottom + 1)
    }
}
