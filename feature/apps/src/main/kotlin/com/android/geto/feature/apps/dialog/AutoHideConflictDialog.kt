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
 * Why the app did not open, when Auto-hide settings (IMD+) is holding the device down.
 *
 * Only the memory function can reach this. IMD+ has applied the device-wide list; a per-app
 * profile that asks for exactly those settings has nothing left to do and simply opens the app.
 * One that asks for anything *more* cannot be satisfied without hiding settings on top of
 * IMD+'s — and that leaves a device neither mechanism's revert puts back, because IMD+'s revert
 * restores what IMD+ hid, this app's revert restores what this app hid, and nothing owns the
 * overlap.
 *
 * So it is refused, and the way forward is one sentence long: revert IMD+ first, from its
 * notification or the Hide settings tile, then launch the app again.
 */
@Composable
fun AutoHideConflictDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(horizontal = 10.dp, vertical = 6.dp),
                text = stringResource(R.string.auto_hide_conflict_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.auto_hide_conflict_body),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                modifier = Modifier.padding(horizontal = 10.dp),
                text = stringResource(R.string.auto_hide_conflict_fix),
                style = MaterialTheme.typography.bodyMedium,
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
