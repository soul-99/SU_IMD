#!/usr/bin/env python3
"""v3-r4p — legacy icons are shaped to the launcher's icon shape, in the app and on shortcuts.

    "apps with adaptive icons generate good shortcut icons but lecagy ones do not ... also in
     the app the legacy app icons are just displayed raw can we also shape them to the app icon
     shape of system launcher?"

Template `design/out/legacy_icons.png`, column **C**, which the author picked: trim the icon's
own transparent margin, scale what is left to fill the shape, mask. It comes out the same size
and silhouette as the adaptive icon beside it.

## ⚠ Why 'no inset' had to become 'trim, then fill'

'No inset' drawn literally is column B, and it still shows a ring: a legacy icon is a finished
48dp picture with its own transparent margin baked in, so filling the canvas with the *bitmap*
does not fill it with the *artwork*. Trimming first is what closes that gap. The author saw both
and chose C.

## ⚠ This does not reverse `DefaultDrawableWrapper`'s recorded decision

That KDoc gives two reasons for passing the system's bitmap through untouched:

* adaptive foregrounds live on a 108-unit canvas of which only 72 shows, so painting the whole
  canvas renders a logo at two thirds size — **only true of adaptive drawables, which this does
  not touch**; and
* `LauncherActivityInfo.getIcon` already carries the OEM's own treatment, so masking would be a
  second mask over the first — **also about the icons that already arrive shaped**. A drawable
  that is not an `AdaptiveIconDrawable` on API 26+ is one nothing has shaped, which is the case
  the author is reporting and the only case this touches.

Both reasons are why the guard is `drawable !is AdaptiveIconDrawable`, and why it is written
down in the new KDoc rather than left to be rediscovered.

## The shape is the platform's, not a squircle this project chose

`AdaptiveIconDrawable(null, null).iconMask` is the device's own icon mask path — the thing OEMs
override — so a teardrop launcher gets teardrops. The earlier reverted version hard-coded a
squircle; this asks. On API 24 and 25 there is no such thing as an icon mask, so nothing is
shaped there and the icons stay exactly as they are today.

## One implementation, two framings

`LegacyIconShaping` is new and public in `:framework:drawable`, because both callers need the
same trim and the same 72/108 arithmetic and two copies would drift:

* **in the app** the mask has to be applied here, since there is no launcher in the loop;
* **on a shortcut** it must *not* be, because `IconCompat.createWithAdaptiveBitmap` hands the
  launcher a full-bleed square and lets it mask and inset — which is the whole reason adaptive
  shortcuts already look right.

`:framework:shortcut-manager` gains the dependency for it.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHAPING = "framework/drawable/src/main/kotlin/com/android/geto/framework/drawable/LegacyIconShaping.kt"

WRAPPER = "framework/drawable/src/main/kotlin/com/android/geto/framework/drawable/DefaultDrawableWrapper.kt"

FACTORY = "framework/shortcut-manager/src/main/kotlin/com/android/geto/framework/shortcutmanager/ShortcutIconFactory.kt"

GRADLE = "framework/shortcut-manager/build.gradle.kts"

APPICON = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppIcon.kt"

LICENCE = '''/*
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
'''

SHAPING_TEXT = LICENCE + '''package com.android.geto.framework.drawable

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.drawable.AdaptiveIconDrawable
import android.graphics.drawable.Drawable
import android.os.Build
import androidx.annotation.RequiresApi

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
     */
    private fun drawFilling(canvas: Canvas, source: Bitmap, size: Int, fraction: Float) {
        val target = size * fraction

        val scale = target / maxOf(source.width, source.height).toFloat()

        val width = source.width * scale

        val height = source.height * scale

        val left = (size - width) / 2f

        val top = (size - height) / 2f

        canvas.drawBitmap(
            source,
            null,
            RectF(left, top, left + width, top + height),
            Paint(Paint.ANTI_ALIAS_FLAG or Paint.FILTER_BITMAP_FLAG),
        )
    }

    /**
     * The smallest rectangle containing every pixel that is not fully transparent.
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
                if (pixels[row + x] ushr 24 == 0) continue

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
'''

WRAPPER_OLD = '''    /**
     * Deliberately renders the icon exactly as the system handed it over, with no mask and
     * no plate.
     *
     * An earlier version drew adaptive layers unmasked and clipped everything — adaptive
     * and legacy alike — to one squircle, so that every row in the app matched. It looked
     * worse, for two reasons that are worth writing down. Adaptive foregrounds are drawn
     * on a 108-unit canvas of which only the middle 72 is ever shown, so painting the
     * whole canvas into the tile renders every logo at two thirds of the size a launcher
     * shows it. And `LauncherActivityInfo.getIcon` already returns whatever treatment the
     * OEM launcher applies, which on many devices is a mask of its own — so the result was
     * a second mask over the first.
     *
     * Matching a launcher exactly means reproducing per-OEM behaviour that is not
     * queryable. Passing the system's own bitmap through is the only version that is right
     * everywhere. This is also what [ShortcutIconFactory] falls back to for legacy icons,
     * so masking here quietly made pinned shortcuts wrong too.
     */
    override suspend fun toByteArray(drawable: Drawable, size: Int): ByteArray = withContext(defaultDispatcher) {
        val stream = ByteArrayOutputStream()

        // Always a fixed square, rather than the drawable's own intrinsic size capped at
        // it. A legacy icon whose intrinsic size is 48px was being rasterised at 48px and
        // then scaled up to a 50dp slot, which on a high-density screen is four times the
        // pixels it has — the icon read as small and soft next to its neighbours. Rendering
        // every icon at one size costs nothing extra for the ones that were already large.
        //
        // The quality argument is ignored for PNG, which is lossless.
        drawable.toBitmap(width = size, height = size)
            .compress(Bitmap.CompressFormat.PNG, 100, stream)

        stream.toByteArray()
    }'''

WRAPPER_NEW = '''    /**
     * Renders an icon the system has already shaped exactly as it handed it over, and shapes
     * one it has not.
     *
     * An earlier version drew adaptive layers unmasked and clipped everything — adaptive
     * and legacy alike — to one squircle, so that every row in the app matched. It looked
     * worse, for two reasons that are worth writing down. Adaptive foregrounds are drawn
     * on a 108-unit canvas of which only the middle 72 is ever shown, so painting the
     * whole canvas into the tile renders every logo at two thirds of the size a launcher
     * shows it. And `LauncherActivityInfo.getIcon` already returns whatever treatment the
     * OEM launcher applies, which on many devices is a mask of its own — so the result was
     * a second mask over the first.
     *
     * ⚠ **Both of those are about icons that already arrive shaped, and neither is true of one
     * that does not.** A drawable that is not an `AdaptiveIconDrawable` on API 26+ has no 108-unit
     * canvas and has had no OEM treatment applied — it is a finished 48dp picture, which is why
     * the author saw legacy icons drawn raw beside shaped ones. [LegacyIconShaping] shapes only
     * those, and asks the platform for the mask rather than choosing a squircle, so the reverted
     * version's third problem — being right only on some devices — does not come back either.
     */
    override suspend fun toByteArray(drawable: Drawable, size: Int): ByteArray = withContext(defaultDispatcher) {
        val stream = ByteArrayOutputStream()

        // Always a fixed square, rather than the drawable's own intrinsic size capped at
        // it. A legacy icon whose intrinsic size is 48px was being rasterised at 48px and
        // then scaled up to a 50dp slot, which on a high-density screen is four times the
        // pixels it has — the icon read as small and soft next to its neighbours. Rendering
        // every icon at one size costs nothing extra for the ones that were already large.
        val rendered = drawable.toBitmap(width = size, height = size)

        val shaped = if (LegacyIconShaping.isLegacy(drawable)) {
            LegacyIconShaping.maskedInApp(source = rendered, size = size)
        } else {
            rendered
        }

        // The quality argument is ignored for PNG, which is lossless.
        shaped.compress(Bitmap.CompressFormat.PNG, 100, stream)

        stream.toByteArray()
    }'''

FACTORY_OLD = '''    private fun legacyBitmapIcon(icon: ByteArray?): IconCompat? {
        if (icon == null || icon.isEmpty()) return null

        val bitmap = BitmapFactory.decodeByteArray(icon, 0, icon.size) ?: return null

        return IconCompat.createWithBitmap(bitmap)
    }'''

FACTORY_NEW = '''    private fun legacyBitmapIcon(icon: ByteArray?): IconCompat? {
        if (icon == null || icon.isEmpty()) return null

        val bitmap = BitmapFactory.decodeByteArray(icon, 0, icon.size) ?: return null

        // ⚠ **An adaptive bitmap, not a plain one, and that is the author's report.**
        // createWithBitmap says "this is a finished picture, do not touch it", so the launcher
        // could not mask it and a legacy shortcut sat square beside round neighbours. Handing
        // over a full-bleed square instead lets the launcher apply its own shape and inset -
        // the same route the adaptive branch above already takes, which is why that one has
        // always looked right.
        //
        // Below API 26 there is no adaptive icon to match, so the finished picture is still the
        // honest answer there.
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return IconCompat.createWithBitmap(bitmap)
        }

        return IconCompat.createWithAdaptiveBitmap(
            LegacyIconShaping.adaptiveCanvas(source = bitmap, size = ADAPTIVE_BITMAP_SIZE),
        )
    }'''

APPICON_OLD = " * One app icon, already masked to a squircle by the drawable wrapper."

APPICON_NEW = """ * One app icon, rendered by the drawable wrapper.
 *
 * ⚠ Not necessarily masked. An icon the system already shaped is passed through untouched; only
 * a legacy one is given the platform's icon mask - see `LegacyIconShaping`. This line used to
 * say every icon was masked to a squircle, which stopped being true when that masking was
 * reverted and was still saying it a round later."""

EDITS: list[tuple[str, str, str]] = [
    (WRAPPER, WRAPPER_OLD, WRAPPER_NEW),
    (FACTORY, FACTORY_OLD, FACTORY_NEW),
    (APPICON, APPICON_OLD, APPICON_NEW),
    # The new dependency, so the factory can see the shaping.
    (
        GRADLE,
        """    implementation(projects.domain.common)
    implementation(projects.domain.framework)""",
        """    implementation(projects.domain.common)
    implementation(projects.domain.framework)
    // r4p: LegacyIconShaping, shared with the in-app renderer so the two cannot disagree about
    // what a shaped legacy icon looks like.
    implementation(projects.framework.drawable)""",
    ),
    # The import for it.
    (
        FACTORY,
        """import androidx.core.graphics.drawable.IconCompat""",
        """import androidx.core.graphics.drawable.IconCompat
