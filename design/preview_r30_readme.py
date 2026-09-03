#!/usr/bin/env python3
"""
r30 — README.md, rendered the way GitHub will render it.

The author: *"can you show me a template of new readme"*. Markdown in a text file is not a
template; this is the page.

## What it does

* Renders `README.md` with python-markdown, `extra` on, so the raw HTML blocks the README uses for
  its image rows come through as GitHub renders them.
* **Turns the ` ```mermaid ` block into a picture**, with the same `mmdc` that builds the fifteen
  logics diagrams, so the flowchart in the preview is the flowchart GitHub will draw rather than a
  code listing.
* **Inlines every local image as a `data:` URI**, so the file can be sent on its own and still be
  complete. The two Obtainium / GitHub badges stay as remote `https:` URLs — they are remote on
  GitHub too, and faking them would hide a broken one.
* Wraps it in GitHub's own reading width, type scale and rules.

⚠ **`<sub>` and `<u>` are the only markup GitHub honours for "muted" and "underlined".** Inline
CSS is stripped from a README, so what is in the file is what can be had — this preview must show
that honestly rather than styling it with CSS the real page will not have.

Writes a preview; changes nothing in the repo.
"""
from __future__ import annotations

import base64
import mimetypes
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]

README = ROOT / "README.md"
OUT = Path("/root/work/r30_readme_preview.html")

CHROMIUM = "/opt/pw-browsers/chromium"

text = README.read_text(encoding="utf-8")

# ---------------------------------------------------------------- the flowchart

blocks = re.findall(r"```mermaid\n(.*?)\n```", text, re.S)

if len(blocks) != 1:
    print(f"expected 1 mermaid block, found {len(blocks)}")

    sys.exit(1)

with tempfile.TemporaryDirectory() as work:
    source = Path(work) / "flow.mmd"

    picture = Path(work) / "flow.png"

    source.write_text(blocks[0], encoding="utf-8")

    puppeteer = Path(work) / "puppeteer.json"

    puppeteer.write_text(
        '{"executablePath": "%s", "args": ["--no-sandbox"]}' % CHROMIUM,
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "mmdc",
            "-i", str(source),
            "-o", str(picture),
            "-b", "transparent",
            "-t", "neutral",
            "-w", "1100",
            "-p", str(puppeteer),
        ],
        capture_output=True,
        text=True,
    )

    if not picture.exists():
        print("mmdc failed:")

        print(result.stdout[-2000:])

        print(result.stderr[-2000:])

        sys.exit(1)

    flow = base64.b64encode(picture.read_bytes()).decode()

text = re.sub(
    r"```mermaid\n.*?\n```",
    f'<p><img src="data:image/png;base64,{flow}" width="760" alt="How this works"></p>',
    text,
    count=1,
    flags=re.S,
)

# ---------------------------------------------------------------- render

# ⚠ **No `nl2br`.** GitHub renders a `.md` file as CommonMark, where a single newline inside a
# paragraph joins rather than breaking. Turning breaks on here would make the preview kinder than
# the page, which is the one thing a template must not be.
body = markdown.markdown(text, extensions=["extra", "sane_lists"])

# ---------------------------------------------------------------- inline the pictures

missing: list[str] = []


def embed(match: re.Match[str]) -> str:
    reference = match.group(1)

    if reference.startswith(("http", "data:")):
        return match.group(0)

    path = ROOT / reference

    if not path.exists():
        missing.append(reference)

        return match.group(0)

    kind = mimetypes.guess_type(path.name)[0] or "image/png"

    return 'src="data:%s;base64,%s"' % (kind, base64.b64encode(path.read_bytes()).decode())


body = re.sub(r'src="([^"]+)"', embed, body)

if missing:
    print("NOT WRITTEN — these images are referenced and do not exist:")

    for reference in missing:
        print(f"  - {reference}")

    sys.exit(1)

OUT.write_text(
    """<!doctype html>
<meta charset="utf-8">
<title>IMD README - r30 template</title>
<style>
  body { margin:0; background:#0D1117; color:#E6EDF3;
         font:16px/1.6 -apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif; }
  .banner { background:#1C2128; border-bottom:1px solid #30363D; padding:12px 24px;
            font-size:13px; color:#8B949E; }
  .banner b { color:#E6EDF3; }
  main { max-width:1012px; margin:0 auto; padding:32px 32px 80px; }
  h1 { font-size:2em; font-weight:600; padding-bottom:.3em;
       border-bottom:1px solid #30363D; margin:.67em 0 16px; }
  h1:first-child { margin-top:0; }
  h2 { font-size:1.5em; font-weight:600; padding-bottom:.3em;
       border-bottom:1px solid #30363D; margin:24px 0 16px; }
  h3 { font-size:1.25em; font-weight:600; margin:24px 0 16px; }
  h4 { font-size:1em; font-weight:600; margin:24px 0 16px; }
  p, ul, ol { margin:0 0 16px; }
  ul, ol { padding-left:2em; }
  li { margin:.25em 0; }
  sub { color:#8B949E; font-size:.85em; }
  a { color:#4493F8; text-decoration:none; }
  a:hover { text-decoration:underline; }
  code { background:#6E76811A; border-radius:6px; padding:.2em .4em; font-size:85%;
         font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
  pre { background:#161B22; border-radius:6px; padding:16px; overflow:auto; }
  pre code { background:none; padding:0; font-size:85%; }
  img { max-width:100%; vertical-align:top; }
  hr { border:0; border-top:1px solid #30363D; margin:24px 0; }
  em { font-style:italic; }
  strong { font-weight:600; }
  /* GitHub's own dark-mode <mark>: --bgColor-attention-muted over the page's text colour.
     It is the one tag on GitHub's allow-list that gives a solid background and leaves the
     text in the page font - inline CSS is stripped from a README, so this is the whole
     vocabulary available. */
  mark { background:#BB80093D; color:#E6EDF3; padding:.14em .3em; border-radius:4px; }
</style>
<div class="banner">
  <b>Template.</b> This is <code>README.md</code> rendered the way GitHub will render it.
  The poster and the three Automations screenshots are the current ones standing in for the new
  ones &mdash; each slot is marked with a <code>&lt;!-- TODO r30: --&gt;</code> comment in the file.
</div>
<main>
"""
    + body
    + "\n</main>\n",
    encoding="utf-8",
)

print(f"wrote {OUT} ({OUT.stat().st_size / 1024:.0f} KB)")

print("ok")
