#!/usr/bin/env python3
"""
v3-r5 — the IMD icon in the settings manager: broken transition, and the app landing behind.

The author, on a razr fold:

  * *"there was absent animation in razr fold before, now a very broken animation appears. it was
    fine on s22 ultra before and now."*
  * *"in razr fold sometimes the imd app opens in back with the settings manager window on top
    of it."*

## One cause, two symptoms

The icon's press did this, in this order:

    onDismissRequest()     // ServicesActivity::finish
    context.openImdApp()   // startActivity, NEW_TASK | CLEAR_TOP | SINGLE_TOP

`ServicesActivity` is transparent, `excludeFromRecents`, and carries `taskAffinity=""` — so it is
a **translucent activity in a task of its own**, and IMD's own window lives in a different task.
Finishing first asks the window manager to tear that task down and, in the same breath, to bring
another one forward. Which of the two the transition settles on is then a race:

  * lose it and the app's task is raised while the translucent one is still on screen, which is
    the settings manager sitting on top of a freshly opened IMD — the second report exactly;
  * and the transition it has to draw is *out of a translucent window* and *into another task*,
    which has nothing solid to move — the first.

That it looks fine on the S22 Ultra and broken on the razr is what a race looks like: One UI and
Motorola's launcher animate cross-task starts differently, and only one of them is forgiving.

## The fix

Start the app **first**, while the window it is starting from is still alive and still on screen,
and finish afterwards. The window manager then has one ordinary open transition to draw and the
translucent window is removed from behind it, which is an order it cannot get wrong.

⚠ **Which means the press cannot stay inside the dialog**, because only the host knows what
dismissal means: for `ServicesActivity` it is `finish`, and for the in-app copy on the Favourites
tab it is nothing at all — IMD is already the thing behind the dialog, so closing the dialog *is*
opening the app, and it should not start an activity to say so. So `onOpenImdApp` is hoisted to
the caller like every other action on this dialog.

`onOpenRevertConfiguration` is the same two calls in the same wrong order, one screen along, and
gets the same swap. The author has not reported it — it is reachable only by long-pressing Revert
to default — but leaving the identical defect standing next to its fixed twin is not an option
worth having.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

ROUTE = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/SettingsManagerRoute.kt"
)

FAVOURITES = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/services/ServicesActivity.kt"

# --- the dialog: the press becomes one hoisted call ------------------------------------

DIALOG_CLICK_OLD = '''                        .clickable {
                            onDismissRequest()

                            // ⚠ Opens the app, not its settings - the author's
                            // instruction - and never relaunchToAdvancedSettings, which
                            // clears the task and so has nothing to animate from. See
                            // openImdApp's own KDoc for both halves.
                            context.openImdApp()
                        },
'''

DIALOG_CLICK_NEW = '''                        .clickable(onClick = onOpenImdApp),
'''

DIALOG_PARAM_OLD = '''    onDismissRequest: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
'''

DIALOG_PARAM_NEW = '''    onDismissRequest: () -> Unit,
    /**
     * The app icon on the title line.
     *
     * ⚠ **Hoisted in r5, and it had to be.** It used to call `onDismissRequest` and then start
     * IMD, from in here — and that order is what put the app behind the dialog on the author's
     * razr and broke the transition into it. Only the caller knows what dismissal means, and so
     * only the caller can put the two in the right order: see [SettingsManagerRoute]'s two
     * callers for the two answers.
     */
    onOpenImdApp: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
'''

# `LocalContext` was read for this press and for nothing else in that Row.
DIALOG_CONTEXT_OLD = '''            // The app's own icon, as the launcher draws it. This dialog is usually opened
            // from a tile or a shortcut, over somebody else's app, with nothing else on
            // screen to say which app just put a dialog in front of them.
            // Read here rather than inside the button: LocalContext is a composition local
            // and the lambda that uses it runs after the click, outside composition.
            val context = LocalContext.current

'''

DIALOG_CONTEXT_NEW = '''            // The app's own icon, as the launcher draws it. This dialog is usually opened
            // from a tile or a shortcut, over somebody else's app, with nothing else on
            // screen to say which app just put a dialog in front of them.

'''

DIALOG_IMPORT_OLD = "import com.android.geto.common.openImdApp\n"

DIALOG_IMPORT_NEW = ""

DIALOG_CONTEXT_IMPORT_OLD = "import androidx.compose.ui.platform.LocalContext\n"

# Still needed: managerMetrics reads the display metrics through it.
DIALOG_CONTEXT_IMPORT_NEW = "import androidx.compose.ui.platform.LocalContext\n"

# --- the route: forward it, and swap the revert-configuration pair ----------------------

ROUTE_SIG_OLD = '''fun SettingsManagerRoute(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
'''

ROUTE_SIG_NEW = '''fun SettingsManagerRoute(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
    /**
     * What the app icon on the dialog's title line does.
     *
     * ⚠ **The two callers answer it differently, and that is the point of it being here.** Over
     * somebody else's app it has to start IMD and then close this window, in that order; on the
     * Favourites tab IMD is already behind the dialog, so closing the dialog is the whole of it.
     */
    onOpenImdApp: () -> Unit,
'''

ROUTE_FORWARD_OLD = '''        onDismissRequest = onDismissRequest,
        // A plain forward now.'''

ROUTE_FORWARD_NEW = '''        onDismissRequest = onDismissRequest,
        onOpenImdApp = onOpenImdApp,
        // A plain forward now.'''

ROUTE_REVERT_OLD = '''        onOpenRevertConfiguration = {
            // Dismissed first. The dialog is the thing being navigated away from, and
            // leaving it standing over the settings screen it just opened would need
            // dismissing again before the configuration underneath could be used.
            onDismissRequest()

            context.openRevertConfiguration()
        },
'''

ROUTE_REVERT_NEW = '''        onOpenRevertConfiguration = {
            // ⚠ **Started first, dismissed second — r5, and the order is the whole of it.**
            // This used to dismiss first, on the reasoning that the dialog is the thing being
            // navigated away from. That reasoning holds; the ordering it produced does not.
            // Opened from the tile this dialog is a translucent activity in a task of its own,
            // and asking the window manager to tear that task down in the same breath as
            // raising another one is a race — which the author saw on the icon beside this one
            // as IMD arriving *behind* the manager. Starting while this window is still up
            // leaves one ordinary transition to draw and nothing to get wrong.
            context.openRevertConfiguration()

            onDismissRequest()
        },
'''

# --- the two callers --------------------------------------------------------------------

FAV_OLD = '''        SettingsManagerRoute(onDismissRequest = { showManagerDialog = false })
'''

FAV_NEW = '''        SettingsManagerRoute(
            onDismissRequest = { showManagerDialog = false },
            // ⚠ **Nothing is started here, and that is correct.** This copy of the manager is
            // open over IMD itself, so the app the icon offers to open is already the thing
            // behind the dialog: closing it *is* opening the app. Starting an activity to say
            // so would be a no-op with a transition attached.
            onOpenImdApp = { showManagerDialog = false },
        )
'''

ACTIVITY_OLD = '''                SettingsManagerRoute(onDismissRequest = ::finish)
'''

ACTIVITY_NEW = '''                SettingsManagerRoute(
                    onDismissRequest = ::finish,
                    onOpenImdApp = ::openImdAppAndFinish,
                )
'''

ACTIVITY_METHOD_OLD = '''    override fun onCreate(savedInstanceState: Bundle?) {
'''

ACTIVITY_METHOD_NEW = '''    /**
     * The app icon on the manager's title line: bring IMD up, then get out of the way.
     *
     * ⚠ **Started before finished, and the order is the fix — r5.** This activity is translucent,
     * `excludeFromRecents`, and carries an empty `taskAffinity`, so it is a window in a task of
     * its own and IMD's window is in another. Finishing first asks the window manager to remove
     * this task and raise that one at the same moment, and which of the two the transition
     * settles on is a race: the author saw IMD arrive *behind* the manager on his razr, and saw
     * the transition into it drawn out of a window with nothing solid in it. Starting while this
     * window is still up leaves one ordinary open transition, with this one removed from behind
     * it afterwards.
     */
    private fun openImdAppAndFinish() {
        openImdApp()

        finish()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
'''

ACTIVITY_IMPORT_OLD = "import com.android.geto.common.AppLocale\n"

ACTIVITY_IMPORT_NEW = (
    "import com.android.geto.common.AppLocale\n"
    "import com.android.geto.common.openImdApp\n"
)

# (path, old, new)
EDITS = [
    (DIALOG, DIALOG_CLICK_OLD, DIALOG_CLICK_NEW),
    (DIALOG, DIALOG_PARAM_OLD, DIALOG_PARAM_NEW),
    (DIALOG, DIALOG_CONTEXT_OLD, DIALOG_CONTEXT_NEW),
    (DIALOG, DIALOG_IMPORT_OLD, DIALOG_IMPORT_NEW),
    (ROUTE, ROUTE_SIG_OLD, ROUTE_SIG_NEW),
    (ROUTE, ROUTE_FORWARD_OLD, ROUTE_FORWARD_NEW),
    (ROUTE, ROUTE_REVERT_OLD, ROUTE_REVERT_NEW),
    (FAVOURITES, FAV_OLD, FAV_NEW),
    (ACTIVITY, ACTIVITY_IMPORT_OLD, ACTIVITY_IMPORT_NEW),
    (ACTIVITY, ACTIVITY_METHOD_OLD, ACTIVITY_METHOD_NEW),
    (ACTIVITY, ACTIVITY_OLD, ACTIVITY_NEW),
]

# (path, token, count, why)
CHECKS = [
    (DIALOG, "onOpenImdApp", 2, "the dialog declares it and calls it, and does nothing else"),
    # Passed as the handler rather than invoked, so there is no call with parentheses here at
    # all — which is also the check that the dialog no longer starts anything itself.
    (DIALOG, "onClick = onOpenImdApp", 1, "the icon hands the press straight out"),
    (DIALOG, "openImdApp()", 0, "and nothing in this file invokes a start"),
    (DIALOG, "context.openImdApp", 0, "the old in-dialog start is gone"),
    (DIALOG, "com.android.geto.common.openImdApp", 0, "and its import with it"),
    # managerMetrics still reads the display through LocalContext; openTarget-style presses do
    # not live in this file. One read, in the metrics function.
    (DIALOG, "LocalContext.current", 1, "one context read is left, and it is the metrics one"),
    (ROUTE, "onOpenImdApp", 3, "the route takes it, documents it and forwards it"),
    (ROUTE, "context.openRevertConfiguration()\n\n            onDismissRequest()", 1,
     "and the revert configuration now starts before it dismisses"),
    (FAVOURITES, "onOpenImdApp = { showManagerDialog = false }", 1, "in-app just closes"),
    (ACTIVITY, "private fun openImdAppAndFinish()", 1, "the activity starts then finishes"),
    (ACTIVITY, "openImdApp()\n\n        finish()", 1, "in that order"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    report: list[str] = []

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        if path not in originals:
            originals[path] = path.read_text(encoding="utf-8")

        text = planned.get(path, originals[path])

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {rel}\n  anchor {old.strip()[:70]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new and new in originals[path]:
            print(f"REFUSED: {rel} already carries the replacement — has this run before?")
            return 1

        planned[path] = text.replace(old, new, 1)

        report.append(f"  ok        {Path(rel).name:34s} {old.strip().splitlines()[0][:44]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(
                f"REFUSED: {Path(rel).name}: {why} — {token[:48]!r} appears {got} time(s), "
                f"expected {want}",
            )
            return 1

        report.append(f"  checked   {Path(rel).name:34s} x{got}  {token[:40]!r}")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, text in planned.items():
        added = over(text) - over(originals[path])

        if added:
            print(f"REFUSED: {path.name} would gain lines over 120 chars: {sorted(added)}")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print("\n".join(report))

    print(f"\nwrote {len(planned)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
