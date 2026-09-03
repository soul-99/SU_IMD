/*
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
