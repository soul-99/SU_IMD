#!/usr/bin/env python3
"""v3-r4q — the settings manager's logo opens IMD, not IMD's settings.

    "update the settings manager app logo button to open imd app instead of imd app settings page"
    "my request to add animation if possible still stands"

This replaces the `openAdvancedSettings` added earlier in this same round, which navigated to the
Settings tab. Nothing else ever called it, so it goes with the change rather than being left as a
function with no callers.

## ⚠ The animation was never missing; the activity was being destroyed

`relaunchToAdvancedSettings` uses `FLAG_ACTIVITY_CLEAR_TASK`. Its KDoc says why, and the reason is
a real one - it exists for the re-launch that follows a **change of hiding-unhiding mechanism**,
where every screen has to re-read its preferences. But a task that is cleared has nothing left to
animate *from*: the activity is torn down and built again, which is the *"no animation so it
looks wierd"*.

`openImdApp` is the plain launch intent with `CLEAR_TOP` and `SINGLE_TOP` - the same pair
`openRevertConfiguration` already uses - so:

* **raised from inside the app** (the Favourites tab's manager dialog), the running activity is
  handed the intent and stays exactly as it was. The dialog's own dismissal is the whole
  transition, which is what it should be: the app is already there.
* **raised from the tile or the pinned shortcut**, with only `ServicesActivity` running, this is
  an ordinary activity start and gets the system's ordinary activity transition.

⚠ **No extra on the intent, and that is the change he asked for.** `EXTRA_OPEN_ADVANCED_SETTINGS`
is what made `HomeScreen` navigate to Settings; without it the app comes back on whatever tab it
was left on, which is *"open imd app instead of imd app settings page"*.

⚠ **`relaunchToAdvancedSettings` is untouched.** The mechanism-change caller still needs a
rebuilt activity, and a second function beside it - rather than a flag on it - is what stops
either caller from quietly acquiring the other's behaviour.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ADVANCED = "common/src/main/kotlin/com/android/geto/common/AdvancedSettings.kt"

MANAGER = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

OLD_FUNCTION = '''/**
 * Opens the app on Settings with Advanced expanded, **without** restarting it.
 *
 * ⚠ **The difference from [relaunchToAdvancedSettings] is the whole point, and it is visible.**
 * That one clears the task, so the activity is destroyed and rebuilt and there is no transition
 * to watch - the author's *"it opens imd app settings tab but there is no animation so it looks
 * wierd"*. This hands the intent to the running activity instead, exactly as
 * `openRevertConfiguration` does, so `MainActivity.onNewIntent` raises the request and the tab
 * change animates like any other.
 *
 * A second function rather than a flag on the first, so the caller that genuinely needs a
 * rebuilt activity - a change of hiding-unhiding mechanism - cannot lose it by accident.
 */
fun Context.openAdvancedSettings() {
    val intent = packageManager.getLaunchIntentForPackage(packageName) ?: return

    intent.addFlags(
        Intent.FLAG_ACTIVITY_NEW_TASK or
            Intent.FLAG_ACTIVITY_CLEAR_TOP or
            Intent.FLAG_ACTIVITY_SINGLE_TOP,
    )

    intent.putExtra(EXTRA_OPEN_ADVANCED_SETTINGS, true)

    startActivity(intent)
}

'''

NEW_FUNCTION = '''/**
 * Brings IMD to the front, on whatever it was last showing.
 *
 * ⚠ **No extra, and that is the whole of it.** [EXTRA_OPEN_ADVANCED_SETTINGS] is what makes
 * `HomeScreen` navigate to the Settings tab; without it the app simply comes back - the author's
 * *"open imd app instead of imd app settings page"*.
 *
 * ⚠ **`CLEAR_TOP` with `SINGLE_TOP`, never `CLEAR_TASK`.** A cleared task means the activity is
 * destroyed and rebuilt, which has nothing to animate *from* and is exactly the *"no animation so
 * it looks wierd"* this replaces. Raised from inside the app the running activity is handed the
 * intent and stays as it was, so the manager dialog's own dismissal is the transition; raised
 * from the tile or the pinned shortcut it is an ordinary activity start with the system's
 * ordinary transition.
 *
 * A second function rather than a flag on [relaunchToAdvancedSettings], so the caller that
 * genuinely needs a rebuilt activity - a change of hiding-unhiding mechanism - cannot lose it by
 * accident.
 */
fun Context.openImdApp() {
    val intent = packageManager.getLaunchIntentForPackage(packageName) ?: return

    intent.addFlags(
        Intent.FLAG_ACTIVITY_NEW_TASK or
            Intent.FLAG_ACTIVITY_CLEAR_TOP or
            Intent.FLAG_ACTIVITY_SINGLE_TOP,
    )

    startActivity(intent)
}

'''

EDITS: list[tuple[str, str, str]] = [
    (ADVANCED, OLD_FUNCTION, NEW_FUNCTION),
    (
        MANAGER,
        """                            // ⚠ Not relaunchToAdvancedSettings: that clears the task,
                            // so there is no tab transition left to animate. See the two
                            // functions' own KDoc.
                            context.openAdvancedSettings()""",
        """                            // ⚠ Opens the app, not its settings - the author's
                            // instruction - and never relaunchToAdvancedSettings, which
                            // clears the task and so has nothing to animate from. See
                            // openImdApp's own KDoc for both halves.
                            context.openImdApp()""",
    ),
    (
        MANAGER,
        """import com.android.geto.common.openAdvancedSettings""",
        """import com.android.geto.common.openImdApp""",
    ),
]

AFTER = [
    (ADVANCED, "fun Context.openImdApp()", 1),
    (ADVANCED, "openAdvancedSettings", 0),
    (ADVANCED, "fun Context.relaunchToAdvancedSettings()", 1),
    # The extra still exists and is still used by the relaunch below it.
    (ADVANCED, "EXTRA_OPEN_ADVANCED_SETTINGS", 3),
    # Three: the import, the call, and the comment above it that names the function it is
    # deliberately not calling. The comment trap, inflating again.
    (MANAGER, "openImdApp", 3),
    (MANAGER, "openAdvancedSettings", 0),
    (MANAGER, "relaunchToAdvancedSettings", 1),
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

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {ADVANCED}  :: openImdApp replaces openAdvancedSettings")
    print(f"  ok        {MANAGER}  :: the logo opens the app, on whatever tab it was on")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
