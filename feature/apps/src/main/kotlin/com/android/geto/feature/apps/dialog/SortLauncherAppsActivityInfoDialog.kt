/*
 *
 *   Copyright 2023 Einstein Blanco
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

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoSwitch
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.component.GetoChoiceRow
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.feature.apps.R
import com.android.geto.common.R as commonR

@Composable
internal fun SortLauncherAppsActivityInfoDialog(
    modifier: Modifier = Modifier,
    sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo,
    sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo,
    showSystem: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSortLauncherAppsActivityInfo: (SortLauncherAppsActivityInfo) -> Unit,
    onUpdateSortOrderLauncherAppsActivityInfo: (SortOrderLauncherAppsActivityInfo) -> Unit,
    onUpdateShowSystem: (Boolean) -> Unit,
) {
    var selectedSortLauncherAppsActivityInfoIndex by rememberSaveable {
        mutableIntStateOf(
            SortLauncherAppsActivityInfo.entries.indexOf(sortLauncherAppsActivityInfo),
        )
    }

    var selectedSortOrderLauncherAppsActivityInfoIndex by rememberSaveable {
        mutableIntStateOf(
            SortOrderLauncherAppsActivityInfo.entries.indexOf(sortOrderLauncherAppsActivityInfo),
        )
    }

    var selectedShowSystem by rememberSaveable { mutableStateOf(showSystem) }

    DialogContainer(
        modifier = modifier.verticalScroll(rememberScrollState()),
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.sort),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(10.dp))

            SortLauncherAppsActivityInfoDialogSelection(
                selectedSortLauncherAppsActivityInfoIndex = selectedSortLauncherAppsActivityInfoIndex,
                selectedSortOrderLauncherAppsActivityInfoIndex = selectedSortOrderLauncherAppsActivityInfoIndex,
                onUpdateSelectedSortLauncherAppsActivityInfoIndex = {
                    selectedSortLauncherAppsActivityInfoIndex = it
                },
                onUpdateSelectedSortOrderLauncherAppsActivityInfoIndex = {
                    selectedSortOrderLauncherAppsActivityInfoIndex = it
                },
            )

            Spacer(modifier = Modifier.height(8.dp))

            ShowSystemSetting(
                showSystem = selectedShowSystem,
                onUpdateShowSystem = {
                    selectedShowSystem = it
                },
            )

            SortLauncherAppsActivityInfoDialogButtons(
                selectedSortLauncherAppsActivityInfoIndex = selectedSortLauncherAppsActivityInfoIndex,
                selectedSortOrderLauncherAppsActivityInfoIndex = selectedSortOrderLauncherAppsActivityInfoIndex,
                selectedShowSystem = selectedShowSystem,
                onDismissRequest = onDismissRequest,
                onUpdateSortLauncherAppsActivityInfo = onUpdateSortLauncherAppsActivityInfo,
                onUpdateSortOrderLauncherAppsActivityInfo = onUpdateSortOrderLauncherAppsActivityInfo,
                onUpdateShowSystem = onUpdateShowSystem,
            )
        }
    }
}

@Composable
private fun SortLauncherAppsActivityInfoDialogSelection(
    selectedSortLauncherAppsActivityInfoIndex: Int,
    selectedSortOrderLauncherAppsActivityInfoIndex: Int,
    onUpdateSelectedSortLauncherAppsActivityInfoIndex: (Int) -> Unit,
    onUpdateSelectedSortOrderLauncherAppsActivityInfoIndex: (Int) -> Unit,
) {
    // ⚠ **Soft pills rather than Material's outlined segments — the author's D1.** Same component
    // role, same one-of-N semantics; what has gone is the hairline outline and the hard dividers.
    // See GetoChoiceRow, which is where the drawing and the reasoning both live.
    GetoChoiceRow(
        options = SortLauncherAppsActivityInfo.entries,
        selected = SortLauncherAppsActivityInfo.entries[selectedSortLauncherAppsActivityInfoIndex],
        label = { it.getTitle() },
        onSelect = {
            onUpdateSelectedSortLauncherAppsActivityInfoIndex(
                SortLauncherAppsActivityInfo.entries.indexOf(it),
            )
        },
    )

    Spacer(modifier = Modifier.height(10.dp))

    GetoChoiceRow(
        options = SortOrderLauncherAppsActivityInfo.entries,
        selected = SortOrderLauncherAppsActivityInfo.entries[
            selectedSortOrderLauncherAppsActivityInfoIndex,
        ],
        label = { it.getTitle() },
        onSelect = {
            onUpdateSelectedSortOrderLauncherAppsActivityInfoIndex(
                SortOrderLauncherAppsActivityInfo.entries.indexOf(it),
            )
        },
    )
}

@Composable
private fun SortLauncherAppsActivityInfoDialogButtons(
    modifier: Modifier = Modifier,
    selectedSortLauncherAppsActivityInfoIndex: Int,
    selectedSortOrderLauncherAppsActivityInfoIndex: Int,
    selectedShowSystem: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSortLauncherAppsActivityInfo: (SortLauncherAppsActivityInfo) -> Unit,
    onUpdateSortOrderLauncherAppsActivityInfo: (SortOrderLauncherAppsActivityInfo) -> Unit,
    onUpdateShowSystem: (Boolean) -> Unit,
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(10.dp),
        horizontalArrangement = Arrangement.End,
    ) {
        TextButton(
            onClick = onDismissRequest,
        ) {
            Text(text = stringResource(commonR.string.cancel))
        }
        TextButton(
            onClick = {
                val selectedSortLauncherAppsActivityInfo =
                    SortLauncherAppsActivityInfo.entries.getOrNull(
                        selectedSortLauncherAppsActivityInfoIndex,
                    )

                val selectedSortOrdeLauncherAppsActivityInfo =
                    SortOrderLauncherAppsActivityInfo.entries.getOrNull(
                        selectedSortOrderLauncherAppsActivityInfoIndex,
                    )

                selectedSortLauncherAppsActivityInfo?.let(onUpdateSortLauncherAppsActivityInfo)

                selectedSortOrdeLauncherAppsActivityInfo?.let(
                    onUpdateSortOrderLauncherAppsActivityInfo,
                )

                onUpdateShowSystem(selectedShowSystem)

                onDismissRequest()
            },
        ) {
            Text(text = stringResource(commonR.string.update))
        }
    }
}

@Composable
private fun ShowSystemSetting(
    modifier: Modifier = Modifier,
    showSystem: Boolean,
    onUpdateShowSystem: (Boolean) -> Unit,
) {
    Spacer(modifier = Modifier.height(8.dp))

    Row(
        modifier = modifier
            .clickable {
                onUpdateShowSystem(!showSystem)
            }
            .fillMaxWidth()
            .padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = stringResource(R.string.show_system),
                style = MaterialTheme.typography.bodyLarge,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = stringResource(R.string.show_system_applications),
                style = MaterialTheme.typography.bodySmall,
            )
        }

        GetoSwitch(
            checked = showSystem,
            onCheckedChange = onUpdateShowSystem,
        )
    }
}

@Composable
private fun SortLauncherAppsActivityInfo.getTitle() = when (this) {
    SortLauncherAppsActivityInfo.Name -> stringResource(R.string.name)
    SortLauncherAppsActivityInfo.UpdateTime -> stringResource(R.string.update_time)
    SortLauncherAppsActivityInfo.InstallTime -> stringResource(R.string.install_time)
}

@Composable
private fun SortOrderLauncherAppsActivityInfo.getTitle() = when (this) {
    SortOrderLauncherAppsActivityInfo.Ascending -> stringResource(R.string.ascending)
    SortOrderLauncherAppsActivityInfo.Descending -> stringResource(R.string.descending)
}
