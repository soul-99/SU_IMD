#!/usr/bin/env python3
"""
v3-r10 — the five new strings join the deferred list, and the translation baseline holds.

⚠ **The author's standing rule: *"do not run or touch translations"*.** New English strings are
therefore not copied into the locales; they are named here, which is what the header on that set
says it is for - *"this set is the list that final pass works from"*. A new string that was not
listed would show up as a missing translation and quietly move the baseline, which is exactly the
signal this check exists to give.

The five are the two switches the r10 round added, their two subtitles, and the alternative title
the blur switch wears on a device that cannot blur.

⚠ **The baseline is asserted, not assumed.** This script runs the checker before and after and
refuses - reverting its own edit - unless the problem count is identical. Adding a name to this
set is the one edit in the repository that can *hide* a real problem, so it is the one edit that
proves it did not.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECK = ROOT / "tools/check_translations.py"

OLD = '''    # And the fork rename of one row label, which this module needed a copy of because the two
    # dialogs already using these six labels never rename it.
    "revert_defaults_shevery",
}
'''

NEW = '''    # And the fork rename of one row label, which this module needed a copy of because the two
    # dialogs already using these six labels never rename it.
    "revert_defaults_shevery",
    # r10: the two new User interface switches and their subtitles, plus the name the blur
    # switch wears below Android 12, where there is no blur to be had and the band is the fade
    # alone. All five are the author's own words.
    "oled_background_mode",
    "oled_background_mode_summary",
    "progressive_ui_blur",
    "progressive_ui_blur_summary",
    "ui_fade",
}
'''

ADDED = (
    "oled_background_mode",
    "oled_background_mode_summary",
    "progressive_ui_blur",
    "progressive_ui_blur_summary",
    "ui_fade",
)


def problems() -> int:
    """How many the checker reports right now."""
    out = subprocess.run(
        [sys.executable, str(CHECK)], capture_output=True, text=True, check=False,
    ).stdout

    for line in out.splitlines():
        if line.strip().endswith("PROBLEMS"):
            return int(line.split()[0])

        if line.strip() == "OK" or line.strip().endswith("no problems"):
            return 0

    print("REFUSED: could not read a problem count out of the checker")
    print(out[-800:])

    return -1


def main() -> int:
    if not CHECK.is_file():
        print("REFUSED: missing tools/check_translations.py")
        return 1

    original = CHECK.read_text(encoding="utf-8")

    if OLD not in original:
        print("REFUSED: the end of the DEFERRED set is not where this expects it")
        return 1

    if original.count(OLD) != 1:
        print(f"REFUSED: the anchor matches {original.count(OLD)} times, expected 1")
        return 1

    for name in ADDED:
        if f'"{name}",' in original:
            print(f"REFUSED: {name!r} is already deferred — has this run before?")
            return 1

    # ⚠ **Before, with the strings in the source but not in the set.** This is the number the
    # edit has to bring back down, and it is measured rather than remembered.
    before = problems()

    if before < 0:
        return 1

    CHECK.write_text(original.replace(OLD, NEW, 1), encoding="utf-8")

    after = problems()

    if after != before - len(ADDED):
        CHECK.write_text(original, encoding="utf-8")

        print(
            f"REFUSED and reverted: {before} problems before, {after} after; "
            f"expected {before - len(ADDED)}",
        )

        return 1

    print(f"  ok  {before} -> {after} problems; the five r10 strings are deferred, nothing else")

    return 0


if __name__ == "__main__":
    sys.exit(main())
