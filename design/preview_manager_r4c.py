#!/usr/bin/env python3
"""Templates for r4c's settings-manager changes — the three things to look at before building.

    manager_hide_button.png   the bottom action row in both states: 'Hide settings' tonal with
                              the struck-out eye, and 'Unhide settings' red with the open eye
    manager_pill.png          the 'All off' / 'All on' pill at its present 40dp and at three
                              shorter heights, in the reversed order the author asked for
    manager_layout.png        the whole dialog with the pill moved above Developer options

Palette is DarkGreenColorScheme from design-system/theme/Theme.kt plus GetoRed from
AccentColours.kt, both unmodified. Geometry is in dp at 3x against the dialog's own numbers.

⚠ **The glyphs are the author's own, not new artwork.** `ic_hide_tile` (open eye) and
`ic_hidden_tile` (struck-out eye) are the two states his Hide settings tile already shows. They
are rendered here straight from those files, so what is drawn is what would ship.

Nothing here is generated into the app. These are pictures to decide from.
"""
import io
import pathlib
import re

import cairosvg
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(__file__).resolve().parent / 'out'

S = 3  # px per dp


def dp(v):
    return int(round(v * S))


# DarkGreenColorScheme, verbatim.
SURFACE_CONTAINER_HIGH = (0x28, 0x2B, 0x24)
ON_SURFACE = (0xE2, 0xE3, 0xD8)
ON_SURFACE_VARIANT = (0xC5, 0xC8, 0xBA)
OUTLINE = (0x8F, 0x92, 0x85)
OUTLINE_VARIANT = (0x44, 0x48, 0x3D)
SURFACE_VARIANT = (0x44, 0x48, 0x3D)
PRIMARY = (0xB1, 0xD1, 0x8A)
SECONDARY_CONTAINER = (0x40, 0x4A, 0x33)
ON_SECONDARY_CONTAINER = (0xDC, 0xE7, 0xC8)
BACKDROP = (0x11, 0x14, 0x0E)

GETO_RED = (0xB7, 0x1C, 0x1C)
WHITE = (0xFF, 0xFF, 0xFF)

# The Material disabled palette ActionButton restates, over the card colour, so the greyed
# button in the 'today' strip is the grey the author actually sees.
DIMMED_CONTAINER = (0x4F, 0x52, 0x4B)
DIMMED_CONTENT = (0x77, 0x79, 0x71)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CARD_W = dp(340)
PAD = dp(20)
BODY_W = CARD_W - 2 * PAD

PATH_DATA = re.compile(r'android:pathData="([^"]*)"', re.DOTALL)
FILL_TYPE = re.compile(r'android:fillType="(\w+)"')

ROWS = [
    'Developer options',
    'USB debugging',
    'Wireless debugging',
    'Accessibility services',
    'Shizuku service',
    'Display over other apps',
]


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, dp(sz))


def text(dr, xy, s, sz, colour, bold=False, anchor='la'):
    dr.text(xy, s, font=font(sz, bold), fill=colour, anchor=anchor)


def rounded(dr, box, r, fill=None, outline=None, width=1):
    dr.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def fill_box(im, box, radii, colour):
    """A filled box with a radius per corner, which PIL's rounded_rectangle cannot do.

    `radii` is (top-left, top-right, bottom-right, bottom-left) — Compose's own order for
    `RoundedCornerShape`, so the numbers here are the numbers that would go in the code.

    Built as four quadrants. A uniform rounded rectangle already has the right geometry in the
    quadrant of the corner it was drawn for, so each corner is drawn at its own radius over the
    whole box and only its own quarter is kept. Radii are clamped to half the box, which is
    what makes the quadrants meet in the straight sections and agree there.
    """
    x0, y0, x1, y1 = (int(round(v)) for v in box)
    w, h = x1 - x0, y1 - y0

    limit = min(w, h) // 2
    tl, tr, br, bl = [max(0, min(int(r), limit)) for r in radii]

    mask = Image.new('L', (w, h), 0)
    mx, my = w // 2, h // 2

    for r, quadrant in (
        (tl, (0, 0, mx, my)),
        (tr, (mx, 0, w, my)),
        (br, (mx, my, w, h)),
        (bl, (0, my, mx, h)),
    ):
        corner = Image.new('L', (w, h), 0)

        ImageDraw.Draw(corner).rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=255)

        mask.paste(corner.crop(quadrant), quadrant[:2])

    im.paste(Image.new('RGB', (w, h), colour), (x0, y0), mask)


def glyph(name, colour, size_dp):
    """One of the author's tile vectors, rendered at `size_dp` and tinted like Compose's Icon."""
    source = (ROOT / 'app/src/main/res/drawable' / f'{name}.xml').read_text()

    paths = PATH_DATA.findall(source)
    fills = FILL_TYPE.findall(source)

    if not paths:
        raise SystemExit(f'{name}: no pathData, cannot draw the template from the real shape')

    body = ''.join(
        f'<path d="{d}" fill="#ffffff" fill-rule="'
        f'{"evenodd" if (fills[i] if i < len(fills) else "") == "evenOdd" else "nonzero"}"/>'
        for i, d in enumerate(paths)
    )

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'width="{dp(size_dp)}" height="{dp(size_dp)}">{body}</svg>'
    )

    png = cairosvg.svg2png(bytestring=svg.encode())
    mask = Image.open(io.BytesIO(png)).convert('RGBA').split()[3]

    tinted = Image.new('RGBA', mask.size, colour + (0,))
    tinted.putalpha(mask)

    return tinted


