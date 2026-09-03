#!/usr/bin/env python3
"""
v3-r8 — the settings manager's rows, reordered and indented into the shape they already have.

The author's order, with his correction:

    Developer settings
    Wireless debugging
    USB debugging
      Shizuku service                  (nested under USB debugging)
        Display over other apps        (nested under Shizuku service)
    Accessibility services

which is the machinery told honestly: the overlay write goes *through* Shizuku and through nothing
else, and Shizuku needs a debugging channel to start.

⚠ **Visual and nothing else, at his word: *"we are just visually reordering things not their
functions"* / *"or logics"*.** Nothing here gates a row on its parent, nothing changes what a
switch does, and nothing touches the order things are applied in. That order is
[ManualRevertTarget.entries] — `masterPillOnOrder` in `:domain:model` follows it and nine host
assertions guard it — and the enum is not reordered. The header on [rowPosition] has said drawing
order is free since it was written; this is the first time anything has taken it up on that.

⚠ **Shevery needs nothing.** It is the same row under a different name — `getTitle(isShevery)` —
so it inherits this position and this indent without being mentioned.

Style: **T1, indent only, 16 dp a level**, both his picks from the r8 templates. No rail, no elbow,
no panel: the offset is the whole of it. 16 is Material's own list-indent step, so the first level
is unmistakable and the second lands at 32 dp, which "Display over other apps" still clears on the
compact card by a comfortable margin.

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

# --- 1. the order, and the depth beside it ---------------------------------------------

ORDER_OLD = '''private val ManualRevertTarget.rowPosition: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.UsbDebugging -> 1
        ManualRevertTarget.WirelessDebugging -> 2
        ManualRevertTarget.AccessibilityServices -> 3
        ManualRevertTarget.DisplayOverOtherApps -> 4
        ManualRevertTarget.Shizuku -> 5
    }
'''

ORDER_NEW = '''private val ManualRevertTarget.rowPosition: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 1
        ManualRevertTarget.UsbDebugging -> 2
        ManualRevertTarget.Shizuku -> 3
        ManualRevertTarget.DisplayOverOtherApps -> 4
        ManualRevertTarget.AccessibilityServices -> 5
    }

/**
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
private val ManualRevertTarget.nestingLevel: Int
    get() = when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 0
        ManualRevertTarget.UsbDebugging -> 0
        ManualRevertTarget.Shizuku -> 1
        ManualRevertTarget.DisplayOverOtherApps -> 2
        ManualRevertTarget.AccessibilityServices -> 0
    }
'''

# The header above rowPosition names the two rows it used to draw the other way round.
HEADER_OLD = ''' * ⚠ **Display order only.** [ManualRevertTarget.entries] is what every *apply* path
 * follows - `masterPillOnOrder` in :domain:model above all, which puts Shizuku before
 * Display over other apps because the overlay write goes *through* Shizuku, and which
 * nine host assertions guard. Drawing these two rows the other way round says nothing
 * about the order they are switched in, and the enum is deliberately not reordered.
'''

HEADER_NEW = ''' * ⚠ **Display order only.** [ManualRevertTarget.entries] is what every *apply* path
 * follows - `masterPillOnOrder` in :domain:model above all, which puts Shizuku before
 * Display over other apps because the overlay write goes *through* Shizuku, and which
 * nine host assertions guard. Rearranging what is on screen says nothing about the order
 * they are switched in, and the enum is deliberately not reordered.
 *
 * ⚠ **r8 took this up on its offer**, at the author's instruction and with his own emphasis
 * that it is *"just visually reordering things not their functions, or logics"*. Every row
 * moved; see [nestingLevel] for the two that are also drawn indented.
'''

# --- 2. the indent constant ---------------------------------------------------------------

CONST_OLD = '''private val MANAGER_GLYPH_SIZE = 48.dp
'''

CONST_NEW = '''private val MANAGER_GLYPH_SIZE = 48.dp

/**
 * How far one level of [ManualRevertTarget.nestingLevel] moves a row across.
 *
 * ⚠ **The offset is the whole treatment**, at the author's pick from the r8 template: no rail down
 * the left, no elbow into each child, no recessed panel behind the group. He asked for *"only
 * slight indent not too big not too small to notice"*, and 16 dp is Material's own list-indent
 * step — the first level is unmistakable, and the second lands at 32 dp, which "Display over other
 * apps" still clears on the narrowest card the dialog draws.
 *
 * ⚠ **It moves the row's content, not the row.** The whole row still takes the press across the
 * full width — see [TargetRow] — so an indented child is no harder to hit than a top-level one.
 */
private val MANAGER_ROW_INDENT = 16.dp
'''

# --- 3. the row draws itself at its own depth ----------------------------------------------

ROW_OLD = '''    val switchScale = size.switchScale

    val rowPadding = size.rowPadding
'''

ROW_NEW = '''    val switchScale = size.switchScale

    val rowPadding = size.rowPadding

    // ⚠ **Read from the target rather than passed in**, unlike `size` and `isShevery`. Those two
    // are answers the dialog works out once and hands down, and a row that recomputed them could
    // disagree with the card it is drawn on. This is not one of those: how deep a row sits is a
    // fact about the target itself, like `readsASelection` and `opensSomewhere` just below, and
    // there is nothing for it to disagree with.
    val indent = MANAGER_ROW_INDENT * target.nestingLevel
'''

PADDING_OLD = '''            .padding(start = 4.dp, top = rowPadding, bottom = rowPadding),
'''

PADDING_NEW = '''            // ⚠ **The indent goes inside the clickable**, which is what keeps a nested row as
            // easy to hit as a top-level one: the press area is still the full width of the card
            // and only the content moves across.
            .padding(start = 4.dp + indent, top = rowPadding, bottom = rowPadding),
'''

# --- 4. the countdown under the Shizuku row follows it in --------------------------------
#
# It is a footnote to that row and sits directly beneath it, so a row that moved 16 dp across
# while its own countdown stayed at 4 would read as belonging to whatever is above it instead.

COUNTDOWN_OLD = '''                    Text(
                        modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
'''

COUNTDOWN_NEW = '''                    Text(
                        // ⚠ **Indented with the row it explains — r8.** This is a footnote to
                        // the service row directly above it, so it takes that row's own depth;
                        // left at 4 dp it would sit under the *previous* row's left edge and
                        // read as belonging to that one instead.
                        modifier = Modifier.padding(
                            start = 4.dp + MANAGER_ROW_INDENT * target.nestingLevel,
                            bottom = 6.dp,
                        ),
'''

EDITS = [
    (HEADER_OLD, HEADER_NEW),
    (ORDER_OLD, ORDER_NEW),
    (CONST_OLD, CONST_NEW),
    (ROW_OLD, ROW_NEW),
    (PADDING_OLD, PADDING_NEW),
    (COUNTDOWN_OLD, COUNTDOWN_NEW),
]

# The order the six rows are drawn in, top to bottom, as (target, position, level).
WANT_ORDER = [
    ("DeveloperSettings", 0, 0),
    ("WirelessDebugging", 1, 0),
    ("UsbDebugging", 2, 0),
    ("Shizuku", 3, 1),
    ("DisplayOverOtherApps", 4, 2),
    ("AccessibilityServices", 5, 0),
]

CHECKS = [
    ("private val ManualRevertTarget.nestingLevel: Int", 1, "the depth is declared"),
    ("MANAGER_ROW_INDENT", 4, "declared, referenced, and used by the row and its footnote"),
    ("val indent = MANAGER_ROW_INDENT * target.nestingLevel", 1, "each row reads its own depth"),
    (".padding(start = 4.dp + indent,", 1, "and spends it on the content"),
    # Once, and it is not a row: the countdown's `bottom = 6.dp` sibling has been rewritten,
    # so what is left on this spelling is nothing at all.
    (".padding(start = 4.dp,", 0, "no flat 4 dp start padding survives"),
    ("start = 4.dp + MANAGER_ROW_INDENT * target.nestingLevel,", 1, "the footnote follows"),
    # ⚠ Nothing about *behaviour* may move. These are the three that would show it if it had.
    ("ManualRevertTarget.entries", 3, "the apply order is read, not rewritten"),
    ("enum class ManualRevertTarget", 0, "and the enum is not declared in this file at all"),
    ("sortedBy { it.rowPosition }", 1, "one sort, on the display position"),
]


def main() -> int:
    path = ROOT / DIALOG

    if not path.is_file():
        print(f"REFUSED: missing {DIALOG}")
        return 1

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: anchor {old.strip()[:70]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in original:
            print("REFUSED: already applied — has this run before?")
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token[:44]!r} appears {got} time(s), expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:52]!r}")

    # ⚠ **The order is asserted as a whole, not line by line.** Six `-> n` lines each matching
    # once would also pass if two of them were swapped; this reads the two `when` bodies back and
    # checks the list they describe is the one the author approved.
    for name, block_start in (("rowPosition", "private val ManualRevertTarget.rowPosition: Int"),
                              ("nestingLevel", "private val ManualRevertTarget.nestingLevel: Int")):
        start = text.index(block_start)

        body = text[start:text.index("    }", start)]

        got = [
            (line.split("ManualRevertTarget.")[1].split(" ->")[0], int(line.split("-> ")[1]))
            for line in body.splitlines()
            if "ManualRevertTarget." in line and "-> " in line
        ]

        want = [(t, p if name == "rowPosition" else lv) for t, p, lv in WANT_ORDER]

        # rowPosition is written in drawn order; nestingLevel keeps the same run of targets so the
        # two can be read side by side.
        if got != want:
            print(f"REFUSED: {name} reads {got}\n  expected {want}")
            return 1

        print(f"  checked      {name} is the approved order, in order")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    added = over(text) - over(original)

    if added:
        print(f"REFUSED: would gain lines over 120 chars: {sorted(added)}")
        return 1

    path.write_text(text, encoding="utf-8")

    print("\n  ok  six rows reordered, two of them indented, nothing else touched")

    return 0


if __name__ == "__main__":
    sys.exit(main())
