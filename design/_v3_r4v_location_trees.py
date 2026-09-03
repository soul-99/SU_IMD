#!/usr/bin/env python3
"""v3-r4v — every location tree in the app names the row it actually points at.

    "update all the location tree in the app to be accurate, all the dialogs etc"

## What was wrong, checked row by row against `SettingsScreen`

| path | said | the row is actually called |
|---|---|---|
| `help_path_accessibility` | *Accessibility services to hide* | **Accessibility services managed by IMD** |
| `help_path_dooa` | *Display over other apps to hide* | **Display over other apps managed by IMD** |
| `help_path_hide` | *Settings to hide / unhide* | that, **or** *Default settings to hide* |
| `help_path_unhide` | *Revert to default configuration* | that, **or** *Settings to unhide + Revert to default configuration* |
| `help_path_manage_shizuku` | IMD Settings → Shizuku configuration → Manage Shizuku | correct, unchanged |
| `help_path_shizuku` | IMD Settings → Shizuku configuration | correct, unchanged |
| `help_path_help` | IMD Settings → About → Help (readme) | correct — the Help button is in About |

The first two are simply stale: those rows were renamed to *"… managed by IMD"* and the paths were
not. Three modules carry their own copy of each, and all six are corrected.

## ⚠ The last two are not stale — they are **right half the time**, which is worse

Both rows change their label with the unhiding framework, and `SettingsScreen` is where that is
decided:

* under **Memory** — *Settings to hide / unhide* and *Revert to default configuration*;
* under **Revert to default** — *Default settings to hide* and *Settings to unhide + Revert to
  default configuration*.

A single string cannot be accurate for a row whose name depends on a setting. So each gets a
second spelling and the two places that draw them are handed the framework: the help page and the
Revert-to-default notice. Both of their callers already have `userData` in hand.

⚠ **Nothing is renamed.** `help_path_hide` and `help_path_unhide` keep their names and their
current text, which are the Memory spellings — the new-install default — so every existing
translation stays attached to the string it was translated for. The new names carry the other
spelling.

⚠ **The translations are now behind on the two corrected strings**, and are left that way: the
author's standing rule is that translation happens in one pass at the end. The corrected English
is what the checker compares against, so the drift stays visible rather than being papered over.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP_SETTINGS = "feature/app-settings/src/main/res/values/strings.xml"

APPS = "feature/apps/src/main/res/values/strings.xml"

SETTINGS = "feature/settings/src/main/res/values/strings.xml"

HELP = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/help/SetupHelp.kt"

NOTICE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsNoticeDialog.kt"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

MAIN = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- The two stale rows, in all three modules ----------------
    (
        APP_SETTINGS,
        '<string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services to hide</string>',
        '<string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services managed by IMD</string>',
    ),
    (
        APP_SETTINGS,
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>',
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps managed by IMD</string>',
    ),
    (
        APPS,
        '<string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services to hide</string>',
        '<string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services managed by IMD</string>',
    ),
    (
        APPS,
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>',
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps managed by IMD</string>',
    ),
    (
        SETTINGS,
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>',
        '<string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps managed by IMD</string>',
    ),
    (
        SETTINGS,
        '<string name="help_path_accessibility">IMD Settings → Default IMD settings → Accessibility services to hide</string>',
        '<string name="help_path_accessibility">IMD Settings → Default IMD settings → Accessibility services managed by IMD</string>',
    ),
    # ---------------- The two framework-dependent rows gain their other spelling ----------
    (
        SETTINGS,
        '<string name="help_path_hide">IMD Settings → Default IMD settings → Settings to hide / unhide</string>',
        '<string name="help_path_hide">IMD Settings → Default IMD settings → Settings to hide / unhide</string>\n'
        '    <string name="help_path_hide_defaults">IMD Settings → Default IMD settings → Default settings to hide</string>',
    ),
    (
        SETTINGS,
        '<string name="help_path_unhide">IMD Settings → Default IMD settings → Revert to default configuration</string>',
        '<string name="help_path_unhide">IMD Settings → Default IMD settings → Revert to default configuration</string>\n'
        '    <string name="help_path_unhide_both">IMD Settings → Default IMD settings → Settings to unhide + Revert to default configuration</string>',
    ),
    # ---------------- The help page is told which framework it is describing ----------------
    (
        HELP,
        """@Composable
