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

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.feature.apps.R

/**
 * Ten seconds of waiting, made visible.
 *
 * [com.android.geto.domain.usecase.StartShizukuUseCase] gives a fork up to ten seconds to
 * come up, and some of them use most of it. Without this the user taps an app, nothing
 * happens for ten seconds, and the app either opens late or reports a failure - which reads
 * as a hang, and the usual response to a hang is to tap again and start a second one.
 *
 * No title and no buttons, deliberately: there is nothing to decide and nothing to read
 * twice. It is not dismissable either, because dismissing it would not stop the wait, it
 * would only hide it.
 *
 * [reason] is not decoration. The same ten second wait precedes hiding overlay access and
 * giving it back, and a revert that says "to hide" is telling the user the opposite of what
 * is about to happen.
 */
@Composable
fun ShizukuStartingDialog(
    modifier: Modifier = Modifier,
    reason: OverlayStart,
) {
    Dialog(
        onDismissRequest = {},
        properties = DialogProperties(
            dismissOnBackPress = false,
            dismissOnClickOutside = false,
        ),
    ) {
        Surface(
            modifier = modifier.fillMaxWidth(),
            shape = MaterialTheme.shapes.large,
            color = MaterialTheme.colorScheme.surfaceContainerHigh,
            tonalElevation = 6.dp,
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                CircularProgressIndicator(modifier = Modifier.size(24.dp))

                Spacer(modifier = Modifier.width(16.dp))

                Text(
                    modifier = Modifier.weight(1f),
                    text = when (reason) {
                        OverlayStart.Hide ->
                            stringResource(R.string.shizuku_starting_to_hide_overlay)

                        OverlayStart.Restore ->
                            stringResource(R.string.shizuku_starting_to_restore_overlay)
                    },
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }
    }
}
