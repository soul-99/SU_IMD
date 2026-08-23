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

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.feature.settings.R

/**
 * Picks what the notification posted after a launch is for.
 *
 * Two options, one of which is always chosen: there is no "off" here, because the
 * notification is the only way back from a profile that has hidden developer options, and an
 * app that could switch them off with no route back would be a trap.
 *
 * Save rather than apply-on-tap, unlike the theme dialog, because the two modes behave
 * differently enough that changing one by a mis-tap and finding out later — when the
 * notifications look wrong — is worth one extra press to avoid.
 */
@Composable
internal fun NotificationFunctionDialog(
    modifier: Modifier = Modifier,
    selected: NotificationFunction,
    onDismissRequest: () -> Unit,
    onUpdateNotificationFunction: (NotificationFunction) -> Unit,
) {
    var choice by remember(selected) { mutableStateOf(selected) }

    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.notification_function),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(4.dp))

            // Recommended first. A list that opens with the option being steered away from
            // is a list that gets picked from the top by anyone not reading closely.
            Column(modifier = Modifier.selectableGroup()) {
                NotificationFunctionOption(
                    title = stringResource(R.string.notification_function_revert_option),
                    summary = stringResource(R.string.notification_function_revert_summary),
                    detail = stringResource(R.string.notification_function_revert_detail),
                    selected = choice == NotificationFunction.RevertToDefault,
                    onSelect = { choice = NotificationFunction.RevertToDefault },
                )

                NotificationFunctionOption(
                    title = stringResource(R.string.notification_function_memory_option),
                    summary = stringResource(R.string.notification_function_memory_summary),
                    detail = stringResource(R.string.notification_function_memory_detail),
                    selected = choice == NotificationFunction.Memory,
                    onSelect = { choice = NotificationFunction.Memory },
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    onClick = {
                        onUpdateNotificationFunction(choice)

                        onDismissRequest()
                    },
                ) {
                    Text(text = stringResource(R.string.save))
                }
            }
        }
    }
}

/**
 * The whole row is the target, not just the radio button.
 *
 * [Role.RadioButton] on the row and a null handler on the button itself is what stops a
 * screen reader announcing the same choice twice, and what makes a tap anywhere on the
 * two-line description select the option.
 */
@Composable
private fun NotificationFunctionOption(
    modifier: Modifier = Modifier,
    title: String,
    summary: String,
    detail: String,
    selected: Boolean,
    onSelect: () -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onSelect)
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.Top,
    ) {
        RadioButton(selected = selected, onClick = null)

        Column(modifier = Modifier.padding(start = 12.dp)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(4.dp))

            Text(text = summary, style = MaterialTheme.typography.bodyMedium)

            Spacer(modifier = Modifier.height(2.dp))

            Text(text = detail, style = MaterialTheme.typography.bodySmall)
        }
    }
}
