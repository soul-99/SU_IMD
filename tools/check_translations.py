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


# Keys the author has deliberately left untranslated for now.
#
# ⚠ **Empty since r29, and kept rather than deleted.** r29 translated all 150 of the keys this
# held, so there is no debt left for it to record — but the mechanism is the right one and the
# next batch of new strings will want it. A key that is never going to be translated does not
# belong here at all: give it translatable="false", which this checker already skips, the way
# the six Shizuku/Shevery step lines and support_view_github_button now do.
#
# ⚠ **His standing rule from r2b3 on: translation happens in one pass when everything is built.**
# Listing them here rather than copying English into eleven locales keeps the check honest — a
# missing translation stays visible as a deferral rather than being disguised as a translation
# that happens to be identical — and this set *is* the list that final pass works from.
DEFERRED: set[str] = set()


# The whole set Android understands after a backslash. Anything else is a typo, and a doubled
# backslash - legal in principle, meaning one literal backslash - has so far only ever been a value
# that went through an escaping pass twice.
VALID_AFTER_BACKSLASH = frozenset(
    [
        "n",
        "t",
        "u",
        "@",
        "?",
        "'",
        '"',
        "\\",
    ],
)

RAW_STRING = re.compile(r'<string\s+name="([^"]+)"[^>]*>(.*?)</string>', re.S)

HEX = frozenset("0123456789abcdefABCDEF")


def check_escapes(module: pathlib.Path, locale: str) -> list[str]:
    """Backslash escapes, read at the raw level where they actually live.

    \u26a0 **Deliberately not built on `strings()`.** That parses with ElementTree, which resolves
    XML entities and leaves backslash escapes alone as ordinary text - so a doubled backslash is
    invisible to it, and to every other check in this file. r29 lost a whole resource table to one.
    """
    path = module / f"src/main/res/values-{locale}/strings.xml"

    if not path.exists():
        return []

    problems = []

    for name, raw in RAW_STRING.findall(path.read_text(encoding="utf-8")):
        position = 0

        while position < len(raw):
            if raw[position] != "\\":
                position += 1

                continue

            following = raw[position + 1:position + 2]

            if following == "\\":
                problems.append(
                    f"{module.name}/{locale}: '{name}' has a doubled backslash - "
                    "almost always a value that was escaped twice",
                )

                break

            if following not in VALID_AFTER_BACKSLASH:
                problems.append(
                    f"{module.name}/{locale}: '{name}' has an escape Android does not "
                    f"understand: {raw[position:position + 2]!r}",
                )

                break

            if following == "u" and not set(raw[position + 2:position + 6]) <= HEX:
                problems.append(
                    f"{module.name}/{locale}: '{name}' has a truncated unicode escape: "
                    f"{raw[position:position + 6]!r}",
                )

                break

            position += 2

    return problems


def check(module: pathlib.Path, locale: str) -> list[str]:
    base = module / "src/main/res/values/strings.xml"
    other = module / f"src/main/res/values-{locale}/strings.xml"

    if not other.exists():
        return [f"{module.name}: values-{locale} missing"]

    problems = []
    en, tr = strings(base), strings(other)

    for missing in sorted(set(en) - set(tr) - DEFERRED):
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
    ("app", "setup_shizuku_once", ["setup_name_display_over_other_apps"]),
    ("feature/settings", "notification_function_revert_detail", ["revert_defaults_entry"]),
    # r29: SupportDialog underlines these two inside support_intro_3. The coupling is as old as
    # the dialog and was never listed, so a translation of either phrase that did not appear
    # inside that locale's own sentence would simply have underlined nothing.
    ("feature/settings", "support_intro_3",
     ["support_name_project", "support_name_alive"]),
    ("feature/settings", "notification_function_memory_warning_config",
     ["notif_name_all_apps", "notif_name_favourites"]),
    # notification_function_memory_warning_revert is no longer emphasised: as of v2.2 it
    # is a two-part list of which routes revert from memory and which do not, and a bolded
    # substring inside a list reads as one item mattering more than the others.
    ("feature/settings", "settings_to_hide_info_shizuku",
     ["settings_to_hide_name_shizuku_hide"]),
    ("feature/settings", "settings_to_hide_info_watchdog",
     ["settings_to_hide_name_shizuku_watchdog"]),
    ("feature/settings", "manage_overlay_notice", ["section_app_functions"]),
    ("feature/settings", "auto_revert_notice_scope", ["auto_revert_name_shortcuts"]),
    ("feature/settings", "auto_revert_notice_early", ["auto_revert_name_early"]),
    ("feature/settings", "help_hide_title", ["help_name_mandatory"]),
    ("feature/settings", "help_revert_title", ["help_name_revert"]),
    ("feature/settings", "help_general_revert", ["help_name_revert_button"]),
    ("feature/settings", "revert_defaults_notice_body", ["revert_defaults_entry"]),
    # v3: the Unhiding framework picker names the configuration it drives, and the
    # phrase has to be that locale's own revert_defaults or nothing is bolded.
    ("feature/settings", "unhiding_framework_revert_summary", ["revert_defaults"]),
    ("feature/settings", "settings_tab_notice", ["settings_tab_notice_name"]),
    ("feature/apps", "settings_manager_info_live",
     ["settings_manager_title", "settings_manager_info_name_live"]),
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
    # ⚠ **All ten by default since r29.** It used to be Hindi alone, which is how the handover
    # invoked it — so the number it printed was one locale's, and read as the whole app's.
    locales = sys.argv[1:] or [
        "hi", "ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "ja", "ko", "ru",
    ]

    modules = sorted(
        {p.parents[4] for p in REPO.glob("**/src/main/res/values/strings.xml")},
    )
    modules = [m for m in modules if "debug" not in str(m)]

    all_problems = []

    for locale in locales:
        for module in modules:
            all_problems += check(module, locale)

            all_problems += check_escapes(module, locale)

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
