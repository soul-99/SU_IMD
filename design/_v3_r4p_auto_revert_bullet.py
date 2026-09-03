#!/usr/bin/env python3
"""v3-r4p — the auto-revert notice drops its "works for both" sub-point.

The author: *"for auto revert on returning dialog remove this bullet point It works for both..."*
— `auto_revert_notice_trigger_both`, the second sub-point under numbered point 2.

## ⚠ The call site goes; the string stays

`tools/check_translations.py` checks that "no name has been invented" in a locale file, so a
name present in ten translations and absent from `values/strings.xml` is reported as ten
invented names. Deleting the English entry therefore means editing all ten locales in the same
breath — and the standing rule is **do not touch translations**.

An unused string costs a few bytes in the APK and trips no audit in this repo (there is no
unused-resource check in `toolkit/run_all.sh`). A broken translation check costs a round. So the
resource and its ten translations are left exactly where they are, and only the line that draws
them is removed. If the author ever wants the string gone as well, it goes in the same pass that
does the translations.

## What is asserted

* the sub-point's call site occurs exactly once, with its neighbours, in the order shown;
* the *example* sub-point above it survives — it is the one that must not be caught by a
  loose match, since the two lines differ only in the resource name;
* the string resource is still present in `values/strings.xml` afterwards, so a future reader
  finds the deferral rather than a mystery.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoRevertNoticeDialog.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

# ⚠ **Anchored on both neighbours, not on the line alone.** `SubPoint(text = stringResource(`
# appears four times in this file; what makes this one identifiable is that it sits between the
# example sub-point and numbered point 3.
OLD = """        SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_example))

        SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_both))

        NumberedPoint(
            number = 3,"""

NEW = """        SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_example))

        NumberedPoint(
            number = 3,"""

# Kept, and asserted to be kept - see the note above.
KEPT_STRING = '<string name="auto_revert_notice_trigger_both">'

# Asserted to survive the edit: it differs from the removed line only in the resource name.
SURVIVES = "SubPoint(text = stringResource(R.string.auto_revert_notice_trigger_example))"

GONE = "auto_revert_notice_trigger_both"


def main() -> int:
    dialog = ROOT / DIALOG

    strings = ROOT / STRINGS

    for path in (dialog, strings):
        if not path.is_file():
            print(f"REFUSED: missing {path.relative_to(ROOT)}")
            return 1

    text = dialog.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {DIALOG}\n  the sub-point block matched {found} time(s), expected 1")
        return 1

    staged = text.replace(OLD, NEW, 1)

    if staged.count(SURVIVES) != 1:
        print(f"REFUSED: {DIALOG}\n  the example sub-point did not survive the edit")
        return 1

    if GONE in staged:
        print(f"REFUSED: {DIALOG}\n  the removed sub-point is still referenced")
        return 1

    # The resource itself is deliberately untouched. Read rather than written, so a future
    # translation pass finds it where it has always been.
    if KEPT_STRING not in strings.read_text(encoding="utf-8"):
        print(f"REFUSED: {STRINGS}\n  the string resource is already gone; nothing to keep")
        return 1

    dialog.write_text(staged, encoding="utf-8")

    print(f"  ok        {DIALOG}  :: 'It works for both...' sub-point removed")
    print(f"  ok        {STRINGS}  :: resource left in place for the translation pass")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
