#!/usr/bin/env python3
"""
v3-r9 — "Settings manager options": the strings, the row, and the view model call.

The dialog itself is `ManagerRowsDialog.kt`; this puts it on the settings screen.

⚠ **The description is the author's own sentence, verbatim** — *"Only selected options are showed
in the IMD's Settings manager:"* — apostrophe, colon and all. The apostrophe is escaped `\\'` as
Android requires, which `check19_res_escapes` enforces and which changes nothing about what is
drawn.

⚠ **A new `revert_defaults_shevery` beside `revert_defaults_shizuku`.** This module already owns
its own copies of all six row labels — `SettingsToHideDialog` and `RevertDefaultsDialog` both use
them — and the only one missing was the fork rename, because neither of those dialogs makes it.

The row goes in **User interface**, after Icon style, with a subtitle carrying the count the way
Theme and Icon style carry their current value: the row says what it is set to, so the dialog is
for changing it rather than for finding out.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

VM = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

# --- strings -------------------------------------------------------------------------------

STRINGS_OLD = '''    <string name="revert_defaults_shizuku">Shizuku service</string>
'''

STRINGS_NEW = '''    <string name="revert_defaults_shizuku">Shizuku service</string>

    <!--
      The same row under the other fork, and the only one of the six labels this module was
      missing: the two dialogs that already use these strings never rename it. Added for
      "Settings manager options", which does - the manager renames it, so the list that says
      which manager rows are drawn has to rename it too, or it would be offering to hide a row
      by a name that is not on the card.
    -->
    <string name="revert_defaults_shevery">Shevery service</string>
'''

ENTRY_OLD = '''    <string name="developer_note_new_2">Auto hide settings (needs background service).</string>
</resources>
'''

ENTRY_NEW = '''    <string name="developer_note_new_2">Auto hide settings (needs background service).</string>

    <!--
      "Settings manager options" - which rows the settings manager draws.

      The description is the author's own sentence and goes in exactly as he wrote it. The
      apostrophe is escaped because Android requires it in a string resource; nothing about what
      is drawn changes.

      The summary counts what is shown, the way revert_defaults_summary counts what is switched
      on - the row carries its own state so the dialog is for changing it, not for reading it.
    -->
    <string name="manager_rows_entry">Settings manager options</string>
    <string name="manager_rows_title">Settings manager options</string>
    <string name="manager_rows_description">Only selected options are showed in the IMD\\'s Settings manager:</string>
    <string name="manager_rows_summary">%1$d of %2$d shown</string>
</resources>
'''

# --- the row -------------------------------------------------------------------------------

ROW_OLD = '''                onClick = { showIconStyleDialog = true },
            )
        }
'''

ROW_NEW = '''                onClick = { showIconStyleDialog = true },
            )

            SettingsRowDivider()

            // Which rows the settings manager draws. In User interface rather than beside the
            // manager's own configuration in App functions, and deliberately: nothing here
            // changes what IMD does to the device, only what is on one card - which is what
            // every other row in this section is about.
            //
            // The subtitle counts, as Theme's and Icon style's name their current value.
            SettingsColumn(
                title = stringResource(R.string.manager_rows_entry),
                subtitle = stringResource(
                    R.string.manager_rows_summary,
                    userData.managerRows.count { it.value },
                    userData.managerRows.size,
                ),
                onClick = { showManagerRowsDialog = true },
            )
        }
'''

STATE_OLD = '''    var showIconStyleDialog by rememberSaveable { mutableStateOf(false) }
'''

STATE_NEW = '''    var showIconStyleDialog by rememberSaveable { mutableStateOf(false) }

    var showManagerRowsDialog by rememberSaveable { mutableStateOf(false) }
'''

DIALOG_OLD = '''    if (showRevertDefaultsDialog) {
'''

DIALOG_NEW = '''    if (showManagerRowsDialog) {
        ManagerRowsDialog(
            states = userData.managerRows,
            shizukuForkMode = userData.shizukuForkMode,
            onDismissRequest = { showManagerRowsDialog = false },
            onUpdateManagerRows = onUpdateManagerRows,
        )
    }

    if (showRevertDefaultsDialog) {
'''

# The callback, threaded the way onUpdateRevertDefaults already is: route -> screen -> content.
#
# ⚠ The parameter declaration matches **twice** and both are wanted: SettingsScreen takes it and
# hands it to the content composable, which takes it again. An edit that insisted on one match
# would have to name each by its surrounding lines and would break on the next reshuffle of
# either signature; asserting the pair is what actually holds.

CB_ROUTE_OLD = '''        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
'''

CB_ROUTE_NEW = '''        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
        onUpdateManagerRows = viewModel::updateManagerRows,
'''

CB_PARAM_OLD = '''    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
'''

CB_PARAM_NEW = '''    onUpdateRevertDefaults: (Map<ManualRevertTarget, Boolean>) -> Unit,
    onUpdateManagerRows: (Map<ManualRevertTarget, Boolean>) -> Unit,
'''

CB_FORWARD_OLD = '''                    onUpdateRevertDefaults = onUpdateRevertDefaults,
'''

CB_FORWARD_NEW = '''                    onUpdateRevertDefaults = onUpdateRevertDefaults,
                    onUpdateManagerRows = onUpdateManagerRows,
'''

IMPORT_OLD = '''import com.android.geto.feature.settings.dialog.LanguageDialog
'''

IMPORT_NEW = '''import com.android.geto.feature.settings.dialog.LanguageDialog
import com.android.geto.feature.settings.dialog.ManagerRowsDialog
'''

# --- the view model -------------------------------------------------------------------------

VM_OLD = '''    fun updateManagedAccessibilityServices(components: List<String>) {
'''

VM_NEW = '''    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        viewModelScope.launch {
            userDataRepository.updateManagerRows(states = states)
        }
    }

    fun updateManagedAccessibilityServices(components: List<String>) {
'''

EDITS = [
    (STRINGS, STRINGS_OLD, STRINGS_NEW),
    (STRINGS, ENTRY_OLD, ENTRY_NEW),
    (SCREEN, IMPORT_OLD, IMPORT_NEW),
    (SCREEN, STATE_OLD, STATE_NEW),
    (SCREEN, ROW_OLD, ROW_NEW),
    (SCREEN, DIALOG_OLD, DIALOG_NEW),
    (SCREEN, CB_ROUTE_OLD, CB_ROUTE_NEW),
    (SCREEN, CB_PARAM_OLD, CB_PARAM_NEW, 2),
    (SCREEN, CB_FORWARD_OLD, CB_FORWARD_NEW),
    (VM, VM_OLD, VM_NEW),
]

CHECKS = [
    (STRINGS, "manager_rows_description", 1, "the description string is declared once"),
    (STRINGS, "IMD\\'s Settings manager:", 1, "with the apostrophe escaped, exactly as written"),
    (STRINGS, "revert_defaults_shevery", 1, "and the fork rename exists"),
    (SCREEN, "showManagerRowsDialog", 4, "declared, set, tested and cleared"),
    # Seven: the route's `= viewModel::…`, two parameter declarations, and two named-argument
    # pairs (the forward and the dialog call), each of which spells the name twice.
    (SCREEN, "onUpdateManagerRows", 7, "threaded route -> screen -> content -> dialog"),
    (SCREEN, "ManagerRowsDialog(", 1, "the dialog is called once"),
    (VM, "fun updateManagerRows", 1, "and the view model writes it"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for edit in EDITS:
        rel, old, new = edit[0], edit[1], edit[2]

        times = edit[3] if len(edit) > 3 else 1

        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        if text.count(old) != times:
            print(
                f"REFUSED: {Path(rel).name} anchor {old.strip()[:58]!r} "
                f"x{text.count(old)}, expected {times}",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already applied")
            return 1

        planned[path] = text.replace(old, new)

        print(f"  ok       x{times}  {Path(rel).name:22s} {old.strip().splitlines()[0][:44]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:40]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:22s} x{got}  {token[:38]!r}")

    over = lambda s: {ln for ln in s.split("\n")
                      if len(ln) > 120 and not ln.lstrip().startswith("import ")
                      and not ln.lstrip().startswith("<string")}

    for path, text in planned.items():
        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
