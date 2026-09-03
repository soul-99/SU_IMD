#!/usr/bin/env python3
"""
v3-r2e — "revert" becomes "restore" in the toasts, and four toasts are removed.

The author's rules:

* **restore/restored everywhere in the hide/unhide toasts**, "except for when explicitly revert
  to default is run from anywhere other than reverts. like IMD services manager/ intent/ revert
  to default qs toggle."
* Remove the three revert-failure toasts and the Shizuku wait toast.
* **"only hiding ones say IMD+ other say IMD"** — so the three unreachable
  `toast_auto_done_reverted_*` go, and IMD+ unhides keep using the IMD sentences.
* A new one for the Favourites button when there is nothing outstanding:
  `'IMD: No hidden settings to restore'` (the author confirmed the lower-case *no* was a typo).

**Two sentences for the defaults, not one, and that is the whole point of the exception.** The
named `Revert to default` function drives the device to a configured state the user nominated —
it *reverts*. A framework-following unhide under `UnhidingFramework.RevertToDefault` reaches the
same code but is the way back from a hide — it *restores*. Same work, two different things to
say about it, so `toast_done_reverted_defaults` stays exactly as the author wrote it and
`toast_done_restored_defaults` joins it.

⚠ **In several locales the old translation already said "restored".** German
`wiederhergestellt`, Spanish `restaurados`, Japanese `復元`, Korean `복원되었습니다`, Russian
`восстановлены` — the English distinction did not survive into them, so the *renamed* memory
keys keep those translations unchanged and only the five locales that said "revert" are
reworded. Spanish is the one locale where the two defaults sentences would have collided, so
its `reverted` form moves to `revertidos`.

**The failure toasts go because every case they covered already raises a notification** —
`OverlayRestoreRunner.report()` for overlay access, `buildShizukuRevertFailedNotification` for
Shizuku, and the overlay one names Shizuku as the cause when both fail. Verified before removing
them; nothing becomes silent that was not already on screen for longer.

Computes every edit in memory, asserts each match count and locale, and writes nothing if
anything fails.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMON = ROOT / "common/src/main/res"
APPS = ROOT / "feature/apps/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# Gone, in every locale. The three failures and the three IMD+ unhide sentences.
DROP_COMMON = [
    "revert_failed_shizuku_toast",
    "revert_failed_overlay_toast",
    "revert_failed_shizuku_and_overlay_toast",
    "toast_auto_done_reverted_defaults",
    "toast_auto_done_reverted_memory",
    "toast_auto_done_reverted_memory_for",
]

DROP_APPS = ["settings_manager_shizuku_wait"]

# old key -> new key. The `_for` variant's value is derived from its base so the bracket form,
# which differs by locale (full-width in Chinese, an LRM in Arabic), cannot be retyped wrongly.
RENAME = {
    "toast_done_reverted_memory": "toast_done_restored_memory",
    "toast_done_reverted_memory_for": "toast_done_restored_memory_for",
}

RESTORED_MEMORY = {
    "values": "IMD: Settings restored from memory",
    # Unchanged from the old text: these five already said "restored".
    "values-de": "IMD: Einstellungen aus dem Speicher wiederhergestellt",
    "values-es": "IMD: ajustes restaurados desde la memoria",
    "values-ja": "IMD: 設定をメモリーから復元しました",
    "values-ko": "IMD: 설정이 메모리에서 복원되었습니다",
    "values-ru": "IMD: настройки восстановлены из памяти",
    # Reworded: these said revert/return.
    "values-ar": "‏IMD: تمت استعادة الإعدادات من الذاكرة",
    "values-b+pt+BR": "IMD: configurações restauradas da memória",
    "values-b+zh+Hans": "IMD：设置已从记忆中恢复",
    "values-fr": "IMD : paramètres restaurés depuis la mémoire",
    "values-hi": "IMD: सेटिंग मेमोरी से बहाल की गईं",
}

# Added beside the untouched `toast_done_reverted_defaults`.
RESTORED_DEFAULTS = {
    "values": "IMD: Settings restored to defaults",
    "values-ar": "‏IMD: تمت استعادة الإعدادات إلى الوضع الافتراضي",
    "values-b+pt+BR": "IMD: configurações restauradas para os padrões",
    "values-b+zh+Hans": "IMD：设置已恢复为默认值",
    "values-de": "IMD: Einstellungen auf den Standard wiederhergestellt",
    "values-es": "IMD: ajustes restaurados a los valores predeterminados",
    "values-fr": "IMD : paramètres restaurés aux valeurs par défaut",
    "values-hi": "IMD: सेटिंग डिफ़ॉल्ट पर बहाल की गईं",
    "values-ja": "IMD: 設定を既定値に復元しました",
    "values-ko": "IMD: 설정이 기본값으로 복원되었습니다",
    "values-ru": "IMD: настройки восстановлены к значениям по умолчанию",
}

NOTHING_TO_RESTORE = {
    "values": "IMD: No hidden settings to restore",
    "values-ar": "‏IMD: لا توجد إعدادات مخفية لاستعادتها",
    "values-b+pt+BR": "IMD: nenhuma configuração oculta para restaurar",
    "values-b+zh+Hans": "IMD：没有可恢复的隐藏设置",
    "values-de": "IMD: Keine ausgeblendeten Einstellungen zum Wiederherstellen",
    "values-es": "IMD: no hay ajustes ocultos que restaurar",
    "values-fr": "IMD : aucun paramètre masqué à restaurer",
    "values-hi": "IMD: बहाल करने के लिए कोई छिपी सेटिंग नहीं",
    "values-ja": "IMD: 復元する非表示の設定はありません",
    "values-ko": "IMD: 복원할 숨겨진 설정이 없습니다",
    "values-ru": "IMD: нет скрытых настроек для восстановления",
}

# ⚠ Spanish only. Every other locale already renders the two defaults sentences differently —
# zurückgesetzt/wiederhergestellt, 还原/恢复, 戻しました/復元しました — but Spanish said
# "restaurados" for both, which would have made the pair indistinguishable.
REVERTED_DEFAULTS_FIX = {
    "values-es": "IMD: ajustes revertidos a los valores predeterminados",
}

# The Favourites FAB's screen-reader description, which must stop saying "Revert to default"
# now that the button no longer does that. Not visible on screen; TalkBack reads it.
UNHIDE_SETTINGS = {
    "values": "Unhide settings",
    "values-ar": "إظهار الإعدادات",
    "values-b+pt+BR": "Reexibir configurações",
    "values-b+zh+Hans": "取消隐藏设置",
    "values-de": "Einstellungen einblenden",
    "values-es": "Mostrar ajustes",
    "values-fr": "Réafficher les paramètres",
    "values-hi": "सेटिंग दिखाएँ",
    "values-ja": "設定を再表示",
    "values-ko": "설정 다시 표시",
    "values-ru": "Показать настройки",
}

# The author's words, asserted against what actually goes in.
AUTHOR_ENGLISH = {
    "toast_nothing_to_restore": "IMD: No hidden settings to restore",
}

# Must survive untouched: it is the named function's own sentence, verbatim.
MUST_KEEP_ENGLISH = {
    "toast_done_reverted_defaults": "IMD: Settings reverted to defaults",
}


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


def value_of(text: str, key: str) -> str | None:
    match = re.search(rf'<string name="{key}">(.*?)</string>', text, re.S)

    return None if match is None else match.group(1)


def drop(text: str, key: str, locale: str, problems: list[str]) -> str:
    pattern = re.compile(rf'^    <string name="{key}">.*?</string>\n', re.M | re.S)

    found = pattern.findall(text)

    if len(found) != 1:
        problems.append(f"{locale}: {len(found)} of {key}, expected 1")

        return text

    return pattern.sub("", text, count=1)


def insert_after(text: str, anchor: str, key: str, value: str, locale: str,
                 problems: list[str]) -> str:
    if re.search(rf'name="{key}"', text):
        problems.append(f"{locale}: {key} already exists")

        return text

    match = re.search(rf'^    <string name="{anchor}">.*$', text, re.M)

    if match is None:
        problems.append(f"{locale}: {anchor} anchor not found")

        return text

    line = f'    <string name="{key}">{escape(value)}</string>'

    return text.replace(match.group(0), match.group(0) + "\n" + line, 1)


def main() -> int:
    problems: list[str] = []

    for name, table in (
        ("toast_done_restored_memory", RESTORED_MEMORY),
        ("toast_done_restored_defaults", RESTORED_DEFAULTS),
        ("toast_nothing_to_restore", NOTHING_TO_RESTORE),
        ("unhide_settings", UNHIDE_SETTINGS),
    ):
        missing = [locale for locale in LOCALES if locale not in table]

        if missing:
            problems.append(f"{name}: missing {missing}")

        expected = AUTHOR_ENGLISH.get(name)

        if expected is not None and table.get("values") != expected:
            problems.append(
                f"{name}: English is {table.get('values')!r}, author wrote {expected!r}",
            )

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = COMMON / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no common/strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        # The bracket form, taken from the file rather than retyped.
        base = value_of(text, "toast_done_reverted_memory")
        based_for = value_of(text, "toast_done_reverted_memory_for")

        if base is None or based_for is None:
            problems.append(f"{locale}: the memory toasts are not both there")

            continue

        if not based_for.startswith(base):
            problems.append(f"{locale}: {based_for!r} does not extend {base!r}")

            continue

        suffix = based_for[len(base):]

        for key in DROP_COMMON:
            text = drop(text=text, key=key, locale=locale, problems=problems)

        # Rename and reword the memory pair, in one substitution each so a half-done rename
        # cannot exist even transiently.
        for old, new, value in (
            ("toast_done_reverted_memory", RENAME["toast_done_reverted_memory"],
             escape(RESTORED_MEMORY[locale])),
            ("toast_done_reverted_memory_for", RENAME["toast_done_reverted_memory_for"],
             escape(RESTORED_MEMORY[locale]) + suffix),
        ):
            pattern = re.compile(rf'<string name="{old}">.*?</string>', re.S)

            found = pattern.findall(text)

            if len(found) != 1:
                problems.append(f"{locale}: {len(found)} of {old}")

                continue

            text = pattern.sub(f'<string name="{new}">{value}</string>', text, count=1)

        if locale in REVERTED_DEFAULTS_FIX:
            pattern = re.compile(
                r'(<string name="toast_done_reverted_defaults">).*?(</string>)', re.S,
            )

            if len(pattern.findall(text)) != 1:
                problems.append(f"{locale}: cannot find toast_done_reverted_defaults to fix")
            else:
                text = pattern.sub(
                    lambda m, v=escape(REVERTED_DEFAULTS_FIX[locale]):
                        m.group(1) + v + m.group(2),
                    text,
                    count=1,
                )

        text = insert_after(
            text=text,
            anchor="toast_done_reverted_defaults",
            key="toast_done_restored_defaults",
            value=RESTORED_DEFAULTS[locale],
            locale=locale,
            problems=problems,
        )

        text = insert_after(
            text=text,
            anchor="toast_done_restored_memory_for",
            key="toast_nothing_to_restore",
            value=NOTHING_TO_RESTORE[locale],
            locale=locale,
            problems=problems,
        )

        # The named function's English sentence is the author's and must be untouched.
        if locale == "values":
            for key, value in MUST_KEEP_ENGLISH.items():
                if f'<string name="{key}">{value}</string>' not in text:
                    problems.append(f"{locale}: {key} is no longer {value!r}")

        # The two defaults sentences have to be tellable apart in every locale.
        if value_of(text, "toast_done_reverted_defaults") == value_of(
            text, "toast_done_restored_defaults",
        ):
            problems.append(f"{locale}: the two defaults sentences are identical")

        staged[path] = text

    for locale in LOCALES:
        path = APPS / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no feature/apps strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        for key in DROP_APPS:
            text = drop(text=text, key=key, locale=locale, problems=problems)

        text = insert_after(
            text=text,
            anchor="revert_to_default",
            key="unhide_settings",
            value=UNHIDE_SETTINGS[locale],
            locale=locale,
            problems=problems,
        )

        staged[path] = text

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}/{path.parent.parent.parent.parent.name}: "
                            f"does not parse — {error}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(DROP_COMMON) + len(DROP_APPS)} keys dropped, {len(RENAME)} renamed and "
          f"reworded, 3 added, across {len(staged)} files")

    return 0


if __name__ == "__main__":
    sys.exit(main())
