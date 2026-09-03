#!/usr/bin/env python3
"""
v3-r1 — the settings manager's "please wait" note.

Two keys, 11 locales. The English is the author's, verbatim, and is asserted against their
exact text before anything is written — including the ellipsis being three full stops rather
than a U+2026, and the lower-case 'settings'.

Writes nothing unless every key has every locale and every value survives the escaping
checks.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "feature/apps/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# The author's words. Do not tidy: lower-case 'settings', three dots, trailing comma-free.
AUTHOR_HIDING = "IMD hiding settings, please wait..."
AUTHOR_UNHIDING = "IMD unhiding settings, please wait..."

ADD = {
    "settings_manager_busy_hiding": {
        "values": AUTHOR_HIDING,
        "values-ar": "‏IMD يخفي الإعدادات، يرجى الانتظار...",
        "values-b+pt+BR": "IMD ocultando configurações, aguarde...",
        "values-b+zh+Hans": "IMD 正在隐藏设置，请稍候...",
        "values-de": "IMD blendet Einstellungen aus, bitte warten...",
        "values-es": "IMD ocultando ajustes, espera...",
        "values-fr": "IMD masque les paramètres, veuillez patienter...",
        "values-hi": "IMD सेटिंग्स छिपा रहा है, कृपया प्रतीक्षा करें...",
        "values-ja": "IMD が設定を非表示にしています。お待ちください...",
        "values-ko": "IMD가 설정을 숨기는 중입니다. 잠시만 기다려 주세요...",
        "values-ru": "IMD скрывает настройки, подождите...",
    },
    "settings_manager_busy_unhiding": {
        "values": AUTHOR_UNHIDING,
        "values-ar": "‏IMD يعيد إظهار الإعدادات، يرجى الانتظار...",
        "values-b+pt+BR": "IMD reexibindo configurações, aguarde...",
        "values-b+zh+Hans": "IMD 正在恢复设置，请稍候...",
        "values-de": "IMD blendet Einstellungen wieder ein, bitte warten...",
        "values-es": "IMD restaurando ajustes, espera...",
        "values-fr": "IMD réaffiche les paramètres, veuillez patienter...",
        "values-hi": "IMD सेटिंग्स फिर से दिखा रहा है, कृपया प्रतीक्षा करें...",
        "values-ja": "IMD が設定を再表示しています。お待ちください...",
        "values-ko": "IMD가 설정을 다시 표시하는 중입니다. 잠시만 기다려 주세요...",
        "values-ru": "IMD восстанавливает настройки, подождите...",
    },
}


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def main() -> int:
    # --- the author's strings, asserted before anything else -------------------------
    if ADD["settings_manager_busy_hiding"]["values"] != AUTHOR_HIDING:
        return fail("the English hiding string is not the author's text")

    if ADD["settings_manager_busy_unhiding"]["values"] != AUTHOR_UNHIDING:
        return fail("the English unhiding string is not the author's text")

    for key, value in (("hiding", AUTHOR_HIDING), ("unhiding", AUTHOR_UNHIDING)):
        if "…" in value:
            return fail(f"the {key} string uses a U+2026 ellipsis; the author typed three dots")

        if not value.endswith("..."):
            return fail(f"the {key} string lost its trailing three dots")

    # --- coverage ---------------------------------------------------------------------
    for key, values in ADD.items():
        missing = [loc for loc in LOCALES if loc not in values]

        if missing:
            return fail(f"{key} is missing locales: {missing}")

        extra = [loc for loc in values if loc not in LOCALES]

        if extra:
            return fail(f"{key} has unknown locales: {extra}")

    # --- escaping and collisions ------------------------------------------------------
    planned: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")

        for key in ADD:
            if f'name="{key}"' in text:
                return fail(f"{key} already exists in {locale} — has this run before?")

        block = ""

        for key, values in ADD.items():
            value = values[locale]

            if "'" in value and "\\'" not in value:
                return fail(f"{key}/{locale}: unescaped apostrophe")

            if "&" in value and "&amp;" not in value:
                return fail(f"{key}/{locale}: unescaped ampersand")

            if "\n" in value:
                return fail(f"{key}/{locale}: a literal newline collapses to a space; use \\n")

            block += f'    <string name="{key}">{value}</string>\n'

        marker = "</resources>"

        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        planned[path] = text.replace(marker, block + marker)

    # --- the result must still parse ---------------------------------------------------
    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(ADD)} key(s) x {len(LOCALES)} locale(s) = {len(ADD) * len(LOCALES)} strings")
    print(f"  English hiding:   {AUTHOR_HIDING!r}")
    print(f"  English unhiding: {AUTHOR_UNHIDING!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
