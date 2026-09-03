#!/usr/bin/env python3
"""
v3-r1 — "Please setup Auto hide settings first", and its auto-unhide twin.

The author's English for IMD+ is verbatim and asserted. The auto-unhide line is the same
sentence with the feature's own name in it, which is what he asked for ("a similar dialog
box"); the existing auto_unhide_blocked text it replaces said the same thing at more length.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "feature/settings/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

AUTHOR = "Please setup Auto hide settings first"

ADD = {
    "auto_hide_setup_first": {
        "values": AUTHOR,
        "values-ar": "يرجى إعداد إعدادات الإخفاء التلقائي أولاً",
        "values-b+pt+BR": "Configure primeiro as configurações de ocultação automática",
        "values-b+zh+Hans": "请先设置自动隐藏设置",
        "values-de": "Bitte richten Sie zuerst die Auto-Ausblenden-Einstellungen ein",
        "values-es": "Configura primero los ajustes de ocultación automática",
        "values-fr": "Veuillez d\\'abord configurer les paramètres de masquage automatique",
        "values-hi": "कृपया पहले ऑटो हाइड सेटिंग्स सेट करें",
        "values-ja": "先に自動非表示の設定を行ってください",
        "values-ko": "먼저 자동 숨기기 설정을 완료해 주세요",
        "values-ru": "Сначала настройте параметры автоскрытия",
    },
}

REPLACE = {
    "auto_unhide_blocked": {
        "values": "Please setup Auto unhide settings first",
        "values-ar": "يرجى إعداد إعدادات إظهار التلقائي أولاً",
        "values-b+pt+BR": "Configure primeiro as configurações de reexibição automática",
        "values-b+zh+Hans": "请先设置自动恢复设置",
        "values-de": "Bitte richten Sie zuerst die Auto-Einblenden-Einstellungen ein",
        "values-es": "Configura primero los ajustes de reaparición automática",
        "values-fr": "Veuillez d\\'abord configurer les paramètres de réaffichage automatique",
        "values-hi": "कृपया पहले ऑटो अनहाइड सेटिंग्स सेट करें",
        "values-ja": "先に自動再表示の設定を行ってください",
        "values-ko": "먼저 자동 다시 표시 설정을 완료해 주세요",
        "values-ru": "Сначала настройте параметры автовосстановления",
    },
}


def fail(message):
    print(f"REFUSED, nothing written: {message}")
    return 1


def value_of(text, key):
    marker = f'<string name="{key}">'
    start = text.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = text.find("</string>", start)
    return text[start:end] if end != -1 else None


def main():
    if ADD["auto_hide_setup_first"]["values"] != AUTHOR:
        return fail("the English IMD+ line is not the author's text")

    for table in list(ADD.values()) + list(REPLACE.values()):
        missing = [loc for loc in LOCALES if loc not in table]
        if missing:
            return fail(f"missing locales: {missing}")

    planned = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"
        text = path.read_text(encoding="utf-8")

        for key, table in REPLACE.items():
            current = value_of(text, key)
            if current is None:
                return fail(f"{locale}: {key} not found")
            text = text.replace(
                f'<string name="{key}">{current}</string>',
                f'<string name="{key}">{table[locale]}</string>',
                1,
            )

        block = ""
        for key, table in ADD.items():
            if f'name="{key}"' in text:
                return fail(f"{locale}: {key} already exists — has this run before?")
            block += f'    <string name="{key}">{table[locale]}</string>\n'

        for table in list(ADD.values()) + list(REPLACE.values()):
            value = table[locale]
            if "'" in value and "\\'" not in value:
                return fail(f"{locale}: unescaped apostrophe in {value[:34]!r}")
            if "&" in value and "&amp;" not in value:
                return fail(f"{locale}: unescaped ampersand")
            if "\n" in value:
                return fail(f"{locale}: literal newline")

        marker = "</resources>"
        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        planned[path] = text.replace(marker, block + marker, 1)

    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(planned)} locale(s)")
    print(f"  IMD+       : {AUTHOR!r}")
    print(f"  auto unhide: {REPLACE['auto_unhide_blocked']['values']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
