#!/usr/bin/env python3
"""
v3-r4m — the first red line in the Shizuku section drops Shevery and goes singular.

    "from red description line of shizuku config section replace '& Shevery are' with 'is'"
    "and as they with is"  ->  "as it does not"  ->  "basically make it gramatically correct also"

Before:
    The original **RikkaApps version of Shizuku** & **Shevery** are **not supported** as they
    do not support start-stop intents.

After:
    The original **RikkaApps version of Shizuku** is **not supported** as it does not support
    start-stop intents.

⚠ **`shizuku_fork_shevery` comes out of the `emphasised(names = ...)` list with it.** A phrase
handed to `emphasised` that does not occur in the sentence silently matches nothing - it is in
the trap table - so leaving it would be a bold name pointing at text that is no longer there.
The other two names, `shizuku_rikka_name_rikka` and `shizuku_rikka_name_unsupported`, still
occur verbatim and are untouched.

⚠ **English only.** Translations are deferred for the whole project; the key joins
`check_translations.py`'s DEFERRED set, which is the list the eventual pass works from. The
eleven locale copies still carry the old sentence and are deliberately not touched.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
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

OLD_NAMES = """                names = listOf(
                    stringResource(R.string.shizuku_rikka_name_rikka),
                    stringResource(R.string.shizuku_fork_shevery),
                    stringResource(R.string.shizuku_rikka_name_unsupported),
                ),"""

NEW_NAMES = """                // ⚠ **Shevery is no longer in this sentence**, so its name leaves the
                // list with it: a phrase handed to `emphasised` that does not occur matches
                // nothing, silently, which is exactly the kind of bold that goes missing
                // without anything failing.
                names = listOf(
                    stringResource(R.string.shizuku_rikka_name_rikka),
                    stringResource(R.string.shizuku_rikka_name_unsupported),
                ),"""

OLD_COMMENT = """    <!-- The phrases the two red descriptions bold. Held apart rather than positioned, so a
      translation can move them and still be found. shizuku_fork_shevery carries the third. -->"""

NEW_COMMENT = """    <!-- The phrases the two red descriptions bold. Held apart rather than positioned, so a
      translation can move them and still be found. Shevery used to carry a fourth; r4m took
      it out of the first line, and its name left the emphasis list with it. -->"""

OLD_DEFERRED = """    "shizuku_rikka_name_rikka","""

NEW_DEFERRED = """    # r4m: the first red line went singular when Shevery came out of it.
    "shizuku_rikka_warning",
    "shizuku_rikka_name_rikka","""


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in (
        (STRINGS, "shizuku_rikka_warning", OLD_STRING, NEW_STRING),
        (SCREEN, "the emphasis names", OLD_NAMES, NEW_NAMES),
        (CHECK, "the DEFERRED set", OLD_DEFERRED, NEW_DEFERRED),
        (STRINGS, "the emphasis comment", OLD_COMMENT, NEW_COMMENT),
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

    # ⚠ **Both surviving bold phrases must still occur verbatim in the new sentence.** This is
    # the emphasised() trap, asserted rather than assumed - it is the third time this project
    # has been bitten by a name that matched nothing.
    strings = staged[ROOT / STRINGS]

    sentence = NEW_STRING.split(">", 1)[1].rsplit("<", 1)[0]

    for key in ("shizuku_rikka_name_rikka", "shizuku_rikka_name_unsupported"):
        value = strings.split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

        if value not in sentence:
            print(f"REFUSED: bold phrase {value!r} does not occur in the new sentence")
            return 1

    # And the one that left must no longer occur, or removing it from the list would be wrong.
    # ⚠ The declaration carries `translatable="false"`, so it cannot be found by name alone.
    shevery = re.search(
        r'<string name="shizuku_fork_shevery"[^>]*>(.*?)</string>', strings,
    ).group(1)

    if shevery in sentence:
        print(f"REFUSED: {shevery!r} still occurs in the sentence but was dropped from names")
        return 1

    # The English sentence reads as one grammatical clause: singular subject, singular verb.
    for wrong in (" are not supported", "as they do not", "&amp; Shevery"):
        if wrong in sentence:
            print(f"REFUSED: the new sentence still carries {wrong!r}")
            return 1

    # `shizuku_fork_shevery` is used elsewhere - the fork picker itself - so this must not have
    # orphaned the string.
    screen = staged[ROOT / SCREEN]

    if "R.string.shizuku_fork_shevery" not in screen:
        print("REFUSED: shizuku_fork_shevery is now unreferenced in SettingsScreen")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {STRINGS}")
    print(f"  ok        {SCREEN}  :: shevery out of the emphasis names")
    print(f"  ok        {CHECK}  :: key deferred")
    print(f"\n  now: {sentence}")
    print("\nwrote 3 file(s), 3 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
