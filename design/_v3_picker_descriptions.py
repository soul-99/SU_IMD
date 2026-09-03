#!/usr/bin/env python3
"""
v3-r1 — the "Accessibility services to hide" dialog's description, replaced.

The author's two points, verbatim:
    1. Only those turned off by IMD are turned on again
    2. Only enabled ones are shown below

Replaces the old sentence entirely rather than appending to it: the old text described a list
of every installed service, and the list is now narrowed to enabled-or-held.

⚠ The separator is an **escaped** \\n. A literal newline in an unquoted Android string resource
collapses to a single space, which is how the two-line auto_hide title once rendered on one
line in all 11 locales.

The DOOA dialog's description is NOT here — its wording has two open questions with the author.
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

KEY = "accessibility_services_dialog_description"

AUTHOR_POINT_1 = "1. Only those turned off by IMD are turned on again"
AUTHOR_POINT_2 = "2. Only enabled ones are shown below"

NEW = {
    "values": f"{AUTHOR_POINT_1}\\n{AUTHOR_POINT_2}",
    "values-ar": "1. يُعاد تشغيل ما أوقفه IMD فقط\\n2. المُفعّلة فقط معروضة أدناه",
    "values-b+pt+BR": "1. Apenas os desativados pelo IMD são reativados\\n2. Apenas os ativados aparecem abaixo",
    "values-b+zh+Hans": "1. 仅重新开启由 IMD 关闭的服务\\n2. 下方仅显示已启用的服务",
    "values-de": "1. Nur von IMD deaktivierte werden wieder aktiviert\\n2. Unten werden nur aktivierte angezeigt",
    "values-es": "1. Solo se vuelven a activar los que IMD desactivó\\n2. Abajo solo se muestran los activados",
    "values-fr": "1. Seuls ceux désactivés par IMD sont réactivés\\n2. Seuls les activés sont affichés ci-dessous",
    "values-hi": "1. केवल IMD द्वारा बंद किए गए ही फिर से चालू होते हैं\\n2. नीचे केवल सक्षम सेवाएँ दिखाई जाती हैं",
    "values-ja": "1. IMD がオフにしたものだけが再びオンになります\\n2. 下には有効なもののみ表示されます",
    "values-ko": "1. IMD가 끈 항목만 다시 켜집니다\\n2. 아래에는 사용 설정된 항목만 표시됩니다",
    "values-ru": "1. Включаются обратно только отключённые IMD\\n2. Ниже показаны только включённые",
}


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def value_of(text: str, key: str) -> str | None:
    marker = f'<string name="{key}">'
    start = text.find(marker)

    if start == -1:
        return None

    start += len(marker)
    end = text.find("</string>", start)

    return text[start:end] if end != -1 else None


def main() -> int:
    if NEW["values"] != f"{AUTHOR_POINT_1}\\n{AUTHOR_POINT_2}":
        return fail("the English value is not the author's two points")

    missing = [loc for loc in LOCALES if loc not in NEW]

    if missing:
        return fail(f"missing locales: {missing}")

    planned: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")
        current = value_of(text, KEY)

        if current is None:
            return fail(f"{locale}: {KEY} not found")

        value = NEW[locale]

        if "\n" in value:
            return fail(f"{locale}: literal newline — it collapses to a space, use \\\\n")

        if value.count("\\n") != 1:
            return fail(f"{locale}: expected exactly one escaped newline")

        if "'" in value and "\\'" not in value:
            return fail(f"{locale}: unescaped apostrophe")

        if "&" in value and "&amp;" not in value:
            return fail(f"{locale}: unescaped ampersand")

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
    print(f"  English: {NEW['values']!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
