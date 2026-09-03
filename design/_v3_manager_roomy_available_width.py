#!/usr/bin/env python3
"""
v3-r5 — say the roomy tier's available width in Dp arithmetic, not by unwrapping one.

`(windowWidthDp - 2 * MANAGER_ROOMY_MARGIN.value.toInt()).dp` is correct and unreadable: it takes
a Dp apart to get an Int back out of it, truncates, and then re-wraps the answer. `Dp` supports
minus and times directly, so the expression can simply say what it means.

Split from `_v3_manager_size_tiers.py` rather than folded into it: that script is already written
and run, and rewriting a script that has landed to hide a second thought is how the two stop
agreeing about what the tree contains.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

OLD = """        val available = (windowWidthDp - 2 * MANAGER_ROOMY_MARGIN.value.toInt()).dp
"""

NEW = """        val available = windowWidthDp.dp - MANAGER_ROOMY_MARGIN * 2
"""


def main() -> int:
    path = ROOT / DIALOG

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: anchor matched {original.count(OLD)} time(s), expected 1")
        return 1

    if NEW in original:
        print("REFUSED: already applied")
        return 1

    text = original.replace(OLD, NEW)

    for token, want in (
        ("MANAGER_ROOMY_MARGIN.value", 0),
        ("val available = windowWidthDp.dp - MANAGER_ROOMY_MARGIN * 2", 1),
        ("minOf(MANAGER_ROOMY_WIDTH, available)", 1),
    ):
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {token!r} appears {got} time(s), expected {want}")
            return 1

    path.write_text(text, encoding="utf-8")

    print("  ok  roomy available width now reads as Dp arithmetic")

    return 0


if __name__ == "__main__":
    sys.exit(main())
