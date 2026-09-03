#!/usr/bin/env python3
"""Templates for the four r4p items that are visual — pictures to decide from, not code.

    light_sections.png      the settings tab's collapsible sections in light theme, today
                            beside the proposed collapsed-body tint, with the same pair in
                            dark so the change can be judged in both.
    legacy_icons.png        a legacy (non-adaptive) icon as it is drawn today and as it
                            would be drawn plated and masked at full size, in the app list
                            and as a home-screen shortcut.
    fav_unhide_fab.png      the Favourites tab's unhide button in its idle state, light
                            theme, today beside the proposal — and its red active state,
                            which does not change.
    support_signature.png   the signature block at the foot of the Support dialog.

Palette is `LightGreenColorScheme` and `DarkGreenColorScheme` from
`design-system/theme/Theme.kt`, unmodified, and every derived colour is computed here the way
the composable computes it — `primary.copy(alpha = a).compositeOver(surfaceContainerLowest)`.

⚠ **The author's screenshots have Dynamic Theme on, so his hues are the wallpaper's, not
these.** What carries over is the *relationship*: every proposed colour below is an alpha of
`primary` over a container, so it follows whatever scheme is in force. Nothing here hard-codes
a colour into the app.

Geometry is dp at 3x against the real composables' own numbers: CollapsibleSection's 12/4dp
card padding and `shapes.large`, the FAB's 56dp and 24dp glyph, SupportDialog's 20dp padding.

Nothing here is generated into the app.
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent / "out"

SCALE = 3

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def dp(v: float) -> int:
    return int(round(v * SCALE))


def font(size: float, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT_B if bold else FONT, dp(size))


# ---------------------------------------------------------------- palettes

LIGHT = {
    "primary": (0x4C, 0x66, 0x2B),
    "onPrimary": (0xFF, 0xFF, 0xFF),
    "surface": (0xF9, 0xFA, 0xEF),
    "onSurface": (0x1A, 0x1C, 0x16),
    "onSurfaceVariant": (0x44, 0x48, 0x3D),
    "outlineVariant": (0xC5, 0xC8, 0xBA),
    "surfaceContainerLowest": (0xFF, 0xFF, 0xFF),
    "surfaceContainerLow": (0xF3, 0xF4, 0xE9),
    "surfaceContainer": (0xEE, 0xEF, 0xE3),
    "surfaceContainerHigh": (0xE8, 0xE9, 0xDE),
    "surfaceContainerHighest": (0xE2, 0xE3, 0xD8),
}

DARK = {
    "primary": (0xB1, 0xD1, 0x8A),
    "onPrimary": (0x1F, 0x37, 0x01),
    "surface": (0x12, 0x14, 0x0E),
    "onSurface": (0xE2, 0xE3, 0xD8),
    "onSurfaceVariant": (0xC5, 0xC8, 0xBA),
    "outlineVariant": (0x44, 0x48, 0x3D),
    "surfaceContainerLowest": (0x0C, 0x0F, 0x09),
    "surfaceContainerLow": (0x1A, 0x1C, 0x16),
    "surfaceContainer": (0x1E, 0x20, 0x1A),
    "surfaceContainerHigh": (0x28, 0x2B, 0x24),
    "surfaceContainerHighest": (0x33, 0x36, 0x2E),
}

GETO_RED = (0xB3, 0x26, 0x1E)


def over(fg, alpha: float, bg):
    """`fg.copy(alpha = alpha).compositeOver(bg)` — the composable's own expression."""
    return tuple(int(round(f * alpha + b * (1 - alpha))) for f, b in zip(fg, bg))


def hexof(c) -> str:
    return "#%02X%02X%02X" % c


# The three tints. 0.16 and 0.34 are what CollapsibleSection already uses; 0.12 is the
# proposal, chosen so the collapsed card clears the page by an order of magnitude more than
# surfaceContainerLow does and still sits below the open section's body.
BODY_ALPHA = 0.16
HEADING_ALPHA = 0.34
COLLAPSED_ALPHA = 0.12


