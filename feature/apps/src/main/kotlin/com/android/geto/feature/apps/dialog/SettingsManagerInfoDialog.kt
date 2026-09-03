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
package com.android.geto.feature.apps.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.apps.R

/**
 * What the services manager is, and what it is not.
 *
 * Both points here answer a misreading rather than describing a feature, which is why they
 * are worth a dialog at all. The first: the manager shows live state and toggles it, and
 * decides nothing about what launching an app through IMD will hide - people reasonably
 * assume the switches they can see are the configuration. The second: Android's developer
 * options toggle is a flag, not an undo, so switching it off leaves animation scales, a mock
 * location app and everything else exactly as they were set.
 *
 * Shown automatically the first time the manager is opened, and afterwards only on request,
 * from the information button beside the title.
 */
@Composable
internal fun SettingsManagerInfoDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .verticalScroll(rememberScrollState())
                .padding(10.dp),
        ) {
            InfoPoint(
                number = 1,
                // Two bolded phrases now: the manager's own name and "live status". Both are
                // resources rather than literals so that each locale bolds its own words —
                // a phrase passed here must occur verbatim in that locale's sentence or the
                // emphasis silently matches nothing, which is the Russian-case bug this
                // project already paid for once.
                text = emphasised(
                    text = stringResource(R.string.settings_manager_info_live),
                    names = listOf(
                        stringResource(R.string.settings_manager_title),
                        stringResource(R.string.settings_manager_info_name_live),
                    ),
                ),
                extra = emphasised(
                    text = stringResource(R.string.settings_manager_info_live_extra),
                    names = listOf(stringResource(R.string.settings_manager_info_name_defaults)),
                ),
            )

            InfoPoint(
                number = 2,
                text = AnnotatedString(
                    stringResource(R.string.settings_manager_info_developer),
                ),
                extra = emphasised(
                    text = stringResource(R.string.settings_manager_info_developer_extra),
                    names = listOf(stringResource(R.string.settings_manager_info_name_reset)),
                ),
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
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
 * One numbered point and the paragraph that follows it.
 *
 * The second paragraph is indented to the first's text rather than to its number, so the
 * two read as one point with a consequence rather than as two separate items - which is
 * what a reader would otherwise take a second unnumbered line to be.
 */
@Composable
private fun InfoPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: AnnotatedString,
    extra: AnnotatedString,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 8.dp),
    ) {
        Text(
            modifier = Modifier.width(26.dp),
            text = "$number.",
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.primary,
        )

        Spacer(modifier = Modifier.width(4.dp))

        Column {
            Text(text = text, style = MaterialTheme.typography.bodyMedium)

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = extra,
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
