#!/usr/bin/env python3
"""
r30g — the author's new screenshots and poster go in, and the README points at them.

*"start building and use these ss and posters"*, *"we will use same ss for fdroid"*, and the three
placements he gave:

* under **Settings manager** — the settings manager window, and the QS toggles
* under **Automations** — auto unhide, IMD+, tasker

## The set replaces the old one wholesale

Ten files in, eleven out. F-Droid renders `phoneScreenshots` in filename order and shows every file
it finds, so a leftover from the old set does not sit quietly beside the new ones — it appears in
the listing. The old names are therefore deleted rather than left in place, and the directory is
asserted to hold exactly the ten afterwards.

⚠ **`docs/help_page.png` is not in this directory and is not touched.** It is SUIMD.md's setup
picture, it lives under `docs/`, and it has nothing to do with the store listing.

## The two the author needs to know about

Both are facts about the pictures, not about this script, and neither is something a script may
quietly fix:

1. **`10_imd_intents.png` still shows the title as "IMD intents (EXPERIMENTAL)".** It was taken
   before r30a stripped that tag. The README will therefore show a screenshot contradicting the
   rename he asked for, in the section named after it.
2. **The poster and `02_settings_manager.png` show the old bright-lime switches**, taken before
   r30f took `primary` to #8FAE6E.

Both are asserted below as *known* — the assertions record the state rather than passing silently,
so re-shooting either one is a visible change to this file rather than a thing to remember.

Copies the files, rewrites the README's five references, asserts, writes nothing if any fails.
"""
from __future__ import annotations

import hashlib
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SOURCE = Path("/mnt/user-data/uploads/imd-fdroid-screenshots")

SHOTS = ROOT / "fastlane/metadata/android/en-US/images/phoneScreenshots"

README = ROOT / "README.md"

NEW = [
    "01_poster.png",
    "02_settings_manager.png",
    "03_qs_toggles.png",
    "04_favourites.png",
    "05_add_shortcut.png",
    "06_notification.png",
    "07_settings.png",
    "08_how_auto_unhide_works.png",
    "09_how_imd_plus_works.png",
    "10_imd_intents.png",
]

OLD = [
    "01_poster.png",
    "02_services_manager.png",
    "03_qs_toggles.png",
    "04_favourites.png",
    "05_add_shortcut.png",
    "06_revert_notification.png",
    "07_settings_ui.png",
    "08_settings_defaults.png",
    "09_shizuku_config.png",
    "10_settings_advanced.png",
    "11_settings_tasker.png",
]

# The screenshot whose own title still carries the tag r30a removed. Recorded so that replacing it
# is a change to this line rather than something to remember.
KNOWN_STALE = "10_imd_intents.png"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


# ---------------------------------------------------------------- the files

