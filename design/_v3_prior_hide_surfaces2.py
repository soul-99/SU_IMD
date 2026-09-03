#!/usr/bin/env python3
"""
v3-r2b3 part 3 — the device-wide gate, the shortcut, the per-app screen, IMD+ and Tasker.

Finishes what part 2 started. Every route that can hide now either asks the question or has a
stated reason not to.

⚠ **IMD+ asks before it does anything**, which is the author's instruction and the thing that
makes both buttons mean the same on every surface. `AutoHideViewModel.run` reads the debt first
and only hands over to `AutoHideRunner` once the answer is in — so Ignore has a run to carry on
with, where an earlier draft had the popup arriving after IMD+ had already given up.

⚠ **A failed Restore on IMD+ closes the window and leaves the app alone**: the notification
`RevertToDefaultRunner` raised is the report, IMD+ does not run, and `PriorHide` stays suppressed
so the next detection of the same app does not prompt again. Tapping *Try again* on that
notification restores from the debt, which clears it, which clears the suppression — the author's
rule, arrived at through the condition that actually matters rather than by watching
notifications.

⚠ **Tasker gets no dialog and that is deliberate.** It is the one route with no window, and an
automation that stopped to ask a question would simply never run. It suppresses and proceeds;
the first-owner rule, shipped in r2b, is what makes proceeding safe.

⚠ **English only.** From this round on the author translates in one pass at the end, so the three
new keys go into `check_translations.py`'s DEFERRED set instead of being written into eleven
locales twice. The set is the list that pass will work from.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPLY_HIDE = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
    "ApplySettingsToHideUseCase.kt"
)
SHORTCUT = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt"
SHORTCUT_VM = (
    "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"
)
AUTO_ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt"
AUTO_VM = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideViewModel.kt"
RUNNER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt"
TASKER = (
    "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
    "TaskerIntegrationBroadcastReceiver.kt"
)
APP_SETTINGS = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsScreen.kt"
)
APP_SETTINGS_VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)
TRANSLATIONS = "tools/check_translations.py"

EDITS: dict[str, list[tuple[str, str]]] = {}

# --- the device-wide hide -------------------------------------------------------------------
EDITS[APPLY_HIDE] = [
    (
        """import com.android.geto.domain.model.effectiveSettingsToHide
""",
        """import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (
        """        // ⚠ **The grant is checked before anything is touched, and that ordering is the whole
""",
        """        // ⚠ **The force-close gate.** Settings are down and no hide in this process put them
        // there, so the process that did is gone and its revert notification went with it.
        // Nothing is written and nothing is launched — the caller shows the popup, and the user
        // chooses between putting the old state back and letting go of it.
        //
        // Suppressed here rather than by each caller: IMD+ draws its dialog over the app the
        // user just opened, which is itself a window change its detector sees, so a dialog
        // nobody has answered yet would put another one up behind it.
        if (PriorHide.shouldWarn(settingsHidden = userData.settingsHidden)) {
            PriorHide.suppress()

            return AppSettingsResult.HiddenFromPreviousUse
        }

        // ⚠ **The grant is checked before anything is touched, and that ordering is the whole
""",
    ),
]

# --- the pinned shortcut --------------------------------------------------------------------
EDITS[SHORTCUT] = [
    (
        """import com.android.geto.feature.apps.PermissionsLostDialog
""",
        """import com.android.geto.feature.apps.PermissionsLostDialog
import com.android.geto.feature.apps.PriorHideDialog
""",
    ),
    (
        """    AutoHideConflict,
    PermissionsLost,
}
""",
        """    AutoHideConflict,
    PermissionsLost,

    /** Settings are down from a run of IMD that is no longer alive. */
    PriorHide,
}
""",
    ),
    (
        """                    TerminalScreen.PermissionsLost -> PermissionsLostDialog(onDismissRequest = ::finish)
""",
        """                    TerminalScreen.PermissionsLost -> PermissionsLostDialog(onDismissRequest = ::finish)

                    // Both answers end in this shortcut doing what it was tapped to do, so
                    // neither closes the window: the apply runs again and the collector below
                    // picks up where it left off. The transparent window stays, which is what
                    // lets the Shizuku spinner show through for a restore that has to wait.
                    TerminalScreen.PriorHide -> PriorHideDialog(
                        onRestore = {
                            terminalScreen = TerminalScreen.None

                            viewModel.restoreThenApply(componentName = componentName)
                        },
                        onIgnore = {
                            terminalScreen = TerminalScreen.None

                            viewModel.discardThenApply(componentName = componentName)
                        },
                    )
""",
    ),
    (
        """                    if (result == AppSettingsResult.NoPermission) {
                        terminalScreen = TerminalScreen.PermissionsLost

                        return@collect
                    }
""",
        """                    if (result == AppSettingsResult.NoPermission) {
                        terminalScreen = TerminalScreen.PermissionsLost

                        return@collect
                    }

                    // Nothing was written and the app is not opening. A shortcut has no other
                    // surface to say this on, and saying nothing is how the home-screen icon
                    // becomes a tap that silently hides over somebody else's hide.
                    if (result == AppSettingsResult.HiddenFromPreviousUse) {
                        terminalScreen = TerminalScreen.PriorHide

                        return@collect
                    }
""",
    ),
]

