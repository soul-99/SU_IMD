#!/usr/bin/env python3
"""
r30h — the three greens, before and after.

Shows what the author was looking at: the settings manager's two action buttons and the Favourites
tab's manager button each painting themselves a different green from every other button in the app,
and from each other.

Left column is the tree before r30h; right column is after. Both use the r30f `primary` (#8FAE6E),
so the only thing changing between the columns is *which role* each button draws itself in.

Writes a comparison sheet; changes nothing.
"""
from __future__ import annotations

from pathlib import Path

OUT = Path("/root/work/r30_manager_buttons.html")

LIGHT = {
    "primary": "4E7819",
    "onPrimary": "FFFFFF",
    "primaryContainer": "CFFF91",
    "onPrimaryContainer": "102000",
    "secondaryContainer": "DFF0BF",
    "onSecondaryContainer": "152405",
    "surface": "F9FAEF",
    "onSurface": "1A1C16",
    "card": "E8E9DE",
    "outline": "75796C",
    "offTrack": "E1E4D5",
    "idleFab": "E2E3D8",
    "onIdleFab": "44483D",
}

DARK = {
    "primary": "8FAE6E",
    "onPrimary": "1F3800",
    "primaryContainer": "375F05",
    "onPrimaryContainer": "CFFF91",
    "secondaryContainer": "41512C",
    "onSecondaryContainer": "DFF0BF",
    "surface": "1B1E16",
    "onSurface": "E2E3D8",
    "card": "31352B",
    "outline": "8F9285",
    "offTrack": "44483D",
    "idleFab": "3C4036",
    "onIdleFab": "C5C8BA",
}

ROWS = [
    "Developer settings",
    "USB debugging",
    "Wireless debugging",
    "Shizuku service",
    "Accessibility services",
    "Display over other apps",
]


def panel(t: dict[str, str], after: bool) -> str:
    action_bg = t["primary"] if after else t["primaryContainer"]

    action_ink = t["onPrimary"] if after else t["onPrimaryContainer"]

    fab_bg = t["primary"] if after else t["secondaryContainer"]

    fab_ink = t["onPrimary"] if after else t["onSecondaryContainer"]

    rows = "".join(
        f"""<div class="cardrow"><span>{name}</span>
        <span class="switch" style="background:#{t['primary']}"><i style="background:#{t['onPrimary']}"></i></span></div>"""
        for name in ROWS
    )

    return f"""
<div class="panel" style="background:#{t['surface']};color:#{t['onSurface']}">
  <div class="card" style="background:#{t['card']}">
    <div class="title">Settings Manager</div>
    {rows}
    <div class="actions">
      <span class="action" style="background:#{action_bg};color:#{action_ink}">Hide settings</span>
      <span class="action" style="background:#{action_bg};color:#{action_ink}">Revert to default</span>
    </div>
  </div>
  <div class="fabs">
    <span class="fab small" style="background:#{fab_bg};color:#{fab_ink}">&#9881;</span>
    <span class="fab" style="background:#{t['idleFab']};color:#{t['onIdleFab']}">&#128065;</span>
    <span class="cap">Favourites &middot; nothing hidden</span>
  </div>
  <div class="hex">
    action buttons <b>#{action_bg}</b><br>
    manager FAB <b>#{fab_bg}</b> &middot; switches #{t['primary']}
  </div>
</div>"""


columns = "".join(
    f"""
<section>
  <h2>{name}</h2>
  <p class="note">{note}</p>
  {panel(LIGHT, after)}
  {panel(DARK, after)}
</section>"""
    for name, note, after in (
        ("Before", "three greens: primary on the switches, primaryContainer on the two buttons, secondaryContainer on the FAB", False),
        ("After", "one green: primary on all of them", True),
    )
)

OUT.write_text(
    f"""<!doctype html>
<meta charset="utf-8">
<title>IMD r30h - the manager buttons</title>
<style>
  body {{ margin:0; padding:28px; background:#101210; color:#E6E8E3;
         font:14px/1.5 -apple-system,Segoe UI,Roboto,sans-serif; }}
  h1 {{ font-size:20px; margin:0 0 4px; }}
  .lede {{ color:#9AA096; margin:0 0 22px; max-width:80ch; }}
  .lede b {{ color:#E6E8E3; font-weight:600; }}
  .grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,380px)); gap:22px; }}
  h2 {{ font-size:15px; margin:0 0 2px; }}
  .note {{ color:#8B918A; font-size:12px; margin:0 0 10px; min-height:34px; }}
  .panel {{ border-radius:14px; padding:16px; margin-bottom:12px; }}
  .card {{ border-radius:14px; padding:14px; }}
  .title {{ font-size:13px; font-weight:700; opacity:.8; margin-bottom:8px; }}
  .cardrow {{ display:flex; justify-content:space-between; align-items:center;
              gap:12px; padding:6px 0; font-size:13px; }}
  .switch {{ position:relative; width:40px; height:24px; border-radius:12px;
             display:inline-block; flex:none; }}
  .switch i {{ position:absolute; right:4px; top:50%; transform:translateY(-50%);
               width:17px; height:17px; border-radius:50%; }}
  .actions {{ display:flex; gap:10px; margin-top:12px; }}
  .action {{ flex:1; border-radius:20px; padding:11px 12px; text-align:center;
             font-size:12px; font-weight:600; }}
  .fabs {{ display:flex; gap:12px; align-items:center; margin-top:16px; }}
  .fab {{ width:48px; height:48px; border-radius:16px; display:inline-flex;
          align-items:center; justify-content:center; font-size:20px; flex:none; }}
  .fab.small {{ width:40px; height:40px; border-radius:12px; font-size:17px; }}
  .cap {{ font-size:11px; opacity:.5; }}
  .hex {{ font:11px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;
          opacity:.62; margin-top:12px; }}
</style>
<h1>One green instead of three</h1>
<p class="lede">The switches always drew themselves in <b>primary</b>, like every other filled
button in the app. The manager's two action buttons drew themselves in
<b>primaryContainer</b> and the Favourites manager button in <b>secondaryContainer</b> &mdash;
so three greens, and after the theme change they drifted further apart. Light panel above,
dark below.</p>
<div class="grid">{columns}</div>
""",
    encoding="utf-8",
)

print(f"wrote {OUT}")
