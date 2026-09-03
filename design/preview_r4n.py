#!/usr/bin/env python3
"""Templates for r4n items 1, 2, 6 and 8 — the three visual changes, to decide from.

    imd_plus_requirements.png   item 1 + item 2: the 'Shizuku configuration in IMD'
                                requirement row in its three states — Thedjchi met,
                                Thedjchi unmet, and Shevery (red, suffixed, never met) —
                                and what item 2 adds to the Thedjchi ones.
    shizuku_rows_shevery.png    item 6: the Shizuku service row drawn greyed and unticked
                                on Shevery, in Settings to hide/ disable, in Revert to
                                default configuration, and as a per-app template; plus the
                                popup a press raises.
    revert_row_title.png        item 8: the settings-list row and the dialog heading, the
                                current two lines beside the proposed two.
    dev_note_dialog.png         the new upgrade notice, 'Note from developer', beside the
                                one v3 already shows upgraders so the overlap is visible.
    shizuku_setup_page.png      the proposed onboarding page: the Shizuku configuration
                                section with Skip and Manage buttons under it, both fork
                                toggles unselected, and the popup a blocked Manage raises.

⚠ **The suffix, the fork sentence and the popup wording are PROPOSALS, marked as such on
each sheet.** Everything else is read from the tree. The author's strings go in verbatim, so
nothing here is built until he has written or approved those three.

Palette is DarkGreenColorScheme from design-system/theme/Theme.kt, unmodified. Geometry is in
dp at 3x against the real composables' own numbers: SettingToHideRow's 10dp padding and 4dp
spacer, AutoHideRequirementRow's 10dp padding, 12dp dot and 12dp spacer,
AppSettingTemplateItem's 10dp padding and 2/5/5dp spacers, ConfigureFirstDialog's 20dp
padding and 10/14dp spacers.

Greying is Material's disabled pair — content at 38% of onSurface, the control's border at
38% of outline — composited over the surface behind it, exactly as preview_templates_r4m.py
did for the DOOA rows the author is asking these to match.

Nothing here is generated into the app. These are pictures to decide from.
"""
import json
import pathlib
import re

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
OUTLINE_VARIANT = (0x44, 0x48, 0x3D)
PRIMARY = (0xB1, 0xD1, 0x8A)
ON_PRIMARY = (0x1F, 0x37, 0x01)
ERROR = (0xFF, 0xB4, 0xAB)
BACKDROP = (0x11, 0x14, 0x0E)

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

CARD_W = dp(340)

STRINGS = (ROOT / 'feature/settings/src/main/res/values/strings.xml').read_text(
    encoding='utf-8',
)


def s(name):
    """The real string, so the rows say what they would say on the device."""
    m = re.search(rf'<string name="{name}"[^>]*>(.*?)</string>', STRINGS, re.S)

    if m is None:
        raise SystemExit(f'REFUSED: no string named {name}')

    return (
        m.group(1)
        .replace('&amp;', '&')
        .replace('&gt;', '>')
        .replace('&lt;', '<')
        .replace('\\u2192', '→')
        .replace("\\'", "'")
        .replace('\\n', '\n')
    )


# ⚠ Proposals. Every one of these needs the author's own words before anything is built.
PROPOSED_SHEVERY_SUFFIX = ' (Shevery not supported)'
PROPOSED_SHIZUKU_THEDJCHI_ONLY = (
    'managing the Shizuku service is only supported for Thedjchi fork of Shizuku'
)


def mix(fg, bg, alpha):
    """Material's disabled colours are an alpha over whatever is behind them."""
    return tuple(int(round(f * alpha + b * (1 - alpha))) for f, b in zip(fg, bg))


def font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, dp(sz))


def text(dr, xy, string, sz, colour, bold=False):
    dr.text(xy, string, font=font(sz, bold), fill=colour)


def wrapped(dr, xy, string, sz, colour, width, bold=False, leading=13):
    """Draws `string` inside `width` px, returning the height used."""
    f = font(sz, bold)
    words, line, y = string.split(), '', xy[1]

    for word in words:
        trial = f'{line} {word}'.strip()

        if dr.textlength(trial, font=f) > width and line:
            dr.text((xy[0], y), line, font=f, fill=colour)

            y += dp(leading)

            line = word
        else:
            line = trial

    if line:
        dr.text((xy[0], y), line, font=f, fill=colour)

        y += dp(leading)

    return y - xy[1]


