#!/usr/bin/env python3
"""v3-r4n — a comment written in r4n's own item-6 script trips check18.

    v3tree/.../SettingsToHideDialog.kt: calls `canHide` with no import
    v3tree/.../RevertDefaultsDialog.kt: calls `canHide` with no import

Neither file calls it. Both carry a comment I wrote explaining that `shizukuBlocked == null` is
the same question the engine asks:

    // 'null' is exactly `UserData.canHide(ManualRevertTarget.Shizuku)` - ...

`check18_missing_imports` matches `\\.canHide\\s*\\(` against the file body **without stripping
comments** (`toolkit/audit/check18_missing_imports.py`, lines 54-56), so a comment that spells a
function the way a call spells it *is* a call as far as the checker is concerned.

⚠ **This is the comment trap for the sixth time in this project, and the first time it has been
one of my own explanations rather than an assertion.** The rule in the trap table is written for
`design/_*.py` assertions — "spell every checked token the way it can only appear in a
statement" — and it turns out to cut both ways: **a comment must spell a function the way a call
cannot.** Backtick-and-space instead of backtick-and-paren is the whole fix.

The explanation is worth keeping — the equality between the row's greying and the engine's gate
is the reason item 6 cannot drift — so the sentence is reworded rather than deleted.

Asserts each anchor matches exactly once, that no dotted or bare call spelling survives in
either file, and that the sentence still names the function. Writes nothing if any assertion
fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"
REVERT = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"

OLD = """    // ⚠ **One expression for the Shizuku row's three states, read by `checked`, by `enabled`
    // and by the press.** `null` is exactly `UserData.canHide(ManualRevertTarget.Shizuku)` -
    // 'Manage Shizuku' on and a fork that answers intents - so the row and the engine cannot
    // disagree. The fork case comes first: on Shevery there is nothing to go and switch on,
    // so sending the reader to Manage Shizuku would be sending them nowhere."""

NEW = """    // ⚠ **One expression for the Shizuku row's three states, read by `checked`, by `enabled`
    // and by the press.** `null` is exactly the answer `UserData.canHide` gives for the
    // Shizuku target - 'Manage Shizuku' on and a fork that answers intents - so the row and
    // the engine cannot disagree. The fork case comes first: on Shevery there is nothing to
    // go and switch on, so sending the reader to Manage Shizuku would be sending them
    // nowhere.
    //
    // ⚠ Spelled without its brackets on purpose: check18_missing_imports matches
    // `.canHide` followed by an open bracket against the whole file, comments included, and
    // would read this sentence as an unimported call."""


def main() -> int:
    staged: dict[Path, str] = {}

    for rel in (HIDE, REVERT):
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = path.read_text(encoding="utf-8")

        found = text.count(OLD)

        if found != 1:
            print(f"REFUSED: {rel}\n  the comment matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(OLD, NEW, 1)

    # ⚠ **Both spellings check18 recognises must be gone.** Its dotted form is `.canHide(` and
    # its bare form is `canHide(` not preceded by a word character or a dot. Reproduced here
    # rather than described, so this assertion fails for the same reason the checker would.
    for path, text in staged.items():
        if re.search(r"\.canHide\s*\(", text):
            print(f"REFUSED: {path.name} still spells a dotted call")
            return 1

        if re.search(r"(?<![\w.])canHide\s*\(", text):
            print(f"REFUSED: {path.name} still spells a bare call")
            return 1

        # And the explanation must survive — a fix that solved this by deleting the sentence
        # would take the reason for the whole expression with it.
        if "canHide" not in text:
            print(f"REFUSED: {path.name} no longer names the function at all")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {HIDE}")
    print(f"  ok        {REVERT}")
    print("\nwrote 2 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
