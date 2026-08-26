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

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import com.android.geto.common.SettingsChangeLog
import com.android.geto.feature.settings.R
import com.android.geto.common.R as commonR

/**
 * Everything the settings observer has seen, newest first.
 *
 * The observer's notification only ever showed the most recent change, and was replaced by
 * the next one before you could read it. This is the same information kept still: the table,
 * a readable label, the key, and the value it moved from and to - which together are exactly
 * the four fields the "Add setting" form asks for.
 *
 * A lazy list rather than a scrolling column, because a busy device fills three hundred rows
 * and composing all of them to show ten is wasteful. It scrolls itself, which is why this page
 * asks [SettingsPage] not to scroll the body around it.
 */
@Composable
internal fun SettingsChangeLogDialog(
    modifier: Modifier = Modifier,
    entries: List<SettingsChangeLog.Entry>,
    onClear: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.settings_log_title),
        scrollableBody = false,
        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                enabled = entries.isNotEmpty(),
                onClick = onClear,
            ) {
                Text(text = stringResource(R.string.settings_log_clear))
            }
        },
    ) {
        if (entries.isEmpty()) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 8.dp),
                text = stringResource(R.string.settings_log_empty),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        } else {
            // Says what the list is for, because a wall of keys and numbers does not.
            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.settings_log_description),
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Spacer(modifier = Modifier.height(8.dp))

            LazyColumn(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f),
            ) {
                items(entries) { entry ->
                    SettingsChangeRow(entry = entry)

                    HorizontalDivider()
                }
            }
        }
    }
}

/** One observed change: table and label on top, then the key, then the value it moved to. */
@Composable
private fun SettingsChangeRow(
    modifier: Modifier = Modifier,
    entry: SettingsChangeLog.Entry,
) {
    val table = when (entry.table) {
        SettingsChangeLog.Table.System -> stringResource(commonR.string.system)
        SettingsChangeLog.Table.Secure -> stringResource(commonR.string.secure)
        SettingsChangeLog.Table.Global -> stringResource(commonR.string.global)
        SettingsChangeLog.Table.Unknown -> stringResource(R.string.settings_log_unknown_table)
    }

    val unset = stringResource(R.string.settings_log_unset)

    Column(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 8.dp),
    ) {
        Text(
            text = stringResource(R.string.settings_log_entry_heading, table, entry.label),
            style = MaterialTheme.typography.bodyLarge,
        )

        Spacer(modifier = Modifier.height(2.dp))

        // The key is the one line here that has to be copied exactly, so it gets the
        // monospace-ish treatment of standing on its own rather than being folded into a
        // sentence with the label.
        Text(
            text = entry.key,
            style = MaterialTheme.typography.bodySmall,
            color = MaterialTheme.colorScheme.onSurfaceVariant,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis,
        )

        Spacer(modifier = Modifier.height(2.dp))

        // Both ends when there are two: the value to apply and the value to put back are the
        // remaining two fields of a profile, and a change caught in the act gives you both.
        Text(
            text = if (entry.previousValue == null) {
                stringResource(R.string.settings_log_value, entry.value ?: unset)
            } else {
                stringResource(
                    R.string.settings_log_value_change,
                    entry.previousValue ?: unset,
                    entry.value ?: unset,
                )
            },
            style = MaterialTheme.typography.bodySmall,
        )
    }
}
