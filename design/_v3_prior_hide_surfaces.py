#!/usr/bin/env python3
"""
v3-r2b3 part 2 — the force-close popup on every surface that can launch.

Part 1 built the mechanism; this puts it on screen. Five surfaces, and one that deliberately
does not get a dialog.

| surface | Restore | Ignore |
| --- | --- | --- |
| Apps, Favourites | settle, then launch if clear | discard, then launch |
| pinned shortcut | settle, then apply-and-launch if clear | discard, then apply-and-launch |
| per-app settings screen | settle, then apply-and-launch if clear | discard, then apply-and-launch |
| IMD+ | settle, then run if clear | discard, then run |
| Tasker | — | suppresses and proceeds; no window to ask in |

⚠ **IMD+ is gated before it does anything**, at the author's instruction, which is what makes
both buttons mean the same there as everywhere else. Earlier drafts had the popup arrive after
IMD+ had already decided not to hide, so Ignore had nothing to carry on with. Now
`AutoHideViewModel.run` asks first and only calls the runner once the answer is in.

⚠ **A failed Restore stops the hide and says nothing new.** The failure notifications that
`RevertToDefaultRunner` already raises are the report — no second one. On IMD+ the app is left
open and IMD+ does not run, which is the author's rule.

⚠ **The spinner comes free.** `overlayStart` already drives `ShizukuStartingDialog` on all four
launch surfaces, and a restore that waits on Shizuku reports through the same tracker — so the
wait shows itself as soon as the dialog is dismissed. That was the author's "display revert
spinners when restore is clicked", with no new state.

### Suppression, in one place

The **use case** sets `PriorHide.suppress()` when it returns the value, rather than each surface
doing it. IMD+ draws over the app the user just opened, which is itself a window change its
detector sees; without suppression a dialog nobody has answered yet would put another one up
behind it. Both buttons clear it — Restore through `PriorHide.settled()` on success,
Ignore through `discardPendingReverts`.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps"

EFFECT = f"{APPS}/AppLaunchEffect.kt"
APPS_SCREEN = f"{APPS}/AppsScreen.kt"
FAV_SCREEN = f"{APPS}/FavouriteAppsScreen.kt"
APPS_VM = f"{APPS}/AppsViewModel.kt"
FAV_VM = f"{APPS}/FavouriteAppsViewModel.kt"

SHORTCUT = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt"
SHORTCUT_VM = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"

AUTO_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt"
AUTO_VM = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideViewModel.kt"

RUNNER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt"
TASKER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "TaskerIntegrationBroadcastReceiver.kt"
)

APP_SETTINGS = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsScreen.kt"
)
APP_SETTINGS_VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsViewModel.kt"
)

APPLY_APP = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/ApplyAppSettingsUseCase.kt"
)
APPLY_HIDE = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
    "ApplySettingsToHideUseCase.kt"
)

TRANSLATIONS = "tools/check_translations.py"

# The gate, written identically into both hide use cases. Placed after the IMD+ conflict check
# and before the permission check: it is a question about the *previous* run, so it belongs
# ahead of everything about this one.
GATE = """
        // ⚠ **The force-close gate.** Settings are down and no hide in this process put them
        // there, so the process that did is gone and its revert notification went with it.
        // Nothing is written and nothing is launched — the caller shows the popup, and the
        // user chooses between putting the old state back and letting go of it.
        //
        // Suppressed here rather than by each caller: IMD+ draws its dialog over the app the
        // user just opened, which is itself a window change its detector sees, so a dialog
        // nobody has answered yet would put another one up behind it.
        if (PriorHide.shouldWarn(settingsHidden = userData.settingsHidden)) {
            PriorHide.suppress()

            return@withContext AppSettingsResult.HiddenFromPreviousUse
        }
"""

EDITS: dict[str, list[tuple[str, str]]] = {}

EDITS[APPLY_APP] = [
    (
        """import com.android.geto.domain.model.hideOwnsRevert
""",
        """import com.android.geto.domain.model.hideOwnsRevert
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (
        """        if (!secureSettingsWrapper.hasWriteSecureSettingsPermission()) {""",
        GATE + """
        if (!secureSettingsWrapper.hasWriteSecureSettingsPermission()) {""",
    ),
]

