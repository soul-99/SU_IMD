#!/usr/bin/env python3
"""v3-r4t — the auto unhide page leaves the initialisation flow.

    "remove auto unhide page setup from initialisation screen"

The flow becomes six pages: Permissions, Shizuku, Accessibility, Display over other apps, Settings
to hide, Reminders.

## ⚠ The page constants renumber, and that is not cosmetic

`nextAfter` walks *forward by one* until it reaches `REMINDERS`, so the constants are a contiguous
sequence and a gap in it is a page the walk stops on and cannot draw. `REMINDERS` therefore moves
from 6 to 5 rather than the removed 5 being left as a hole. The script asserts the whole sequence
is declared once each and in order, which is the check that catches exactly this.

## ⚠ `AutoUnhideStep` goes with it, and `AutoUnhidePage` does not

The step wrapper had one caller and is removed. The **dialog** it wrapped is untouched, including
the `onSkip`/`flat` support r4r gave it: that is what Settings still opens, and stripping a
parameter because its only setup caller left would be undoing a working thing for tidiness.

⚠ **The `setup_step_auto_unhide` string stays too.** It is still listed in the translation
checker's deferred set and costs nothing; deleting a string is how a later "put that page back"
turns into a missing resource.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

STEPS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

EDITS: list[tuple[str, str, str]] = [
    (
        SCREEN,
        """/** Auto unhide, whole — r4r. */
private const val AUTO_UNHIDE = 5

/** The reminders, which is where `remindersOnly` opens. */
private const val REMINDERS = 6""",
        """/**
 * The reminders, which is where `remindersOnly` opens.
 *
 * ⚠ **5, not 6.** Auto unhide was page 5 until r4t, when the author took it out of the flow.
 * `nextAfter` walks forward one page at a time until it reaches this, so the constants have to
 * be contiguous — a gap left where the removed page was is a number the walk stops on with
 * nothing to draw.
 */
private const val REMINDERS = 5""",
    ),
    (
        SCREEN,
        """
                AUTO_UNHIDE -> AutoUnhideStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_auto_unhide),
                    onSkip = { advance(AUTO_UNHIDE) },
                    onNext = { advance(AUTO_UNHIDE) },
                )
""",
        "",
    ),
    (
        SCREEN,
        "import com.android.geto.feature.settings.AutoUnhideStep\n",
        "",
    ),
    (
        STEPS,
        """/**
 * Auto unhide, whole.
 *
 * ⚠ **With all five of its satellites.** The minutes pickers, the ADB command, the how-it-works
 * dialog and the used-for refusal belong to this page rather than to the settings screen that
 * hosts it today, and a step without them is a page whose rows open nothing.
 */
@Composable
fun AutoUnhideStep(""",
        """/**
 * Auto unhide, whole.
 *
 * ⚠ **No longer part of the setup flow** — the author took it out in r4t. Kept rather than
 * deleted: it is the one place the whole page and all five of its satellites are wired together
 * for a flat step, and rebuilding that from scratch is the cost of removing it. `AutoUnhidePage`
 * itself is untouched and is what Settings opens.
 *
 * ⚠ **With all five of its satellites.** The minutes pickers, the ADB command, the how-it-works
 * dialog and the used-for refusal belong to this page rather than to the settings screen that
 * hosts it today, and a step without them is a page whose rows open nothing.
 */
@Suppress("unused")
@Composable
fun AutoUnhideStep(""",
    ),
]

AFTER = [
    (SCREEN, "AUTO_UNHIDE", 0),
    (SCREEN, "AutoUnhideStep", 0),
    (SCREEN, "setup_step_auto_unhide", 0),
    (SCREEN, "private const val REMINDERS = 5", 1),
    (STEPS, "fun AutoUnhideStep(", 1),
    (STEPS, '@Suppress("unused")', 1),
]

ORDER = [
    "PERMISSIONS = 0",
    "SHIZUKU = 1",
    "ACCESSIBILITY = 2",
    "OVERLAY = 3",
    "SETTINGS_TO_HIDE = 4",
    "REMINDERS = 5",
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
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ Contiguous, distinct and in order, or nextAfter stops on a page it cannot draw.
    positions = []

    for name in ORDER:
        if staged[SCREEN].count(name) != 1:
            print(f"REFUSED: {SCREEN}\n  {name!r} is not declared exactly once")
            return 1

        positions.append(staged[SCREEN].index(name))

    if positions != sorted(positions):
        print(f"REFUSED: {SCREEN}\n  the page constants are not declared in flow order")
        return 1

    # Every remaining page constant is still reached by a branch of the `when`.
    for name in ("SHIZUKU", "ACCESSIBILITY", "OVERLAY", "SETTINGS_TO_HIDE"):
        if f"                {name} -> " not in staged[SCREEN]:
            print(f"REFUSED: {SCREEN}\n  {name} has no branch")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: six pages, auto unhide gone, constants contiguous")
    print(f"  ok        {STEPS}  :: AutoUnhideStep kept but no longer routed to")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
