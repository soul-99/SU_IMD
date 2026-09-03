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
 * Shown once to an install that existed before this version, pointing at what moved.
 *
 * Never to a fresh install: somebody seeing the app for the first time has no old Settings tab
 * to compare it against, and telling them something changed would be describing a history they
 * were not part of. `settingsNoticeRevision` and `setupNoticeVersion` together are what decide
 * that - see `MainActivity`.
 */
// ⚠ **Public, unlike most of its neighbours in this folder, and it has to be.** This one is
// shown from `MainActivity` in the `app` module, and `internal` is module-scoped — the same
// reason AutoHideNothingToHideDialog and RevertDefaultsNoticeDialog are public. Marked internal
// first, which compiled here and failed in the author's build.
@Composable
fun SettingsTabNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = emphasised(
                    text = stringResource(R.string.settings_tab_notice),
                    names = listOf(stringResource(R.string.settings_tab_notice_name)),
                ),
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
