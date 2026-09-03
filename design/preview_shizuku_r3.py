#!/usr/bin/env python3
"""Templates for r3's Shizuku work — the three things that have to be looked at before building.

    shevery_dialog.png        the rewritten Shevery pop-up, with the 'How this works' flow
                              chart in three shapes: A one chain, B two labelled halves,
                              C a rail with no boxes
    thedjchi_dialog.png       the new Thedjchi pop-up, and the ⓘ button beside 'Thedjchi'
                              in the fork row that also opens it
    manage_shizuku_row.png    the new 'Manage Shizuku' master toggle at the top of the
                              section, its bold RECOMMENDED line, and the two rewritten
                              red descriptions below it

Palette is DarkGreenColorScheme from design-system/theme/Theme.kt, unmodified. Geometry is in
dp at 3x against the dialogs' own numbers — 20dp card padding, 8dp between points.

Every sentence drawn here is the author's own, verbatim from the v3 spec, including the
numbering he wrote inside the strings and the spelling of 'fialures', which is queried rather
than corrected.

Nothing here is generated into the app. These are pictures to decide from.
"""
import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent / 'out'

S = 3  # px per dp


def dp(v):
    return int(round(v * S))


# DarkGreenColorScheme, verbatim.
SURFACE_CONTAINER_HIGH = (0x28, 0x2B, 0x24)
SURFACE_CONTAINER = (0x1D, 0x21, 0x1A)
ON_SURFACE = (0xE2, 0xE3, 0xD8)
ON_SURFACE_VARIANT = (0xC5, 0xC8, 0xBA)
OUTLINE = (0x8F, 0x92, 0x85)
OUTLINE_VARIANT = (0x44, 0x48, 0x3D)
PRIMARY = (0xB1, 0xD1, 0x8A)
ON_PRIMARY = (0x1F, 0x37, 0x01)
PRIMARY_CONTAINER = (0x35, 0x4E, 0x16)
ON_PRIMARY_CONTAINER = (0xCD, 0xED, 0xA3)
SURFACE_VARIANT = (0x44, 0x48, 0x3D)
ERROR = (0xFF, 0xB4, 0xAB)
BACKDROP = (0x11, 0x14, 0x0E)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CARD_W = dp(340)
PAD = dp(20)
BODY_W = CARD_W - 2 * PAD

LEAD = "Please open your Shizuku app > Settings and do the following:"

SHEVERY_POINTS = [
    ("1. ErrorProtect ", "ON"),
    ("2. TCP mode ", "ON"),
    ("3. Auto-disable USB debugging ", "OFF"),
    ("4. Stop and restart Shevery service", ""),
]

THEDJCHI_POINTS = [
    ("1. Watchdog ", "OFF"),
    ("2. TCP mode ", "ON"),
    ("3. Auto disable USB debugging ", "OFF"),
    ("4. Stop and restart Shizuku service", ""),
]

TCP_RED = ("you should change your TCP port to something random other than 5555 "
           "for security")
REBOOT_SHEVERY = ("You will need to start Shevery manually atleast once after every "
                  "device reboot.")
REBOOT_SHIZUKU = ("You will need to start Shizuku manually atleast once after every "
                  "device reboot.")

HOW_1 = ("Shevery is supported via Shevery's own ErrorProtect service (make sure it is "
         "turned on within your Shevery app)")
HOW_3 = "Shevery takes upto 40s to restart after revert."
HOW_4 = "Shevery framework might be prone to failures"

# Points 2 and 3 of the old dialog, summarised into four steps.
FLOW = [
    "IMD hides USB debugging settings",
    "Shevery service stops",
    "IMD unhides USB debugging settings",
    "ErrorProtect starts it again (scans every 10s)",
]

RED_1 = ("The original RikkaApps version of Shizuku & Shevery are not supported as they "
         "do not support start-stop intents.")
