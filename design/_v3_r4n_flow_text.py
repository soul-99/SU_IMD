#!/usr/bin/env python3
"""v3-r4n item 5 — two lines of the IMD+ "How this works" flow.

The author's instruction, verbatim:

    point 3: remove the word 'names.'
    point 2: replace ', before it has read anything' with
             ' (as first launch might detect settings before IMD hiding them)'

⚠ **The text only. The flowchart images stay frozen** — this is `auto_hide_flow_2` and
`auto_hide_flow_3`, the numbered steps `AutoHideDialogs.FlowStep` draws, not anything under
`docs/` or `tools/logics/`.

Before:
    2. IMD+ closes it through Shizuku, before it has read anything.
    3. IMD hides whatever Settings to hide/ disable names.

After:
    2. IMD+ closes it through Shizuku (as first launch might detect settings before IMD hiding
       them).
    3. IMD hides whatever Settings to hide/ disable

⚠ **Step 3 loses its full stop, and that is the literal reading of the instruction.** The token
the author quoted is `'names.'`, stop included, and every other one of the nine steps ends in a
full stop — so this is either deliberate or a slip in the quoting. Applied literally rather than
tidied, and flagged for him: restoring the stop is a one-character change to this script.

⚠ **English only.** Translations are deferred; both keys join `check_translations.py`'s
`DEFERRED` set, which is the list the eventual pass works from. The eleven locale copies keep
the old sentences.

Asserts every anchor matches exactly once and that neither replaced phrase survives anywhere in
the file. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"

OLD_FLOW_2 = (
    '    <string name="auto_hide_flow_2">IMD+ closes it through Shizuku, '
    "before it has read anything.</string>"
)

NEW_FLOW_2 = (
    '    <string name="auto_hide_flow_2">IMD+ closes it through Shizuku '
    "(as first launch might detect settings before IMD hiding them).</string>"
)

OLD_FLOW_3 = (
    '    <string name="auto_hide_flow_3">IMD hides whatever Settings to hide/ '
    "disable names.</string>"
)

NEW_FLOW_3 = (
    '    <string name="auto_hide_flow_3">IMD hides whatever Settings to hide/ '
    "disable</string>"
)

# Anchored to the neighbouring deferral so the insertion point cannot drift — a bare line in
# that set is a one-token string and several of them are substrings of each other.
OLD_DEFERRED = """    # r3: the greyed-toggle explainer and its two location trees."""

NEW_DEFERRED = """    # r4n: the two IMD+ flow steps the author rewrote.
    "auto_hide_flow_2",
    "auto_hide_flow_3",
    # r3: the greyed-toggle explainer and its two location trees."""

# ⚠ **Spelled the way they can only appear in a string resource, not as bare words.** The
# comment trap: this script's own docstring quotes both phrases, and a bare
# "before it has read anything" would match the file's KDoc if one ever mentioned it.
GONE = (
    (STRINGS, "Shizuku, before it has read anything."),
    (STRINGS, "disable names."),
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in (
        (STRINGS, "auto_hide_flow_2", OLD_FLOW_2, NEW_FLOW_2),
        (STRINGS, "auto_hide_flow_3", OLD_FLOW_3, NEW_FLOW_3),
        (CHECK, "the DEFERRED set", OLD_DEFERRED, NEW_DEFERRED),
    ):
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries {name} — has this run before?")
            return 1

        staged[path] = text.replace(old, new, 1)

    # Neither replaced phrase may survive anywhere in the file.
    for rel, phrase in GONE:
        if phrase in staged[ROOT / rel]:
            print(f"REFUSED: {rel} still carries {phrase!r} after the edit")
            return 1

    # ⚠ **Position, not presence** (the anchor trap, handover_6 §4.2). Step 2 must still come
    # before step 3, and both before step 4 — an edit that landed in the wrong element would
    # otherwise pass every count above.
    strings = staged[ROOT / STRINGS]

    two = strings.index('name="auto_hide_flow_2"')
    three = strings.index('name="auto_hide_flow_3"')
    four = strings.index('name="auto_hide_flow_4"')

    if not two < three < four:
        print("REFUSED: the flow steps are no longer in order in the file")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: auto_hide_flow_2, auto_hide_flow_3")
    print(f"  ok        {CHECK}  :: both keys deferred")
    print("\n  2. IMD+ closes it through Shizuku (as first launch might detect settings "
          "before IMD hiding them).")
    print("  3. IMD hides whatever Settings to hide/ disable")
    print("\nwrote 2 file(s), 3 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
