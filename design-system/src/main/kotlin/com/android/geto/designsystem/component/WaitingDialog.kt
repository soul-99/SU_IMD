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

import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

/**
 * A spinner and a sentence, for a wait the user cannot otherwise see.
 *
 * The shape `ShizukuStartingDialog` has always had — a 24 dp indicator, 16 dp of space, one line
 * of text — with the sentence as a parameter instead of a `when` over one enum, so the force-close
 * popup's restore can use it from three separate windows.
 *
 * ⚠ **Here rather than beside `ShizukuStartingDialog` in `feature/apps`.** Same reason
 * [PriorHideDialog] is here: `feature/apps` depends on `feature/app-settings`, so anything both
 * of them need has to live below both. `:common` is not an option either — that module has no
 * Compose.
 *
 * ⚠ **`dismissible = false`, and no buttons.** There is nothing to decide, and dismissing it would
 * not stop the work — it would only hide it. `compact`, because this is a card with one line in
 * it and the platform's own width is exactly right for that.
 */
@Composable
fun WaitingDialog(
    text: String,
    modifier: Modifier = Modifier,
) {
    DialogContainer(
        modifier = modifier,
        compact = true,
        dismissible = false,
        onDismissRequest = {},
    ) {
        Row(
            modifier = Modifier.padding(horizontal = 20.dp, vertical = 24.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            CircularProgressIndicator(modifier = Modifier.size(24.dp))

            Spacer(modifier = Modifier.width(16.dp))

            Text(
                modifier = Modifier.weight(1f),
                text = text,
                style = MaterialTheme.typography.bodyMedium,
            )
        }
    }
}
