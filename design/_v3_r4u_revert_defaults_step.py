#!/usr/bin/env python3
"""v3-r4u — Revert to default joins the initialisation flow.

    "also you removed the rev to def config screen from initialisation??why"

## ⚠ It was never there, and I should have said so at the time

The four steps r4r built are the four the author listed: *"1. Select accessibility services to
hide / manage 2. Select Display over other apps ... 3. Select settings to hide / unhide 4. Auto
unhide settings"*. Revert to default was not among them and has never been a page of setup — this
is checked against the r4q and r4r1 source zips, not remembered.

What did happen is that in r4q he asked for a paragraph *"in bold to rev to def config dialog and
initialisation page"*, and only the dialog had one to add. That sentence was the ask for this
page, and it went by as a slip of wording rather than being raised with him. That was the mistake,
and it is what this fixes.

## The step is the dialog, as all the others are

`RevertDefaultsDialog` is already built on `SettingsPage`, so it gains the same two parameters
`SettingsToHideDialog` got in r4r — `onSkip` non-null means "draw flat, put Skip at the left" —
and `SettingsPage` does the rest.

⚠ **No new heading string, and that is deliberate.** Every other step was given a `setup_step_*`
title the author wrote and confirmed. This page already computes its own title from his labels,
and it computes it **differently under the memory function** — *Revert to default* against the
two-line entry label. A fixed heading here would be one of those two, wrong half the time; the
step passes no `stepTitle` and lets the page keep the title it already gets right.

⚠ **Placed after Settings to hide.** That page says what a launch takes away; this one says what
comes back. Reading them the other way round asks the user to configure a recovery from a state
they have not chosen yet.

## ⚠ The page constants renumber again

`nextAfter` walks forward one page at a time to `REMINDERS`, so the sequence has to stay
contiguous: inserting at 5 moves `REMINDERS` to 6. The script asserts the whole sequence is
declared once each, in order, and that every constant has a branch.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"

STEPS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. The dialog can be a step ----------------
    (
        DIALOG,
        """    shizukuForkMode: ShizukuForkMode,
    onDismissRequest: () -> Unit,""",
        """    shizukuForkMode: ShizukuForkMode,
    /**
     * Non-null turns this into a step of the setup flow.
     *
     * The page is drawn flat rather than as a dialog, and its footer carries Skip at the left
     * beside Next at the right — see `SettingsPage`, which does both.
     */
    onSkip: (() -> Unit)? = null,
    onDismissRequest: () -> Unit,""",
    ),
    (
        DIALOG,
        """        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                onClick = {
                    onUpdateRevertDefaults(draft)

                    onDismissRequest()
                },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },""",
        """        // ⚠ **No stepTitle parameter, unlike the other three steps.** This page already
        // computes its own title from the author's labels, and computes it *differently* under
        // the memory function — see above. A fixed heading passed in from the flow would be one
        // of those two and wrong half the time.
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // One lambda, two labels: Save and Next do the same two things in the same order,
            // and writing them once is what stops them drifting apart.
            val commit = {
                onUpdateRevertDefaults(draft)

                onDismissRequest()
            }

            if (onSkip != null) {
                TextButton(onClick = onSkip) {
                    Text(text = stringResource(commonR.string.skip))
                }
            }

            TextButton(onClick = commit) {
                Text(
                    text = stringResource(
                        if (onSkip != null) commonR.string.next else R.string.save,
                    ),
                )
            }
        },""",
    ),
    # ---------------- 2. The step wrapper ----------------
    (
        STEPS,
        """/**
 * Auto unhide, whole.""",
        """/**
 * What a revert puts back.
 *
 * ⚠ **Placed after [SettingsToHideStep] in the flow**: that page says what a launch takes away,
 * this one says what comes back, and the other order asks the user to configure a recovery from
 * a state they have not chosen yet.
 *
 * ⚠ **No `stepTitle`**, unlike the three steps above. The page's own title changes with the
 * unhiding framework — see `RevertDefaultsDialog` — so a heading handed in from the flow would be
 * wrong under one of the two.
 */
@Composable
fun RevertDefaultsStep(
    modifier: Modifier = Modifier,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    RevertDefaultsDialog(
        modifier = modifier,
        states = userData.revertDefaults,
        overlayBlockedPaths = overlayBlockedPaths(userData = userData),
        accessibilityManageable = userData.accessibilityManageable,
        manageShizukuEffective = userData.manageShizukuEffective,
        shizukuForkMode = userData.shizukuForkMode,
        unhidingFramework = userData.unhidingFramework,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onUpdateRevertDefaults = viewModel::updateRevertDefaults,
    )
}

