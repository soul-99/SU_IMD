#!/usr/bin/env python3
"""
r29a — the closing setup page's fourth point becomes four sub-points, and the strings that are
never going to be translated say so.

## The setup page

The author, on the "Setup is now almost complete" page: *"in the setup is now almost complete page
point 4. the setup is now complete but.... change the points under that to"* — and then four lines,
where there were three. His words, verbatim, numbering included:

    1. Auto unhide settings (RECOMMENDED)
    2. Auto hide settings (IMD+, needs background service)
    3. All other settings for deeper customisation
    4. IMD intents (Tasker / Macrodroid...etc integration)

The order is the change, not just the wording: the two automations now lead and "all other
settings" has dropped to third. `setup_done_4_4` is new, so `SetupCompletePage` grows a fourth
`SubPoint` beside it.

## translatable="false"

⚠ **The six Shizuku/Shevery step lines are one bold-coupled group with ON and OFF.**
`ShizukuSetupBody` bolds `shizuku_setup_on` / `shizuku_setup_off` as a *substring* of each step
line — `thedjchi_setup_1 to R.string.shizuku_setup_off`, and so on. Translate a step line without
translating the word, or the word without the line, and the bold silently stops appearing. The
author's answer was to leave all six English: the reader is looking at Shizuku's own English-only
settings screen while they follow them, so the words on the page and the words on their screen
match, and the coupling never has to be maintained across ten locales.

`support_view_github_button` joins them for a different reason: *"view Project on GitHub"* is his
deliberate lowercase-view, capital-Project, and he asked for it left alone.

## support_point_star_link

Deleted, English and all ten locales. r27 replaced the inline link with a button under the point;
the comment in the English file says it was kept to avoid orphaning eight translations. Those
translations are being written this round, so the reason has expired and the string has no Kotlin
reference at all.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP_STRINGS = ROOT / "app/src/main/res/values/strings.xml"
SETTINGS_STRINGS = ROOT / "feature/settings/src/main/res/values/strings.xml"
SETUP_PAGE = ROOT / "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

LOCALES = ["hi", "ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "ja", "ko", "ru"]

# The six step lines plus the two words they bold, and the button the author asked to leave alone.
UNTRANSLATABLE = [
    "shizuku_setup_on",
    "shizuku_setup_off",
    "thedjchi_setup_1",
    "thedjchi_setup_2",
    "thedjchi_setup_3",
    "shevery_setup_1",
    "shevery_setup_2",
    "shevery_setup_3",
    "support_view_github_button",
]

failures: list[str] = []
writes: dict[Path, str] = {}


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


# ---------------------------------------------------------------- the four sub-points

app = APP_STRINGS.read_text(encoding="utf-8")

app = replace_once(
    app,
    '    <string name="setup_done_4_1">1. All other IMD app settings</string>\n'
    '    <string name="setup_done_4_2">2. IMD+ (auto hide settings on normal app launches, needs background service)</string>\n'
    '    <string name="setup_done_4_3">3. IMD intents (Tasker integration)</string>\n',
    '    <string name="setup_done_4_1">1. Auto unhide settings (RECOMMENDED)</string>\n'
    '    <string name="setup_done_4_2">2. Auto hide settings (IMD+, needs background service)</string>\n'
    '    <string name="setup_done_4_3">3. All other settings for deeper customisation</string>\n'
    '    <string name="setup_done_4_4">4. IMD intents (Tasker / Macrodroid...etc integration)</string>\n',
    "app strings: the three sub-points under setup_done_4",
)

writes[APP_STRINGS] = app

# ⚠ The needles below are checked against the *new* text, after the edit that created them —
# asserting a string is present before the edit that writes it is the trap section 8 of the
# handover calls "my own new code".
for name, want in (
    ("setup_done_4_1", "1. Auto unhide settings (RECOMMENDED)"),
    ("setup_done_4_2", "2. Auto hide settings (IMD+, needs background service)"),
    ("setup_done_4_3", "3. All other settings for deeper customisation"),
    ("setup_done_4_4", "4. IMD intents (Tasker / Macrodroid...etc integration)"),
):
    check(
        app.count(f'<string name="{name}">{want}</string>') == 1,
        f"app strings: {name} is not his line, verbatim",
    )

check(
    "IMD+ (auto hide settings on normal app launches" not in app,
    "app strings: the old point 2 survived",
)

check(
    "1. All other IMD app settings" not in app,
    "app strings: the old point 1 survived",
)

# ---------------------------------------------------------------- the fourth SubPoint

setup = SETUP_PAGE.read_text(encoding="utf-8")

setup = replace_once(
    setup,
    "            SubPoint(text = stringResource(R.string.setup_done_4_3))\n",
    "            SubPoint(text = stringResource(R.string.setup_done_4_3))\n"
    "\n"
    "            SubPoint(text = stringResource(R.string.setup_done_4_4))\n",
    "setup page: the third sub-point of point 4",
)

writes[SETUP_PAGE] = setup

for n in (1, 2, 3, 4):
    check(
        setup.count(f"R.string.setup_done_4_{n}") == 1,
        f"setup page: setup_done_4_{n} is not drawn exactly once",
    )

# ---------------------------------------------------------------- translatable="false"

settings = SETTINGS_STRINGS.read_text(encoding="utf-8")

for name in UNTRANSLATABLE:
    pattern = f'<string name="{name}">'

    if not check(
        settings.count(pattern) == 1,
        f"settings strings: {name} not found exactly once (already marked?)",
    ):
        continue

    settings = settings.replace(
        pattern,
        f'<string name="{name}" translatable="false">',
        1,
    )

for name in UNTRANSLATABLE:
    check(
        settings.count(f'<string name="{name}" translatable="false">') == 1,
        f"settings strings: {name} did not get its translatable=false",
    )

# ---------------------------------------------------------------- support_point_star_link

STAR_LINK = re.compile(r'[ \t]*<string name="support_point_star_link">.*?</string>\n', re.S)

found = len(STAR_LINK.findall(settings))

if check(found == 1, f"settings strings: support_point_star_link found {found}x in English"):
    settings = STAR_LINK.sub("", settings, count=1)

# The comment above the block explains why the string was being kept. It is going with it.
settings = replace_once(
    settings,
    "      support_point_star_link is no longer used: r27 replaced the inline link with a button under\n"
    "      the point, matching the Share button under point 1. It is kept rather than deleted because\n"
    "      removing it would orphan the phrase in eight translation files. -->\n",
    "      r29 deleted support_point_star_link: r27 had already replaced the inline link with a button\n"
    "      under the point, and the only reason it was kept - not orphaning the translations - expired\n"
    "      when this round translated the rest. -->\n",
    "settings strings: the support_point_star_link comment",
)

check(
    "support_point_star_link\">" not in settings,
    "settings strings: the English support_point_star_link survived",
)

writes[SETTINGS_STRINGS] = settings

for locale in LOCALES:
    path = ROOT / f"feature/settings/src/main/res/values-{locale}/strings.xml"

    if not check(path.exists(), f"{locale}: strings.xml is missing"):
        continue

    text = path.read_text(encoding="utf-8")

    found = len(STAR_LINK.findall(text))

    if not check(found == 1, f"{locale}: support_point_star_link found {found}x, expected 1"):
        continue

    text = STAR_LINK.sub("", text, count=1)

    check(
        '<string name="support_point_star_link">' not in text,
        f"{locale}: support_point_star_link survived the delete",
    )

    writes[path] = text

# ⚠ Counted over the eleven files by name, not by sniffing the buffers. "does this text still
# contain the needle" is true of every file that never had it — including this script's other two
# edits — which is the handout's comment trap wearing a different coat.
star_link_files = [SETTINGS_STRINGS] + [
    ROOT / f"feature/settings/src/main/res/values-{locale}/strings.xml" for locale in LOCALES
]

check(len(star_link_files) == 11, "support_point_star_link: expected 11 files to clear")

for path in star_link_files:
    if check(path in writes, f"support_point_star_link: {path.name} was never staged"):
        # ⚠ The *element*, not the name. The English file's comment above the block still
        # says why the string went, so a bare name search finds the explanation and calls it a
        # survivor - the import-line trap, one file over.
        check(
            '<string name="support_point_star_link">' not in writes[path],
            f"support_point_star_link: survived in {path.parent.name}",
        )

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
