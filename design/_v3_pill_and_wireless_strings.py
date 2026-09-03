#!/usr/bin/env python3
"""
v3 — the seven English strings this round needs, and their deferral.

All seven are the author's own words and go in verbatim, including the leading "1. " and
"2. " he wrote inside the two notice points. They are numbered *in the string* rather than
composed from `shizuku_help_bullet` because that is how he wrote them, and the house rule is
that anything he put between single quotes is not touched — a composer would have to strip his
numbers to avoid printing them twice.

Where each one goes:

  feature/settings
    restore_wireless_also        the nested checkbox under Wireless debugging in
                                 Settings to hide/unhide, drawn only under the memory
                                 unhiding framework
    restore_wireless_notice_1    the two-point popup that checkbox raises on the way on
    restore_wireless_notice_2
    wireless_private_wifi_notice the *different*, shorter popup the Revert to default
                                 configuration dialog raises when its Wireless debugging
                                 switch is turned on. Deliberately not the two-point one:
                                 point 1 says IMD "does not restore it on unhiding", which is
                                 false in that dialog — that switch is exactly what restores
                                 it. The author confirmed the split.

  feature/apps
    settings_manager_all_on      the master pill below the last toggle
    settings_manager_all_off
    settings_manager_pending     the red line above the toggles, shown while IMD is holding
                                 something unreverted

⚠ **`settings_manager_pending` shares its opening words with `settings_manager_busy_hiding`**
("IMD hiding settings..."), and that is survivable only because the two are never drawn at
once: the busy note means work is running *now*, this one means a hide has finished and its
revert has not happened. The dialog suppresses this one while the busy note is up, on the
author's instruction.

All seven are added to `check_translations.py`'s DEFERRED set. Translations are deferred to
the end of the project on the author's standing instruction, and a deferral recorded there is
what keeps the check honest rather than merely quiet.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS_STRINGS = "feature/settings/src/main/res/values/strings.xml"
APPS_STRINGS = "feature/apps/src/main/res/values/strings.xml"
TRANSLATIONS = "tools/check_translations.py"

NEW_KEYS = [
    "restore_wireless_also",
    "restore_wireless_notice_1",
    "restore_wireless_notice_2",
    "wireless_private_wifi_notice",
    "settings_manager_all_on",
    "settings_manager_all_off",
    "settings_manager_pending",
]

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (SETTINGS_STRINGS, [
        (
            """    <string name="revert_defaults_wireless_debugging">Wireless debugging</string>
""",
            """    <string name="revert_defaults_wireless_debugging">Wireless debugging</string>

    <!--
      Wireless debugging, and the one setting in this app that is deliberately not put back.

      restore_wireless_also is a nested checkbox under the Wireless debugging row in
      Settings to hide/unhide, drawn only under the memory unhiding framework - under Revert
      to default the destination is that dialog's own Wireless debugging switch instead, and
      one question with two answers is worse than either.

      The two popups are different on purpose. The two-point one belongs to the checkbox;
      the one-liner belongs to the Revert to default switch, where point 1 would be false.
    -->
    <string name="restore_wireless_also">Restore wireless debugging also</string>
    <string name="restore_wireless_notice_1">1. By default IMD only hides wireless debugging and does not restore it on unhiding for public WiFi security reasons.</string>
    <string name="restore_wireless_notice_2">2. Only enable this if you always use private WiFi.</string>
    <string name="wireless_private_wifi_notice">Only enable this if you always use private WiFi.</string>
""",
            1,
        ),
    ]),
    (APPS_STRINGS, [
        (
            """    <string name="settings_manager_info_name_live">live status</string>
""",
            """    <string name="settings_manager_info_name_live">live status</string>

    <!-- The master pill below the last toggle. Two halves of one control, one long shape. -->
    <string name="settings_manager_all_on">All on</string>
    <string name="settings_manager_all_off">All off</string>

    <!--
      Shown above the toggles while IMD is holding something it has not reverted yet.

      ⚠ It opens with the same words as settings_manager_busy_hiding above and means
      something else: that one is work running right now, this one is a hide that finished
      with its revert still owing. They are never drawn together - the dialog suppresses this
      one while the busy note is up - which is the only reason the overlap is survivable.
    -->
    <string name="settings_manager_pending">IMD hiding settings currently, any changes made here before revert will be undone after settings restoration</string>
""",
            1,
        ),
    ]),
    (TRANSLATIONS, [
        (
            """    "prior_hide_restoring",
}""",
            """    "prior_hide_restoring",
    # The wireless debugging opt-in and its two popups, the Revert to default one-liner, and
    # the settings manager's master pill and pending-revert line.
    "restore_wireless_also",
    "restore_wireless_notice_1",
    "restore_wireless_notice_2",
    "wireless_private_wifi_notice",
    "settings_manager_all_on",
    "settings_manager_all_off",
    "settings_manager_pending",
}""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Each key defined exactly once across the two files, and each one deferred. The first
    # catches a name already taken; the second catches a key added here and forgotten there,
    # which would fail check_translations the moment anybody ran it.
    settings = staged[ROOT / SETTINGS_STRINGS]
    apps = staged[ROOT / APPS_STRINGS]
    deferred = staged[ROOT / TRANSLATIONS]

    for key in NEW_KEYS:
        defined = (settings + apps).count(f'<string name="{key}">')

        if defined != 1:
            problems.append(f"{key}: defined {defined} times, expected 1")

        if f'"{key}",' not in deferred:
            problems.append(f"{key}: not in check_translations DEFERRED")

    # ⚠ An unescaped apostrophe in a values file is a build failure aapt reports and nothing
    # in the audit suite reproduces. None of these seven has one, and this is what says so if
    # a later edit to this script introduces one.
    for path in (ROOT / SETTINGS_STRINGS, ROOT / APPS_STRINGS):
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in staged[path].splitlines():
            if line in before or "<string name=" not in line:
                continue

            body = line.split(">", 1)[1].rsplit("</string>", 1)[0]

            if "'" in body.replace("\\'", ""):
                problems.append(
                    f"{path.relative_to(ROOT)}: unescaped apostrophe in {line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print(f"ok — {len(NEW_KEYS)} strings in, all seven deferred")

    return 0


if __name__ == "__main__":
    sys.exit(main())
