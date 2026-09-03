#!/usr/bin/env python3
"""
v3-r2b3c — a spinner while `'Restore settings first'` settles the debts.

**The author's request:** "when this new fail safe dialog runs pending reverts, it should show
spinners for use to know what is happening, for all IMD+, IMD, IMD shortcuts". He asked for the
same thing earlier in the round — "we can display revert spinners outside the all also just when
this restore is clicked".

**Why it is needed and the existing spinner is not enough.** `ShizukuStartingDialog` covers one
specific wait: a fork taking up to ten seconds to come up. A restore that needs no Shizuku start
still writes overlay AppOps, the accessibility list, four global settings and every per-app
snapshot — seconds of nothing, immediately after the user answered a dialog and it vanished. The
five surfaces already comment that the popup closes *before* the call so the Shizuku spinner shows
through; this is the rest of that thought.

**One flag, six writers, three readers.**

`PriorHideRestore` is an object in `:common`, beside `AutoUnhideWatch` and `SettingsChangeLog`,
holding a `StateFlow<Boolean>`. It is written by wrapping the six `flushPendingReverts` calls the
popup owns, and by nothing else — the Favourites Unhide button makes the same call and answers in
a toast of its own, and a spinner appearing over an unrelated screen would be worse than none.

⚠ **Three readers, not five.** The apps list, favourites and the per-app settings screen all live
in `MainActivity`'s nav host, so one dialog there covers all four in-app routes including the new
home-screen one. The shortcut and IMD+ windows are their own activities and each need their own.
Five would mean two spinners stacked on the same window.

⚠ **Behind the Shizuku spinner where both can be true.** In the shortcut and IMD+ windows the
Shizuku wait is the more specific answer — it names what is being waited for — so it wins, and
this one takes the remaining case.

⚠ **A `track` helper rather than two assignments.** The flag has to clear on every exit, and a
restore can throw: `finally` in one place beats six.

⚠ **Restore only.** `'Ignore all previous reverts'` is datastore writes and is over before a
spinner could be seen.

The sentence is **mine, not the author's** — flagged for him to overwrite. It is modelled on the
one string in the project that already describes this event, `auto_hide_revert_toast`:
"IMD+ is restoring your settings…".

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LICENCE = """/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
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
"""

FLAG_PATH = "common/src/main/kotlin/com/android/geto/common/PriorHideRestore.kt"

FLAG = LICENCE + '''package com.android.geto.common

import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Whether the force-close popup's `'Restore settings first'` is running right now.
 *
 * A restore started from that popup can spend seconds writing overlay AppOps, the accessibility
 * list, four global settings and every per-app snapshot — and it starts at the moment the dialog
 * the user just answered disappears. Without this the screen goes back to normal and stays there
 * while the device is being changed underneath it, which reads as the answer having done nothing.
 *
 * **An object with a flow, like [SettingsChangeLog] beside it**, and for the same reason: the six
 * writers are spread across `feature/apps`, `feature/app-settings` and `app`, and the readers are
 * three separate windows. An injected singleton would have to reach all nine.
 *
 * ⚠ **Only the popup's own restore.** `SettingsHiddenRunner.flushPendingReverts` is also what the
 * Favourites tab's Unhide button calls, and what a change of framework runs before it takes
 * effect. Neither should raise a modal spinner — the first answers in a toast on a screen the
 * user is already looking at, and the second is not a thing the user is waiting on. So this is
 * wrapped around the call at the six sites the popup owns rather than set inside the runner.
 *
 * ⚠ **In memory, and that is not a compromise here.** It describes a call that is in flight in
 * this process; a value that survived the process would be describing a call that cannot be.
 */
object PriorHideRestore {

    private val _running = MutableStateFlow(false)

    /** True from the moment the answer is given until the restore has finished, or failed. */
    val running: StateFlow<Boolean> = _running.asStateFlow()

    /**
     * Run [block] with the flag up, and put it down however [block] ends.
     *
     * The `finally` is the whole point of this existing rather than two assignments at each of
     * the six sites: a restore that throws must not leave a spinner on screen forever.
     */
    suspend fun <T> track(block: suspend () -> T): T {
        _running.value = true

        return try {
            block()
        } finally {
            _running.value = false
        }
    }
}
'''

DIALOG_PATH = "design-system/src/main/kotlin/com/android/geto/designsystem/component/WaitingDialog.kt"

DIALOG = LICENCE + '''package com.android.geto.designsystem.component

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * A spinner and a sentence, for a wait the user cannot otherwise see.
 *
 * The shape `ShizukuStartingDialog` has always had — a 24 dp indicator, 16 dp of space, one line
 * of text — with the sentence as a parameter instead of a `when` over one enum, so the force-close
 * popup's restore can use it from three separate windows.
 *
 * ⚠ **Here rather than beside `ShizukuStartingDialog` in `feature/apps`.** Same reason
 * [PriorHideDialog] is here: `feature/apps` depends on `feature/app-settings`, so anything both
 * of them need has to live below both. `:common` is not an option either — that module has no
 * Compose.
 *
 * ⚠ **`dismissible = false`, and no buttons.** There is nothing to decide, and dismissing it would
 * not stop the work — it would only hide it. `compact`, because this is a card with one line in
 * it and the platform's own width is exactly right for that.
 */
@Composable
fun WaitingDialog(
    text: String,
    modifier: Modifier = Modifier,
) {
    DialogContainer(
        modifier = modifier,
        compact = true,
        dismissible = false,
        onDismissRequest = {},
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(modifier = Modifier.size(24.dp))

            Spacer(modifier = Modifier.width(16.dp))

            Text(
                modifier = Modifier.weight(1f),
                text = text,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
'''

STRINGS = "common/src/main/res/values/strings.xml"

STRINGS_EDITS: list[tuple[str, str]] = [
    (
        """    <string name="prior_hide_ignore">Ignore all previous reverts</string>