def sheet(w, h, ground=BACKDROP):
    im = Image.new('RGB', (w, h), ground)

    return im, ImageDraw.Draw(im)


def caption(dr, x, y, string, colour=ON_SURFACE_VARIANT, bold=False):
    text(dr, (x, y), string, 10, colour, bold=bold)

    return dp(16)


def checkbox(dr, x, y, checked, border, tick_ground, tick):
    """Material's 20dp box with a 2dp border, filled when checked."""
    box, r = dp(20), dp(2)

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


TEMPLATES = json.loads(
    (ROOT / 'framework/asset-manager/src/main/assets/AppSettingTemplates.json').read_text(),
)

TYPE_TITLE = {'GLOBAL': 'Global', 'SECURE': 'Secure', 'SYSTEM': 'System'}


def plus(dr, cx, cy, colour, arm_dp=6):
    arm, thick = dp(arm_dp), max(1, dp(1.4))

    dr.rectangle((cx - arm, cy - thick, cx + arm, cy + thick), fill=colour)
    dr.rectangle((cx - thick, cy - arm, cx + thick, cy + arm), fill=colour)


# ---------------------------------------------------------------------------------------
# SettingToHideRow — 10dp padding, label, 4dp spacer, note, trailing checkbox
# ---------------------------------------------------------------------------------------
def setting_row(dr, x, y, w, label, note, checked, enabled, ground, label_colour=None):
    pad = dp(10)

    content = label_colour or (ON_SURFACE if enabled else mix(ON_SURFACE, ground, 0.38))
    note_c = content

    box_x = x + w - pad - dp(20)
    text_w = box_x - (x + pad) - dp(16)

    cy = y + pad

    used = wrapped(dr, (x + pad, cy), label, 12, content, text_w, leading=17)

    cy += used + dp(4)

    if note:
        cy += wrapped(dr, (x + pad, cy), note, 9.5, note_c, text_w, leading=13)

    h = cy + pad - y

    checkbox(
        dr, box_x, y + (h - dp(20)) / 2,
        checked=checked,
        border=OUTLINE if enabled else mix(OUTLINE, ground, 0.38),
        tick_ground=PRIMARY,
        tick=ON_PRIMARY,
    )

    return h


# ---------------------------------------------------------------------------------------
# AppSettingTemplateItem — 10dp padding, label / description / type / key, add button
# ---------------------------------------------------------------------------------------
def template_row_height(template):
    """Same arithmetic as [template_row], so the card can be sized before anything is drawn."""
    h = dp(10) + dp(17) + dp(5) + dp(13) + dp(5) + dp(13) + dp(10)

    return h + (dp(2) + dp(13) if template.get('description') else 0)


def template_row(dr, x, y, w, template, blocked, ground):
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

    plus(dr, x + w - pad - dp(12), y + h / 2, label_c)

    return h

# ---------------------------------------------------------------------------------------
# 1 — item 1 and item 2: the IMD+ 'Shizuku configuration in IMD' requirement row
# ---------------------------------------------------------------------------------------
def requirement_row(dr, x, y, w, title, note, dot, ground, title_colour=None, suffix=None):
    """AutoHideRequirementRow: 12dp dot, 12dp spacer, title, 4dp spacer, subtitle."""
    pad = dp(10)

    content = {
        'met': ON_SURFACE,
        'unmet': ON_SURFACE,
        'optional': mix(ON_SURFACE, ground, 0.38),
        'error': ON_SURFACE,
    }[dot]

    colour = {
        'met': PRIMARY,
        'unmet': ERROR,
        'optional': OUTLINE_VARIANT,
        'error': ERROR,
    }[dot]

    cy = y + pad

    dr.ellipse((x + pad, cy + dp(3), x + pad + dp(12), cy + dp(15)), fill=colour)

    tx = x + pad + dp(12) + dp(12)
    text_w = w - (tx - x) - pad

    # ⚠ **Two colours in one title, at the author's instruction: the suffix alone is red.**
    # Drawn as two runs on one wrapped line rather than as one coloured string, because the
    # suffix has to sit immediately after the title with no break of its own.
    if suffix:
        f = font(12)

        head_w = dr.textlength(title, font=f)

        if head_w + dr.textlength(suffix, font=f) <= text_w:
            text(dr, (tx, cy), title, 12, content)
            text(dr, (tx + head_w, cy), suffix, 12, ERROR)

            used = dp(17)
        else:
            # Wraps: the title takes the first line, the suffix the second, still red.
            used = wrapped(dr, (tx, cy), title, 12, content, text_w, leading=17)

            used += wrapped(dr, (tx, cy + used), suffix, 12, ERROR, text_w, leading=17)
    else:
        used = wrapped(dr, (tx, cy), title, 12, title_colour or content, text_w, leading=17)

    cy += used + dp(4)

    cy += wrapped(dr, (tx, cy), note, 9.5, content, text_w, leading=13)

    return cy + pad - y


