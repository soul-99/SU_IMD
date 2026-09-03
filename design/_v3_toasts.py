#!/usr/bin/env python3
"""
v3-r2 — the toast set.

The author's replacement for every hiding/unhiding toast. Two families:

* **start**, short, said as the work begins — the old toasts' slot;
* **completion**, long, said when it has finished — which is the new part, and the reason the
  set is this size: the sentence now names *which* framework acted.

Each has an IMD form and an IMD+ form, the latter differing only in the `IMD+: ` prefix, at the
author's instruction. `[app name]` is a placeholder in the author's notation; it is written as
`%1$s`, which is the same string with the substitution Android understands.

Every English string is the author's, verbatim. Computes the whole edit in memory, asserts the
locale coverage and that no key already exists, and writes nothing if anything fails.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "common/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# key -> {locale: text}. English is the author's, character for character.
ADD: dict[str, dict[str, str]] = {
    # ---- start, IMD ------------------------------------------------------------------
    "toast_hiding": {
        "values": "IMD: Hiding settings...",
        "values-ar": "‏IMD: جارٍ إخفاء الإعدادات...",
        "values-b+pt+BR": "IMD: ocultando configurações...",
        "values-b+zh+Hans": "IMD：正在隐藏设置...",
        "values-de": "IMD: Einstellungen werden ausgeblendet...",
        "values-es": "IMD: ocultando ajustes...",
        "values-fr": "IMD : masquage des paramètres...",
        "values-hi": "IMD: सेटिंग छिपाई जा रही हैं...",
        "values-ja": "IMD: 設定を非表示にしています...",
        "values-ko": "IMD: 설정을 숨기는 중...",
        "values-ru": "IMD: скрытие настроек...",
    },
    "toast_unhiding": {
        "values": "IMD: Unhiding settings...",
        "values-ar": "‏IMD: جارٍ إظهار الإعدادات...",
        "values-b+pt+BR": "IMD: reexibindo configurações...",
        "values-b+zh+Hans": "IMD：正在取消隐藏设置...",
        "values-de": "IMD: Einstellungen werden wieder eingeblendet...",
        "values-es": "IMD: mostrando ajustes...",
        "values-fr": "IMD : réaffichage des paramètres...",
        "values-hi": "IMD: सेटिंग दिखाई जा रही हैं...",
        "values-ja": "IMD: 設定を再表示しています...",
        "values-ko": "IMD: 설정을 다시 표시하는 중...",
        "values-ru": "IMD: восстановление настроек...",
    },
    # ---- start, IMD+ -----------------------------------------------------------------
    "toast_auto_hiding": {
        "values": "IMD+: Hiding settings...",
        "values-ar": "‏IMD+: جارٍ إخفاء الإعدادات...",
        "values-b+pt+BR": "IMD+: ocultando configurações...",
        "values-b+zh+Hans": "IMD+：正在隐藏设置...",
        "values-de": "IMD+: Einstellungen werden ausgeblendet...",
        "values-es": "IMD+: ocultando ajustes...",
        "values-fr": "IMD+ : masquage des paramètres...",
        "values-hi": "IMD+: सेटिंग छिपाई जा रही हैं...",
        "values-ja": "IMD+: 設定を非表示にしています...",
        "values-ko": "IMD+: 설정을 숨기는 중...",
        "values-ru": "IMD+: скрытие настроек...",
    },
    "toast_auto_unhiding": {
        "values": "IMD+: Unhiding settings...",
        "values-ar": "‏IMD+: جارٍ إظهار الإعدادات...",
        "values-b+pt+BR": "IMD+: reexibindo configurações...",
        "values-b+zh+Hans": "IMD+：正在取消隐藏设置...",
        "values-de": "IMD+: Einstellungen werden wieder eingeblendet...",
        "values-es": "IMD+: mostrando ajustes...",
        "values-fr": "IMD+ : réaffichage des paramètres...",
        "values-hi": "IMD+: सेटिंग दिखाई जा रही हैं...",
        "values-ja": "IMD+: 設定を再表示しています...",
        "values-ko": "IMD+: 설정을 다시 표시하는 중...",
        "values-ru": "IMD+: восстановление настроек...",
    },
    # ---- start, auto revert ----------------------------------------------------------
    "toast_auto_revert_running": {
        "values": "IMD: Auto revert running...",
        "values-ar": "‏IMD: جارٍ التراجع التلقائي...",
        "values-b+pt+BR": "IMD: reversão automática em andamento...",
        "values-b+zh+Hans": "IMD：正在自动还原...",
        "values-de": "IMD: Automatische Wiederherstellung läuft...",
        "values-es": "IMD: reversión automática en curso...",
        "values-fr": "IMD : rétablissement automatique en cours...",
        "values-hi": "IMD: ऑटो रिवर्ट चल रहा है...",
        "values-ja": "IMD: 自動復元を実行しています...",
        "values-ko": "IMD: 자동 되돌리기 실행 중...",
        "values-ru": "IMD: выполняется автоматический возврат...",
    },
    # ---- completion, IMD -------------------------------------------------------------
    "toast_done_hidden": {
        "values": "IMD: Settings hidden",
        "values-ar": "‏IMD: تم إخفاء الإعدادات",
        "values-b+pt+BR": "IMD: configurações ocultadas",
        "values-b+zh+Hans": "IMD：设置已隐藏",
        "values-de": "IMD: Einstellungen ausgeblendet",
        "values-es": "IMD: ajustes ocultados",
        "values-fr": "IMD : paramètres masqués",
        "values-hi": "IMD: सेटिंग छिपा दी गईं",
        "values-ja": "IMD: 設定を非表示にしました",
        "values-ko": "IMD: 설정이 숨겨졌습니다",
        "values-ru": "IMD: настройки скрыты",
    },
    "toast_done_hidden_for": {
        "values": "IMD: Settings hidden for %1$s",
        "values-ar": "‏IMD: تم إخفاء الإعدادات لـ ‎%1$s",
        "values-b+pt+BR": "IMD: configurações ocultadas para %1$s",
        "values-b+zh+Hans": "IMD：已为 %1$s 隐藏设置",
        "values-de": "IMD: Einstellungen für %1$s ausgeblendet",
        "values-es": "IMD: ajustes ocultados para %1$s",
        "values-fr": "IMD : paramètres masqués pour %1$s",
        "values-hi": "IMD: %1$s के लिए सेटिंग छिपा दी गईं",
        "values-ja": "IMD: %1$s の設定を非表示にしました",
        "values-ko": "IMD: %1$s의 설정이 숨겨졌습니다",
        "values-ru": "IMD: настройки скрыты для %1$s",
    },
    "toast_done_reverted_defaults": {
        "values": "IMD: Settings reverted to defaults",
        "values-ar": "‏IMD: تمت إعادة الإعدادات إلى الوضع الافتراضي",
        "values-b+pt+BR": "IMD: configurações revertidas para os padrões",
        "values-b+zh+Hans": "IMD：设置已还原为默认值",
        "values-de": "IMD: Einstellungen auf Standard zurückgesetzt",
        "values-es": "IMD: ajustes restaurados a los valores predeterminados",
        "values-fr": "IMD : paramètres rétablis aux valeurs par défaut",
        "values-hi": "IMD: सेटिंग डिफ़ॉल्ट पर वापस लाई गईं",
        "values-ja": "IMD: 設定を既定値に戻しました",
        "values-ko": "IMD: 설정이 기본값으로 되돌려졌습니다",
        "values-ru": "IMD: настройки возвращены к значениям по умолчанию",
    },
    "toast_done_reverted_memory": {
        "values": "IMD: Settings reverted from memory",
        "values-ar": "‏IMD: تمت إعادة الإعدادات من الذاكرة",
        "values-b+pt+BR": "IMD: configurações revertidas da memória",
        "values-b+zh+Hans": "IMD：设置已从记忆中还原",
        "values-de": "IMD: Einstellungen aus dem Speicher wiederhergestellt",
        "values-es": "IMD: ajustes restaurados desde la memoria",
        "values-fr": "IMD : paramètres rétablis depuis la mémoire",
        "values-hi": "IMD: सेटिंग मेमोरी से वापस लाई गईं",
        "values-ja": "IMD: 設定をメモリーから復元しました",
        "values-ko": "IMD: 설정이 메모리에서 복원되었습니다",
        "values-ru": "IMD: настройки восстановлены из памяти",
    },
    "toast_done_reverted_memory_for": {
        "values": "IMD: Settings reverted from memory (%1$s)",
        "values-ar": "‏IMD: تمت إعادة الإعدادات من الذاكرة (‎%1$s)",
        "values-b+pt+BR": "IMD: configurações revertidas da memória (%1$s)",
        "values-b+zh+Hans": "IMD：设置已从记忆中还原（%1$s）",
        "values-de": "IMD: Einstellungen aus dem Speicher wiederhergestellt (%1$s)",
        "values-es": "IMD: ajustes restaurados desde la memoria (%1$s)",
        "values-fr": "IMD : paramètres rétablis depuis la mémoire (%1$s)",
        "values-hi": "IMD: सेटिंग मेमोरी से वापस लाई गईं (%1$s)",
        "values-ja": "IMD: 設定をメモリーから復元しました (%1$s)",
        "values-ko": "IMD: 설정이 메모리에서 복원되었습니다 (%1$s)",
        "values-ru": "IMD: настройки восстановлены из памяти (%1$s)",
    },
    # ---- completion, IMD+ ------------------------------------------------------------
    "toast_auto_done_hidden": {
        "values": "IMD+: Settings hidden",
        "values-ar": "‏IMD+: تم إخفاء الإعدادات",
        "values-b+pt+BR": "IMD+: configurações ocultadas",
        "values-b+zh+Hans": "IMD+：设置已隐藏",
        "values-de": "IMD+: Einstellungen ausgeblendet",
        "values-es": "IMD+: ajustes ocultados",
        "values-fr": "IMD+ : paramètres masqués",
        "values-hi": "IMD+: सेटिंग छिपा दी गईं",
        "values-ja": "IMD+: 設定を非表示にしました",
        "values-ko": "IMD+: 설정이 숨겨졌습니다",
        "values-ru": "IMD+: настройки скрыты",
    },
    "toast_auto_done_hidden_for": {
        "values": "IMD+: Settings hidden for %1$s",
        "values-ar": "‏IMD+: تم إخفاء الإعدادات لـ ‎%1$s",
        "values-b+pt+BR": "IMD+: configurações ocultadas para %1$s",
        "values-b+zh+Hans": "IMD+：已为 %1$s 隐藏设置",
        "values-de": "IMD+: Einstellungen für %1$s ausgeblendet",
        "values-es": "IMD+: ajustes ocultados para %1$s",
        "values-fr": "IMD+ : paramètres masqués pour %1$s",
        "values-hi": "IMD+: %1$s के लिए सेटिंग छिपा दी गईं",
        "values-ja": "IMD+: %1$s の設定を非表示にしました",
        "values-ko": "IMD+: %1$s의 설정이 숨겨졌습니다",
        "values-ru": "IMD+: настройки скрыты для %1$s",
    },
    "toast_auto_done_reverted_defaults": {
        "values": "IMD+: Settings reverted to defaults",
        "values-ar": "‏IMD+: تمت إعادة الإعدادات إلى الوضع الافتراضي",
        "values-b+pt+BR": "IMD+: configurações revertidas para os padrões",
        "values-b+zh+Hans": "IMD+：设置已还原为默认值",
        "values-de": "IMD+: Einstellungen auf Standard zurückgesetzt",
        "values-es": "IMD+: ajustes restaurados a los valores predeterminados",
        "values-fr": "IMD+ : paramètres rétablis aux valeurs par défaut",
        "values-hi": "IMD+: सेटिंग डिफ़ॉल्ट पर वापस लाई गईं",
        "values-ja": "IMD+: 設定を既定値に戻しました",
        "values-ko": "IMD+: 설정이 기본값으로 되돌려졌습니다",
        "values-ru": "IMD+: настройки возвращены к значениям по умолчанию",
    },
    "toast_auto_done_reverted_memory": {
        "values": "IMD+: Settings reverted from memory",
        "values-ar": "‏IMD+: تمت إعادة الإعدادات من الذاكرة",
        "values-b+pt+BR": "IMD+: configurações revertidas da memória",
        "values-b+zh+Hans": "IMD+：设置已从记忆中还原",
        "values-de": "IMD+: Einstellungen aus dem Speicher wiederhergestellt",
        "values-es": "IMD+: ajustes restaurados desde la memoria",
        "values-fr": "IMD+ : paramètres rétablis depuis la mémoire",
        "values-hi": "IMD+: सेटिंग मेमोरी से वापस लाई गईं",
        "values-ja": "IMD+: 設定をメモリーから復元しました",
        "values-ko": "IMD+: 설정이 메모리에서 복원되었습니다",
        "values-ru": "IMD+: настройки восстановлены из памяти",
    },
    "toast_auto_done_reverted_memory_for": {
        "values": "IMD+: Settings reverted from memory (%1$s)",
        "values-ar": "‏IMD+: تمت إعادة الإعدادات من الذاكرة (‎%1$s)",
        "values-b+pt+BR": "IMD+: configurações revertidas da memória (%1$s)",
        "values-b+zh+Hans": "IMD+：设置已从记忆中还原（%1$s）",
        "values-de": "IMD+: Einstellungen aus dem Speicher wiederhergestellt (%1$s)",
        "values-es": "IMD+: ajustes restaurados desde la memoria (%1$s)",
        "values-fr": "IMD+ : paramètres rétablis depuis la mémoire (%1$s)",
        "values-hi": "IMD+: सेटिंग मेमोरी से वापस लाई गईं (%1$s)",
        "values-ja": "IMD+: 設定をメモリーから復元しました (%1$s)",
        "values-ko": "IMD+: 설정이 메모리에서 복원되었습니다 (%1$s)",
        "values-ru": "IMD+: настройки восстановлены из памяти (%1$s)",
    },
}

# The author's English, for the assertion below. Kept apart from ADD so a slip in one is not
# copied into the other.
AUTHOR_ENGLISH = {
    "toast_hiding": "IMD: Hiding settings...",
    "toast_unhiding": "IMD: Unhiding settings...",
    "toast_auto_hiding": "IMD+: Hiding settings...",
    "toast_auto_unhiding": "IMD+: Unhiding settings...",
    "toast_auto_revert_running": "IMD: Auto revert running...",
    "toast_done_hidden": "IMD: Settings hidden",
    "toast_done_hidden_for": "IMD: Settings hidden for %1$s",
    "toast_done_reverted_defaults": "IMD: Settings reverted to defaults",
    "toast_done_reverted_memory": "IMD: Settings reverted from memory",
    "toast_done_reverted_memory_for": "IMD: Settings reverted from memory (%1$s)",
    "toast_auto_done_hidden": "IMD+: Settings hidden",
    "toast_auto_done_hidden_for": "IMD+: Settings hidden for %1$s",
    "toast_auto_done_reverted_defaults": "IMD+: Settings reverted to defaults",
    "toast_auto_done_reverted_memory": "IMD+: Settings reverted from memory",
    "toast_auto_done_reverted_memory_for": "IMD+: Settings reverted from memory (%1$s)",
}

ANCHOR = '    <string name="permissions_lost">'


def escape(text: str) -> str:
    """Android resource escaping. A literal apostrophe or ampersand breaks aapt."""
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


def main() -> int:
    problems: list[str] = []

    # Every key in every locale, and the English exactly as the author wrote it.
    for key, texts in ADD.items():
        missing = [locale for locale in LOCALES if locale not in texts]

        if missing:
            problems.append(f"{key}: missing {missing}")

        if texts.get("values") != AUTHOR_ENGLISH.get(key):
            problems.append(
                f"{key}: English is {texts.get('values')!r}, "
                f"author wrote {AUTHOR_ENGLISH.get(key)!r}",
            )

        # A placeholder in one locale and not another is a crash, not a typo.
        with_arg = {loc for loc, text in texts.items() if "%1$s" in text}

        if with_arg and len(with_arg) != len(LOCALES):
            problems.append(f"{key}: %1$s in {len(with_arg)} of {len(LOCALES)} locales")

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")
            continue

        text = path.read_text(encoding="utf-8")

        for key in ADD:
            if re.search(rf'name="{key}"', text):
                problems.append(f"{locale}: {key} already exists")

        if ANCHOR not in text:
            problems.append(f"{locale}: anchor not found")
            continue

        block = "".join(
            f'    <string name="{key}">{escape(ADD[key][locale])}</string>\n'
            for key in ADD
        )

        staged[path] = text.replace(ANCHOR, block + ANCHOR, 1)

    # Everything staged must still parse as XML, which is the check that catches an escape
    # this script forgot rather than one it knows about.
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

    print(f"ok — {len(ADD)} keys across {len(staged)} locales")

    return 0


if __name__ == "__main__":
    sys.exit(main())