RESOLVE_METHODS = """
    /**
     * The popup's two answers, both of which end in this launch running again.
     *
     * ⚠ **Restore only goes on if the device is actually clear.** `flushPendingReverts` reports
     * that from what the revert said *and* what the records say afterwards. A revert that could
     * not put Shizuku or overlay access back has already raised its own notification, so the
     * launch is abandoned rather than adding a second one saying the same thing.
     *
     * ⚠ **Ignore is permanent**: the old record is thrown away and the device is taken as it
     * stands. The button says so.
     */
    fun restoreThenApply(componentName: String) {
        appScope.launch {
            if (settingsHiddenRunner.flushPendingReverts()) {
                applyAppSettings(componentName = componentName)
            }
        }
    }

    fun discardThenApply(componentName: String) {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            applyAppSettings(componentName = componentName)
        }
    }
"""

EDITS[SHORTCUT_VM] = [
    (
        """import com.android.geto.domain.model.revertNamesApp
""",
        """import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.model.revertNamesApp
""",
    ),
    # ⚠ check_new_types again: appScope's type was never named in this file either.
    (
        """import kotlinx.coroutines.flow.SharingStarted
""",
        """import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.SharingStarted
""",
    ),
    (
        """    private val userDataRepository: UserDataRepository,
    shizukuStartTracker: ShizukuStartTracker,
) : ViewModel() {""",
        """    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
    shizukuStartTracker: ShizukuStartTracker,
) : ViewModel() {""",
    ),
    (
        """    fun applyAppSettings(componentName: String) {
""",
        RESOLVE_METHODS + """
    fun applyAppSettings(componentName: String) {
""",
    ),
]

# --- IMD+ ------------------------------------------------------------------------------------
EDITS[RUNNER] = [
    (
        """    PermissionsLost,
}
""",
        """    PermissionsLost,

    /**
     * Settings are down from a run of IMD that is no longer alive.
     *
     * Raised by [com.android.geto.activity.autohide.AutoHideViewModel] **before** the runner is
     * asked to do anything, at the author's instruction — so that both of the popup's answers
     * have a run left to carry on with. A value here rather than a flag on the activity because
     * `AutoHideActivity` already draws every one of these and knows nothing else about them.
     */
    HiddenFromPreviousUse,
}
""",
    ),
]

