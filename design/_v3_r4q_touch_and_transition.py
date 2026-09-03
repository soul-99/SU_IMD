#!/usr/bin/env python3
"""v3-r4q — three reports about touches and transitions.

    "when app page changes and animation stop just before if i click somewhere previous page's
     buttons were they got pressed even though they are not visible on the screen leading to
     wrong touches"
    "when i long press app icons in IMD first time create shortcut does not open but it does on
     second time, this bug does not occur every time"
    "when i click on the imd app logo icon in the settings manager it opens imd app settings tab
     but there is no animation so it looks wierd"

---

## 1. Touches landing on the tab that is leaving

⚠ **Both destinations are composed for the length of a tab transition.** The one sliding out is
still laid out, still hit-testable, and still holding the position its buttons had - so a tap
that lands while the animation is finishing goes to a control the user can barely see. That is
exactly the report, and it is not a race in this app's code: it is what an animated `NavHost`
does unless something stops it.

`Modifier.blockTouchesWhileAnimating` consumes every pointer change on the **initial** pass while
its destination's own enter/exit transition is running. Initial rather than main, because a
consumer on the main pass runs *after* the children have already had their chance.

⚠ **It is applied to the arriving destination as well as the leaving one**, which is deliberate:
a press that lands on a control still sliding into place is aimed at where it *was*, not where it
is, and is as likely to be wrong. Nothing is dropped that a user meant - the animation is
150-300ms.

⚠ **The flag is read inside the pointer loop, not in the modifier chain.** Building the chain
conditionally would tear down and rebuild the pointer input every time a transition started or
stopped, and a pointer input rebuilt mid-gesture loses the gesture.

## 2. "Create shortcut" not opening on the first long press

Not intermittent, and not a lost press: `ShortcutRoute` draws **nothing at all** until its lookup
lands -

    val loaded = target?.takeIf { it.componentName == componentName } ?: return

- and that lookup is `getActivityIcon` plus a `ShortcutManager` query, both cold on the first
press of a session and both warm afterwards. So the first long press looks like it did nothing,
the user presses again, and the second one is instant. *"this bug does not occur every time"* is
the tell: it happens exactly when the lookup is slow.

⚠ **The `return` itself is right and is kept.** Its own comment records the bug it fixed: this
ViewModel outlives the dialog, so drawing early showed the *previous* app's icon and seeded the
label fields with the previous app's name. What is added is a loading dialog in front of that
return, so the press has an answer immediately without any of the previous app's data being
drawn.

## 3. No animation opening Settings from the manager's IMD logo

⚠ **There is nothing to animate: the activity is being destroyed and rebuilt.**
`relaunchToAdvancedSettings` uses `FLAG_ACTIVITY_CLEAR_TASK`, and its KDoc says why - it is
written for the re-launch that follows a **change of hiding-unhiding mechanism**, where every
screen must re-read its preferences.

The logo is not that. It opens a tab. So it now goes through the same route
`openRevertConfiguration` already uses - `CLEAR_TOP` with `SINGLE_TOP` - which hands the intent
to the running activity, raises `advancedSettingsRequest`, and lets `HomeScreen`'s existing
effect navigate. That navigation is an ordinary tab change and animates like one.

⚠ **`relaunchToAdvancedSettings` is left exactly as it is**, because the mechanism-change caller
still needs a torn-down activity. A second function beside it, rather than a flag on the first,
so neither caller can quietly acquire the other's behaviour.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLOCKER = "design-system/src/main/kotlin/com/android/geto/designsystem/component/TransitionTouchBlocker.kt"

SETTINGS_NAV = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/navigation/SettingsNavigation.kt"

APPS_NAV = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/navigation/AppsNavigation.kt"

FAVOURITES_NAV = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/navigation/FavouriteAppsNavigation.kt"

SHORTCUT = "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/shortcut/ShortcutRoute.kt"

ADVANCED = "common/src/main/kotlin/com/android/geto/common/AdvancedSettings.kt"

MANAGER = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

LICENCE = '''/*
 *
 *   Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
'''

BLOCKER_TEXT = LICENCE + '''package com.android.geto.designsystem.component

import androidx.compose.animation.AnimatedVisibilityScope
import androidx.compose.animation.ExperimentalAnimationApi
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.rememberUpdatedState
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.pointer.PointerEventPass
import androidx.compose.ui.input.pointer.pointerInput

/**
 * Swallows touches while this destination's own transition is running.
 *
 * ⚠ **Both destinations are on screen for the length of a tab change**, and the one leaving is
 * still laid out and still hit-testable where its buttons used to be - so a tap landing as the
 * animation finishes reaches a control the user can barely see. The author's report:
 * *"previous page's buttons were they got pressed even though they are not visible on the
 * screen leading to wrong touches"*.
 *
 * ⚠ **The arriving destination is blocked too, on purpose.** A press aimed at a control that is
 * still sliding into place is aimed at where it *was*. Over a transition of a few hundred
 * milliseconds, refusing both is the only answer that cannot act on a stale position.
 *
 * ⚠ **[PointerEventPass.Initial], not the default.** The main pass runs after the children have
 * already been offered the event, which is too late to stop a button from taking it.
 *
 * ⚠ **The flag is read inside the loop rather than around the modifier.** Adding and removing
 * `pointerInput` as transitions start and stop would rebuild the pointer handler mid-gesture,
 * and a rebuilt handler loses whatever gesture was in progress.
 */
@OptIn(ExperimentalAnimationApi::class)
@Composable
fun Modifier.blockTouchesWhileAnimating(scope: AnimatedVisibilityScope): Modifier {
    val animating by rememberUpdatedState(scope.transition.isRunning)

    return pointerInput(Unit) {
        awaitPointerEventScope {
            while (true) {
                val event = awaitPointerEvent(PointerEventPass.Initial)

                if (animating) {
                    event.changes.forEach { it.consume() }
                }
            }
        }
    }
}
'''

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. the three tabs ----------------
    (
        SETTINGS_NAV,
        """    composable<SettingsRouteData> {
        SettingsRoute()
    }""",
        """    composable<SettingsRouteData> {
        // Full size around a full-size destination, so this changes no layout - it only gives
        // the transition somewhere to hang its touch blocker. See blockTouchesWhileAnimating.
        Box(modifier = Modifier.fillMaxSize().blockTouchesWhileAnimating(this)) {
            SettingsRoute()
        }
    }""",
    ),
    (
        SETTINGS_NAV,
        """import androidx.navigation.NavController""",
        """import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.navigation.NavController""",
    ),
    (
        SETTINGS_NAV,
        """import com.android.geto.feature.settings.SettingsRoute""",
        """import com.android.geto.designsystem.component.blockTouchesWhileAnimating
