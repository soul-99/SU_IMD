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
package com.android.geto.feature.settings.dialog

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.selection.selectableGroup
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.semantics.Role
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.IconStyle
import com.android.geto.feature.settings.R

/**
 * How app icons are drawn — the author's *"Icon style"*.
 *
 * ⚠ **Built as `ThemeDialog` is, two rows above it in the same section**: a radio group, then
 * Cancel beside the committing button. Two controls in one section that behave differently is a
 * worse outcome than either shape on its own.
 *
 * ⚠ **The choice is a draft until Save.** The author asked for a Save button, and a radio that
 * wrote as it was tapped would make that button decorative — and Cancel a lie.
 */
@Composable
internal fun IconStyleDialog(
    modifier: Modifier = Modifier,
    selected: IconStyle,
    onSave: (IconStyle) -> Unit,
    onDismissRequest: () -> Unit,
) {
    var draft by rememberSaveable(selected) { mutableStateOf(selected) }

    DialogContainer(
        modifier = modifier.verticalScroll(rememberScrollState()),
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.icon_style),
                style = MaterialTheme.typography.titleLarge,
            )

            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .selectableGroup(),
            ) {
                IconStyleOption(
                    label = stringResource(R.string.icon_style_smart),
                    note = stringResource(R.string.icon_style_smart_note),
                    selected = draft == IconStyle.SmartAdaptive,
                    onSelect = { draft = IconStyle.SmartAdaptive },
                )

                IconStyleOption(
                    label = stringResource(R.string.icon_style_system),
                    note = stringResource(R.string.icon_style_system_note),
                    selected = draft == IconStyle.System,
                    onSelect = { draft = IconStyle.System },
                )
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 8.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.cancel))
                }

                TextButton(
                    onClick = {
                        onSave(draft)

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
 * One option, with the line that says what it does.
 *
 * The whole row is the target rather than the button alone — the note is the part most people
 * read, and a row whose explanation is not tappable invites a miss.
 */
@Composable
private fun IconStyleOption(
    label: String,
    note: String,
    selected: Boolean,
    onSelect: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .selectable(selected = selected, role = Role.RadioButton, onClick = onSelect)
            .padding(horizontal = 16.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Null, so TalkBack announces one control for the row rather than two.
        RadioButton(selected = selected, onClick = null)

        Column(modifier = Modifier.padding(start = 10.dp)) {
            Text(text = label, style = MaterialTheme.typography.bodyLarge)

            Text(
                text = note,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )
        }
    }
}