# ---------------------------------------------------------------- helpers


def rounded(draw: ImageDraw.ImageDraw, box, radius: int, fill, outline=None):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=SCALE)


def label(draw, xy, text, size=11, bold=False, fill=(0x33, 0x33, 0x33)):
    draw.text(xy, text, font=font(size, bold), fill=fill)


def chevron(draw, cx, cy, size, colour, up=False):
    h = size / 2
    pts = [(cx - h, cy - h / 2), (cx, cy + h / 2), (cx + h, cy - h / 2)]

    if up:
        pts = [(x, 2 * cy - y) for x, y in pts]

    draw.line(pts, fill=colour, width=max(2, SCALE), joint="curve")


# ---------------------------------------------------------------- 1. sections


def section_stack(img, draw, x, y, width, pal, collapsed_fill, titles):
    """One column of sections: the first open, the rest closed."""
    card_h = dp(44)
    gap = dp(8)
    radius = dp(16)

    body = over(pal["primary"], BODY_ALPHA, pal["surfaceContainerLowest"])
    heading = over(pal["primary"], HEADING_ALPHA, pal["surfaceContainerLowest"])

    # Open section: heading strip, then three rows on the body tint.
    open_h = card_h + dp(3 * 30)

    rounded(draw, [x, y, x + width, y + open_h], radius, body)

    strip = Image.new("RGB", (width, card_h), heading)
    mask = Image.new("L", (width, card_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, width - 1, card_h * 2], radius=radius, fill=255,
    )
    img.paste(strip, (x, y), mask)

    label(draw, (x + dp(12), y + dp(15)), titles[0], 12, True, pal["onSurface"])
    chevron(draw, x + width - dp(20), y + card_h // 2, dp(12), pal["onSurface"], up=True)

    for i in range(3):
        ry = y + card_h + dp(8) + i * dp(30)
        label(draw, (x + dp(18), ry), "Setting row %d" % (i + 1), 12, False, pal["onSurface"])

    yy = y + open_h + gap

    for title in titles[1:]:
        rounded(draw, [x, yy, x + width, yy + card_h], radius, collapsed_fill)

        label(draw, (x + dp(12), yy + dp(15)), title, 12, True, pal["onSurface"])
        chevron(draw, x + width - dp(20), yy + card_h // 2, dp(12), pal["onSurface"])

        yy += card_h + gap

    return yy


def sheet_sections():
    width = dp(880)
    height = dp(520)

    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    label(draw, (dp(16), dp(12)), "Settings tab sections — collapsed card tint", 15, True)

    titles = ["Shizuku config", "Auto hide", "Auto unhide", "Advanced"]

    panels = [
        ("LIGHT — today", LIGHT, LIGHT["surfaceContainerLow"],
         "collapsed = surfaceContainerLow " + hexof(LIGHT["surfaceContainerLow"])),
        ("LIGHT — proposed", LIGHT,
         over(LIGHT["primary"], COLLAPSED_ALPHA, LIGHT["surfaceContainerLowest"]),
         "collapsed = primary @ 12% over lowest " +
         hexof(over(LIGHT["primary"], COLLAPSED_ALPHA, LIGHT["surfaceContainerLowest"]))),
        ("DARK — today", DARK, DARK["surfaceContainerLow"],
         "collapsed = surfaceContainerLow " + hexof(DARK["surfaceContainerLow"])),
        ("DARK — proposed", DARK,
         over(DARK["primary"], COLLAPSED_ALPHA, DARK["surfaceContainerLowest"]),
         "collapsed = primary @ 12% over lowest " +
         hexof(over(DARK["primary"], COLLAPSED_ALPHA, DARK["surfaceContainerLowest"]))),
    ]

    col_w = dp(190)
    x = dp(20)

    for name, pal, collapsed, note in panels:
        # The page behind the cards, so the separation being judged is card-against-page.
        page_top = dp(44)
        page_bottom = height - dp(58)

        draw.rectangle([x - dp(6), page_top, x + col_w + dp(6), page_bottom], fill=pal["surface"])

        label(draw, (x - dp(6), dp(28)), name, 11, True)

        section_stack(img, draw, x, page_top + dp(8), col_w, pal, collapsed, titles)

        label(draw, (x - dp(6), page_bottom + dp(6)), note, 8, False, (0x55, 0x55, 0x55))
        label(
            draw,
            (x - dp(6), page_bottom + dp(18)),
            "page = " + hexof(pal["surface"]),
            8,
            False,
            (0x55, 0x55, 0x55),
        )

        x += col_w + dp(26)

    label(
        draw,
        (dp(16), height - dp(30)),
        "Heading strip (primary @ 34%) and open body (primary @ 16%) are unchanged — "
        "'which section is open' is still said by the strip.",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(18)),
        "Today, light: card %s against page %s — a difference of 6/6/6." % (
            hexof(LIGHT["surfaceContainerLow"]), hexof(LIGHT["surface"]),
        ),
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    img.save(OUT / "light_sections.png")


# ---------------------------------------------------------------- 2. legacy icons


def squircle_mask(size: int) -> Image.Image:
    """The launcher's shape, drawn as a superellipse — close enough for a template."""
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.28), fill=255)

    return mask


