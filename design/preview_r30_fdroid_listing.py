#!/usr/bin/env python3
"""
r30 — the F-Droid listing, rendered as the page and shown as the three files.

Two views of the same thing, because the author has to approve both: the page a user lands on, and
the exact text going into `title.txt`, `short_description.txt` and `full_description.txt`.

⚠ **The rendering is F-Droid's, not a browser's.** F-Droid's client takes a small subset of HTML —
`<b> <i> <u> <br> <ul> <ol> <li> <a> <p>` — turns a blank line into a paragraph and a bare newline
into a break, and prints anything else as source. This preview does the same, so a tag that would
show up as literal text on the real page shows up as literal text here.

⚠ **The screenshot strip is every file in `phoneScreenshots/`, in filename order.** That is exactly
what F-Droid publishes — there is no way to list a subset — so the strip is the listing, not a
selection of it.

Writes a preview; changes nothing.
"""
from __future__ import annotations

import base64
import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

METADATA = ROOT / "fastlane/metadata/android/en-US"

SHOTS = METADATA / "images/phoneScreenshots"

OUT = Path("/root/work/r30_fdroid_listing.html")

LIMITS = {"title": 50, "short_description": 80, "full_description": 4000}


def read(name: str) -> str:
    return (METADATA / f"{name}.txt").read_text(encoding="utf-8").rstrip("\n")


def data_uri(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()


title, short, full = read("title"), read("short_description"), read("full_description")

# F-Droid's own rendering, reproduced: links become links, a blank line a paragraph, a newline a
# break. Everything outside the tag subset is left as the literal text it would print as.
body = re.sub(r"(https://\S+?)(?=[\s)]|$)", r'<a href="\1">\1</a>', full)

body = "<p>" + body.replace("\n\n", "</p><p>").replace("\n", "<br>") + "</p>"

strip = "".join(
    f'<figure><img src="{data_uri(path)}"><figcaption>{html.escape(path.name)}</figcaption></figure>'
    for path in sorted(SHOTS.iterdir())
)

# ⚠ **Drawn above the description, because that is where F-Droid draws it** - full width, before a
# word of the text. A near-square banner therefore fills most of a phone screen on its own, which
# is the thing the preview exists to make visible rather than to describe.
feature_path = METADATA / "images/featureGraphic.png"

if feature_path.exists():
    with __import__("PIL.Image", fromlist=["Image"]).open(feature_path) as image:
        shape = f"{image.size[0]} x {image.size[1]}, ratio {image.size[0] / image.size[1]:.2f}"

    feature = (
        f'<figure class="feature"><img src="{data_uri(feature_path)}">'
        f"<figcaption>featureGraphic.png &mdash; {shape}</figcaption></figure>"
    )
else:
    feature = ""

sources = "".join(
    f"""<div class="file">
  <div class="fname">{name}.txt <span class="{'over' if len(text) > LIMITS[name] else 'under'}">{len(text)} / {LIMITS[name]}</span></div>
  <pre>{html.escape(text)}</pre>
</div>"""
    for name, text in (("title", title), ("short_description", short), ("full_description", full))
)

OUT.write_text(
    f"""<!doctype html>
<meta charset="utf-8">
<title>IMD - F-Droid listing</title>
<style>
  body {{ margin:0; background:#0F0F0F; color:#E8E8E8;
          font:15px/1.65 Roboto,-apple-system,"Segoe UI",sans-serif; }}
  .banner {{ background:#1A1A1A; border-bottom:1px solid #2A2A2A; padding:12px 20px;
             font-size:13px; color:#9A9A9A; }}
  .banner b {{ color:#E8E8E8; }}
  .cols {{ display:grid; grid-template-columns:minmax(0,620px) minmax(0,560px);
           gap:34px; justify-content:center; padding:24px 20px 70px; align-items:start; }}
  .head {{ display:flex; gap:16px; align-items:center; }}
  .head img {{ width:72px; height:72px; border-radius:16px; flex:none; background:#fff; }}
  h1 {{ font-size:22px; margin:0 0 2px; font-weight:600; }}
  .short {{ color:#B0B0B0; font-size:14px; margin:0; }}
  .meta {{ color:#8A8A8A; font-size:12px; margin-top:3px; }}
  .strip {{ display:flex; gap:12px; overflow-x:auto; padding:20px 0 6px; }}
  figure {{ margin:0; flex:none; }}
  .strip img {{ height:310px; border-radius:10px; border:1px solid #262626; display:block; }}
  figcaption {{ font:10px/1.8 ui-monospace,Menlo,monospace; color:#6E6E6E; text-align:center; }}
  .feature {{ margin:0 0 20px; }}
  .feature img {{ width:100%; border-radius:10px; display:block; border:1px solid #262626; }}
  .feature figcaption {{ font:11px/1.8 ui-monospace,Menlo,monospace; color:#6E6E6E; }}
  .desc p {{ margin:0 0 14px; }}
  .desc b {{ font-weight:700; color:#fff; }}
  a {{ color:#7FC3F5; }}
  hr {{ border:0; border-top:1px solid #242424; margin:16px 0; }}
  h2 {{ font-size:13px; text-transform:uppercase; letter-spacing:.08em;
        color:#8A8A8A; margin:0 0 12px; font-weight:600; }}
  .file {{ background:#161616; border:1px solid #262626; border-radius:10px;
           margin-bottom:14px; overflow:hidden; }}
  .fname {{ background:#1D1D1D; padding:8px 12px; font:12px ui-monospace,Menlo,monospace;
            color:#C8C8C8; display:flex; justify-content:space-between; }}
  .under {{ color:#8FAE6E; }}
  .over {{ color:#FF8A80; font-weight:700; }}
  pre {{ margin:0; padding:12px; white-space:pre-wrap; word-break:break-word;
         font:12px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace; color:#B8B8B8; }}
</style>
<div class="banner">
  <b>Template.</b> Left is the F-Droid page as the client will render it &mdash; its HTML subset,
  its paragraph rules, and every file in <code>phoneScreenshots/</code> in filename order, which is
  what it publishes. Right is the exact text of the three files, with the character caps.
</div>
<div class="cols">
  <div>
    <div class="head">
      <img src="{data_uri(METADATA / 'images/icon.png')}">
      <div>
        <h1>{html.escape(title)}</h1>
        <p class="short">{html.escape(short)}</p>
        <div class="meta">com.soul_99.suIMD &middot; GPL-3.0 &middot; No ads, no tracking</div>
      </div>
    </div>
    <div class="strip">{strip}</div>
    <hr>
    {feature}
    <div class="desc">{body}</div>
  </div>
  <div>
    <h2>The three files</h2>
    {sources}
  </div>
</div>
""",
    encoding="utf-8",
)

print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")

for name, text in (("title", title), ("short_description", short), ("full_description", full)):
    print(f"  {name:20s} {len(text):5d} / {LIMITS[name]}")
