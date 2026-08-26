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
import androidx.compose.material3.VerticalDivider
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
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
import com.android.geto.domain.model.ShizukuGrant
import com.android.geto.feature.settings.help.SetupHelpContent
import kotlinx.coroutines.launch

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
    grantViaShizuku: suspend () -> ShizukuGrant,
    onContinue: () -> Unit,
) {
    // Two pages, so a boolean rather than an index: `rememberSaveable` around
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

        Spacer(modifier = Modifier.height(16.dp))

        // Left aligned, unlike the name and full form above it. It is a numbered list now,
        // and a centred list has no left edge for the eye to come back to.
        Text(
            modifier = Modifier.fillMaxWidth(),
            text = stringResource(R.string.setup_purpose),
            style = MaterialTheme.typography.bodyMedium,
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
 * Page two. Nothing here is enforced — both items are optional in the sense that the app
 * runs without them — but both are silent when unconfigured, which is exactly the kind of
 * thing that gets diagnosed as "the app is broken" months later.
 */
@Composable
private fun ConfigurePage(
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)?,
    onContinue: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Spacer(modifier = Modifier.height(8.dp))

        // The page's whole body lives in feature/settings, because Settings shows the same
        // thing behind a Help button. Two copies of a page that is nothing but navigation
        // paths would be out of step by the next release that moves a menu.
        SetupHelpContent()

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            modifier = Modifier.fillMaxWidth(),
            onClick = onContinue,
        ) {
            Text(text = stringResource(R.string.setup_finish))
        }

        if (onBack != null) {
            Spacer(modifier = Modifier.height(4.dp))

            TextButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = onBack,
            ) {
                Text(text = stringResource(R.string.setup_back))
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
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

        FlowStep(
            number = 1,
            text = stringResource(R.string.setup_how_off),
            note = stringResource(R.string.setup_how_off_note),
        )

        FlowConnector()

        FlowStep(
            number = 2,
            text = stringResource(R.string.setup_how_use),
        )

        // The only labelled edge, because it is the only transition the user has to cause.
        FlowConnector(label = stringResource(R.string.setup_how_revert))

        FlowStep(
            number = 3,
            text = stringResource(R.string.setup_how_on),
        )
    }
}

/** One box in the flow. */
@Composable
private fun FlowStep(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    note: String? = null,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Row(
            modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
            verticalAlignment = Alignment.Top,
        ) {
            Text(
                text = stringResource(R.string.setup_how_number, number),
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(modifier = Modifier.width(10.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(text = text, style = MaterialTheme.typography.bodyMedium)

                if (note != null) {
                    Spacer(modifier = Modifier.height(2.dp))

                    Text(
                        text = note,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
        }
    }
}

/**
 * The line and arrowhead between two steps, with an optional word on the edge.
 *
 * Drawn from a divider and an icon rather than a character, so it inherits the theme's colours
 * and stays the same weight as everything else on the page in every font and locale.
 */
@Composable
private fun FlowConnector(
    modifier: Modifier = Modifier,
    label: String? = null,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(start = 20.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            VerticalDivider(
                modifier = Modifier.height(14.dp),
                color = MaterialTheme.colorScheme.outlineVariant,
            )

            Icon(
                modifier = Modifier.size(14.dp),
                imageVector = GetoIcons.ArrowDownward,
                contentDescription = null,
                tint = MaterialTheme.colorScheme.outline,
            )
        }

        if (label != null) {
            Spacer(modifier = Modifier.width(8.dp))

            Text(
                text = label,
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.primary,
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
        Toast.makeText(this, R.string.setup_open_settings_failed, Toast.LENGTH_LONG).show()
    }
}
