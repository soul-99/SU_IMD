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

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.provider.Settings
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Image
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.ContentCopy
import androidx.compose.material.icons.filled.RadioButtonUnchecked
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.designsystem.component.emphasised
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.ShizukuGrant
import com.android.geto.feature.settings.AccessibilityStep
import com.android.geto.feature.settings.CustomiseUiStep
import com.android.geto.feature.settings.ManagerRowsStep
import com.android.geto.feature.settings.OverlayStep
import com.android.geto.feature.settings.RevertDefaultsStep
import com.android.geto.feature.settings.SettingsToHideStep
import kotlinx.coroutines.launch

/** The permissions step. */
/**
 * How wide a setup page is allowed to get.
 *
 * ⚠ **Must equal `DIALOG_MAX_WIDTH` in `:design-system`'s Dialog.kt**, which is private to that
 * file. Repeated rather than published because making a layout number part of that module's API
 * for one caller costs more than this comment does; if the two ever disagree the setup flow is
 * merely a different width from the dialogs, not broken.
 */
private val SETUP_MAX_WIDTH = 580.dp

private const val PERMISSIONS = 0

/** The Shizuku configuration, added in r4o. */
private const val SHIZUKU = 1

/** The accessibility services IMD may manage — r4r. */
private const val ACCESSIBILITY = 2

/** The apps whose Display over other apps IMD may manage — r4r. */
private const val OVERLAY = 3

/** Which settings a launch hides — r4r. */
private const val SETTINGS_TO_HIDE = 4

/** What a revert puts back — r4u. */
private const val REVERT_DEFAULTS = 5

/** Which rows the settings manager draws — r19b. */
private const val MANAGER_ROWS = 6

/** How the app looks — r19b. */
private const val CUSTOMISE_UI = 7

/**
 * The reminders, which is where `remindersOnly` opens.
 *
 * ⚠ **The number moves whenever a page is added or removed**, and it has to. `nextAfter` walks
 * forward one page at a time until it reaches this, so the constants have to stay contiguous — a
 * gap is a number the walk stops on with nothing to draw. It was 6, then 5 when r4t took auto
 * unhide out, 6 again once r4u put Revert to default in, and 8 since r19b added the two pages
 * above.
 */
private const val REMINDERS = 8

/**
 * The next page after [from], stepping over the ones this install has no use for.
 *
 * ⚠ **One function rather than a decision at each hop.** There are five hops through four
 * optional pages, and a chain of `if (a) ... else if (b) ...` written out at each of them is how
 * a page ends up unreachable — or worse, reachable from one direction only.
 *
 * ⚠ **[configuring] gates all five configuration pages, Shizuku included**, on the author's
 * instruction. It is `!upgradedToV3`: an install that existed before v3 has answered these
 * questions already, and asking again would read as the app having forgotten.
 */
private fun nextAfter(from: Int, configuring: Boolean): Int {
    var page = from + 1

    while (page < REMINDERS) {
        // ⚠ **Every configuration page now has the same rule**, since r4s took the Display over
        // other apps pre-check out — it hid the step on devices where it should have appeared,
        // and the step now shows itself and asks the list directly. The loop stays because the
        // flow is still five hops and a page-by-page decision at each of them is how one becomes
        // unreachable.
        if (configuring) return page

        page += 1
    }

    return REMINDERS
}

/**
 * The page before [from], stepping back over the ones this install has no use for.
 *
 * ⚠ **[SHIZUKU] is the floor, not [PERMISSIONS]** — the author asked for Back *"after initial
 * shizuku and notification permission screen"*. Permissions is a gate rather than a step: it
 * cannot be passed until both are granted, so walking back into it could only ever be a dead
 * end, and the Shizuku page behind it is the last thing there was a choice to change.
 *
 * The mirror of [nextAfter], written the same way for the same reason its comment gives: a
 * decision written out at each of five hops is how a page becomes reachable from one direction
 * only.
 */
private fun previousBefore(from: Int, configuring: Boolean): Int {
    var page = from - 1

    while (page > SHIZUKU) {
        if (configuring) return page

        page -= 1
    }

    return SHIZUKU
}

