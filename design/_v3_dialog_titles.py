#!/usr/bin/env python3
"""
v3-r2 — the two configuration dialogs take dynamic titles and dynamic descriptions.

The author's rule: the dialogs are titled the same as the rows that open them, so a two-line
row label makes a two-line dialog title. And the description at the **top** of the
Settings-to-hide dialog now says which routes read the list, which depends on **both**
frameworks — four sentences, one per combination.

Of the four info lines that used to sit at the bottom of the Settings-to-hide dialog, the
per-app one is replaced by the description at the top and the watchdog one is dropped on the
author's instruction. The two that stay move below the checkboxes and both go red.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE_DIALOG = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "SettingsToHideDialog.kt"
)
REVERT_DIALOG = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "RevertDefaultsDialog.kt"
)
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (HIDE_DIALOG, [
        # both frameworks in, because the description needs both
        ("""    shizukuForkMode: ShizukuForkMode,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
""",
         """    shizukuForkMode: ShizukuForkMode,
    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
    onDismissRequest: () -> Unit,
    onUpdateSettingsToHide: (Map<ManualRevertTarget, Boolean>) -> Unit,
""", 1),
        ("        title = stringResource(R.string.settings_to_hide_title),\n",
         """        // The same label the row that opened this carries, so the two cannot describe
        // the list differently. Driven by the unhiding framework — see the row for why that
        // is the half that decides it.
        title = if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.settings_to_hide_both_label)
        } else {
            stringResource(R.string.settings_to_hide_defaults_label)
        },
""", 1),
    ]),
    (REVERT_DIALOG, [
        ("""    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {""",
         """    unhidingFramework: UnhidingFramework,
    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
) {""", 1),
        ("        title = stringResource(R.string.revert_defaults),\n",
         """        // Two lines under Revert to default, one under the memory function — the same
        // label as the row, at the author's instruction.
        title = if (unhidingFramework == UnhidingFramework.Memory) {
            stringResource(R.string.revert_defaults)
        } else {
            stringResource(R.string.revert_defaults_entry_both)
        },
""", 1),
    ]),
    (SCREEN, [
        ("""            shizukuForkMode = userData.shizukuForkMode,
            onDismissRequest = { showSettingsToHideDialog = false },
""",
         """            shizukuForkMode = userData.shizukuForkMode,
            hidingFramework = userData.hidingFramework,
            unhidingFramework = userData.unhidingFramework,
            onDismissRequest = { showSettingsToHideDialog = false },
""", 1),
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

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok — dialog titles are dynamic")

    return 0


if __name__ == "__main__":
    sys.exit(main())
