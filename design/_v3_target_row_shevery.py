#!/usr/bin/env python3
"""r4c — `isShevery` reaches the row that draws the title, and a check for the scope mistake.

The author's build of r4b:

    e: AndroidSettingsManagerDialog.kt:672:56 Unresolved reference 'isShevery'.
    e: AndroidSettingsManagerDialog.kt:714:53 Unresolved reference 'isShevery'.

⚠ **The second zip in a row to reach him without compiling, and a different mistake from the
first.** r4a was a missing *import*; this is a missing *parameter*. `isShevery` was added to
`AndroidSettingsManagerDialog` and read inside `TargetRow`, which is a separate private
composable in the same file and had no such parameter. Nothing in the suite could see it:
`feature/apps` is not one of the five modules the sandbox compiles, `check_symbol_imports` asks
about cross-package names rather than local scope, and `check9_arity` counts arguments at a call
site rather than identifiers in a body.

`tools/check_local_scope.py` is added with this fix. It is deliberately narrow: for each Kotlin
file it asks whether an identifier used inside one function is a **parameter of a different
function in the same file** and nothing else in scope. That is exactly the shape of threading a
new parameter halfway and no further, which is the mistake, and it keeps the false-positive rate
low enough to be worth running.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (MANAGER, [
        (
            """private fun TargetRow(
    modifier: Modifier = Modifier,
    target: ManualRevertTarget,
    enabled: Boolean,
    usable: Boolean,
""",
            """private fun TargetRow(
    modifier: Modifier = Modifier,
    target: ManualRevertTarget,
    enabled: Boolean,
    usable: Boolean,
    /**
     * Whether Shevery is the selected fork, which is what renames the Shizuku row.
     *
     * ⚠ **Passed in rather than read here.** The dialog above collects it once and hands the
     * same answer to every row; a row that read it for itself could disagree with the
     * usability test that was computed from it a few lines earlier.
     */
    isShevery: Boolean = false,
""",
            1,
        ),
        (
            """                TargetRow(
""",
            """                TargetRow(
                    isShevery = isShevery,
""",
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

    manager = staged.get(ROOT / MANAGER, "")

    # Both title call sites live in TargetRow, and TargetRow must now take the parameter.
    if manager.count("target.getTitle(isShevery = isShevery)") != 2:
        problems.append(f"{MANAGER}: expected both titles to read the parameter")

    if manager.count("    isShevery: Boolean = false,") != 2:
        problems.append(f"{MANAGER}: expected the dialog and the row each to take it")

    checker = ROOT / "tools/check_local_scope.py"

    if not checker.exists():
        problems.append(f"{checker.relative_to(ROOT)}: the check this fix comes with is missing")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    result = subprocess.run(
        [sys.executable, str(checker), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout.strip())

    if result.returncode != 0:
        print("⚠ the check still reports problems — the fix is incomplete")

        return 1

    print("ok - the row takes isShevery, and check_local_scope reports a clean tree")

    return 0


if __name__ == "__main__":
    sys.exit(main())
