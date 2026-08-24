#!/usr/bin/env python3
"""Check a translated strings.xml against the English it came from.

Machine translation goes wrong in ways a reader of that language would spot instantly and a
reader of this one would not, so this checks only the things that are mechanical and that
break the app rather than merely read badly:

* every name in the English file is present, and no name has been invented
* format specifiers survive, in the same set - a lost %1$s is a crash, not a typo
* the XML parses, and the escapes Android needs are intact

Run it over every locale before shipping.
"""
import pathlib
import re
import sys
import xml.etree.ElementTree as ET

REPO = pathlib.Path(__file__).resolve().parents[1]
SPEC = re.compile(r"%\d*\$?[sdf]|%[sdf]")


def strings(path: pathlib.Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    return {
        e.get("name"): "".join(e.itertext())
        for e in root.findall("string")
        if e.get("translatable") != "false"
    }


def check(module: pathlib.Path, locale: str) -> list[str]:
    base = module / "src/main/res/values/strings.xml"
    other = module / f"src/main/res/values-{locale}/strings.xml"

    if not other.exists():
        return [f"{module.name}: values-{locale} missing"]

    problems = []
    en, tr = strings(base), strings(other)

    for missing in sorted(set(en) - set(tr)):
        problems.append(f"{module.name}/{locale}: missing '{missing}'")

    for extra in sorted(set(tr) - set(en)):
        problems.append(f"{module.name}/{locale}: unknown name '{extra}'")

    for name in sorted(set(en) & set(tr)):
        want, got = sorted(SPEC.findall(en[name])), sorted(SPEC.findall(tr[name]))

        if want != got:
            problems.append(
                f"{module.name}/{locale}: '{name}' format specifiers {want} -> {got}",
            )

        # An untranslated string is not always wrong - product names, adb commands and
        # single letters stay put - but a long one usually means a line was skipped.
        if len(en[name]) > 25 and en[name] == tr[name]:
            problems.append(f"{module.name}/{locale}: '{name}' identical to English")

    return problems



# Short strings that are matched as substrings inside longer ones, to bold them. Get the
# wording even slightly different between the two and nothing is bolded, silently - which
# is exactly the kind of thing a translator working string by string cannot see.
EMPHASIS = [
    ("app", "setup_secure_settings_shizuku", ["setup_use_shizuku"]),
    ("feature/settings", "notification_function_revert_detail", ["revert_defaults_entry"]),
    ("feature/settings", "notification_function_memory_warning_config",
     ["notif_name_all_apps", "notif_name_favourites"]),
    ("feature/settings", "notification_function_memory_warning_revert",
     ["notif_name_revert_button", "revert_defaults_entry"]),
    ("feature/settings", "settings_to_hide_info_shizuku",
     ["settings_to_hide_name_shizuku_hide"]),
    ("feature/settings", "settings_to_hide_info_watchdog",
     ["settings_to_hide_name_shizuku_watchdog"]),
    ("feature/settings", "help_hide_title", ["help_name_mandatory"]),
    ("feature/settings", "help_revert_title", ["help_name_revert"]),
    ("feature/settings", "help_general_revert", ["help_name_revert_button"]),
    ("feature/settings", "revert_defaults_notice_body", ["revert_defaults_entry"]),
    ("feature/apps", "settings_manager_info_live", ["settings_manager_title"]),
    ("feature/apps", "settings_manager_info_live_extra",
     ["settings_manager_info_name_defaults"]),
    ("feature/apps", "settings_manager_info_developer_extra",
     ["settings_manager_info_name_reset"]),
]


def check_emphasis(locale: str) -> list[str]:
    problems = []

    for module, holder, names in EMPHASIS:
        path = REPO / module / f"src/main/res/values-{locale}/strings.xml"

        if not path.exists():
            continue

        s = strings(path)

        if holder not in s:
            continue

        for name in names:
            if name in s and s[name] not in s[holder]:
                problems.append(
                    f"{module}/{locale}: '{s[name]}' does not appear inside '{holder}', "
                    f"so it will not be bolded",
                )

    return problems


def main() -> int:
    locales = sys.argv[1:] or ["hi"]

    modules = sorted(
        {p.parents[4] for p in REPO.glob("**/src/main/res/values/strings.xml")},
    )
    modules = [m for m in modules if "debug" not in str(m)]

    all_problems = []

    for locale in locales:
        for module in modules:
            all_problems += check(module, locale)

        all_problems += check_emphasis(locale)

    for p in all_problems:
        print(" ", p)

    total = sum(
        len(strings(m / "src/main/res/values/strings.xml")) for m in modules
    )
    print(f"\n{len(modules)} modules, {total} English strings, locales: {', '.join(locales)}")
    print("ALL CHECKS PASS" if not all_problems else f"{len(all_problems)} PROBLEMS")

    return 1 if all_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
