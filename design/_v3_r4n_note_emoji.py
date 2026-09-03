#!/usr/bin/env python3
"""v3-r4n, corrective — the scientist emoji goes into the resources literally.

`check19_res_escapes` refused the two strings `_v3_r4n_developer_note.py` wrote:

    developer_note_title: invalid escape \\U
    developer_note_notification: invalid escape \\U

⚠ **Android string resources have no `\\U` escape.** `\\uXXXX` takes four hex digits and
therefore only reaches the Basic Multilingual Plane. 🧑‍🔬 is `U+1F9D1 U+200D U+1F52C` — two
astral code points joined by a zero-width joiner — so it cannot be written as `\\u` escapes at
all without hand-encoding surrogate pairs, which nobody reading the file afterwards would
recognise as an emoji.

The answer is the one the project already uses: **put the characters in.** `about_shell_emoji`
carries 🌙☕️🥲 literally and has done since v2.5.

⚠ **And that string is also where the coffee-emoji fix lives**, which is worth recording next to
this one: the author fixed it by adding `U+FE0F` after `U+2615`, asking for emoji presentation so
the renderer reaches the colour emoji font instead of DejaVu Sans Mono's monochrome glyph. 🧑‍🔬
needs no such marker — it has no text presentation to fall back to.

Asserts each anchor matches exactly once, that no `\\U` escape survives in either file, and that
each string carries the exact three code points of the author's emoji. Writes nothing if any
assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS = "feature/settings/src/main/res/values/strings.xml"
NOTIFICATION = "framework/notification-manager/src/main/res/values/strings.xml"

SCIENTIST = "\U0001F9D1‍\U0001F52C"

EDITS = (
    (
        SETTINGS,
        "the dialog title",
        '    <string name="developer_note_title">Note from developer \\U0001F9D1\\u200D\\U0001F52C</string>',
        f'    <string name="developer_note_title">Note from developer {SCIENTIST}</string>',
    ),
    (
        NOTIFICATION,
        "the notification body",
        '    <string name="developer_note_notification">IMD: Important note from developer \\U0001F9D1\\u200D\\U0001F52C</string>',
        f'    <string name="developer_note_notification">IMD: Important note from developer {SCIENTIST}</string>',
    ),
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = path.read_text(encoding="utf-8")

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    for rel, _, _, _ in EDITS:
        text = staged[ROOT / rel]

        if "\\U0001F" in text:
            print(f"REFUSED: {rel} still carries a \\U escape")
            return 1

    # ⚠ **The exact code points, asserted.** A ZWJ sequence that lost its joiner renders as two
    # separate emoji rather than one glyph, and it is invisible in a diff.
    for rel, key in ((SETTINGS, "developer_note_title"), (NOTIFICATION, "developer_note_notification")):
        value = staged[ROOT / rel].split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

        if not value.endswith(SCIENTIST):
            print(f"REFUSED: {key} does not end with the author's emoji: {value!r}")
            return 1

        if [hex(ord(c)) for c in value[-3:]] != ["0x1f9d1", "0x200d", "0x1f52c"]:
            print(f"REFUSED: {key} does not carry the ZWJ sequence intact")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {SETTINGS}  :: developer_note_title")
    print(f"  ok        {NOTIFICATION}  :: developer_note_notification")
    print(f"\n  now: Note from developer {SCIENTIST}")
    print("\nwrote 2 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