def draw_requirements():
    ground = SURFACE_CONTAINER_HIGH

    title = s('auto_hide_req_shizuku_configured')
    note = s('auto_hide_req_shizuku_configured_note').strip()

    panels = [
        (
            'Thedjchi, configuration complete, Manage Shizuku ON',
            [
                (s('auto_hide_req_shizuku_permission'),
                 s('auto_hide_req_shizuku_permission_note'), 'met', None),
                (title, note, 'met', None),
            ],
            'Unchanged from today, except that item 2 folds "Manage Shizuku is on" into '
            'this row\'s condition — so it can now read unmet where it used to read met.',
        ),
        (
            'Thedjchi, but Manage Shizuku OFF  —  item 2',
            [
                (s('auto_hide_req_shizuku_permission'),
                 s('auto_hide_req_shizuku_permission_note'), 'met', None),
                (title, note, 'unmet', None),
            ],
            'Item 2: "why is imd+ on if manage shizuku is off". Today this row reads met, '
            'because it asks isShizukuConfigured only. Red dot, same words, IMD+ refuses.',
        ),
        (
            'Shevery  —  item 1',
            [
                (s('auto_hide_req_shizuku_permission'),
                 s('auto_hide_req_shizuku_permission_note'), 'met', None),
                (title, note, 'error', None),
            ],
            'Item 1: the suffix alone in the error colour, title normal, dot red. Never met '
            'on Shevery, so the IMD+ toggle will not turn on.',
        ),
    ]

    w = dp(40) + CARD_W + dp(150)

    heights = []

    probe = Image.new('RGB', (10, 10))
    pdr = ImageDraw.Draw(probe)

    for _, rows, _ in panels:
        h = dp(20) + dp(24)

        for t, n, d, c in rows:
            h += requirement_row(
                pdr, 0, 0, CARD_W - dp(20), t, n, d, ground, c,
                suffix=PROPOSED_SHEVERY_SUFFIX if d == 'error' else None,
            )

        heights.append(h + dp(16))

    # Drawn tall and cropped, rather than measured: the footnotes wrap to a variable number
    # of lines and an under-estimate silently clips the last card off the bottom.
    im, dr = sheet(w, dp(24) + sum(dp(120) + h for h in heights))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'IMD+  →  Requirements   (items 1 and 2)', bold=True)
    y += caption(
        dr, x, y,
        "Your string. The suffix alone is red — title normal, dot red — as you asked.",
    )
    y += dp(10)

    for (heading, rows, foot), card_h in zip(panels, heights):
        y += caption(dr, x, y, heading, bold=True)

        dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(28), fill=ground)

        ry = y + dp(20)

        text(dr, (x + dp(20), ry), s('auto_hide_requirements'), 11, PRIMARY, bold=True)

        ry += dp(24)

        for t, n, d, c in rows:
            ry += requirement_row(
                dr, x + dp(10), ry, CARD_W - dp(20), t, n, d, ground, title_colour=c,
                suffix=PROPOSED_SHEVERY_SUFFIX if d == 'error' else None,
            )

        y += card_h + dp(8)

        y += wrapped(dr, (x, y), foot, 10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15)

        y += dp(12)

    im.crop((0, 0, w, y + dp(16))).save(OUT / 'imd_plus_requirements.png')