def legacy_artwork(size: int) -> Image.Image:
    """A stand-in for a legacy icon: square artwork with transparent margins."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    inset = int(size * 0.10)

    d.rectangle([inset, inset, size - inset, size - inset], fill=(0x2B, 0x63, 0x9C, 0xFF))
    d.ellipse(
        [int(size * 0.30), int(size * 0.30), int(size * 0.70), int(size * 0.70)],
        fill=(0xFF, 0xD5, 0x4F, 0xFF),
    )

    return img


def trim(img: Image.Image) -> Image.Image:
    """Drop a legacy icon's transparent margin, so what is left is the artwork itself."""
    box = img.split()[3].getbbox()

    return img.crop(box) if box else img


def sheet_icons():
    width = dp(880)
    height = dp(400)

    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    label(draw, (dp(16), dp(10)), "Legacy (non-adaptive) icons — three ways to shape them", 15, True)

    size = dp(72)

    def place(px, py, art, bg):
        draw.rectangle(
            [px - dp(16), py - dp(12), px + size + dp(16), py + size + dp(12)], fill=bg,
        )

        img.paste(art.convert("RGB"), (px, py), art.split()[3])

    def plated(art, scale_to_fill: bool, inset: float):
        """Plate, optionally scale the artwork, then mask to the launcher shape."""
        canvas = Image.new("RGBA", (size, size), (0xFF, 0xFF, 0xFF, 0xFF))

        if scale_to_fill:
            piece = trim(art).resize((size, size), Image.LANCZOS)
            canvas.alpha_composite(piece, (0, 0))
        else:
            side = int(size * (1 - 2 * inset))
            piece = art.resize((side, side), Image.LANCZOS)
            off = (size - side) // 2
            canvas.alpha_composite(piece, (off, off))

        out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        out.paste(canvas, (0, 0), squircle_mask(size))

        return out

    art = legacy_artwork(size)

    columns = [
        (dp(60), "today — raw", art),
        (dp(240), "A  inset 72/108, plated", plated(art, False, (1 - 72 / 108) / 2)),
        (dp(420), "B  no inset, natural size", plated(art, False, 0.0)),
        (dp(600), "C  no inset, trimmed to fill", plated(art, True, 0.0)),
    ]

    # An adaptive icon, unchanged by any of this, for the comparison the eye actually makes.
    adaptive = Image.new("RGBA", (size, size), (0x2B, 0x63, 0x9C, 0xFF))
    ImageDraw.Draw(adaptive).ellipse(
        [int(size * 0.28), int(size * 0.28), int(size * 0.72), int(size * 0.72)],
        fill=(0xFF, 0xD5, 0x4F, 0xFF),
    )
    shaped = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    shaped.paste(adaptive, (0, 0), squircle_mask(size))

    columns.append((dp(760), "an adaptive icon — untouched", shaped))

    rows = [
        (dp(66), "in the app list", LIGHT["surface"]),
        (dp(216), "as a home-screen shortcut", (0x3A, 0x42, 0x50)),
    ]

    for y, name, bg in rows:
        label(draw, (dp(16), y - dp(26)), name, 11, True)

        for px, caption, picture in columns:
            place(px, y, picture, bg)

            if y == rows[-1][0]:
                label(draw, (px - dp(16), y + size + dp(18)), caption, 8)

    label(
        draw,
        (dp(16), height - dp(44)),
        "A keeps the icon at its drawn size, so the plate shows as a wide ring. "
        "B is 'no inset' literally: the bitmap fills the canvas, but a legacy",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(32)),
        "icon's own transparent margin still leaves a ring. C trims that margin first and "
        "scales the artwork to fill the shape — no ring, and the",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(20)),
        "corners of edge-to-edge artwork are clipped by the mask. C is the one that looks "
        "like a launcher icon.",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    img.save(OUT / "legacy_icons.png")


