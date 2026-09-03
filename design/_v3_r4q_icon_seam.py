#!/usr/bin/env python3
"""v3-r4q — the hairline of plate along a shaped legacy icon's bottom and right.

    "a very thin white line is visible in legacy app icons shortcut's bottom and right edges
     only, ss attaching see the two bottom ones, otherwise icons now match perfectly now so its
     good if u can't fix that"

## Bottom and right only is the signature of a rounding error, not of a wrong size

`drawFilling` computed a float destination rectangle:

    val left = (size - width) / 2f
    canvas.drawBitmap(source, null, RectF(left, top, left + width, top + height), paint)

With an odd remainder the rectangle's edges fall on half-pixels. The rasteriser rounds the top and
left **outward** and the bottom and right **inward**, so the artwork covers its box on two sides
and stops a fraction short on the other two - and what shows through there is the white plate
underneath. Exactly two edges, exactly one pixel, exactly as reported.

## The fix, in two parts

1. **An integer `Rect`.** Nothing lands on a half-pixel, so the two sides cannot round in
   different directions. For the in-app case, where the artwork fills the whole canvas, this
   alone makes the rectangle exactly `0, 0, size, size`.

2. **A one-pixel bleed outward.** ⚠ Rounding is not the only way a hairline appears: the launcher
   anti-aliases its own mask against whatever is under the edge, and on the shortcut path that is
   the plate. Drawing the artwork one pixel past its box puts artwork under the mask edge instead.
   The bleed is clipped by the canvas on the in-app path and hidden under the mask on the shortcut
   path, so it costs one pixel of overdraw and is never visible as artwork.

⚠ **This is a fix I cannot verify here.** The sandbox cannot render, and the seam is a
sub-pixel artifact of a rasteriser and a launcher mask. The reasoning above is sound and the
change cannot make anything worse - a one-pixel bleed under a mask is invisible either way - but
whether the line is gone is a question only the device answers. The author has already said this
one is optional.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHAPING = "framework/drawable/src/main/kotlin/com/android/geto/framework/drawable/LegacyIconShaping.kt"

OLD = '''    /**
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
    }'''

NEW = '''    /**
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
    }'''

BLEED = '''    /** The plate behind a trimmed icon, filling whatever its own margin used to cover. */
    private const val PLATE = Color.WHITE'''

BLEED_NEW = '''    /** The plate behind a trimmed icon, filling whatever its own margin used to cover. */
    private const val PLATE = Color.WHITE

    /**
     * How far the artwork is drawn past its own box, in pixels.
     *
     * One, and it is a seam-killer rather than a size: see [drawFilling]. Both callers draw into
     * a canvas or under a mask that swallows it.
     */
    private const val BLEED = 1'''


def main() -> int:
    path = ROOT / SHAPING

    if not path.is_file():
        print(f"REFUSED: missing {SHAPING}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in ((BLEED, BLEED_NEW), (OLD, NEW)):
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SHAPING}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    # RectF has no other use in this file, so its import goes with it. Stripped *before* the
    # absence check, not after - the first draft asserted RectF was gone while its own import
    # line was still there, and refused itself.
    text = text.replace("import android.graphics.RectF\n", "", 1)

    if "RectF" in text:
        print(f"REFUSED: {SHAPING}\n  RectF survives the edit")
        return 1

    if "import kotlin.math.roundToInt" not in text:
        text = text.replace(
            "import androidx.annotation.RequiresApi\n",
            "import androidx.annotation.RequiresApi\nimport kotlin.math.roundToInt\n",
            1,
        )

    for token, expected in (
        ("import android.graphics.Rect\n", 1),
        ("import android.graphics.RectF", 0),
        ("import kotlin.math.roundToInt", 1),
        # Five: the declaration plus its four uses in the destination rect.
        ("BLEED", 5),
        ("roundToInt()", 2),
    ):
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SHAPING}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SHAPING}  :: integer destination rect, one pixel of bleed")
    print("  ⚠ unverifiable here — this is a sub-pixel artifact only the device can settle")
    print("\nwrote 1 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