# ---------------------------------------------------------------------------------------
# 2 — item 6: the Shizuku service row greyed on Shevery, in all four places
# ---------------------------------------------------------------------------------------
def draw_shevery_rows():
    ground = SURFACE_CONTAINER_HIGH

    shizuku_label = s('revert_defaults_shizuku')
    hide_note = s('settings_to_hide_shizuku_note')
    revert_note = s('revert_defaults_shizuku_note')

    w = dp(40) + CARD_W + dp(150)

    probe = Image.new('RGB', (10, 10))
    pdr = ImageDraw.Draw(probe)

    rw = CARD_W - dp(20)

    h_hide = setting_row(pdr, 0, 0, rw, shizuku_label, hide_note, False, False, ground)
    h_rev = setting_row(pdr, 0, 0, rw, shizuku_label, revert_note, False, False, ground)
    dooa_label = s('revert_defaults_display_over_other_apps')
    dooa_hide_note = s('settings_to_hide_overlay_note').replace('\n', ' ')
    dooa_rev_note = s('revert_defaults_overlay_note').replace('\n', ' ')

    h_dooa_hide = setting_row(pdr, 0, 0, rw, dooa_label, dooa_hide_note, False, False, ground)
    h_dooa_rev = setting_row(pdr, 0, 0, rw, dooa_label, dooa_rev_note, False, False, ground)

    im, dr = sheet(w, dp(1500))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'Item 6  —  Shevery: greyed and unticked, not removed', bold=True)
    y += caption(
        dr, x, y,
        'PROPOSED WORDING in the popup at the bottom — mine, not yours.',
        colour=ERROR,
    )
    y += dp(10)

    for heading, note, row_h, dooa_note, dooa_h in (
        (s('settings_to_hide_title'), hide_note, h_hide, dooa_hide_note, h_dooa_hide),
        (s('revert_defaults'), revert_note, h_rev, dooa_rev_note, h_dooa_rev),
    ):
        y += caption(dr, x, y, heading, bold=True)

        card_h = dp(20) + dp(30) + row_h + dooa_h + dp(14)

        dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(28), fill=ground)

        ry = y + dp(20)

        text(dr, (x + dp(20), ry + dp(2)), heading, 15, ON_SURFACE)

        ry += dp(30)

        ry += setting_row(
            dr, x + dp(10), ry, rw, shizuku_label, note,
            checked=False, enabled=False, ground=ground,
        )

        setting_row(
            dr, x + dp(10), ry, rw, dooa_label, dooa_note,
            checked=False, enabled=False, ground=ground,
        )

        y += card_h + dp(8)

        y += wrapped(
            dr, (x, y),
            'Today this row is not drawn at all on Shevery — an if (supportsIntents) wrapper '
            'removes it. Now it draws like the DOOA row under it: 38% content, 38% border, '
            'unticked in the drawing only. The stored tick is untouched and returns on Thedjchi.',
            10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
        )

        y += dp(14)

    # The per-app template, and the popup a press raises.
    #
    # ⚠ **A live row is drawn above the greyed one deliberately.** The + on a blocked row is
    # at 38% like everything else in it, which is hard to judge in isolation — the author asked
    # to see it, and the only honest way to show it is beside the same glyph at full contrast.
    y += caption(dr, x, y, 'Per app config  →  Templates', bold=True)

    rows = [
        (TEMPLATES[1], False),   # Hide USB Debugging — live, for the + at full contrast
        (TEMPLATES[5], True),    # Hide Shizuku service — blocked on Shevery
    ]

    heights = [template_row_height(tpl) for tpl, _ in rows]

    card_h = dp(20) + dp(30) + sum(heights) + dp(14)

    dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(28), fill=ground)

    ry = y + dp(20)

    text(dr, (x + dp(20), ry + dp(2)), 'Templates', 15, ON_SURFACE)

    ry += dp(30)

    for (tpl, blocked), h in zip(rows, heights):
        template_row(dr, x + dp(10), ry, CARD_W - dp(20), tpl, blocked, ground)

        ry += h

    y += card_h + dp(8)

    y += wrapped(
        dr, (x, y),
        'This is the reversal. Today appSettingHidden removes this template on Shevery — '
        'your earlier "keep them hidden until Shevery\'s engine lands". It now greys instead, '
        'and so does an already-added row, unticked with its stored position remembered.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    y += dp(16)

    y += caption(dr, x, y, 'A press on any of them  —  ConfigureFirstDialog', bold=True)

    pop_w = CARD_W

    msg_h = wrapped(pdr, (0, 0), PROPOSED_SHIZUKU_THEDJCHI_ONLY, 12, ON_SURFACE,
                    pop_w - dp(40), leading=17)

    pop_h = dp(20) + msg_h + dp(14) + dp(36) + dp(20)

    dr.rounded_rectangle((x, y, x + pop_w, y + pop_h), radius=dp(28),
                         fill=SURFACE_CONTAINER_HIGH)

    wrapped(dr, (x + dp(20), y + dp(20)), PROPOSED_SHIZUKU_THEDJCHI_ONLY, 12, ON_SURFACE,
            pop_w - dp(40), leading=17)

    text(dr, (x + pop_w - dp(90), y + pop_h - dp(42)), s('understood'), 12, PRIMARY,
         bold=True)

    y += pop_h + dp(8)

    y += wrapped(
        dr, (x, y),
        'No path line, exactly like the DOOA one on Shevery: there is nothing to go and '
        'configure. Its DOOA counterpart reads "managing Display over other apps is only '
        'supported for Thedjchi fork of Shizuku" — this sentence is my parallel of it and '
        'needs your words.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    im.crop((0, 0, w, y + dp(30))).save(OUT / 'shizuku_rows_shevery.png')


# ---------------------------------------------------------------------------------------
# 3 — item 8: the revert row's two lines
# ---------------------------------------------------------------------------------------
def draw_revert_title():
    ground = SURFACE_CONTAINER_HIGH

    current = s('revert_defaults_entry_both')
    # ⚠ The trailing "+" is the author's, added after the first template: it replaces
    # the " /" the current string carries and joins the two lines into one phrase.
    proposed = 'Settings to unhide +\nRevert to default configuration'

    w = dp(40) + CARD_W + dp(150)

    im, dr = sheet(w, dp(560))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'Item 8  —  the row under Settings to hide', bold=True)
    y += caption(
        dr, x, y,
        'Both lines are your own strings, so nothing here is proposed wording.',
    )
    y += dp(10)

    for heading, value in (('Today', current), ('Item 8', proposed)):
        y += caption(dr, x, y, heading, bold=True)

        lines = value.split('\n')

        card_h = dp(14) + len(lines) * dp(19) + dp(4) + dp(15) + dp(14)

        dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(20), fill=ground)

        cy = y + dp(14)

        for line in lines:
            text(dr, (x + dp(16), cy), line, 13, ON_SURFACE)

            cy += dp(19)

        cy += dp(4)

        text(dr, (x + dp(16), cy), '3 of 6 switched on', 9.5, ON_SURFACE_VARIANT)

        y += card_h + dp(14)

    y += dp(4)

    y += wrapped(
        dr, (x, y),
        'One string, revert_defaults_entry_both, read by two call sites — the settings-list '
        'row (SettingsScreen.kt:824) and the dialog heading (RevertDefaultsDialog.kt:135) — '
        'so both change together. Under the memory function neither shows this: they fall '
        'back to "Revert to default configuration" alone, which item 8 does not touch.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    im.crop((0, 0, w, y + dp(24))).save(OUT / 'revert_row_title.png')



EMOJI_FONT = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'


def emoji(im, xy, glyph, px):
    """Paste one colour emoji.

    ⚠ **NotoColorEmoji is a CBDT bitmap font and only loads at 109 px**, so the glyph is drawn
    at that size and resized down. 🧑‍🔬 is a ZWJ sequence and composes to one glyph here,
    which is what the device will do too.
    """
    f = ImageFont.truetype(EMOJI_FONT, 109)

    tile = Image.new('RGBA', (160, 140), (0, 0, 0, 0))

    ImageDraw.Draw(tile).text((0, 0), glyph, font=f, embedded_color=True)

    box = tile.getbbox()

    if box is None:
        return 0

    tile = tile.crop(box)

    w = int(round(px * tile.width / tile.height))

    im.paste(tile.resize((w, px), Image.LANCZOS), (int(xy[0]), int(xy[1])), tile.resize(
        (w, px), Image.LANCZOS,
    ))

    return w


# ---------------------------------------------------------------------------------------
# 4 — the new upgrade notice
# ---------------------------------------------------------------------------------------
BULLET = '\u2022'

DEV_NOTE_TITLE = 'Note from developer '

DEV_NOTE_BODY = (
    'IMD have undergone a major update and I have matched your previous settings to your '
    'corresponding current ones. But, still:'
)

DEV_NOTE_POINTS = (
    'it is recommended to clear IMD app data, or',
    'At least check all the settings of IMD once before using the app.',
)

DEV_NOTE_NEW = 'New functions in the app to try:'

DEV_NOTE_NEW_POINTS = (
    'Auto unhide settings(RECOMMENDED)',
    'Auto hide settings (needs background service).',
)


def draw_dev_note():
    ground = SURFACE_CONTAINER_HIGH

    w = dp(40) + CARD_W + dp(150)

    im, dr = sheet(w, dp(1400))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'The new upgrade notice  —  every word is yours', bold=True)
    y += caption(
        dr, x, y,
        'Shown once to an install that existed before v3. Nothing here is proposed wording.',
    )
    y += dp(10)

    pad = dp(20)
    inner = CARD_W - pad * 2

    # Measured first so the card can be drawn behind the text.
    cy = pad

    cy += dp(24)                                        # title
    cy += dp(10)
    cy += wrapped(dr, (0, -9999), DEV_NOTE_BODY, 11.5, ground, inner, leading=15)
    cy += dp(8)

    for point in DEV_NOTE_POINTS:
        cy += wrapped(dr, (0, -9999), point, 11.5, ground, inner - dp(22), leading=15)
        cy += dp(4)

    cy += dp(10)
    cy += dp(16)                                        # the green line
    cy += dp(6)

    for point in DEV_NOTE_NEW_POINTS:
        cy += wrapped(dr, (0, -9999), point, 11.5, ground, inner - dp(22), leading=15)
        cy += dp(4)

    card_h = cy + dp(14) + dp(36) + pad

    dr.rounded_rectangle((x, y, x + CARD_W, y + card_h), radius=dp(28), fill=ground)

    ty = y + pad

    tw = dr.textlength(DEV_NOTE_TITLE, font=font(16))

    text(dr, (x + pad, ty), DEV_NOTE_TITLE, 16, ON_SURFACE)

    emoji(im, (x + pad + tw, ty - dp(2)), '\U0001F9D1\u200d\U0001F52C', dp(20))

    ty += dp(24) + dp(10)

    ty += wrapped(dr, (x + pad, ty), DEV_NOTE_BODY, 11.5, ON_SURFACE, inner, leading=15)

    ty += dp(8)

    for point in DEV_NOTE_POINTS:
        text(dr, (x + pad + dp(8), ty), BULLET, 11.5, ON_SURFACE_VARIANT)

        ty += wrapped(
            dr, (x + pad + dp(22), ty), point, 11.5, ON_SURFACE_VARIANT,
            inner - dp(22), leading=15,
        )

        ty += dp(4)

    ty += dp(10)

    # ⚠ Bold and green — `primary` in this scheme, the same green the section headings take.
    text(dr, (x + pad, ty), DEV_NOTE_NEW, 11.5, PRIMARY, bold=True)

    ty += dp(16) + dp(6)

    for point in DEV_NOTE_NEW_POINTS:
        text(dr, (x + pad + dp(8), ty), BULLET, 11.5, ON_SURFACE_VARIANT)

        ty += wrapped(
            dr, (x + pad + dp(22), ty), point, 11.5, ON_SURFACE_VARIANT,
            inner - dp(22), leading=15,
        )

        ty += dp(4)

    text(dr, (x + CARD_W - dp(90), y + card_h - dp(40)), s('understood'), 12, PRIMARY,
         bold=True)

    y += card_h + dp(14)

    y += wrapped(
        dr, (x, y),
        'This replaces the notice v3 shows upgraders today — "' + s('settings_tab_notice')
        + '" — which comes out with its strings and its MainActivity branch.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    y += dp(16)

    # The notification, for the two routes that have no window to put a dialog in.
    y += caption(dr, x, y, 'The tile and Tasker route  —  heads-up notification', bold=True)

    note_h = dp(96)

    dr.rounded_rectangle((x, y, x + CARD_W, y + note_h), radius=dp(24),
                         fill=SURFACE_CONTAINER_HIGH)

    text(dr, (x + dp(18), y + dp(16)), 'IMD', 9.5, PRIMARY, bold=True)

    body = 'IMD: Important note from developer '

    text(dr, (x + dp(18), y + dp(38)), body, 12, ON_SURFACE)

    emoji(im, (x + dp(18) + dr.textlength(body, font=font(12)), y + dp(36)),
          '\U0001F9D1\u200d\U0001F52C', dp(18))

    text(dr, (x + dp(18), y + dp(66)), 'IMD app update notice', 9, ON_SURFACE_VARIANT)

    y += note_h + dp(10)

    y += wrapped(
        dr, (x, y),
        'Alerting, and re-posted if swiped away — it only goes for good once the dialog behind '
        'it has been read. Tapping it opens IMD to the dialog above.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    y += dp(14)

    y += wrapped(
        dr, (x, y),
        'One thing to confirm: your first message said the New-functions list was a "nested '
        'numbered list". Both lists are bullets here, on your "yes use bullets please" — say '
        'if you meant only the first two.',
        10, ERROR, CARD_W + dp(140), leading=15,
    )

    im.crop((0, 0, w, y + dp(24))).save(OUT / 'dev_note_dialog.png')



# ---------------------------------------------------------------------------------------
# 5 — the proposed Shizuku setup page in onboarding
# ---------------------------------------------------------------------------------------
def switch(dr, x, y, on, ground):
    """Material's 52x32dp switch, near enough for a layout template."""
    w, h = dp(52), dp(32)

    track = PRIMARY if on else mix(OUTLINE, ground, 0.5)

    dr.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=track)

    r = dp(12)

    cx = x + w - r - dp(4) if on else x + r + dp(4)

    dr.ellipse((cx - r, y + h / 2 - r, cx + r, y + h / 2 + r),
               fill=ON_PRIMARY if on else SURFACE_CONTAINER_HIGH)

    return h


def radio(dr, x, y, selected, ground):
    """An unselected fork toggle is an empty ring — the state the author is asking for."""
    r = dp(10)

    dr.ellipse((x, y, x + r * 2, y + r * 2), outline=OUTLINE, width=max(1, dp(2)))

    if selected:
        dr.ellipse((x + dp(5), y + dp(5), x + r * 2 - dp(5), y + r * 2 - dp(5)), fill=PRIMARY)

    return r * 2


def field(dr, x, y, w, label, value, ground):
    """An outlined text field with its label, empty."""
    h = dp(56)

    dr.rounded_rectangle((x, y, x + w, y + h), radius=dp(4), outline=OUTLINE,
                         width=max(1, dp(1)))

    text(dr, (x + dp(12), y + dp(10)), label, 9, ON_SURFACE_VARIANT)

    text(dr, (x + dp(12), y + dp(28)), value, 11.5,
         ON_SURFACE if value else ON_SURFACE_VARIANT)

    return h + dp(10)


def button(dr, x, y, w, label, filled, ground, enabled=True):
    h = dp(40)

    if filled:
        fill = PRIMARY if enabled else mix(ON_SURFACE, ground, 0.12)

        dr.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=fill)

        colour = ON_PRIMARY if enabled else mix(ON_SURFACE, ground, 0.38)
    else:
        dr.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, outline=OUTLINE,
                             width=max(1, dp(1)))

        colour = PRIMARY

    f = font(12, bold=True)

    dr.text((x + w / 2, y + h / 2), label, font=f, fill=colour, anchor='mm')

    return h


