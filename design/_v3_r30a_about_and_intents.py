#!/usr/bin/env python3
"""
r30a — the About line says Supercharged, and IMD intents drops its EXPERIMENTAL tag.

The author: *"rename in about section 'fork of geto...' to 'Supercharged fork of...'"* and
*"remove experimental tag from intents"*.

## The About line

`about_fork_of` is the first of four strings the About page lays out as
**Fork of · Geto app · by · JackEblan**, so only the first one moves: "Fork of" becomes his
"Supercharged fork of", verbatim.

⚠ **The ten translations render the sense, not the word.** "Supercharged" is a flourish that does
not carry into most of these languages as anything but a car engine, so each locale gets its own
idiom for an enhanced or built-upon fork — Portuguese *turbinado*, which does carry it; German
*Erweiterter*; Russian *Улучшенный*. The English is his and is untouched.

## The EXPERIMENTAL tag

The tag lives **inside the string**, not in a badge composable, so removing it is a string edit in
two places × eleven files:

* `tasker_integration` — the row title and the page heading
* `help_path_intents` — the navigation trail, which names the row and must keep naming it correctly

⚠ **`imd_plus_experimental` is untouched.** That is IMD+'s own badge, a separate string on a
separate feature, and the author asked about intents.

⚠ **Two historical lines are also untouched, deliberately.** `README.md` line 148 and `SUIMD.md`
line 307 both say *"Tasker / MacroDroid integration is now IMD intents (EXPERIMENTAL)"* — they are
changelog entries recording what v2.2 did at the time, and rewriting them would be falsifying a
record rather than renaming a feature. The README's own heading, which describes the feature as it
is now, does change.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS_RES = ROOT / "feature/settings/src/main/res"
README = ROOT / "README.md"

LOCALES = ["", "hi", "ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "ja", "ko", "ru"]

FORK_OF = {
    "": "Supercharged fork of",
    "hi": "उन्नत फ़ोर्क है",
    "ar": "نسخة معدَّلة ومحسَّنة من",
    "b+pt+BR": "Fork turbinado do",
    "b+zh+Hans": "强化分支自",
    "de": "Erweiterter Fork von",
    "es": "Fork mejorado de",
    "fr": "Fork amélioré de",
    "ja": "強化フォーク元",
    "ko": "강화 포크 원본:",
    "ru": "Улучшенный форк приложения",
}

# ⚠ Both bracket shapes. Japanese and Chinese use the full-width pair and put no space before it,
# so a needle written for "( ... )" finds nothing in two of the eleven files and the tag survives
# exactly where nobody would look for it.
TAG = re.compile(r"\s*[(（][^)）]*[)）]$")

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


def VALUE_for(name: str) -> re.Pattern[str]:
    return re.compile(r'(<string name="%s"[^>]*>)(.*?)(</string>)' % re.escape(name), re.S)


def edit_value(text: str, name: str, new_value: str, label: str) -> str:
    found = len(VALUE_for(name).findall(text))

    if not check(found == 1, f"{label}: {name} found {found}x, expected 1"):
        return text

    return VALUE_for(name).sub(lambda m: m.group(1) + new_value + m.group(3), text, count=1)


def current(text: str, name: str) -> str | None:
    match = VALUE_for(name).search(text)

    return match.group(2) if match else None


for locale in LOCALES:
    folder = "values" if not locale else f"values-{locale}"

    path = SETTINGS_RES / folder / "strings.xml"

    if not check(path.exists(), f"{folder}: strings.xml is missing"):
        continue

    text = path.read_text(encoding="utf-8")

    # ---------------------------------------------------------- about_fork_of

    was = current(text, "about_fork_of")

    if check(was is not None, f"{folder}: about_fork_of is missing"):
        check(
            was != FORK_OF[locale],
            f"{folder}: about_fork_of already says the new thing",
        )

        text = edit_value(text, "about_fork_of", FORK_OF[locale], folder)

    # ---------------------------------------------------------- the tag

    for name, tail in (("tasker_integration", "IMD intents"), ("help_path_intents", "IMD intents")):
        was = current(text, name)

        if not check(was is not None, f"{folder}: {name} is missing"):
            continue

        stripped = TAG.sub("", was)

        # ⚠ Asserted, not assumed: the regex removing "the last bracketed thing" would happily eat
        # a bracket that was part of the sentence. Every one of these must end in the bare feature
        # name once the tag is off, and none of the eleven translates it.
        check(
            stripped.endswith(tail),
            f"{folder}: {name} does not end in {tail!r} after the tag — got {stripped!r}",
        )

        check(
            stripped != was,
            f"{folder}: {name} had no tag to remove — {was!r}",
        )

        text = edit_value(text, name, stripped, folder)

    writes[path] = text

check(len(writes) == 11, f"strings written to {len(writes)} files, expected 11")

# ---------------------------------------------------------------- the README heading

readme = README.read_text(encoding="utf-8")

readme = replace_once(
    readme,
    "#### Tasker / MacroDroid integration (EXPERIMENTAL, secured with auth keys)\n",
    "#### IMD intents - Tasker / MacroDroid integration (secured with auth keys)\n",
    "readme: the intents heading",
)

# ⚠ The remaining occurrence is line 148, a v2.2 changelog entry. It stays: it records what that
# release did, and a record that is edited to match the present is not a record.
check(
    readme.count("EXPERIMENTAL") == 1,
    f"readme: {readme.count('EXPERIMENTAL')} EXPERIMENTAL left, expected 1 (the v2.2 entry)",
)

writes[README] = readme

# ---------------------------------------------------------------- write

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

print(f"wrote {len(writes)} files")

print("ok")
