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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.emphasised
import com.android.geto.feature.settings.R

/**
 * Tells somebody that their revert configuration was reset under them.
 *
 * Shown once, to installs upgrading into v1.6.6, because the alternative is a device that
 * quietly stops restoring things it used to restore with nothing anywhere saying why. A
 * default narrowing for safety is defensible; doing it silently is not.
 *
 * The path is the same string the help page uses, rather than a second copy of the same
 * words, so a rename or a translation reaches both. That matters more than it looks: this
 * dialog's only useful content is where to go, and a path naming a screen that no longer
 * exists under that name is worse than no path at all.
 */
@Composable
fun RevertDefaultsNoticeDialog(
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
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.revert_defaults_notice_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = emphasised(
                    text = stringResource(R.string.revert_defaults_notice_body),
                    names = listOf(stringResource(R.string.revert_defaults_entry)),
                ),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.help_path_unhide),
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                color = MaterialTheme.colorScheme.primary,
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.revert_defaults_notice_dismiss))
                }
            }
        }
    }
}
