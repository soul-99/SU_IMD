#!/usr/bin/env python3
"""
v3-r11 — the settings manager's order depends on which service is configured, and the nesting
shrinks to the one relationship that is real.

The author, in full:

    remove nesting from settings manager only nest display over other apps under shevery if
    shevery is the toggle selected.

    new order:  1 develp opt  2 usb debug  3 wireless deb  4 shizuku  5 accessb serv  6 dooa

    when using shevery:  1 develop opt  2 wireless debug  3 usb debug  4 accessib serv
                         5 shevery  6 (nested under shevery) DOOOA

⚠ **Two orders, and the switch between them is the same `isShevery` the row labels already use.**
r8 gave every row a fixed position and indented three of them; this replaces that with a pair of
orders and a single indent. Nothing about *behaviour* moves - the author's r8 words still hold,
*"we are just visually reordering things not their functions, or logics"* - and
[ManualRevertTarget.entries] is still what every apply path walks.

⚠ **The dialog follows, because it is the same list.** `MANAGER_ROW_ORDER` in :feature:settings is
a copy of this order (that module cannot see :feature:apps), and it takes the same `isShevery` it
already takes for the Shizuku/Shevery row's name.

⚠ **The one indent left is the only dependency that is genuinely a parent.** Overlay access is
written *through* the configured service; under Shevery that service is the row directly above it.
Under Shizuku the author asked for a flat list, and a flat list is what he gets - the relationship
is no less true, but he has looked at both and this is his call.

Also here because it is one string in two places: **'Setting manager toggles'**, his rename of
"Settings manager options", in the User interface row and in the dialog's own title.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MGR = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

DIALOG = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "ManagerRowsDialog.kt"
)

STRINGS = "feature/settings/src/main/res/values/strings.xml"

# --- the two orders --------------------------------------------------------------------

ORDER_OLD = '''private val ManualRevertTarget.rowPosition: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 1
        ManualRevertTarget.UsbDebugging -> 2
        ManualRevertTarget.Shizuku -> 3
        ManualRevertTarget.DisplayOverOtherApps -> 4
        ManualRevertTarget.AccessibilityServices -> 5
    }
'''

ORDER_NEW = '''private fun ManualRevertTarget.rowPosition(isShevery: Boolean): Int = if (isShevery) {
    // The author's Shevery order: the two debugging rows the other way round, the service
    // fifth, and overlay access hanging off it.
    when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 1
        ManualRevertTarget.UsbDebugging -> 2
        ManualRevertTarget.AccessibilityServices -> 3
        ManualRevertTarget.Shizuku -> 4
        ManualRevertTarget.DisplayOverOtherApps -> 5
    }
} else {
    // And his Shizuku order, flat.
    when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.UsbDebugging -> 1
        ManualRevertTarget.WirelessDebugging -> 2
        ManualRevertTarget.Shizuku -> 3
        ManualRevertTarget.AccessibilityServices -> 4
        ManualRevertTarget.DisplayOverOtherApps -> 5
    }
}
'''

NEST_OLD = '''private val ManualRevertTarget.nestingLevel: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 0
        ManualRevertTarget.UsbDebugging -> 0
        ManualRevertTarget.Shizuku -> 1
        ManualRevertTarget.DisplayOverOtherApps -> 2
        ManualRevertTarget.AccessibilityServices -> 0
    }
'''

NEST_NEW = '''private fun ManualRevertTarget.nestingLevel(isShevery: Boolean): Int =
    if (isShevery && this == ManualRevertTarget.DisplayOverOtherApps) 1 else 0
'''

NEST_HEADER_OLD = '''/**
 * How far in each row is drawn, in levels of [MANAGER_ROW_INDENT].
 *
 * ⚠ **Decoration, and only decoration — the author's *"we are just visually reordering things not
 * their functions, or logics"*.** Nothing is gated on a parent, no switch does anything different,
 * and the order things are *applied* in is untouched. This says where a row sits on screen and
 * says nothing else.
 *
 * What it draws is the dependency that already exists: overlay access is written **through**
 * Shizuku and through nothing else, and Shizuku needs a debugging channel before it can start. The
 * two debugging rows stay level with each other — they are two routes to the same channel, not
 * parent and child — and Shizuku hangs under the pair.
 *
 * Exhaustive for the same reason [rowPosition] is: a seventh target cannot be added without
 * someone deciding how deep it goes.
 */
'''

NEST_HEADER_NEW = '''/**
 * How far in a row is drawn, in levels of [MANAGER_ROW_INDENT] — which since r11 is at most one.
 *
 * ⚠ **Decoration, and only decoration — the author's *"we are just visually reordering things not
 * their functions, or logics"*.** Nothing is gated on a parent, no switch does anything different,
 * and the order things are *applied* in is untouched.
 *
 * ⚠ **One indent, and only under Shevery.** r8 indented Shizuku under the debugging rows and
 * overlay access under Shizuku; the author has since looked at both and asked for a flat list
 * except for this one pair. Under Shevery the configured service sits directly above overlay
 * access and is what the overlay write goes through, so the indent is saying something true about
 * two adjacent rows. Under Shizuku the same relationship holds but the rows are not adjacent, and
 * an indent that reaches across the list draws a line nobody can follow — which is why the flat
 * order is not a loss.
 */
'''

SORT_OLD = '''    return drawn.filter { shown[it] != false }.sortedBy { it.rowPosition }
'''

SORT_NEW = '''    return drawn.filter { shown[it] != false }.sortedBy { it.rowPosition(isShevery) }
'''

ROWS_SIG_OLD = '''private fun rows(
    manageShizuku: Boolean,
    shown: Map<ManualRevertTarget, Boolean>,
): List<ManualRevertTarget> {
'''

ROWS_SIG_NEW = '''private fun rows(
    manageShizuku: Boolean,
    shown: Map<ManualRevertTarget, Boolean>,
    /** Which of the two orders to draw — see [rowPosition]. */
    isShevery: Boolean,
): List<ManualRevertTarget> {
'''

ROWS_CALL_OLD = '''            val drawnRows = rows(manageShizuku = manageShizuku, shown = managerRows)
'''

ROWS_CALL_NEW = '''            val drawnRows = rows(
                manageShizuku = manageShizuku,
                shown = managerRows,
                isShevery = isShevery,
            )
'''

INDENT_OLD = '''    val indent = MANAGER_ROW_INDENT * target.nestingLevel
'''

INDENT_NEW = '''    val indent = MANAGER_ROW_INDENT * target.nestingLevel(isShevery)
'''

COUNTDOWN_OLD = '''                            start = 4.dp + MANAGER_ROW_INDENT * target.nestingLevel,
'''

COUNTDOWN_NEW = '''                            start = 4.dp + MANAGER_ROW_INDENT * target.nestingLevel(isShevery),
'''

# The header above rowPosition still describes r8's arrangement.
HEADER_OLD = ''' * ⚠ **r8 took this up on its offer**, at the author's instruction and with his own emphasis
 * that it is *"just visually reordering things not their functions, or logics"*. Every row
 * moved; see [nestingLevel] for the two that are also drawn indented.
'''

HEADER_NEW = ''' * ⚠ **r8 took this up on its offer and r11 split it in two**, both at the author's instruction
 * and with his own emphasis that it is *"just visually reordering things not their functions, or
 * logics"*. Which order is drawn follows the configured service; see [nestingLevel] for the one
 * row that is also drawn indented, and only in one of the two.
'''

# --- the dialog's copy of the order ------------------------------------------------------

STRINGS_OLD = '''    <string name="manager_rows_entry">Settings manager options</string>
'''

STRINGS_NEW = '''    <string name="manager_rows_entry">Setting manager toggles</string>
'''

STRINGS_TITLE_OLD = '''    <string name="manager_rows_title">Settings manager options</string>
'''

STRINGS_TITLE_NEW = '''    <string name="manager_rows_title">Setting manager toggles</string>
'''

# Two comments name the old title. Left as they are they would send the next reader looking for
# a string that no longer exists.
COMMENT1_OLD = '''      "Settings manager options", which does - the manager renames it, so the list that says
'''

COMMENT1_NEW = '''      "Setting manager toggles", which does - the manager renames it, so the list that says
'''

COMMENT2_OLD = '''      "Settings manager options" - which rows the settings manager draws.
'''

COMMENT2_NEW = '''      "Setting manager toggles" - which rows the settings manager draws. Renamed by the author
      in r11; it was "Settings manager options" until then.
'''

EDITS = [
    (MGR, HEADER_OLD, HEADER_NEW),
    (MGR, ORDER_OLD, ORDER_NEW),
    (MGR, NEST_HEADER_OLD, NEST_HEADER_NEW),
    (MGR, NEST_OLD, NEST_NEW),
    (MGR, ROWS_SIG_OLD, ROWS_SIG_NEW),
    (MGR, SORT_OLD, SORT_NEW),
    (MGR, ROWS_CALL_OLD, ROWS_CALL_NEW),
    (MGR, INDENT_OLD, INDENT_NEW),
    (MGR, COUNTDOWN_OLD, COUNTDOWN_NEW),
    (STRINGS, STRINGS_OLD, STRINGS_NEW),
    (STRINGS, STRINGS_TITLE_OLD, STRINGS_TITLE_NEW),
    (STRINGS, COMMENT1_OLD, COMMENT1_NEW),
    (STRINGS, COMMENT2_OLD, COMMENT2_NEW),
]

# (target, position under Shizuku, position under Shevery, indent under Shevery)
WANT = [
    ("DeveloperSettings", 0, 0, 0),
    ("UsbDebugging", 1, 2, 0),
    ("WirelessDebugging", 2, 1, 0),
    ("Shizuku", 3, 4, 0),
    ("AccessibilityServices", 4, 3, 0),
    ("DisplayOverOtherApps", 5, 5, 1),
]

CHECKS = [
    (MGR, "rowPosition(isShevery)", 1, "one sort, on the configured order"),
    (MGR, "nestingLevel(isShevery)", 2, "the row and its countdown share one depth"),
    (MGR, "ManualRevertTarget.entries", 3, "the apply order is read, not rewritten"),
    (MGR, "enum class ManualRevertTarget", 0, "and the enum is not declared here"),
    (STRINGS, ">Setting manager toggles<", 2, "the row and the dialog title, both renamed"),
    # Once, and it is the note recording what the name used to be. No string carries it.
    (STRINGS, "Settings manager options", 1, "the old name survives only as history"),
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

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip().splitlines()[0][:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:34s} {old.strip().splitlines()[0][:40]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:44]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:34s} x{got}  {token[:38]!r}")

    # ⚠ **Both orders are read back as lists, not line by line.** Six `-> n` lines each matching
    # once would also pass with two of them swapped; this reads the two `when` bodies and checks
    # they describe the two orders the author wrote out.
    text = planned[ROOT / MGR]

    start = text.index("private fun ManualRevertTarget.rowPosition(")

    body = text[start:text.index("\n}\n", start)]

    shevery_body, shizuku_body = body.split("} else {")

    for name, source, index in (("Shevery", shevery_body, 2), ("Shizuku", shizuku_body, 1)):
        got = sorted(
            (line.split("ManualRevertTarget.")[1].split(" ->")[0], int(line.split("-> ")[1]))
            for line in source.splitlines()
            if "ManualRevertTarget." in line and "-> " in line
        )

        want = sorted((t, w[index - 1]) for t, *w in ((t, a, b) for t, a, b, _ in WANT))

        if got != want:
            print(f"REFUSED: the {name} order reads {got}\n  expected {want}")
            return 1

        print(f"  checked      the {name} order is the one the author wrote")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, content in planned.items():
        if over(content) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, content in planned.items():
        path.write_text(content, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s) — two orders, one indent, one rename")

    return 0


if __name__ == "__main__":
    sys.exit(main())
