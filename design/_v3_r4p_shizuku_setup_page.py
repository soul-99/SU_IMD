#!/usr/bin/env python3
"""v3-r4p — the Shizuku setup page draws the real configuration section.

The companion to `_v3_r4p_shizuku_section_shared.py`, which made `ShizukuSection` public and gave
it `showManageRow` and `commitDelay`. This replaces r4o's re-implementation with a page that
holds a draft and hands the section its callbacks.

## The draft

Four `rememberSaveable` values, assembled into a `UserData` copy that the section is given. The
section owns its own field state and reports through the callbacks, so the four values below are
sinks: they are what the **Manage shizuku configuration** button reads, and what `onSave` sends.
Nothing reaches the repository until that button is pressed, so **Skip** still leaves the install
exactly as it found it.

⚠ **`commitDelay = Duration.ZERO`.** See the shared-section script: a 500 ms debounce between the
last keystroke and the draft is the difference between a filled form and *"Please fill all fields
first"*.

## ⚠ The fork starts Unset whatever is stored

    "in this page keep both thedjchi and shevery toggles unselected until user selects one"
    "also at initial shizuku intitialisation page keep both toggles unselected until user
     selects one"

Said twice, because r4o's page seeded from the stored fork and `DetectShizukuForkUseCase` writes
one on a fresh install whenever it finds either app on the device - so a toggle arrived already
picked. The draft therefore starts at [ShizukuForkMode.Unset] regardless, and nothing is lost:
picking a fork runs the section's own `commitFork`, which fills the package and start action in
from `ShizukuForkDefaults` and the installed-app list.

The start action starts blank for the same reason - the section derives one from the fork, and a
seeded value would be an answer to a question nobody has asked yet.

## The installed-app list

The package field's picker and its ⟳ need one, and `MainActivityViewModel` had none. It gains the
same three fields and the same `refreshInstalledApps` `SettingsViewModel` has, over the same
`GetInstalledAppsUseCase` - a counter rather than a list-changed wait, for the reason documented
there.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/ShizukuSetupPage.kt"

SETUP = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

VIEWMODEL = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"

ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"

PAGE_TEXT = '''/*
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
package com.android.geto.onboarding

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UserData
import com.android.geto.feature.settings.ShizukuSection
import kotlin.time.Duration
import com.android.geto.feature.settings.R as settingsR

/**
 * The Shizuku configuration, offered once during setup.
 *
 * ⚠ **It draws the real section, not a copy of it.** r4o's page re-implemented the fields and
 * lost fifteen things - the links, both ⓘ buttons, the *supported, but not recommended* caution,
 * the app picker and its ⟳, the *No Shizuku app found* line, the masked auth key, the fields
 * staying hidden until a fork is picked, and the Shevery choice being held until its notice is
 * acknowledged. [ShizukuSection] is public for exactly this, and the author's *"keep everything
 * from the original config page"* is only true for as long as there is one of it.
 *
 * ⚠ **A draft, not live writes.** The four values below are where the section's callbacks land,
 * and nothing reaches the repository until **Manage shizuku configuration** is pressed. That is
 * what makes **Skip** a real answer rather than a half-configured install.
 *
 * ⚠ **Both fork choices start unselected**, whatever is stored - the author's instruction, twice.
 * `DetectShizukuForkUseCase` writes a fork on a fresh install as soon as it sees either app, so
 * seeding from the stored value handed the reader a decision already made for them. Nothing is
 * lost by starting at [ShizukuForkMode.Unset]: picking a fork fills the package and action in
 * from `ShizukuForkDefaults`, which is what the section does in Settings too.
 */
@Composable
internal fun ShizukuSetupPage(
    modifier: Modifier = Modifier,
    userData: UserData,
    installedApps: List<InstalledAppData>,
    installedAppsRevision: Int,
    onRefreshInstalledApps: (Boolean) -> Unit,
    onSave: (
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) -> Unit,
    onSkip: () -> Unit,
) {
    var forkMode by rememberSaveable { mutableStateOf(ShizukuForkMode.Unset) }

    var packageName by rememberSaveable { mutableStateOf(userData.shizukuPackageName) }

    // Blank on purpose. The section derives one from whichever fork is picked, and a seeded
    // value would be an answer to a question that has not been asked yet.
    var startAction by rememberSaveable { mutableStateOf("") }

    var authKey by rememberSaveable { mutableStateOf(userData.shizukuAuthKey) }

    var showFillFirst by rememberSaveable { mutableStateOf(false) }

    // ⚠ **The same four terms as `UserData.isShizukuConfigured`**, asked of the draft rather
    // than of the stored values - nothing here is stored yet. Kept as one expression so the
    // button and the pop-up cannot disagree about what "filled" means.
    val configured = forkMode != ShizukuForkMode.Unset &&
        packageName.isNotBlank() &&
        startAction.isNotBlank() &&
        (!forkMode.requiresAuthKey || authKey.isNotBlank())

    // What the section is shown: the install as it stands, with the four draft values over it.
    val draft = userData.copy(
        shizukuForkMode = forkMode,
        shizukuPackageName = packageName,
        shizukuStartAction = startAction,
        shizukuAuthKey = authKey,
    )

    if (showFillFirst) {
        ConfigureFirstDialog(
            message = stringResource(R.string.shizuku_setup_fill_first),
            dismissLabel = stringResource(settingsR.string.understood),
            onDismissRequest = { showFillFirst = false },
        )
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 8.dp, vertical = 24.dp),
    ) {
        Spacer(modifier = Modifier.height(8.dp))

        Text(
            modifier = Modifier.padding(horizontal = 16.dp),
            text = stringResource(settingsR.string.shizuku_setup_page_title),
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.height(12.dp))

        ShizukuSection(
            userData = draft,
            installedApps = installedApps,
            // Nothing on this page draws the switch, so nothing can move it. The Manage button
            // below is what turns it on, through onSave.
            onUpdateManageShizuku = {},
            onUpdateShizukuForkMode = { forkMode = it },
            onUpdateShizukuAuthKey = { authKey = it },
            onUpdateShizukuPackageName = { packageName = it },
            onUpdateShizukuStartAction = { startAction = it },
            onRefreshInstalledApps = onRefreshInstalledApps,
            installedAppsRevision = installedAppsRevision,
            // The recommendation without the switch it belongs to - see ShizukuSection.
            showManageRow = false,
            // ⚠ **No debounce here.** Settings can afford to wait 500 ms after the last
            // keystroke because it is always live; this page's button reads the draft, and a
            // field typed just before the tap would otherwise still be missing from it - a
            // full form met with "Please fill all fields first".
            commitDelay = Duration.ZERO,
        )

        Spacer(modifier = Modifier.height(24.dp))

        // ⚠ **Enabled whatever the draft says, and greyed by its colours instead.** A disabled
        // Button swallows the press inside its own bounds, and a button that does nothing at
        // all is how somebody decides the page is broken rather than that a field is empty.
        Button(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            colors = if (configured) {
                ButtonDefaults.buttonColors()
            } else {
                ButtonDefaults.buttonColors(
                    containerColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f),
                    contentColor = MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f),
                )
            },
            onClick = {
                if (configured) {
                    onSave(forkMode, packageName, startAction, authKey)
                } else {
                    showFillFirst = true
                }
            },
        ) {
            Text(text = stringResource(R.string.shizuku_setup_manage))
        }

        Spacer(modifier = Modifier.height(4.dp))

        TextButton(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 16.dp),
            onClick = onSkip,
        ) {
            Text(text = stringResource(R.string.shizuku_setup_skip))
        }

        Spacer(modifier = Modifier.height(8.dp))
    }
}
'''

EDITS: list[tuple[str, str, str]] = [
    # ---- SetupScreen: three new parameters threaded to the page ----
    (
        SETUP,
        """    /** Seeds the Shizuku page's draft, including whatever the fork detection found. */
    userData: UserData,""",
        """    /**
     * Seeds the Shizuku page's draft.
     *
     * ⚠ Its **fork** is not read from here. The page starts both toggles unselected whatever is
     * stored, because `DetectShizukuForkUseCase` writes one on a fresh install as soon as it
     * sees either app - see [ShizukuSetupPage].
     */
    userData: UserData,
    /** For the Shizuku page's package picker and its re-detect button. */
    installedApps: List<InstalledAppData>,
    installedAppsRevision: Int,
    onRefreshInstalledApps: (Boolean) -> Unit,""",
    ),
    (
        SETUP,
        """import com.android.geto.domain.model.ShizukuForkMode""",
        """import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ShizukuForkMode""",
    ),
    # ---- SetupScreen: the page's own call site ----
    (
        SETUP,
        """        SHIZUKU -> ShizukuSetupPage(
            modifier = modifier,
            userData = userData,""",
        """        SHIZUKU -> ShizukuSetupPage(
            modifier = modifier,
            userData = userData,
            installedApps = installedApps,
            installedAppsRevision = installedAppsRevision,
            onRefreshInstalledApps = onRefreshInstalledApps,""",
    ),
    # ---- MainActivity: collect the two flows ----
    (
        ACTIVITY,
        """                val priorHide by viewModel.priorHide.collectAsStateWithLifecycle()""",
        """                val priorHide by viewModel.priorHide.collectAsStateWithLifecycle()

                // For the Shizuku setup page's package picker. Empty until the section asks,
                // which it does when it is first composed - so nothing is enumerated for a
                // user who never reaches that page.
                val installedApps by viewModel.installedApps.collectAsStateWithLifecycle()

                val installedAppsRevision by viewModel.installedAppsRevision
                    .collectAsStateWithLifecycle()""",
    ),
    (
        ACTIVITY,
        """                                        userData = uiState.userData,
                                        onSaveShizuku = viewModel::saveShizukuConfiguration,""",
        """                                        userData = uiState.userData,
                                        installedApps = installedApps,
                                        installedAppsRevision = installedAppsRevision,
                                        onRefreshInstalledApps = viewModel::refreshInstalledApps,
                                        onSaveShizuku = viewModel::saveShizukuConfiguration,""",
    ),
    # ---- MainActivityViewModel: the installed-app list ----
    (
        VIEWMODEL,
        """    fun saveShizukuConfiguration(""",
        """    private val _installedApps = MutableStateFlow<List<InstalledAppData>>(emptyList())

    /**
     * The device's apps, for the Shizuku setup page's package picker.
     *
     * ⚠ Not read on the way in. Enumerating every package and rasterising an icon each is far
     * too heavy to do while somebody is being walked through permissions, so the section asks
     * for it when it is first composed - the same arrangement `SettingsViewModel` has, over the
     * same use case.
     */
    val installedApps = _installedApps.asStateFlow()

    /**
     * Bumped after the list is published, so a caller waiting on a refresh wakes to find the
     * apps already there.
     *
     * A counter rather than a wait for the list to *change*: a re-detect that finds exactly what
     * was already there changes nothing, and a waiter watching the list would wait out its
     * ceiling for an answer that had already arrived.
     */
    private val _installedAppsRevision = MutableStateFlow(0)
    val installedAppsRevision = _installedAppsRevision.asStateFlow()

    /** Guards against two enumerations running at once; only ever touched from the main thread. */
    private val installedAppsInFlight = MutableStateFlow(false)

    fun refreshInstalledApps(force: Boolean = false) {
        if (installedAppsInFlight.value) return

        if (!force && _installedApps.value.isNotEmpty()) return

        installedAppsInFlight.update { true }

        viewModelScope.launch {
            try {
                _installedApps.update { getInstalledAppsUseCase() }
            } finally {
                installedAppsInFlight.update { false }

                _installedAppsRevision.update { it + 1 }
            }
        }
    }

    fun saveShizukuConfiguration(""",
    ),
    (
        VIEWMODEL,
        """    private val settingsHiddenRunner: SettingsHiddenRunner,""",
        """    private val settingsHiddenRunner: SettingsHiddenRunner,
    // r4p: the Shizuku setup page draws the real configuration section, whose package field
    // offers a picker over the installed apps.
    private val getInstalledAppsUseCase: GetInstalledAppsUseCase,""",
    ),
]

# Imports that must be present afterwards, added only if they are not already there.
IMPORTS: list[tuple[str, list[str]]] = [
    (
        VIEWMODEL,
        [
            "import com.android.geto.domain.model.InstalledAppData",
            "import com.android.geto.domain.usecase.GetInstalledAppsUseCase",
        ],
    ),
]

AFTER = [
    (SETUP, "installedApps: List<InstalledAppData>,", 1),
    (SETUP, "onRefreshInstalledApps: (Boolean) -> Unit,", 1),
    # Declared once and handed on once.
    (SETUP, "installedApps = installedApps,", 1),
    (SETUP, "installedAppsRevision = installedAppsRevision,", 1),
    (SETUP, "onRefreshInstalledApps = onRefreshInstalledApps,", 1),
    (ACTIVITY, "onRefreshInstalledApps = viewModel::refreshInstalledApps,", 1),
    (ACTIVITY, "viewModel.installedApps.collectAsStateWithLifecycle()", 1),
    (ACTIVITY, "installedApps = installedApps,", 1),
    (VIEWMODEL, "fun refreshInstalledApps(", 1),
    (VIEWMODEL, "getInstalledAppsUseCase", 2),
    (VIEWMODEL, "MutableStateFlow", 5),
]


def add_import(text: str, statement: str) -> str:
    """Insert one import in sorted position among the plain `import com.` lines."""
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    if not indices:
        raise SystemExit(f"REFUSED: no com.android.geto imports to sort {statement!r} into")

    target = next(
        (i for i in indices if lines[i] > statement + "\n"),
        indices[-1] + 1,
    )

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    page = ROOT / PAGE

    if not page.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    # The page is replaced wholesale rather than patched: r4o's body is the thing being
    # removed. Asserted to be r4o's, so this cannot silently overwrite a later revision.
    old_page = page.read_text(encoding="utf-8")

    for marker in ("internal fun ShizukuSetupPage(", "private fun ForkChoice(", "OutlinedTextField("):
        if marker not in old_page:
            print(f"REFUSED: {PAGE}\n  {marker!r} is absent; this is not the page r4o wrote")
            return 1

    if "ShizukuSection(" in old_page:
        print(f"REFUSED: {PAGE}\n  already draws ShizukuSection; nothing to replace")
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

    for relative, statements in IMPORTS:
        for statement in statements:
            staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    page.write_text(PAGE_TEXT, encoding="utf-8")

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: draws ShizukuSection over a draft")
    print(f"  ok        {SETUP}  :: installed apps threaded through")
    print(f"  ok        {ACTIVITY}  :: passes them from the ViewModel")
    print(f"  ok        {VIEWMODEL}  :: installed apps, revision and refresh")
    print(f"\nwrote {len(staged) + 1} file(s), {len(EDITS) + 1} edit(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
