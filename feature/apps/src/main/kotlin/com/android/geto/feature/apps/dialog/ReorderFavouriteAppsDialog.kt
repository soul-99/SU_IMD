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
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.ListItem
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.feature.apps.R
import com.android.geto.common.R as commonR

/**
 * Move-up / move-down rather than drag-to-reorder on purpose: the favourites grid
 * already binds long press to launch-or-modify, and a drag handle competing with that
 * gesture is how you get accidental launches.
 */
@Composable
internal fun ReorderFavouriteAppsDialog(
    modifier: Modifier = Modifier,
    favouriteApps: List<LauncherAppsActivityInfo>,
    savedComponentNames: List<String>,
    onDismissRequest: () -> Unit,
    onUpdateFavouriteComponentNames: (List<String>) -> Unit,
) {
    val ordered = remember(favouriteApps) {
        mutableStateListOf<LauncherAppsActivityInfo>().apply { addAll(favouriteApps) }
    }

    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            Text(
                modifier = Modifier.padding(10.dp),
                text = stringResource(R.string.reorder_favourites),
                style = MaterialTheme.typography.titleLarge,
            )

            LazyColumn(modifier = Modifier.heightIn(max = 400.dp)) {
                items(items = ordered, key = { it.componentName }) { info ->
                    val index = ordered.indexOf(info)

                    ListItem(
                        headlineContent = {
                            Text(text = info.activityLabel, maxLines = 1)
                        },
                        leadingContent = {
                            AsyncImage(
                                modifier = Modifier.size(36.dp),
                                model = info.activityIcon,
                                contentDescription = null,
                            )
                        },
                        trailingContent = {
                            Row {
                                IconButton(
                                    enabled = index > 0,
                                    onClick = {
                                        if (index > 0) {
                                            ordered.add(index - 1, ordered.removeAt(index))
                                        }
                                    },
                                ) {
                                    Icon(
                                        imageVector = GetoIcons.ArrowUpward,
                                        contentDescription = stringResource(R.string.move_up),
                                    )
                                }

                                IconButton(
                                    enabled = index < ordered.lastIndex,
                                    onClick = {
                                        if (index < ordered.lastIndex) {
                                            ordered.add(index + 1, ordered.removeAt(index))
                                        }
                                    },
                                ) {
                                    Icon(
                                        imageVector = GetoIcons.ArrowDownward,
                                        contentDescription = stringResource(R.string.move_down),
                                    )
                                }
                            }
                        },
                    )
                }
            }

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.cancel))
                }

                TextButton(
                    onClick = {
                        val reordered: List<String> = ordered.map { it.componentName }

                        // Saving only what the dialog could show would quietly delete
                        // favourites whose app is merely unavailable right now — an
                        // unmounted SD card or a paused work profile, not an uninstall.
                        val unresolved: List<String> =
                            savedComponentNames.filterNot { it in reordered }

                        onUpdateFavouriteComponentNames(reordered + unresolved)
                    },
                ) {
                    Text(text = stringResource(commonR.string.update))
                }
            }
        }
    }
}
