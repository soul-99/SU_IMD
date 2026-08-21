"""Renders the generated geometry back in the source PNG's own coordinate space and
diffs it against the original artwork, so 'it looks right' is a number rather than an
opinion. Needs cairosvg and Pillow; not part of the app build."""
import io

import numpy as np
from PIL import Image

import gen

# Re-express the same construction in the source PNG's 1024x1024 space: identity
# transform, gear crest back at its measured radius.
gen.S = 1.0
gen.tx = lambda x: x
gen.ty = lambda y: y
gen.sc = lambda v: v

svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" width="1024" height="1024">'
    '<rect width="1024" height="1024" fill="#FFFFFF"/>'
    f'<path fill="{gen.GEAR_COLOUR}" d="{gen.gear_path()}"/>'
    f'<path fill="{gen.KEY_COLOUR}" d="{gen.key_body()}"/>'
    f'<path fill="{gen.GEAR_COLOUR}" d="{gen.key_hole()}"/></svg>'
)

import cairosvg  # noqa: E402

png = cairosvg.svg2png(bytestring=svg.encode(), output_width=1024, output_height=1024)
mine = np.asarray(Image.open(io.BytesIO(png)).convert("RGB")).astype(int)
Image.fromarray(mine.astype("uint8")).save("rebuilt.png")

src = np.asarray(Image.open("src.png").convert("RGB")).astype(int)
diff = np.abs(mine - src).sum(2)

key = np.array([19, 167, 91])
near_key = np.abs(src - key).sum(2) < 200
for _ in range(6):  # cheap dilation, no scipy needed
    near_key = (near_key | np.roll(near_key, 1, 0) | np.roll(near_key, -1, 0) |
                np.roll(near_key, 1, 1) | np.roll(near_key, -1, 1))

print(f"mean abs diff   : {diff.mean():.3f} / 765")
print(f"pixels off >120 : {(diff > 120).sum():6d}  ({(diff > 120).mean() * 100:.3f}% of frame)")
print(f"   in key       : {(diff[near_key] > 120).sum():6d}")
print(f"   in gear      : {(diff[~near_key] > 120).sum():6d}")

heat = np.zeros((1024, 1024, 3), dtype="uint8")
heat[..., 0] = np.clip(diff, 0, 255)
heat[..., 1] = np.clip(diff, 0, 255) // 3
Image.fromarray(heat).save("diff.png")
