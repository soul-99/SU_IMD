#!/usr/bin/env python3
"""
r24b — the spinner import r24a left behind, and the assertion that should have caught it.

r24a moved the settings manager's `CircularProgressIndicator` into the switch's thumb and then
asserted the import was still needed:

    check(code(manager).count("CircularProgressIndicator") >= 1, ...)

which passed, because `code()` strips *comments* and the thing it was counting was the **import
line**. `check12_unusedimports` reported it a minute later. This is the same family as the comment
trap that has caught every round of these scripts: a needle that the file names for a reason other
than the one being tested. The fix that generalises is the one r23 already wrote for comments —
count on the part of the file the test is actually about, which for an import means the body with
the import line taken out. That is what the removal below does, and what r24a should have done.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def code(text: str) -> str:
    """Just the lines the compiler reads — see the note in `_v3_r23_*.py`."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


manager = MANAGER.read_text(encoding="utf-8")

SPINNER = "import androidx.compose.material3.CircularProgressIndicator\n"

if check(manager.count(SPINNER) == 1, "manager: the spinner import was not found"):
    body = code(manager.replace(SPINNER, ""))

    if check(
        "CircularProgressIndicator" not in body,
        "manager: CircularProgressIndicator is used after all — the import must stay",
    ):
        manager = manager.replace(SPINNER, "", 1)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

MANAGER.write_text(manager, encoding="utf-8")

print(f"wrote {MANAGER.relative_to(ROOT).as_posix()}")

print("ok")
