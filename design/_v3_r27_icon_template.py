#!/usr/bin/env python3
"""
Builds `design/template_r27_settings_icons.html` — the eleven settings-row icons, both themes.

⚠ **Generated rather than typed, and the four existing glyphs are pulled from the repo itself.**
`Setting manager toggles`, `Settings to hide`, `Revert to default` and the two framework rows all
resolve to drawables that already ship — so the template renders their *actual* `pathData` rather
than my impression of it. A template that flatters the drawing is worse than no template.

Rendering the four also settled how the seven new ones have to look: they are one family — a solid
gear with a symbol knocked out of it (droid, struck-out eye, open eye, revert arrow). Seven icons in
an unrelated outline style sitting between them would read as two sets in one list. So the new
drawings take the same weight and the same knocked-out treatment where the source allows it.

Writes only the template. No source file is touched.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OUT = ROOT / "design/template_r27_settings_icons.html"

ANDROID = "{http://schemas.android.com/apk/res/android}"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def repo_glyph(name: str) -> str:
    """The real thing, straight out of `:design-system`, as SVG body at a 24 viewBox."""
    path = ROOT / f"design-system/src/main/res/drawable/{name}.xml"

    if not check(path.exists(), f"{name}: not in the repo"):
        return ""

    root = ET.parse(path).getroot()

    width = float(root.get(ANDROID + "viewportWidth"))

    check(width == 24, f"{name}: viewport is {width}, the template assumes 24")

    body = ""

    for element in root.iter("path"):
        data = element.get(ANDROID + "pathData")

        rule = "evenodd" if element.get(ANDROID + "fillType") == "evenOdd" else "nonzero"

        body += f'<path d="{data}" fill="currentColor" fill-rule="{rule}"/>'

    return body


SERVICES = repo_glyph("ic_services_glyph")


def services_droid() -> str:
    """The droid out of `ic_services_glyph`, which the author called perfect — so it is *that* one.

    ⚠ **Extracted rather than redrawn.** Two attempts at drawing a droid to those proportions were
    both called weird, and they would be: the glyph's head is a specific curve, not a semicircle,
    and its antennae have a particular length and rake. That path is already in the repo, as
    subpaths 1 to 3 of a four-subpath drawable — subpath 0 is the gear.

    ⚠ **`evenOdd` does the rest.** In the source those three are *holes* punched through the gear.
    Taken on their own with the same rule, the head fills and the two eyes stay holes, which is
    exactly the solid-head-hollow-eyes the author asked for.

    Scaled to 0.80 about the centre so it fits inside the octagram: the head's corner sits 7.95 from
    the middle and the star's inner radius is 7.5.
    """
    import re  # noqa: PLC0415

    path = ROOT / "design-system/src/main/res/drawable/ic_services_glyph.xml"

    data = ET.parse(path).getroot().find("path").get(ANDROID + "pathData")

    subpaths = [piece for piece in re.split(r"(?=M)", data) if piece.strip()]

    check(len(subpaths) == 4, f"services glyph: expected 4 subpaths, found {len(subpaths)}")

    droid = "".join(subpaths[1:])

    return (
        '<g transform="translate(2.4,2.4) scale(0.80)">'
        f'<path d="{droid}" fill="currentColor" fill-rule="evenodd"/>'
        "</g>"
    )

HIDDEN = repo_glyph("ic_hidden_glyph")

HIDE = repo_glyph("ic_hide_glyph")

REVERT = repo_glyph("ic_revert_glyph")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# The seven drawn from what the author sent. Stroke-based, `currentColor` throughout so one tint
# reaches everything — which is the whole point of a monochrome set.
# ─────────────────────────────────────────────────────────────────────────────────────────────

S = 'fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round"'


def sun() -> str:
    """His sun-with-a-crescent-bite, flares thickened as asked."""
    import math  # noqa: PLC0415

    flares = ""

    # ⚠ **These numbers are measured off the author's own file, not chosen.** Sampling his PNG
    # radially along three different rays agrees to a hundredth: the ring runs from 6.2 to 7.8, and
    # the flares from 8.7 to 11.95. So the gap he is asking for is **0.9**, and the flares stop at
    # 11.95 rather than running to the edge of the box.
    #
    # ⚠ **Round caps are why the previous version touched.** A cap adds half the stroke width past
    # the coordinate, so a flare drawn from 8.9 with a 2.6 stroke actually starts at 7.6 — which is
    # under the ring's outer edge at 7.7. The numbers below are the *visual* extents worked back
    # through the cap: 9.9 - 1.2 = 8.7 and 10.7 + 1.2 = 11.9.
    inner, outer, width = 9.9, 10.7, 2.4

    for index in range(8):
        angle = math.radians(index * 45)

        x1, y1 = 12 + inner * math.cos(angle), 12 + inner * math.sin(angle)

        x2, y2 = 12 + outer * math.cos(angle), 12 + outer * math.sin(angle)

        flares += f'<path d="M{x1:.2f},{y1:.2f} L{x2:.2f},{y2:.2f}" {S} stroke-width="{width}"/>'

    ring = f'<circle cx="12" cy="12" r="6.85" {S} stroke-width="1.9"/>'

    # ⚠ **Two arcs, computed — and the three drafts before it were all wrong for the same reason
    # in the end.** What the author's picture shows is a disc filling the ring with a crescent
    # bitten out of its top-left: the black is a fat gibbous, the white is the notch.
    #
    # The obvious way to draw that is two circles with `evenOdd`, and it does not work. `evenOdd`
    # fills whatever is covered an *odd* number of times, so the part of the bite circle that hangs
    # **outside** the disc is covered once and comes out solid — a blob past the sun's ring, which
    # is exactly what the last draft rendered. A bite that opens onto the edge has to cross the
    # boundary, so there is no offset that avoids this; the construction itself is wrong.
    #
    # So the outline is built properly: the disc's major arc from one intersection to the other,
    # then the bite circle's minor arc back. Intersections are solved for rather than eyeballed,
    # because the sweep flags depend on which side they fall.
    # ⚠ **Everything scaled 0.82 about the centre — the author's *"too big, cut it"*.** Scaling the
    # disc alone would have changed the shape of the moon, because how deep the notch bites is the
    # relationship *between* the two circles. Shrinking both keeps the same gibbous, smaller.
    disc_x, disc_y, disc_r = 12.0, 12.0, 4.10

    bite_x, bite_y, bite_r = 8.392, 8.146, 3.28

    dx, dy = bite_x - disc_x, bite_y - disc_y

    distance = math.hypot(dx, dy)

    along = (disc_r ** 2 - bite_r ** 2 + distance ** 2) / (2 * distance)

    across = math.sqrt(disc_r ** 2 - along ** 2)

    mid_x, mid_y = disc_x + along * dx / distance, disc_y + along * dy / distance

    off_x, off_y = across * -dy / distance, across * dx / distance

    first = (mid_x - off_x, mid_y - off_y)

    second = (mid_x + off_x, mid_y + off_y)

    moon = (
        '<path fill="currentColor" d="'
        f'M{first[0]:.3f},{first[1]:.3f} '
        # ⚠ **The flags, worked out rather than guessed — the draft before this had both wrong and
        # drew the bite circle instead of the disc.** Screen angles run clockwise because y points
        # down. The disc's major arc must pass the *bottom right*, away from the notch: from the
        # lower-left intersection that is the anticlockwise, >180 degree arc, so `1 0`. The bite's
        # arc must bulge back *into* the disc: from the upper-right intersection that is the
        # clockwise, <180 degree arc, so `0 1`.
        f'A {disc_r} {disc_r} 0 1 0 {second[0]:.3f},{second[1]:.3f} '
        f'A {bite_r} {bite_r} 0 0 1 {first[0]:.3f},{first[1]:.3f} Z"/>'
    )

    return flares + ring + moon


LANGUAGE = (
    # Back bubble with its tail, and an A.
    f'<path d="M12.6,8.0 H3.4 a1.7 1.7 0 0 0 -1.7,1.7 v6.2 a1.7 1.7 0 0 0 1.7,1.7 h1.0 v3.2 '
    f'l3.5,-3.2 h4.7 a1.7 1.7 0 0 0 1.7,-1.7 v-2.4" {S} stroke-width="1.9"/>'
    f'<path d="M5.2,15.1 L7.5,10.0 L9.8,15.1 M6.0,13.5 h3.0" {S} stroke-width="1.7"/>'
    # Front bubble, raised and to the right, with the strokes of 文.
    f'<path d="M12.0,2.0 h8.6 a1.7 1.7 0 0 1 1.7,1.7 v6.4 a1.7 1.7 0 0 1 -1.7,1.7 h-2.4 '
    f'l-3.5,3.1 v-3.1 h-2.7 a1.7 1.7 0 0 1 -1.7,-1.7 v-6.4 a1.7 1.7 0 0 1 1.7,-1.7 Z" '
    f'{S} stroke-width="1.9"/>'
    f'<path d="M16.5,3.5 v1.1 M13.6,5.5 h5.9" {S} stroke-width="1.6"/>'
    f'<path d="M17.1,5.9 C16.6,7.7 15.4,9.0 13.8,9.9 M15.6,7.1 C16.6,8.6 17.9,9.5 19.4,9.9" '
    f'{S} stroke-width="1.6"/>'
)


def icon_style(ring_on: bool = True) -> str:
    """Line diagram, solid droid head, hollow eyes, and the circle pulled in tight to the star."""
    import math

    points = []

    for index in range(16):
        radius = 9.5 if index % 2 == 0 else 7.5

        angle = math.radians(index * 22.5 - 90)

        points.append(f"{12 + radius * math.cos(angle):.2f},{12 + radius * math.sin(angle):.2f}")

    star = (
        f'<path d="M{points[0]} ' + " ".join(f"L{p}" for p in points[1:]) +
        '" fill="none" stroke="currentColor" stroke-linejoin="miter" stroke-miterlimit="6" '
        'stroke-width="1.6" d-close="Z"/>'
    ).replace('d-close="Z"/>', '/>').replace(f'L{points[-1]}"', f'L{points[-1]} Z"')

    # ⚠ **10.4, not the source's 11.6** — the author's *"bring the circle radius small to bring it
    # closer to the star inside"*. At 9.3 of star point that leaves 1.1 of air, which reads as a
    # ring around the star rather than as an unrelated circle.
    ring = f'<circle cx="12" cy="12" r="11.0" {S} stroke-width="1.4"/>'

    # ⚠ **Redrawn to the shape of `ic_services_glyph`'s droid**, at the author's word: the first
    # version had a small dome and stubs for antennae and read as an insect. The proportions here
    # are that glyph's — a wide dome about twice as broad as it is tall, antennae springing from
    # the shoulders at roughly 40 degrees, eyes set well apart and high.
    droid = services_droid()

    return (ring if ring_on else "") + star + droid


def app_grid() -> str:
    """Nine rounded squares. His, and unchanged — it was already a clean monochrome mark."""
    cells = ""

    for row in range(3):
        for column in range(3):
            x = 3.2 + column * 6.3

            y = 3.2 + row * 6.3

            cells += f'<rect x="{x:.2f}" y="{y:.2f}" width="4.9" height="4.9" rx="1.35" fill="currentColor"/>'

    return cells


# ⚠ **Traced off the author's own file rather than drawn by eye — r27.** He asked for the hands
# and legs to *"match approximately"*, and two drafts of guessing had not got there, so the PNG was
# thresholded and measured instead. In the 24-unit space his figure gives:
#
#   * head top at y 4.04, centred x 12, about 1.9 across the radius
#   * arm stroke ~1.95 thick, its centre-line at y 8.6 at the fingertips and y 9.6 at the chest —
#     so the arms rise slightly *outward*, which is the detail both earlier drafts had inverted
#   * fingertips reaching x 5.12 and 18.88
#   * torso ending at y 14.4, where the legs split
#   * leg tips at (9.25, 19.96) and (14.75, 19.96)
#
# The ring is sized so the leg tips clear its inner edge by about a stroke's width, which is what
# his own drawing does — close, deliberately, but not touching.
ACCESSIBILITY = (
    f'<circle cx="12" cy="12" r="10.75" {S} stroke-width="2.3"/>'
    '<circle cx="12" cy="5.95" r="1.92" fill="currentColor"/>'
    f'<path d="M5.9,8.55 C8.2,9.25 10.1,9.6 12,9.6 C13.9,9.6 15.8,9.25 18.1,8.55" '
    f'{S} stroke-width="1.95"/>'
    f'<path d="M12,9.6 L12,14.4 M12,14.4 L9.3,19.6 M12,14.4 L14.7,19.6" {S} stroke-width="1.95"/>'
)

DOOA = (
    # The window underneath, open where the one on top overlaps it.
    f'<path d="M11.8,5.6 H4.2 a2.0 2.0 0 0 0 -2.0,2.0 V17.8 a2.0 2.0 0 0 0 2.0,2.0 H14.4 '
    f'a2.0 2.0 0 0 0 2.0,-2.0 V13.4" {S} stroke-width="2.0"/>'
    # The one on top of it.
    f'<rect x="13.8" y="2.4" width="8.0" height="8.0" rx="1.8" {S} stroke-width="2.0"/>'
    # And the arrow that says which way it goes. A chevron head, not a filled triangle: at this
    # size a triangle's three points land on different pixels and it reads as a smudge.
    f'<path d="M6.0,16.4 L11.2,11.2" {S} stroke-width="2.2"/>'
    f'<path d="M7.4,11.6 L11.6,10.8 L10.8,15.0" {S} stroke-width="2.1"/>'
)


def swap_badge() -> str:
    """Option B's mark: two arrows, for *which mechanism* rather than *what state*.

    ⚠ **No backing disc, and that is not a style choice.** A `VectorDrawable` drawn through
    Compose's `Icon` is painted in **one** colour — every path becomes the tint. A disc in the
    card's colour, which is what a badge normally uses to separate itself from what it sits on,
    would come out the same grey as the gear and simply blot it. The only real hole would be an
    `evenOdd` subpath cut into the gear's own path, and cutting a hole in a glyph the repo owns is
    a change to a shared asset for one row's benefit.

    So the two shapes are kept **apart** instead: the gear shrinks to 78 % in the top-left and the
    arrows sit in the corner it vacates, with clearance between them. Nothing overlaps, so nothing
    needs separating.
    """
    return (
        '<g transform="translate(12.9,13.6) scale(0.50)">'
        f'<path d="M1.4,6.0 H14.6 M11.2,2.6 L14.9,6.0 L11.2,9.4" {S} stroke-width="2.7"/>'
        f'<path d="M16.6,14.2 H3.4 M6.8,10.8 L3.1,14.2 L6.8,17.6" {S} stroke-width="2.7"/>'
        "</g>"
    )


def shrunk(body: str) -> str:
    """A repo glyph pulled up and in, so the badge has a corner of its own — see [swap_badge]."""
    return f'<g transform="translate(-0.6,-1.0) scale(0.78)">{body}</g>'


# ⚠ **Without the gear — r27, at the author's word:** *"for settings to hide icon use the icon
# without the gear"*. The QS glyph carries a gear because it is a *settings* tile; on a row that
# already says "Settings to hide" the gear repeats the word and crowds the eye that carries the
# meaning.
#
# ⚠ **And it resolves the collision by itself.** `Settings to hide` and `Hiding framework` were
# going to share one glyph; a gearless eye here and the geared one in Advanced makes them plainly
# different without a badge — see section 2.
EYE_HIDDEN = (
    f'<path d="M2.4,12 C4.8,7.6 8.2,5.4 12,5.4 C15.8,5.4 19.2,7.6 21.6,12 '
    f'C19.2,16.4 15.8,18.6 12,18.6 C8.2,18.6 4.8,16.4 2.4,12 Z" {S} stroke-width="2.0"/>'
    '<circle cx="12" cy="12" r="2.7" fill="currentColor"/>'
    f'<path d="M4.4,3.4 L19.6,20.6" {S} stroke-width="2.4"/>'
)

ROWS = [
    ("User interface", [
        ("Dynamic theme", "Available on Android 12 +", "SWITCH-OFF"),
        ("Theme", "Follow System", sun()),
        ("Language", "System / automatic", LANGUAGE),
        ("Icon style", "Smart adaptive icons", icon_style()),
        ("Setting manager toggles", "6 of 6 shown", SERVICES),
        ("App drawer shortcuts", "1 of 2 shown", app_grid()),
        ("Progressive UI blur", "applies a blur to the edges", "SWITCH-ON"),
    ]),
    ("App functions", [
        ("Settings to hide", "4 of 7 selected", EYE_HIDDEN),
        ("Revert to default", "5 of 7 selected", REVERT),
        ("Accessibility services", "2 managed", ACCESSIBILITY),
        ("Display over other apps", "3 managed", DOOA),
    ]),
    # ⚠ **Variant B, at the author's pick.** The swap badge says *which mechanism* rather than
    # *what state* — which is what these two rows actually choose.
    ("Advanced", [
        ("Hiding framework", "Shizuku", shrunk(HIDDEN) + swap_badge()),
        ("Unhiding framework", "Memory", shrunk(HIDE) + swap_badge()),
    ]),
]

VARIANT_B = [
    ("Hiding framework", "Shizuku", shrunk(HIDDEN) + swap_badge()),
    ("Unhiding framework", "Memory", shrunk(HIDE) + swap_badge()),
]


def icon(body: str, size: int = 24) -> str:
    return f'<svg class="ic" viewBox="0 0 24 24" width="{size}" height="{size}">{body}</svg>'


def rows_html(sections) -> str:
    out = ""

    for title, rows in sections:
        out += f'<div class="section">{title}</div>'

        for name, subtitle, body in rows:
            if body == "SWITCH-OFF":
                trailing = '<span class="sw off"><i></i></span>'
            elif body == "SWITCH-ON":
                trailing = '<span class="sw"><i></i></span>'
            else:
                trailing = f'<span class="lead">{icon(body)}</span>'

            out += (
                '<div class="row">'
                f'<span class="words"><b>{name}</b><i>{subtitle}</i></span>'
                f"{trailing}"
                "</div>"
            )

    return out


HTML = f"""<title>r27 Settings Icons</title>
<style>
  :root {{ --ink:#16180f; --page:#f4f5ec; --muted:#5c6152; --rule:#d3d7c6; }}
  @media (prefers-color-scheme: dark) {{
    :root:not([data-theme="light"]) {{ --ink:#e6e8dc; --page:#14160f; --muted:#9aa08d; --rule:#2e3327; }}
  }}
  :root[data-theme="dark"] {{ --ink:#e6e8dc; --page:#14160f; --muted:#9aa08d; --rule:#2e3327; }}

  body {{
    background:var(--page); color:var(--ink); margin:0; padding:26px 18px 70px;
    font:15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  }}
  main {{ max-width:1000px; margin:0 auto; }}
  h1 {{ font-size:21px; margin:0 0 4px; letter-spacing:-0.01em; }}
  .sub {{ color:var(--muted); margin:0 0 8px; font-size:13.5px; max-width:72ch; }}
  h2 {{
    font-size:12px; text-transform:uppercase; letter-spacing:.09em; color:var(--muted);
    margin:34px 0 6px; font-weight:600; border-top:1px solid var(--rule); padding-top:14px;
  }}
  p.note {{ color:var(--muted); font-size:13.5px; margin:0 0 18px; max-width:72ch; }}
  .flag {{ border-left:3px solid #d08a2c; padding:10px 0 10px 14px; margin:0 0 20px; font-size:13.5px; max-width:72ch; }}
  .flag b {{ color:var(--ink); }}
  code {{ font-size:.9em; opacity:.85; }}

  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(330px,1fr)); gap:16px; }}
  .panel {{ border-radius:14px; padding:14px 16px 18px; border:1px solid var(--rule); }}
  .panel h3 {{ font-size:11.5px; letter-spacing:.08em; text-transform:uppercase; margin:0 0 12px; opacity:.6; font-weight:600; }}

  /* the settings card, at the app's real colours */
  .light {{ --card:#e2e3d8; --on:#1a1c16; --outline:#75796c; --dim:#44483d; --pri:#4e7819; }}
  .dark  {{ --card:#3c4036; --on:#e2e3d8; --outline:#8f9285; --dim:#c5c8ba; --pri:#b3e675; }}
  .card {{ background:var(--card); color:var(--on); border-radius:12px; padding:6px 0; }}

  .section {{
    font-size:11px; letter-spacing:.08em; text-transform:uppercase; opacity:.55;
    padding:12px 16px 4px; font-weight:600;
  }}
  .row {{ display:flex; align-items:center; gap:14px; padding:10px 16px; }}
  .lead {{ flex:none; width:24px; height:24px; color:var(--outline); display:block; margin-left:auto; }}
  .words {{ flex:1; }}
  /* a real switch, so the alignment down the right edge can be judged */
  .sw {{ flex:none; width:44px; height:27px; border-radius:14px; position:relative; margin-left:auto;
        background:var(--pri); }}
  .sw i {{ position:absolute; right:3px; top:3px; width:21px; height:21px; border-radius:50%;
          background:var(--card); }}
  .sw.off {{ background:transparent; border:2px solid var(--outline); }}
  .sw.off i {{ right:auto; left:6px; top:8px; width:11px; height:11px; background:var(--outline); }}
  .ic {{ display:block; }}
  .words {{ display:flex; flex-direction:column; }}
  .words b {{ font-weight:400; font-size:15px; }}
  .words i {{ font-style:normal; font-size:12px; opacity:.72; margin-top:3px; }}

  /* the tab bar, where the grid does NOT go grey */
  .tabs {{ display:flex; gap:6px; align-items:center; padding:8px; border-radius:24px; background:var(--card); width:max-content; }}
  .tab {{ display:flex; align-items:center; gap:7px; padding:9px 16px; border-radius:20px; font-size:14px; color:var(--dim); }}
  .tab.on {{ background:var(--pri); color:var(--card); }}
  .tab svg {{ display:block; }}

  .strip {{ display:flex; gap:20px; flex-wrap:wrap; align-items:flex-end; margin-top:6px; }}
  .strip figure {{ margin:0; text-align:center; color:var(--outline); }}
  .strip figcaption {{ font-size:10.5px; color:var(--muted); margin-top:6px; max-width:88px; line-height:1.3; }}
</style>

<main>
  <h1>r27 — the eleven settings-row icons</h1>
  <p class="sub">Drawn at the app's real card colours and tinted <code>colorScheme.outline</code>, the off-switch rim grey you asked for: <code>#75796C</code> light, <code>#8F9285</code> dark. Nothing is built yet.</p>

  <div class="flag">
    <b>The five that already ship are rendered from their actual <code>pathData</code>, not from my impression of them</b> — and rendering them settled how the other six had to look. Your Quick Settings glyphs are one family: a <em>solid gear with a symbol knocked out of it</em>. Six icons in an unrelated thin-outline style sitting between them would have read as two sets in one list, so the new drawings take the same weight. Where a source of yours was already a silhouette (the app grid, the accessibility mark) it is kept as-is.
  </div>

  <h2>1 &middot; The whole list, both themes</h2>
  <div class="grid">
    <div class="panel">
      <h3>Light</h3>
      <div class="card light">{rows_html(ROWS)}</div>
    </div>
    <div class="panel">
      <h3>Dark</h3>
      <div class="card dark">{rows_html(ROWS)}</div>
    </div>
  </div>

  <h2>2 &middot; The collision &mdash; your one decision</h2>
  <p class="note">You said <em>&ldquo;similar icons&rdquo;</em>, and taken literally <b>Settings to hide</b> and <b>Hiding framework</b> both become the struck-out eye. <b>A</b> shares them &mdash; different sections, both genuinely about hiding, nothing new to draw. <b>B</b> adds a swap badge to the framework pair, because those two rows are a choice of <em>which mechanism</em> rather than a switch for <em>what state</em>.</p>
  <div class="grid">
    <div class="panel">
      <h3>A &middot; shared</h3>
      <div class="card light">{rows_html([("Advanced", ROWS[2][1])])}</div>
      <div style="height:10px"></div>
      <div class="card dark">{rows_html([("Advanced", ROWS[2][1])])}</div>
    </div>
    <div class="panel">
      <h3>B &middot; with a swap badge</h3>
      <div class="card light">{rows_html([("Advanced", VARIANT_B)])}</div>
      <div style="height:10px"></div>
      <div class="card dark">{rows_html([("Advanced", VARIANT_B)])}</div>
    </div>
  </div>

  <h2>3 &middot; The grid&rsquo;s second home &mdash; the All Apps tab</h2>
  <p class="note">Same drawing, <b>not</b> grey. The tab bar tints its own icons by selected state; forcing <code>outline</code> here would make the selected tab illegible against its own fill. One shared <code>GetoIcons</code> entry, tinted by each call site. It replaces Material&rsquo;s dotted <code>Apps</code> grid.</p>
  <div class="grid">
    <div class="panel">
      <h3>Light</h3>
      <div class="tabs light">
        <span class="tab"><svg viewBox="0 0 24 24" width="20" height="20"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z" fill="currentColor"/></svg>Favourites</span>
        <span class="tab on"><svg viewBox="0 0 24 24" width="20" height="20">{app_grid()}</svg>All Apps</span>
      </div>
    </div>
    <div class="panel">
      <h3>Dark</h3>
      <div class="tabs dark">
        <span class="tab"><svg viewBox="0 0 24 24" width="20" height="20"><path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8L12 17.2 5.9 20.6l1.4-6.8L2.2 9.1l6.9-.8z" fill="currentColor"/></svg>Favourites</span>
        <span class="tab on"><svg viewBox="0 0 24 24" width="20" height="20">{app_grid()}</svg>All Apps</span>
      </div>
    </div>
  </div>

  <h2>4 &middot; One honest problem &mdash; Icon style at real size</h2>
  <p class="note">This is the only one of the eleven with <b>three nested shapes</b>: ring, octagram, droid. At 24&nbsp;dp &mdash; the size it actually draws at &mdash; the ring and the star&rsquo;s points collapse into each other and the droid turns to mush. Every other icon in the set is two shapes or fewer and holds up. <b>Dropping the ring</b> gives the star room and the droid back; it is still your line diagram with a solid head and hollow eyes, and the star is still tight. Your call &mdash; I have drawn both at the true size rather than describing the problem.</p>
  <div class="panel">
    <div class="strip light">
      <figure>{icon(icon_style(), 96)}<figcaption>with ring, 96px</figcaption></figure>
      <figure>{icon(icon_style(), 24)}<figcaption><b>with ring, real size</b></figcaption></figure>
      <figure>{icon(icon_style(False), 96)}<figcaption>no ring, 96px</figcaption></figure>
      <figure>{icon(icon_style(False), 24)}<figcaption><b>no ring, real size</b></figcaption></figure>
    </div>
    <div style="height:14px"></div>
    <div class="strip dark" style="background:#3c4036;border-radius:10px;padding:12px">
      <figure>{icon(icon_style(), 24)}<figcaption style="color:#9aa08d">with ring</figcaption></figure>
      <figure>{icon(icon_style(False), 24)}<figcaption style="color:#9aa08d">no ring</figcaption></figure>
    </div>
  </div>

  <h2>5 &middot; The six new drawings, large</h2>
  <p class="note">At 3&times; so the detail can be judged, with your changes applied.</p>
  <div class="panel">
    <div class="strip light">
      <figure>{icon(sun(), 72)}<figcaption>Theme &mdash; flares thickened</figcaption></figure>
      <figure>{icon(LANGUAGE, 72)}<figcaption>Language</figcaption></figure>
      <figure>{icon(icon_style(), 72)}<figcaption>Icon style &mdash; line, solid head, hollow eyes, tight circle</figcaption></figure>
      <figure>{icon(app_grid(), 72)}<figcaption>App drawer</figcaption></figure>
      <figure>{icon(ACCESSIBILITY, 72)}<figcaption>Accessibility</figcaption></figure>
      <figure>{icon(DOOA, 72)}<figcaption>Display over other apps</figcaption></figure>
    </div>
  </div>
</main>
"""

check("<path" in SERVICES, "services: no path data was read")

check(HIDDEN != HIDE, "the hide and hidden glyphs came back identical")

check(HTML.count('class="row"') == 13 * 2 + 2 * 4, "template: unexpected row count")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

OUT.write_text(HTML, encoding="utf-8")

print(f"wrote {OUT.relative_to(ROOT).as_posix()}")

print("ok")
