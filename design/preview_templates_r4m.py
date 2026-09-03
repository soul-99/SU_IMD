#!/usr/bin/env python3
"""Templates for r4m item 2 — the greyed per-app rows, to decide from before building.

    templates_dialog.png   the Templates dialog in the per-app config page, with the two
                           gated templates shown greyed instead of removed
    per_app_rows.png       the per-app config list, with an already-added gated row drawn
                           unchecked and greyed beside a live one
    blocked_popup.png      the ConfigureFirstDialog a press on either of them raises,
                           in its two shapes — with a path, and the Shevery one without

Palette is DarkGreenColorScheme from design-system/theme/Theme.kt, unmodified. Geometry is in
dp at 3x against the real composables' own numbers: AppSettingTemplateItem's 10dp row padding
and 2/5/5dp spacers, and ListItem's three-line metrics for AppSettingItem.

Labels, descriptions and keys are read from the real
framework/asset-manager/src/main/assets/AppSettingTemplates.json, so the rows say what they
would say on the device.

Greying is Material's disabled pair — content at 38% of onSurface, the control's container at
12% — composited over the surface behind it, which is the same grey the app already draws on
the settings manager's unusable rows.

Nothing here is generated into the app. These are pictures to decide from.
"""
import json
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = pathlib.Path(__file__).resolve().parent / 'out'

S = 3  # px per dp


def dp(v):
    return int(round(v * S))


# DarkGreenColorScheme, verbatim.
SURFACE = (0x12, 0x14, 0x0E)
SURFACE_CONTAINER_HIGH = (0x28, 0x2B, 0x24)
ON_SURFACE = (0xE2, 0xE3, 0xD8)
ON_SURFACE_VARIANT = (0xC5, 0xC8, 0xBA)
OUTLINE = (0x8F, 0x92, 0x85)
PRIMARY = (0xB1, 0xD1, 0x8A)
ON_PRIMARY = (0x1F, 0x37, 0x01)
BACKDROP = (0x11, 0x14, 0x0E)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CARD_W = dp(340)

TEMPLATES = json.loads(
    (ROOT / 'framework/asset-manager/src/main/assets/AppSettingTemplates.json').read_text(),
)

TYPE_TITLE = {'GLOBAL': 'Global', 'SECURE': 'Secure', 'SYSTEM': 'System'}

# The two the author is gating: Display over other apps and Shizuku service.
GATED_KEYS = {'op_system_alert_window', 'shizuku_service'}


def mix(fg, bg, alpha):
    """Material's disabled colours are an alpha over whatever is behind them."""
    return tuple(int(round(f * alpha + b * (1 - alpha))) for f, b in zip(fg, bg))


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, dp(sz))


def text(dr, xy, s, sz, colour, bold=False, anchor='la'):
    dr.text(xy, s, font=font(sz, bold), fill=colour, anchor=anchor)


def sheet(w, h, ground=BACKDROP):
    im = Image.new('RGB', (w, h), ground)

    return im, ImageDraw.Draw(im)


def caption(dr, x, y, s, colour=ON_SURFACE_VARIANT, bold=False):
    text(dr, (x, y), s, 10, colour, bold=bold)

    return dp(16)


def plus(dr, cx, cy, colour, arm_dp=6):
    """GetoIcons.Add at 24dp, drawn as the two bars Material's own glyph is."""
    arm, thick = dp(arm_dp), max(1, dp(1.4))

    dr.rectangle((cx - arm, cy - thick, cx + arm, cy + thick), fill=colour)
    dr.rectangle((cx - thick, cy - arm, cx + thick, cy + arm), fill=colour)


def bin_glyph(dr, cx, cy, colour):
    """Icons.Default.Delete, near enough for a layout template: lid, body, two slots."""
    w, h = dp(7), dp(9)

    dr.rectangle((cx - w, cy - h + dp(3), cx + w, cy - h + dp(4)), fill=colour)
    dr.rectangle((cx - dp(2), cy - h + dp(1), cx + dp(2), cy - h + dp(3)), fill=colour)
    dr.rectangle((cx - w + dp(1.5), cy - h + dp(4), cx + w - dp(1.5), cy + h - dp(2)),
                 fill=colour)


