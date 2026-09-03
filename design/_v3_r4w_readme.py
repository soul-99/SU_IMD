#!/usr/bin/env python3
"""v3-r4w — the help/readme page, to the template the author approved.

    "add the new template"

Five changes, all from his brief:

* **§3** — the title gains *" / Display over other apps"* after *accessibility services*; the body
  is his sentence verbatim; and it now shows **two** location trees instead of one.
* **§4** — *IMD SERVICES MANAGER* becomes *IMD SETTINGS MANAGER*, and *"Use this service manager"*
  becomes *"Use this settings manager"*. The third line already said *IMD Settings Manager* and is
  untouched.
* **§5** — the title becomes *Setup Shizuku configuration*, with the bracket dropped.
* **§6** — new: *Discover & setup automations*, three numbered items each followed by its tree.

## ⚠ `HelpSection` takes a list of paths, not a second parameter

Section 3 is the first to need two. `secondPath: String? = null` would have worked and would have
made section 7 need a third parameter; a list costs the same today and nothing tomorrow. Every
existing caller passes `listOf(one)`, which is why they all appear in the edits below.

## ⚠ The three new paths were read off the settings screen, not invented

* Auto unhide sits at the foot of **Default IMD settings**, under its own section divider.
* Auto hide sits in the section titled **IMD+ (needs background service)** — the bracket is part
  of the section's real name, not a gloss.
* IMD intents sits in **Advanced** and is really called **IMD intents (EXPERIMENTAL)**.

The script asserts each of those three labels is still what the settings strings say, so a rename
breaks this rather than quietly making the readme wrong again.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HELP = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/help/SetupHelp.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- HelpSection takes any number of paths ----------------
    (
        HELP,
        """private fun HelpSection(
    modifier: Modifier = Modifier,
    number: Int,
    title: AnnotatedString,
    path: String,
    body: String?,
    pathFirst: Boolean,
) {""",
        """private fun HelpSection(
    modifier: Modifier = Modifier,
    number: Int,
    title: AnnotatedString,
    /**
     * The menu path or paths this step is reached by.
     *
     * ⚠ **A list since r4w, because section 3 covers two rows.** A `secondPath` parameter would
     * have done the same job and left section 7 needing a third; this costs the same today and
     * nothing later.
     */
    paths: List<String>,
    body: String?,
    pathFirst: Boolean,
) {""",
    ),
    (
        HELP,
        """            if (pathFirst) {
                HelpPath(path = path)

                body?.let {
                    Spacer(modifier = Modifier.height(10.dp))

                    Text(text = it, style = MaterialTheme.typography.bodySmall)
                }
            } else {
                body?.let {
                    Text(text = it, style = MaterialTheme.typography.bodySmall)

                    Spacer(modifier = Modifier.height(10.dp))
                }

                HelpPath(path = path)
            }""",
        """            if (pathFirst) {
                HelpPaths(paths = paths)

                body?.let {
                    Spacer(modifier = Modifier.height(10.dp))

                    Text(text = it, style = MaterialTheme.typography.bodySmall)
                }
            } else {
                body?.let {
                    Text(text = it, style = MaterialTheme.typography.bodySmall)

                    Spacer(modifier = Modifier.height(10.dp))
                }

                HelpPaths(paths = paths)
            }""",
    ),
    (
        HELP,
        """/** The same colour and weight [HelpPath] uses, for a path inside a longer sentence. */""",
        """/** One or more paths, stacked, with a hair of space between them. */
@Composable
private fun HelpPaths(
    modifier: Modifier = Modifier,
    paths: List<String>,
) {
    Column(modifier = modifier) {
        paths.forEachIndexed { index, path ->
            if (index > 0) Spacer(modifier = Modifier.height(4.dp))

            HelpPath(path = path)
        }
    }
}

/** The same colour and weight [HelpPath] uses, for a path inside a longer sentence. */""",
    ),
    # ---------------- The four existing callers ----------------
    (
        HELP,
        """            path = stringResource(
                if (unhidingFramework == UnhidingFramework.Memory) {
                    R.string.help_path_hide
                } else {
                    R.string.help_path_hide_defaults
                },
            ),""",
        """            paths = listOf(
                stringResource(
                    if (unhidingFramework == UnhidingFramework.Memory) {
                        R.string.help_path_hide
                    } else {
                        R.string.help_path_hide_defaults
                    },
                ),
            ),""",
    ),
    (
        HELP,
        """            path = stringResource(
                if (unhidingFramework == UnhidingFramework.Memory) {
                    R.string.help_path_unhide
                } else {
                    R.string.help_path_unhide_both
                },
            ),""",
        """            paths = listOf(
                stringResource(
                    if (unhidingFramework == UnhidingFramework.Memory) {
                        R.string.help_path_unhide
                    } else {
                        R.string.help_path_unhide_both
                    },
                ),
            ),""",
    ),
    (
        HELP,
        """            path = stringResource(R.string.help_path_accessibility),""",
        """            // ⚠ **Two rows, two trees.** The step covers accessibility services *and*
            // Display over other apps since r4w, and a step that names one of the two places it
            // is asking about is worse than one that names neither.
            paths = listOf(
                stringResource(R.string.help_path_accessibility),
                stringResource(R.string.help_path_dooa),
            ),""",
    ),
    (
        HELP,
        """            path = stringResource(R.string.help_path_shizuku),""",
        """            paths = listOf(stringResource(R.string.help_path_shizuku)),""",
    ),
    # ---------------- Section 6 ----------------
    (
        HELP,
        """        HelpSection(
            number = 5,""",
        """        HelpSection(
            number = 5,""",
    ),
    (
        HELP,
        """            body = stringResource(R.string.help_shizuku_body),
            pathFirst = false,
        )
    }
}""",
        """            body = stringResource(R.string.help_shizuku_body),
            pathFirst = false,
        )

        AutomationsSection(number = 6)
    }
}

