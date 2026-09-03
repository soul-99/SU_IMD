#!/usr/bin/env python3
"""Build the (SU) IMD F-Droid poster.

Reads the five app screenshots ``02``-``06`` from

    fastlane/metadata/android/en-US/images/phoneScreenshots/

and writes ``01_poster.png`` back into the same folder.  That folder is the
single source of truth for the F-Droid listing, the README and this poster --
there is no ``docs/screenshots``.

The poster is laid out as HTML and rendered with headless chromium through
Playwright at ``deviceScaleFactor=2``, so the CSS canvas is 1200 px wide and
the PNG comes out 2400 px wide -- the same width as the poster it replaces.

Requirements
------------
    pip install playwright && playwright install chromium
    (in the Anthropic sandbox chromium is pre-installed at
     PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers -- do NOT run `playwright install`)

Fonts
-----
The body face is Arial/Helvetica (``Liberation Sans`` on Linux), matching the
poster this one is based on.  Nothing here depends on a webfont.

Usage
-----
    python3 tools/poster/build_poster.py [--out PATH] [--html PATH]
"""

from __future__ import annotations

import argparse
import base64
import mimetypes
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SHOTS = REPO / "fastlane/metadata/android/en-US/images/phoneScreenshots"
ICON = REPO / "design/ic_launcher.svg"

# The five screenshots, in the order the author fixed them (F-Droid shows them
# in filename order, and the poster shows the same five in the same order).
SCREENSHOTS = [
    "02_settings_manager.png",
    "03_qs_toggles.png",
    "04_favourites.png",
    "05_add_shortcut.png",
    "06_notification.png",
]

# ---------------------------------------------------------------------------
# Palette.  The greens are the *app logo's* own greens, taken from
# design/ic_launcher.svg -- not the Material primary the app's UI uses.
# ---------------------------------------------------------------------------
BG = "#12140E"          # poster ground (app surface)
SURFACE = "#171A12"     # features panel fill
INK = "#EFF0E6"         # headline white
BODY = "#E2E3D8"        # body text
MUTED = "#9AA08E"       # de-emphasised parentheticals
FAINT = "#8A907E"       # footer fine print
GREEN = "#13A75B"       # ic_launcher.svg KEY green -- the poster's accent
GREEN_SOFT = "#A5DBB9"  # ic_launcher.svg gear green -- reference only
RED = "#FF6B6B"         # the one red on the poster: "auth key"

# ---------------------------------------------------------------------------
# Copy.  Every string below is the author's, verbatim -- spacing, punctuation
# and capitalisation included.  Do not "correct" them.
# ---------------------------------------------------------------------------
TITLE = "IMD - It's My Device"
TAGLINE = "Shut up! It's my device"

LEAD_1 = ('IMD is a powerful <b class="hl">settings/ services manager</b> which shows live '
          "status of your settings with ability to open anywhere and toggle them on-off "
          "quickly.")
LEAD_2 = ('It can <b class="hl">hide settings from restrictive apps (banking, '
          "payments...etc)</b> by automating them to turn on-off with app launches.")
SECURITY_LABEL = "Security Concerns:"
SECURITY = ("This app never tampers with the app you are opening, it simply automates "
            "turning the problematic settings OFF &rarr; ON.")

TAGS = [
    "Free &amp; open source (FOSS)",
    "No root",
    "No internet access",
    "No ads/trackers",
    "Small app size",
    "Android 7+",
    "No unnecessary background process",
    "Near zero battery / system resources usage",
    "Material design 3 expressive",
    "Optimised for foldables/ tablets",
]

SUPPORTED = [
    "Developer settings",
    "ADB - Debugging",
    "Accessibility services",
    'Display over other apps <span class="g">(needs active Shizuku service)</span>',
    "Shizuku service",
    '+many more <span class="m">(per app configuration - hiding framework)</span>',
]

MANAGER_BODY = ("View live settings and services status anywhere and quickly toggle them "
                "on-off.")

