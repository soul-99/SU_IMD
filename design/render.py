"""Writes every icon asset the app ships, from the geometry in gen.py.

  app/src/main/res/drawable/ic_launcher_foreground.xml   adaptive foreground (vector)
  app/src/main/res/drawable/ic_launcher_monochrome.xml   themed-icon silhouette (vector)
  app/src/main/res/drawable/ic_splash.xml                splash-screen icon (vector)
  app/src/main/res/mipmap-*/ic_launcher.png              legacy, pre-API-26 launchers
  app/src/main/res/mipmap-*/ic_launcher_round.png        legacy circular variant
  app/src/main/ic_launcher-playstore.png                 512px store listing

Needs cairosvg and Pillow; not part of the app build. Run gen.py's sibling trace.py first
if the source artwork ever changes.
"""
import io
import os
import shutil
import sys

import cairosvg
from PIL import Image, ImageDraw

import gen

REPO = sys.argv[1] if len(sys.argv) > 1 else "../suIMD"
RES = os.path.join(REPO, "app/src/main/res")
BACKGROUND = "#FFFFFF"        # matches @color/ic_launcher_background

GEAR, BODY, HOLE = gen.gear_path(), gen.key_body(), gen.key_hole()

FOREGROUND = (
    f'    <path\n        android:fillColor="{gen.GEAR_COLOUR}"\n        android:pathData="{GEAR}" />\n'
    f'    <path\n        android:fillColor="{gen.KEY_COLOUR}"\n        android:pathData="{BODY}" />\n'
    # Painted in the gear colour rather than cut out with even-odd: the shaft overlaps the
    # bow, and an even-odd knockout across the whole key would punch through that overlap
    # as well as the intended hole.
    f'    <path\n        android:fillColor="{gen.GEAR_COLOUR}"\n        android:pathData="{HOLE}" />\n')

# Themed icons are a single tinted silhouette, so the gear alone is used. Knocking the key
# out with even-odd would also knock out every place the key self-overlaps.
MONOCHROME = f'    <path\n        android:fillColor="#FFFFFF"\n        android:pathData="{GEAR}" />\n'

SVG = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="512" height="512">\n'
       f'  <title>SU IMD (Geto+)</title>\n'
       f'  <rect width="108" height="108" fill="{BACKGROUND}"/>\n'
       f'  <path fill="{gen.GEAR_COLOUR}" d="{GEAR}"/>\n'
       f'  <path fill="{gen.KEY_COLOUR}" d="{BODY}"/>\n'
       f'  <path fill="{gen.GEAR_COLOUR}" d="{HOLE}"/>\n</svg>\n')


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    print("wrote", path)


def raster(size):
    """The full 108x108 artwork rendered at `size`, on the launcher background."""
    png = cairosvg.svg2png(bytestring=SVG.encode(), output_width=size, output_height=size)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def masked(size, radius):
    """Legacy icons are pre-masked bitmaps; API 26+ ignores these entirely."""
    art = raster(size)
    mask = Image.new("L", (size * 4, size * 4), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size * 4 - 1, size * 4 - 1), radius=int(radius * size * 4), fill=255)
    art.putalpha(mask.resize((size, size), Image.LANCZOS))
    return art


def main():
    write(f"{RES}/drawable/ic_launcher_foreground.xml", gen.vector(FOREGROUND))
    write(f"{RES}/drawable/ic_launcher_monochrome.xml", gen.vector(MONOCHROME))
    write(f"{RES}/drawable/ic_splash.xml", gen.vector(FOREGROUND))

    for bucket, size in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96),
                         ("xxhdpi", 144), ("xxxhdpi", 192)):
        d = f"{RES}/mipmap-{bucket}"
        os.makedirs(d, exist_ok=True)
        masked(size, 0.22).save(f"{d}/ic_launcher.png")
        masked(size, 0.50).save(f"{d}/ic_launcher_round.png")
        print("wrote", d, f"({size}px)")

    store = raster(512).convert("RGB")
    store.save(os.path.join(REPO, "app/src/main/ic_launcher-playstore.png"))
    print("wrote play-store icon (512px)")

    design = os.path.join(REPO, "design")
    os.makedirs(design, exist_ok=True)
    write(os.path.join(design, "ic_launcher.svg"), SVG)
    for name in ("gen.py", "trace.py", "render.py", "verify.py", "geometry.py"):
        shutil.copy(name, os.path.join(design, name))
    print("copied the generator into design/")


if __name__ == "__main__":
    main()