def action_button(im, dr, x, y, w, label, glyph_name, container, content):
    """One ActionButton: 18dp glyph, 8dp gap, labelLarge, Material's own button padding."""
    h = dp(40)

    rounded(dr, (x, y, x + w, y + h), dp(20), fill=container)

    icon = glyph(glyph_name, content, 18)
    f = font(11)
    tw = dr.textlength(label, font=f)

    total = icon.width + dp(8) + tw
    ix = int(x + (w - total) / 2)

    im.paste(icon, (ix, int(y + (h - icon.height) / 2)), icon)
    text(dr, (ix + icon.width + dp(8), y + h / 2), label, 11, content, anchor='lm')

    return h


def pill(im, dr, x, y, w, height_dp, sz=11, gap_dp=6, inner_dp=None, ground=None):
    """The master pill: 'All off' left, 'All on' right, split by a band of the card behind it.

    `gap_dp` is the width of that band and `inner_dp` the radius of the two corners either side
    of it. `inner_dp=None` rounds them as hard as the outer ends, which makes the two halves
    read as two separate stadiums rather than one pill with a bite out of it.
    """
    h = dp(height_dp)
    outer = int(h / 2)
    inner = outer if inner_dp is None else dp(inner_dp)
    gap = dp(gap_dp)

    mid = x + w / 2

    # ⚠ **Filled, not outlined.** MasterPill is a Surface in surfaceVariant with no border at
    # all - the author caught an earlier template drawing it with one. The only line in it
    # today is the hairline divider, and that is the thing being replaced.
    if gap_dp == 0:
        fill_box(im, (x, y, x + w, y + h), [outer] * 4, SURFACE_VARIANT)

        text(dr, (x + w / 4, y + h / 2), 'All off', sz, ON_SURFACE_VARIANT, anchor='mm')
        text(dr, (x + 3 * w / 4, y + h / 2), 'All on', sz, ON_SURFACE_VARIANT, anchor='mm')

        return h

    halves = [
        ((x, y, mid - gap / 2, y + h), (True, False, False, True), 'All off'),
        ((mid + gap / 2, y, x + w, y + h), (False, True, True, False), 'All on'),
    ]

    for box, outer_corners, label in halves:
        # (top-left, top-right, bottom-right, bottom-left)
        radii = [outer if is_outer else inner for is_outer in outer_corners]

        fill_box(im, box, radii, SURFACE_VARIANT)

        x0, _, x1, _ = box

        text(dr, ((x0 + x1) / 2, y + h / 2), label, sz, ON_SURFACE_VARIANT, anchor='mm')

    return h


def toggle_row(im, dr, x, y, w, label, on):
    h = dp(48)

    text(dr, (x, y + h / 2), label, 12, ON_SURFACE, anchor='lm')

    tw, th = dp(46), dp(26)
    tx = x + w - tw

    rounded(
        dr, (tx, y + (h - th) / 2, tx + tw, y + (h + th) / 2), int(th / 2),
        fill=PRIMARY if on else (0x3A, 0x3E, 0x35),
        outline=None if on else OUTLINE, width=max(1, dp(1)),
    )

    knob = dp(10) if not on else dp(11)
    cx = tx + (tw - th / 2 - dp(2) if on else th / 2 + dp(2))
    cy = y + h / 2

    dr.ellipse(
        (cx - knob, cy - knob, cx + knob, cy + knob),
        fill=(0x1F, 0x37, 0x01) if on else OUTLINE,
    )

    return h


def sheet(w, h):
    im = Image.new('RGB', (w, h), BACKDROP)

    return im, ImageDraw.Draw(im)


def caption(dr, x, y, s, colour=ON_SURFACE_VARIANT, bold=False):
    text(dr, (x, y), s, 10, colour, bold=bold)

    return dp(16)


