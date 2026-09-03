#!/usr/bin/env python3
"""
v3-r9 — record the five new strings as deferred translations.

r9 adds five English strings — the "Settings manager options" row, dialog title, description and
summary, plus the Shevery rename of one row label — and `check_translations` went from **72 problems
/ 739 strings** to **122 / 744**. Exactly five keys times ten locales; nothing else moved.

⚠ **DEFERRED is not a way of silencing the checker, it is the list the final pass works from.** Its
own header says so: the author's standing rule is that translation happens in one pass when
everything is built, and listing a key here *"keeps the check honest — a missing translation stays
visible as a deferral rather than being disguised as a translation that happens to be identical"*.
So the five belong in it, and with them the baseline returns to 72, which is what makes 72 mean
anything on the next round.

Nothing is written unless the count comes back to the baseline.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER = "tools/check_translations.py"

BASELINE_PROBLEMS = 72

OLD = '''    "revert_shevery",
    "shevery_service_first",
    "shevery_wait_countdown",
}
'''

NEW = '''    "revert_shevery",
    "shevery_service_first",
    "shevery_wait_countdown",
    # r9: "Settings manager options" - the User interface row, the dialog it opens, and the
    # author's own description sentence inside it.
    "manager_rows_entry",
    "manager_rows_title",
    "manager_rows_description",
    "manager_rows_summary",
    # And the fork rename of one row label, which this module needed a copy of because the two
    # dialogs already using these six labels never rename it.
    "revert_defaults_shevery",
}
'''

LOCALES = ["ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "hi", "ja", "ko", "ru"]


def problems() -> int:
    out = subprocess.run(
        [sys.executable, str(ROOT / CHECKER), *LOCALES],
        capture_output=True,
        text=True,
        cwd=ROOT,
    ).stdout

    for line in out.splitlines():
        if line.strip().endswith("PROBLEMS"):
            return int(line.split()[0])

    raise SystemExit("REFUSED: could not read a problem count from the checker")


def main() -> int:
    path = ROOT / CHECKER

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: anchor matched {original.count(OLD)} time(s)")
        return 1

    if NEW in original:
        print("REFUSED: already applied")
        return 1

    before = problems()

    path.write_text(original.replace(OLD, NEW, 1), encoding="utf-8")

    after = problems()

    if after != BASELINE_PROBLEMS:
        path.write_text(original, encoding="utf-8")

        print(
            f"REFUSED: {before} -> {after} problems, expected {BASELINE_PROBLEMS}. "
            "Reverted; something other than these five keys has moved.",
        )
        return 1

    print(f"  ok  {before} -> {after} problems, back to the baseline")

    return 0


if __name__ == "__main__":
    sys.exit(main())
