#!/usr/bin/env python3
"""
v3-r2 — the `Unhide settings and services` intent, in the Tasker integration page.

The author's new intent, and the pair of the `Hide settings and services` entry that has been
there since the integration was added. It replaces `Revert using memory` in the **picker** —
the old action string still works, so nobody's existing macro breaks.

It is also no longer conditional. The old entry appeared only under the memory function,
because offering it in the other mode would have documented a button the user had not chosen.
This one follows whichever Unhiding framework is set, so it is always the right thing to offer.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "feature/settings/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

KEY = "tasker_fn_unhide"

AUTHOR = "Unhide settings and services"

ADD = {
    "values": AUTHOR,
    "values-ar": "إظهار الإعدادات والخدمات",
    "values-b+pt+BR": "Reexibir configurações e serviços",
    "values-b+zh+Hans": "取消隐藏设置和服务",
    "values-de": "Einstellungen und Dienste wieder einblenden",
    "values-es": "Mostrar ajustes y servicios",
    "values-fr": "Réafficher les paramètres et les services",
    "values-hi": "सेटिंग और सेवाएँ दिखाएँ",
    "values-ja": "設定とサービスを再表示",
    "values-ko": "설정 및 서비스 다시 표시",
    "values-ru": "Показать настройки и службы",
}

PAGE = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "TaskerIntegrationPage.kt"
)

PAGE_OLD = """        // Only when the memory function is the one in use. The trigger works regardless, but
        // offering it in any other mode would be documenting a button the user has not chosen.
        if (notificationFunction == NotificationFunction.Memory) {
            BroadcastSection(
                title = stringResource(R.string.tasker_fn_revert_memory),
                packageName = packageName,
                action = TaskerIntegration.ACTION_REVERT_USING_MEMORY,
            )
        }
"""

PAGE_NEW = """        // ⚠ **Not conditional any more, and that is the change.** Its predecessor appeared
        // only under the memory function, because offering it in the other mode would have
        // documented a button the user had not chosen. This one settles whatever is
        // outstanding the way the current Unhiding framework says, so it is the right thing
        // to offer under either — and it is the route that answers the old objection to the
        // memory function, that a lost notification leaves no way back.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_unhide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_UNHIDE_SETTINGS,
        )
"""

ANCHOR = '    <string name="tasker_fn_hide">'


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


def main() -> int:
    problems: list[str] = []

    missing = [locale for locale in LOCALES if locale not in ADD]

    if missing:
        problems.append(f"{KEY}: missing {missing}")

    if ADD.get("values") != AUTHOR:
        problems.append(f"{KEY}: English is {ADD.get('values')!r}, author wrote {AUTHOR!r}")

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        if re.search(rf'name="{KEY}"', text):
            problems.append(f"{locale}: {KEY} already exists")

        match = re.search(r'^    <string name="tasker_fn_hide">.*$', text, re.M)

        if match is None:
            problems.append(f"{locale}: tasker_fn_hide anchor not found")

            continue

        line = f'    <string name="{KEY}">{escape(ADD[locale])}</string>\n'

        staged[path] = text.replace(match.group(0), line + match.group(0), 1)

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}: does not parse — {error}")

    page = ROOT / PAGE
    page_text = page.read_text(encoding="utf-8")

    if page_text.count(PAGE_OLD) != 1:
        problems.append(
            f"{PAGE}: expected 1 of the conditional memory section, "
            f"found {page_text.count(PAGE_OLD)}",
        )
    else:
        page_text = page_text.replace(PAGE_OLD, PAGE_NEW, 1)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    page.write_text(page_text, encoding="utf-8")

    print(f"ok — {KEY} across {len(staged)} locales, and the page entry swapped")

    return 0


if __name__ == "__main__":
    sys.exit(main())
