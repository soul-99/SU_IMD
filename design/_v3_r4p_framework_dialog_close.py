#!/usr/bin/env python3
"""v3-r4p — the framework choosers close themselves once the save has landed.

    "also in unhiding and hiding framework dialog if all goes sucessful after save button press,
     close the dialog after save button press"

## ⚠ 'If all goes successful' is the whole instruction, and it rules out the easy version

Closing in the Save button's own click handler would also close on a **failure**, and a failed
save is the one case where the chooser has to stay: `saveFramework` sweeps the outstanding hides
first and, if anything survives, leaves the preference **unwritten** on purpose - so the dialog
would vanish having changed nothing, with the old framework still selected underneath.

The dialog is therefore closed by the save reporting success, not by the press.

## ⚠ A new state rather than watching for Idle to come back

`FrameworkSave` ran `Idle -> Running -> Idle`, and "Idle" cannot distinguish *finished* from
*never started*. Worse, the two writes are conflated by the `StateFlow` if they land between two
recompositions, so a screen watching for `Running` and then `Idle` can legitimately observe
neither. A distinct **`Saved`** is not conflatable away: the flow rests there until the screen
clears it, exactly as `Failed` already does.

`clearFrameworkSave()` already exists for `Failed`, so the clearing half needs nothing new.

## ⚠ The comment being replaced was right about its own case

    // Deliberately left open by the Save button. The spinner that may follow is
    // raised by the route above this screen, and closing this first would show the
    // settings list for a frame in between.

That is an argument against closing **on the press**, and it still holds - which is why this
does not do that. Closing on `Saved` happens after the spinner has already come and gone, so
there is no frame to show the list in.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VIEWMODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

# ⚠ The two signature tails are identical - `SettingsScreen` and `Success` end the same way -
# so each anchor carries the line that follows, which is the only thing that tells them apart.
SCREEN_TAIL = """    installedAppsRevision: Int,
) {
    // The scroll modifier lives on the content column rather than here: a Box that scrolls"""

SUCCESS_TAIL = """    installedAppsRevision: Int,
) {
    val context = LocalContext.current"""

NEW_PARAMS = """    installedAppsRevision: Int,
    /**
     * The last framework save finished and the preference was written.
     *
     * ⚠ Not "the save is over": a save that could not settle the outstanding hides reports
     * [FrameworkSave.Failed] and leaves the preference alone, and the chooser stays open over
     * it so the choice that did not take is still there.
     */
    frameworkSaved: Boolean,
    /** Clears [frameworkSaved], once the choosers above have acted on it. */
    onFrameworkSaveHandled: () -> Unit,
) {"""

EDITS: list[tuple[str, str, str]] = [
    # 1. The new state.
    (
        VIEWMODEL,
        """            store()

            _frameworkSave.update { FrameworkSave.Idle }""",
        """            store()

            // ⚠ **Saved rather than back to Idle.** Idle cannot tell "finished" from "never
            // started", and a StateFlow would conflate Running and Idle away entirely if both
            // landed between two recompositions - so a screen waiting for the save to finish
            // could legitimately observe neither. Saved rests here until the screen clears it,
            // the same shape Failed already has.
            _frameworkSave.update { FrameworkSave.Saved }""",
    ),
    (
        VIEWMODEL,
        """enum class FrameworkSave {
    Idle,""",
        """enum class FrameworkSave {
    Idle,

    /**
     * The sweep cleared and the preference was written.
     *
     * Rests here until [SettingsViewModel.clearFrameworkSave], which is what lets the framework
     * choosers close themselves on a save that worked and stay open on one that did not.
     */
    Saved,""",
    ),
    # 2. The route hands both halves down.
    (
        SCREEN,
        """        onRefreshInstalledApps = viewModel::refreshInstalledApps,
        installedAppsRevision = installedAppsRevision,
    )""",
        """        onRefreshInstalledApps = viewModel::refreshInstalledApps,
        installedAppsRevision = installedAppsRevision,
        frameworkSaved = frameworkSave == FrameworkSave.Saved,
        onFrameworkSaveHandled = viewModel::clearFrameworkSave,
    )""",
    ),
    # 3. Both signatures.
    (SCREEN, SCREEN_TAIL, NEW_PARAMS + SCREEN_TAIL[len("    installedAppsRevision: Int,\n) {"):]),
    (SCREEN, SUCCESS_TAIL, NEW_PARAMS + SUCCESS_TAIL[len("    installedAppsRevision: Int,\n) {"):]),
    # 4. And the hand-off between them.
    (
        SCREEN,
        """                    onRefreshInstalledApps = onRefreshInstalledApps,
                    installedAppsRevision = installedAppsRevision,""",
        """                    onRefreshInstalledApps = onRefreshInstalledApps,
                    installedAppsRevision = installedAppsRevision,
                    frameworkSaved = frameworkSaved,
                    onFrameworkSaveHandled = onFrameworkSaveHandled,""",
    ),
    # 5. The close itself, beside the two flags it closes.
    (
        SCREEN,
        """    var showRevertDefaultsDialog by rememberSaveable { mutableStateOf(false) }""",
        """    var showRevertDefaultsDialog by rememberSaveable { mutableStateOf(false) }

    // ⚠ **Closed by the save landing, never by the press** - the author's "if all goes
    // sucessful after save button press, close the dialog". A save that cannot settle the
    // outstanding hides leaves the preference unwritten, so closing on the press would take
    // the chooser away having changed nothing.
    //
    // Both flags are cleared without asking which chooser was open: only one can be, and a
    // false on a flag that is already false is not a recomposition.
    LaunchedEffect(frameworkSaved) {
        if (!frameworkSaved) return@LaunchedEffect

        showHidingFrameworkDialog = false

        showUnhidingFrameworkDialog = false

        onFrameworkSaveHandled()
    }""",
    ),
    # 6. The comment that argued against closing on the press, kept and finished.
    (
        SCREEN,
        """            // Deliberately left open by the Save button. The spinner that may follow is
            // raised by the route above this screen, and closing this first would show the
            // settings list for a frame in between.
            onSave = onSaveHidingFramework,""",
        """            // Deliberately left open by the Save button itself. The spinner that may
            // follow is raised by the route above this screen, and closing this first would
            // show the settings list for a frame in between.
            //
            // ⚠ It is closed by the effect above instead, once the save reports Saved - which
            // is after the spinner has come and gone, so there is no frame to show the list in,
            // and a save that failed leaves it open.
            onSave = onSaveHidingFramework,""",
    ),
]

AFTER = [
    # One use. The enum member itself is spelled "Saved," inside the declaration, not
    # "FrameworkSave.Saved" - the first draft counted a declaration it had written as a
    # qualified reference.
    (VIEWMODEL, "FrameworkSave.Saved", 1),
    (VIEWMODEL, "\n    Saved,", 1),
    (VIEWMODEL, "FrameworkSave.Idle", 2),
    # Three, two of them in KDoc: the flow's own doc, saveFramework's doc, and the one write.
    # Counted from the file as it stands, not guessed.
    (VIEWMODEL, "FrameworkSave.Failed", 3),
    # Nine: the route's argument, then twice in each of the two parameter blocks (the
    # declaration and the sibling KDoc that names it), twice in the hand-off between them, and
    # twice in the effect. The parameter block is inserted into both signatures, so anything it
    # contains is counted twice - which is what the first draft's 6 forgot.
    (SCREEN, "frameworkSaved", 9),
    (SCREEN, "onFrameworkSaveHandled", 6),
    (SCREEN, "showHidingFrameworkDialog = false", 2),
    (SCREEN, "showUnhidingFrameworkDialog = false", 2),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # LaunchedEffect is new to this composable but not to the file; asserted rather than added.
    if "import androidx.compose.runtime.LaunchedEffect" not in staged[SCREEN]:
        print(f"REFUSED: {SCREEN}\n  LaunchedEffect is used but not imported")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {VIEWMODEL}  :: FrameworkSave.Saved")
    print(f"  ok        {SCREEN}  :: both choosers close on a save that landed")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
