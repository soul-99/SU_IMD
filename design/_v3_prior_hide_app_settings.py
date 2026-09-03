#!/usr/bin/env python3
"""
v3-r2b3 part 4 — the popup on the per-app settings screen.

Part 3 added this screen's `when` branch, which sets a flag. This declares that flag, plumbs the
two answers down from the ViewModel and puts the dialog on screen.

Three layers, because that is how this screen is built: `AppSettingsRoute` holds the ViewModel,
`AppSettingsScreen` holds the dialog state, and the effect that reads the apply result is a
third composable below it — the same path `onShowWriteSecureSettingsDialog` already takes, which
is why the new parameter is modelled on it exactly rather than invented.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsScreen.kt"
)

EDITS: list[tuple[str, str]] = [
    # 1. The Route hands the two answers down.
    (
        """        onApplyAppSettings = viewModel::applyAppSettings,
""",
        """        onApplyAppSettings = viewModel::applyAppSettings,
        onRestoreThenApply = viewModel::restoreThenApply,
        onDiscardThenApply = viewModel::discardThenApply,
""",
    ),
    # 2. The screen accepts them.
    (
        """    onApplyAppSettings: () -> Unit,
    onRevertAppSettings: () -> Unit,
""",
        """    onApplyAppSettings: () -> Unit,
    /**
     * The force-close popup's two answers, both of which end in this screen's launch running
     * again. See `SettingsHiddenRunner.discardPendingReverts` — the second one is permanent.
     */
    onRestoreThenApply: () -> Unit,
    onDiscardThenApply: () -> Unit,
    onRevertAppSettings: () -> Unit,
""",
    ),
    # 3. The flag, beside the three this screen already keeps.
    (
        """    var showWriteSecureSettingsDialog by rememberSaveable { mutableStateOf(false) }
""",
        """    var showWriteSecureSettingsDialog by rememberSaveable { mutableStateOf(false) }

    // Settings are down from a run of IMD that is no longer alive. Saved like its neighbours:
    // losing it to a rotation would leave a launch that simply did nothing, with the only
    // explanation gone.
    var showPriorHideDialog by rememberSaveable { mutableStateOf(false) }
""",
    ),
    # 4. The effect below is told how to raise it, exactly as it is told about the grant.
    (
        """        onShowWriteSecureSettingsDialog = {
            showWriteSecureSettingsDialog = true
        },
""",
        """        onShowWriteSecureSettingsDialog = {
            showWriteSecureSettingsDialog = true
        },
        onShowPriorHideDialog = {
            showPriorHideDialog = true
        },
""",
    ),
    (
        """    onShowWriteSecureSettingsDialog: () -> Unit,
    onResetGetPinShortcutResult: () -> Unit,
""",
        """    onShowWriteSecureSettingsDialog: () -> Unit,
    onShowPriorHideDialog: () -> Unit,
    onResetGetPinShortcutResult: () -> Unit,
""",
    ),
    (
        """                priorHide = true
""",
        """                onShowPriorHideDialog()
""",
    ),
    # 5. And the dialog itself, beside the one it is modelled on.
    (
        """    if (showWriteSecureSettingsDialog) {
        WriteSecureSettingsDialog(
            onDismissRequest = {
                showWriteSecureSettingsDialog = false
            },
        )
    }
""",
        """    if (showWriteSecureSettingsDialog) {
        WriteSecureSettingsDialog(
            onDismissRequest = {
                showWriteSecureSettingsDialog = false
            },
        )
    }

    // Dismissed before either call, so the Shizuku spinner a restore may need is not hidden
    // behind a dialog that has already been answered.
    if (showPriorHideDialog) {
        PriorHideDialog(
            onRestore = {
                showPriorHideDialog = false

                onRestoreThenApply()
            },
            onIgnore = {
                showPriorHideDialog = false

                onDiscardThenApply()
            },
        )
    }
""",
    ),
]


def main() -> int:
    problems: list[str] = []

    path = ROOT / SCREEN

    if not path.exists():
        print(f"REFUSED — {SCREEN} is missing")

        return 1

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{len(line)} chars — {line.strip()[:60]}")

    # The flag part 3 set has to be gone: it never had a declaration, which is the whole
    # reason this script exists.
    if "priorHide = true" in text:
        problems.append("the undeclared flag from part 3 is still there")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print("ok — the per-app settings screen shows the popup and both answers reach the runner")

    return 0


if __name__ == "__main__":
    sys.exit(main())
