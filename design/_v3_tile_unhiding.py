#!/usr/bin/env python3
"""
v3-r1f — the Hide settings tile's label while a revert is running.

One key, 11 locales, inserted directly after `hide_tile_working` so the four tile labels
stay together in every file.

The tile was reading "Hiding settings…" in both directions, because the only thing it knew
was that *something* was in flight. `SettingsWorkTracker.work` now names the direction, so
the unhide half gets its own label. Each translation reuses the verb that locale already
uses for unhiding in `settings_manager_busy_unhiding`, so the two never disagree.

Writes nothing unless the anchor matches exactly once in every locale, no locale already
has the key, every value survives the escaping checks, and every result still parses.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "app/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

KEY = "hide_tile_unhiding"

ANCHOR_KEY = "hide_tile_working"

# The English is the exact parallel of the label it sits beside — same shape, same U+2026
# ellipsis — with the one word that changes changed.
AUTHOR_ENGLISH = "Unhiding settings…"

VALUES = {
    "values": AUTHOR_ENGLISH,
    "values-ar": "جارٍ إعادة إظهار الإعدادات…",
    "values-b+pt+BR": "Reexibindo configurações…",
    "values-b+zh+Hans": "正在恢复设置…",
    "values-de": "Einstellungen werden wieder eingeblendet…",
    "values-es": "Restaurando ajustes…",
    "values-fr": "Réaffichage des paramètres…",
    "values-hi": "सेटिंग्स फिर से दिखाई जा रही हैं…",
    "values-ja": "設定を再表示しています…",
    "values-ko": "설정을 다시 표시하는 중…",
    "values-ru": "Восстановление настроек…",
}

# The verb each locale already uses for unhiding, from settings_manager_busy_unhiding in
# feature/apps. Asserted as a substring of the new value so the two cannot drift apart.
CONSISTENT_WITH = {
    "values": "nhiding",
    "values-ar": "إعادة إظهار",
    "values-b+pt+BR": "eexibindo",
    "values-b+zh+Hans": "恢复",
    "values-de": "wieder ein",
    "values-es": "estaurando",
    "values-fr": "éaffich",
    "values-hi": "फिर से दिखा",
    "values-ja": "再表示",
    "values-ko": "다시 표시",
    "values-ru": "осстанов",
}


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def main() -> int:
    # --- the English, asserted before anything else ------------------------------------
    if VALUES["values"] != AUTHOR_ENGLISH:
        return fail("the English value is not the intended text")

    if not AUTHOR_ENGLISH.endswith("…"):
        return fail("the English value lost its U+2026 ellipsis")

    if "..." in AUTHOR_ENGLISH:
        return fail("the English value uses three dots; the tile labels use U+2026")

    # --- coverage -----------------------------------------------------------------------
    missing = [loc for loc in LOCALES if loc not in VALUES]

    if missing:
        return fail(f"{KEY} is missing locales: {missing}")

    extra = [loc for loc in VALUES if loc not in LOCALES]

    if extra:
        return fail(f"{KEY} has unknown locales: {extra}")

    for locale, value in VALUES.items():
        if not value.endswith("…"):
            return fail(f"{KEY}/{locale}: does not end in the U+2026 ellipsis")

        if CONSISTENT_WITH[locale] not in value:
            return fail(
                f"{KEY}/{locale}: does not use this locale's own unhiding verb "
                f"{CONSISTENT_WITH[locale]!r}",
            )

    # --- escaping, collisions and the anchor ---------------------------------------------
    planned: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")

        if f'name="{KEY}"' in text:
            return fail(f"{KEY} already exists in {locale} — has this run before?")

        value = VALUES[locale]

        if "'" in value and "\\'" not in value:
            return fail(f"{KEY}/{locale}: unescaped apostrophe")

        if "&" in value and "&amp;" not in value:
            return fail(f"{KEY}/{locale}: unescaped ampersand")

        if "\n" in value:
            return fail(f"{KEY}/{locale}: a literal newline collapses to a space; use \\n")

        anchors = re.findall(
            rf'^[ \t]*<string name="{ANCHOR_KEY}">.*</string>[ \t]*\n',
            text,
            flags=re.MULTILINE,
        )

        if len(anchors) != 1:
            return fail(f"{locale}: {ANCHOR_KEY} anchor matched {len(anchors)} times, wanted 1")

        anchor = anchors[0]

        indent = anchor[: len(anchor) - len(anchor.lstrip())]

        planned[path] = text.replace(
            anchor,
            anchor + f'{indent}<string name="{KEY}">{value}</string>\n',
            1,
        )

    # --- the result must still parse, and must contain exactly one new key ----------------
    for path, text in planned.items():
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

        found = [child for child in root if child.get("name") == KEY]

        if len(found) != 1:
            return fail(f"{path.relative_to(ROOT)}: {len(found)} copies of {KEY}, wanted 1")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {KEY} x {len(LOCALES)} locale(s) = {len(LOCALES)} strings")
    print(f"  English: {AUTHOR_ENGLISH!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
