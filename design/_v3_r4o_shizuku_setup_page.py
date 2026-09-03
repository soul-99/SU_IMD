#!/usr/bin/env python3
"""v3-r4o — a Shizuku page in setup, between the permissions step and the reminders.

The author:

    "can we add a new initialisation screen shizuku setup after permission grant setting
     screen? which just shows all the contents of shizuku config section with page buttons
     below 'skip' and 'manage shizuku configuration' and the manage button is only allowed to
     be clicked when all values are filled, otherwise display a popup on clicking 'please fill
     all fields first, in this page keep both thedjchi and shevery toggles unselected until
     user selects one then make one selected mandatory"

and, after seeing the template:

    "no need to show manage shizuku toggle in the new shizuku page as button already enabled it"

---

## What the page is

The Shizuku configuration section's contents, minus its master switch: the two red lines, the
two fork choices with their setup pop-ups, and the three fields. Under them, **Manage shizuku
configuration** and **Skip**.

⚠ **No Manage Shizuku toggle, and its bold "RECOMMENDED ON" line goes with it.** The button is
what switches it on, so a toggle above would ask the same question twice — and a recommendation
about a control that is not on the page describes nothing.

## Both toggles unselected

`ShizukuForkMode.Unset` already exists for exactly this, and its KDoc says why: *"there is no
safe default. Guessing produces the one outcome worth avoiding: a toggle that looks configured
and silently does nothing."* Once one is picked, the picker cannot be returned to neither —
"then make one selected mandatory".

⚠ **`DetectShizukuForkUseCase` still guesses, at the author's decision** — *"leave the guess as
it is"*. It only writes when it actually finds a Shizuku or Shevery app installed, so on a device
with neither, which is the case he was describing, both toggles do open unselected. On a device
with one installed the page opens with that fork picked, which he has accepted.

## The Manage button

Greyed until the draft satisfies the same four terms as `UserData.isShizukuConfigured` — a fork
chosen, a package, a start action, and an auth key when the fork needs one. ⚠ **Greyed but still
clickable**, so the press can raise *'Please fill all fields first'* rather than doing nothing:
the same rule every other blocked control in this app follows, and the reason `SettingToHideRow`
and `SettingsColumn` wrap their controls instead of disabling them.

⚠ **The button writes the four fields first and the master switch last.** They are separate
writes, and a process death between them has to leave a filled-in configuration with the switch
off — which `manageShizukuEffective` reads as "not managing" and the user can turn on in one tap
— rather than a switch on over a half-written configuration.

## Skip

Always live, and it does not write. An install that skips keeps whatever the fork detection left
and `manageShizuku` off, which is the fresh-install default.

⚠ **The page does not come back.** The author chose "after Permissions, before reminders", and a
skip that reappeared next launch would be a decision the app refused to accept.

## The three labels

His words, with a leading capital on each — the same correction he made for the pop-up when
asked. "shizuku" inside the button label is left lower-case as he wrote it.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/ShizukuSetupPage.kt"
SETUP = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"
ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"
VM = "app/src/main/kotlin/com/android/geto/activity/main/MainActivityViewModel.kt"
STRINGS = "app/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"

NEW_PAGE = '''/*
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
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UserData
import com.android.geto.feature.settings.dialog.SheveryNoticeDialog
import com.android.geto.feature.settings.dialog.ThedjchiSetupDialog
import com.android.geto.feature.settings.R as settingsR

/**
 * The Shizuku configuration, offered once during setup.
 *
 * ⚠ **The section's contents without its master switch.** The author's page: the two red lines,
 * the fork choice and the three fields, with **Manage shizuku configuration** and **Skip** under
 * them. The Manage button is what switches Manage Shizuku on — *"no need to show manage shizuku
 * toggle in the new shizuku page as button already enabled it"* — so the toggle and its bold
 * recommendation are not drawn here.
 *
 * ⚠ **A draft, not live writes.** Every field edits local state and nothing reaches the
 * repository until Manage is pressed. Skip therefore leaves the install exactly as it found it,
 * which is what makes skipping a real answer rather than a half-configured one.
 *
 * ⚠ **Both fork choices start unselected** when nothing has chosen one — [ShizukuForkMode.Unset],
 * which exists precisely because guessing produces "a toggle that looks configured and silently
 * does nothing". Once one is picked there is no way back to neither: the author's *"then make one
 * selected mandatory"*, and the reason the two rows are `selectable` rather than a checkbox pair.
 */
@Composable
internal fun ShizukuSetupPage(
    modifier: Modifier = Modifier,
    userData: UserData,
    onSave: (
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) -> Unit,
    onSkip: () -> Unit,
) {
    // Seeded from whatever the fork detection found, which may be nothing at all.
    var forkMode by rememberSaveable { mutableStateOf(userData.shizukuForkMode) }

    var packageName by rememberSaveable { mutableStateOf(userData.shizukuPackageName) }

    var startAction by rememberSaveable { mutableStateOf(userData.shizukuStartAction) }

    var authKey by rememberSaveable { mutableStateOf(userData.shizukuAuthKey) }

    var showThedjchiNotice by rememberSaveable { mutableStateOf(false) }

    var showSheveryNotice by rememberSaveable { mutableStateOf(false) }

    var showFillFirst by rememberSaveable { mutableStateOf(false) }

    // ⚠ **The same four terms as `UserData.isShizukuConfigured`**, asked of the draft rather
    // than of the stored values — nothing here is stored yet. Kept as one expression so the
    // button and the pop-up cannot disagree about what "filled" means.
    val configured = forkMode != ShizukuForkMode.Unset &&
        packageName.isNotBlank() &&
        startAction.isNotBlank() &&
        (!forkMode.requiresAuthKey || authKey.isNotBlank())

    if (showThedjchiNotice) {
        ThedjchiSetupDialog(onDismissRequest = { showThedjchiNotice = false })
    }

    if (showSheveryNotice) {
        SheveryNoticeDialog(onDismissRequest = { showSheveryNotice = false })
    }

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
            .padding(24.dp),
    ) {
        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(settingsR.string.shizuku_setup_page_title),
            style = MaterialTheme.typography.titleLarge,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.height(12.dp))

        // The two red lines the settings section shows, unchanged. Plain rather than
        // emphasised: the bold phrases there are built by `emphasised`, which lives in
        // design-system and would need the same three name resources threading through here
        // for a page somebody reads once.
        Text(
            text = stringResource(settingsR.string.shizuku_rikka_warning),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error,
        )

        Spacer(modifier = Modifier.height(8.dp))

        Text(
            text = stringResource(settingsR.string.shizuku_rikka_recommend_prefix) +
                " " + stringResource(settingsR.string.shizuku_rikka_recommend_link),
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.error,
        )

        Spacer(modifier = Modifier.height(16.dp))

        ForkChoice(
            label = stringResource(settingsR.string.shizuku_fork_thedjchi),
            note = stringResource(settingsR.string.shizuku_fork_mode_thedjchi_suffix),
            selected = forkMode == ShizukuForkMode.Thedjchi,
            onSelect = {
                forkMode = ShizukuForkMode.Thedjchi

                showThedjchiNotice = true
            },
        )

        ForkChoice(
            label = stringResource(settingsR.string.shizuku_fork_shevery),
            note = stringResource(settingsR.string.shizuku_fork_shevery_caution),
            selected = forkMode == ShizukuForkMode.Other,
            onSelect = {
                forkMode = ShizukuForkMode.Other

                showSheveryNotice = true
            },
        )

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = packageName,
            onValueChange = { packageName = it },
            label = { Text(text = stringResource(settingsR.string.shizuku_package_name)) },
            singleLine = true,
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = startAction,
            onValueChange = { startAction = it },
            label = { Text(text = stringResource(settingsR.string.shizuku_start_action)) },
            singleLine = true,
        )

        Spacer(modifier = Modifier.height(8.dp))

        OutlinedTextField(
            modifier = Modifier.fillMaxWidth(),
            value = authKey,
            onValueChange = { authKey = it },
            label = { Text(text = stringResource(settingsR.string.shizuku_auth_key)) },
            singleLine = true,
        )

        Spacer(modifier = Modifier.height(24.dp))

        // ⚠ **Enabled whatever the draft says, and greyed by its colours instead.** A disabled
        // Button swallows the press inside its own bounds, and a button that does nothing at
        // all is how somebody decides the page is broken rather than that a field is empty.
        Button(
            modifier = Modifier.fillMaxWidth(),
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
            modifier = Modifier.fillMaxWidth(),
            onClick = onSkip,
        ) {
            Text(text = stringResource(R.string.shizuku_setup_skip))
        }

        Spacer(modifier = Modifier.height(8.dp))
    }
}

/**
 * One fork, and the whole row is the target.
 *
 * `selectable` rather than a plain `clickable` so the row reads as one of a set to a screen
 * reader, and so that picking one can never unpick it — which is the author's "then make one
 * selected mandatory".
 */
@Composable
private fun ForkChoice(
    label: String,
    note: String,
    selected: Boolean,
    onSelect: () -> Unit,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .selectable(selected = selected, onClick = onSelect)
            .padding(vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        RadioButton(selected = selected, onClick = null)

        Spacer(modifier = Modifier.width(12.dp))

        Column {
            Text(text = label, style = MaterialTheme.typography.bodyLarge)

            Text(
                text = note,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
'''

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# The strings
# ---------------------------------------------------------------------------------------
edit(
    STRINGS,
    "the page's three labels",
    """    <string name="tip_got_it">Got it</string>""",
    """    <!-- The Shizuku page in setup. The author's words, with a leading capital on each. -->
    <string name="shizuku_setup_manage">Manage shizuku configuration</string>
    <string name="shizuku_setup_skip">Skip</string>
    <string name="shizuku_setup_fill_first">Please fill all fields first</string>

    <string name="tip_got_it">Got it</string>""",
)

edit(
    "feature/settings/src/main/res/values/strings.xml",
    "the page heading",
    """    <string name="shizuku_choose_app">Choose an installed app</string>""",
    """    <!-- The heading of the Shizuku page in setup, which shows this section's contents. -->
    <string name="shizuku_setup_page_title">Shizuku configuration</string>
    <string name="shizuku_choose_app">Choose an installed app</string>""",
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4o: the Shevery red line now names IMD+, and the auto-unhide switch's second refusal.""",
    """    # r4o: the Shizuku page in setup.
    "shizuku_setup_manage",
    "shizuku_setup_skip",
    "shizuku_setup_fill_first",
    "shizuku_setup_page_title",
    # r4o: the Shevery red line now names IMD+, and the auto-unhide switch's second refusal.""",
)