RED_1_BOLD = ["RikkaApps version of Shizuku", "Shevery", "not supported"]
RED_2 = ("RikkaApps Shizuku is outdated and not maintained now, so it is recommended to "
         "download Thedjchi fork of Shizuku (community maintained).")
RED_2_BOLD = ["outdated"]
RED_2_LINK = "Thedjchi fork of Shizuku (community maintained)"


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def rounded(dr, box, r, fill=None, outline=None, width=1):
    dr.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def text(dr, xy, s, sz, colour, bold=False, anchor='la'):
    dr.text(xy, s, font=font(sz, bold), fill=colour, anchor=anchor)


def runs_for(s, bolds, link=None):
    """Split s into (fragment, bold, link) runs on the phrases in bolds and link."""
    marks = [(s.index(b), b, True, False) for b in bolds if b in s]

    if link and link in s:
        marks.append((s.index(link), link, False, True))

    marks.sort()
    out, i = [], 0

    for start, phrase, bold, is_link in marks:
        if start < i:
            continue

        if start > i:
            out.append((s[i:start], False, False))

        out.append((phrase, bold, is_link))
        i = start + len(phrase)

    if i < len(s):
        out.append((s[i:], False, False))

    return out


def rich(dr, x, y, runs, sz, colour, max_w, leading, link_colour=None):
    """Draw styled runs wrapped to max_w, returning the y below the last line."""
    words = []

    for frag, bold, is_link in runs:
        parts = frag.split(' ')

        for n, w in enumerate(parts):
            if w == '' and n:
                continue

            words.append((w, bold, is_link))

    cur_x, drawn = x, False

    for w, bold, is_link in words:
        f = font(sz, bold)
        piece = w if not drawn else ' ' + w
        adv = f.getlength(piece)

        if cur_x + adv > x + max_w and drawn:
            y += leading
            cur_x, piece, drawn = x, w, False
            adv = f.getlength(piece)

        c = (link_colour or PRIMARY) if is_link else colour
        dr.text((cur_x, y), piece, font=f, fill=c)

        if is_link:
            dr.line([cur_x, y + int(sz * 1.15), cur_x + adv, y + int(sz * 1.15)],
                    fill=c, width=max(1, dp(0.5)))

        cur_x += adv
        drawn = True

    return y + leading


def wrapped(dr, x, y, s, sz, colour, max_w, leading, bold=False):
    return rich(dr, x, y, [(s, bold, False)], sz, colour, max_w, leading)


def card(w, h):
    img = Image.new('RGB', (w + dp(24), h + dp(24)), BACKDROP)
    dr = ImageDraw.Draw(img)
    rounded(dr, [dp(12), dp(12), dp(12) + w, dp(12) + h], dp(28),
            fill=SURFACE_CONTAINER_HIGH)

    return img, dr


def numbered(dr, x, y, points, sz, leading):
    for head, tail in points:
        f, fb = font(sz), font(sz, True)
        dr.text((x, y), head, font=f, fill=ON_SURFACE)

        if tail:
            dr.text((x + f.getlength(head), y), tail, font=fb, fill=ON_SURFACE)

        y += leading

    return y


# --------------------------------------------------------------------------------------
# The three flow-chart shapes
# --------------------------------------------------------------------------------------

def arrow(dr, cx, y0, y1, colour):
    dr.line([cx, y0, cx, y1 - dp(4)], fill=colour, width=max(1, dp(1.5)))
    dr.polygon([(cx - dp(4), y1 - dp(6)), (cx + dp(4), y1 - dp(6)), (cx, y1)], fill=colour)


def node_box(dr, x, y, w, label, sz):
    f = font(sz)
    lines, line = [], ''

    for word in label.split():
        trial = f'{line} {word}'.strip()

        if f.getlength(trial) > w - dp(20) and line:
            lines.append(line)
            line = word
        else:
            line = trial

    if line:
        lines.append(line)

    h = dp(12) + len(lines) * dp(15) + dp(4)
    rounded(dr, [x, y, x + w, y + h], dp(8), fill=SURFACE_VARIANT)

    ty = y + dp(8)

    for ln in lines:
        dr.text((x + dp(10), ty), ln, font=f, fill=ON_SURFACE)
        ty += dp(15)

    return y + h


