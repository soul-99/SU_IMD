#!/usr/bin/env python3
"""Template: the existing dialogs used as setup steps, with Skip and Next below.

    setup_dialog_steps.png   the Settings to hide dialog as it appears in Settings today,
                             beside the same dialog as a setup step - identical body, its
                             action row swapped for Skip and Next.

Nothing about the dialogs' bodies changes. The only difference is the action slot each of them
already has, which carries Save in Settings and Skip / Next during setup.

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


PAL = {
    "primary": (0x4C, 0x66, 0x2B),
    "onPrimary": (0xFF, 0xFF, 0xFF),
    "surface": (0xF9, 0xFA, 0xEF),
    "onSurface": (0x1A, 0x1C, 0x16),
    "onSurfaceVariant": (0x44, 0x48, 0x3D),
    "lowest": (0xFF, 0xFF, 0xFF),
    "outline": (0xC5, 0xC8, 0xBA),
}

ROWS = [
    ("Developer settings", None),
    ("USB debugging", "stopping USB debugging will kill Shizuku"),
    ("Wireless debugging", None),
    ("Accessibility services", "Only apps selected in IMD settings"),
    ("Shizuku service", "ensure Shizuku values are properly"),
    ("Display over other apps", "Only apps selected in IMD settings"),
]


def dialog(img, draw, x, y, w, actions, scrim):
    h = dp(430)

    if scrim:
        draw.rectangle([x - dp(18), y - dp(30), x + w + dp(18), y + h + dp(46)], fill=(0x2A, 0x2C, 0x26))

    draw.rounded_rectangle([x, y, x + w, y + h], radius=dp(26), fill=PAL["lowest"])

    cy = y + dp(22)

    draw.text((x + dp(20), cy), "Settings to hide/ disable", font=font(15, True), fill=PAL["onSurface"])
    cy += dp(28)

    draw.text(
        (x + dp(20), cy),
        "These settings are hidden when you launch",
        font=font(10),
        fill=PAL["onSurfaceVariant"],
    )
    cy += dp(14)
    draw.text((x + dp(20), cy), "an app.", font=font(10), fill=PAL["onSurfaceVariant"])
    cy += dp(22)

    for label, note in ROWS:
        draw.text((x + dp(20), cy), label, font=font(12), fill=PAL["onSurface"])

        sx = x + w - dp(58)
        draw.rounded_rectangle([sx, cy, sx + dp(34), cy + dp(18)], radius=dp(9), fill=PAL["primary"])
        draw.ellipse([sx + dp(18), cy + dp(2), sx + dp(32), cy + dp(16)], fill=PAL["lowest"])

        cy += dp(18)

        if note:
            draw.text((x + dp(20), cy), note, font=font(9), fill=PAL["onSurfaceVariant"])
            cy += dp(14)

        cy += dp(8)

    # The action row - the only thing that differs between the two.
    ay = y + h - dp(38)
    ax = x + w - dp(20)

    for label in reversed(actions):
        tw = draw.textlength(label, font=font(12, True))
        draw.text((ax - tw, ay), label, font=font(12, True), fill=PAL["primary"])
        ax -= tw + dp(24)


def main():
    OUT.mkdir(exist_ok=True)

    width, height = dp(720), dp(560)
    img = Image.new("RGB", (width, height), (0xFA, 0xFA, 0xFA))
    draw = ImageDraw.Draw(img)

    draw.text(
        (dp(20), dp(14)),
        "The dialogs we already have, used as setup steps",
        font=font(16, True),
        fill=(0x33, 0x33, 0x33),
    )

    draw.text((dp(30), dp(46)), "in Settings — today", font=font(11, True), fill=(0x33, 0x33, 0x33))
    dialog(img, draw, dp(30), dp(66), dp(290), ["SAVE"], scrim=False)

    draw.text((dp(390), dp(46)), "as a setup step", font=font(11, True), fill=(0x33, 0x33, 0x33))
    dialog(img, draw, dp(390), dp(66), dp(290), ["SKIP", "NEXT"], scrim=True)

    for i, note in enumerate([
        "Identical body — same composable, same rows, same notes. Only the action slot each dialog",
        "already has changes: SAVE in Settings, SKIP / NEXT during setup. NEXT saves and moves on;",
        "SKIP moves on and writes nothing, so the install is left exactly as it was found.",
    ]):
        draw.text((dp(20), height - dp(52) + i * dp(14)), note, font=font(9), fill=(0x44, 0x44, 0x44))

    img.save(OUT / "setup_dialog_steps.png")
    print("  wrote     design/out/setup_dialog_steps.png")


if __name__ == "__main__":
    main()