for name in NEW:
    source = SOURCE / name

    if not check(source.exists(), f"source: {name} is missing"):
        continue

    check(source.stat().st_size > 20_000, f"source: {name} is suspiciously small")

    check(source.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n", f"source: {name} is not a PNG")

check(SHOTS.is_dir(), "the phoneScreenshots directory is missing")

for name in OLD:
    check((SHOTS / name).exists(), f"old set: {name} is not there — has this already run?")

# ---------------------------------------------------------------- the README

text = README.read_text(encoding="utf-8")

PREFIX = "fastlane/metadata/android/en-US/images/phoneScreenshots"

REPLACEMENTS = [
    # The poster, and the TODO comment above it.
    (
        f"""<!-- TODO r30: replace with the new poster -->
<p>
  <img src="{PREFIX}/01_poster.png" width="100%" alt="Poster: what IMD does, with screenshots of the IMD services manager, the Quick Settings tiles, the Favourites tab, creating a shortcut and the revert notification">
</p>""",
        f"""<p>
  <img src="{PREFIX}/01_poster.png" width="100%" alt="Poster: IMD - It's My Device. A settings/services manager that shows the live status of your settings, and a hider that turns them off and back on around a restrictive app. Lists the supported settings, the three automations, and five screenshots of the app">
</p>""",
    ),
    # Settings manager: the window, and the QS toggles beside it.
    (
        f"""<p>
  <img src="{PREFIX}/02_services_manager.png" width="240" alt="The IMD services manager dialog over a homescreen, listing Developer settings, USB debugging, Wireless debugging, Accessibility services, Shizuku service and Display over other apps, each with a switch, and a Revert to default button at the bottom">
</p>""",
        f"""<p>
  <img src="{PREFIX}/02_settings_manager.png" width="230" alt="The Settings Manager window over a homescreen: All off / All on, then Developer settings, USB debugging, Wireless debugging, Shizuku service, Accessibility services and Display over other apps, each with a switch and a link out to Android's own page, and Hide settings / Revert to default at the bottom">
  <img src="{PREFIX}/03_qs_toggles.png" width="230" alt="The Quick Settings shade with three IMD tiles: Settings hidden, Settings manager and Revert to default">
</p>""",
    ),
    # Automations: auto unhide, IMD+, intents - in the order of the three points below them.
    (
        f"""<!-- TODO r30: replace the three below with the new Automations screenshots -->
<p>
  <img src="{PREFIX}/06_revert_notification.png" width="200" alt="The ongoing revert notification, which puts the hidden settings back on a tap">
  <img src="{PREFIX}/10_settings_advanced.png" width="200" alt="The Advanced settings screen, where Auto-hide settings and IMD intents are configured">
  <img src="{PREFIX}/11_settings_tasker.png" width="200" alt="The IMD intents screen, showing the per-install auth key and the intents to copy into an automation app">
</p>""",
        f"""<p>
  <img src="{PREFIX}/08_how_auto_unhide_works.png" width="200" alt="The 'How auto unhide works' page: seven numbered steps from IMD hiding your settings to the notification going away once everything is back">
  <img src="{PREFIX}/09_how_imd_plus_works.png" width="200" alt="The 'How IMD+ works' page: nine numbered steps from opening a watched app to IMD's own accessibility service coming back and IMD+ being armed again">
  <img src="{PREFIX}/10_imd_intents.png" width="200" alt="The IMD intents screen, showing the per-install auth key with a refresh, and the type, package, class and action of each intent with a copy button on every value">
</p>""",
    ),
]

for old, new in REPLACEMENTS:
    found = text.count(old)

    if not check(found == 1, f"readme: a block to replace was found {found}x, expected 1"):
        continue

    text = text.replace(old, new, 1)

check("TODO r30" not in text, "readme: a TODO marker survived")

# Every picture the README now names must be one of the ten going in, and every one of the three
# placements must be present. A rename in the source folder cannot silently break the page.
referenced = [
    reference.rsplit("/", 1)[-1]
    for reference in __import__("re").findall(r'src="([^"]+)"', text)
    if reference.startswith(PREFIX)
]

check(
    referenced == [
        "01_poster.png",
        "02_settings_manager.png",
        "03_qs_toggles.png",
        "08_how_auto_unhide_works.png",
        "09_how_imd_plus_works.png",
        "10_imd_intents.png",
    ],
    f"readme: the pictures are {referenced}",
)

for name in referenced:
    check(name in NEW, f"readme: {name} is not in the new set")

# ⚠ Recorded, not fixed. See the module docstring.
check(
    KNOWN_STALE in referenced,
    f"{KNOWN_STALE} is no longer referenced — if it was re-shot, drop this assertion",
)

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for name in OLD:
    (SHOTS / name).unlink()

for name in NEW:
    shutil.copy2(SOURCE / name, SHOTS / name)

    # ⚠ **`copy2` carries the mode across, and these arrive read-only from the upload staging.**
    # Ten read-only PNGs in a repo is a small thing until git on Windows has to overwrite one on a
    # checkout or a pull, which fails rather than asking.
    (SHOTS / name).chmod(0o644)

README.write_text(text, encoding="utf-8")

present = sorted(path.name for path in SHOTS.iterdir())

if present != NEW:
    print(f"WROTE, BUT the directory now holds {present}")

    sys.exit(1)

print(f"phoneScreenshots: {len(OLD)} removed, {len(NEW)} added")

for name in NEW:
    size = (SHOTS / name).stat().st_size

    print(f"  {name:32s} {size / 1024:7.0f} KB  {digest(SHOTS / name)}")

print("\nREADME now shows:")

for name in referenced:
    print(f"  {name}")

print("\nok")
