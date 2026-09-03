#!/usr/bin/env python3
"""v3-r4n item 5, corrective — flow step 3 keeps its full stop.

`_v3_r4n_flow_text.py` applied the instruction literally. The author wrote *"point 3: remove the
word 'names.'"* with the stop inside the quotes, so that script removed both and left:

    3. IMD hides whatever Settings to hide/ disable

⚠ **Put to him rather than tidied silently**, because it was the only one of the nine steps
without a full stop and the standing rule is that his strings go in verbatim unless a typo is
found *and asked about*. His answer: **keep the full stop.** So the word goes and the stop stays:

    3. IMD hides whatever Settings to hide/ disable.

A separate script rather than an edit to the first one, so the history in `design/` records the
question and the answer rather than pretending the literal reading never shipped.

`auto_hide_flow_3` is already in `check_translations.py`'s `DEFERRED` set — the first script put
it there — so there is nothing to add here.

Asserts the anchor matches exactly once, that the result is not what the first script wrote, and
that the step is still in position between steps 2 and 4. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"

OLD_FLOW_3 = (
    '    <string name="auto_hide_flow_3">IMD hides whatever Settings to hide/ '
    "disable</string>"
)

NEW_FLOW_3 = (
    '    <string name="auto_hide_flow_3">IMD hides whatever Settings to hide/ '
    "disable.</string>"
)


def main() -> int:
    path = ROOT / STRINGS

    if not path.is_file():
        print(f"REFUSED: missing {STRINGS}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD_FLOW_3)

    if found != 1:
        print(f"REFUSED: {STRINGS}\n  auto_hide_flow_3 matched {found} time(s), expected 1")
        print("  run design/_v3_r4n_flow_text.py first")
        return 1

    if NEW_FLOW_3 in text:
        print(f"REFUSED: {STRINGS} already carries the full stop — has this run before?")
        return 1

    staged = text.replace(OLD_FLOW_3, NEW_FLOW_3, 1)

    # ⚠ **The word must be gone and the stop present** — the two halves of the answer, asserted
    # separately, because an edit that satisfied one and not the other would read as done.
    element = staged.split('<string name="auto_hide_flow_3">', 1)[1].split("</string>", 1)[0]

    if "names" in element:
        print(f"REFUSED: the word survives: {element!r}")
        return 1

    if not element.endswith("."):
        print(f"REFUSED: the step still has no full stop: {element!r}")
        return 1

    # ⚠ **Position, not presence** — the anchor trap. Step 3 must still sit between 2 and 4.
    two = staged.index('name="auto_hide_flow_2"')
    three = staged.index('name="auto_hide_flow_3"')
    four = staged.index('name="auto_hide_flow_4"')

    if not two < three < four:
        print("REFUSED: the flow steps are no longer in order in the file")
        return 1

    # The deferral the first script added must still be there; this script relies on it.
    deferred = (ROOT / CHECK).read_text(encoding="utf-8")

    if deferred.count('    "auto_hide_flow_3",') != 1:
        print(f"REFUSED: {CHECK} does not defer auto_hide_flow_3 exactly once")
        return 1

    path.write_text(staged, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: auto_hide_flow_3")
    print(f"\n  3. {element}")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
