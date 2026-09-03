#!/usr/bin/env python3
"""
v3-r9 — rename ManagerRowsDialog's `label` extension, which the import checker was right about.

`ManagerRowsDialog.kt` declared `private fun ManualRevertTarget.label(...)`, and
`check_symbol_imports` went from **0 to 23** reports the moment it landed. Not one of them is a real
missing import: the checker collects top-level declarations by name, `label` is now a top-level name
owned by `com.android.geto.feature.settings.dialog`, and every unrelated `label` in the tree — a
data-class property, a parameter, a local — looks like a reference to it that forgot its import.

The checker is not wrong to complain. A tree-wide top-level declaration called `label` is a name
collision waiting to happen whoever reads it next, and `private` does not help: the file is still
declaring one of the most reused identifiers in the codebase at top level.

So it becomes `managerRowLabel`, which nothing else can be mistaken for. The parameter named `label`
inside `ManagerRowCheckbox` is untouched — a function parameter is not a top-level declaration and
was never part of this.

Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/ManagerRowsDialog.kt"
)

DECL_OLD = '''/** The label the manager gives this row, in this module's own copy of the strings. */
@Composable
private fun ManualRevertTarget.label(shizukuForkMode: ShizukuForkMode): String = when (this) {
'''

DECL_NEW = '''/**
 * The label the manager gives this row, in this module's own copy of the strings.
 *
 * ⚠ **Not called `label`, and `check_symbol_imports` is why.** That checker collects top-level
 * declarations by name, so a top-level `label` here made every unrelated `label` in the tree — a
 * property, a parameter, a local — look like a reference to this one with a missing import: 23 of
 * them, from a baseline of zero. A name this reused does not belong at top level whoever declares
 * it, and `private` does not change that.
 */
@Composable
private fun ManualRevertTarget.managerRowLabel(shizukuForkMode: ShizukuForkMode): String =
    when (this) {
'''

USE_OLD = '''                    label = target.label(shizukuForkMode),
'''

USE_NEW = '''                    label = target.managerRowLabel(shizukuForkMode),
'''


def main() -> int:
    path = ROOT / DIALOG

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in ((DECL_OLD, DECL_NEW), (USE_OLD, USE_NEW)):
        if text.count(old) != 1:
            print(f"REFUSED: anchor {old.strip()[:60]!r} matched {text.count(old)} time(s)")
            return 1

        if new in original:
            print("REFUSED: already applied")
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in (
        ("fun ManualRevertTarget.managerRowLabel", 1, "renamed once"),
        ("target.managerRowLabel(", 1, "and called once"),
        ("ManualRevertTarget.label(", 0, "the old name is gone"),
        # The parameter keeps its name; it is not a top-level declaration.
        ("    label: String,", 1, "ManagerRowCheckbox's parameter is untouched"),
    ):
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:48]!r}")

    path.write_text(text, encoding="utf-8")

    print("\n  ok  the extension is managerRowLabel")

    return 0


if __name__ == "__main__":
    sys.exit(main())
