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
package com.android.geto.feature.settings.help

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedCard
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.settings.R

/**
 * What someone has to set up themselves, and where.
 *
 * Lives here rather than in the onboarding package because it is shown from two places that
 * cannot see each other's code: the second page of first-run setup, in the app module, and a
 * Help button in Settings. One copy, so the instructions cannot drift apart — which for a
 * page whose entire content is navigation paths is exactly what would happen.
 */
@Composable
fun SetupHelpContent(modifier: Modifier = Modifier) {
    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        Text(
            text = stringResource(R.string.help_title),
            style = MaterialTheme.typography.headlineSmall,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(12.dp))

        Text(
            text = stringResource(R.string.help_intro),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )

        Spacer(modifier = Modifier.height(24.dp))

        // Cards, as the setup pages have always used — only the status circle and the
        // "Step N" label are gone. Those belonged to the permissions page, where each item
        // really is either done or not; nothing here can be checked, and a permanently
        // unticked circle beside every item read as four things having gone wrong.
        HelpSection(
            number = 1,
            title = stringResource(R.string.help_hide_title),
            body = stringResource(R.string.help_hide_body),
        )

        HelpSection(
            number = 2,
            title = stringResource(R.string.help_revert_title),
            body = stringResource(R.string.help_revert_body),
        )

        HelpSection(
            number = 3,
            title = stringResource(R.string.help_accessibility_title),
            body = stringResource(R.string.help_accessibility_body),
        )

        HelpSection(
            number = 4,
            title = stringResource(R.string.help_shizuku_title),
            body = stringResource(R.string.help_shizuku_body),
        )

        Spacer(modifier = Modifier.height(12.dp))

        OutlinedCard(modifier = Modifier.fillMaxWidth()) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text(
                    text = stringResource(R.string.help_general_title),
                    style = MaterialTheme.typography.titleMedium,
                )

                Spacer(modifier = Modifier.height(12.dp))

                Text(
                    text = stringResource(R.string.help_general_shortcuts),
                    style = MaterialTheme.typography.bodySmall,
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = emphasised(
                        text = stringResource(R.string.help_general_manager),
                        names = listOf(stringResource(R.string.help_name_manager)),
                    ),
                    style = MaterialTheme.typography.bodySmall,
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = emphasised(
                        text = stringResource(R.string.help_general_access),
                        names = listOf(
                            stringResource(R.string.help_name_manager),
                            stringResource(R.string.help_name_revert),
                        ),
                    ),
                    style = MaterialTheme.typography.bodySmall,
                )

                // Indented, so the three routes read as belonging to the sentence above
                // rather than as three more points in the same list.
                Text(
                    modifier = Modifier.padding(start = 16.dp, top = 2.dp),
                    text = stringResource(R.string.help_general_access_items),
                    style = MaterialTheme.typography.bodySmall,
                )
            }
        }
    }
}

/**
 * The same content as a dialog, for the Help button in Settings.
 *
 * Height-capped and scrollable: on a short screen the four sections do not fit, and a dialog
 * that runs off the bottom takes its own close button with it.
 */
@Composable
fun SetupHelpDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            SetupHelpContent(
                modifier = Modifier
                    .heightIn(max = 520.dp)
                    .verticalScroll(rememberScrollState()),
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.help_close))
                }
            }
        }
    }
}

@Composable
private fun HelpSection(
    modifier: Modifier = Modifier,
    number: Int,
    title: String,
    body: String,
) {
    OutlinedCard(modifier = modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = stringResource(R.string.help_numbered_title, number, title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(text = body, style = MaterialTheme.typography.bodySmall)
        }
    }

    Spacer(modifier = Modifier.height(12.dp))
}
