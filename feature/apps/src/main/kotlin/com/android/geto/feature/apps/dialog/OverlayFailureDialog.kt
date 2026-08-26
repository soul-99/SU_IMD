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
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.feature.apps.R

/**
 * Why the app did not open, when the reason was overlay access rather than settings.
 *
 * A dialog and not the snackbar every other launch failure uses, for two reasons. The launch
 * is abandoned, so there is nothing behind the message to look at and nothing lost by
 * interrupting; and a shortcut launch has no snackbar host at all, which is how this failure
 * used to produce a window that simply never opened and said nothing about why.
 *
 * The two points are the only two things that fix it, in the order worth trying: the Shizuku
 * permission prompt is the one people miss, and everything else is the fork configuration.
 */
@Composable
fun OverlayFailureDialog(
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
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.overlay_failure_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.overlay_failure_check),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            OverlayFailurePoint(text = stringResource(R.string.overlay_failure_point_permission))

            OverlayFailurePoint(text = stringResource(R.string.overlay_failure_point_configuration))

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
 * One bullet.
 *
 * The marker is a composable of its own rather than a character typed into the string,
 * because a translated string carrying its own bullet is a translated string that can lose
 * it - and right-to-left languages put it on the other side without being asked.
 */
@Composable
private fun OverlayFailurePoint(
    modifier: Modifier = Modifier,
    text: String,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(horizontal = 10.dp, vertical = 4.dp),
    ) {
        Text(text = "•", style = MaterialTheme.typography.bodyMedium)

        Spacer(modifier = Modifier.width(8.dp))

        Text(
            modifier = Modifier.weight(1f),
            text = text,
            style = MaterialTheme.typography.bodyMedium,
        )
    }
}
