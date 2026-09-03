#!/usr/bin/env python3
"""
r30 — the green, and the one thing that stops the light primary being used in dark mode as-is.

The author: *"i like the light primaries lets use those for both modes"*.

## The catch, in numbers

`primary` in a Material dark scheme does **two** jobs. It fills things — a switch track, a filled
button, a checkbox — and it is also **ink**: about thirty places in this app draw a word, a link or
an icon in `colorScheme.primary` directly on the page or on a card. A light scheme gets away with
one token for both because its page is white. A dark scheme does not.

The deep green measured against both jobs, on this app's own surfaces:

| | white on it | as a word on the page | as a word on a card |
| --- | --- | --- | --- |
| **#58743E** (the light primary) | 5.27 ✓ | 3.20 ✗ | **2.38 ✗** |
| #B3E675 (today) | 1.45 ✗ | 11.65 | 8.65 |

2.38:1 is not "a bit dim" — it is the emphasised phrases in the Support dialog, the links, the
green headings and the tinted icons all going nearly invisible inside every dialog in the app. So
the request is right and the single token is what cannot carry it. Three ways out, drawn below.

* **A — exactly as asked.** `primary` in dark becomes the light green, `onPrimary` becomes white.
  The switches and buttons are exactly what he liked. The green ink column shows the cost.
* **B — split the two jobs.** Fills take the deep green with white on them; ink keeps a green
  light enough to read. Identical to A everywhere he looked, and nothing else breaks. Costs one new
  token, wired into the two places that fill: `GetoToggles` and the filled button default.
* **C — one token, no split.** Keep Material's contract (dark ink on a light primary) but take the
  primary a long way down: **#8FAE6E**. Every ratio clears 4.5:1 both ways, and it is far off the
  highlighter without being the light green.

⚠ **The light scheme is not touched in any of these.** Today's `#4E7819` and the muted `#58743E` he
picked out are within a hair of each other; the light scheme was never the thing that read as a
highlighter, and leaving it exactly as it is means one scheme fewer to re-test.

Writes a comparison sheet; changes nothing in the app.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path("/root/work/r30_green_preview.html")


def to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex_value: str) -> float:
    text = hex_value.lstrip("#")

    r, g, b = (to_linear(int(text[i:i + 2], 16) / 255) for i in (0, 2, 4))

    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    high, low = sorted((luminance(a), luminance(b)), reverse=True)

    return round((high + 0.05) / (low + 0.05), 2)


# The light scheme, unchanged, and the dark scheme's neutrals, unchanged. Only `fill`, `onFill`
# and `ink` differ between the four dark columns.
LIGHT = {
    "fill": "4E7819",
    "onFill": "FFFFFF",
    "ink": "4E7819",
    "container": "CFFF91",
    "onContainer": "102000",
    "surface": "F9FAEF",
    "onSurface": "1A1C16",
    "card": "E8E9DE",
    "outline": "75796C",
    "offTrack": "E1E4D5",
}

DARK = {
    "container": "375F05",
    "onContainer": "CFFF91",
    "surface": "1B1E16",
    "onSurface": "E2E3D8",
    "card": "31352B",
    "outline": "8F9285",
    "offTrack": "44483D",
}

VARIANTS = [
    (
        "Now",
        "what is in the app today",
        {"fill": "B3E675", "onFill": "1F3800", "ink": "B3E675"},
    ),
    (
        "A &mdash; as asked",
        "the light green in dark mode too, white on it",
        {"fill": "58743E", "onFill": "FFFFFF", "ink": "58743E"},
    ),
    (
        "B &mdash; split",
        "same fill as A; ink stays readable",
        {"fill": "58743E", "onFill": "FFFFFF", "ink": "B0D18C"},
    ),
    (
        "C &mdash; one token",
        "no split, primary taken well down",
        {"fill": "8FAE6E", "onFill": "1F3800", "ink": "8FAE6E"},
    ),
]


def chrome(t: dict[str, str], dark: bool) -> str:
    """Real app chrome, plus the thing a fill-only preview hides: green used as ink."""
    ratio = contrast(t["ink"], t["card"])

    verdict = "pass" if ratio >= 4.5 else "fail"

    return f"""
