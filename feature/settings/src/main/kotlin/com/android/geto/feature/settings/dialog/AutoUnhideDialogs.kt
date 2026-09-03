/*
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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R

/**
 * "How auto unhide works", as the same numbered flow the IMD+ page uses.
 *
 * Seven steps rather than nine, and the shape of them is the point: the first three are what
 * the user already does, the fourth is the only thing being asked of them, and the last three
 * are what IMD does about it. A feature that puts settings back on its own has to be readable
 * as a sequence, or it reads as the device changing by itself.
 */
@Composable
internal fun AutoUnhideHowItWorksDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    val steps = listOf(
        stringResource(R.string.auto_unhide_flow_1),
        stringResource(R.string.auto_unhide_flow_2),
        stringResource(R.string.auto_unhide_flow_3),
        stringResource(R.string.auto_unhide_flow_4),
        stringResource(R.string.auto_unhide_flow_5),
        stringResource(R.string.auto_unhide_flow_6),
        stringResource(R.string.auto_unhide_flow_7),
    )

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.auto_unhide_how_it_works),
        onDismissRequest = onDismissRequest,
    ) {
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.auto_unhide_flow_intro),
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(modifier = Modifier.height(12.dp))

        steps.forEachIndexed { index, step ->
            FlowStep(number = index + 1, text = step, last = index == steps.lastIndex)
        }

        Spacer(modifier = Modifier.height(12.dp))
    }
}

/**
 * How long one of the two backups waits.
 *
 * A short list of whole minutes rather than a free number field. The useful answers here span
 * one order of magnitude and the difference between 12 and 13 minutes is not a difference
 * anybody has an opinion about — a list can be answered with one tap, where a field has to be
 * typed into, validated, and defended against a zero.
 */
@Composable
internal fun AutoUnhideMinutesDialog(
    modifier: Modifier = Modifier,
    title: String,
    selected: Int,
    onSelect: (Int) -> Unit,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(vertical = 20.dp)) {
            Text(
                modifier = Modifier.padding(horizontal = 20.dp),
                text = title,
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            AUTO_UNHIDE_MINUTE_OPTIONS.forEach { minutes ->
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            onSelect(minutes)

                            onDismissRequest()
                        }
                        .padding(horizontal = 20.dp, vertical = 10.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    RadioButton(selected = minutes == selected, onClick = null)

                    Spacer(modifier = Modifier.width(12.dp))

                    Text(
                        text = stringResource(R.string.auto_unhide_minutes, minutes),
                        style = MaterialTheme.typography.bodyLarge,
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * The `adb` route to the dump permission, for anyone who does not use Shizuku.
 *
 * Shown rather than run, obviously — this is a command for a computer. The copy button is the
 * whole point of the dialog: the command is long, exact, and contains the app's package name,
 * and a user retyping it from a phone screen is a user who gets one character wrong.
 */
@Composable
internal fun AutoUnhideAdbCommandDialog(
    modifier: Modifier = Modifier,
    command: String,
    onDismissRequest: () -> Unit,
) {
    val clipboard = LocalClipboardManager.current

    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_unhide_adb_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.auto_unhide_adb_body),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Monospace on its own ground, so a command reads as a command. Wrapped rather
            // than scrolled: unlike the About screen's shell block there is no alignment to
            // protect here, and a command the user cannot see all of is one they cannot check.
            Surface(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(8.dp),
                color = MaterialTheme.colorScheme.surfaceContainerHighest,
            ) {
                Text(
                    modifier = Modifier.padding(12.dp),
                    text = command,
                    style = MaterialTheme.typography.bodySmall,
                    fontFamily = FontFamily.Monospace,
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    onClick = { clipboard.setText(AnnotatedString(command)) },
                ) {
                    Text(text = stringResource(R.string.auto_unhide_adb_copy))
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * What the switch says when it will not move.
 *
 * The same treatment IMD+ gives its blocked switch: the tap falls through the disabled control
 * to the row underneath, which raises this, so a control that cannot be used still explains
 * itself instead of being inert.
 */
@Composable
internal fun AutoUnhideBlockedDialog(
    modifier: Modifier = Modifier,
    /**
     * Which refusal this is.
     *
     * ⚠ **Passed in rather than decided here**, because the caller is the only one holding the
     * requirements — and because the two sentences are answers to two different questions: a
     * permission granted outside the app, or a trigger the user has not ticked yet.
     */
    permissionsMissing: Boolean = false,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = if (permissionsMissing) {
                    stringResource(R.string.auto_unhide_permissions_blocked)
                } else {
                    stringResource(R.string.auto_unhide_blocked)
                },
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * What the last "used for" checkbox says when it refuses to be unticked.
 *
 * Both boxes clear would leave the feature switched on and unable to act on anything, which is
 * a worse state than off: the switch would still read on and the user would be waiting for
 * settings that were never coming back.
 */
@Composable
internal fun AutoUnhideUsedForBlockedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_unhide_used_for_blocked),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * The intervals offered, in minutes.
 *
 * One and two are there for anyone testing the feature rather than living with it; the useful
 * everyday answers are the middle three. Sixty is the ceiling because a session still hidden
 * an hour after the phone was put down is one the user has plainly forgotten, which is exactly
 * the case these backups exist for.
 */
internal val AUTO_UNHIDE_MINUTE_OPTIONS = listOf(1, 2, 5, 10, 15, 30, 60)