# ---------------------------------------------------------------- 3. the FAB


def sheet_fab():
    width = dp(560)
    height = dp(250)

    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    label(draw, (dp(16), dp(12)), "Favourites tab — unhide button, light theme", 15, True)

    fab = dp(56)

    def draw_fab(px, py, container, content, caption, sub):
        draw.rectangle(
            [px - dp(24), py - dp(20), px + fab + dp(24), py + fab + dp(20)],
            fill=LIGHT["surface"],
        )

        rounded(draw, [px, py, px + fab, py + fab], dp(16), container)

        # The eye glyph, at its 24dp.
        g = dp(24)
        cx, cy = px + fab // 2, py + fab // 2

        draw.ellipse([cx - g // 2, cy - g // 4, cx + g // 2, cy + g // 4], outline=content, width=SCALE)
        draw.ellipse([cx - g // 6, cy - g // 6, cx + g // 6, cy + g // 6], fill=content)

        label(draw, (px - dp(24), py + fab + dp(28)), caption, 10, True)
        label(draw, (px - dp(24), py + fab + dp(42)), sub, 8, False, (0x55, 0x55, 0x55))

    y = dp(64)

    draw_fab(
        dp(60), y,
        over(LIGHT["onSurface"], 0.12, LIGHT["surface"]),
        over(LIGHT["onSurface"], 0.38, LIGHT["surface"]),
        "idle — today",
        "onSurface @ 12% = " + hexof(over(LIGHT["onSurface"], 0.12, LIGHT["surface"])),
    )

    draw_fab(
        dp(230), y,
        LIGHT["surfaceContainerHighest"],
        LIGHT["onSurfaceVariant"],
        "idle — proposed",
        "surfaceContainerHighest = " + hexof(LIGHT["surfaceContainerHighest"]),
    )

    draw_fab(
        dp(400), y,
        GETO_RED,
        (0xFF, 0xFF, 0xFF),
        "something hidden — unchanged",
        "GetoRed " + hexof(GETO_RED),
    )

    label(
        draw,
        (dp(16), height - dp(28)),
        "Still greyed, still pressable, still answering with a toast — only the container "
        "becomes an opaque tonal step",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(16)),
        "instead of 12% ink over a near-white page, which is what makes it vanish in light "
        "theme.",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    img.save(OUT / "fav_unhide_fab.png")


# ---------------------------------------------------------------- 4. the signature


def sheet_signature():
    width = dp(560)
    height = dp(260)

    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    label(draw, (dp(16), dp(12)), "Support dialog — signature at the foot", 15, True)

    # The dialog's own surface.
    box = [dp(40), dp(44), width - dp(40), height - dp(56)]
    rounded(draw, box, dp(24), LIGHT["surfaceContainerLowest"])

    inner = dp(20)

    label(
        draw,
        (box[0] + inner, box[1] + inner),
        "5.  Contribute to the project",
        11,
        False,
        LIGHT["onSurface"],
    )

    # ⚠ The alignment the author asked for: the 's' of soul_99 over the '(' of (Dr.
    # The "- " hangs to the left, outside the aligned column, so both lines' first word
    # starts at the same x.
    f = font(11)

    line1 = "soul_99"
    line2 = "(Dr. Utkarsh Rajput)"

    w1 = draw.textlength(line1, font=f)
    w2 = draw.textlength(line2, font=f)
    dash = draw.textlength("- ", font=f)

    right = box[2] - inner

    # The block is right-aligned on its widest line; the dash hangs left of it.
    left = right - max(w1, w2)

    sig_y = box[3] - inner - dp(46)

    draw.text((left - dash, sig_y), "- ", font=f, fill=LIGHT["onSurface"])
    draw.text((left, sig_y), line1, font=f, fill=LIGHT["onSurface"])
    draw.text((left, sig_y + dp(16)), line2, font=f, fill=LIGHT["onSurfaceVariant"])

    # The guide line, so the alignment is visible rather than asserted.
    draw.line(
        [(left, sig_y - dp(6)), (left, sig_y + dp(30))],
        fill=(0xC0, 0x30, 0x30),
        width=max(1, SCALE // 2),
    )

    label(draw, (box[0] + inner, box[3] - inner - dp(14)), "CLOSE", 10, True, LIGHT["primary"])

    label(
        draw,
        (dp(16), height - dp(40)),
        "The red guide is where 's' and '(' both start — the author's "
        "\"make s aligned with (\".",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(28)),
        "The \"- \" hangs outside the block, so nothing about the two strings changes.",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(16)),
        "(Right-aligned on the wider line, which is line two.)",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    img.save(OUT / "support_signature.png")



# ---------------------------------------------------------------- 5. manager rows


def sheet_manager_note():
    width = dp(620)
    height = dp(330)

    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    label(draw, (dp(16), dp(10)), "Settings manager — 'Only selected ones'", 15, True)

    pal = LIGHT

    card = [dp(20), dp(40), width - dp(20), height - dp(56)]
    rounded(draw, card, dp(20), pal["surfaceContainerLowest"])

    rows = [
        ("Shizuku", None),
        ("Accessibility services", "Only selected ones"),
        ("Display over other apps", "Only selected ones"),
        ("USB debugging", None),
    ]

    y = card[1] + dp(18)

    for title, note in rows:
        label(draw, (card[0] + dp(16), y), title, 13, False, pal["onSurface"])

        # The switch, so the note's position relative to it is what is being judged.
        sx = card[2] - dp(64)
        sy = y + dp(2)

        rounded(draw, [sx, sy, sx + dp(38), sy + dp(20)], dp(10), pal["primary"])
        draw.ellipse(
            [sx + dp(20), sy + dp(2), sx + dp(36), sy + dp(18)], fill=pal["surfaceContainerLowest"],
        )

        if note is None:
            y += dp(44)
            continue

        # labelSmall — 11sp. Small, and still a real type step rather than a shrunk body.
        label(draw, (card[0] + dp(16), y + dp(20)), note, 11, False, pal["onSurfaceVariant"])

        y += dp(56)

    label(
        draw,
        (dp(16), height - dp(40)),
        "'Only selected ones' — the author's string, verbatim — under those two rows only, in "
        "labelSmall (11sp)",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(28)),
        "on onSurfaceVariant. The two long scope sentences that used to sit here, removed at the "
        "author's own",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    label(
        draw,
        (dp(16), height - dp(16)),
        "instruction, stay removed — their strings are still in the tree and still reachable from "
        "the \u24d8 dialog.",
        9,
        False,
        (0x44, 0x44, 0x44),
    )

    img.save(OUT / "manager_only_selected.png")


def main() -> None:
    OUT.mkdir(exist_ok=True)

    sheet_sections()
    sheet_icons()
    sheet_fab()
    sheet_signature()
    sheet_manager_note()

    for name in (
        "light_sections.png",
        "legacy_icons.png",
        "fav_unhide_fab.png",
        "support_signature.png",
        "manager_only_selected.png",
    ):
        print("  wrote     design/out/" + name)


if __name__ == "__main__":
    main()