<div class="panel" style="background:#{t['surface']};color:#{t['onSurface']}">
  <div class="row">
    <button style="background:#{t['fill']};color:#{t['onFill']}">Launch app</button>
    <span class="switch" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span>
    <span class="switch off" style="background:#{t['offTrack']};border-color:#{t['outline']}"><i style="background:#{t['outline']}"></i></span>
    <span class="cb" style="background:#{t['fill']};color:#{t['onFill']}">&#10003;</span>
  </div>
  <div class="card" style="background:#{t['card']}">
    <div class="title">IMD Settings Manager</div>
    <div class="cardrow"><span>Developer settings</span><span class="switch small" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span></div>
    <div class="cardrow"><span>USB debugging</span><span class="switch small" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span></div>
    <div class="cardrow"><span>Wireless debugging</span><span class="switch small" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span></div>
    <div class="cardrow"><span>Accessibility services</span><span class="switch small" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span></div>
    <div class="cardrow"><span>Shizuku service</span><span class="switch small off" style="background:#{t['offTrack']};border-color:#{t['outline']}"><i style="background:#{t['outline']}"></i></span></div>
    <div class="cardrow"><span>Display over other apps</span><span class="switch small" style="background:#{t['fill']}"><i style="background:#{t['onFill']}"></i></span></div>
    <div class="ink">You can do these for free, if you want to
      <b style="color:#{t['ink']}">support this project</b> and
      <b style="color:#{t['ink']}">keep it alive</b>.<br>
      <span style="color:#{t['ink']}">Report</span> bugs &middot;
      <span style="color:#{t['ink']}">Join</span> discussions</div>
  </div>
  <div class="hex">
    fill <b>#{t['fill']}</b> &middot; ink on it {contrast(t['fill'], t['onFill'])}:1<br>
    ink <b>#{t['ink']}</b> on the card <span class="{verdict}">{ratio}:1</span>
  </div>
</div>"""


columns = "".join(
    f"""
<section>
  <h2>{name}</h2>
  <p class="note">{note}</p>
  {chrome(LIGHT, dark=False)}
  {chrome({**DARK, **tokens}, dark=True)}
</section>"""
    for name, note, tokens in VARIANTS
)

OUT.write_text(
    f"""<!doctype html>
<meta charset="utf-8">
<title>IMD r30 - the green</title>
<style>
  body {{ margin:0; padding:28px; background:#101210; color:#E6E8E3;
         font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .lede {{ color:#9AA096; margin:0 0 22px; max-width:82ch; }}
  .lede b {{ color:#E6E8E3; font-weight:600; }}
  .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; }}
  section {{ min-width:0; }}
  h2 {{ font-size:15px; margin:0 0 2px; }}
  .note {{ color:#8B918A; font-size:12px; margin:0 0 10px; min-height:34px; }}
  .panel {{ border-radius:14px; padding:14px; margin-bottom:12px; }}
  .row {{ display:flex; gap:9px; align-items:center; flex-wrap:wrap; margin-bottom:12px; }}
  button {{ border:0; border-radius:20px; padding:9px 15px; font:inherit;
            font-weight:600; font-size:12px; cursor:default; }}
  .switch {{ position:relative; width:44px; height:26px; border-radius:13px;
             display:inline-block; border:2px solid transparent; flex:none; }}
  .switch i {{ position:absolute; right:4px; top:50%; transform:translateY(-50%);
               width:19px; height:19px; border-radius:50%; }}
  .switch.off i {{ right:auto; left:6px; width:13px; height:13px; }}
  .switch.small {{ width:38px; height:23px; }}
  .switch.small i {{ width:16px; height:16px; }}
  .switch.small.off i {{ width:11px; height:11px; }}
  .cb {{ width:22px; height:22px; border-radius:5px; display:inline-flex;
         align-items:center; justify-content:center; font-size:14px; font-weight:700; }}
  .card {{ border-radius:12px; padding:12px; }}
  .title {{ font-size:12px; font-weight:700; opacity:.75; margin-bottom:6px; }}
  .cardrow {{ display:flex; justify-content:space-between; align-items:center;
              gap:10px; padding:5px 0; font-size:12px; }}
  .ink {{ font-size:12px; line-height:1.7; margin-top:10px;
          padding-top:9px; border-top:1px solid #8888881f; }}
  .hex {{ font:11px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;
          opacity:.62; margin-top:10px; }}
  .pass {{ color:#7BC96F; }}
  .fail {{ color:#FF8A80; font-weight:700; }}
</style>
<h1>The light green in dark mode &mdash; and what it costs</h1>
<p class="lede">In a dark scheme <b>primary does two jobs</b>: it fills a switch track or a button,
and it is also the colour about thirty places in this app draw a word, a link or an icon in. The
light green is excellent at the first and fails the second &mdash; look at the line of text under
the manager rows in column&nbsp;A, and at the red ratio beneath it. <b>B</b> gives you A's
switches with that line still readable. <b>C</b> keeps one token and takes the primary a long way
down instead. Light panel above, dark below; the light scheme is identical in all four.</p>
<div class="grid">{columns}</div>
""",
    encoding="utf-8",
)

print(f"wrote {OUT}")

for name, _, tokens in VARIANTS:
    ratio = contrast(tokens["ink"], DARK["card"])

    print(
        f"  {name.replace('&mdash;', '-'):18s} fill #{tokens['fill']}  ink #{tokens['ink']}  "
        f"ink on card {ratio}:1 {'PASS' if ratio >= 4.5 else 'FAIL'}",
    )
