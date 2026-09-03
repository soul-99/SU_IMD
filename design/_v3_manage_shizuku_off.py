#!/usr/bin/env python3
"""r4j — with Manage Shizuku off, the two rows it governs leave the manager and DOOA reads off.

Two instructions:

    "if manage shizuku is toggled off in settings hide shizuku and dooa both toggles in
     settings manager"

    "in settings to hide and revert to def config window show dooa toggle unchecked along with
     being unclickable when manage shizuku toggle is off, but remember the previous state of the
     checkboxes if manage shizuku is turned on in future"

and one correction, which is why this script is smaller than it looks:

    "instead show the one we made already for dooa checkboxes when manage shizuku toggle is off"

### 1. The manager drops both rows

`rows(manageShizuku)` already dropped the Shizuku row; it now drops Display over other apps with
it. Overlay access is written through Shizuku and nothing else, so with Manage Shizuku off that
row is a switch for a mechanism the user has turned off — and unlike a row that is merely
unusable, there is no state worth showing and no configuring that would make it movable while
the master switch is off.

⚠ **`usableTargets` is derived from the drawn rows**, so the master pill stops touching overlay
access for free rather than needing to be told separately.

### 2. The two configuration dialogs show it unchecked, and forget nothing

⚠ **Almost all of this already existed**, which the author spotted before I built anything new.
`SettingsToHideDialog` and `RevertDefaultsDialog` both take `overlayBlockedPaths`, both already
pass `enabled = overlayBlockedPaths == null`, and both already answer a press with the
`ConfigureFirstDialog` naming the path to Manage Shizuku. Blocked and explained: done since r4.

The one thing missing was the author's *"show dooa toggle unchecked"*, so the checkbox now reads

    checked = overlayBlockedPaths == null && draft[DisplayOverOtherApps] == true

⚠ **A display test, not a write.** `draft` is untouched, so the stored selection survives being
blocked — which is the author's *"remember the previous state … if manage shizuku is turned on in
future"*. Saving while blocked writes the same `draft` back, so even a Save in that state
preserves the choice rather than quietly clearing it.

⚠ **`== null` rather than `isNullOrEmpty()`.** An empty list is the Shevery case — blocked
because the fork cannot do it at all — and it is still blocked; only *no list* means allowed.
That is the existing convention on the line above, kept.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
TO_HIDE = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
           "SettingsToHideDialog.kt")
DEFAULTS = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
            "RevertDefaultsDialog.kt")

CHECKBOX_OLD = """            checked = draft[ManualRevertTarget.DisplayOverOtherApps] == true,
            enabled = overlayBlockedPaths == null,
"""

CHECKBOX_NEW = """            // ⚠ **Unchecked while blocked, at the author's instruction - and only in the
            // drawing.** `draft` is not touched, so the stored selection survives Manage
            // Shizuku being switched off and comes back when it is switched on again; a Save
            // taken in this state writes the same draft back rather than quietly clearing it.
            //
            // `== null` and not `isNullOrEmpty()`: an empty list is the Shevery case, blocked
            // because the fork cannot do this at all, and it is still blocked. Only no list
            // at all means allowed - the convention the line below has always used.
            checked = overlayBlockedPaths == null &&
                draft[ManualRevertTarget.DisplayOverOtherApps] == true,
            enabled = overlayBlockedPaths == null,
"""

ROWS_OLD = """private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> =
    if (manageShizuku) {
        ManualRevertTarget.entries
    } else {
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku
        }
    }
"""

ROWS_NEW = """private fun rows(manageShizuku: Boolean): List<ManualRevertTarget> =
    if (manageShizuku) {
        ManualRevertTarget.entries
    } else {
        // ⚠ **Both rows, at the author's instruction.** Overlay access is written through
        // Shizuku and through nothing else, so with Manage Shizuku off that row is a switch
        // for a mechanism the user has turned off. Unlike a row that is merely unusable there
        // is no live state worth showing and no configuring that would make it movable while
        // the master switch is down, so it leaves rather than sitting there refusing.
        //
        // `usableTargets` is filtered from what is drawn, so the master pill stops touching
        // overlay access as a consequence of this rather than needing to be told.
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku &&
                it != ManualRevertTarget.DisplayOverOtherApps
        }
    }
"""


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in (
        (MANAGER, [(ROWS_OLD, ROWS_NEW, 1)]),
        (TO_HIDE, [(CHECKBOX_OLD, CHECKBOX_NEW, 1)]),
        (DEFAULTS, [(CHECKBOX_OLD, CHECKBOX_NEW, 1)]),
    ):
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    manager = staged[ROOT / MANAGER]

    # ⚠ Asserted against code, never the prose around it.
    for rel, text, token, expected in (
        (MANAGER, manager, "it != ManualRevertTarget.Shizuku &&", 1),
        (MANAGER, manager, "it != ManualRevertTarget.DisplayOverOtherApps", 1),
        (TO_HIDE, staged[ROOT / TO_HIDE], "checked = overlayBlockedPaths == null &&", 1),
        (DEFAULTS, staged[ROOT / DEFAULTS], "checked = overlayBlockedPaths == null &&", 1),
        # The block and its explanation are untouched: both dialogs keep the r4 mechanism.
        (TO_HIDE, staged[ROOT / TO_HIDE], "enabled = overlayBlockedPaths == null,", 1),
        (DEFAULTS, staged[ROOT / DEFAULTS], "enabled = overlayBlockedPaths == null,", 1),
        # ⚠ Two: accessibility services has the same blocked treatment, and an earlier draft of
        # this assertion counted only the overlay one and refused.
        (TO_HIDE, staged[ROOT / TO_HIDE], "onBlockedClick = {", 2),
        (DEFAULTS, staged[ROOT / DEFAULTS], "onBlockedClick = {", 2),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # ⚠ **The draft must not be written from this.** Blocking is a drawing decision; a write
    # here would be the thing the author asked us not to do - forgetting the selection.
    for rel in (TO_HIDE, DEFAULTS):
        text = staged[ROOT / rel]

        if "draft = draft + (ManualRevertTarget.DisplayOverOtherApps to false)" in text:
            problems.append(f"{rel}: something clears the stored overlay selection")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - both rows leave the manager, and DOOA reads off without forgetting anything")

    return 0


if __name__ == "__main__":
    sys.exit(main())
