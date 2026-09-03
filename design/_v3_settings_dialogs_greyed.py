#!/usr/bin/env python3
"""
v3-r4m-b — the two configuration dialogs: the Shizuku row greys, greyed rows draw unticked,
and the "x of y" summary counts what is drawn.

Three of the five gaps found while closing "disabled toggles dont run for IMD+", answered by
the author:

  4. **The Shizuku row was drawn live with 'Manage Shizuku' off**, in both Settings to
     hide/unhide and Revert to default configuration. Spec item 9 asks for it greyed and
     unclickable there. Neither dialog was told the master switch's value.
  5a. **A greyed row drew ticked.** Display over other apps already drew unticked; the
     accessibility row did not. The author: *"Unticked everywhere"* - and the tick is only
     hidden in the drawing, never in the draft, so a Save in that state writes the same map
     back and the answer returns when the thing it needs is configured again.
  5b. **The summary disagreed with the rows.** `withoutOverlayWhenUnmanaged` dropped Display
     over other apps out of the count, from back when that row was not drawn at all - but it
     has been drawn for everyone since r4. The author: *"Counted in the total, not in the
     ticked count"*, so every row the dialog draws is in `y` and only the rows that will run
     are in `x`.

⚠ **`x` comes from `effectiveSettingsToHide` for the hide dialog**, which is the map the launch
paths read - so the number the user sees is, by construction, the number of settings that will
actually be hidden.

⚠ **The revert dialog counts its stored ticks instead, and that is not an oversight.** Reverts
are deliberately not gated (the author's decision): a revert still hands back anything IMD
already took, whatever the row says. So on that side every drawn row can still run, and
`effectiveRevertDefaults` would be the wrong map to count - it forces the overlay entry true
while a debt is outstanding, which is a debt rather than a configuration.

⚠ **The Shizuku row is still not drawn at all on a fork with no intents.** That is unchanged and
deliberate; bringing it back is the stop-intent round.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOGS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog"

HIDE = f"{DIALOGS}/SettingsToHideDialog.kt"
REVERT = f"{DIALOGS}/RevertDefaultsDialog.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

PARAM = """    /** Whether anything at all is selected under 'Accessibility services to hide'. */
    accessibilityManageable: Boolean,"""

PARAM_NEW = """    /** Whether anything at all is selected under 'Accessibility services to hide'. */
    accessibilityManageable: Boolean,
    /**
     * Whether 'Manage Shizuku' is on **and** the configuration under it is complete.
     *
     * The effective value, never the stored one - see `UserData.manageShizukuEffective`. With
     * it off IMD is not driving that service at all, so the row below greys rather than
     * offering to hide something the master switch has said no to.
     */
    manageShizukuEffective: Boolean,"""

PATH_DECL = """    val accessibilityPath = stringResource(R.string.help_path_accessibility)"""

PATH_DECL_NEW = """    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)"""

# --- Settings to hide/unhide ------------------------------------------------------------

HIDE_ACCESSIBILITY_OLD = """            enabled = accessibilityManageable,
            onBlockedClick = { blockedPaths = listOf(accessibilityPath) },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )"""

HIDE_ACCESSIBILITY_NEW = """            enabled = accessibilityManageable,
            onBlockedClick = { blockedPaths = listOf(accessibilityPath) },
            onCheckedChange = { toggle(ManualRevertTarget.AccessibilityServices, it) },
        )"""

HIDE_SHIZUKU_OLD = """            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.settings_to_hide_shizuku_note),
                checked = draft[ManualRevertTarget.Shizuku] == true,
                onCheckedChange = { wanted ->
                    toggle(ManualRevertTarget.Shizuku, wanted)

                    // Only on the way on, and only then. Both forks need something switched
                    // in their own app before IMD can drive their service, and neither says
                    // so anywhere the user would look - the failure is silent and arrives
                    // later, at the moment a hide is supposed to work.
                    if (wanted) showShizukuServiceNotice = true
                },
            )"""

HIDE_SHIZUKU_NEW = """            SettingToHideRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.settings_to_hide_shizuku_note),
                // ⚠ **Unticked while blocked, and only in the drawing** - the same rule the
                // two rows around it follow. `draft` is untouched, so the stored answer
                // survives 'Manage Shizuku' being switched off and comes back when it is
                // switched on again; a Save taken in this state writes the same draft back.
                checked = manageShizukuEffective &&
                    draft[ManualRevertTarget.Shizuku] == true,
                // ⚠ **Spec item 9, and it was missing.** This row was drawn live with the
                // master switch off, offering to stop a service IMD is not managing - and
                // since r4m the hide would have refused it anyway, so the control was a
                // promise the engine had already broken.
                enabled = manageShizukuEffective,
                onBlockedClick = { blockedPaths = listOf(manageShizukuPath) },
                onCheckedChange = { wanted ->
                    toggle(ManualRevertTarget.Shizuku, wanted)

                    // Only on the way on, and only then. Both forks need something switched
                    // in their own app before IMD can drive their service, and neither says
                    // so anywhere the user would look - the failure is silent and arrives
                    // later, at the moment a hide is supposed to work.
                    if (wanted) showShizukuServiceNotice = true
                },
            )"""

HIDE_ACC_CHECKED_OLD = """            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            // ⚠ **Dead with nothing selected**, on the author's instruction."""