# ---------------------------------------------------------------------------------------
# Three pages instead of two
# ---------------------------------------------------------------------------------------
edit(
    SETUP,
    "the page state",
    """    // Two pages, so a boolean rather than an index: `rememberSaveable` around
    // `mutableStateOf` is the pattern already proven everywhere else in this app.
    var configuring by rememberSaveable { mutableStateOf(remindersOnly) }

    if (!configuring) {
        PermissionsPage(
            modifier = modifier,
            setupState = setupState,
            grantViaShizuku = grantViaShizuku,
            onNext = { configuring = true },
        )
    } else {
        // No way back when there was no permissions step to come from — Back would otherwise
        // drop the user into a page asking them to grant what they already granted. Hoisted
        // into a typed local because `if (x) null else { { ... } }` inline reads as a bug.
        val onBack: (() -> Unit)? = if (remindersOnly) {
            null
        } else {
            { configuring = false }
        }

        ConfigurePage(
            modifier = modifier,
            onBack = onBack,
            onContinue = onContinue,
        )
    }""",
    """    // ⚠ **Three pages since r4o, so an index rather than a boolean.** Permissions, then the
    // Shizuku configuration, then the reminders. `remindersOnly` still opens straight at the
    // last one: an update has already granted the permissions and has a Shizuku configuration
    // if it wants one, and asking again would read as the app having forgotten.
    var page by rememberSaveable { mutableIntStateOf(if (remindersOnly) REMINDERS else PERMISSIONS) }

    when (page) {
        PERMISSIONS -> PermissionsPage(
            modifier = modifier,
            setupState = setupState,
            grantViaShizuku = grantViaShizuku,
            onNext = { page = SHIZUKU },
        )

        SHIZUKU -> ShizukuSetupPage(
            modifier = modifier,
            userData = userData,
            // ⚠ **Both answers move on.** Skipping is a real answer, and a page that came
            // back after it would be the app refusing to accept one.
            onSave = { forkMode, packageName, startAction, authKey ->
                onSaveShizuku(forkMode, packageName, startAction, authKey)

                page = REMINDERS
            },
            onSkip = { page = REMINDERS },
        )

        else -> {
            // No way back when there was no permissions step to come from — Back would
            // otherwise drop the user into a page asking them to grant what they already
            // granted. Hoisted into a typed local because `if (x) null else { { ... } }`
            // inline reads as a bug.
            val onBack: (() -> Unit)? = if (remindersOnly) {
                null
            } else {
                { page = SHIZUKU }
            }

            ConfigurePage(
                modifier = modifier,
                onBack = onBack,
                onContinue = onContinue,
            )
        }
    }""",
)

