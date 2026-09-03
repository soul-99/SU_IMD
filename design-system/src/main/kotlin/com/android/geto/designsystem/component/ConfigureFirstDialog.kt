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
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp

/**
 * Why a greyed toggle or template will not move, and where to go and fix it.
 *
 * One sentence and a location tree — the author's shape: *"'Please configure the settings
 * first' (from next line) [display a location tree to the setting]"*. More than one path
 * where more than one thing is missing, so somebody who has configured neither is not sent
 * back twice.
 *
 * ⚠ **[paths] may be empty, and then this is a plain notice.** The Shevery case has nothing to
 * point at: Display over other apps is not supported on that fork at all, so a path would be
 * directions to a picker that can never help.
 *
 * ⚠ **Here rather than in a feature module, and the sentences are parameters.** The same two
 * reasons as [PriorHideDialog]: `feature/apps` depends on `feature/app-settings`, so anything
 * both surfaces need cannot live in either, and this module has no `values/` folder to hold
 * product copy in.
 *
 * The paths carry the primary colour and a medium weight, which is how `HelpPath` already
 * draws the same shape in the setup help.
 */
@Composable
fun ConfigureFirstDialog(
    message: String,
    modifier: Modifier = Modifier,
    paths: List<String> = emptyList(),
    dismissLabel: String,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(text = message, style = MaterialTheme.typography.bodyLarge)

            for (path in paths) {
                Spacer(modifier = Modifier.height(10.dp))

                Text(
                    text = path,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Medium,
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = dismissLabel)
                }
            }
        }
    }
}
