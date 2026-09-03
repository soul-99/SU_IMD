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
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.settings.R

/**
 * Shown once to an install that existed before v3, in the author's own words.
 *
 * ⚠ **Replaces `SettingsTabNoticeDialog`**, which said a smaller version of the same thing to
 * the same person on the same first launch — *"ingonre my previous dialog"*. That one's strings
 * are left declared and unused because their eleven translations are frozen.
 *
 * Never to a fresh install: somebody seeing the app for the first time has no previous settings
 * to have had matched, and telling them their configuration was carried over would be describing
 * a history they were not part of. `settingsNoticeRevision` and `setupNoticeVersion` together
 * decide that — see `MainActivity`.
 *
 * ⚠ **Public, unlike most of its neighbours in this folder, and it has to be.** It is shown from
 * `MainActivity` in the `app` module, and `internal` is module-scoped — the same reason
 * `AutoHideNothingToHideDialog` and `RevertDefaultsNoticeDialog` are public. Marking it internal
 * compiles here and fails in the author's build.
 */
@Composable
fun DeveloperNoteDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.developer_note_title),
                style = MaterialTheme.typography.titleMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                text = stringResource(R.string.developer_note_body),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            NotePoint(text = stringResource(R.string.developer_note_point_1))

            NotePoint(text = stringResource(R.string.developer_note_point_2))

            Spacer(modifier = Modifier.height(12.dp))

            // Bold, and in the scheme's primary — the green the section headings already take,
            // so "new" reads as an invitation rather than as another caveat.
            Text(
                text = stringResource(R.string.developer_note_new),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.primary,
                fontWeight = FontWeight.Bold,
            )

            Spacer(modifier = Modifier.height(6.dp))

            NotePoint(text = stringResource(R.string.developer_note_new_1))

            NotePoint(text = stringResource(R.string.developer_note_new_2))

            Spacer(modifier = Modifier.height(14.dp))

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
 * One nested bullet.
 *
 * ⚠ **A drawn dot rather than a numbered label**, at the author's correction — *"the first two
 * are nested bullets not numbered"*, and then *"yes use bullets please"* for the second pair.
 * The glyph is a Row of its own so a wrapped second line lines up under the first word rather
 * than under the dot.
 */
@Composable
private fun NotePoint(text: String, modifier: Modifier = Modifier) {
    Row(modifier = modifier.padding(start = 8.dp, top = 4.dp)) {
        Text(text = BULLET, style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.width(8.dp))

        Text(text = text, style = MaterialTheme.typography.bodyMedium)
    }
}

private const val BULLET = "\u2022"
