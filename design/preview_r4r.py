#!/usr/bin/env python3
"""Template for the page that replaces the help/readme step at the end of setup.

    setup_complete_page.png   the author's title, his numbered list with its nested lists,
                              the two 'Add toggle' buttons, the signature and 'Let's go'.

Every word is his, verbatim. Two things are marked on the sheet as questions rather than
decisions: the nested numbering, and what the Add toggle buttons do below Android 13.

Palette is LightGreenColorScheme from design-system/theme/Theme.kt. Geometry is dp at 3x.
"""
from __future__ import annotations

import pathlib

from PIL import Image, ImageDraw, ImageFont

OUT = pathlib.Path(__file__).resolve().parent / "out"

SCALE = 3

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def dp(v):
    return int(round(v * SCALE))


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, dp(size))


LIGHT = {
    "primary": (0x4C, 0x66, 0x2B),
    "onPrimary": (0xFF, 0xFF, 0xFF),
    "surface": (0xF9, 0xFA, 0xEF),
    "onSurface": (0x1A, 0x1C, 0x16),
    "onSurfaceVariant": (0x44, 0x48, 0x3D),
    "outline": (0x75, 0x79, 0x6C),
}


def main():
    OUT.mkdir(exist_ok=True)

    width, height = dp(400), dp(870)

    img = Image.new("RGB", (width, height), LIGHT["surface"])
    draw = ImageDraw.Draw(img)

    pal = LIGHT
    x = dp(24)
    y = dp(36)

    draw.text((x, y), "Setup is now almost complete", font=font(20, True), fill=pal["primary"])
    y += dp(42)

    def line(text, indent=0, size=12, bold=False, colour=None, gap=20):
        nonlocal y
        draw.text(
            (x + dp(indent), y),
            text,
            font=font(size, bold),
            fill=colour or pal["onSurface"],
        )
        y += dp(gap)

    def button(label, indent):
        nonlocal y
        w, h = dp(96), dp(30)
        bx = x + dp(indent)
        draw.rounded_rectangle([bx, y, bx + w, y + h], radius=dp(15), fill=pal["primary"])
        tw = draw.textlength(label, font=font(11, True))
        draw.text(
            (bx + (w - tw) / 2, y + dp(8)), label, font=font(11, True), fill=pal["onPrimary"],
        )
        y += h + dp(12)

    line("1.  Now simply launch your problematic apps by", 0)
    line("     clicking on them in IMD.", 0, gap=26)

    line("2.  For quick access:", 0)
    line("1.  Long press app icons to create", 18)
    line("      homescreen shortcuts", 18)
    line("2.  Add apps to favourite tab", 18)
    line("3.  Add Hide settings quick settings toggle", 18)
    line("      (tip: long pressing toggle opens", 18, size=11, colour=pal["onSurfaceVariant"])
    line("      Settings manager)", 18, size=11, colour=pal["onSurfaceVariant"], gap=24)
    button("Add toggle", 22)

    y += dp(6)
    line("3.  Use IMD's own Settings manager:", 0)
    line("1.  Use Settings manager app icon in your", 18)
    line("      app drawer", 18)
    line("2.  Add Settings manager quick settings", 18)
    line("      toggle", 18, gap=24)
    button("Add toggle", 22)

    y += dp(6)
    line("4.  The setup is now complete but you are", 0)
    line("     recommended to checkout:", 0)
    line("1.  All other IMD app settings", 18)
    line("2.  IMD+ (auto hide settings on normal app", 18)
    line("      launches, needs background service)", 18)
    line("3.  IMD intents (Tasker integration)", 18)

    # The foot: signature left, Let's go right.
    fy = height - dp(96)

    draw.text(
        (x, fy + dp(9)),
        "Made with (heart) by soul_99",
        font=font(11),
        fill=pal["onSurfaceVariant"],
    )

    bw, bh = dp(94), dp(36)
    bx = width - dp(24) - bw
    draw.rounded_rectangle([bx, fy, bx + bw, fy + bh], radius=dp(18), fill=pal["primary"])
    tw = draw.textlength("Let's go", font=font(12, True))
    draw.text(
        (bx + (bw - tw) / 2, fy + dp(11)), "Let's go", font=font(12, True), fill=pal["onPrimary"],
    )

    note = [
        "Heading in the theme's primary, as asked. The two Add toggle buttons appear on Android 13+",
        "only \u2014 there is no older API that can add a quick settings tile. The signature carries the",
        "\ud83d\udc9d emoji in the app; this sheet's font has no colour emoji, hence (heart).",
    ]

    for i, line_text in enumerate(note):
        draw.text(
            (x, height - dp(30) + i * dp(9)),
            line_text,
            font=font(7),
            fill=(0x55, 0x55, 0x55),
        )

    img.save(OUT / "setup_complete_page.png")
    print("  wrote     design/out/setup_complete_page.png")


if __name__ == "__main__":
    main()
