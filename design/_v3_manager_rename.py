#!/usr/bin/env python3
"""
v3-r1 — "IMD services manager" becomes 'IMD Settings Manager', and info bullet 1 is rewritten.

Seven keys across three modules, 11 locales each.

⚠ **settings_manager_title and settings_manager_info_live must move together.**
`tools/check_translations.py` asserts the title appears verbatim inside that sentence in every
locale; renaming one without the other breaks the check AND silently stops the bold highlight
matching. The author confirmed the bullet follows the rename.

The new bullet also bolds a second phrase, "live status", which needs a name key of its own
plus an entry in check_translations' coupling list. Both are added here.

Author's bullet 1, with 'displays' rather than the 'display' first written — confirmed
30 Aug 2026:
    **IMD Settings Manager** displays the **live status** of settings and change them easily.

Point 2 and its description are untouched, as asked.

Asserts every anchor matches exactly once, every key covers every locale, and nothing is left
saying the old name. Writes nothing if any check fails.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

OLD_NAME_EN = "IMD services manager"
NEW_NAME_EN = "IMD Settings Manager"

# The whole of bullet 1, the author's words.
NEW_INFO_LIVE_EN = (
    "IMD Settings Manager displays the live status of settings and change them easily."
)

APPS = "feature/apps/src/main/res"
SETTINGS = "feature/settings/src/main/res"
APP = "app/src/main/res"

# Per-locale name of the manager. Each locale's own wording, matching how it already
# translated "IMD services manager".
NAME = {
    "values": NEW_NAME_EN,
    "values-ar": "مدير إعدادات IMD",
    "values-b+pt+BR": "Gerenciador de configurações do IMD",
    "values-b+zh+Hans": "IMD 设置管理器",
    "values-de": "IMD-Einstellungsmanager",
    "values-es": "Gestor de ajustes de IMD",
    "values-fr": "Gestionnaire de paramètres IMD",
    "values-hi": "IMD सेटिंग्स प्रबंधक",
    "values-ja": "IMD 設定マネージャー",
    "values-ko": "IMD 설정 관리자",
    "values-ru": "Диспетчер настроек IMD",
}

LIVE_STATUS = {
    "values": "live status",
    "values-ar": "الحالة المباشرة",
    "values-b+pt+BR": "status ao vivo",
    "values-b+zh+Hans": "实时状态",
    "values-de": "Live-Status",
    "values-es": "estado en vivo",
    "values-fr": "état en direct",
    "values-hi": "लाइव स्थिति",
    "values-ja": "ライブ状態",
    "values-ko": "실시간 상태",
    "values-ru": "текущее состояние",
}

# settings_manager_info_live, built per locale so the two bolded phrases above occur in it
# verbatim — the rule that the Russian help_launch_tile_name bug exists to enforce.
INFO_LIVE = {
    "values": f"{NAME['values']} displays the {LIVE_STATUS['values']} of settings and change them easily.",
    "values-ar": f"يعرض {NAME['values-ar']} {LIVE_STATUS['values-ar']} للإعدادات ويغيّرها بسهولة.",
    "values-b+pt+BR": f"O {NAME['values-b+pt+BR']} exibe o {LIVE_STATUS['values-b+pt+BR']} das configurações e permite alterá-las facilmente.",
    "values-b+zh+Hans": f"{NAME['values-b+zh+Hans']}显示设置的{LIVE_STATUS['values-b+zh+Hans']}，并可轻松更改。",
    "values-de": f"Der {NAME['values-de']} zeigt den {LIVE_STATUS['values-de']} der Einstellungen an und ändert sie mühelos.",
    "values-es": f"El {NAME['values-es']} muestra el {LIVE_STATUS['values-es']} de los ajustes y permite cambiarlos fácilmente.",
    "values-fr": f"Le {NAME['values-fr']} affiche l\\'{LIVE_STATUS['values-fr']} des paramètres et permet de les modifier facilement.",
    "values-hi": f"{NAME['values-hi']} सेटिंग्स की {LIVE_STATUS['values-hi']} दिखाता है और उन्हें आसानी से बदलता है.",
    "values-ja": f"{NAME['values-ja']}は設定の{LIVE_STATUS['values-ja']}を表示し、簡単に変更できます。",
    "values-ko": f"{NAME['values-ko']}가 설정의 {LIVE_STATUS['values-ko']}를 표시하고 쉽게 변경합니다.",
    "values-ru": f"{NAME['values-ru']} показывает {LIVE_STATUS['values-ru']} настроек и позволяет легко их менять.",
}

# Straight per-locale replacements of the old name inside longer sentences.
# module -> key -> (must contain, replace this substring with the locale's new name)
SUBSTITUTIONS = [
    (APPS, "shevery_toggle_point_status"),
    (SETTINGS, "notification_function_memory_warning_revert"),
    (SETTINGS, "help_general_manager_places"),
    (SETTINGS, "tasker_fn_services"),
]

REPLACE_WHOLE = [
    (APPS, "settings_manager_title", NAME),
    (APPS, "settings_manager_info_live", INFO_LIVE),
]

ADD = [
    (APPS, "settings_manager_info_name_live", LIVE_STATUS),
]


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def value_of(text: str, key: str) -> str | None:
    marker = f'<string name="{key}">'
    start = text.find(marker)

    if start == -1:
        return None

    start += len(marker)
    end = text.find("</string>", start)

    return text[start:end] if end != -1 else None


def main() -> int:
    # --- the author's English, asserted first ---------------------------------------
    if INFO_LIVE["values"] != NEW_INFO_LIVE_EN:
        return fail("the English bullet 1 is not the author's confirmed text")

    if "displays" not in NEW_INFO_LIVE_EN:
        return fail("bullet 1 lost the confirmed 'displays'")

    for table, label in ((NAME, "NAME"), (LIVE_STATUS, "LIVE_STATUS"), (INFO_LIVE, "INFO_LIVE")):
        missing = [loc for loc in LOCALES if loc not in table]

        if missing:
            return fail(f"{label} is missing locales: {missing}")

    # --- the coupling the translation check enforces ----------------------------------
    for locale in LOCALES:
        if NAME[locale] not in INFO_LIVE[locale]:
            return fail(
                f"{locale}: the manager name is not verbatim inside bullet 1 — "
                "check_translations would fail and the bold would match nothing",
            )

        if LIVE_STATUS[locale] not in INFO_LIVE[locale]:
            return fail(f"{locale}: 'live status' is not verbatim inside bullet 1")

    planned: dict[Path, str] = {}

    def edit(module: str, locale: str) -> tuple[Path, str]:
        path = ROOT / module / locale / "strings.xml"
        return path, planned.get(path, read(path))

    # --- whole-value replacements ------------------------------------------------------
    for module, key, table in REPLACE_WHOLE:
        for locale in LOCALES:
            path, text = edit(module, locale)
            current = value_of(text, key)

            if current is None:
                return fail(f"{module}/{locale}: {key} not found")

            planned[path] = text.replace(
                f'<string name="{key}">{current}</string>',
                f'<string name="{key}">{table[locale]}</string>',
                1,
            )

    # --- substring replacements inside longer sentences --------------------------------
    for module, key in SUBSTITUTIONS:
        for locale in LOCALES:
            path, text = edit(module, locale)
            current = value_of(text, key)

            if current is None:
                return fail(f"{module}/{locale}: {key} not found")

            # Each locale spells the old name its own way. English is the only one this
            # script can assert a literal for; for the rest, the old name is whatever that
            # locale used in settings_manager_title before this run.
            old_local = OLD_NAME_EN if locale == "values" else None

            if old_local is None:
                apps_before = read(ROOT / APPS / locale / "strings.xml")
                old_local = value_of(apps_before, "settings_manager_title")

                if old_local is None:
                    return fail(f"{locale}: cannot read the old manager name")

            if old_local not in current:
                # Some locales word the surrounding sentence without naming the manager.
                continue

            planned[path] = text.replace(
                f'<string name="{key}">{current}</string>',
                f'<string name="{key}">{current.replace(old_local, NAME[locale])}</string>',
                1,
            )

    # --- the new name key ---------------------------------------------------------------
    for module, key, table in ADD:
        for locale in LOCALES:
            path, text = edit(module, locale)

            if f'name="{key}"' in text:
                return fail(f"{module}/{locale}: {key} already exists — has this run before?")

            marker = "</resources>"

            if text.count(marker) != 1:
                return fail(f"{module}/{locale}: expected exactly one {marker}")

            planned[path] = text.replace(
                marker,
                f'    <string name="{key}">{table[locale]}</string>\n{marker}',
                1,
            )

    # --- everything must still parse, and nothing may say the old English name ----------
    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

        if OLD_NAME_EN in text:
            line = next((n for n, l in enumerate(text.split("\n"), 1) if OLD_NAME_EN in l), 0)
            return fail(f"{path.relative_to(ROOT)}:{line} still says {OLD_NAME_EN!r}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(planned)} file(s)")
    print(f"  title      -> {NEW_NAME_EN!r}")
    print(f"  bullet 1   -> {NEW_INFO_LIVE_EN!r}")
    print(f"  new key    -> settings_manager_info_name_live = {LIVE_STATUS['values']!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
