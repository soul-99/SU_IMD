#!/usr/bin/env python3
"""v3-r4p — the IMD intents page lists its four functions in the author's order.

    "in the imd intents show intents in this order:
     settings maanger / hide set / unhide set / rev to def"

Today the page reads Settings Manager, Revert to default, Unhide, Hide — the order they were
built in rather than the order somebody sets them up in. The requested order is the order of a
session: open the manager, hide, unhide, and revert to defaults as the way out.

## ⚠ The comment moves with the section it is about

The eight-line note above the Unhide section explains why *that* section is no longer conditional.
Left in place it would sit above Hide and describe the wrong thing — the comment trap this project
has now hit seven times, in its other direction: a comment that stays put while the code under it
is replaced says something false about its new neighbour.

## What is asserted

* the three broadcast sections and the note occur exactly once each, as one contiguous block;
* the Settings Manager section above them is untouched — it is an activity, not a broadcast, and
  is not part of the move;
* after the edit the four titles appear in the requested order, checked by their positions in
  the file rather than by their presence.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/TaskerIntegrationPage.kt"

OLD = """        BroadcastSection(
            title = stringResource(R.string.tasker_fn_revert_default),
            packageName = packageName,
            action = TaskerIntegration.ACTION_REVERT_TO_DEFAULT,
        )

        // ⚠ **Not conditional any more, and that is the change.** Its predecessor appeared
        // only under the memory function, because offering it in the other mode would have
        // documented a button the user had not chosen. This one settles whatever is
        // outstanding the way the current Unhiding framework says, so it is the right thing
        // to offer under either — and it is the route that answers the old objection to the
        // memory function, that a lost notification leaves no way back.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_unhide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_UNHIDE_SETTINGS,
        )

        BroadcastSection(
            title = stringResource(R.string.tasker_fn_hide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_HIDE_SETTINGS,
        )"""

NEW = """        BroadcastSection(
            title = stringResource(R.string.tasker_fn_hide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_HIDE_SETTINGS,
        )

        // ⚠ **Not conditional any more, and that is the change.** Its predecessor appeared
        // only under the memory function, because offering it in the other mode would have
        // documented a button the user had not chosen. This one settles whatever is
        // outstanding the way the current Unhiding framework says, so it is the right thing
        // to offer under either — and it is the route that answers the old objection to the
        // memory function, that a lost notification leaves no way back.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_unhide),
            packageName = packageName,
            action = TaskerIntegration.ACTION_UNHIDE_SETTINGS,
        )

        // ⚠ **Last, at the author's instruction**: manager, hide, unhide, revert. It is the
        // order of a session rather than the order these were built in.
        BroadcastSection(
            title = stringResource(R.string.tasker_fn_revert_default),
            packageName = packageName,
            action = TaskerIntegration.ACTION_REVERT_TO_DEFAULT,
        )"""

# The activity section stays exactly where it is, above all three broadcasts.
UNTOUCHED = "FunctionSection(title = stringResource(R.string.tasker_fn_services)) {"

# Checked by position after the edit, not by presence.
ORDER = [
    "R.string.tasker_fn_services)",
    "R.string.tasker_fn_hide)",
    "R.string.tasker_fn_unhide)",
    "R.string.tasker_fn_revert_default)",
]


def main() -> int:
    path = ROOT / PAGE

    if not path.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {PAGE}\n  the three-section block matched {found} time(s), expected 1")
        return 1

    if text.count(UNTOUCHED) != 1:
        print(f"REFUSED: {PAGE}\n  the Settings Manager section is not where it was")
        return 1

    staged = text.replace(OLD, NEW, 1)

    if staged.count(UNTOUCHED) != 1:
        print(f"REFUSED: {PAGE}\n  the Settings Manager section did not survive the edit")
        return 1

    positions = []

    for token in ORDER:
        if staged.count(token) != 1:
            print(f"REFUSED: {PAGE}\n  {token} occurs {staged.count(token)} time(s), expected 1")
            return 1

        positions.append(staged.index(token))

    if positions != sorted(positions):
        print(f"REFUSED: {PAGE}\n  the four functions are not in the requested order")
        return 1

    path.write_text(staged, encoding="utf-8")

    print(f"  ok        {PAGE}  :: manager, hide, unhide, revert to default")
    print("  ok        the note moved with the Unhide section it describes")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
