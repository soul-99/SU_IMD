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

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalClipboardManager
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.AnnotatedString
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.unit.dp
import com.android.geto.feature.settings.R

/**
 * The diagnostic log, and the switch that decides whether there is one.
 *
 * **`scrollableBody = false`, and that is the whole layout.** The page does not scroll; the log
 * takes whatever height is left and scrolls inside its own box. That is what keeps the three
 * buttons on screen however long the log gets — with a scrolling page they would sit at the
 * bottom of forty thousand lines, which is where nobody would ever find them.
 *
 * Recording is off until it is switched on, and switching it on starts nothing running: a log
 * line is an append on a code path that was executing anyway, so with nothing hidden and IMD+
 * off this costs the same whether it is on or not.
 */
@Composable
internal fun DiagnosticsDialog(
    modifier: Modifier = Modifier,
    enabled: Boolean,
    log: String,
    onSetEnabled: (Boolean) -> Unit,
    onClear: () -> Unit,
    onExport: (String) -> Unit,
    onDismissRequest: () -> Unit,
) {
    val clipboard = LocalClipboardManager.current

    // Android's own "create a document" picker, so the copy lands wherever the user keeps
    // things rather than somewhere this app decided. A null result is the user backing out,
    // which is not a failure and says nothing.
    val saveLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.CreateDocument(LOG_MIME_TYPE),
    ) { uri -> uri?.let { onExport(it.toString()) } }

    SettingsPage(
        modifier = modifier,
        title = stringResource(R.string.diagnostics_title),
        scrollableBody = false,
        onDismissRequest = onDismissRequest,
    ) {
        AutoHideSwitchRow(
            title = stringResource(R.string.diagnostics_switch),
            checked = enabled,
            enabled = true,
            subtitle = if (enabled) {
                stringResource(R.string.diagnostics_switch_on)
            } else {
                stringResource(R.string.diagnostics_switch_off)
            },
            onCheckedChange = onSetEnabled,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // weight(1f) is what makes the buttons below immovable: the log gets the space that is
        // left over rather than the space it wants, so a long log scrolls rather than growing.
        Surface(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
                .padding(horizontal = 10.dp),
            shape = RoundedCornerShape(8.dp),
            color = MaterialTheme.colorScheme.surfaceContainerHighest,
        ) {
            Text(
                modifier = Modifier
                    .verticalScroll(rememberScrollState())
                    .horizontalScroll(rememberScrollState())
                    .padding(10.dp),
                text = log.ifBlank { stringResource(R.string.diagnostics_empty) },
                style = MaterialTheme.typography.bodySmall,
                fontFamily = FontFamily.Monospace,
                // Machine output, so it is read in columns. A wrapped line puts the message
                // under the timestamp of the line before it and the column disappears.
                softWrap = false,
            )
        }

        Spacer(modifier = Modifier.height(10.dp))

        Row(
            modifier = Modifier.padding(horizontal = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            Button(
                modifier = Modifier.weight(1f),
                enabled = log.isNotBlank(),
                onClick = { clipboard.setText(AnnotatedString(log)) },
            ) {
                Text(text = stringResource(R.string.diagnostics_copy))
            }

            Button(
                modifier = Modifier.weight(1f),
                enabled = log.isNotBlank(),
                onClick = { saveLauncher.launch(LOG_FILE_NAME) },
            ) {
                Text(text = stringResource(R.string.diagnostics_save))
            }
        }

        // Outlined and on its own row rather than a third of a crowded one. It is the only
        // button here that destroys something, and it should not sit a thumb's width from
        // "Copy log".
        OutlinedButton(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            enabled = log.isNotBlank(),
            onClick = onClear,
        ) {
            Text(text = stringResource(R.string.diagnostics_clear))
        }
    }
}

private const val LOG_MIME_TYPE = "text/plain"

/** Suggested in the picker; the user can rename it there. */
private const val LOG_FILE_NAME = "imd-diagnostics.log"
