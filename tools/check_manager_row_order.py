#!/usr/bin/env python3
"""
The settings manager's row order, and the options dialog's copy of it, must describe the same card.

⚠ **Two files, one arrangement, and no compiler between them.** `rowPosition` / `nestingLevel` in
`AndroidSettingsManagerDialog` (`:feature:apps`) decide what the manager draws;
`managerRowOrder` in `ManagerRowsDialog` (`:feature:settings`) decides what the dialog offers, and
that module cannot see the other. Both files' headers have claimed since r9 that a host assertion
keeps the copy honest. It did not exist. This is it.

What is checked, for each of the two configured services:

  * the same six targets,
  * in the same order,
  * at the same indent.

Exit status is 0 when they agree, 1 when they do not.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ROOT / (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

DIALOG = ROOT / (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "ManagerRowsDialog.kt"
)

ARM = re.compile(r"ManualRevertTarget\.(\w+)\s*->\s*(\d+)")

PAIR = re.compile(r"ManualRevertTarget\.(\w+)\s+to\s+(\d+)")


def block(text: str, start_marker: str) -> tuple[str, str]:
    """The two arms of an `if (isShevery) { ... } else { ... }` body, in that order."""
    at = text.index(start_marker)

    end = text.index("\n}\n", at)

    body = text[at:end]

    if "} else {" not in body:
        raise SystemExit(f"FAILED: {start_marker!r} is not the two-armed shape this expects")

    shevery, shizuku = body.split("} else {", 1)

    return shevery, shizuku


def manager_order() -> dict[str, list[tuple[str, int]]]:
    text = MANAGER.read_text(encoding="utf-8")

    shevery, shizuku = block(text, "private fun ManualRevertTarget.rowPosition(")

    nest = text[text.index("private fun ManualRevertTarget.nestingLevel("):]

    # The manager's indent is a one-line rule rather than a table: one target, under Shevery.
    indented = re.search(r"isShevery && this == ManualRevertTarget\.(\w+)\)\s*1", nest)

    if not indented:
        raise SystemExit("FAILED: nestingLevel is not the single-target rule this expects")

    deep = indented.group(1)

    out = {}

    for name, arm in (("shevery", shevery), ("shizuku", shizuku)):
        rows = sorted(
            ((target, int(pos)) for target, pos in ARM.findall(arm)),
            key=lambda row: row[1],
        )

        out[name] = [
            (target, 1 if name == "shevery" and target == deep else 0)
            for target, _ in rows
        ]

    return out


def dialog_order() -> dict[str, list[tuple[str, int]]]:
    text = DIALOG.read_text(encoding="utf-8")

    shevery, shizuku = block(text, "private fun managerRowOrder(")

    return {
        name: [(target, int(level)) for target, level in PAIR.findall(arm)]
        for name, arm in (("shevery", shevery), ("shizuku", shizuku))
    }


def main() -> int:
    manager = manager_order()

    dialog = dialog_order()

    problems = []

    for fork in ("shizuku", "shevery"):
        got = dialog[fork]

        want = manager[fork]

        if len(want) != 6:
            problems.append(f"{fork}: the manager lists {len(want)} rows, expected 6")

        if got != want:
            problems.append(
                f"{fork}:\n"
                f"    manager draws  {want}\n"
                f"    dialog offers  {got}",
            )

    if problems:
        print("### the settings manager and its options dialog disagree\n")

        for problem in problems:
            print(f"  {problem}")

        print(
            "\n  Both lists are written by hand in two modules that cannot see each other. "
            "Change them together.",
        )

        return 1

    for fork in ("shizuku", "shevery"):
        drawn = " ".join(
            f"{target}{'>' if level else ''}" for target, level in manager[fork]
        )

        print(f"  ok  {fork:8s} {drawn}")

    print("\n  the manager and its options dialog agree on both orders")

    return 0


if __name__ == "__main__":
    sys.exit(main())