EDITS[EFFECT] = [
    (
        """    onPermissionsLost: () -> Unit,
    onConsumed: () -> Unit,
""",
        """    onPermissionsLost: () -> Unit,
    onPriorHide: (componentName: String) -> Unit,
    onConsumed: () -> Unit,
""",
    ),
    (
        """                AppSettingsResult.NoPermission -> onPermissionsLost()
            }
""",
        """                AppSettingsResult.NoPermission -> onPermissionsLost()

                // Nothing was written and the app is not opening: the settings that are down
                // belong to a run of IMD that is no longer alive, and the user has not been
                // told. The component name rides along because both answers end in launching
                // this same app.
                AppSettingsResult.HiddenFromPreviousUse -> onPriorHide(launch.componentName)
            }
""",
    ),
    (
        """/**
 * Shown when a favourite is tapped that has no settings configured.
""",
        """/**
 * Settings are still down from a run of IMD that is no longer alive.
 *
 * Two answers, and both of them end in the app opening — which is why neither button dismisses
 * without doing something and there is no third way out.
 *
 * ⚠ **`'Ignore all previous reverts'` is permanent**, and the label is written to say so. An
 * earlier draft read just `'Ignore'`, which sounds like "carry on" rather than "throw the record
 * away". Afterwards nothing in IMD knows those settings were ever on, and `Revert to default` is
 * the only way to a known state.
 *
 * Public, like the two dialogs above it, because the pinned shortcut and IMD+ live in the `app`
 * module and have to say exactly the same thing.
 */
@Composable
fun PriorHideDialog(
    modifier: Modifier = Modifier,
    onRestore: () -> Unit,
    onIgnore: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onIgnore) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(
                text = stringResource(commonR.string.prior_hide_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onIgnore) {
                    Text(text = stringResource(commonR.string.prior_hide_ignore))
                }

                TextButton(onClick = onRestore) {
                    Text(text = stringResource(commonR.string.prior_hide_restore))
                }
            }
        }
    }
}

/**
 * Shown when a favourite is tapped that has no settings configured.
""",
    ),
]

SCREEN_STATE = (
    """    var autoHideConflict by rememberSaveable { mutableStateOf(false) }
""",
    """    var autoHideConflict by rememberSaveable { mutableStateOf(false) }

    // Which app was being launched when IMD noticed that the settings already down belong to a
    // run of itself that is no longer alive. The component name rather than a flag, because
    // both answers end in launching that same app. Saved for the same reason as the rest.
    var priorHide by rememberSaveable { mutableStateOf<String?>(null) }
""",
)

SCREEN_WIRING = (
    """        onPermissionsLost = { permissionsLost = true },
        onConsumed = viewModel::consumeAppLaunch,
    )
""",
    """        onPermissionsLost = { permissionsLost = true },
        onPriorHide = { priorHide = it },
        onConsumed = viewModel::consumeAppLaunch,
    )
""",
)

SCREEN_DIALOG = (
    """    if (permissionsLost) {
        PermissionsLostDialog(onDismissRequest = { permissionsLost = false })
    }
""",
    """    if (permissionsLost) {
        PermissionsLostDialog(onDismissRequest = { permissionsLost = false })
    }

    // Cleared before either call, so the Shizuku spinner underneath is visible for the wait
    // rather than hidden behind a dialog nobody can answer any more.
    priorHide?.let { componentName ->
        PriorHideDialog(
            onRestore = {
                priorHide = null

                viewModel.restoreThenLaunch(componentName = componentName)
            },
            onIgnore = {
                priorHide = null

                viewModel.discardThenLaunch(componentName = componentName)
            },
        )
    }
""",
)

EDITS[APPS_SCREEN] = [SCREEN_STATE, SCREEN_WIRING, SCREEN_DIALOG]
EDITS[FAV_SCREEN] = [SCREEN_STATE, SCREEN_WIRING, SCREEN_DIALOG]

VM_METHODS = """
    /**
     * The popup's two answers, both of which end in launching the app that raised it.
     *
     * ⚠ **Restore only goes on if the device is actually clear.** `flushPendingReverts` reports
     * that by looking at what the revert said *and* at what the records say afterwards. A revert
     * that could not put Shizuku or overlay access back has already raised its own notification
     * from `RevertToDefaultRunner`, so the launch is abandoned in silence rather than adding a
     * second one saying the same thing.
     *
     * ⚠ **Ignore is permanent.** It throws the old record away and takes the device as it
     * stands; nothing afterwards knows those settings were ever on. The button says so.
     *
     * On the application scope, not [viewModelScope]: a restore can wait on Shizuku for seconds
     * and the user may well leave the tab while it does.
     */
    fun restoreThenLaunch(componentName: String) {
        appScope.launch {
            if (settingsHiddenRunner.flushPendingReverts()) launchApp(componentName = componentName)
        }
    }

    fun discardThenLaunch(componentName: String) {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            launchApp(componentName = componentName)
        }
    }
"""

EDITS[APPS_VM] = [
    (
        """import com.android.geto.domain.model.revertNamesApp
""",
        """import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.model.revertNamesApp
""",
    ),
    # ⚠ Caught by tools/check_new_types.py, which is exactly what it is for: `appScope` is
    # typed CoroutineScope and this file had never named that type.
    (
        """import kotlinx.coroutines.flow.MutableStateFlow
""",
        """import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
""",
    ),
    (
        """    private val userDataRepository: UserDataRepository,
) : ViewModel() {""",
        """    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {""",
    ),
    (
        """    fun consumeAppLaunch() {
""",
        VM_METHODS + """
    fun consumeAppLaunch() {
""",
    ),
]

EDITS[FAV_VM] = [
    (
        """    /** Cleared once handled, so tapping the same app twice emits twice. */
""",
        VM_METHODS + """
    /** Cleared once handled, so tapping the same app twice emits twice. */
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {}

    for name, edits in EDITS.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(staged)} files: the dialog, the gate and the two in-app launch surfaces")

    return 0


if __name__ == "__main__":
    sys.exit(main())
