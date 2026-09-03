#!/usr/bin/env python3
"""
v3-r9 — GetoApplication now calls `first()`, so it has to import it.

`_v3_autohide_detector_selection.py` reads the migration flag with
`userDataRepository.userData.first()`, and this file collected flows but had never taken a single
value from one. Caught by `check_symbol_imports`, which is exactly what that checker is for.

Split from the script that introduced the call so the two read separately: one is the wiring, this
is the consequence.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APP = "app/src/main/kotlin/com/android/geto/GetoApplication.kt"

OLD = "import kotlinx.coroutines.flow.drop\n"

NEW = "import kotlinx.coroutines.flow.drop\nimport kotlinx.coroutines.flow.first\n"


def main() -> int:
    path = ROOT / APP

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: anchor matched {original.count(OLD)} time(s)")
        return 1

    if NEW in original:
        print("REFUSED: already applied")
        return 1

    text = original.replace(OLD, NEW, 1)

    if text.count("import kotlinx.coroutines.flow.first") != 1:
        print("REFUSED: the import did not land exactly once")
        return 1

    if text.count(".first()") < 1:
        print("REFUSED: nothing in this file calls first(), so the import would be unused")
        return 1

    path.write_text(text, encoding="utf-8")

    print("  ok  first() is imported")

    return 0


if __name__ == "__main__":
    sys.exit(main())
