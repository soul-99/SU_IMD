#!/usr/bin/env python3
"""
v3-r1 — the "Display over other apps to hide" dialog's description, replaced.

Three points. The first is drawn in red by the dialog and so lives in its own key; the other
two share one string with an escaped \n between them.

The author's words, with two corrections he confirmed on 30 Aug 2026:
  * point 2 spells out "Display over other apps" rather than his shorthand "DOOAs", which is
    not UI text anywhere else in the app;
  * point 3 reads "are shown below", matching the accessibility picker, rather than "are show".
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

DELAY_KEY = "overlay_packages_dialog_delay"
DESC_KEY = "overlay_packages_dialog_description"

AUTHOR_POINT_1 = "1. Will add slight delay to hiding time"
AUTHOR_POINT_2 = "2. Uses Shizuku to turn Display over other apps on/off."
AUTHOR_POINT_3 = "3. Only enabled ones are shown below"

DELAY = {
    "values": AUTHOR_POINT_1,
    "values-ar": "1. سيضيف تأخيرًا بسيطًا لوقت الإخفاء",
    "values-b+pt+BR": "1. Adiciona um pequeno atraso ao tempo de ocultação",
    "values-b+zh+Hans": "1. 会略微增加隐藏耗时",
    "values-de": "1. Verlängert die Ausblendzeit geringfügig",
    "values-es": "1. Añade un ligero retraso al tiempo de ocultación",
    "values-fr": "1. Ajoute un léger délai au masquage",
    "values-hi": "1. छिपाने के समय में थोड़ी देरी जोड़ेगा",
    "values-ja": "1. 非表示にかかる時間が少し長くなります",
    "values-ko": "1. 숨기는 시간이 약간 길어집니다",
    "values-ru": "1. Немного увеличит время скрытия",
}

DESC = {
    "values": f"{AUTHOR_POINT_2}\\n{AUTHOR_POINT_3}",
    "values-ar": "2. يستخدم Shizuku لتشغيل وإيقاف العرض فوق التطبيقات الأخرى.\\n3. المُفعّلة فقط معروضة أدناه",
    "values-b+pt+BR": "2. Usa o Shizuku para ativar/desativar Sobrepor a outros apps.\\n3. Apenas os ativados aparecem abaixo",
    "values-b+zh+Hans": "2. 使用 Shizuku 开启或关闭“显示在其他应用上层”。\\n3. 下方仅显示已启用的应用",
    "values-de": "2. Nutzt Shizuku, um „Über anderen Apps einblenden“ ein- und auszuschalten.\\n3. Unten werden nur aktivierte angezeigt",
    "values-es": "2. Usa Shizuku para activar o desactivar Mostrar sobre otras aplicaciones.\\n3. Abajo solo se muestran los activados",
    "values-fr": "2. Utilise Shizuku pour activer ou désactiver Affichage par-dessus les autres applis.\\n3. Seuls les activés sont affichés ci-dessous",
    "values-hi": "2. Shizuku का उपयोग करके अन्य ऐप्स के ऊपर दिखाएँ को चालू/बंद करता है.\\n3. नीचे केवल सक्षम ऐप्स दिखाए जाते हैं",
    "values-ja": "2. Shizuku を使って「他のアプリの上に重ねて表示」をオン・オフします。\\n3. 下には有効なもののみ表示されます",
    "values-ko": "2. Shizuku를 사용해 다른 앱 위에 표시를 켜고 끕니다.\\n3. 아래에는 사용 설정된 항목만 표시됩니다",
    "values-ru": "2. Использует Shizuku, чтобы включать и выключать «Поверх других приложений».\\n3. Ниже показаны только включённые",
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
    if "DOOA" in DESC["values"]:
        return fail("point 2 still carries the DOOAs shorthand the author replaced")

    if "are show below" in DESC["values"]:
        return fail("point 3 still carries the uncorrected 'are show'")

    for table, label in ((DELAY, "DELAY"), (DESC, "DESC")):
        missing = [loc for loc in LOCALES if loc not in table]
        if missing:
            return fail(f"{label} missing locales: {missing}")

    planned = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"
        text = path.read_text(encoding="utf-8")

        current = value_of(text, DESC_KEY)
        if current is None:
            return fail(f"{locale}: {DESC_KEY} not found")

        if f'name="{DELAY_KEY}"' in text:
            return fail(f"{locale}: {DELAY_KEY} already exists — has this run before?")

        for value in (DELAY[locale], DESC[locale]):
            if "\n" in value:
                return fail(f"{locale}: literal newline collapses to a space; use \\\\n")
            if "'" in value and "\\'" not in value:
                return fail(f"{locale}: unescaped apostrophe in {value[:30]!r}")
            if "&" in value and "&amp;" not in value:
                return fail(f"{locale}: unescaped ampersand")

        if DESC[locale].count("\\n") != 1:
            return fail(f"{locale}: description needs exactly one escaped newline")

        text = text.replace(
            f'<string name="{DESC_KEY}">{current}</string>',
            f'<string name="{DELAY_KEY}">{DELAY[locale]}</string>\n'
            f'    <string name="{DESC_KEY}">{DESC[locale]}</string>',
            1,
        )

        planned[path] = text

    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {DELAY_KEY} + replaced {DESC_KEY} in {len(planned)} locale(s)")
    print(f"  red point : {AUTHOR_POINT_1!r}")
    print(f"  points 2-3: {DESC['values']!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