def shizuku_page_body(dr, im, x, top, ground, draw):
    """Lays the page out, drawing only when `draw` — so the card can be sized first.

    ⚠ **Two passes on purpose.** The first draft drew the content and then filled the card
    behind it, which painted over everything. The card's height depends on the content, and
    the content has to sit on top of the card, so the measure and the draw are separate runs.
    """
    inner = CARD_W - dp(40)

    px = x + dp(20)

    py = top + dp(24)

    if draw:
        text(dr, (px, py), 'Shizuku configuration', 16, PRIMARY, bold=True)

    py += dp(30)

    # ⚠ **No Manage Shizuku switch here, at the author's instruction**: the Manage button at
    # the foot of the page is what switches it on, so a toggle above would be the same
    # decision asked twice. Its bold "RECOMMENDED ON" line goes with it - it describes a
    # toggle that is no longer on this page.

    for line in (s('shizuku_rikka_warning'),
                 s('shizuku_rikka_recommend_prefix') + ' ' + s('shizuku_rikka_recommend_link')):
        py += wrapped(dr, (px, py if draw else -9999), line, 9.5, ERROR, inner, leading=13)

        py += dp(6)

    py += dp(10)

    # ⚠ Both forks unselected — the author's instruction for this page.
    for label, note in (
        (s('shizuku_fork_thedjchi'), s('shizuku_fork_mode_thedjchi_suffix')),
        (s('shizuku_fork_shevery'), s('shizuku_fork_shevery_caution')),
    ):
        if draw:
            radio(dr, px, py + dp(2), selected=False, ground=ground)

            text(dr, (px + dp(30), py), label, 12, ON_SURFACE)

        py += dp(17)

        py += wrapped(dr, (px + dp(30), py if draw else -9999), note, 9.5, ON_SURFACE_VARIANT,
                      inner - dp(30), leading=13)

        py += dp(10)

    py += dp(6)

    for label in (s('shizuku_package_name'), s('shizuku_start_action'), s('shizuku_auth_key')):
        if draw:
            field(dr, px, py, inner, label, '', ground)

        py += dp(66)

    py += dp(6)

    # ⚠ Stacked, not side by side. "Manage shizuku configuration" does not fit half a phone
    # width at button type, and a label that has to shrink to fit is a label nobody reads.
    if draw:
        button(dr, px, py, inner, 'Manage shizuku configuration',
               filled=True, ground=ground, enabled=False)

    py += dp(48)

    if draw:
        button(dr, px, py, inner, 'Skip', filled=False, ground=ground)

    py += dp(40) + dp(24)

    return py