/**
 * First-run screen, in two pages.
 *
 * The first cannot be passed until both permissions are in place, because every single
 * thing this app does is a secure-settings write plus a notification to undo it — without
 * them the app looks like it works and quietly does nothing.
 *
 * The second is informational. Shizuku restart and the accessibility service list cannot
 * be configured from here — the values have to be read out of the Shizuku app, and the
 * service list is a personal choice — so this says where to go rather than pretending to
 * be a wizard.
 */
@Composable
fun SetupScreen(
    modifier: Modifier = Modifier,
    setupState: SetupState,
    /**
     * Opens straight at the reminders page, skipping the permissions step.
     *
     * Used after an update, where the permissions are already granted and the only thing
     * worth showing is what has changed since the user last read these.
     */
    remindersOnly: Boolean = false,
    /**
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
    onRefreshInstalledApps: (Boolean) -> Unit,
    grantViaShizuku: suspend () -> ShizukuGrant,
    /** Writes the four fields and then switches Manage Shizuku on, in that order. */
    onSaveShizuku: (
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) -> Unit,
    onContinue: () -> Unit,
) {
    // ⚠ **Three pages since r4o, so an index rather than a boolean.** Permissions, then the
    // Shizuku configuration, then the reminders. `remindersOnly` still opens straight at the
    // last one: an update has already granted the permissions and has a Shizuku configuration
    // if it wants one, and asking again would read as the app having forgotten.
    var page by rememberSaveable { mutableIntStateOf(if (remindersOnly) REMINDERS else PERMISSIONS) }

    // ⚠ **The one question that decides whether any of the configuration is shown**, and the
    // only field that can answer it: see nextAfter. Not `remindersOnly`, which means something
    // else — an upgrade missing a permission still walks through Permissions and still must not
    // walk through the configuration.
    val configuring = !userData.upgradedToV3

    val advance = { from: Int ->
        page = nextAfter(from = from, configuring = configuring)
    }

    // ⚠ **Not `page -= 1`.** The pages this walks over are the same optional ones `advance`
    // steps across, and the two have to agree or Back lands somewhere Next never visited.
    val retreat = { from: Int ->
        page = previousBefore(from = from, configuring = configuring)
    }

    // ⚠ **One cap for every page of the flow**, rather than three more edits in the pages that
    // build their own roots. The four steps drawn through DialogContainer already carry an
    // identical cap of their own; an identical constraint inside an identical constraint is a
    // no-op, and this way a page added later is capped without anyone remembering to do it.
    //
    // On a phone nothing moves: 580.dp is wider than the display, so the constraint never binds.
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.TopCenter,
    ) {
        Box(modifier = Modifier.widthIn(max = SETUP_MAX_WIDTH)) {
            when (page) {
                PERMISSIONS -> PermissionsPage(
                    modifier = modifier,
                    setupState = setupState,
                    grantViaShizuku = grantViaShizuku,
                    onNext = { advance(PERMISSIONS) },
                )

                SHIZUKU -> ShizukuSetupPage(
                    modifier = modifier,
                    userData = userData,
                    installedApps = installedApps,
                    installedAppsRevision = installedAppsRevision,
                    onRefreshInstalledApps = onRefreshInstalledApps,
                    // ⚠ **Both answers move on.** Skipping is a real answer, and a page that came
                    // back after it would be the app refusing to accept one.
                    onSave = { forkMode, packageName, startAction, authKey ->
                        onSaveShizuku(forkMode, packageName, startAction, authKey)

                        advance(SHIZUKU)
                    },
                    onSkip = { advance(SHIZUKU) },
                )

                ACCESSIBILITY -> AccessibilityStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_accessibility),
                    onBack = { retreat(ACCESSIBILITY) },
                    onSkip = { advance(ACCESSIBILITY) },
                    onNext = { advance(ACCESSIBILITY) },
                )

                OVERLAY -> OverlayStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_overlay),
                    onBack = { retreat(OVERLAY) },
                    onSkip = { advance(OVERLAY) },
                    onNext = { advance(OVERLAY) },
                )

                SETTINGS_TO_HIDE -> SettingsToHideStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_settings_to_hide),
                    onBack = { retreat(SETTINGS_TO_HIDE) },
                    onSkip = { advance(SETTINGS_TO_HIDE) },
                    onNext = { advance(SETTINGS_TO_HIDE) },
                )

                // No stepTitle: this page's own heading changes with the unhiding framework.
                REVERT_DEFAULTS -> RevertDefaultsStep(
                    modifier = modifier,
                    onBack = { retreat(REVERT_DEFAULTS) },
                    onSkip = { advance(REVERT_DEFAULTS) },
                    onNext = { advance(REVERT_DEFAULTS) },
                )

                MANAGER_ROWS -> ManagerRowsStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_manager_rows),
                    onBack = { retreat(MANAGER_ROWS) },
                    onSkip = { advance(MANAGER_ROWS) },
                    onNext = { advance(MANAGER_ROWS) },
                )

                CUSTOMISE_UI -> CustomiseUiStep(
                    modifier = modifier,
                    stepTitle = stringResource(R.string.setup_step_customise_ui),
                    onBack = { retreat(CUSTOMISE_UI) },
                    onSkip = { advance(CUSTOMISE_UI) },
                    onNext = { advance(CUSTOMISE_UI) },
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

                    // ⚠ **Drawn directly, not wrapped.** It was inside a `verticalScroll` Column
                    // until r4s, and its body — a `weight(1f)` child — was therefore measured against an
                    // unbounded height and given none of it. The page needs a bounded parent, which is
                    // what this branch is.
                    SetupCompletePage(
                        modifier = modifier,
                        onBack = onBack,
                        onContinue = onContinue,
                    )
                }
            }
        }
    }
}