edit(
    SETUP,
    "the screen's new parameters",
    """    remindersOnly: Boolean = false,
    grantViaShizuku: suspend () -> ShizukuGrant,
    onContinue: () -> Unit,
) {""",
    """    remindersOnly: Boolean = false,
    /** Seeds the Shizuku page's draft, including whatever the fork detection found. */
    userData: UserData,
    grantViaShizuku: suspend () -> ShizukuGrant,
    /** Writes the four fields and then switches Manage Shizuku on, in that order. */
    onSaveShizuku: (
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) -> Unit,
    onContinue: () -> Unit,
) {""",
)

edit(
    SETUP,
    "the page constants",
    """import kotlinx.coroutines.launch""",
    """import kotlinx.coroutines.launch

/** The permissions step. */
private const val PERMISSIONS = 0

/** The Shizuku configuration, added in r4o. */
private const val SHIZUKU = 1

/** The reminders, which is where `remindersOnly` opens. */
private const val REMINDERS = 2""",
)

# ---------------------------------------------------------------------------------------
# The call site and the writes
# ---------------------------------------------------------------------------------------
edit(
    ACTIVITY,
    "the SetupScreen call",
    """                                        remindersOnly = !permissionsMissing && remindersDue,
                                        grantViaShizuku = {""",
    """                                        remindersOnly = !permissionsMissing && remindersDue,
                                        userData = uiState.userData,
                                        onSaveShizuku = viewModel::saveShizukuConfiguration,
                                        grantViaShizuku = {""",
)