# ---------------------------------------------------------------------------------------
# 1 — the hide/unhide button, both states, against what is there today
# ---------------------------------------------------------------------------------------
def draw_hide_button():
    w = dp(40) + CARD_W + dp(40)
    im, dr = sheet(w, dp(370))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'TODAY', bold=True)
    y += dp(4)

    rounded(dr, (x - dp(8), y, x + CARD_W + dp(8), y + dp(58)), dp(12),
            fill=SURFACE_CONTAINER_HIGH)

    half = (BODY_W - dp(10)) / 2
    by = y + dp(9)

    action_button(im, dr, x, by, half, 'Unhide settings', 'ic_hide_tile',
                  DIMMED_CONTAINER, DIMMED_CONTENT)
    action_button(im, dr, x + half + dp(10), by, half, 'Revert to default', 'ic_revert_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)

    y += dp(58) + dp(6)
    y += caption(dr, x, y, 'nothing hidden: greyed, and the press only raises a toast')

    y += dp(24)

    y += caption(dr, x, y, 'PROPOSED — nothing hidden', bold=True)
    y += dp(4)

    rounded(dr, (x - dp(8), y, x + CARD_W + dp(8), y + dp(58)), dp(12),
            fill=SURFACE_CONTAINER_HIGH)

    by = y + dp(9)

    action_button(im, dr, x, by, half, 'Hide settings', 'ic_hidden_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)
    action_button(im, dr, x + half + dp(10), by, half, 'Revert to default', 'ic_revert_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)

    y += dp(58) + dp(6)
    y += caption(dr, x, y, 'same colour as Revert to default; struck-out eye = what you get')

    y += dp(24)

    y += caption(dr, x, y, 'PROPOSED — something hidden', bold=True)
    y += dp(4)

    rounded(dr, (x - dp(8), y, x + CARD_W + dp(8), y + dp(58)), dp(12),
            fill=SURFACE_CONTAINER_HIGH)

    by = y + dp(9)

    action_button(im, dr, x, by, half, 'Unhide settings', 'ic_hide_tile', GETO_RED, WHITE)
    action_button(im, dr, x + half + dp(10), by, half, 'Revert to default', 'ic_revert_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)

    y += dp(58) + dp(6)
    caption(dr, x, y, 'red as today; open eye = what you get')

    im.save(OUT / 'manager_hide_button.png')


# ---------------------------------------------------------------------------------------
# 2 — how short is 'very small'
# ---------------------------------------------------------------------------------------
def draw_pill():
    im, dr = sheet(dp(40) + CARD_W + dp(40), dp(330))

    x, y = dp(40), dp(24)

    # The card behind the pill, so the gap shows the colour it would really show.
    rounded(dr, (x - dp(20), dp(10), x + BODY_W + dp(20), dp(320)), dp(20),
            fill=SURFACE_CONTAINER_HIGH)

    y += caption(dr, x, y, "TODAY — 40dp, one filled pill, a hairline down the middle",
                 bold=True)
    y += dp(2)
    y += pill(im, dr, x, y, BODY_W, 40, 11, gap_dp=0, inner_dp=0)

    mid = x + BODY_W / 2
    dr.line((mid, y - dp(40) + dp(7), mid, y - dp(7)),
            fill=OUTLINE, width=max(1, dp(1)))

    y += dp(26)

    for gap, inner, note in [
        (4, 2, 'A — 28dp, 4dp gap, inner corners at 2dp'),
        (4, 4, 'B — 28dp, 4dp gap, inner corners at 4dp'),
        (4, 6, 'C — 28dp, 4dp gap, inner corners at 6dp (what you saw before)'),
    ]:
        y += caption(dr, x, y, note, bold=True)
        y += dp(2)
        y += pill(im, dr, x, y, BODY_W, 28, 10, gap_dp=gap, inner_dp=inner,
                  ground=SURFACE_CONTAINER_HIGH)
        y += dp(26)

    im.save(OUT / 'manager_pill.png')


# ---------------------------------------------------------------------------------------
# 3 — the pill in its new place, above Developer options
# ---------------------------------------------------------------------------------------
def draw_layout():
    im, dr = sheet(dp(24) + CARD_W + dp(24), dp(560))

    x0 = dp(24)
    card_h = dp(524)

    rounded(dr, (x0, dp(18), x0 + CARD_W, dp(18) + card_h), dp(28),
            fill=SURFACE_CONTAINER_HIGH)

    x = x0 + PAD
    y = dp(18) + dp(22)

    text(dr, (x, y), 'IMD Settings Manager', 15, ON_SURFACE, bold=True)
    y += dp(34)

    # The pill, moved above the first toggle.
    y += pill(im, dr, x, y, BODY_W, 28, 10, gap_dp=4, inner_dp=2)
    y += dp(10)

    dr.line((x, y, x + BODY_W, y), fill=OUTLINE_VARIANT, width=max(1, dp(1)))
    y += dp(6)

    for i, label in enumerate(ROWS):
        y += toggle_row(im, dr, x, y, BODY_W, label, on=i < 3)

    y += dp(12)

    half = (BODY_W - dp(10)) / 2

    action_button(im, dr, x, y, half, 'Hide settings', 'ic_hidden_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)
    action_button(im, dr, x + half + dp(10), y, half, 'Revert to default', 'ic_revert_tile',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)

    y += dp(40) + dp(6)

    text(dr, (x + BODY_W, y + dp(10)), 'Close', 11, PRIMARY, anchor='rm')

    im.save(OUT / 'manager_layout.png')


def main():
    OUT.mkdir(exist_ok=True)

    draw_hide_button()
    draw_pill()
    draw_layout()

    print('wrote manager_hide_button.png, manager_pill.png, manager_layout.png')


if __name__ == '__main__':
    main()
