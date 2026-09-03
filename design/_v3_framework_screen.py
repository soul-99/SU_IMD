#!/usr/bin/env python3
"""
v3-r2 — the settings screen: two framework rows at the top of Advanced, the dialogs behind
them, and the Save flow that replaces the re-launch.

Four edits, and the third is the one to read twice:

1. The route wires `frameworkSave` instead of `mechanismSwitch`. The spinner stays; the
   re-launch goes, replaced by the failure dialog.
2. The old "Hiding-unhiding mechanism" row is removed from the middle of Advanced and the two
   framework rows go in at the **top** of it, which the author asked for twice.
3. The two rows in Default IMD settings take dynamic labels. Both are driven by the
   **unhiding** framework, and the red ⓘ by the **hiding** one — that asymmetry is deliberate
   and the author confirmed it: under the memory function the hide list *is* the unhide list,
   because memory restores exactly what was hidden.
4. `NotificationFunction.getTitle()` becomes a pair of framework titles, used for the "using
   X" subtitle on each row.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str, int]] = [
    # ---- 1. the route --------------------------------------------------------------------
    (
        "    val mechanismSwitch by viewModel.mechanismSwitch.collectAsStateWithLifecycle()\n",
        "    val frameworkSave by viewModel.frameworkSave.collectAsStateWithLifecycle()\n",
        1,
    ),
    (
        "        onSwitchMechanism = viewModel::switchMechanism,\n",
        "        onSaveHidingFramework = viewModel::saveHidingFramework,\n"
        "        onSaveUnhidingFramework = viewModel::saveUnhidingFramework,\n",
        1,
    ),
    (
        """    // Kept here rather than passed down with everything else. A change of mechanism ends by
    // starting the app over, which needs a Context and a modal that covers whatever the
    // settings list is showing - neither of which belongs in the stateless screen below.
    if (mechanismSwitch == MechanismSwitch.Running) PendingRevertsDialog()

    LaunchedEffect(mechanismSwitch) {
        if (mechanismSwitch == MechanismSwitch.Relaunch) context.relaunchToAdvancedSettings()
    }
""",
        """    // Kept here rather than passed down with everything else: a modal that covers whatever
    // the settings list is showing does not belong in the stateless screen below.
    if (frameworkSave == FrameworkSave.Running) PendingRevertsDialog()

    // ⚠ **No re-launch, unlike the mechanism switch this replaces.** That existed because
    // several screens read the mechanism as they composed and a change underneath a running
    // one left parts of it describing the old mechanism. Every one of them now collects a
    // Flow off the same repository and recomposes on its own — the two launch view models,
    // the per-app screen, the apps and favourites lists, and this screen — so the restart
    // bought a blink and nothing else. Verified by reading each reader, not assumed.
    if (frameworkSave == FrameworkSave.Failed) {
        FrameworkRevertsFailedDialog(onDismissRequest = viewModel::clearFrameworkSave)
    }