EDITS[AUTO_VM] = [
    (
        """    userDataRepository: UserDataRepository,
    private val autoHideRunner: AutoHideRunner,
""",
        """    private val userDataRepository: UserDataRepository,
    private val autoHideRunner: AutoHideRunner,
    private val settingsHiddenRunner: SettingsHiddenRunner,
""",
    ),
    (
        """    fun run(packageName: String) {
        if (started) return

        started = true

        appScope.launch {
            // Declared outside the try so a run that throws still closes the window rather than
            // leaving it standing over the app, transparent and eating every touch.
            var result = AutoHideOutcome.Done

            try {
                result = autoHideRunner.run(packageName = packageName)
            } finally {
                if (result == AutoHideOutcome.Done) {
                    _finished.update { true }
                } else {
                    _outcome.update { result }
                }
            }
        }
    }
""",
        """    fun run(packageName: String) {
        if (started) return

        started = true

        watched = packageName

        appScope.launch {
            // ⚠ **Asked before IMD+ does anything at all**, which is the author's instruction
            // and what makes both of the popup's answers mean the same here as on every other
            // surface: the app has not been force-stopped yet, so there is still a run to carry
            // on with. An earlier draft asked after the hide had already been refused.
            if (PriorHide.shouldWarn(userDataRepository.userData.first().settingsHidden)) {
                PriorHide.suppress()

                _outcome.update { AutoHideOutcome.HiddenFromPreviousUse }

                return@launch
            }

            hide()
        }
    }

    /**
     * The run itself, once nothing is standing in front of it.
     *
     * Extracted from [run] so the popup's two answers can reach it without going back through
     * the `started` guard, which has already done its job by then.
     */
    private suspend fun hide() {
        val packageName = watched ?: return

        // Declared outside the try so a run that throws still closes the window rather than
        // leaving it standing over the app, transparent and eating every touch.
        var result = AutoHideOutcome.Done

        try {
            result = autoHideRunner.run(packageName = packageName)
        } finally {
            if (result == AutoHideOutcome.Done) {
                _finished.update { true }
            } else {
                _outcome.update { result }
            }
        }
    }

    /**
     * Settle everything, then run IMD+ — but only if the device came out clear.
     *
     * ⚠ **A failed restore closes the window and leaves the app alone.** The notification
     * `RevertToDefaultRunner` raised is the report; IMD+ does not run, and [PriorHide] stays
     * suppressed so the next detection of the same app does not prompt again. Tapping *Try
     * again* on that notification restores from the debt, which clears it, which clears the
     * suppression — so the author's "IMD+ should run again once the user has sorted Shizuku out"
     * follows from the condition that actually matters.
     */
    fun restoreThenRun() {
        appScope.launch {
            _outcome.update { AutoHideOutcome.Done }

            if (settingsHiddenRunner.flushPendingReverts()) hide() else _finished.update { true }
        }
    }

    /** Throw the old record away, take the device as it stands, and run. Permanent. */
    fun discardThenRun() {
        appScope.launch {
            _outcome.update { AutoHideOutcome.Done }

            settingsHiddenRunner.discardPendingReverts()

            hide()
        }
    }
""",
    ),
    (
        """    private var started = false
""",
        """    private var started = false

    /** The app this window was opened for, kept so the popup's answers can resume its run. */
    @Volatile
    private var watched: String? = null
""",
    ),
    (
        """import com.android.geto.broadcastreceiver.AutoHideRunner
""",
        """import com.android.geto.broadcastreceiver.AutoHideRunner
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.settingsHidden
import kotlinx.coroutines.flow.first
""",
    ),
]

EDITS[AUTO_ACTIVITY] = [
    (
        """import com.android.geto.feature.apps.PermissionsLostDialog
""",
        """import com.android.geto.feature.apps.PermissionsLostDialog
import com.android.geto.feature.apps.PriorHideDialog
""",
    ),
    (
        """                } else if (overlayStart != null) {
""",
                """                } else if (outcome == AutoHideOutcome.HiddenFromPreviousUse) {
                    // Ahead of the spinner for the same reason as the three above: this is a
                    // conclusion, and IMD+ has not started anything to wait for yet. Both
                    // answers resume the run, so neither closes this window — which is what
                    // lets the spinner below show through while a restore waits on Shizuku.
                    PriorHideDialog(
                        onRestore = viewModel::restoreThenRun,
                        onIgnore = viewModel::discardThenRun,
                    )
                } else if (overlayStart != null) {
""",
    ),
]

# --- Tasker, which has no window --------------------------------------------------------------
EDITS[TASKER] = [
    (
        """import com.android.geto.domain.model.AppSettingsResult
""",
        """import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.AppSettingsResult
""",
    ),
    (
        """                        // ⚠ **The toast used to fire whatever came back**, so an
""",
        """                        // ⚠ **No popup on this route, and it is the only one.** An
                        // automation has no window to ask in, and one that stopped to ask a
                        // question would simply never run — which is worse than proceeding,
                        // because the first-owner rule means a hide over an older hide records
                        // nothing for what is already down and strands nothing.
                        PriorHide.suppress()

                        // ⚠ **The toast used to fire whatever came back**, so an
""",
    ),
]

