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
 * Re-organise favourites: order them, and drop the ones that should not be here.
 *
 * Move-up / move-down rather than drag-to-reorder on purpose: the favourites grid already
 * binds long press, and a drag handle competing with that gesture is how you get accidental
 * launches.
 *
 * Both the ordering and the removals are staged until Update, so Cancel undoes everything —
 * removal especially, since the alternative is a mis-tap that silently drops a favourite.
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

    // Removals are tracked by name rather than inferred from what is missing at save time.
    // The save below deliberately keeps favourites the dialog could not show, and a removed
    // app is indistinguishable from one of those — so without this list, removing an app
    // would put it straight back.
    val removed = remember(favouriteApps) { mutableStateListOf<String>() }

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

                                IconButton(
                                    onClick = {
                                        removed.add(info.componentName)

                                        // removeAt, not remove(info): the element overload
                                        // and the deprecated index one are told apart by
                                        // the element type, and the index is already here.
                                        ordered.removeAt(index)
                                    },
                                ) {
                                    Icon(
                                        imageVector = GetoIcons.Remove,
                                        contentDescription = stringResource(
                                            R.string.remove_from_favourites,
                                        ),
                                        tint = MaterialTheme.colorScheme.error,
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
                        // Anything removed here is excluded from that rescue, or the two
                        // rules would cancel out and removal would never take effect.
                        val unresolved: List<String> = savedComponentNames.filterNot {
                            it in reordered || it in removed
                        }

                        onUpdateFavouriteComponentNames(reordered + unresolved)
                    },
                ) {
                    Text(text = stringResource(commonR.string.update))
                }
            }
        }
    }
}
