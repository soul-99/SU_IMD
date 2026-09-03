#!/usr/bin/env python3
"""
v3-r1b — "IMD+ failed to hide settings as Shizuku service could not be started."

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

KEY = "auto_hide_shizuku_failed"

AUTHOR = (
    "IMD+ failed to hide settings as Shizuku service could not be started. "
    "Please check your settings."
)

ADD = {
    "values": AUTHOR,
    "values-ar": "فشل ‏IMD+ في إخفاء الإعدادات لتعذّر تشغيل خدمة Shizuku. يرجى التحقق من إعداداتك.",
    "values-b+pt+BR": "O IMD+ não conseguiu ocultar as configurações porque o serviço Shizuku não pôde ser iniciado. Verifique suas configurações.",
    "values-b+zh+Hans": "IMD+ 无法隐藏设置，因为 Shizuku 服务无法启动。请检查你的设置。",
    "values-de": "IMD+ konnte die Einstellungen nicht ausblenden, da der Shizuku-Dienst nicht gestartet werden konnte. Bitte prüfen Sie Ihre Einstellungen.",
    "values-es": "IMD+ no pudo ocultar los ajustes porque el servicio Shizuku no se pudo iniciar. Comprueba tus ajustes.",
    "values-fr": "IMD+ n\\'a pas pu masquer les paramètres car le service Shizuku n\\'a pas pu démarrer. Veuillez vérifier vos paramètres.",
    "values-hi": "IMD+ सेटिंग्स नहीं छिपा सका क्योंकि Shizuku सेवा शुरू नहीं हो सकी. कृपया अपनी सेटिंग्स जाँचें.",
    "values-ja": "Shizuku サービスを開始できなかったため、IMD+ は設定を非表示にできませんでした。設定を確認してください。",
    "values-ko": "Shizuku 서비스를 시작할 수 없어 IMD+가 설정을 숨기지 못했습니다. 설정을 확인해 주세요.",
    "values-ru": "IMD+ не удалось скрыть настройки: служба Shizuku не запустилась. Проверьте настройки.",
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
