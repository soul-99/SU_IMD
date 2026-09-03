#!/usr/bin/env python3
"""v3-r4u — picking a fork starts the search for Shizuku instead of guessing from an empty list.

    "in shizuku config initialisation screen a toggle is selected by user start to autosearch the
     shizuku and autfill the app package name"

## ⚠ The autofill already exists. What is missing is the list it needs

`commitFork` has filled the package and the start action since the fork picker was written:

    val suggested = ShizukuForkDefaults.packageFor(mode = mode, apps = installedApps)

It works in Settings and does nothing on the setup page, and the reason is `installedApps`.
Settings loads that list as part of the screen; **setup has not read it yet** when the user picks
a fork on the second page, so `packageFor` searches an empty list, finds nothing, and writes
blank. The user then has to find the ⟳ button to make the very search the app was about to do.

So this is not a new autofill. It is `commitFork` noticing it searched nothing and asking for the
list — the same request the ⟳ button makes, through the same effect, with the same spinner, so the
user sees a search happening rather than an empty box.

## ⚠ An automatic search never clears a field; the button still does

The refresh effect wrote its result unconditionally, which is right for the ⟳ button — pressing it
and getting a blank field back is the app saying *"nothing found"*. It is wrong for a search the
user did not ask for: silently emptying a package name they typed by hand would be the app
overwriting an answer. So the automatic pass writes only when it found something, and the manual
one behaves exactly as it did.

## ⚠ The start action is recomputed too, and only in the automatic case

`actionFor` depends on the label of the selected package, which the first attempt did not have.
For the Thedjchi family the answer is constant and nothing changes; for **Other** it is Shevery's
action or Shizuku's depending on what was found, so a package discovered by the search has to
re-decide it. The manual button is left writing the package alone, as before.

## ⚠ Read through `rememberUpdatedState`, not captured

The effect waits for a package-manager round trip, which is long enough for the user to change
their mind and pick the other fork. `forkMode` was captured at launch; it is now read live, so a
search that lands after a second choice fills in for the second one.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. The flag that tells the two callers apart, and a live read of the fork.
    (
        """    var refreshTick by remember { mutableIntStateOf(0) }

    // rememberUpdatedState so the snapshotFlow below observes the *current* values: both are
    // plain parameters, and a flow built over one directly would capture a single value
    // forever.
    val latestApps by rememberUpdatedState(installedApps)

    val latestRevision by rememberUpdatedState(installedAppsRevision)""",
        """    var refreshTick by remember { mutableIntStateOf(0) }

    // ⚠ **Which of the two started the refresh in flight.** The ⟳ button and picking a fork run
    // the same search, and they must not do the same thing with a blank result: an empty field
    // after a press the user made says "nothing found", and an empty field after a search they
    // did not ask for is the app deleting their answer.
    var refreshIsAuto by remember { mutableStateOf(false) }

    // rememberUpdatedState so the snapshotFlow below observes the *current* values: both are
    // plain parameters, and a flow built over one directly would capture a single value
    // forever.
    val latestApps by rememberUpdatedState(installedApps)

    val latestRevision by rememberUpdatedState(installedAppsRevision)

    // ⚠ Live rather than captured, for the same reason. The effect below waits on a package
    // manager round trip — long enough for the user to pick the other family — and a search that
    // lands afterwards must fill in for the family they are now looking at.
    val latestForkMode by rememberUpdatedState(forkMode)""",
    ),
    # 2. What the effect does with what it found.
    (
        """        packageName = ShizukuForkDefaults.packageFor(mode = forkMode, apps = latestApps)

        refreshing = false
    }""",
        """        val suggested = ShizukuForkDefaults.packageFor(
            mode = latestForkMode,
            apps = latestApps,
        )

        // ⚠ The automatic pass writes only what it found; the button writes whatever it got,
        // blank included, because that is how it reports "nothing found".
        if (suggested.isNotBlank() || !refreshIsAuto) {
            packageName = suggested
        }

        // ⚠ And only the automatic pass touches the action. The first attempt decided it without
        // a package to look at, which for the Other family is the difference between Shevery's
        // action and Shizuku's. The button has never written this and still does not.
        if (refreshIsAuto && suggested.isNotBlank()) {
            startAction = ShizukuForkDefaults.actionFor(
                mode = latestForkMode,
                selectedLabel = latestApps.labelOf(suggested),
            )
        }

        refreshIsAuto = false

        refreshing = false
    }""",
    ),
    # 3. Picking a fork asks for the list when the one in hand had nothing.
    (
        """        startAction = ShizukuForkDefaults.actionFor(
            mode = mode,
            selectedLabel = installedApps.labelOf(suggested),
        )

        onUpdateShizukuForkMode(mode)
    }""",
        """        startAction = ShizukuForkDefaults.actionFor(
            mode = mode,
            selectedLabel = installedApps.labelOf(suggested),
        )

        onUpdateShizukuForkMode(mode)

        // ⚠ **Nothing found, which during setup usually means nothing was searched.** Settings
        // has the installed list already; the setup page has not read it by the time the user
        // picks a family on page two, so the guess above ran against an empty list. This is the
        // author's *"start to autosearch"*: the same request the ⟳ button makes, through the
        // same effect and the same spinner, so a search is visibly happening rather than a box
        // being silently blank.
        if (suggested.isBlank()) {
            refreshIsAuto = true

            refreshTick += 1
        }
    }""",
    ),
]

AFTER = [
    ("refreshIsAuto", 5),
    ("val latestForkMode by rememberUpdatedState(forkMode)", 1),
    ("mode = latestForkMode,", 2),
    # The old unconditional write is gone.
    ("packageName = ShizukuForkDefaults.packageFor(mode = forkMode, apps = latestApps)", 0),
    # The manual button's own entry point is untouched.
    ("refreshTick += 1", 2),
]


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {SCREEN}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # Everything the new lines lean on already exists in this file.
    for token in (
        "private fun List<InstalledAppData>.labelOf(",
        "import androidx.compose.runtime.rememberUpdatedState",
        "import androidx.compose.runtime.mutableStateOf",
    ):
        if token not in text:
            print(f"REFUSED: {SCREEN}\n  {token!r} is absent")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: picking a fork searches for the app when the list is empty")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
