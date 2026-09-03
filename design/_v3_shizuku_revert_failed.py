#!/usr/bin/env python3
"""
v3-r1d — "Failed to start Shizuku service, please click here to start manually."

v3 spec item 5, pulled forward from r3 at the author's request.

The author's sentence, verbatim, asserted before anything is written.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "framework/notification-manager/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

KEY = "shizuku_revert_failed"
AUTHOR = "Failed to start Shizuku service, please click here to start manually"

ADD = {
    "values": AUTHOR,
    "values-ar": "تعذّر تشغيل خدمة Shizuku، اضغط هنا لتشغيلها يدويًا",
    "values-b+pt+BR": "Falha ao iniciar o serviço Shizuku, toque aqui para iniciá-lo manualmente",
    "values-b+zh+Hans": "无法启动 Shizuku 服务，请点击此处手动启动",
    "values-de": "Shizuku-Dienst konnte nicht gestartet werden, hier tippen, um ihn manuell zu starten",
    "values-es": "No se pudo iniciar el servicio Shizuku, toca aquí para iniciarlo manualmente",
    "values-fr": "Impossible de démarrer le service Shizuku, appuyez ici pour le lancer manuellement",
    "values-hi": "Shizuku सेवा शुरू नहीं हो सकी, इसे मैन्युअली शुरू करने के लिए यहाँ टैप करें",
    "values-ja": "Shizuku サービスを開始できませんでした。ここをタップして手動で開始してください",
    "values-ko": "Shizuku 서비스를 시작하지 못했습니다. 여기를 눌러 수동으로 시작해 주세요",
    "values-ru": "Не удалось запустить службу Shizuku, нажмите здесь, чтобы запустить её вручную",
}


def fail(message):
    print(f"REFUSED, nothing written: {message}")
    return 1


def main():
    if ADD["values"] != AUTHOR:
        return fail("the English value is not the author's text")

    missing = [loc for loc in LOCALES if loc not in ADD]

    if missing:
        return fail(f"missing locales: {missing}")

    planned = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")

        if f'name="{KEY}"' in text:
            return fail(f"{locale}: {KEY} already exists — has this run before?")

        value = ADD[locale]

        if "'" in value and "\\'" not in value:
            return fail(f"{locale}: unescaped apostrophe")

        if "&" in value and "&amp;" not in value:
            return fail(f"{locale}: unescaped ampersand")

        if "\n" in value:
            return fail(f"{locale}: literal newline")

        marker = "</resources>"

        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        planned[path] = text.replace(
            marker, f'    <string name="{KEY}">{value}</string>\n{marker}', 1,
        )

    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {KEY} in {len(planned)} locale(s)")
    print(f"  English: {AUTHOR!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
