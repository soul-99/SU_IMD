#!/usr/bin/env python3
"""v3-r4q — the accessibility dialog's description loses its first point, and its numbering.

    "remove the point 1 from accessibility services to manage description
     only one left so no need to display it as numbered list"

`accessibility_services_dialog_description` read:

    1. Only those turned off by IMD are turned on again
    2. Only enabled ones are shown below

The first goes; the second stops being *"2."* and stops being a list, because a list of one is
not a list. What is left is the sentence the author already wrote for it, unchanged apart from
its number.

⚠ **The newline goes with the number.** A `\\n` at the head of a one-line string is a blank line
above it on screen - the kind of thing that survives a round because it reads as spacing rather
than as a leftover.

## The initialisation screen

*"also update the corresponding initialisation screen if not already"* - there is not one yet.
The accessibility page is part of the onboarding batch that is not built, and when it is it will
draw this dialog's own content rather than a copy of it, exactly as the Shizuku page draws
`ShizukuSection`. So this string is the only place the sentence lives, and the page inherits it.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"

OLD = """    <string name="accessibility_services_dialog_description">1. Only those turned off by IMD are turned on again\\n2. Only enabled ones are shown below</string>"""

NEW = """    <string name="accessibility_services_dialog_description">Only enabled ones are shown below</string>"""

# The DOOA dialog's own list keeps its numbering - it still has three points, and the author
# renumbered nothing there. Asserted so this cannot have caught the wrong string.
UNTOUCHED = "3. Only enabled ones are shown below</string>"


def main() -> int:
    path = ROOT / STRINGS

    if not path.is_file():
        print(f"REFUSED: missing {STRINGS}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {STRINGS}\n  the description matched {found} time(s), expected 1")
        return 1

    if text.count(UNTOUCHED) != 1:
        print(f"REFUSED: {STRINGS}\n  the DOOA list is not where it was")
        return 1

    staged = text.replace(OLD, NEW, 1)

    if staged.count(UNTOUCHED) != 1:
        print(f"REFUSED: {STRINGS}\n  the DOOA list did not survive the edit")
        return 1

    if "1. Only those turned off by IMD" in staged:
        print(f"REFUSED: {STRINGS}\n  the removed point survives")
        return 1

    path.write_text(staged, encoding="utf-8")

    print(f"  ok        {STRINGS}  :: one sentence, no number, no leading newline")
    print("  ok        the DOOA dialog's three-point list untouched")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
