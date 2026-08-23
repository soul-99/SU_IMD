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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SegmentedButton
import androidx.compose.material3.SegmentedButtonDefaults
import androidx.compose.material3.SingleChoiceSegmentedButtonRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.feature.apps.R

/**
 * Every choice here applies the moment it is tapped. Sort and view change what is on
 * screen behind the dialog, so staging them behind an Update button would hide the
 * effect of the choice being made.
 *
 * A third group used to choose what a tap and a long press did. That is no longer a
 * preference: the notification function decides it, because the two modes need different
 * things behind a long press -- a shortcut in one, a per-app profile in the other -- and a
 * user-set override could only ever disagree with the mode it was in.
 */
@Composable
internal fun FavouriteAppsOptionsDialog(
    modifier: Modifier = Modifier,
    sortFavouriteApps: SortFavouriteApps,
    favouriteAppsView: FavouriteAppsView,
    canReorder: Boolean,
    onDismissRequest: () -> Unit,
    onUpdateSortFavouriteApps: (SortFavouriteApps) -> Unit,
    onUpdateFavouriteAppsView: (FavouriteAppsView) -> Unit,
    onReorderClick: () -> Unit,
) {
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
                text = stringResource(R.string.favourite_apps_options),
                style = MaterialTheme.typography.titleLarge,
            )

            OptionLabel(text = stringResource(R.string.sort))

            SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
                SortFavouriteApps.entries.forEachIndexed { index, entry ->
                    SegmentedButton(
                        selected = entry == sortFavouriteApps,
                        onClick = { onUpdateSortFavouriteApps(entry) },
                        shape = SegmentedButtonDefaults.itemShape(
                            index = index,
                            count = SortFavouriteApps.entries.size,
                        ),
                    ) {
                        Text(text = entry.getTitle())
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            OptionLabel(text = stringResource(R.string.view))

            SingleChoiceSegmentedButtonRow(modifier = Modifier.fillMaxWidth()) {
                FavouriteAppsView.entries.forEachIndexed { index, entry ->
                    SegmentedButton(
                        selected = entry == favouriteAppsView,
                        onClick = { onUpdateFavouriteAppsView(entry) },
                        shape = SegmentedButtonDefaults.itemShape(
                            index = index,
                            count = FavouriteAppsView.entries.size,
                        ),
                    ) {
                        Text(text = entry.getTitle())
                    }
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(top = 10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(
                    enabled = canReorder,
                    onClick = onReorderClick,
                ) {
                    Text(text = stringResource(R.string.reorder))
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }
}

@Composable
private fun OptionLabel(
    modifier: Modifier = Modifier,
    text: String,
) {
    Text(
        modifier = modifier.padding(horizontal = 10.dp, vertical = 6.dp),
        text = text,
        style = MaterialTheme.typography.titleSmall,
    )
}

@Composable
private fun SortFavouriteApps.getTitle() = when (this) {
    SortFavouriteApps.Custom -> stringResource(R.string.custom)
    SortFavouriteApps.Alphabetical -> stringResource(R.string.alphabetical)
}

@Composable
private fun FavouriteAppsView.getTitle() = when (this) {
    FavouriteAppsView.List -> stringResource(R.string.list)
    FavouriteAppsView.Grid -> stringResource(R.string.grid)
}
