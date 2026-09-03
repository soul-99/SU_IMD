#!/usr/bin/env python3
"""Templates for the next round: the master pill, the pending-revert line, the checkbox.

Three sheets, each answering one question the author has to look at before it is built:

    manager_pill.png              the All on / All off pill, shape A, in three background
                                  weights - "lightly theme colour shaded"
    manager_pending_note.png      the red pending-revert line with its i button, drawn
                                  against the existing busy note it shares a slot with
    hide_wireless_checkbox.png    the nested 'Restore wireless debugging also' checkbox, in
                                  Settings to hide/unhide, which is a checkbox dialog

Palette is DarkGreenColorScheme from design-system/theme/Theme.kt, unmodified. Geometry is
in dp at 3x against the dialogs' own numbers - 10dp row padding, 16dp before the actions.

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
ON_SURFACE = (0xE2, 0xE3, 0xD8)
ON_SURFACE_VARIANT = (0xC5, 0xC8, 0xBA)
OUTLINE = (0x8F, 0x92, 0x85)
OUTLINE_VARIANT = (0x44, 0x48, 0x3D)
PRIMARY = (0xB1, 0xD1, 0x8A)
ON_PRIMARY = (0x1F, 0x37, 0x01)
PRIMARY_CONTAINER = (0x35, 0x4E, 0x16)
ON_PRIMARY_CONTAINER = (0xCD, 0xED, 0xA3)
SECONDARY_CONTAINER = (0x40, 0x4A, 0x33)
ON_SECONDARY_CONTAINER = (0xDC, 0xE7, 0xC8)
SURFACE_VARIANT = (0x44, 0x48, 0x3D)
ERROR = (0xFF, 0xB4, 0xAB)
SCRIM = (0x00, 0x00, 0x00)
GETO_RED = (0xB7, 0x1C, 0x1C)
WHITE = (0xFF, 0xFF, 0xFF)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

ROWS = [
    'Developer settings',
    'USB debugging',
    'Wireless debugging',
    'Accessibility services',
    'Shizuku',
    'Display over other apps',
]

# Shizuku drawn unusable, so the sheets show what "the pill does not touch untogglable
# toggles" looks like: the service is running and honestly reported, and cannot be operated
# because IMD has no configuration to send its intents through.
UNUSABLE = {'Shizuku'}
CHECKED = {'Developer settings', 'USB debugging', 'Shizuku'}

PENDING_NOTE = ('IMD hiding settings currently, any changes made here before revert '
                'will be undone after settings restoration')


def blend(fg, bg, alpha):
    return tuple(int(f * alpha + b * (1 - alpha)) for f, b in zip(fg, bg))


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def rounded(dr, box, r, fill=None, outline=None, width=1):
    dr.rounded_rectangle(box, radius=r, fill=fill, outline=outline, width=width)


def text(dr, xy, s, sz, colour, bold=False, anchor='la'):
    dr.text(xy, s, font=font(sz, bold), fill=colour, anchor=anchor)


def wrapped(dr, x, y, s, sz, colour, max_w, leading):
    """Draw s wrapped to max_w px, returning the y below the last line."""
    f = font(sz)
    words, line = s.split(), ''
    for w in words:
        trial = f'{line} {w}'.strip()
        if f.getlength(trial) > max_w and line:
            dr.text((x, y), line, font=f, fill=colour)
            y += leading
            line = w
        else:
            line = trial
    if line:
        dr.text((x, y), line, font=f, fill=colour)
        y += leading
    return y


def switch(dr, cx, cy, on, muted=False):
    """M3 switch, 52x32dp."""
    w, h = dp(52), dp(32)
    x0, y0 = cx - w // 2, cy - h // 2
    if on:
        track = PRIMARY if not muted else blend(PRIMARY_CONTAINER, SURFACE_CONTAINER_HIGH,
                                                0.45)
        border = track
        thumb = ON_PRIMARY if not muted else blend(PRIMARY, SURFACE_CONTAINER_HIGH, 0.55)
        tr, tx = dp(12), x0 + w - dp(16)
    else:
        track, border, thumb = SURFACE_VARIANT, OUTLINE, OUTLINE
        tr, tx = dp(8), x0 + dp(16)
    rounded(dr, [x0, y0, x0 + w, y0 + h], h // 2, fill=track, outline=border, width=dp(2))
    dr.ellipse([tx - tr, cy - tr, tx + tr, cy + tr], fill=thumb)


def checkbox(dr, x, cy, checked, size=18):
    s = dp(size)
    box = [x, cy - s // 2, x + s, cy + s // 2]
    if checked:
        rounded(dr, box, dp(2), fill=PRIMARY)
        dr.line([x + s * 2 // 9, cy, x + s * 4 // 9, cy + s * 2 // 9],
                fill=ON_PRIMARY, width=dp(2))
        dr.line([x + s * 4 // 9, cy + s * 2 // 9, x + s * 7 // 9, cy - s * 2 // 9],
                fill=ON_PRIMARY, width=dp(2))
    else:
        rounded(dr, box, dp(2), fill=None, outline=ON_SURFACE_VARIANT, width=dp(2))


def info_circle(dr, x, cy, colour, size=18):
    r = dp(size) // 2
    dr.ellipse([x, cy - r, x + 2 * r, cy + r], outline=colour, width=dp(2))
    text(dr, (x + r, cy), 'i', dp(size * 11 // 18), colour, anchor='mm')


def action_button(dr, box, label, container, content):
    rounded(dr, box, dp(20), fill=container)
    cx, cy = (box[0] + box[2]) // 2, (box[1] + box[3]) // 2
    lw = int(font(dp(12), True).getlength(label))
    gx = cx - (dp(24) + lw) // 2 + dp(8)
    dr.ellipse([gx - dp(8), cy - dp(8), gx + dp(8), cy + dp(8)], outline=content, width=dp(2))
    text(dr, (gx + dp(16), cy), label, dp(12), content, bold=True, anchor='lm')


# --------------------------------------------------------------------------------------
# The manager dialog, drawn for sheets 1 and 2
# --------------------------------------------------------------------------------------

def pill(dr, box, container, content, divider):
    r = (box[3] - box[1]) // 2
    rounded(dr, box, r, fill=container)
    mid = (box[0] + box[2]) // 2
    dr.line([mid, box[1] + dp(7), mid, box[3] - dp(7)], fill=divider, width=max(1, dp(1)))
    cy = (box[1] + box[3]) // 2
    text(dr, ((box[0] + mid) // 2, cy), 'All on', dp(14), content, bold=True, anchor='mm')
    text(dr, ((mid + box[2]) // 2, cy), 'All off', dp(14), content, bold=True, anchor='mm')


def title_row(dr, left, y):
    dr.ellipse([left, y, left + dp(32), y + dp(32)], fill=PRIMARY_CONTAINER)
    text(dr, (left + dp(16), y + dp(16)), 'IMD', dp(10), ON_PRIMARY_CONTAINER, bold=True,
         anchor='mm')
    text(dr, (left + dp(44), y + dp(16)), 'IMD Settings Manager', dp(17), ON_SURFACE,
         anchor='lm')
    ix = left + dp(44) + int(font(dp(17)).getlength('IMD Settings Manager')) + dp(10)
    info_circle(dr, ix, y + dp(16), ON_SURFACE_VARIANT)


def manager(pill_style, caption, pending=False, busy=False, w_dp=320):
    """The manager dialog. pill_style is (container, content, divider)."""
    h = dp(504) + (dp(46) if pending else 0) + (dp(22) if busy else 0)
    w = dp(w_dp)
    img = Image.new('RGB', (w, h), SCRIM)
    dr = ImageDraw.Draw(img)

    card = [dp(8), dp(8), w - dp(8), h - dp(8)]
    rounded(dr, card, dp(28), fill=SURFACE_CONTAINER_HIGH)
    left, right = card[0] + dp(20), card[2] - dp(20)

    y = card[1] + dp(20)
    title_row(dr, left, y)
    y += dp(42)

    if pending:
        info_circle(dr, left, y + dp(7), ERROR, size=15)
        y = wrapped(dr, left + dp(24), y, PENDING_NOTE, dp(11), ERROR,
                    right - left - dp(24), dp(15)) + dp(6)

    if busy:
        text(dr, (left, y), 'IMD hiding settings, please wait...', dp(12), PRIMARY,
             anchor='lt')
        y += dp(22)

    for name in ROWS:
        text(dr, (left, y + dp(20)), name, dp(15), ON_SURFACE, anchor='lm')
        switch(dr, right - dp(26), y + dp(20), name in CHECKED, muted=name in UNUSABLE)
        y += dp(40)

    y += dp(10)
    pill(dr, [left, y, right, y + dp(40)], *pill_style)
    y += dp(40) + dp(16)

    bh, gap = dp(40), dp(10)
    half = (right - left - gap) // 2
    action_button(dr, [left, y, left + half, y + bh], 'Unhide settings', GETO_RED, WHITE)
    action_button(dr, [right - half, y, right, y + bh], 'Revert to default',
                  SECONDARY_CONTAINER, ON_SECONDARY_CONTAINER)
    y += bh + dp(6)
    text(dr, (right, y + dp(14)), 'Close', dp(14), PRIMARY, bold=True, anchor='rm')
    return img, caption


def contact(panels, name):
    OUT.mkdir(exist_ok=True)
    cw = max(p[0].size[0] for p in panels)
    ch = max(p[0].size[1] for p in panels)
    pad, cap = dp(14), dp(32)
    out = Image.new('RGB', (pad + (cw + pad) * len(panels), ch + cap + pad * 2), (10, 12, 8))
    dr = ImageDraw.Draw(out)
    for i, (img, caption) in enumerate(panels):
        x = pad + (cw + pad) * i
        out.paste(img, (x, pad))
        text(dr, (x + cw // 2, pad + ch + cap // 2), caption, dp(13), ON_SURFACE_VARIANT,
             anchor='mm')
    path = OUT / name
    out.save(path)
    print(f'wrote {path}  {out.size[0]}x{out.size[1]}')


CARD = SURFACE_CONTAINER_HIGH

A1 = (blend(PRIMARY, CARD, 0.10), PRIMARY, blend(PRIMARY, CARD, 0.40))
A2 = (blend(PRIMARY, CARD, 0.18), PRIMARY, blend(PRIMARY, CARD, 0.50))
A3 = (SURFACE_VARIANT, ON_SURFACE_VARIANT, OUTLINE)


def pill_sheet():
    contact([
        manager(A1, 'A1  primary at 10% - the lightest that still reads as a control'),
        manager(A2, 'A2  primary at 18%'),
        manager(A3, 'A3  surfaceVariant - the theme’s own neutral shade'),
    ], 'manager_pill.png')


def pending_sheet():
    contact([
        manager(A2, 'F  a revert pending', pending=True),
        manager(A2, 'G  pending, and a hide running as well', pending=True, busy=True),
    ], 'manager_pending_note.png')


# --------------------------------------------------------------------------------------
# Sheet 3 - the nested checkbox, in Settings to hide/unhide
# --------------------------------------------------------------------------------------

HIDE_ROWS = [
    ('Developer settings', None),
    ('USB debugging', 'Takes the Shizuku service down with it.'),
    ('Wireless debugging', None),
    ('Accessibility services', 'Only the services picked in settings.'),
]


def hide_dialog(indent_dp, rule, caption, w_dp=320):
    w, h = dp(w_dp), dp(400)
    img = Image.new('RGB', (w, h), SCRIM)
    dr = ImageDraw.Draw(img)
    card = [dp(8), dp(8), w - dp(8), h - dp(8)]
    rounded(dr, card, dp(28), fill=SURFACE_CONTAINER_HIGH)
    left, right = card[0] + dp(20), card[2] - dp(20)

    y = card[1] + dp(22)
    text(dr, (left, y), 'Settings to hide/unhide', dp(16), ON_SURFACE, anchor='lt')
    y += dp(28)
    y = wrapped(dr, left, y, 'Hidden on every launch, and put back from memory.', dp(11),
                ON_SURFACE_VARIANT, right - left, dp(15)) + dp(8)

    for name, note in HIDE_ROWS:
        text(dr, (left, y + dp(13)), name, dp(14), ON_SURFACE, anchor='lm')
        if note:
            text(dr, (left, y + dp(28)), note, dp(10), ON_SURFACE, anchor='lm')
        checkbox(dr, right - dp(20), y + dp(13), True)
        y += dp(40) if not note else dp(52)

        if name == 'Wireless debugging':
            cx = left + dp(indent_dp)
            if rule:
                dr.line([left + dp(6), y - dp(22), left + dp(6), y + dp(13)],
                        fill=OUTLINE_VARIANT, width=dp(2))
                dr.line([left + dp(6), y + dp(13), cx - dp(6), y + dp(13)],
                        fill=OUTLINE_VARIANT, width=dp(2))
            text(dr, (cx, y + dp(13)), 'Restore wireless debugging also', dp(13), ON_SURFACE,
                 anchor='lm')
            checkbox(dr, right - dp(20), y + dp(13), False)
            y += dp(38)

    y += dp(8)
    info_circle(dr, left, y + dp(7), ERROR, size=14)
    wrapped(dr, left + dp(22), y, 'Tick all of them, or the ones left on give the rest away.',
            dp(10), ERROR, right - left - dp(22), dp(14))

    text(dr, (right, card[3] - dp(22)), 'SAVE', dp(13), PRIMARY, bold=True, anchor='rm')
    return img, caption


def checkbox_sheet():
    contact([
        hide_dialog(20, False, 'D  indented only'),
        hide_dialog(24, True, 'E  indented, with an elbow to its parent'),
    ], 'hide_wireless_checkbox.png')


if __name__ == '__main__':
    pill_sheet()
    pending_sheet()
    checkbox_sheet()