def checkbox(dr, x, y, checked, border, tick_ground, tick):
    """Material's 20dp box with a 2dp border, filled when checked."""
    box = dp(20)
    r = dp(2)

    if checked:
        dr.rounded_rectangle((x, y, x + box, y + box), radius=r, fill=tick_ground)

        dr.line(
            (x + dp(4.5), y + dp(10), x + dp(8.5), y + dp(14), x + dp(15.5), y + dp(6)),
            fill=tick, width=max(1, dp(2)),
        )
    else:
        dr.rounded_rectangle(
            (x, y, x + box, y + box), radius=r, outline=border, width=max(1, dp(2)),
        )

    return box


# ---------------------------------------------------------------------------------------
# 1 — the Templates dialog, two rows greyed instead of removed
# ---------------------------------------------------------------------------------------
def template_row_height(template):
    """Same arithmetic as [template_row], so the card can be sized before anything is drawn."""
    h = dp(10) + dp(17) + dp(5) + dp(13) + dp(5) + dp(13) + dp(10)

    return h + (dp(2) + dp(13) if template.get('description') else 0)


def template_row(dr, x, y, w, template, blocked, ground):
    """AppSettingTemplateItem: 10dp padding, label / description / type / key, add button."""
    pad = dp(10)

    label_c = mix(ON_SURFACE, ground, 0.38) if blocked else ON_SURFACE
    body_c = mix(ON_SURFACE_VARIANT, ground, 0.38) if blocked else ON_SURFACE_VARIANT
    small_c = mix(ON_SURFACE, ground, 0.38) if blocked else ON_SURFACE

    cy = y + pad

    text(dr, (x + pad, cy), template['label'], 12, label_c)
    cy += dp(17)

    if template.get('description'):
        cy += dp(2)

        text(dr, (x + pad, cy), template['description'], 9.5, body_c)

        cy += dp(13)

    cy += dp(5)
    text(dr, (x + pad, cy), TYPE_TITLE[template['settingType']], 9.5, small_c)
    cy += dp(13)

    cy += dp(5)
    text(dr, (x + pad, cy), template['key'], 9.5, small_c)
    cy += dp(13)

    h = cy + pad - y

    plus(
        dr, x + w - pad - dp(12), y + h / 2,
        mix(ON_SURFACE, ground, 0.38) if blocked else ON_SURFACE,
    )

    return h


def draw_templates_dialog():
    ground = SURFACE_CONTAINER_HIGH

    rows_h = sum(template_row_height(t) for t in TEMPLATES)

    w = dp(40) + CARD_W + dp(120)
    im, dr = sheet(w, dp(110) + dp(20) + dp(30) + rows_h + dp(20) + dp(60))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'Per app config  →  Templates', bold=True)
    y += caption(
        dr, x, y,
        'The two gated rows stay in the list, greyed. A tap on either raises the popup below.',
    )
    y += dp(8)

    card_h = dp(20) + dp(30) + rows_h + dp(20)

    dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(28), fill=ground)

    ry = y + dp(20)

    text(dr, (x + dp(20), ry + dp(4)), 'Templates', 16, ON_SURFACE)
    ry += dp(30)

    for t in TEMPLATES:
        ry += template_row(
            dr, x + dp(10), ry, CARD_W - dp(20), t,
            blocked=t['key'] in GATED_KEYS, ground=ground,
        )

    y += card_h + dp(18)

    caption(
        dr, x, y,
        'Greyed: label, description, type, key and the + all at 38%. Nothing is removed.',
    )

    im.save(OUT / 'templates_dialog.png')


# ---------------------------------------------------------------------------------------
# 2 — the per-app config list, an added gated row beside a live one
# ---------------------------------------------------------------------------------------
def app_setting_row(dr, x, y, w, setting, blocked, ground):
    """AppSettingItem: ListItem with overline key, headline label, supporting type."""
    h = dp(88)

    on_c = mix(ON_SURFACE, ground, 0.38) if blocked else ON_SURFACE
    var_c = mix(ON_SURFACE_VARIANT, ground, 0.38) if blocked else ON_SURFACE_VARIANT

    cx = x + dp(16)
    cy = y + (h - dp(20)) / 2

    checkbox(
        dr, cx, cy,
        checked=False if blocked else setting['enabled'],
        border=mix(OUTLINE, ground, 0.38) if blocked else OUTLINE,
        tick_ground=PRIMARY,
        tick=ON_PRIMARY,
    )

    tx = cx + dp(20) + dp(16)
    ty = y + dp(16)

    text(dr, (tx, ty), setting['key'], 9.5, var_c)
    ty += dp(15)

    text(dr, (tx, ty), setting['label'], 12, on_c)
    ty += dp(19)

    text(dr, (tx, ty), TYPE_TITLE[setting['settingType']], 9.5, var_c)

    bin_glyph(dr, x + w - dp(28), y + h / 2, on_c)

    return h


