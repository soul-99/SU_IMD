#!/usr/bin/env python3
"""v3-r4n item 8 — the two-line label under Settings to hide.

The author's instruction: when the unhiding framework is Revert to default, the row reads
'Settings to unhide' and then, on the next line, 'Revert to default configuration'. Confirmed
from the rendered template with one addition of his: **a plus sign after the first line**,
replacing the " /" the string carries today, so the two lines read as one phrase.

Before:
    Settings to unhide on Revert /
    Revert to default configuration

After:
    Settings to unhide +
    Revert to default configuration

⚠ **One string, two call sites, and they must move together.** `revert_defaults_entry_both` is
read by the settings-list row (`SettingsScreen.kt`) and by the dialog's own heading
(`RevertDefaultsDialog.kt`), which is the point — the author asked for the row and the dialog it
opens to say the same thing. Both are asserted to still read it after the edit, so a future
round cannot quietly leave one behind.

⚠ **Only under the Revert-to-default unhiding framework.** Under the memory function both sites
fall back to `revert_defaults` alone; that branch is untouched.

⚠ **English only.** Translations deferred; the key joins `check_translations.py`'s `DEFERRED`
set. The eleven locale copies keep the old label.

Asserts every anchor matches exactly once, that the replaced phrase is gone, and that both
readers survive. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"

OLD_STRING = (
    '    <string name="revert_defaults_entry_both">Settings to unhide on Revert /'
    "\\nRevert to default configuration</string>"
)

NEW_STRING = (
    '    <string name="revert_defaults_entry_both">Settings to unhide +'
    "\\nRevert to default configuration</string>"
)

OLD_DEFERRED = """    # r4n: the two IMD+ flow steps the author rewrote."""

NEW_DEFERRED = """    # r4n: the revert row's two-line label, and the two IMD+ flow steps.
    "revert_defaults_entry_both",
    # r4n: the two IMD+ flow steps the author rewrote."""

# ⚠ Spelled as it can only appear in a `stringResource` call, never as a bare word — the
# comment trap, which this project has now hit four times.
READERS = (
    (SCREEN, "R.string.revert_defaults_entry_both"),
    (DIALOG, "R.string.revert_defaults_entry_both"),
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in (
        (STRINGS, "revert_defaults_entry_both", OLD_STRING, NEW_STRING),
        (CHECK, "the DEFERRED set", OLD_DEFERRED, NEW_DEFERRED),
    ):
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = path.read_text(encoding="utf-8")

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries {name} — has this run before?")
            return 1

        staged[path] = text.replace(old, new, 1)

    strings = staged[ROOT / STRINGS]

    # ⚠ **Scoped to this element, and the first draft was not.** "Settings to unhide on Revert"
    # is also the whole of `revert_defaults_entry`, the phrase the reset notice bolds inside its
    # own sentence — a different string the author has not asked to change. A file-wide absence
    # check refuses forever on it. Bare-line and bare-phrase anchors are the trap; the answer is
    # to bound the check to the element being edited.
    element = strings.split('<string name="revert_defaults_entry_both">', 1)[1]
    element = element.split("</string>", 1)[0]

    if "on Revert" in element or " /" in element:
        print(f"REFUSED: the old label survives inside the element: {element!r}")
        return 1

    if not element.startswith("Settings to unhide +\\n"):
        print(f"REFUSED: the new element does not start with the plus line: {element!r}")
        return 1

    # And the neighbour it is a substring of must be untouched.
    if '<string name="revert_defaults_entry">Settings to unhide on Revert</string>' not in strings:
        print("REFUSED: revert_defaults_entry changed — it is a different string")
        return 1

    # ⚠ **Both readers, asserted.** The whole instruction is that the row and its dialog say
    # the same thing; an edit that left one reading a different key would satisfy every count
    # above and still ship two different labels.
    for rel, needle in READERS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        found = path.read_text(encoding="utf-8").count(needle)

        if found != 1:
            print(f"REFUSED: {rel}\n  reads the key {found} time(s), expected exactly 1")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}")
    print(f"  ok        {CHECK}  :: key deferred")
    print("  ok        both readers still on revert_defaults_entry_both")
    print("\n  now: Settings to unhide +\\nRevert to default configuration")
    print("\nwrote 2 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