def draw_shizuku_setup():
    ground = SURFACE_CONTAINER_HIGH

    w = dp(40) + CARD_W + dp(150)

    im, dr = sheet(w, dp(2400))

    x, y = dp(40), dp(24)

    y += caption(dr, x, y, 'Setup  \u2192  new page, after Permissions', bold=True)
    y += caption(
        dr, x, y,
        'PROPOSED LAYOUT. Both button labels are yours; the popup sentence is mine.',
        colour=ERROR,
    )
    y += dp(10)

    bottom = shizuku_page_body(dr, im, x, y, ground, draw=False)

    dr.rounded_rectangle((x, y, x + CARD_W, bottom), radius=dp(28), fill=ground)

    shizuku_page_body(dr, im, x, y, ground, draw=True)

    y = bottom + dp(14)

    y += wrapped(
        dr, (x, y),
        'Manage is greyed until every field is filled and a fork is picked; Skip is always '
        'live. Both fork toggles start unselected, and once one is picked one stays picked.',
        10, ON_SURFACE_VARIANT, CARD_W + dp(140), leading=15,
    )

    y += dp(16)

    y += caption(dr, x, y, 'A press on the greyed Manage button', bold=True)

    message = 'please fill all fields first'

    pop_w = CARD_W

    msg_h = wrapped(dr, (0, -9999), message, 12, ON_SURFACE, pop_w - dp(40), leading=17)

    pop_h = dp(20) + msg_h + dp(14) + dp(36) + dp(20)

    dr.rounded_rectangle((x, y, x + pop_w, y + pop_h), radius=dp(28), fill=ground)

    wrapped(dr, (x + dp(20), y + dp(20)), message, 12, ON_SURFACE, pop_w - dp(40), leading=17)

    text(dr, (x + pop_w - dp(90), y + pop_h - dp(42)), s('understood'), 12, PRIMARY, bold=True)

    y += pop_h + dp(10)

    y += wrapped(
        dr, (x, y),
        'Your words, lower-cased as you wrote them. Say if you want it capitalised.',
        10, ERROR, CARD_W + dp(140), leading=15,
    )

    im.crop((0, 0, w, y + dp(24))).save(OUT / 'shizuku_setup_page.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    draw_requirements()
    draw_shevery_rows()
    draw_revert_title()
    draw_dev_note()
    draw_shizuku_setup()

    print('  ok  design/out/imd_plus_requirements.png')
    print('  ok  design/out/shizuku_rows_shevery.png')
    print('  ok  design/out/revert_row_title.png')
    print('  ok  design/out/dev_note_dialog.png')
    print('  ok  design/out/shizuku_setup_page.png')


if __name__ == '__main__':
    main()
