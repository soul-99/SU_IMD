#!/usr/bin/env python3
"""
v3-r4m — draw the Shizuku row *below* Display over other apps in the settings manager.

    "move the shizuku toggle below the dooa toggle in the settings manager"

Wanted display order: Developer settings, USB debugging, Wireless debugging,
Accessibility services, Display over other apps, Shizuku.

⚠ **This is DISPLAY ONLY, and the enum's own order is deliberately left alone.**
`ManualRevertTarget.entries` is what every *apply* path follows — `masterPillOnOrder` in
:domain:model above all, which nine host assertions guard, and which puts Shizuku before
Display over other apps on the way on because the overlay write goes *through* Shizuku.
Drawing the two rows the other way round must not, and does not, change that: `rows()` now
returns an explicit display list and nothing else reads it.

⚠ Written as an exhaustive `when` on an extension property rather than as a `listOf`, so a
seventh `ManualRevertTarget` cannot be added without a decision about where it is drawn.
A `listOf` would simply leave it out, and nothing in the audit suite reads this file.

The `manageShizuku = false` branch is untouched and still drops both Shizuku and Display
over other apps — the sort runs after the filter, so it is a no-op there.

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

# --- the new display order, inserted immediately above rows()'s KDoc ------------------

ROW_POSITION = '''/**
 * Where each row is drawn in the settings manager, top to bottom.
 *
 * ⚠ **Display order only.** [ManualRevertTarget.entries] is what every *apply* path
 * follows - `masterPillOnOrder` in :domain:model above all, which puts Shizuku before
 * Display over other apps because the overlay write goes *through* Shizuku, and which
 * nine host assertions guard. Drawing these two rows the other way round says nothing
 * about the order they are switched in, and the enum is deliberately not reordered.
 *
 * An exhaustive `when` rather than a `listOf`: a seventh target cannot then be added
 * without a decision about where it goes. A list would simply leave it out, and nothing
 * in the audit suite reads this file.
 */
private val ManualRevertTarget.rowPosition: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.UsbDebugging -> 1
        ManualRevertTarget.WirelessDebugging -> 2
        ManualRevertTarget.AccessibilityServices -> 3
        ManualRevertTarget.DisplayOverOtherApps -> 4
        ManualRevertTarget.Shizuku -> 5
    }

'''

# rows() becomes a block body so the sort is applied once, after the filter.
OLD_ROWS_HEAD = """private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> =
    if (manageShizuku) {
        ManualRevertTarget.entries
    } else {"""

NEW_ROWS_HEAD = """private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> {
    val drawn = if (manageShizuku) {
        ManualRevertTarget.entries
    } else {"""

OLD_ROWS_TAIL = """        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku &&
                it != ManualRevertTarget.DisplayOverOtherApps
        }
    }
"""

NEW_ROWS_TAIL = """        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku &&
                it != ManualRevertTarget.DisplayOverOtherApps
        }
    }

    return drawn.sortedBy { it.rowPosition }
}
"""

# The KDoc line rows()'s doc block opens with, used as the insertion point for ROW_POSITION.
DOC_OPEN = """/**
 * Which rows this dialog draws.
"""


def main() -> int:
    path = ROOT / DIALOG

    if not path.is_file():
        print(f"REFUSED: missing {DIALOG}")
        return 1

    text = path.read_text(encoding="utf-8")

    if "rowPosition" in text:
        print("REFUSED: rowPosition already present — has this run before?")
        return 1

    for name, anchor in (
        ("rows() doc block", DOC_OPEN),
        ("rows() head", OLD_ROWS_HEAD),
        ("rows() tail", OLD_ROWS_TAIL),
    ):
        found = text.count(anchor)

        if found != 1:
            print(f"REFUSED: {name} matched {found} time(s), expected exactly 1")
            return 1

    text = text.replace(DOC_OPEN, ROW_POSITION + DOC_OPEN, 1)
    text = text.replace(OLD_ROWS_HEAD, NEW_ROWS_HEAD, 1)
    text = text.replace(OLD_ROWS_TAIL, NEW_ROWS_TAIL, 1)

    # --- assert POSITION, not merely presence (the r4e trap) -------------------------
    #
    # rowPosition must land *above* rows(), and the return must land *inside* rows() and
    # above the next top-level declaration after it. Anchors that name a function by what
    # follows it are what put r4d's block in the wrong function.
    at_position = text.index("private val ManualRevertTarget.rowPosition")
    at_rows = text.index("private fun rows(manageShizuku: Boolean)")
    at_return = text.index("    return drawn.sortedBy { it.rowPosition }")
    at_next = text.index("\n/**\n * Manage the settings this app switches off")

    if not at_position < at_rows < at_return < at_next:
        print(
            "REFUSED: placement wrong — "
            f"rowPosition@{at_position} rows@{at_rows} "
            f"return@{at_return} next@{at_next}"
        )
        return 1

    # Every enum constant named exactly once in the when, and the enum itself untouched.
    for constant in (
        "DeveloperSettings",
        "UsbDebugging",
        "WirelessDebugging",
        "AccessibilityServices",
        "DisplayOverOtherApps",
        "Shizuku",
    ):
        arm = f"        ManualRevertTarget.{constant} -> "

        if text.count(arm) != 1:
            print(f"REFUSED: when arm for {constant} matched {text.count(arm)} time(s)")
            return 1

    over = [
        (n, len(line))
        for n, line in enumerate(text.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ")
    ]

    if over:
        print(f"REFUSED: {DIALOG} would carry lines over 120 chars: {over}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {DIALOG}")
    print("  + rowPosition (display order: dev, usb, wireless, a11y, DOOA, Shizuku)")
    print("  ~ rows() is now a block body, sorting once after the filter")
    print("\nwrote 1 file, 3 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