import com.android.geto.feature.settings.SettingsRoute""",
    ),
    (
        APPS_NAV,
        """    composable<AppsRouteData> {
        AppsRoute(snackbarHostState = snackbarHostState, onClickApp = onClickApp)
    }""",
        """    composable<AppsRouteData> {
        // See settingsScreen - a full-size wrapper for the touch blocker, no layout change.
        Box(modifier = Modifier.fillMaxSize().blockTouchesWhileAnimating(this)) {
            AppsRoute(snackbarHostState = snackbarHostState, onClickApp = onClickApp)
        }
    }""",
    ),
    (
        APPS_NAV,
        """import androidx.compose.material3.SnackbarHostState""",
        """import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.SnackbarHostState
import androidx.compose.ui.Modifier""",
    ),
    (
        APPS_NAV,
        """import com.android.geto.feature.apps.AppsRoute""",
        """import com.android.geto.designsystem.component.blockTouchesWhileAnimating
import com.android.geto.feature.apps.AppsRoute""",
    ),
    (
        FAVOURITES_NAV,
        """    composable<FavouriteAppsRouteData> {
        FavouriteAppsRoute(
            snackbarHostState = snackbarHostState,
            onClickApp = onClickApp,
        )""",
        """    composable<FavouriteAppsRouteData> {
        // See settingsScreen - a full-size wrapper for the touch blocker, no layout change.
        Box(modifier = Modifier.fillMaxSize().blockTouchesWhileAnimating(this)) {
            FavouriteAppsRoute(
                snackbarHostState = snackbarHostState,
                onClickApp = onClickApp,
            )
        }""",
    ),
    (
        FAVOURITES_NAV,
        """import androidx.compose.material3.SnackbarHostState""",
        """import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.SnackbarHostState
import androidx.compose.ui.Modifier""",
    ),
    (
        FAVOURITES_NAV,
        """import com.android.geto.feature.apps.FavouriteAppsRoute""",
        """import com.android.geto.designsystem.component.blockTouchesWhileAnimating
import com.android.geto.feature.apps.FavouriteAppsRoute""",
    ),
    # ---------------- 2. the shortcut dialog answers immediately ----------------
    (
        SHORTCUT,
        """    // Nothing is drawn until the lookup for *this* app has landed. The ViewModel belongs
    // to the tab and outlives the dialog, so without this check the previous app's result
    // is what the first composition sees -- and the label fields, seeded once, keep it.
    val loaded = target?.takeIf { it.componentName == componentName } ?: return""",
        """    // Nothing is drawn until the lookup for *this* app has landed. The ViewModel belongs
    // to the tab and outlives the dialog, so without this check the previous app's result
    // is what the first composition sees -- and the label fields, seeded once, keep it.
    //
    // ⚠ **A spinner in front of it, since r4q.** The check is right and stays; what was wrong
    // was drawing *nothing*, because the lookup is an icon read plus a ShortcutManager query
    // and both are cold on the first press of a session. The author's report - "first time
    // create shortcut does not open but it does on second time, this bug does not occur every
    // time" - is that dead interval, and the second press feeling instant is the same lookup
    // being warm. Nothing of the previous app is drawn here, so the bug the return exists for
    // cannot come back through it.
    val loaded = target?.takeIf { it.componentName == componentName } ?: run {
        ShortcutLoadingDialog(modifier = modifier, onDismissRequest = onDismissRequest)

        return
    }""",
    ),
    # ---------------- 3. the manager's logo navigates instead of relaunching ----------
    (
        ADVANCED,
        """fun Context.relaunchToAdvancedSettings() {""",
        """/**
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

fun Context.relaunchToAdvancedSettings() {""",
    ),
    (
        MANAGER,
        """                            context.relaunchToAdvancedSettings()""",
        """                            // ⚠ Not relaunchToAdvancedSettings: that clears the task,
                            // so there is no tab transition left to animate. See the two
                            // functions' own KDoc.
                            context.openAdvancedSettings()""",
    ),
    (
        MANAGER,
        """import com.android.geto.common.relaunchToAdvancedSettings""",
        """import com.android.geto.common.openAdvancedSettings""",
    ),
]

SHORTCUT_DIALOG = '''
/**
 * What a long press shows while the icon and the existing-shortcut lookup are still running.
 *
 * ⚠ **A dialog rather than nothing.** The lookup is fast once warm and slow exactly once per
 * session, and drawing nothing for that interval is indistinguishable from the press having been
 * missed - which is what the author reported and what made him press again.
 *
 * Dismissible, so a press that turns out to have been a mistake is not a wait.
 */
@Composable
private fun ShortcutLoadingDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(32.dp),
            contentAlignment = Alignment.Center,
        ) {
            CircularProgressIndicator()
        }
    }
}
'''

SHORTCUT_IMPORTS = [
    "import androidx.compose.foundation.layout.Box",
    "import androidx.compose.foundation.layout.fillMaxWidth",
    "import androidx.compose.foundation.layout.padding",
    "import androidx.compose.material3.CircularProgressIndicator",
    "import androidx.compose.ui.Alignment",
    "import androidx.compose.ui.unit.dp",
    "import com.android.geto.designsystem.component.DialogContainer",
]

AFTER = [
    (SETTINGS_NAV, "blockTouchesWhileAnimating(this)", 1),
    (APPS_NAV, "blockTouchesWhileAnimating(this)", 1),
    (FAVOURITES_NAV, "blockTouchesWhileAnimating(this)", 1),
    (SHORTCUT, "ShortcutLoadingDialog", 2),
    (ADVANCED, "fun Context.openAdvancedSettings()", 1),
    (ADVANCED, "fun Context.relaunchToAdvancedSettings()", 1),
    (MANAGER, "openAdvancedSettings", 2),
    (MANAGER, "relaunchToAdvancedSettings", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    blocker = ROOT / BLOCKER

    if blocker.exists():
        print(f"REFUSED: {BLOCKER}\n  already exists; this script creates it")
        return 1

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

    # The loading dialog goes at the end of the shortcut route's file, with its imports.
    staged[SHORTCUT] = staged[SHORTCUT].rstrip("\n") + "\n" + SHORTCUT_DIALOG

    for statement in SHORTCUT_IMPORTS:
        staged[SHORTCUT] = add_import(staged[SHORTCUT], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # ⚠ The manager reaches into :common for the new function; both modules must already see
    # each other or this is an unresolved reference in a module the sandbox cannot build.
    manager_gradle = (ROOT / "feature/apps/build.gradle.kts").read_text(encoding="utf-8")

    if "projects.common" not in manager_gradle:
        print("REFUSED: feature/apps does not depend on :common")
        return 1

    blocker.write_text(BLOCKER_TEXT, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {BLOCKER}  :: new")
    print("  ok        all three tabs refuse touches while transitioning")
    print(f"  ok        {SHORTCUT}  :: a spinner instead of nothing")
    print(f"  ok        {ADVANCED}  :: openAdvancedSettings beside the relaunch")
    print(f"  ok        {MANAGER}  :: the logo navigates rather than restarting the app")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