HIDE_ACC_CHECKED_NEW = """            // Unticked while blocked, in the drawing only. See the Shizuku row below.
            checked = accessibilityManageable &&
                draft[ManualRevertTarget.AccessibilityServices] == true,
            // ⚠ **Dead with nothing selected**, on the author's instruction."""

# --- Revert to default configuration -----------------------------------------------------

REVERT_ACC_OLD = """            checked = draft[ManualRevertTarget.AccessibilityServices] == true,
            // Dead with nothing selected, exactly as in Settings to hide/unhide - see the
            // matching row there for why IMD+'s own detector is not part of this question."""

REVERT_ACC_NEW = """            // Unticked while blocked, in the drawing only - the author's rule for every
            // greyed control. The draft keeps the stored answer.
            checked = accessibilityManageable &&
                draft[ManualRevertTarget.AccessibilityServices] == true,
            // Dead with nothing selected, exactly as in Settings to hide/unhide - see the
            // matching row there for why IMD+'s own detector is not part of this question."""

REVERT_SHIZUKU_OLD = """            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.revert_defaults_shizuku_note),
                checked = draft[ManualRevertTarget.Shizuku] == true,
                onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
            )"""

REVERT_SHIZUKU_NEW = """            RevertDefaultRow(
                label = stringResource(R.string.revert_defaults_shizuku),
                note = stringResource(R.string.revert_defaults_shizuku_note),
                // Unticked and greyed with 'Manage Shizuku' off, in the drawing only - spec
                // item 9 names this dialog as well as the hide one.
                checked = manageShizukuEffective &&
                    draft[ManualRevertTarget.Shizuku] == true,
                enabled = manageShizukuEffective,
                onBlockedClick = { blockedPaths = listOf(manageShizukuPath) },
                onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },
            )"""

# --- the screen: the summaries, and the new argument ------------------------------------

SCREEN_SUMMARY_OLD = """    val hideStates = userData.settingsToHide
        .withoutOverlayWhenUnmanaged(userData.overlayManageable)
        .withoutShizukuWhenNoIntents(userData.shizukuForkMode)

    val revertStates = userData.revertDefaults
        .withoutOverlayWhenUnmanaged(userData.overlayManageable)
        .withoutShizukuWhenNoIntents(userData.shizukuForkMode)"""

SCREEN_SUMMARY_NEW = """    // ⚠ **Every row the dialog draws is counted, and only the rows that will run are ticked.**
    // The author's rule for the summary. `withoutOverlayWhenUnmanaged` used to drop Display
    // over other apps out of both numbers, which was right while that row was hidden - it has
    // been drawn for everyone since r4, so the summary had been reading one row short.
    //
    // `effectiveSettingsToHide` is the map the launch paths actually read, so `x` is the
    // number of settings that will really be hidden rather than the number ticked. A row
    // greyed because it cannot work therefore leaves the count and stays in the total.
    val hideStates = userData.effectiveSettingsToHide

    // ⚠ **The stored ticks, not the effective map, and the asymmetry is deliberate.** Reverts
    // are not gated: a revert hands back anything IMD already took, whatever the row says. So
    // every drawn row here can still run - and `effectiveRevertDefaults` would be the wrong
    // thing to count anyway, since it forces the overlay entry true while a debt is
    // outstanding, which is a debt rather than a configuration.
    val revertStates = userData.revertDefaults
        .withoutShizukuWhenNoIntents(userData.shizukuForkMode)"""

SCREEN_HIDE_CALL_OLD = """            accessibilityManageable = userData.accessibilityManageable,
            shizukuForkMode = userData.shizukuForkMode,
            hidingFramework = userData.hidingFramework,"""

SCREEN_HIDE_CALL_NEW = """            accessibilityManageable = userData.accessibilityManageable,
            manageShizukuEffective = userData.manageShizukuEffective,
            shizukuForkMode = userData.shizukuForkMode,
            hidingFramework = userData.hidingFramework,"""

SCREEN_REVERT_CALL_OLD = """            accessibilityManageable = userData.accessibilityManageable,
            shizukuForkMode = userData.shizukuForkMode,
            unhidingFramework = userData.unhidingFramework,"""

SCREEN_REVERT_CALL_NEW = """            accessibilityManageable = userData.accessibilityManageable,
            manageShizukuEffective = userData.manageShizukuEffective,
            shizukuForkMode = userData.shizukuForkMode,
            unhidingFramework = userData.unhidingFramework,"""

