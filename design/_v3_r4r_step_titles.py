#!/usr/bin/env python3
"""v3-r4r — a setup step wears the author's own heading, in the theme's colour.

    "do display full dialog contents, their descriptions also and use heading i gave"
    "also display these titles in theme colour give it some flair like you did to the help/readme
     section headings"

The four headings, as written, with the double space in the fourth fixed at his instruction:

    Select accessibility services to hide / manage
    Select Display over other apps to hide / manage
    Select settings to hide / unhide
    Setup auto unhide settings service

## ⚠ Nothing is trimmed from the bodies

*"display full dialog contents, their descriptions also"* - flat mode never removed anything, and
this changes only the line at the top. Every description, note and system-settings button each
dialog draws in Settings is drawn in its setup step, because it is the same composable.

## The colour is a rule, not a fifth parameter

`SettingsPage` already knows it is `flat`; the two list dialogs already know `onSkip != null`. So
the heading colour follows from what the composable already has, and a step cannot end up with
the author's wording in the wrong colour because somebody forgot an argument.

`primary` with `titleLarge` is what the Shizuku setup page already uses for its own heading, and
it is the same accent the help page's `SubHeading` and `HelpPath` use - so the flair he is asking
for is the one already in the app rather than a new one.

## The strings live in :app

The setup flow resolves them and passes them down, so they sit beside `setup_next` and the other
onboarding strings rather than in a feature module that has no idea a setup flow exists.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP_STRINGS = "app/src/main/res/values/strings.xml"

PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsPage.kt"

ACCESSIBILITY = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AccessibilityServicesDialog.kt"

OVERLAY = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/OverlayPackagesDialog.kt"

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"

UNHIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhidePage.kt"

TRANSLATIONS = "tools/check_translations.py"

STEP_TITLE_DOC = '''    /**
     * The heading this step wears, replacing the one this dialog carries in Settings.
     *
     * Null everywhere but the setup flow. Drawn in the theme's `primary`, which is the accent
     * the Shizuku setup page's heading and the help page's own sub-headings already use.
     */
    stepTitle: String? = null,
'''

EDITS: list[tuple[str, str, str]] = [
    # ---- the four headings ----
    (
        APP_STRINGS,
        """    <string name="setup_next">Next</string>""",
        """    <!-- The four configuration steps' headings, the author's own wording. -->
    <string name="setup_step_accessibility">Select accessibility services to hide / manage</string>
    <string name="setup_step_overlay">Select Display over other apps to hide / manage</string>
    <string name="setup_step_settings_to_hide">Select settings to hide / unhide</string>
    <string name="setup_step_auto_unhide">Setup auto unhide settings service</string>
    <string name="setup_next">Next</string>""",
    ),
    (
        TRANSLATIONS,
        """    # r4r: the setup flow's Skip and Next.""",
        """    # r4r: the four configuration steps' headings.
    "setup_step_accessibility",
    "setup_step_overlay",
    "setup_step_settings_to_hide",
    "setup_step_auto_unhide",
    # r4r: the setup flow's Skip and Next.""",
    ),
    # ---- SettingsPage colours its title when flat ----
    (
        PAGE,
        """                Text(
                    modifier = Modifier.weight(1f),
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                )""",
        """                Text(
                    modifier = Modifier.weight(1f),
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                    // ⚠ **A rule, not a parameter.** The page already knows it is a setup step,
                    // so its heading cannot end up in the wrong colour because a caller forgot
                    // an argument. primary is what the Shizuku setup page's own heading uses.
                    color = if (flat) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        LocalContentColor.current
                    },
                )""",
    ),
    # ---- accessibility ----
    (
        ACCESSIBILITY,
        """    onSkip: (() -> Unit)? = null,""",
        STEP_TITLE_DOC + """    onSkip: (() -> Unit)? = null,""",
    ),
    (
        ACCESSIBILITY,
        """                text = stringResource(R.string.accessibility_services),
                style = MaterialTheme.typography.titleLarge,""",
        """                text = stepTitle ?: stringResource(R.string.accessibility_services),
                style = MaterialTheme.typography.titleLarge,
                color = if (stepTitle != null) {
                    MaterialTheme.colorScheme.primary
                } else {
                    LocalContentColor.current
                },""",
    ),
    # ---- overlay ----
    (
        OVERLAY,
        """    onSkip: (() -> Unit)? = null,""",
        STEP_TITLE_DOC + """    onSkip: (() -> Unit)? = null,""",
    ),
    (
        OVERLAY,
        """                text = stringResource(R.string.overlay_packages),
                style = MaterialTheme.typography.titleLarge,""",
        """                text = stepTitle ?: stringResource(R.string.overlay_packages),
                style = MaterialTheme.typography.titleLarge,
                color = if (stepTitle != null) {
                    MaterialTheme.colorScheme.primary
                } else {
                    LocalContentColor.current
                },""",
    ),
    # ---- settings to hide ----
    (
        HIDE,
        """        title = if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.settings_to_hide_both_label)
        } else {
            stringResource(R.string.settings_to_hide_defaults_label)
        },""",
        """        title = stepTitle ?: if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.settings_to_hide_both_label)
        } else {
            stringResource(R.string.settings_to_hide_defaults_label)
        },""",
    ),
    # ---- auto unhide ----
    (
        UNHIDE,
        """        title = stringResource(R.string.auto_unhide_title),""",
        """        title = stepTitle ?: stringResource(R.string.auto_unhide_title),""",
    ),
]

IMPORTS = [
    (PAGE, "import androidx.compose.material3.LocalContentColor"),
    (ACCESSIBILITY, "import androidx.compose.material3.LocalContentColor"),
    (OVERLAY, "import androidx.compose.material3.LocalContentColor"),
]

AFTER = [
    (APP_STRINGS, "setup_step_", 4),
    # Three: the outer modifier, the new title colour, and the footer arrangement.
    (PAGE, "if (flat) {", 3),
    # Three each: the declaration, the elvis on the title text, and the colour test.
    (ACCESSIBILITY, "stepTitle", 3),
    (OVERLAY, "stepTitle", 3),
    # Two each: the declaration inserted below, and the elvis on the container's title.
    (HIDE, "stepTitle", 2),
    (UNHIDE, "stepTitle", 2),
    (TRANSLATIONS, '"setup_step_accessibility"', 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

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
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    # The two SettingsPage dialogs need the parameter declared as well as used.
    for relative, anchor in (
        (HIDE, "    overlayBlockedPaths: List<String>?,"),
        (UNHIDE, "    onDismissRequest: () -> Unit,"),
    ):
        if staged[relative].count(anchor) != 1:
            print(f"REFUSED: {relative}\n  {anchor.strip()!r} is not unique")
            return 1

        staged[relative] = staged[relative].replace(
            anchor,
            STEP_TITLE_DOC + anchor,
            1,
        )

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {APP_STRINGS}  :: four headings, the double space fixed")
    print(f"  ok        {PAGE}  :: a flat page's heading is primary")
    print("  ok        all four dialogs take stepTitle")
    print(f"  ok        {TRANSLATIONS}  :: deferred")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS) + 2} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