AUTOMATIONS = [
    "Auto unhide settings",
    "Auto hide settings <span class=\"g\">(IMD+)</span>",
    'IMD Intents <span class="m">(Tasker / Macrodroid integration secured via '
    '<span class="r">auth key</span>)</span>',
]

REPO_URL = "github.com/soul-99/SU_IMD"
FORK_LINE = ('Supercharged fork of <b>Geto</b> by <b>Jack Eblan</b>, licensed GPL-3.0')
CREDIT = ("Poster &amp; app screenshots &copy; 2026 soul_99 &mdash; the developer's own work, "
          "licensed CC BY-SA 4.0.")


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def build_html(shots: list[Path], icon_svg: str) -> str:
    chips = "\n".join(f'<span class="chip">{t}</span>' for t in TAGS)
    supported = "\n".join(f"<li>{t}</li>" for t in SUPPORTED)
    automations = "\n".join(f"<li>{t}</li>" for t in AUTOMATIONS)
    frames = "\n".join(
        f'<div class="shot"><img src="{data_uri(p)}" alt=""></div>' for p in shots
    )

    return f"""<!doctype html>
<meta charset="utf-8">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body {{ background:{BG}; }}
  body {{
    width:1200px;
    font-family:"Liberation Sans", Arial, Helvetica, sans-serif;
    color:{BODY};
    -webkit-font-smoothing:antialiased;
  }}
  .poster {{ padding:32px 38px 26px; }}

  /* ---- top half ------------------------------------------------------ */
  .top {{ display:flex; align-items:stretch; gap:32px; }}
  .left {{ flex:1 1 auto; display:flex; flex-direction:column; min-width:0; }}

  .brand {{ display:flex; align-items:center; gap:18px; }}
  .brand .icon {{ width:68px; height:68px; border-radius:15px; overflow:hidden;
                  flex:0 0 68px; background:#fff; }}
  .brand .icon svg {{ display:block; width:100%; height:100%; }}
  h1 {{ font-size:44px; line-height:1.06; font-weight:700; color:{INK};
        letter-spacing:-0.6px; }}
  .tagline {{ font-size:17px; font-weight:700; color:{GREEN}; margin-top:5px; }}

  .lead {{ font-size:18.5px; line-height:1.62; color:{INK}; margin-top:20px; }}
  .lead b {{ color:{INK}; }}
  /* the two phrases the author wants on a solid, soft-cornered block */
  .lead b.hl {{
    background:{GREEN}; color:{BG}; padding:2px 9px; border-radius:8px;
    -webkit-box-decoration-break:clone; box-decoration-break:clone;
  }}
  .plus {{ font-size:24px; font-weight:700; color:{GREEN}; margin:8px 0 -10px;
           line-height:1; }}
  .sec {{ font-size:15.5px; line-height:1.42; font-weight:700; color:{BODY};
          margin-top:20px; }}
  .sec u {{ text-decoration:underline; text-underline-offset:3px; }}

  /* ---- tag chips (no backing block -- they sit on the poster ground) --- */
  .tagbar {{
    margin:26px 0 0; display:flex; flex-wrap:wrap; gap:9px;
    align-self:flex-start;
  }}
  .chip {{
    background:{GREEN}; color:{BG}; font-size:13px; font-weight:700;
    padding:9px 15px; border-radius:8px; white-space:nowrap;
  }}

  /* ---- features panel ------------------------------------------------ */
  .features {{
    position:relative; flex:0 0 440px; background:{SURFACE};
    border:1.5px solid rgba(19,167,91,.55); border-radius:16px;
    padding:30px 26px 26px;
  }}
  .features .legend {{
    position:absolute; top:-11px; left:22px; background:{BG}; padding:0 11px;
    font-size:15px; font-weight:700; letter-spacing:2.4px; color:{GREEN};
  }}
  .features h2 {{
    font-size:17px; font-weight:700; color:{INK}; text-decoration:underline;
    text-underline-offset:3px; margin-bottom:11px;
  }}
  .features h2 + p, .features h2 + ol, .features h2 + ul {{ margin-top:0; }}
  .features section + section {{ margin-top:22px; }}
  .features ol {{ padding-left:24px; }}
  .features ul {{ padding-left:20px; list-style:disc; }}
  .features li {{ font-size:15.5px; line-height:1.5; margin-bottom:4px; }}
  .features li ul {{ margin-top:5px; padding-left:19px; }}
  .features li ul li {{ font-size:15px; margin-bottom:3px; }}
  .features p {{ font-size:15.5px; line-height:1.5; }}
  .g {{ color:{GREEN}; font-weight:700; }}
  .m {{ color:{MUTED}; }}
  .r {{ color:{RED}; font-weight:700; }}

  /* ---- screenshot strip ---------------------------------------------- */
  .shots {{ display:flex; gap:11px; margin:28px -27px 0; }}
  .shot {{ flex:1 1 0; border-radius:6px; overflow:hidden; line-height:0; }}
  .shot img {{ width:100%; display:block; }}

  /* ---- footer --------------------------------------------------------- */
  hr {{ border:0; border-top:1px solid rgba(239,240,230,.14); margin:26px 0 0; }}
  .foot {{ display:flex; justify-content:space-between; align-items:baseline;
           gap:24px; margin-top:20px; font-size:17px; }}
  .foot .url {{ color:{GREEN}; font-weight:700; }}
  .foot .fork {{ color:{BODY}; }}
  .foot .fork b {{ color:{INK}; }}
  .credit {{ margin-top:16px; font-size:12.5px; color:{FAINT}; }}
</style>
<div class="poster">
  <div class="top">
    <div class="left">
      <div class="brand">
        <div class="icon">{icon_svg}</div>
        <div>
          <h1>{TITLE}</h1>
          <div class="tagline">{TAGLINE}</div>
        </div>
      </div>

      <p class="lead">{LEAD_1}</p>
      <p class="plus">+</p>
      <p class="lead">{LEAD_2}</p>
      <p class="sec"><u>{SECURITY_LABEL}</u> {SECURITY}</p>

      <div class="tagbar">
{chips}
      </div>
    </div>

    <div class="features">
      <span class="legend">FEATURES</span>
      <section>
        <h2>Supported settings / services:</h2>
        <ol>
{supported}
        </ol>
      </section>
      <section>
        <h2>Settings Manager:</h2>
        <p>{MANAGER_BODY}</p>
      </section>
      <section>
        <h2>Automations:</h2>
        <ul>
{automations}
        </ul>
      </section>
    </div>
  </div>

  <div class="shots">
{frames}
  </div>

  <hr>
  <div class="foot">
    <span class="url">{REPO_URL}</span>
    <span class="fork">{FORK_LINE}</span>
  </div>
  <div class="credit">{CREDIT}</div>
</div>
"""


def render(html: str, out: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1200},
                                device_scale_factor=2)
        page.set_content(html, wait_until="load")
        page.wait_for_timeout(300)
        page.locator(".poster").screenshot(path=str(out))
        browser.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=SHOTS / "01_poster.png")
    ap.add_argument("--html", type=Path, default=None,
                    help="also write the intermediate HTML here (debugging)")
    args = ap.parse_args()

    missing = [n for n in SCREENSHOTS if not (SHOTS / n).is_file()]
    if missing:
        print(f"missing screenshots in {SHOTS}: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not ICON.is_file():
        print(f"missing app icon: {ICON}", file=sys.stderr)
        return 1

    icon_svg = ICON.read_text(encoding="utf-8")
    html = build_html([SHOTS / n for n in SCREENSHOTS], icon_svg)
    if args.html:
        args.html.write_text(html, encoding="utf-8")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    render(html, args.out)

    from PIL import Image
    with Image.open(args.out) as im:
        print(f"wrote {args.out}  {im.width}x{im.height}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
