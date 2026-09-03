#!/usr/bin/env python3
"""
v3-r9 — the settings manager draws only the rows "Settings manager options" selected.

The preference exists and the dialog writes it; this is the end that reads it.

⚠ **Two filters, and the order between them does not matter because they are both removals.**
`manageShizuku` already takes the Shizuku and overlay rows away when the master switch is off;
this takes away whatever the user unticked. A row has to survive both to be drawn.

⚠ **"All off / All on only manages the displayed toggles" needs no code**, which is the author's
own instruction and was already true: `usableTargets` is filtered out of `drawnRows`, so a row that
stops being drawn stops being touched by the pill in the same breath. The comment in `rows()`
already says this about the `manageShizuku` case; it now covers a second caller.

⚠ **Defaulted to every row at the composable's parameter.** The dialog has two hosts and only one
of them is wired to a view model that knows about this preference; a default of "show it" means a
caller that has not been told draws what the manager has always drawn, rather than an empty card.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

ROUTE = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerRoute.kt"
)

VM = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerViewModel.kt"
)

# --- the view model exposes it --------------------------------------------------------------

VM_OLD = '''    val manageShizuku = userDataRepository.userData
        .map { it.manageShizukuEffective }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )
'''

VM_NEW = '''    val manageShizuku = userDataRepository.userData
        .map { it.manageShizukuEffective }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Which rows the user chose to see, from "Settings manager options" in Settings.
     *
     * ⚠ **Drawing only, exactly like [manageShizuku] above** — and unlike it, not a statement
     * about whether IMD manages the target at all. A row hidden here is still hidden by a hide,
     * still restored by a revert, and still counted by everything in the engine; it is simply not
     * on this card.
     *
     * ⚠ **Starts as every row.** The initial value is what the manager has always drawn, so the
     * frame before the store answers looks like the card the user knows rather than an empty one
     * that fills in.
     */
    val managerRows = userDataRepository.userData
        .map { it.managerRows }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ManagerRows.Default,
        )
'''

VM_IMPORT_OLD = "import com.android.geto.domain.model.manageShizukuEffective\n"

VM_IMPORT_NEW = (
    "import com.android.geto.domain.model.ManagerRows\n"
    "import com.android.geto.domain.model.manageShizukuEffective\n"
)

# --- the route collects and forwards ---------------------------------------------------------

ROUTE_COLLECT_OLD = '''    val manageShizuku by viewModel.manageShizuku.collectAsStateWithLifecycle()
'''

ROUTE_COLLECT_NEW = '''    val manageShizuku by viewModel.manageShizuku.collectAsStateWithLifecycle()

    val managerRows by viewModel.managerRows.collectAsStateWithLifecycle()
'''

ROUTE_PASS_OLD = '''        manageShizuku = manageShizuku,
'''

ROUTE_PASS_NEW = '''        manageShizuku = manageShizuku,
        managerRows = managerRows,
'''

# --- the dialog takes it and filters ----------------------------------------------------------

DIALOG_PARAM_OLD = '''    manageShizuku: Boolean = true,
'''

DIALOG_PARAM_NEW = '''    manageShizuku: Boolean = true,
    /**
     * Which rows the user chose to see, from "Settings manager options" in Settings.
     *
     * ⚠ **Defaulted to every row**, and that default is doing real work: a caller that has not
     * been told draws what this dialog has always drawn rather than an empty card. It is also
     * what the value starts as while the store is being read.
     *
     * ⚠ **Drawing only.** See `ManagerRows` — a row missing from here is not switched off, not
     * excluded from a hide, and not skipped by Revert to default.
     */
    managerRows: Map<ManualRevertTarget, Boolean> = ManagerRows.Default,
'''

DIALOG_CALL_OLD = '''            val drawnRows = rows(manageShizuku = manageShizuku)
'''

DIALOG_CALL_NEW = '''            val drawnRows = rows(manageShizuku = manageShizuku, shown = managerRows)
'''

ROWS_SIG_OLD = '''private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> {
'''

ROWS_SIG_NEW = '''private fun rows(
    manageShizuku: Boolean,
    shown: Map<ManualRevertTarget, Boolean>,
): List<ManualRevertTarget> {
'''

ROWS_RETURN_OLD = '''    return drawn.sortedBy { it.rowPosition }
'''

ROWS_RETURN_NEW = '''    // ⚠ **A second removal, not a second opinion — r9.** Above decides what IMD is managing at
    // all; this decides what the user asked to look at. A row has to survive both, and neither
    // knows about the other.
    //
    // `!= false` rather than `== true`: a target with no stored answer is one this build knows
    // and the store has not been asked about, and the safe direction there is to draw it. See
    // ManagerRows.decode, which resolves the same case the same way.
    return drawn.filter { shown[it] != false }.sortedBy { it.rowPosition }
'''

DIALOG_IMPORT_OLD = "import com.android.geto.domain.model.ManualRevertTarget\n"

DIALOG_IMPORT_NEW = (
    "import com.android.geto.domain.model.ManagerRows\n"
    "import com.android.geto.domain.model.ManualRevertTarget\n"
)

EDITS = [
    (VM, VM_IMPORT_OLD, VM_IMPORT_NEW),
    (VM, VM_OLD, VM_NEW),
    (ROUTE, ROUTE_COLLECT_OLD, ROUTE_COLLECT_NEW),
    (ROUTE, ROUTE_PASS_OLD, ROUTE_PASS_NEW),
    (DIALOG, DIALOG_IMPORT_OLD, DIALOG_IMPORT_NEW),
    (DIALOG, DIALOG_PARAM_OLD, DIALOG_PARAM_NEW),
    (DIALOG, DIALOG_CALL_OLD, DIALOG_CALL_NEW),
    (DIALOG, ROWS_SIG_OLD, ROWS_SIG_NEW),
    (DIALOG, ROWS_RETURN_OLD, ROWS_RETURN_NEW),
]

CHECKS = [
    (VM, "val managerRows = userDataRepository.userData", 1, "the view model exposes it"),
    (ROUTE, "managerRows = managerRows,", 1, "the route forwards it"),
    (DIALOG, "shown[it] != false", 1, "and the dialog filters on it, once"),
    (DIALOG, "rows(manageShizuku = manageShizuku, shown = managerRows)", 1, "one call site"),
    (DIALOG, "ManagerRows.Default", 1, "one default, on the parameter"),
    # The pill's list is derived from what was drawn and must stay that way - this is the whole
    # of "All off / All on only manages the displayed toggles".
    (DIALOG, "val usableTargets = drawnRows.filter(usableOf)", 1, "the pill still follows the card"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        if text.count(old) != 1:
            print(f"REFUSED: {Path(rel).name} anchor {old.strip()[:58]!r} x{text.count(old)}")
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already applied")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:32s} {old.strip().splitlines()[0][:40]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:40]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:32s} x{got}  {token[:34]!r}")

    over = lambda s: {ln for ln in s.split("\n")
                      if len(ln) > 120 and not ln.lstrip().startswith("import ")}

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