""",
        1,
    ),
    # ---- 2. Advanced ---------------------------------------------------------------------
    (
        """            // First in Advanced, because it is the one switch here that adds and removes
            // settings elsewhere in this screen: three overlay rows under Default IMD
            // settings appear and disappear with it. Off by default, since overlay access
            // is the only thing IMD touches that cannot be written at all without a working
            // Shizuku service - on a device without one those three rows can only fail.
            SwitchSetting(
                title = stringResource(R.string.manage_overlay),
""",
        """            // ⚠ **The two frameworks come first, at the author's instruction, stated
            // twice in the v3 spec.** They outrank the overlay switch below not because they
            // add rows to this screen but because they decide what every other row on it
            // means: which list a launch reads, and which revert puts it back.
            SettingsColumn(
                title = stringResource(R.string.hiding_framework),
                subtitle = stringResource(
                    R.string.framework_using,
                    userData.hidingFramework.getTitle(),
                ),
                onClick = { showHidingFrameworkDialog = true },
            )

            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.unhiding_framework),
                subtitle = stringResource(
                    R.string.framework_using,
                    userData.unhidingFramework.getShortTitle(),
                ),
                onClick = { showUnhidingFrameworkDialog = true },
            )

            SettingsRowDivider()

            // Was first in Advanced, and is now third: it is the one switch here that adds
            // and removes settings elsewhere in this screen - three overlay rows under
            // Default IMD settings appear and disappear with it. Off by default, since
            // overlay access is the only thing IMD touches that cannot be written at all
            // without a working Shizuku service.
            SwitchSetting(
                title = stringResource(R.string.manage_overlay),
""",
        1,
    ),
    (
        """            // Advanced because the recommended answer is the default and nobody has to
            // come here: choosing the memory function means taking on a profile per app,
            // which is the opposite of what Default IMD settings above is for.
            SettingsColumn(
                title = stringResource(R.string.notification_function),
                subtitle = userData.notificationFunction.getTitle(),
                onClick = { showNotificationFunctionDialog = true },
            )

            SettingsRowDivider()

""",
        "",
        1,
    ),
    # ---- 3. the two rows in Default IMD settings -----------------------------------------
    (
        """            SettingsColumn(
                title = stringResource(R.string.settings_to_hide),
                subtitle = stringResource(
                    R.string.settings_to_hide_summary,
                    hideStates.count { it.value },
                    hideStates.size,
                ),
                onClick = { showSettingsToHideDialog = true },
                // Only while the memory function is chosen, because only then is this row
                // mostly not what a launch reads: the per-app profile is. The mark says so
                // rather than the row being hidden, since the two things it still drives -
                // the tile and the intents - are real and configured here.
                trailing = if (userData.notificationFunction == NotificationFunction.Memory) {
                    { MemoryHideNoticeButton(onClick = { showMemoryHideNotice = true }) }
                } else {
                    null
                },
            )
""",
        """            SettingsColumn(
                // ⚠ **Driven by the *unhiding* framework, which is not the obvious half.**
                // Under the memory function this list is also the unhide list, because
                // memory restores exactly what was hidden from it; under Revert to default a
                // separate list drives the unhide and this one is hide-only. The author's
                // rule, and it holds up.
                title = if (userData.unhidingFramework == UnhidingFramework.Memory) {
                    stringResource(R.string.settings_to_hide_both_label)
                } else {
                    stringResource(R.string.settings_to_hide_defaults_label)
                },
                subtitle = stringResource(
                    R.string.settings_to_hide_summary,
                    hideStates.count { it.value },
                    hideStates.size,
                ),
                onClick = { showSettingsToHideDialog = true },
                // The mark is the *hiding* half, and independent of the label above: under
                // Per app configuration this row is mostly not what a launch reads, because
                // the per-app profile is. It says so rather than the row being hidden, since
                // the two things it still drives - the tile and the intents - are real and
                // are configured here.
                trailing = if (userData.hidingFramework == HidingFramework.PerApp) {
                    { MemoryHideNoticeButton(onClick = { showMemoryHideNotice = true }) }
                } else {
                    null
                },
            )
""",
        1,
    ),
    (
        """            SettingsColumn(
                // Named for what it does here rather than for the dialog it opens: in a
                // list beside "Settings to hide", "Revert to default configuration" says
                // nothing about the relationship between the two.
                title = stringResource(R.string.revert_defaults_entry),
""",
        """            SettingsColumn(
                // Two lines under Revert to default, one under the memory function. Named
                // for what it does here as well as for the dialog it opens: in a list beside
                // the hide row, "Revert to default configuration" alone says nothing about
                // the relationship between the two, and under the memory function there is
                // no relationship left to describe.
                title = if (userData.unhidingFramework == UnhidingFramework.Memory) {
                    stringResource(R.string.revert_defaults)
                } else {
                    stringResource(R.string.revert_defaults_entry_both)
                },
""",
        1,
    ),
    # ---- 4. the dialogs ------------------------------------------------------------------
    (
        "    var showNotificationFunctionDialog by rememberSaveable { mutableStateOf(false) }\n",
        "    var showHidingFrameworkDialog by rememberSaveable { mutableStateOf(false) }\n"
        "\n"
        "    var showUnhidingFrameworkDialog by rememberSaveable { mutableStateOf(false) }\n",
        1,
    ),
    (
        "    onSwitchMechanism: (NotificationFunction) -> Unit,\n",
        "    onSaveHidingFramework: (HidingFramework) -> Unit,\n"
        "    onSaveUnhidingFramework: (UnhidingFramework) -> Unit,\n",
        2,
    ),
    (
        "                    onSwitchMechanism = onSwitchMechanism,\n",
        "                    onSaveHidingFramework = onSaveHidingFramework,\n"
        "                    onSaveUnhidingFramework = onSaveUnhidingFramework,\n",
        1,
    ),
    (
        "            onSwitchMechanism = onSwitchMechanism,\n",
        "            onSaveHidingFramework = onSaveHidingFramework,\n"
        "            onSaveUnhidingFramework = onSaveUnhidingFramework,\n",
        1,
    ),
    # ---- 5. the title extensions ---------------------------------------------------------
    (
        """internal fun NotificationFunction.getTitle() = when (this) {
    NotificationFunction.Memory -> stringResource(R.string.notification_function_memory)
    NotificationFunction.RevertToDefault -> stringResource(R.string.notification_function_revert)
}""",
        """internal fun HidingFramework.getTitle() = when (this) {
    HidingFramework.ImdDefaults -> stringResource(R.string.hiding_framework_defaults)
    HidingFramework.PerApp -> stringResource(R.string.hiding_framework_per_app)
}

/**
 * The short form, for the "using X" subtitle.
 *
 * Trimmed of the bracketed half the picker carries — "Memory function", not "Memory function
 * (Revert to what was actually hidden)" — at the author's instruction, and confirmed
 * deliberate. A settings row's second line is one line; the parenthesis is for the dialog,
 * where there is room to explain.
 */
@Composable
internal fun UnhidingFramework.getShortTitle() = when (this) {
    UnhidingFramework.Memory -> stringResource(R.string.notification_function_memory)
    UnhidingFramework.RevertToDefault -> stringResource(R.string.unhiding_framework_revert)
}""",
        1,
    ),
]


def main() -> int:
    path = ROOT / SCREEN
    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in EDITS:
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:64]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Only lines this edit *adds*. SettingsScreen already carries one long line — the
    # labelOf signature — and refusing over somebody else's is how a guard gets switched off.
    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if len(line) > 120 and line not in before:
            problems.append(f"added line over 120 chars: {line.strip()[:70]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print("ok — settings screen re-pointed at the two frameworks")

    return 0


if __name__ == "__main__":
    sys.exit(main())