</resources>""",
        """    <string name="prior_hide_ignore">Ignore all previous reverts</string>
    <!--
      Shown while 'Restore settings first' is working. Modelled on auto_hide_revert_toast,
      "IMD+ is restoring your settings…", which is the one string in the project that already
      describes this event.
    -->
    <string name="prior_hide_restoring">IMD is restoring your settings…</string>
</resources>""",
    ),
]

TRANSLATIONS = "tools/check_translations.py"

TRANSLATIONS_EDITS: list[tuple[str, str]] = [
    (
        """    "prior_hide_ignore",
}""",
        """    "prior_hide_ignore",
    "prior_hide_restoring",
}""",
    ),
]

# --- the six writers -------------------------------------------------------------------

APPS_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsViewModel.kt"

FAV_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsViewModel.kt"

SETTINGS_VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)

SHORTCUT_VM = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"

AUTO_HIDE_VM = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideViewModel.kt"

MAIN_VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

LAUNCH_EDITS: list[tuple[str, str]] = [
    (
        """            if (settingsHiddenRunner.flushPendingReverts()) launchApp(componentName = componentName)
""",
        """            // Wrapped so the screen can say what is happening: this call writes overlay
            // AppOps, the accessibility list, four settings and every per-app snapshot, and
            // the dialog that explained it has already gone.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) launchApp(componentName = componentName)
""",
    ),
]

APPS_IMPORT = [
    (
        """import com.android.geto.common.AutoUnhideWatch
""",
        """import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.PriorHideRestore
""",
    ),
]

SETTINGS_VM_EDITS: list[tuple[str, str]] = [
    (
        """            if (settingsHiddenRunner.flushPendingReverts()) applyAppSettings()
""",
        """            // See AppsViewModel.restoreThenLaunch: the flag is what puts a spinner on the
            // screen for the seconds this call can take.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) applyAppSettings()
""",
    ),
]

SHORTCUT_VM_EDITS: list[tuple[str, str]] = [
    (
        """            if (settingsHiddenRunner.flushPendingReverts()) {
                applyAppSettings(componentName = componentName)
            }
""",
        """            // The shortcut's window is transparent, so without this the user answers a
            // dialog, it disappears, and nothing at all is on screen while the device changes.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) {
                applyAppSettings(componentName = componentName)
            }
""",
    ),
]

AUTO_HIDE_VM_EDITS: list[tuple[str, str]] = [
    (
        """            if (settingsHiddenRunner.flushPendingReverts()) hide() else _finished.update { true }
""",
        """            // IMD+ draws over the app the user just opened, so this window is the only
            // surface the wait has.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) hide() else _finished.update { true }
""",
    ),
]

MAIN_VM_EDITS: list[tuple[str, str]] = [
    (
        """        appScope.launch {
            settingsHiddenRunner.flushPendingReverts()
        }
""",
        """        appScope.launch {
            PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }
        }
""",
    ),
    (
        """import com.android.geto.common.ApplicationScope
""",
        """import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
