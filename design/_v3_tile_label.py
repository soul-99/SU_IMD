#!/usr/bin/env python3
"""
v3-r1 — the services tile and shortcut become "Settings manager".

⚠ **One string, two surfaces.** `services_shortcut_label` is the label for both the Quick
Settings tile (AndroidManifest :188) and the home-screen shortcut (:82). The author asked for
the tile; the shortcut moves with it, because both open the same dialog and naming them
differently would be worse than either name alone.

Kept short deliberately: a QS tile label is truncated at roughly 12-16 characters on most
launchers. "Settings manager" is 16, exactly as long as the "Services manager" it replaces, so
nothing that fitted before stops fitting.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "app/src/main/res"

KEY = "services_shortcut_label"

NEW = {
    "values": "Settings manager",
    "values-ar": "مدير الإعدادات",
    "values-b+pt+BR": "Gerenciador de config.",
    "values-b+zh+Hans": "设置管理器",
    "values-de": "Einstellungsmanager",
    "values-es": "Gestor de ajustes",
    "values-fr": "Gestionnaire de param.",
    "values-hi": "सेटिंग्स प्रबंधक",
    "values-ja": "設定マネージャー",
    "values-ko": "설정 관리자",
    "values-ru": "Диспетчер настроек",
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
    if len(NEW["values"]) > len("Services manager"):
        return fail("the English label is longer than the one it replaces; a tile would clip it")

    planned = {}

    for locale, value in NEW.items():
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")
        current = value_of(text, KEY)

        if current is None:
            return fail(f"{locale}: {KEY} not found")

        if "'" in value and "\\'" not in value:
            return fail(f"{locale}: unescaped apostrophe")

        planned[path] = text.replace(
            f'<string name="{KEY}">{current}</string>',
            f'<string name="{KEY}">{value}</string>',
            1,
        )

    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"replaced {KEY} in {len(planned)} locale(s)")
    print(f"  English: {NEW['values']!r}  ({len(NEW['values'])} chars)")
    print("  drives BOTH the QS tile and the home-screen shortcut")
    return 0


if __name__ == "__main__":
    sys.exit(main())
