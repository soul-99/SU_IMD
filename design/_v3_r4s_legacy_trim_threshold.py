#!/usr/bin/env python3
"""v3-r4s — the last legacy icons stop showing a dark hairline at their margins.

    "most legacy icons look fine now but still few like this 1.1.1.1 one show thin black line
     around margins"

## ⚠ The diagnosis, and it is a diagnosis - this cannot be seen from here

`opaqueBounds` trims at `alpha == 0`. **Any** pixel with a single unit of alpha counts as artwork,
and a legacy icon whose own background is a rounded square drawn onto transparency has a ring of
exactly that around its outside: the anti-aliased edge, one or two pixels wide, alpha somewhere
between 1 and 30, and the same colour as the background it belongs to. On a dark icon - 1.1.1.1 is
a dark plate with an orange mark on it - that ring is nearly-invisible **black**.

So the trim keeps it, the artwork is then scaled so that ring lands on the very edge of the
square, and the mask draws it over the white plate. A pixel that was invisible against nothing is
a grey-black hairline against white, all the way round. Which is the report, on exactly the icons
it should be: the ones whose artwork is dark and reaches its own edge, and not the ones with a
real transparent margin - *"most legacy icons look fine now but still few"*.

## The fix

Trim at a threshold instead of at zero. `ALPHA_FLOOR = 16` - about six percent - is below
anything a designer draws on purpose and above every anti-aliasing ring, so the box closes onto
the solid artwork and the ring falls outside it. `BLEED` then does what it was added for: it
stretches the *solid* edge one pixel past the box, and there is no longer a faint one for it to
stretch instead.

⚠ **Nothing else changes.** Same trim, same fill, same mask, same plate. A bitmap that is opaque
edge to edge still trims to itself, and a fully transparent one still returns null and is left
alone rather than reduced to nothing.

⚠ **Unverifiable in this sandbox**, like the seam fix before it: there is no device here to draw
an icon on. The reasoning is above so it can be judged rather than taken on trust, and if the
hairline survives it, the next thing to suspect is the plate rather than the trim.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHAPING = "framework/drawable/src/main/kotlin/com/android/geto/framework/drawable/LegacyIconShaping.kt"

EDITS: list[tuple[str, str]] = [
    (
        """    /** Whether this drawable is one nothing has shaped. */""",
        """    /**
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

    /** Whether this drawable is one nothing has shaped. */""",
    ),
    (
        """     * Read once into an `IntArray` rather than pixel by pixel through `getPixel`, which is a
     * JNI call each time and is the difference between a list that scrolls and one that does
     * not when a device has four hundred apps on it.
     */""",
        """     * "Not fully transparent" is [ALPHA_FLOOR], not zero — see that constant for the hairline
     * that comes of using zero.
     *
     * Read once into an `IntArray` rather than pixel by pixel through `getPixel`, which is a
     * JNI call each time and is the difference between a list that scrolls and one that does
     * not when a device has four hundred apps on it.
     */""",
    ),
    (
        """                if (pixels[row + x] ushr 24 == 0) continue""",
        """                if (pixels[row + x] ushr 24 < ALPHA_FLOOR) continue""",
    ),
]

AFTER = [
    ("private const val ALPHA_FLOOR = 16", 1),
    ("ushr 24 < ALPHA_FLOOR", 1),
    ("ushr 24 == 0", 0),
    # Untouched, and asserted so: the trim's two escape hatches and the bleed.
    ("?: return bitmap", 1),
    ("if (right < left || bottom < top) return null", 1),
    ("private const val BLEED = 1", 1),
]


def main() -> int:
    path = ROOT / SHAPING

    if not path.is_file():
        print(f"REFUSED: missing {SHAPING}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SHAPING}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SHAPING}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SHAPING}  :: the trim closes onto solid artwork")
    print("\nwrote 1 file(s), 3 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