fun SetupHelpContent(modifier: Modifier = Modifier) {""",
        """@Composable
fun SetupHelpContent(
    modifier: Modifier = Modifier,
    /**
     * Which unhiding framework is in force.
     *
     * ⚠ **Two of the paths on this page name a row whose label depends on it**, so a page that
     * did not know it was right for one setting and wrong for the other — see the two
     * `help_path_*` pairs. It is not used for anything else here.
     */
    unhidingFramework: UnhidingFramework,
) {""",
    ),
    (
        HELP,
        """            path = stringResource(R.string.help_path_hide),""",
        """            path = stringResource(
                if (unhidingFramework == UnhidingFramework.Memory) {
                    R.string.help_path_hide
                } else {
                    R.string.help_path_hide_defaults
                },
            ),""",
    ),
    (
        HELP,
        """            path = stringResource(R.string.help_path_unhide),""",
        """            path = stringResource(
                if (unhidingFramework == UnhidingFramework.Memory) {
                    R.string.help_path_unhide
                } else {
                    R.string.help_path_unhide_both
                },
            ),""",
    ),
    (
        HELP,
        """fun SetupHelpDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {""",
        """fun SetupHelpDialog(
    modifier: Modifier = Modifier,
    /** Passed straight through to [SetupHelpContent] — see the parameter there. */
    unhidingFramework: UnhidingFramework,
    onDismissRequest: () -> Unit,
) {""",
    ),
    (
        HELP,
        """            SetupHelpContent(
                modifier = Modifier""",
        """            SetupHelpContent(
                unhidingFramework = unhidingFramework,
                modifier = Modifier""",
    ),
    (
        SCREEN,
        "        SetupHelpDialog(onDismissRequest = { showHelp = false })",
        "        SetupHelpDialog(\n"
        "            unhidingFramework = userData.unhidingFramework,\n"
        "            onDismissRequest = { showHelp = false },\n"
        "        )",
    ),
    # ---------------- And so is the Revert to default notice ----------------
    (
        NOTICE,
        """fun RevertDefaultsNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {""",
        """fun RevertDefaultsNoticeDialog(
    modifier: Modifier = Modifier,
    /**
     * Which unhiding framework is in force — the row this points at is named differently under
     * each, so one fixed path would be wrong for whichever the reader is not using.
     */
    unhidingFramework: UnhidingFramework,
    onDismissRequest: () -> Unit,
) {""",
    ),
    (
        NOTICE,
        """                text = stringResource(R.string.help_path_unhide),""",
        """                text = stringResource(
                    if (unhidingFramework == UnhidingFramework.Memory) {
                        R.string.help_path_unhide
                    } else {
                        R.string.help_path_unhide_both
                    },
                ),""",
    ),
    (
        MAIN,
        """                                        RevertDefaultsNoticeDialog(
                                            onDismissRequest =
                                                viewModel::acknowledgeRevertDefaultsNotice,
                                        )""",
        """                                        RevertDefaultsNoticeDialog(
                                            unhidingFramework =
                                                uiState.userData.unhidingFramework,
                                            onDismissRequest =
                                                viewModel::acknowledgeRevertDefaultsNotice,
                                        )""",
    ),
    (
        TRANSLATIONS,
        """    # r4s: what the create-shortcut dialog says when the lookup never lands.
    "shortcut_lookup_failed",""",
        """    # r4s: what the create-shortcut dialog says when the lookup never lands.
    "shortcut_lookup_failed",
    # r4v: the other spelling of the two rows whose label follows the unhiding framework.
    "help_path_hide_defaults",
    "help_path_unhide_both",""",
    ),
]

IMPORTS = [
    (HELP, "import com.android.geto.domain.model.UnhidingFramework"),
    (NOTICE, "import com.android.geto.domain.model.UnhidingFramework"),
]

AFTER = [
    (APP_SETTINGS, "Accessibility services managed by IMD", 1),
    (APP_SETTINGS, "Display over other apps managed by IMD", 1),
    (APPS, "Accessibility services managed by IMD", 1),
    (APPS, "Display over other apps managed by IMD", 1),
    (SETTINGS, "Accessibility services managed by IMD", 1),
    (SETTINGS, "Display over other apps managed by IMD", 1),
    (SETTINGS, 'name="help_path_hide_defaults"', 1),
    (SETTINGS, 'name="help_path_unhide_both"', 1),
    # ⚠ **No *path* still says the old row name.** Spelled as the whole path, because the old
    # phrase survives elsewhere on purpose: `accessibility_services` and `overlay_packages` are
    # the two *dialogs'* own titles, which are not what a location tree names — a tree names the
    # row you tap, and that row is called "… managed by IMD". A first draft asserted the phrase
    # was gone from the file entirely and was refused by exactly those two.
    (APP_SETTINGS, "\\u2192 Accessibility services to hide", 0),
    (APP_SETTINGS, "\\u2192 Display over other apps to hide", 0),
    (APPS, "\\u2192 Accessibility services to hide", 0),
    (APPS, "\\u2192 Display over other apps to hide", 0),
    (SETTINGS, "→ Accessibility services to hide", 0),
    (SETTINGS, "\\u2192 Display over other apps to hide", 0),
    (HELP, "unhidingFramework", 6),
    (HELP, "R.string.help_path_hide_defaults", 1),
    (HELP, "R.string.help_path_unhide_both", 1),
    (NOTICE, "R.string.help_path_unhide_both", 1),
    (SCREEN, "SetupHelpDialog(", 1),
    (MAIN, "unhidingFramework =", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ **The corrected names are read out of the settings screen, not typed from memory.**
    # If a row is renamed again, this is what fails rather than the paths quietly going stale
    # a second time.
    screen = staged[SCREEN]

    for row in (
        'name="accessibility_services_row"',
        'name="overlay_packages_row"',
    ):
        if row in screen:
            print(f"REFUSED: {SCREEN}\n  unexpected: {row}")
            return 1

    labels = (ROOT / SETTINGS).read_text(encoding="utf-8")

    for name, phrase in (
        ("accessibility_services_row", "Accessibility services\\nmanaged by IMD"),
        ("overlay_packages_row", "Display over other apps\\nmanaged by IMD"),
        ("settings_to_hide_both_label", "Settings to hide / unhide"),
        ("settings_to_hide_defaults_label", "Default settings to hide"),
        ("revert_defaults", "Revert to default configuration"),
    ):
        if f'<string name="{name}">{phrase}</string>' not in labels:
            print(f"REFUSED: {SETTINGS}\n  the row {name!r} is no longer {phrase!r}")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print("  ok        six stale paths corrected across three modules")
    print("  ok        the two framework-dependent rows have both spellings")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
