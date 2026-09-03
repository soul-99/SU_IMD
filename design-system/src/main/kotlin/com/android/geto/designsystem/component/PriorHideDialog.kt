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
package com.android.geto.designsystem.component

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * Settings are still down from a run of IMD that is no longer alive.
 *
 * Two answers, and both of them end in the launch going ahead — which is why neither button
 * dismisses without doing something and there is no third way out.
 *
 * ⚠ **`dismissible = false`, and that is not a detail.** This dialog shipped once with
 * `onDismissRequest = onIgnore`, which handed the *permanent* answer to a back press and to a
 * tap beside the card. The author lost a device's pending reverts to a stray tap. There is no
 * harmless dismissal to offer here — every way out of this dialog changes the device — so it
 * has none, and `onDismissRequest` is left empty rather than pointed at either button.
 *
 * ⚠ **Ignoring is permanent**, and the label the callers pass is written to say so. Afterwards
 * nothing in IMD knows those settings were ever on, and `Revert to default` is the only way back
 * to a known state.
 *
 * ⚠ **Here rather than in `feature/apps`, where the other launch dialogs live.** It was there
 * first, and it did not build: `feature/apps` depends on `feature/app-settings`, so the per-app
 * settings screen — which is one of the five surfaces that has to show this — can never see it.
 * `design-system` is the one module all five already use, for `DialogContainer` immediately
 * below.
 *
 * ⚠ **The sentences are parameters, not resources.** This module does not depend on `:common`,
 * where they live beside `permissions_lost`, and has no `values/` folder at all — giving it one
 * to hold three sentences would put product copy in the design system and add a module to the
 * translation sweep. Every caller can already read them.
 */
@Composable
fun PriorHideDialog(
    title: String,
    restoreLabel: String,
    ignoreLabel: String,
    modifier: Modifier = Modifier,
    onRestore: () -> Unit,
    onIgnore: () -> Unit,
) {
    DialogContainer(
        modifier = modifier,
        dismissible = false,
        // Unreachable while dismissible is false, and deliberately empty rather than either
        // answer: if it ever does become reachable, doing nothing is the safe outcome.
        onDismissRequest = {},
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(text = title, style = MaterialTheme.typography.titleMedium)

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onIgnore) {
                    Text(text = ignoreLabel)
                }

                TextButton(onClick = onRestore) {
                    Text(text = restoreLabel)
                }
            }
        }
    }
}
