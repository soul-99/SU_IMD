#!/usr/bin/env python3
"""
r20d — the one call site r20b's rename missed.

`DialogContainer`'s parameter went from `frostedBackdrop` to `frostedWindow` because the thing it
does changed: r19 frosted the page *behind the window*, r20b frosts the card itself. The rename
was right and the assertion behind it was not — it checked that `frostedBackdrop` had gone from
`Dialog.kt`, which is the file where the name was *declared*, and said nothing about the file that
passes it. A named argument is exactly as much a use of the name as the declaration is.

The check below is the one that should have been written: no Kotlin file anywhere still says
`frostedBackdrop`, and the one that passes the new name passes it by name.

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


manager = MANAGER.read_text(encoding="utf-8")

OLD = """        // ⚠ **The one dialog that frosts what is behind it — r19, at the author's request.**
        // It is opened over somebody else's app as often as over IMD's own list, and the
        // frosting is what says the manager is the subject rather than a card that happened
        // to land there. Does nothing while Progressive UI blur is off.
        frostedBackdrop = true,
"""

NEW = """        // ⚠ **The one dialog that frosts its own card — r19, at the author's request, and
        // corrected in r20b.** It is opened over somebody else's app as often as over IMD's own
        // list, and the frosting is what says the manager is the subject rather than a card that
        // happened to land there. The page *around* it is left alone — the author's *"keep
        // outside BG as it was"*. Does nothing while Progressive UI blur is off.
        frostedWindow = true,
"""

found = manager.count(OLD)

if check(found == 1, f"manager: the frosted argument was found {found}x, expected 1"):
    manager = manager.replace(OLD, NEW, 1)

# ⚠ The check r20b should have made: the old name is gone from *every* file, not just the one that
# declared it. A rename is only done when nothing says the old word.
for path in sorted(ROOT.glob("**/src/**/*.kt")):
    if "/build/" in path.as_posix():
        continue

    text = manager if path == MANAGER else path.read_text(encoding="utf-8")

    check(
        "frostedBackdrop" not in text,
        f"{path.relative_to(ROOT).as_posix()} still says frostedBackdrop",
    )

check("frostedWindow = true," in manager, "the manager no longer asks for a frosted window")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

MANAGER.write_text(manager, encoding="utf-8")

print(f"wrote {MANAGER.relative_to(ROOT).as_posix()}")

print("ok")
