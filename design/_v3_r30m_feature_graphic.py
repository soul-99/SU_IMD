#!/usr/bin/env python3
"""
r30m — the poster also becomes the F-Droid feature graphic.

The author, asked whether the poster should stay in the screenshot strip or move to
`featureGraphic`: *"both"*.

## What each one is

`images/featureGraphic.png` is the banner F-Droid's client draws **above the description**, full
width. `images/phoneScreenshots/01_poster.png` is the first card in the horizontally scrolling
strip. They are different slots and F-Droid reads them independently, so the same picture can sit
in both — which is what he asked for, and what this writes.

## The shape problem, which the copy does not solve

The poster is **2400 × 2530**, a ratio of 0.95. Nearly square.

* **In the strip** that is merely odd: the nine screenshots beside it are 1080 × 2520 (0.43), and
  F-Droid lays the strip out at a fixed height, so the poster renders more than twice as wide as
  its neighbours and its text is far too small to read at that height.
* **As a feature graphic it is worse**, because that slot is full width: a near-square image at
  full width fills most of a phone screen before the description begins.

So this script also writes a **candidate crop** — outside the repo, for the author to look at, not
into the tree. The poster's own screenshot strip starts at y = 1227, measured rather than guessed,
so the header block above it (title, tagline, both description paragraphs, the security line, the
ten tag pills and the whole features box) is exactly **2400 × 1200 — a ratio of 2.00**, which is
the landscape banner the slot is designed for. Nothing is added and nothing is redrawn; it is his
poster with the part that duplicates the strip below it left off.

⚠ **The crop is not installed.** He asked for the poster in both places and that is what lands.
The crop is a preview of the alternative, and swapping it in is one line here.

Computes the copy in memory, asserts, writes nothing if any assertion fails.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]

IMAGES = ROOT / "fastlane/metadata/android/en-US/images"

POSTER = IMAGES / "phoneScreenshots/01_poster.png"

FEATURE = IMAGES / "featureGraphic.png"

CANDIDATE = Path("/root/work/r30_featureGraphic_cropped.png")

# fdroidserver: ALLOWED_EXTENSIONS = ('png', 'jpg', 'jpeg')
ALLOWED = {".png", ".jpg", ".jpeg"}

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


check(POSTER.exists(), "the poster is not in phoneScreenshots")

check(not FEATURE.exists(), "featureGraphic.png already exists")

check(FEATURE.suffix in ALLOWED, f"{FEATURE.name}: F-Droid reads only {sorted(ALLOWED)}")

check(IMAGES.is_dir(), "the images directory is missing")

# ⚠ The name is fixed. F-Droid looks for exactly `featureGraphic` beside `icon`; a file called
# anything else in this directory is ignored silently rather than reported.
check(FEATURE.name == "featureGraphic.png", "the feature graphic must be named featureGraphic.png")

if POSTER.exists():
    with Image.open(POSTER) as poster:
        width, height = poster.size

        check(poster.format == "PNG", f"the poster is {poster.format}, not PNG")

        # Measured, not assumed: the first row at x=30 that is not the poster's ground colour is
        # the top of its screenshot strip, and everything above it is the header block.
        pixels = poster.convert("RGB").load()

        ground = pixels[8, 8]

        strip_top = next(
            (
                y
                for y in range(height)
                if sum(abs(a - b) for a, b in zip(pixels[30, y], ground)) > 60
            ),
            None,
        )

        check(strip_top is not None, "could not find the poster's screenshot strip")

        if strip_top is not None:
            check(
                1000 < strip_top < height - 500,
                f"the strip starts at y={strip_top}, which is not where a header block ends",
            )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

shutil.copy2(POSTER, FEATURE)

# copy2 carries the source's mode; a read-only file in a repo trips git on Windows.
FEATURE.chmod(0o644)

with Image.open(POSTER) as poster:
    banner = poster.crop((0, 0, width, strip_top - 27))

    banner.save(CANDIDATE, format="PNG", optimize=True)

print(f"featureGraphic.png   {width} x {height}   ratio {width / height:.2f}   (the poster, as asked)")

print(
    f"candidate crop       {banner.size[0]} x {banner.size[1]}   "
    f"ratio {banner.size[0] / banner.size[1]:.2f}   -> {CANDIDATE}",
)

print("\nthe crop is NOT in the repo — it is there to be looked at")

print("ok")