""",
    ),
]

# --- the three readers -----------------------------------------------------------------

MAIN_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"

MAIN_ACTIVITY_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.common.AutoRevertPending
""",
        """import com.android.geto.common.AutoRevertPending
import com.android.geto.common.PriorHideRestore
""",
    ),
    (
        """import com.android.geto.designsystem.component.PriorHideDialog
""",
        """import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.component.WaitingDialog
""",
    ),
    (
        """                val priorHide by viewModel.priorHide.collectAsStateWithLifecycle()
""",
        """                val priorHide by viewModel.priorHide.collectAsStateWithLifecycle()

                // One reader for all four in-app routes. The apps list, favourites and the
                // per-app settings screen are all inside the nav host below, so a spinner in
                // each of them would be three spinners on one window.
                val priorHideRestoring by PriorHideRestore.running
                    .collectAsStateWithLifecycle()
""",
    ),
    (
        """                                    } else if (uiState.userData.setupNoticeVersion != 0 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {
""",
        """                                    } else if (priorHideRestoring) {
                                        // Second in the chain, so a notice cannot appear over
                                        // the restore the user has just asked for.
                                        WaitingDialog(
                                            text = stringResource(
                                                commonR.string.prior_hide_restoring,
                                            ),
                                        )
                                    } else if (uiState.userData.setupNoticeVersion != 0 &&
                                        uiState.userData.settingsNoticeRevision <
                                        SETTINGS_NOTICE_REVISION
                                    ) {
""",
    ),
]

SHORTCUT_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt"

SHORTCUT_ACTIVITY_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.designsystem.component.PriorHideDialog
""",
        """import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.component.WaitingDialog
""",
    ),
    (
        """            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()
""",
        """            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()

            val priorHideRestoring by PriorHideRestore.running.collectAsStateWithLifecycle()
""",
    ),
    (
        """                    TerminalScreen.None ->
                        if (overlayStart == OverlayStart.Hide) {
                            ShizukuStartingDialog(reason = OverlayStart.Hide)
                        }
""",
        """                    TerminalScreen.None ->
                        if (overlayStart == OverlayStart.Hide) {
                            ShizukuStartingDialog(reason = OverlayStart.Hide)
                        } else if (priorHideRestoring) {
                            // After the Shizuku branch, because that one names what is being
                            // waited for and this one only says that something is.
                            WaitingDialog(
                                text = stringResource(commonR.string.prior_hide_restoring),
                            )
                        }
""",
    ),
]

AUTO_HIDE_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt"

AUTO_HIDE_ACTIVITY_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.designsystem.component.PriorHideDialog
""",
        """import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.component.WaitingDialog
""",
    ),
    (
        """            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()
""",
        """            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()

            val priorHideRestoring by PriorHideRestore.running.collectAsStateWithLifecycle()
""",
    ),
    (
        """                } else if (overlayStart != null) {
""",
        """                } else if (priorHideRestoring && overlayStart == null) {
                    // The restore the popup's first answer started. Behind the Shizuku spinner
                    // where both are true, since that one names the wait.
                    WaitingDialog(
                        text = stringResource(commonR.string.prior_hide_restoring),
                    )
                } else if (overlayStart != null) {
""",
    ),
]

# The five files the first run of this script forgot. `check_new_types` reported every one of
# them, which is exactly the round-level question it was built to ask.
APP_SCOPE_IMPORT = [
    (
        """import com.android.geto.common.ApplicationScope
""",
        """import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
""",
    ),
]

APP_LOCALE_IMPORT = [
    (
        """import com.android.geto.common.AppLocale
""",
        """import com.android.geto.common.AppLocale
import com.android.geto.common.PriorHideRestore
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    targets: list[tuple[str, list[tuple[str, str]]]] = [
        (STRINGS, STRINGS_EDITS),
        (TRANSLATIONS, TRANSLATIONS_EDITS),
        (APPS_VM, LAUNCH_EDITS + APPS_IMPORT),
        (FAV_VM, LAUNCH_EDITS + APPS_IMPORT),
        (SETTINGS_VM, SETTINGS_VM_EDITS + APP_SCOPE_IMPORT),
        (SHORTCUT_VM, SHORTCUT_VM_EDITS + APP_SCOPE_IMPORT),
        (AUTO_HIDE_VM, AUTO_HIDE_VM_EDITS + APP_SCOPE_IMPORT),
        (MAIN_VM, MAIN_VM_EDITS),
        (MAIN_ACTIVITY, MAIN_ACTIVITY_EDITS),
        (SHORTCUT_ACTIVITY, SHORTCUT_ACTIVITY_EDITS + APP_LOCALE_IMPORT),
        (AUTO_HIDE_ACTIVITY, AUTO_HIDE_ACTIVITY_EDITS + APP_LOCALE_IMPORT),
    ]

    written: list[tuple[Path, str]] = []

    for relative, edits in targets:
        path = ROOT / relative

        text = apply(path, edits, problems)

        if text is not None:
            written.append((path, text))

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in written:
        path.write_text(text, encoding="utf-8")

    (ROOT / FLAG_PATH).write_text(FLAG, encoding="utf-8")

    (ROOT / DIALOG_PATH).write_text(DIALOG, encoding="utf-8")

    print("ok — the restore says it is running, on all three windows")

    return 0


if __name__ == "__main__":
    sys.exit(main())