@Composable
private fun PermissionsPage(
    modifier: Modifier = Modifier,
    setupState: SetupState,
    grantViaShizuku: suspend () -> ShizukuGrant,
    onNext: () -> Unit,
) {
    val context = LocalContext.current

    val scope = rememberCoroutineScope()

    var asking by remember { mutableStateOf(false) }

    var grant by remember { mutableStateOf<ShizukuGrant?>(null) }

    // Shizuku answers on its own schedule — the user has to tap Allow in another app —
    // so the screen re-reads the real permission state once the call returns rather than
    // trusting the result alone.
    LaunchedEffect(grant) {
        if (grant == ShizukuGrant.Granted) setupState.refresh()
    }

    val adbCommand = stringResource(R.string.setup_adb_command, context.packageName)

    val notificationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission(),
    ) {
        setupState.refresh()
    }

    Column(
        modifier = modifier
            .fillMaxSize()
            // MainActivity calls enableEdgeToEdge and this screen has no Scaffold of its
            // own, so without this the icon sits under the status bar and Continue sits
            // under the gesture bar.
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        // The launcher icon is an <adaptive-icon> XML on API 26+, and painterResource
        // only understands <vector> and raster assets — handing it the mipmap crashes on
        // the very first screen of a fresh install. The foreground layer is a plain
        // vector, and its single green reads on both light and dark backgrounds.
        Image(
            modifier = Modifier.size(84.dp),
            painter = painterResource(R.drawable.ic_launcher_foreground),
            contentDescription = null,
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = stringResource(R.string.app_name),
            style = MaterialTheme.typography.headlineSmall,
            textAlign = TextAlign.Center,
        )

        Text(
            text = stringResource(R.string.app_full_form),
            style = MaterialTheme.typography.titleMedium,
            color = MaterialTheme.colorScheme.primary,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(20.dp))

        HowItWorksFlow(modifier = Modifier.fillMaxWidth())

        Spacer(modifier = Modifier.height(24.dp))

        SetupStep(
            stepNumber = 1,
            title = stringResource(R.string.setup_secure_settings_title),
            done = setupState.hasSecureSettings,
        ) {
            Text(
                text = stringResource(R.string.setup_secure_settings_why),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(12.dp))

            CommandBlock(command = adbCommand)

            // Two ways to the same grant, side by side, because which one is easier
            // depends entirely on whether there is a computer within reach.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedButton(
                    modifier = Modifier.weight(1f),
                    enabled = !setupState.hasSecureSettings,
                    onClick = { context.copyToClipboard(adbCommand) },
                ) {
                    Icon(
                        modifier = Modifier.size(16.dp),
                        imageVector = Icons.Default.ContentCopy,
                        contentDescription = null,
                    )

                    Spacer(modifier = Modifier.width(6.dp))

                    Text(text = stringResource(R.string.setup_copy_command))
                }

                Button(
                    modifier = Modifier.weight(1f),
                    enabled = !asking && !setupState.hasSecureSettings,
                    onClick = {
                        scope.launch {
                            asking = true

                            grant = grantViaShizuku()

                            asking = false
                        }
                    },
                ) {
                    Text(text = stringResource(R.string.setup_use_shizuku))
                }
            }

            TextButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = setupState::refresh,
            ) {
                Text(text = stringResource(R.string.setup_check_again))
            }

            val outcome = when {
                asking -> R.string.setup_shizuku_working
                grant == ShizukuGrant.Granted -> R.string.setup_shizuku_granted
                grant == ShizukuGrant.NotRunning -> R.string.setup_shizuku_not_running
                grant == ShizukuGrant.PermissionDenied -> R.string.setup_shizuku_denied
                grant == ShizukuGrant.Failed -> R.string.setup_shizuku_failed
                else -> null
            }

            if (outcome != null) {
                Text(
                    text = stringResource(outcome),
                    style = MaterialTheme.typography.bodySmall,
                    color = if (grant == ShizukuGrant.Granted || asking) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                )

                Spacer(modifier = Modifier.height(8.dp))
            }

            // Shizuku first, and marked as the recommendation. Both routes end at the same
            // grant, but only one of them needs a computer — and the button that does it is
            // right above this text, which the ADB command is not.
            Text(
                text = emphasised(
                    text = stringResource(R.string.setup_secure_settings_shizuku),
                    names = listOf(stringResource(R.string.setup_use_shizuku)),
                ),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = emphasised(
                    text = stringResource(R.string.setup_shizuku_once),
                    names = listOf(stringResource(R.string.setup_name_display_over_other_apps)),
                ),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = stringResource(R.string.setup_shizuku_once_extra),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.setup_secure_settings_adb),
                style = MaterialTheme.typography.bodySmall,
            )
        }

        Spacer(modifier = Modifier.height(12.dp))

        SetupStep(
            stepNumber = 2,
            title = stringResource(R.string.setup_notifications_title),
            done = setupState.hasNotifications,
        ) {
            Text(
                text = stringResource(R.string.setup_notifications_why),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
            ) {
                OutlinedButton(
                    modifier = Modifier.weight(1f),
                    enabled = !setupState.hasNotifications,
                    onClick = {
                        // The runtime permission only exists on Tiramisu and later; before
                        // that the only way notifications are off is a system-settings
                        // toggle, so send the user straight there.
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                            notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                        } else {
                            context.openNotificationSettings()
                        }
                    },
                ) {
                    Text(text = stringResource(R.string.setup_allow_notifications))
                }

                TextButton(
                    modifier = Modifier.weight(1f),
                    onClick = { context.openNotificationSettings() },
                ) {
                    Text(text = stringResource(R.string.setup_open_settings))
                }
            }

            // A second refusal makes the system dialog a no-op, and nothing on screen would
            // explain why the button stopped doing anything.
            Text(
                text = stringResource(R.string.setup_notifications_denied_hint),
                style = MaterialTheme.typography.bodySmall,
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            modifier = Modifier.fillMaxWidth(),
            enabled = setupState.isComplete,
            onClick = onNext,
        ) {
            Text(text = stringResource(R.string.setup_next))
        }

        if (!setupState.isComplete) {
            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = stringResource(R.string.setup_blocked),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.error,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/**
 * What the app does to the device, drawn rather than described.
 *
 * The three steps were one sentence with chevrons in it, which reads as a list of features
 * rather than as a sequence with a beginning and an end. Drawn as a flow, the shape carries
 * the argument the sentence was making: the settings come back, and the middle step is the
 * user's, not the app's.
 *
 * The note under the first step is the point of the whole block. Nothing here works around an
 * app's checks - the settings really are off while that app runs, which is why it is satisfied
 * and why they have to be put back afterwards.
 */
@Composable
private fun HowItWorksFlow(modifier: Modifier = Modifier) {
    Column(modifier = modifier) {
        Text(
            text = stringResource(R.string.setup_how_title),
            style = MaterialTheme.typography.titleSmall,
        )

        Spacer(modifier = Modifier.height(10.dp))

        // Laid out across the width rather than down the page: the three steps sit in one row
        // with the arrows between them, which keeps the block short on a screen that already
        // scrolls. The steps carry the same argument the README's flow does.
        Row(
            modifier = Modifier.fillMaxWidth(),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            FlowStep(
                modifier = Modifier.weight(1f),
                number = 1,
                text = stringResource(R.string.setup_how_off),
            )

            FlowConnector()

            FlowStep(
                modifier = Modifier.weight(1f),
                number = 2,
                text = stringResource(R.string.setup_how_use),
            )

            // The only labelled edge, because it is the only transition the user has to cause.
            FlowConnector(label = stringResource(R.string.setup_how_revert))

            FlowStep(
                modifier = Modifier.weight(1f),
                number = 3,
                text = stringResource(R.string.setup_how_on),
            )
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Once tucked under the first box; on its own line under the whole row it stays the
        // point of the block - the settings really are off, nothing is being worked around.
        Text(
            text = stringResource(R.string.setup_how_off_note),
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

/** One box in the flow: the step number over its line of text, sized to share the row evenly. */
@Composable
private fun FlowStep(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
) {
    OutlinedCard(modifier = modifier) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 8.dp, vertical = 10.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
        ) {
            Text(
                text = stringResource(R.string.setup_how_number, number),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = text,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/**
 * The arrowhead between two steps, with an optional word beneath it.
 *
 * A forward arrow now the steps run left to right, and the auto-mirrored one, so the flow still
 * reads start-to-end under a right-to-left locale. Drawn from an icon rather than a character so
 * it inherits the theme's colours at the same weight as everything else on the page.
 */
@Composable
private fun FlowConnector(
    modifier: Modifier = Modifier,
    label: String? = null,
) {
    Column(
        modifier = modifier.padding(horizontal = 4.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Icon(
            modifier = Modifier.size(16.dp),
            imageVector = GetoIcons.ArrowForward,
            contentDescription = null,
            tint = MaterialTheme.colorScheme.outline,
        )

        if (label != null) {
            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
                textAlign = TextAlign.Center,
            )
        }
    }
}

@Composable
private fun SetupStep(
    modifier: Modifier = Modifier,
    stepNumber: Int,
    title: String,
    done: Boolean,
    content: @Composable () -> Unit,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = if (done) {
                        Icons.Default.CheckCircle
                    } else {
                        Icons.Default.RadioButtonUnchecked
                    },
                    contentDescription = null,
                    tint = if (done) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    },
                )

                Spacer(modifier = Modifier.width(10.dp))

                Column(modifier = Modifier.weight(1f)) {
                    Text(
                        text = stringResource(R.string.setup_step, stepNumber),
                        style = MaterialTheme.typography.labelSmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )

                    Text(
                        text = title,
                        style = MaterialTheme.typography.titleMedium,
                    )
                }

                Text(
                    text = if (done) {
                        stringResource(R.string.setup_granted)
                    } else {
                        stringResource(R.string.setup_not_granted)
                    },
                    style = MaterialTheme.typography.labelMedium,
                    color = if (done) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        MaterialTheme.colorScheme.error
                    },
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            content()
        }
    }
}

@Composable
private fun CommandBlock(
    modifier: Modifier = Modifier,
    command: String,
) {
    Surface(
        modifier = modifier.fillMaxWidth(),
        shape = RoundedCornerShape(8.dp),
        color = MaterialTheme.colorScheme.surfaceVariant,
    ) {
        // The command is longer than any phone is wide, and wrapping a shell command makes
        // it harder to read than scrolling it.
        Text(
            modifier = Modifier
                .padding(12.dp)
                .horizontalScroll(rememberScrollState()),
            text = command,
            style = MaterialTheme.typography.bodySmall,
            fontFamily = FontFamily.Monospace,
            maxLines = 1,
        )
    }
}

private fun Context.copyToClipboard(text: String) {
    val clipboard = getSystemService(Context.CLIPBOARD_SERVICE) as? ClipboardManager ?: return

    clipboard.setPrimaryClip(ClipData.newPlainText("adb command", text))

    // Android 13 and later show their own copy confirmation, so a second one would be
    // duplicated noise.
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) {
        Toast.makeText(this, R.string.setup_copied, Toast.LENGTH_SHORT).show()
    }
}

private fun Context.openNotificationSettings() {
    val intent = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
        Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
            .putExtra(Settings.EXTRA_APP_PACKAGE, packageName)
    } else {
        Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS)
            .setData(Uri.fromParts("package", packageName, null))
    }

    try {
        startActivity(intent)
    } catch (_: ActivityNotFoundException) {
        Toast.makeText(this, R.string.setup_open_settings_failed, Toast.LENGTH_SHORT).show()
    }
}