# --- the per-app settings screen ---------------------------------------------------------------
EDITS[APP_SETTINGS] = [
    (
        """import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
""",
        """import com.android.geto.broadcastreceiver.postAppliedSettingsNotification
import com.android.geto.feature.apps.PriorHideDialog
""",
    ),
    (
        """            AppSettingsResult.NoPermission -> {
                onShowWriteSecureSettingsDialog()

                onResetApplyAppSettingsResult()
            }
""",
        """            AppSettingsResult.NoPermission -> {
                onShowWriteSecureSettingsDialog()

                onResetApplyAppSettingsResult()
            }

            // Nothing was written and the app is not opening. The dialog below is the only
            // surface this screen has for it, and both of its answers come back here.
            AppSettingsResult.HiddenFromPreviousUse -> {
                priorHide = true

                onResetApplyAppSettingsResult()
            }
""",
    ),
    (
        """            AppSettingsResult.DisabledAppSettings -> {
                snackbarHostState.showSnackbar(message = appSettingsDisabled)

                // Without this reset the StateFlow keeps the same value, so every later
                // tap of revert produces no emission and the button looks dead.
                onResetRevertAppSettingsResult()
            }
""",
        """            AppSettingsResult.DisabledAppSettings -> {
                snackbarHostState.showSnackbar(message = appSettingsDisabled)

                // Without this reset the StateFlow keeps the same value, so every later
                // tap of revert produces no emission and the button looks dead.
                onResetRevertAppSettingsResult()
            }

            // A revert cannot produce it — the gate is on the hide — but the `when` is
            // exhaustive over the same enum and silence here would be a compile error rather
            // than a decision.
            AppSettingsResult.HiddenFromPreviousUse -> onResetRevertAppSettingsResult()
""",
    ),
]

EDITS[APP_SETTINGS_VM] = [
    (
        """import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
""",
        """import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
""",
    ),
    # ⚠ And a third time. Three view models gained the same parameter and none of them had
    # ever named its type — one grep the audit suite cannot do, and now does.
    (
        """import kotlinx.coroutines.flow.MutableStateFlow
""",
        """import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
""",
    ),
    (
        """    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
""",
        """    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
""",
    ),
    (
        """    fun applyAppSettings() {
""",
        """    /**
     * The popup's two answers, both of which end in this screen's launch running again.
     *
     * ⚠ **Restore only goes on if the device came out clear**, and ⚠ **Ignore is permanent** —
     * see `SettingsHiddenRunner.discardPendingReverts`. On the application scope because a
     * restore can wait on Shizuku for seconds and this screen may well be left in that time.
     */
    fun restoreThenApply() {
        appScope.launch {
            if (settingsHiddenRunner.flushPendingReverts()) applyAppSettings()
        }
    }

    fun discardThenApply() {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            applyAppSettings()
        }
    }

    fun applyAppSettings() {
""",
    ),
]

# --- the translation check --------------------------------------------------------------------
EDITS[TRANSLATIONS] = [
    (
        """def check(module: pathlib.Path, locale: str) -> list[str]:
""",
        '''# Keys the author has deliberately left untranslated for now.
#
# ⚠ **His standing rule from r2b3 on: translation happens in one pass when everything is built.**
# Listing them here rather than copying English into eleven locales keeps the check honest — a
# missing translation stays visible as a deferral rather than being disguised as a translation
# that happens to be identical — and this set *is* the list that final pass works from.
DEFERRED = {
    "prior_hide_title",
    "prior_hide_restore",
    "prior_hide_ignore",
}


def check(module: pathlib.Path, locale: str) -> list[str]:
''',
    ),
    (
        """    for missing in sorted(set(en) - set(tr)):
        problems.append(f"{module.name}/{locale}: missing '{missing}'")
""",
        """    for missing in sorted(set(en) - set(tr) - DEFERRED):
        problems.append(f"{module.name}/{locale}: missing '{missing}'")
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

    print(f"ok — {len(staged)} files: device-wide gate, shortcut, per-app screen, IMD+, Tasker")

    return 0


if __name__ == "__main__":
    sys.exit(main())
