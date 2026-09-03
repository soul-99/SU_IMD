#!/usr/bin/env python3
"""
v3-r2 — "Revert" becomes "Unhide settings" in the notifications.

The author's rule (i): replace the standalone **verb**, and leave the proper name
`Revert to default` alone everywhere — it is the Unhiding framework's option 2, the Tasker
function, the tile, the shortcut and the Favourites button, and renaming it would rename all of
those with it.

So the four notification bodies lose "revert", the overlay-failure title becomes
'Unhide settings failure', and the memory channel's name follows the verb. The
`Revert to default` channel keeps its name because that is what it is.

⚠ `shizuku_usb_fallback_title` is **not** touched and must not be: all three notifications in
ShizukuFallbackNotification.kt share it, including the two r1 added.

Computes the whole edit in memory, asserts every match count and locale, and writes nothing if
anything fails.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "framework/notification-manager/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# key -> {locale: new text}
REPLACE: dict[str, dict[str, str]] = {
    "hidden_revert_default": {
        "values": "Settings hidden, click to unhide settings.",
        "values-ar": "تم إخفاء الإعدادات، اضغط لإظهار الإعدادات.",
        "values-b+pt+BR": "Configurações ocultadas, toque para reexibir as configurações.",
        "values-b+zh+Hans": "设置已隐藏，点击以取消隐藏设置。",
        "values-de": "Einstellungen ausgeblendet, zum Einblenden tippen.",
        "values-es": "Ajustes ocultados, toca para mostrarlos.",
        "values-fr": "Paramètres masqués, appuyez pour les réafficher.",
        "values-hi": "सेटिंग छिपा दी गईं, दिखाने के लिए टैप करें.",
        "values-ja": "設定を非表示にしました。再表示するにはタップしてください。",
        "values-ko": "설정이 숨겨졌습니다. 다시 표시하려면 탭하세요.",
        "values-ru": "Настройки скрыты, нажмите, чтобы показать их.",
    },
    "hidden_revert_memory": {
        "values": "Settings hidden, click to unhide settings from memory.",
        "values-ar": "تم إخفاء الإعدادات، اضغط لإظهار الإعدادات من الذاكرة.",
        "values-b+pt+BR": "Configurações ocultadas, toque para reexibi-las da memória.",
        "values-b+zh+Hans": "设置已隐藏，点击以从记忆中取消隐藏设置。",
        "values-de": "Einstellungen ausgeblendet, zum Einblenden aus dem Speicher tippen.",
        "values-es": "Ajustes ocultados, toca para mostrarlos desde la memoria.",
        "values-fr": "Paramètres masqués, appuyez pour les réafficher depuis la mémoire.",
        "values-hi": "सेटिंग छिपा दी गईं, मेमोरी से दिखाने के लिए टैप करें.",
        "values-ja": "設定を非表示にしました。メモリーから再表示するにはタップしてください。",
        "values-ko": "설정이 숨겨졌습니다. 메모리에서 다시 표시하려면 탭하세요.",
        "values-ru": "Настройки скрыты, нажмите, чтобы восстановить их из памяти.",
    },
    "auto_hide_hidden_revert": {
        "values": "IMD+ hid your settings, click to unhide settings.",
        "values-ar": "‏IMD+ أخفى إعداداتك، اضغط لإظهار الإعدادات.",
        "values-b+pt+BR": "O IMD+ ocultou suas configurações, toque para reexibi-las.",
        "values-b+zh+Hans": "IMD+ 已隐藏你的设置，点击以取消隐藏设置。",
        "values-de": "IMD+ hat Ihre Einstellungen ausgeblendet, zum Einblenden tippen.",
        "values-es": "IMD+ ocultó tus ajustes, toca para mostrarlos.",
        "values-fr": "IMD+ a masqué vos paramètres, appuyez pour les réafficher.",
        "values-hi": "IMD+ ने आपकी सेटिंग छिपा दीं, दिखाने के लिए टैप करें.",
        "values-ja": "IMD+ が設定を非表示にしました。再表示するにはタップしてください。",
        "values-ko": "IMD+가 설정을 숨겼습니다. 다시 표시하려면 탭하세요.",
        "values-ru": "IMD+ скрыл ваши настройки, нажмите, чтобы показать их.",
    },
    "auto_hide_hidden_revert_memory": {
        "values": "IMD+ hid your settings, click to unhide settings from memory.",
        "values-ar": "‏IMD+ أخفى إعداداتك، اضغط لإظهار الإعدادات من الذاكرة.",
        "values-b+pt+BR": "O IMD+ ocultou suas configurações, toque para reexibi-las da memória.",
        "values-b+zh+Hans": "IMD+ 已隐藏你的设置，点击以从记忆中取消隐藏设置。",
        "values-de": "IMD+ hat Ihre Einstellungen ausgeblendet, zum Einblenden aus dem Speicher tippen.",
        "values-es": "IMD+ ocultó tus ajustes, toca para mostrarlos desde la memoria.",
        "values-fr": "IMD+ a masqué vos paramètres, appuyez pour les réafficher depuis la mémoire.",
        "values-hi": "IMD+ ने आपकी सेटिंग छिपा दीं, मेमोरी से दिखाने के लिए टैप करें.",
        "values-ja": "IMD+ が設定を非表示にしました。メモリーから再表示するにはタップしてください。",
        "values-ko": "IMD+가 설정을 숨겼습니다. 메모리에서 다시 표시하려면 탭하세요.",
        "values-ru": "IMD+ скрыл ваши настройки, нажмите, чтобы восстановить их из памяти.",
    },
    "overlay_restore_failed_title": {
        "values": "Unhide settings failure",
        "values-ar": "فشل إظهار الإعدادات",
        "values-b+pt+BR": "Falha ao reexibir configurações",
        "values-b+zh+Hans": "取消隐藏设置失败",
        "values-de": "Einblenden der Einstellungen fehlgeschlagen",
        "values-es": "Error al mostrar los ajustes",
        "values-fr": "Échec du réaffichage des paramètres",
        "values-hi": "सेटिंग दिखाने में विफल",
        "values-ja": "設定の再表示に失敗しました",
        "values-ko": "설정 다시 표시 실패",
        "values-ru": "Не удалось показать настройки",
    },
    "revert_using_memory": {
        "values": "Unhide settings using memory",
        "values-ar": "إظهار الإعدادات باستخدام الذاكرة",
        "values-b+pt+BR": "Reexibir configurações usando a memória",
        "values-b+zh+Hans": "使用记忆取消隐藏设置",
        "values-de": "Einstellungen aus dem Speicher einblenden",
        "values-es": "Mostrar ajustes usando la memoria",
        "values-fr": "Réafficher les paramètres depuis la mémoire",
        "values-hi": "मेमोरी का उपयोग करके सेटिंग दिखाएँ",
        "values-ja": "メモリーを使って設定を再表示",
        "values-ko": "메모리를 사용해 설정 다시 표시",
        "values-ru": "Показать настройки из памяти",
    },
}

AUTHOR_ENGLISH = {
    "overlay_restore_failed_title": "Unhide settings failure",
}

# The proper name must survive untouched.
MUST_KEEP = {"revert_to_default": "Revert to default"}


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


def main() -> int:
    problems: list[str] = []

    for key, texts in REPLACE.items():
        missing = [locale for locale in LOCALES if locale not in texts]

        if missing:
            problems.append(f"{key}: missing {missing}")

        expected = AUTHOR_ENGLISH.get(key)

        if expected is not None and texts.get("values") != expected:
            problems.append(
                f"{key}: English is {texts.get('values')!r}, author wrote {expected!r}",
            )

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        for key, texts in REPLACE.items():
            pattern = re.compile(rf'(<string name="{key}">)(.*?)(</string>)', re.S)

            found = pattern.findall(text)

            if len(found) != 1:
                problems.append(f"{locale}: {len(found)} of {key}")

                continue

            text = pattern.sub(
                lambda m, value=escape(texts[locale]): m.group(1) + value + m.group(3),
                text,
                count=1,
            )

        # The English name of the function that keeps its name.
        if locale == "values":
            for key, value in MUST_KEEP.items():
                if f'<string name="{key}">{value}</string>' not in text:
                    problems.append(f"{locale}: {key} is no longer {value!r}")

        staged[path] = text

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}: does not parse — {error}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(REPLACE)} keys reworded across {len(staged)} locales")

    return 0


if __name__ == "__main__":
    sys.exit(main())