def draw_per_app_rows():
    ground = SURFACE

    shown = [
        dict(TEMPLATES[0], enabled=True),
        dict(TEMPLATES[3], enabled=True),
        dict(TEMPLATES[4], enabled=True),
        dict(TEMPLATES[5], enabled=True),
    ]

    w = dp(40) + CARD_W + dp(120)
    im, dr = sheet(w, dp(110) + dp(88) * len(shown) + dp(80))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'Per app config  →  the rows already added', bold=True)
    y += caption(
        dr, x, y,
        'The two gated rows are drawn unchecked and greyed. The stored tick is not written.',
    )
    y += dp(10)

    list_h = dp(88) * len(shown)

    dr.rectangle((x, y, x + CARD_W, y + list_h), fill=ground)

    ry = y

    for s in shown:
        ry += app_setting_row(
            dr, x, ry, CARD_W, s, blocked=s['key'] in GATED_KEYS, ground=ground,
        )

    y += list_h + dp(18)

    y += caption(
        dr, x, y,
        'Rows 3 and 4 were added while the feature was on and were ticked. They show',
    )
    caption(
        dr, x, y + dp(2),
        'unchecked here only — switch Manage Shizuku back on and the tick comes back.',
    )

    im.save(OUT / 'per_app_rows.png')


# ---------------------------------------------------------------------------------------
# 3 — the popup a press raises, in both its shapes
# ---------------------------------------------------------------------------------------
def blocked_dialog(im, dr, x, y, message, paths):
    pad = dp(20)

    lines = [(message, 12, ON_SURFACE)]

    for p in paths:
        lines.append((p, 9.5, PRIMARY))

    h = pad + dp(18) + sum(dp(24) for _ in paths) + dp(14) + dp(36) + dp(6)

    dr.rounded_rectangle((x, y, x + CARD_W, y + h), radius=dp(28),
                         fill=SURFACE_CONTAINER_HIGH)

    cy = y + pad

    text(dr, (x + pad, cy), lines[0][0], 12, ON_SURFACE)
    cy += dp(18)

    for p in paths:
        cy += dp(10)

        text(dr, (x + pad, cy), p, 9.5, PRIMARY, bold=True)

        cy += dp(14)

    cy += dp(14)

    text(dr, (x + CARD_W - pad, cy + dp(10)), 'Understood', 11, PRIMARY, anchor='ra')

    return h


def draw_blocked_popup():
    w = dp(40) + CARD_W + dp(120)
    im, dr = sheet(w, dp(430))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'What a press on a greyed row says', bold=True)
    y += caption(dr, x, y, 'ConfigureFirstDialog, unchanged — the same one the three '
                           'other surfaces already use.')
    y += dp(10)

    y += blocked_dialog(
        im, dr, x, y,
        'Please configure the settings first',
        [
            'IMD Settings → Shizuku configuration → Manage Shizuku',
            'IMD Settings → Default IMD settings → Display over other apps to hide',
        ],
    )

    y += dp(20)

    y += caption(dr, x, y, 'and on Shevery, where there is nothing to point at:')
    y += dp(4)

    blocked_dialog(
        im, dr, x, y,
        'managing Display over other apps is only',
        [],
    )

    text(dr, (x + dp(20), y + dp(38)), 'supported for Thedjchi fork of Shizuku', 12, ON_SURFACE)

    im.save(OUT / 'blocked_popup.png')


def main():
    OUT.mkdir(exist_ok=True)

    draw_templates_dialog()
    draw_per_app_rows()
    draw_blocked_popup()

    print('wrote templates_dialog.png, per_app_rows.png, blocked_popup.png to design/out')


if __name__ == '__main__':
    main()