/**
 * Auto unhide, whole.""",
    ),
    (
        STEPS,
        "import com.android.geto.feature.settings.dialog.OverlayStepWaiting\n",
        "import com.android.geto.feature.settings.dialog.OverlayStepWaiting\n"
        "import com.android.geto.feature.settings.dialog.RevertDefaultsDialog\n",
    ),
    # ---------------- 3. The flow ----------------
    (
        SCREEN,
        """/**
 * The reminders, which is where `remindersOnly` opens.
 *
 * ⚠ **5, not 6.** Auto unhide was page 5 until r4t, when the author took it out of the flow.
 * `nextAfter` walks forward one page at a time until it reaches this, so the constants have to
 * be contiguous — a gap left where the removed page was is a number the walk stops on with
 * nothing to draw.
 */
private const val REMINDERS = 5""",
        """/** What a revert puts back — r4u. */
private const val REVERT_DEFAULTS = 5

/**
 * The reminders, which is where `remindersOnly` opens.
 *
 * ⚠ **The number moves whenever a page is added or removed**, and it has to. `nextAfter` walks
 * forward one page at a time until it reaches this, so the constants have to stay contiguous — a
 * gap is a number the walk stops on with nothing to draw. It was 6, then 5 when r4t took auto
 * unhide out, and is 6 again now that r4u has put Revert to default in.
 */
private const val REMINDERS = 6""",
    ),
    (
        SCREEN,
        """                SETTINGS_TO_HIDE -> SettingsToHideStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_settings_to_hide),
                    onSkip = { advance(SETTINGS_TO_HIDE) },
                    onNext = { advance(SETTINGS_TO_HIDE) },
                )""",
        """                SETTINGS_TO_HIDE -> SettingsToHideStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_settings_to_hide),
                    onSkip = { advance(SETTINGS_TO_HIDE) },
                    onNext = { advance(SETTINGS_TO_HIDE) },
                )

                // No stepTitle: this page's own heading changes with the unhiding framework.
                REVERT_DEFAULTS -> RevertDefaultsStep(
                    modifier = modifier,
                    onSkip = { advance(REVERT_DEFAULTS) },
                    onNext = { advance(REVERT_DEFAULTS) },
                )""",
    ),
    (
        SCREEN,
        "import com.android.geto.feature.settings.OverlayStep\n",
        "import com.android.geto.feature.settings.OverlayStep\n"
        "import com.android.geto.feature.settings.RevertDefaultsStep\n",
    ),
]

IMPORTS = [
    (DIALOG, "import com.android.geto.common.R as commonR"),
]

AFTER = [
    (DIALOG, "flat = onSkip != null,", 1),
    (DIALOG, "commonR.string.skip", 1),
    (DIALOG, "commonR.string.next", 1),
    (DIALOG, "R.string.save", 1),
    (STEPS, "fun RevertDefaultsStep(", 1),
    (STEPS, "RevertDefaultsDialog(", 1),
    (SCREEN, "REVERT_DEFAULTS", 4),
    (SCREEN, "private const val REMINDERS = 6", 1),
]

ORDER = [
    "PERMISSIONS = 0",
    "SHIZUKU = 1",
    "ACCESSIBILITY = 2",
    "OVERLAY = 3",
    "SETTINGS_TO_HIDE = 4",
    "REVERT_DEFAULTS = 5",
    "REMINDERS = 6",
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    lines.insert(indices[-1] + 1, statement + "\n")

    return "".join(lines)


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
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    positions = []

    for name in ORDER:
        if staged[SCREEN].count(name) != 1:
            print(f"REFUSED: {SCREEN}\n  {name!r} is not declared exactly once")
            return 1

        positions.append(staged[SCREEN].index(name))

    if positions != sorted(positions):
        print(f"REFUSED: {SCREEN}\n  the page constants are not declared in flow order")
        return 1

    for name in ("SHIZUKU", "ACCESSIBILITY", "OVERLAY", "SETTINGS_TO_HIDE", "REVERT_DEFAULTS"):
        if f"                {name} -> " not in staged[SCREEN]:
            print(f"REFUSED: {SCREEN}\n  {name} has no branch")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {DIALOG}  :: can be drawn flat with Skip and Next")
    print(f"  ok        {STEPS}  :: RevertDefaultsStep")
    print(f"  ok        {SCREEN}  :: seven pages, Revert to default after Settings to hide")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