def flow_a(dr, x, y, w, sz):
    """One chain of four boxes."""
    for n, label in enumerate(FLOW):
        y = node_box(dr, x, y, w, label, sz)

        if n < len(FLOW) - 1:
            arrow(dr, x + w // 2, y + dp(2), y + dp(14), OUTLINE)
            y += dp(16)

    return y


def flow_b(dr, x, y, w, sz):
    """Two labelled halves of two boxes each."""
    for heading, pair in (('To stop', FLOW[:2]), ('To restart', FLOW[2:])):
        text(dr, (x, y), heading, sz, PRIMARY, bold=True)
        y += dp(16)

        for n, label in enumerate(pair):
            y = node_box(dr, x, y, w, label, sz)

            if n == 0:
                arrow(dr, x + w // 2, y + dp(2), y + dp(14), OUTLINE)
                y += dp(16)

        y += dp(14)

    return y


def flow_c(dr, x, y, w, sz):
    """A rail of dots, no boxes."""
    f = font(sz)
    rail = x + dp(5)

    for n, label in enumerate(FLOW):
        lines, line = [], ''

        for word in label.split():
            trial = f'{line} {word}'.strip()

            if f.getlength(trial) > w - dp(22) and line:
                lines.append(line)
                line = word
            else:
                line = trial

        if line:
            lines.append(line)

        dr.ellipse([rail - dp(4), y + dp(3), rail + dp(4), y + dp(11)], fill=PRIMARY)

        ty = y

        for ln in lines:
            dr.text((x + dp(20), ty), ln, font=f, fill=ON_SURFACE)
            ty += dp(15)

        y = ty

        if n < len(FLOW) - 1:
            arrow(dr, rail, y + dp(1), y + dp(13), OUTLINE)
            y += dp(15)

    return y


# --------------------------------------------------------------------------------------
# Sheet 1 — the Shevery dialog, three chart shapes
# --------------------------------------------------------------------------------------

def shevery_card(flow, tag):
    h = dp(760)
    img, dr = card(CARD_W, h)
    x, y = dp(12) + PAD, dp(12) + PAD

    y = wrapped(dr, x, y, LEAD, dp(15), ON_SURFACE, BODY_W, dp(20)) + dp(6)
    y = numbered(dr, x + dp(12), y, SHEVERY_POINTS, dp(14), dp(19)) + dp(10)
    y = wrapped(dr, x, y, TCP_RED, dp(13), ERROR, BODY_W, dp(17)) + dp(8)
    y = rich(dr, x, y, [(REBOOT_SHEVERY, True, False)], dp(13), ON_SURFACE, BODY_W,
             dp(17)) + dp(16)

    dr.line([x, y, x + BODY_W, y], fill=OUTLINE_VARIANT, width=max(1, dp(1)))
    y += dp(14)

    text(dr, (x, y), 'How this works', dp(15), ON_SURFACE, bold=True)
    y += dp(24)

    y = wrapped(dr, x + dp(14), y, '1. ' + HOW_1, dp(13), ON_SURFACE_VARIANT,
                BODY_W - dp(14), dp(17)) + dp(10)

    text(dr, (x + dp(14), y), '2.', dp(13), ON_SURFACE_VARIANT)
    y = flow(dr, x + dp(32), y, BODY_W - dp(46), dp(12)) + dp(12)

    y = wrapped(dr, x + dp(14), y, '3. ' + HOW_3, dp(13), ON_SURFACE_VARIANT,
                BODY_W - dp(14), dp(17)) + dp(6)
    y = wrapped(dr, x + dp(14), y, '4. ' + HOW_4, dp(13), ERROR, BODY_W - dp(14), dp(17))

    y += dp(14)
    text(dr, (x + BODY_W, y), 'Understood', dp(14), PRIMARY, bold=True, anchor='ra')

    label = Image.new('RGB', (img.width, dp(28)), BACKDROP)
    ImageDraw.Draw(label).text((dp(12), dp(6)), tag, font=font(dp(13), True), fill=PRIMARY)

    out = Image.new('RGB', (img.width, img.height + dp(28)), BACKDROP)
    out.paste(label, (0, 0))
    out.paste(img, (0, dp(28)))

    return out


def sheet_shevery():
    cards = [
        shevery_card(flow_b, 'B - as approved, with your wording changes'),
    ]
    w = sum(c.width for c in cards)
    h = max(c.height for c in cards)
    sheet = Image.new('RGB', (w, h), BACKDROP)
    x = 0

    for c in cards:
        sheet.paste(c, (x, 0))
        x += c.width

    sheet.save(OUT / 'shevery_dialog.png')
    print('  shevery_dialog.png')


# --------------------------------------------------------------------------------------
# Sheet 2 — the Thedjchi dialog and the ⓘ beside the fork name
# --------------------------------------------------------------------------------------

def info_circle(dr, x, cy, colour, size=18):
    r = dp(size) // 2
    dr.ellipse([x, cy - r, x + 2 * r, cy + r], outline=colour, width=max(1, dp(1.5)))
    text(dr, (x + r, cy + dp(0.5)), 'i', dp(size * 10 // 18), colour, bold=True, anchor='mm')


def sheet_thedjchi():
    h = dp(300)
    img, dr = card(CARD_W, h)
    x, y = dp(12) + PAD, dp(12) + PAD

    y = wrapped(dr, x, y, LEAD, dp(15), ON_SURFACE, BODY_W, dp(20)) + dp(6)
    y = numbered(dr, x + dp(12), y, THEDJCHI_POINTS, dp(14), dp(19)) + dp(10)
    y = wrapped(dr, x, y, TCP_RED, dp(13), ERROR, BODY_W, dp(17)) + dp(8)
    y = rich(dr, x, y, [(REBOOT_SHIZUKU, True, False)], dp(13), ON_SURFACE, BODY_W, dp(17))

    y += dp(14)
    text(dr, (x + BODY_W, y), 'Understood', dp(14), PRIMARY, bold=True, anchor='ra')

    # The fork row underneath, showing where the ⓘ sits.
    row_h = dp(88)
    out = Image.new('RGB', (img.width, img.height + row_h), BACKDROP)
    out.paste(img, (0, 0))
    rd = ImageDraw.Draw(out)

    ry = img.height + dp(16)
    rounded(rd, [dp(12), ry, dp(12) + CARD_W, ry + dp(56)], dp(12),
            fill=SURFACE_CONTAINER)

    cy = ry + dp(28)
    rd.ellipse([dp(28), cy - dp(10), dp(28) + dp(20), cy + dp(10)], outline=PRIMARY,
               width=max(1, dp(2)))
    rd.ellipse([dp(33), cy - dp(5), dp(33) + dp(10), cy + dp(5)], fill=PRIMARY)

    f = font(dp(14))
    lx = dp(60)
    rd.text((lx, cy - dp(8)), 'Thedjchi', font=f, fill=PRIMARY)
    rd.line([lx, cy + dp(9), lx + f.getlength('Thedjchi'), cy + dp(9)], fill=PRIMARY,
            width=max(1, dp(1)))
    info_circle(rd, lx + int(f.getlength('Thedjchi')) + dp(8), cy, ON_SURFACE_VARIANT)

    rd.text((lx, cy + dp(12)), '/ other forks of Shizuku that support start-stop intents',
            font=font(dp(11)), fill=ON_SURFACE_VARIANT)

    out.save(OUT / 'thedjchi_dialog.png')
    print('  thedjchi_dialog.png')


# --------------------------------------------------------------------------------------
# Sheet 3 — the Manage Shizuku master toggle and the two rewritten red lines
# --------------------------------------------------------------------------------------

def switch(dr, cx, cy, on, muted=False):
    w, h = dp(52), dp(32)
    x0, y0 = cx - w // 2, cy - h // 2

    if on:
        track, border, thumb = PRIMARY, PRIMARY, ON_PRIMARY
        tr, tx = dp(12), x0 + w - dp(16)
    else:
        track, border, thumb = SURFACE_VARIANT, OUTLINE, OUTLINE
        tr, tx = dp(8), x0 + dp(16)

    if muted:
        track = tuple(int(c * 0.45 + s * 0.55)
                      for c, s in zip(track, SURFACE_CONTAINER_HIGH))
        border = track
        thumb = tuple(int(c * 0.55 + s * 0.45)
                      for c, s in zip(thumb, SURFACE_CONTAINER_HIGH))

    rounded(dr, [x0, y0, x0 + w, y0 + h], h // 2, fill=track, outline=border, width=dp(2))
    dr.ellipse([tx - tr, cy - tr, tx + tr, cy + tr], fill=thumb)


def manage_panel(on, muted, tag, note):
    h = dp(300)
    img, dr = card(CARD_W, h)
    x, y = dp(12) + PAD, dp(12) + PAD

    y = wrapped(dr, x, y, 'Shizuku (Thedjchi) configuration in IMD', dp(15), ON_SURFACE,
                BODY_W, dp(21), bold=True) + dp(8)

    dim = ON_SURFACE if not muted else tuple(
        int(c * 0.38 + s * 0.62) for c, s in zip(ON_SURFACE, SURFACE_CONTAINER_HIGH))

    text(dr, (x, y + dp(6)), 'Manage Shizuku', dp(15), dim)
    switch(dr, x + BODY_W - dp(26), y + dp(14), on, muted)
    y += dp(34)

    y = rich(dr, x, y, [('RECOMMENDED ON if you use Shizuku', True, False)], dp(13),
             ON_SURFACE_VARIANT, BODY_W, dp(18)) + dp(14)

    y = rich(dr, x, y, runs_for(RED_1, RED_1_BOLD), dp(12), ERROR, BODY_W, dp(16),
             link_colour=ERROR) + dp(6)
    y = rich(dr, x, y, runs_for(RED_2, RED_2_BOLD, RED_2_LINK), dp(12), ERROR, BODY_W,
             dp(16), link_colour=ERROR) + dp(14)

    if note:
        y = wrapped(dr, x, y, note, dp(12), ON_SURFACE_VARIANT, BODY_W, dp(16))

    label = Image.new('RGB', (img.width, dp(28)), BACKDROP)
    ImageDraw.Draw(label).text((dp(12), dp(6)), tag, font=font(dp(13), True), fill=PRIMARY)

    out = Image.new('RGB', (img.width, img.height + dp(28)), BACKDROP)
    out.paste(label, (0, 0))
    out.paste(img, (0, dp(28)))

    return out


def sheet_manage():
    cards = [
        manage_panel(True, False, 'on  — every field below filled', ''),
        manage_panel(False, True,
                     'off + unusable — a field below is blank',
                     'A tap here says why, and the stored answer is kept so filling the '
                     'field again puts the switch back where it was.'),
    ]
    w = sum(c.width for c in cards)
    h = max(c.height for c in cards)
    sheet = Image.new('RGB', (w, h), BACKDROP)
    x = 0

    for c in cards:
        sheet.paste(c, (x, 0))
        x += c.width

    sheet.save(OUT / 'manage_shizuku_row.png')
    print('  manage_shizuku_row.png')


def main():
    OUT.mkdir(exist_ok=True)
    sheet_shevery()
    sheet_thedjchi()
    sheet_manage()
    print('ok')


if __name__ == '__main__':
    main()
