#!/usr/bin/env python3
"""v3-r4n item 4 — the red RikkaApps line finally goes singular.

⚠ **This finishes a job r4m started and r4m1 shipped half-done.** `_v3_rikka_warning_singular.py`
made four edits in one all-or-nothing write. Three of them are in the tree:

* `SettingsScreen.kt` has dropped `shizuku_fork_shevery` from the `emphasised(names = ...)` list,
* the comment above the bold phrases in `strings.xml` says Shevery left,
* `shizuku_rikka_warning` is in `check_translations.py`'s `DEFERRED` set.

The fourth — the sentence itself — is not. `strings.xml` still carries the plural. Something
reverted that one string after the script ran; the script cannot be re-run because its
`SettingsScreen` anchor is already the new text, so this does the one remaining edit.

Live effect being fixed: the line names Shevery and "Shevery" is no longer bold, because the
name was taken out of the emphasis list while the sentence that contains it was not.

Before:
    The original RikkaApps version of Shizuku &amp; Shevery are not supported as they do not
    support start-stop intents.

After:
    The original RikkaApps version of Shizuku is not supported as it does not support
    start-stop intents.

⚠ **English only.** Translations are deferred for the whole project and the key is already in
the `DEFERRED` set; the eleven locale copies keep the old sentence deliberately.

Asserts its anchor matches exactly once, that both surviving bold phrases still occur verbatim
in the new sentence, that the dropped one does not, and that the Kotlin side really is already
in its post-r4m shape — because if it were not, this edit would take the bold off a name that
is still in the list. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
CHECK = "tools/check_translations.py"

OLD_STRING = (
    '    <string name="shizuku_rikka_warning">The original RikkaApps version of Shizuku '
    "&amp; Shevery are not supported as they do not support start-stop intents.</string>"
)

NEW_STRING = (
    '    <string name="shizuku_rikka_warning">The original RikkaApps version of Shizuku '
    "is not supported as it does not support start-stop intents.</string>"
)

# ⚠ The three edits that already landed. Asserted as PRESENT, so this script refuses on a tree
# where r4m's work is absent — there the original script should be run instead.
ALREADY = (
    (
        SCREEN,
        "the emphasis names, minus Shevery",
        """                names = listOf(
                    stringResource(R.string.shizuku_rikka_name_rikka),
                    stringResource(R.string.shizuku_rikka_name_unsupported),
                ),""",
    ),
    (
        STRINGS,
        "the rewritten emphasis comment",
        "Shevery used to carry a fourth; r4m took",
    ),
    (CHECK, "the deferred key", '    "shizuku_rikka_warning",'),
)


def main() -> int:
    strings_path = ROOT / STRINGS

    for rel, name, needle in ALREADY:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        found = path.read_text(encoding="utf-8").count(needle)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            print("  this tree is not post-r4m; run design/_v3_rikka_warning_singular.py")
            return 1

    text = strings_path.read_text(encoding="utf-8")

    found = text.count(OLD_STRING)

    if found != 1:
        print(f"REFUSED: {STRINGS}\n  the plural sentence matched {found} time(s), expected 1")
        return 1

    if NEW_STRING in text:
        print(f"REFUSED: {STRINGS} already carries the singular sentence")
        return 1

    staged = text.replace(OLD_STRING, NEW_STRING, 1)

    # ⚠ **The emphasised() trap, asserted rather than assumed** — the project's fourth
    # encounter with it. A phrase handed to emphasised() that does not occur matches nothing,
    # silently, so both surviving names must still be substrings of the new sentence.
    sentence = NEW_STRING.split(">", 1)[1].rsplit("<", 1)[0]

    for key in ("shizuku_rikka_name_rikka", "shizuku_rikka_name_unsupported"):
        value = staged.split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

        if value not in sentence:
            print(f"REFUSED: bold phrase {value!r} does not occur in the new sentence")
            return 1

    # ⚠ `shizuku_fork_shevery` carries `translatable="false"`, so it cannot be found by a
    # name-only pattern. It must NOT occur, or dropping it from the names list was wrong.
    shevery = re.search(
        r'<string name="shizuku_fork_shevery"[^>]*>(.*?)</string>', staged,
    ).group(1)

    if shevery in sentence:
        print(f"REFUSED: {shevery!r} still occurs in the sentence but is not in names")
        return 1

    # One grammatical clause: singular subject, singular verb.
    for wrong in (" are not supported", "as they do not", "&amp; Shevery"):
        if wrong in sentence:
            print(f"REFUSED: the new sentence still carries {wrong!r}")
            return 1

    strings_path.write_text(staged, encoding="utf-8")

    print(f"  ok        {STRINGS}")
    print(f"\n  now: {sentence}")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
