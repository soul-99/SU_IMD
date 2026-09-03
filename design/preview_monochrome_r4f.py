#!/usr/bin/env python3
"""Template: the themed (monochrome) launcher icon, as it is and as it would be.

The author: *"for the imd app icon when i use themed icon in the launcher the key in the gear
disappears, but it stays legible for settings manager icon, can we fix it"*.

### What is actually wrong

`ic_launcher_foreground.xml` is three paths:

    #A5DBB9   2268 chars,  1 subpath    the gear
    #13A75B   1490 chars, 10 subpaths   the key
    #A5DBB9    268 chars,  1 subpath    the detail drawn back on top of the key

`ic_launcher_monochrome.xml` is **one** path, 2268 chars, solid `#FFFFFF` — the gear alone. The
key was never in it. A themed icon is filled with one colour, so a solid gear is all there is to
draw and the key cannot appear.

`ic_services_monochrome.xml` is one path, **four** subpaths, `fillType="evenOdd"`: the gear with
its glyph punched out of it. That is why the settings manager icon survives theming and this one
does not.

### The fix this renders

The same trick, with the launcher's own three paths concatenated into one even-odd path: the
gear, the key punched out of it, and the detail punched out of that — which even-odd renders
solid again, exactly as `ic_hidden_tile` does with its pupil.

Nothing here is written into the app. This is a picture to decide from.
"""
import io
import pathlib
import re

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
RES = ROOT / 'app/src/main/res/drawable'
OUT = pathlib.Path(__file__).resolve().parent / 'out'

PATH = re.compile(r'android:pathData="([^"]+)"', re.DOTALL)

BACKDROP = (0x11, 0x14, 0x0E)
LABEL = (0xE2, 0xE3, 0xD8)

# Two of the themed palettes a launcher actually uses: a light plate with dark ink, and the
# reverse. A monochrome layer has to read in both, and neither is the app's own green.
THEMES = [
    ('light theme', (0xDC, 0xE7, 0xC8), (0x2A, 0x33, 0x1C)),
    ('dark theme', (0x40, 0x4A, 0x33), (0xDC, 0xE7, 0xC8)),
]

SIZE = 216
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def paths_of(name):
    return PATH.findall((RES / f'{name}.xml').read_text())


def render(path_data, ink, plate, size=SIZE):
    """One even-odd path on a squircle plate, drawn at the adaptive mask's own crop."""
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" '
        f'width="{size}" height="{size}">'
        f'<path d="{path_data}" fill="rgb{ink}" fill-rule="evenodd"/></svg>'
    )

    glyph = Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode()))).convert('RGBA')

    tile = Image.new('RGBA', (size, size), plate + (255,))

    # The adaptive mask: a squircle over the middle 72 of the 108 viewport. Approximated with
    # a rounded rectangle, which is close enough to judge legibility by.
    mask = Image.new('L', (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=int(size * 0.24), fill=255,
    )

    tile.putalpha(mask)
    tile.alpha_composite(glyph)

    return tile


def main():
    OUT.mkdir(exist_ok=True)

    launcher_fg = paths_of('ic_launcher_foreground')
    launcher_mono = paths_of('ic_launcher_monochrome')
    services_mono = paths_of('ic_services_monochrome')

    if len(launcher_fg) != 3 or len(launcher_mono) != 1 or len(services_mono) != 1:
        raise SystemExit('the icons are not the shape this template was written for')

    proposed = ''.join(launcher_fg)

    columns = [
        ('IMD — today', launcher_mono[0]),
        ('IMD — proposed', proposed),
        ('Settings manager', services_mono[0]),
    ]

    pad = 28
    width = pad + len(columns) * (SIZE + pad)
    height = pad * 2 + 26 + len(THEMES) * (SIZE + 26 + pad)

    sheet = Image.new('RGB', (width, height), BACKDROP)
    draw = ImageDraw.Draw(sheet)

    y = pad

    for theme, plate, ink in THEMES:
        draw.text((pad, y), theme.upper(), font=ImageFont.truetype(FONT_B, 15), fill=LABEL)

        y += 26

        for index, (label, data) in enumerate(columns):
            x = pad + index * (SIZE + pad)

            sheet.paste(render(data, ink, plate), (x, y), render(data, ink, plate))

            draw.text(
                (x, y + SIZE + 6), label, font=ImageFont.truetype(FONT, 14), fill=LABEL,
            )

        y += SIZE + 26 + pad

    sheet.save(OUT / 'monochrome_icon.png')

    print(f'wrote monochrome_icon.png  ({len(launcher_fg)} paths merged, '
          f'{proposed.count("M")} subpaths)')


if __name__ == '__main__':
    main()