import com.android.geto.framework.drawable.LegacyIconShaping""",
    ),
]

AFTER = [
    (WRAPPER, "LegacyIconShaping", 3),
    (FACTORY, "LegacyIconShaping", 2),
    # Three: the adaptive branch's own call, the comment above it that names the function, and
    # the new legacy call. The first draft expected two and forgot the comment - the same trap,
    # counted from the inflating side.
    (FACTORY, "createWithAdaptiveBitmap", 3),
    # Three: the class KDoc's account of what upstream did, the new comment explaining why it
    # was wrong, and the pre-26 fallback that still does it.
    (FACTORY, "createWithBitmap", 3),
    (GRADLE, "projects.framework.drawable", 1),
    (APPICON, "LegacyIconShaping", 1),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    shaping = ROOT / SHAPING

    if shaping.exists():
        print(f"REFUSED: {SHAPING}\n  already exists; this script creates it")
        return 1

    # The wrapper and the factory are in different modules and neither compiles here, so the
    # names they now reach for are asserted against the file that declares them.
    for name in ("fun isLegacy(", "fun trimmed(", "fun adaptiveCanvas(", "fun maskedInApp("):
        if name not in SHAPING_TEXT:
            print(f"REFUSED: {SHAPING}\n  {name!r} is not declared")
            return 1

    shaping.write_text(SHAPING_TEXT, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {SHAPING}  :: new — trim, fill, mask, legacy only")
    print(f"  ok        {WRAPPER}  :: shapes a legacy drawable in the app")
    print(f"  ok        {FACTORY}  :: legacy shortcuts become adaptive bitmaps")
    print(f"  ok        {GRADLE}  :: :framework:drawable on the classpath")
    print(f"  ok        {APPICON}  :: the stale 'already masked to a squircle' KDoc corrected")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
