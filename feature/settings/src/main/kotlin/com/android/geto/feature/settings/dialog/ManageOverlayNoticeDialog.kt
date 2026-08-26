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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.settings.R

/**
 * What is left to do after switching overlay management on.
 *
 * Shown after the switch moves rather than before, unlike the auto revert notice: there is
 * nothing here to agree to or refuse, only three rows that have just appeared elsewhere and
 * do nothing until they are filled in. Switching the feature on with all three left alone is
 * the failure this exists to head off - it looks enabled and hides nothing.
 *
 * Shown every time, not once. Someone switching this back on months later has exactly the
 * same three things to check, and a notice that only ever appeared on the first day would be
 * missing on every occasion anybody actually needed it.
 */
@Composable
internal fun ManageOverlayNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.manage_overlay),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                // The section name is bolded rather than quoted: it is where the reader has
                // to go next, and it is the one part of the sentence they need to find again
                // once the dialog is gone.
                text = emphasised(
                    text = stringResource(R.string.manage_overlay_notice),
                    names = listOf(stringResource(R.string.section_app_functions)),
                ),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(4.dp))

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