/**
 * The things IMD can be made to do on its own — the author's *"Discover & setup automations"*.
 *
 * ⚠ **A card of its own rather than three more numbered steps.** Nothing here has to be
 * configured for the app to work, which is what the five steps above have in common; these are
 * offered, and each is named with the place it lives so it can be found rather than described.
 */
@Composable
private fun AutomationsSection(
    modifier: Modifier = Modifier,
    number: Int,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(
                    R.string.help_numbered_title,
                    number,
                    stringResource(R.string.help_automations_title),
                ),
                style = MaterialTheme.typography.titleMedium,
            )

            AutomationItem(
                text = stringResource(R.string.help_automations_auto_unhide),
                path = stringResource(R.string.help_path_auto_unhide),
            )

            AutomationItem(
                text = stringResource(R.string.help_automations_auto_hide),
                path = stringResource(R.string.help_path_auto_hide),
            )

            AutomationItem(
                text = stringResource(R.string.help_automations_intents),
                path = stringResource(R.string.help_path_intents),
            )
        }
    }

    Spacer(modifier = Modifier.height(12.dp))
}

/** One automation and where it lives, the path indented under the line it belongs to. */
@Composable
private fun AutomationItem(text: String, path: String) {
    Spacer(modifier = Modifier.height(12.dp))

    Text(text = text, style = MaterialTheme.typography.bodySmall)

    Spacer(modifier = Modifier.height(4.dp))

    HelpPath(modifier = Modifier.padding(start = 16.dp), path = path)
}""",
    ),
    # ---------------- Strings ----------------
    (
        STRINGS,
        '<string name="help_accessibility_title">Setup Accessibility services to hide</string>',
        '<string name="help_accessibility_title">Setup Accessibility services / Display over other apps to hide</string>',
    ),
    (
        STRINGS,
        '<string name="help_accessibility_body">The app will not touch any accessibility service until you say which ones, then tick the ones that should be switched off while a locked-down app is open. They are switched back on when you revert.</string>',
        '<string name="help_accessibility_body">This app will not touch any accessibility services or Display over other apps (needs Shizuku), until you select which ones.</string>',
    ),
    (
        STRINGS,
        '<string name="help_shizuku_title">Setup Shizuku Start Intents (only if you use Shizuku)</string>',
        '<string name="help_shizuku_title">Setup Shizuku configuration</string>',
    ),
    (
        STRINGS,
        '<string name="help_general_manager_title">IMD SERVICES MANAGER</string>',
        '<string name="help_general_manager_title">IMD SETTINGS MANAGER</string>',
    ),
    (
        STRINGS,
        '<string name="help_general_manager">Use this service manager to quickly view the live status of your settings/services and also quickly toggle them on-off.</string>',
        '<string name="help_general_manager">Use this settings manager to quickly view the live status of your settings/services and also quickly toggle them on-off.</string>',
    ),
    (
        STRINGS,
        '<string name="help_general_manager_items">',
        '<string name="help_automations_title">Discover &amp; setup automations</string>\n'
        '    <string name="help_automations_auto_unhide">1.  Auto unhide settings</string>\n'
        '    <string name="help_automations_auto_hide">2.  Auto hide settings (needs background service)</string>\n'
        '    <string name="help_automations_intents">3.  IMD intents for Tasker/ Macrodroid... etc.</string>\n'
        '    <string name="help_path_auto_unhide">IMD Settings → Default IMD settings → Auto unhide settings</string>\n'
        '    <string name="help_path_auto_hide">IMD Settings → IMD+ (needs background service) → Auto hide settings</string>\n'
        '    <string name="help_path_intents">IMD Settings → Advanced → IMD intents (EXPERIMENTAL)</string>\n'
        '    <string name="help_general_manager_items">',
    ),
    (
        TRANSLATIONS,
        """    # r4v: Icon style and its two options.
    "icon_style",""",
        """    # r4w: the automations card and its three paths.
    "help_automations_title",
    "help_automations_auto_unhide",
    "help_automations_auto_hide",
    "help_automations_intents",
    "help_path_auto_unhide",
    "help_path_auto_hide",
    "help_path_intents",
    # r4v: Icon style and its two options.
    "icon_style",""",
    ),
]

AFTER = [
    (HELP, "paths = listOf(", 4),
    # ⚠ Spelled with the indentation only a `HelpSection` argument has. A bare token counted the
    # three `AutomationItem(path = …)` arguments this same script adds — the comment trap in its
    # other form, where the script's own new *code* inflates the count rather than its comment.
    (HELP, "\n            path = stringResource(", 0),
    (HELP, "\n                path = stringResource(", 3),
    (HELP, "HelpPaths(paths = paths)", 2),
    (HELP, "AutomationsSection(number = 6)", 1),
    (HELP, "R.string.help_path_dooa", 1),
    (STRINGS, 'name="help_automations_title"', 1),
    (STRINGS, 'name="help_path_intents"', 1),
    (STRINGS, "IMD SETTINGS MANAGER", 1),
    (STRINGS, "IMD SERVICES MANAGER", 0),
    (STRINGS, "Use this settings manager", 1),
    (STRINGS, "(only if you use Shizuku)", 0),
]

# ⚠ The three new trees name real rows. Read out of the strings rather than trusted, so a
# rename breaks this script instead of quietly making the readme wrong the way r4v found it.
ROW_LABELS = [
    ("auto_unhide", "Auto unhide settings"),
    ("auto_hide", "Auto hide settings"),
    ("section_imd_plus", "IMD+ (needs background service)"),
    ("section_advanced", "Advanced"),
    ("tasker_integration", "IMD intents (EXPERIMENTAL)"),
    ("section_app_functions", "Default IMD settings"),
]


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

    labels = staged[STRINGS]

    for name, phrase in ROW_LABELS:
        if f'<string name="{name}">{phrase}</string>' not in labels:
            print(f"REFUSED: {STRINGS}\n  the row {name!r} is no longer {phrase!r}")
            return 1

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    for statement in (
        "import androidx.compose.material3.OutlinedCard",
        "import androidx.compose.foundation.layout.Column",
        "import androidx.compose.foundation.layout.padding",
    ):
        if statement not in staged[HELP]:
            print(f"REFUSED: {HELP}\n  {statement!r} is absent")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {HELP}  :: two trees on §3, a new §6, paths as a list")
    print(f"  ok        {STRINGS}  :: his wording verbatim, manager renamed")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