edit(
    VM,
    "the write",
    """    fun markTipShown() {""",
    """    /**
     * The Shizuku page in setup: the four fields, then the master switch.
     *
     * ⚠ **In that order, and the order is the whole of it.** They are separate writes, and a
     * process death between them has to leave a filled-in configuration with Manage Shizuku
     * off — which `manageShizukuEffective` reads as "not managing", and which the user can turn
     * on in one tap — rather than a switch on over half a configuration, which every gate in
     * the app would then believe.
     */
    fun saveShizukuConfiguration(
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) {
        viewModelScope.launch {
            userDataRepository.updateShizukuForkMode(shizukuForkMode = forkMode)

            userDataRepository.updateShizukuPackageName(shizukuPackageName = packageName)

            userDataRepository.updateShizukuStartAction(shizukuStartAction = startAction)

            userDataRepository.updateShizukuAuthKey(shizukuAuthKey = authKey)

            userDataRepository.updateManageShizuku(enabled = true)
        }
    }

    fun markTipShown() {""",
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    page_path = ROOT / PAGE

    if page_path.exists():
        print(f"REFUSED: {PAGE} already exists")
        return 1

    staged[page_path] = NEW_PAGE

    # The imports the two edited files need.
    for rel, needed, anchor in (
        (SETUP, "import androidx.compose.runtime.mutableIntStateOf",
         "import androidx.compose.runtime.mutableStateOf"),
        (SETUP, "import com.android.geto.domain.model.ShizukuForkMode",
         "import com.android.geto.domain.model.ShizukuGrant"),
        (SETUP, "import com.android.geto.domain.model.UserData",
         "import com.android.geto.domain.model.ShizukuGrant"),
        (VM, "import com.android.geto.domain.model.ShizukuForkMode",
         "import com.android.geto.domain.repository.UserDataRepository"),
    ):
        text = staged[ROOT / rel]

        if anchor not in text:
            print(f"REFUSED: {rel} has no import to anchor {needed!r} against")
            return 1

        if needed not in text:
            text = text.replace(anchor, f"{needed}\n{anchor}", 1)

        if text.count(needed) != 1:
            print(f"REFUSED: {rel} carries {needed!r} {text.count(needed)} time(s)")
            return 1

        staged[ROOT / rel] = text

    # ⚠ **The old two-page state must be gone**, or the boolean and the index would both be
    # live and the screen would open on whichever the compiler reached first.
    setup = staged[ROOT / SETUP]

    if "var configuring by rememberSaveable" in setup:
        print(f"REFUSED: {SETUP} still keeps the two-page boolean")
        return 1

    # ⚠ **Position, not presence.** The three pages have to be reachable in order, and the
    # Shizuku page has to sit between the other two — the author chose where it goes.
    for needle in ("PERMISSIONS -> PermissionsPage(", "SHIZUKU -> ShizukuSetupPage("):
        if needle not in setup:
            print(f"REFUSED: {SETUP} does not draw {needle!r}")
            return 1

    permissions = setup.index("PERMISSIONS -> PermissionsPage(")
    shizuku = setup.index("SHIZUKU -> ShizukuSetupPage(")
    reminders = setup.index("ConfigurePage(")

    if not permissions < shizuku < reminders:
        print("REFUSED: the three pages are not in the author's order")
        return 1

    # ⚠ **The master switch is written last.** The whole point of the ordering.
    vm = staged[ROOT / VM]

    block = vm.split("fun saveShizukuConfiguration(", 1)[1].split("\n    }", 1)[0]

    switch = block.index("updateManageShizuku(enabled = true)")

    for field in (
        "updateShizukuForkMode(",
        "updateShizukuPackageName(",
        "updateShizukuStartAction(",
        "updateShizukuAuthKey(",
    ):
        if field not in block:
            print(f"REFUSED: the save does not write {field!r}")
            return 1

        if block.index(field) > switch:
            print(f"REFUSED: {field!r} is written after the master switch")
            return 1

    # The author's three labels, character for character.
    strings = staged[ROOT / STRINGS]

    for key, expected in (
        ("shizuku_setup_manage", "Manage shizuku configuration"),
        ("shizuku_setup_skip", "Skip"),
        ("shizuku_setup_fill_first", "Please fill all fields first"),
    ):
        value = strings.split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

        if value != expected:
            print(f"REFUSED: {key} reads {value!r}, not {expected!r}")
            return 1

    # And the page must ask the same four terms `isShizukuConfigured` does.
    page = staged[page_path]

    for term in (
        "forkMode != ShizukuForkMode.Unset",
        "packageName.isNotBlank()",
        "startAction.isNotBlank()",
        "!forkMode.requiresAuthKey || authKey.isNotBlank()",
    ):
        if term not in page:
            print(f"REFUSED: the page's 'configured' test is missing {term!r}")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: new")
    print(f"  ok        {SETUP}  :: three pages, Shizuku between the other two")
    print(f"  ok        {ACTIVITY} / {VM}  :: fields first, master switch last")
    print(f"  ok        {STRINGS}  :: the author's three labels")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s) + 1 new file")

    return 0


if __name__ == "__main__":
    sys.exit(main())