EDITS = [
    (HIDE, "the hide dialog's parameter", PARAM, PARAM_NEW),
    (HIDE, "the hide dialog's path", PATH_DECL, PATH_DECL_NEW),
    (HIDE, "the accessibility tick", HIDE_ACC_CHECKED_OLD, HIDE_ACC_CHECKED_NEW),
    (HIDE, "the Shizuku row", HIDE_SHIZUKU_OLD, HIDE_SHIZUKU_NEW),
    (REVERT, "the revert dialog's parameter", PARAM, PARAM_NEW),
    (REVERT, "the revert dialog's path", PATH_DECL, PATH_DECL_NEW),
    (REVERT, "the accessibility tick", REVERT_ACC_OLD, REVERT_ACC_NEW),
    (REVERT, "the Shizuku row", REVERT_SHIZUKU_OLD, REVERT_SHIZUKU_NEW),
    (SCREEN, "the two summaries", SCREEN_SUMMARY_OLD, SCREEN_SUMMARY_NEW),
    (SCREEN, "the hide dialog call", SCREEN_HIDE_CALL_OLD, SCREEN_HIDE_CALL_NEW),
    (SCREEN, "the revert dialog call", SCREEN_REVERT_CALL_OLD, SCREEN_REVERT_CALL_NEW),
]

DROP_IMPORTS = [
    (SCREEN, "import com.android.geto.domain.model.withoutOverlayWhenUnmanaged\n"),
    (SCREEN, "import com.android.geto.domain.model.overlayManageable\n"),
]

ADD_IMPORTS = [
    (SCREEN, "import com.android.geto.domain.model.effectiveSettingsToHide"),
]


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")

    if statement in lines:
        return text

    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    staged: dict[Path, str] = {}
    originals: dict[Path, str] = {}

    def read(rel: str) -> str:
        path = ROOT / rel

        if path not in staged:
            if not path.is_file():
                raise SystemExit(f"REFUSED: missing {rel}")

            originals[path] = path.read_text(encoding="utf-8")
            staged[path] = originals[path]

        return staged[path]

    for rel, name, old, new in EDITS:
        text = read(rel)

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries {name} — has this run before?")
            return 1

        staged[ROOT / rel] = text.replace(old, new, 1)

    for rel, statement in DROP_IMPORTS:
        text = read(rel)

        if text.count(statement) != 1:
            print(f"REFUSED: {rel} import {statement.strip()!r} matched "
                  f"{text.count(statement)} time(s)")
            return 1

        staged[ROOT / rel] = text.replace(statement, "", 1)

    for rel, statement in ADD_IMPORTS:
        staged[ROOT / rel] = insert_import(read(rel), statement)

    screen = staged[ROOT / SCREEN]

    # ⚠ The dropped imports must be genuinely unused. `overlayManageable` is still named in a
    # KDoc further down, which is not a use - so the test is for a code reference.
    # ⚠ Spelled the way each can only appear in a *statement*. The bare names occur in this
    # script's own new comments, which is the trap the table already records - fourth time.
    for gone in (".withoutOverlayWhenUnmanaged(", "(userData.overlayManageable)"):
        if gone in screen:
            print(f"REFUSED: {SCREEN} still references {gone} after dropping its import")
            return 1

    # Assert POSITION: both dialogs must receive the new argument, and each exactly once.
    for name in ("manageShizukuEffective = userData.manageShizukuEffective",):
        if screen.count(name) != 2:
            print(f"REFUSED: {name} passed {screen.count(name)} time(s), expected 2")
            return 1

    for rel in (HIDE, REVERT):
        text = staged[ROOT / rel]

        at_param = text.index("    manageShizukuEffective: Boolean,")
        at_path = text.index("    val manageShizukuPath = stringResource(")
        at_use = text.index("                enabled = manageShizukuEffective,")

        if not at_param < at_path < at_use:
            print(
                f"REFUSED: {rel} placement wrong — "
                f"param@{at_param} path@{at_path} use@{at_use}"
            )
            return 1

        # Every greyed control in these two files draws unticked. Three rows, three guards.
        for guarded in (
            "checked = accessibilityManageable &&",
            "checked = manageShizukuEffective &&",
        ):
            if text.count(guarded) != 1:
                print(f"REFUSED: {rel} has {text.count(guarded)} of {guarded!r}, expected 1")
                return 1

        # The overlay row already had its guard and must keep it.
        if "checked = overlayBlockedPaths == null &&" not in text:
            print(f"REFUSED: {rel} lost the overlay row's unticked guard")
            return 1

    for path, text in staged.items():
        was = {line for line in originals[path].split("\n") if len(line) > 120}

        gained = [
            (n, len(line))
            for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ") and line not in was
        ]

        if gained:
            print(f"REFUSED: {path.relative_to(ROOT)} would gain lines over 120: {gained}")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {HIDE}")
    print(f"  ok        {REVERT}")
    print(f"  ok        {SCREEN}  :: summaries + two call sites")
    print("  ~ Shizuku row greys with 'Manage Shizuku' off, in both dialogs")
    print("  ~ every greyed row draws unticked")
    print("  ~ x = what will run, y = what is drawn")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
