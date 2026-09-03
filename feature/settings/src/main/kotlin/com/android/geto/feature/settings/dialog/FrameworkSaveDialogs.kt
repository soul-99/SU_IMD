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
import com.android.geto.feature.settings.R

/**
 * What a framework change asks before it happens, when something is still hidden.
 *
 * ⚠ **Changing either framework while a hide is outstanding is how a debt is stranded.** The
 * two frameworks are undone by different reverts and each has routes the other does not, so a
 * pile of per-app memory records under a framework that no longer reads them has nothing left
 * that clears it. The sweep has always run at a mechanism change; what is new in v3 is that
 * the user is told, and gets to say no.
 *
 * Confirm-shaped rather than a progress spinner because the reverts are about to change the
 * device — settings come back on, Shizuku may be started — and that is not something to do to
 * somebody who only meant to change a preference.
 */
@Composable
internal fun FrameworkPendingRevertsDialog(
    modifier: Modifier = Modifier,
    onConfirm: () -> Unit,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.framework_pending_reverts),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.cancel))
                }

                TextButton(onClick = onConfirm) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * The sweep ran and could not finish, so the preference has not moved.
 *
 * **Not changing the setting is the whole point.** A framework that changed anyway would leave
 * the outstanding hide readable only by the framework that is no longer selected — which is
 * precisely the stranded debt the sweep exists to prevent, arrived at by a different road.
 *
 * Points at the notifications rather than offering a retry: whatever stopped the revert —
 * Shizuku down, overlay access unreachable, the grant withdrawn — has already posted its own
 * notification saying which, and that notification is the one with the fix on it.
 */
@Composable
internal fun FrameworkRevertsFailedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.framework_pending_reverts_failed),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

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
