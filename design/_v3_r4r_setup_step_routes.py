#!/usr/bin/env python3
"""v3-r4r — four setup steps, each wiring the dialog it is made of.

    "just use those dialogs with Skip and Next buttons below"

The dialogs already know how to be a step - `onSkip` and `stepTitle`, from the two scripts before
this one. What was missing is the wiring, and this is it: one composable per step, each obtaining
`SettingsViewModel` and handing the dialog exactly what `SettingsRoute` hands it.

## ⚠ In `:feature:settings`, not in `:app`, and that is the decision worth reading

The steps need derived state that lives on the settings screen: `overlayBlockedPaths`, the
own-detector rule, and `AutoUnhideRequirements` - which is itself built from the auto-unhide
checks *and* the auto-hide system checks. Rebuilding that in `:app` would be a second copy of the
reasoning that decides when a row is blocked, and it would drift from the first the next time a
requirement is added.

So the derivations stay in the module that owns them and `:app` gains no state at all: no
accessibility list, no overlay list, no auto-unhide callbacks threaded through `SetupScreen`. It
is the argument that made the Shizuku page draw `ShizukuSection` rather than copy it.

## ⚠ The DOOA step can decide it has nothing to show

    "if IMD fails to get DOOA list to load skip it"

`overlayPackages` is nullable, and null after the read has finished means the device would not
answer. The step calls [onUnavailable] then, and the flow moves past it - so a step that could
only show an error never appears at all. While the read is still running it draws the same
loading dialog the settings screen draws.

⚠ **`LaunchedEffect`, not a call during composition.** Advancing the flow from inside a
composition is a state write during layout; keyed on the two values it reads, it fires once when
they settle.

## ⚠ The auto unhide step carries all five of its satellites

The minutes pickers, the ADB command, the how-it-works dialog and the used-for refusal are part of
that page, not of the settings screen that happens to host it today. A step without them would be
a page whose rows open nothing.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

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

STEPS_TEXT = LICENCE + '''package com.android.geto.feature.settings

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.domain.model.AutoUnhideRequirements
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.accessibilityManageable
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.feature.settings.dialog.AccessibilityServicesDialog
import com.android.geto.feature.settings.dialog.AutoUnhideAdbCommandDialog
import com.android.geto.feature.settings.dialog.AutoUnhideHowItWorksDialog
import com.android.geto.feature.settings.dialog.AutoUnhideMinutesDialog
import com.android.geto.feature.settings.dialog.AutoUnhidePage
import com.android.geto.feature.settings.dialog.AutoUnhideUsedForBlockedDialog
import com.android.geto.feature.settings.dialog.OverlayLoadingDialog
import com.android.geto.feature.settings.dialog.OverlayPackagesDialog
import com.android.geto.feature.settings.dialog.SettingsToHideDialog
import com.android.geto.feature.settings.dialog.rememberAutoHideSystemChecks
import com.android.geto.feature.settings.dialog.usageAccessSettingsIntent

/**
 * The configuration steps of the setup flow.
 *
 * ⚠ **Each one is the dialog Settings already shows, drawn flat.** Not a page built to look like
 * it - the same composable, with `onSkip` and `stepTitle` set. A row added to any of those
 * dialogs appears here without anybody remembering to add it twice.
 *
 * ⚠ **They live here rather than in `:app` because of what they have to derive.**
 * `overlayBlockedPaths`, the own-detector rule and [AutoUnhideRequirements] are all built from
 * state that belongs to the settings screen; a copy of that reasoning in the app module would be
 * a second answer to "is this row blocked", free to drift from the first. This way `:app` needs
 * no new state at all.
 *
 * Every step takes the same pair: [onSkip] moves on without writing, [onNext] moves on after the
 * dialog has written. The dialogs decide which is which - see their `onSkip` parameter.
 */

/** The accessibility services IMD is allowed to manage. */
@Composable
fun AccessibilityStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val services by viewModel.accessibilityServices.collectAsStateWithLifecycle()

    val serviceState by viewModel.autoHideServiceState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    AccessibilityServicesDialog(
        modifier = modifier,
        accessibilityServices = services,
        selectedServices = userData.managedAccessibilityServices,
        // The same rule the settings screen uses: IMD's own detector is only special while
        // IMD+ is on, because that is the only time anything is holding it.
        ownDetector = if (userData.autoHideEnabled) serviceState.ownDetector else "",
        stepTitle = stepTitle,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onRefresh = viewModel::refreshAccessibilityServices,
        onUpdateManagedAccessibilityServices = viewModel::updateManagedAccessibilityServices,
    )
}

/**
 * The apps whose Display over other apps IMD is allowed to manage.
 *
 * ⚠ **Skips itself when the device will not answer.** A null list after the read has finished is
 * the unreadable case, and a step that could only show an error is a step nobody should be shown
 * - the author's *"if IMD fails to get DOOA list to load skip it"*.
 */
@Composable
fun OverlayStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    /** Called instead of drawing anything, when the overlay list cannot be read. */
    onUnavailable: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val packages by viewModel.overlayPackages.collectAsStateWithLifecycle()

    val loading by viewModel.overlayPackagesLoading.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.refreshOverlayPackages()
    }

    // ⚠ In an effect rather than in the composition: advancing the flow is a state write, and a
    // state write during composition is a write during layout.
    LaunchedEffect(loading, packages) {
        if (!loading && packages == null) onUnavailable()
    }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    val list = packages

    if (list == null) {
        // Either still reading, or unreadable - and the effect above has already moved past
        // the second case by the time this draws again.
        OverlayLoadingDialog()

        return
    }

    OverlayPackagesDialog(
        modifier = modifier,
        overlayPackages = list,
        selectedPackages = userData.managedOverlayPackages,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onRefresh = viewModel::refreshOverlayPackages,
        onUpdateManagedOverlayPackages = viewModel::updateManagedOverlayPackages,
    )
}

/** Which settings a launch hides. */
@Composable
fun SettingsToHideStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    SettingsToHideDialog(
        modifier = modifier,
        states = userData.settingsToHide,
        stepTitle = stepTitle,
        onSkip = onSkip,
        overlayBlockedPaths = overlayBlockedPaths(userData = userData),
        accessibilityManageable = userData.accessibilityManageable,
        manageShizukuEffective = userData.manageShizukuEffective,
        shizukuForkMode = userData.shizukuForkMode,
        hidingFramework = userData.hidingFramework,
        unhidingFramework = userData.unhidingFramework,
        restoreWirelessDebugging = userData.restoreWirelessDebugging,
        onDismissRequest = onNext,
        onUpdateSettingsToHide = viewModel::updateSettingsToHide,
        onUpdateRestoreWirelessDebugging = viewModel::updateRestoreWirelessDebugging,
    )
}

/**
 * Auto unhide, whole.
 *
 * ⚠ **With all five of its satellites.** The minutes pickers, the ADB command, the how-it-works
 * dialog and the used-for refusal belong to this page rather than to the settings screen that
 * hosts it today, and a step without them is a page whose rows open nothing.
 */
@Composable
fun AutoUnhideStep(
    modifier: Modifier = Modifier,
    stepTitle: String,
    onSkip: () -> Unit,
    onNext: () -> Unit,
    viewModel: SettingsViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val uiState by viewModel.settingsUiState.collectAsStateWithLifecycle()

    val checks by viewModel.autoUnhideChecks.collectAsStateWithLifecycle()

    val systemChecks = rememberAutoHideSystemChecks()

    var showHowItWorks by rememberSaveable { mutableStateOf(false) }

    var showScreenLockMinutes by rememberSaveable { mutableStateOf(false) }

    var showIdleMinutes by rememberSaveable { mutableStateOf(false) }

    var showAdbCommand by rememberSaveable { mutableStateOf(false) }

    var showUsedForBlocked by rememberSaveable { mutableStateOf(false) }

    val userData = (uiState as? SettingsUiState.Success)?.userData ?: return

    // The same assembly the settings screen makes, from the same three sources. Nothing here is
    // stored: both permissions are granted by shell and arrive without IMD being told.
    val requirements = remember(checks, systemChecks, userData) {
        AutoUnhideRequirements(
            dumpPermission = checks.dumpPermission,
            exitReasonsSupported = checks.exitReasonsSupported,
            usageAccess = checks.usageAccess,
            batteryUnrestricted = systemChecks.batteryUnrestricted,
            notificationsAllowed = systemChecks.notificationsAllowed,
            onAppLaunch = userData.autoUnhideOnAppLaunch,
            onTile = userData.autoUnhideOnTile,
            onSwipe = userData.autoUnhideOnSwipe,
            onScreenLock = userData.autoUnhideOnScreenLock,
            onIdle = userData.autoUnhideOnIdle,
        )
    }

    AutoUnhidePage(
        modifier = modifier,
        userData = userData,
        requirements = requirements,
        stepTitle = stepTitle,
        onSkip = onSkip,
        onDismissRequest = onNext,
        onUpdateAutoUnhideEnabled = viewModel::updateAutoUnhideEnabled,
        onUpdateTriggers = viewModel::updateAutoUnhideTriggers,
        onUpdateUsedFor = { onAppLaunch, onTile ->
            // Refused rather than silently ignored, exactly as on the settings screen: the
            // checkbox will not move, and a control that will not move has to say why.
            if (!viewModel.updateAutoUnhideUsedFor(onAppLaunch, onTile)) {
                showUsedForBlocked = true
            }
        },
        onOpenScreenLockMinutes = { showScreenLockMinutes = true },
        onOpenIdleMinutes = { showIdleMinutes = true },
        onGrantDumpPermission = viewModel::grantAutoUnhideDumpPermission,
        onShowAdbCommand = { showAdbCommand = true },
        onGrantUsageAccess = viewModel::grantAutoUnhideUsageAccess,
        onOpenUsageSettings = { context.startActivity(usageAccessSettingsIntent()) },
        onOpenHowItWorks = { showHowItWorks = true },
        onRefreshSystemChecks = {
            systemChecks.refresh()

            viewModel.refreshAutoUnhideChecks()
        },
    )

    if (showHowItWorks) {
        AutoUnhideHowItWorksDialog(onDismissRequest = { showHowItWorks = false })
    }

    if (showScreenLockMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_lock),
            selected = userData.autoUnhideScreenLockMinutes,
            onSelect = viewModel::updateAutoUnhideScreenLockMinutes,
            onDismissRequest = { showScreenLockMinutes = false },
        )
    }

    if (showIdleMinutes) {
        AutoUnhideMinutesDialog(
            title = stringResource(R.string.auto_unhide_time_idle),
            selected = userData.autoUnhideIdleMinutes,
            onSelect = viewModel::updateAutoUnhideIdleMinutes,
            onDismissRequest = { showIdleMinutes = false },
        )
    }

    if (showAdbCommand) {
        AutoUnhideAdbCommandDialog(
            command = viewModel.autoUnhideAdbCommand(),
            onDismissRequest = { showAdbCommand = false },
        )
    }

    if (showUsedForBlocked) {
        AutoUnhideUsedForBlockedDialog(onDismissRequest = { showUsedForBlocked = false })
    }
}

/**
 * Whether the Display over other apps step has anything to configure.
 *
 * ⚠ **Read before the step is reached, not inside it.** The author's rule is that the step only
 * appears for an install where Shizuku is fully set up on a fork that can drive overlay access -
 * *"only show if shizuku thedjchi configured fully before"* - and that is a question about stored
 * values, answerable by the flow without composing anything.
 *
 * The other reason the step can be absent - the device refusing to list its overlay packages -
 * is not knowable until the read has run, and is handled by the step itself.
 */
fun overlayStepApplies(userData: UserData): Boolean =
    userData.isShizukuConfigured &&
        userData.shizukuForkMode.supportsIntents &&
        userData.manageShizukuEffective
'''

EDITS: list[tuple[str, str, str]] = [
    # `overlayBlockedPaths` is file-private; the steps file is a different file in the same
    # package, so it has to be at least internal.
    (
        SCREEN,
        """private fun overlayBlockedPaths(userData: UserData): List<String>? {""",
        """internal fun overlayBlockedPaths(userData: UserData): List<String>? {""",
    ),
]

# Names the new file reaches for that must exist, checked against the files that declare them
# because none of these modules compiles here.
DECLARED = [
    ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt", [
        "fun refreshAccessibilityServices(",
        "fun updateManagedAccessibilityServices(",
        "fun refreshOverlayPackages(",
        "fun updateManagedOverlayPackages(",
        "fun updateSettingsToHide(",
        "fun updateRestoreWirelessDebugging(",
        "fun updateAutoUnhideEnabled(",
        "fun updateAutoUnhideTriggers(",
        "fun updateAutoUnhideUsedFor(",
        "fun updateAutoUnhideScreenLockMinutes(",
        "fun updateAutoUnhideIdleMinutes(",
        "fun grantAutoUnhideDumpPermission(",
        "fun grantAutoUnhideUsageAccess(",
        "fun autoUnhideAdbCommand(",
        "fun refreshAutoUnhideChecks(",
        "val accessibilityServices",
        "val overlayPackages",
        "val overlayPackagesLoading",
        "val autoUnhideChecks",
        "val autoHideServiceState",
        "val settingsUiState",
    ]),
]


def main() -> int:
    steps = ROOT / STEPS

    if steps.exists():
        print(f"REFUSED: {STEPS}\n  already exists; this script creates it")
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
            print(f"REFUSED: {relative}\n  the anchor matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, names in DECLARED:
        text = (ROOT / relative).read_text(encoding="utf-8")

        missing = [name for name in names if name not in text]

        if missing:
            print(f"REFUSED: {relative}\n  the steps file reaches for absent names: {missing}")
            return 1

    # The four dialogs and the two helpers must be public, or `:app` cannot reach the steps'
    # own callers and the steps cannot reach the dialogs.
    for relative, name in (
        ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AccessibilityServicesDialog.kt", "\nfun AccessibilityServicesDialog("),
        ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/OverlayPackagesDialog.kt", "\nfun OverlayPackagesDialog("),
        ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt", "\nfun SettingsToHideDialog("),
        ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhidePage.kt", "\nfun AutoUnhidePage("),
    ):
        if name not in (ROOT / relative).read_text(encoding="utf-8"):
            print(f"REFUSED: {relative}\n  {name.strip()!r} is not public")
            return 1

    steps.write_text(STEPS_TEXT, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {STEPS}  :: new — four steps and the overlay gate")
    print(f"  ok        {SCREEN}  :: overlayBlockedPaths is internal, so the steps can read it")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
