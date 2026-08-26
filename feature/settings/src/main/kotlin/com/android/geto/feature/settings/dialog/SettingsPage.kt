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
import androidx.compose.foundation.layout.ColumnScope
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.RowScope
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.RectangleShape
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.feature.settings.R

/**
 * A settings screen that fills the window, for the configurations that outgrew a dialog.
 *
 * Every one of these started as a short list and has been added to since. A dialog is capped
 * at the platform's dialog width and grows downwards until it is a scrolling sliver with its
 * buttons pinned to the bottom of a box - readable when it held four rows, cramped by the time
 * it holds six with a paragraph of small print under each.
 *
 * The shape is deliberately the same as the in-app help page, which has been full screen since
 * v1.5: a back arrow and title on top, the body scrolling between two dividers, and the
 * actions on a fixed footer so Save never scrolls out of reach. Built on [DialogContainer]
 * rather than a navigation destination so that the state and callbacks these screens already
 * have keep working unchanged, and so the system back gesture still closes them.
 */
@Composable
internal fun SettingsPage(
    modifier: Modifier = Modifier,
    title: String,
    /**
     * False when the body scrolls itself. A LazyColumn inside a verticalScroll parent is
     * measured with infinite height and throws, so the log - the one page here with a list
     * long enough to want laziness - takes the space instead of being scrolled inside it.
     */
    scrollableBody: Boolean = true,
    onDismissRequest: () -> Unit,
    actions: @Composable RowScope.() -> Unit = {},
    content: @Composable ColumnScope.() -> Unit,
) {
    DialogContainer(
        modifier = modifier.fillMaxSize(),
        shape = RectangleShape,
        fullScreen = true,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 4.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                IconButton(onClick = onDismissRequest) {
                    Icon(
                        modifier = Modifier.size(22.dp),
                        imageVector = GetoIcons.Back,
                        contentDescription = stringResource(R.string.page_back),
                    )
                }

                Spacer(modifier = Modifier.width(4.dp))

                Text(
                    modifier = Modifier.weight(1f),
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                )
            }

            HorizontalDivider()

            // The body scrolls, the header and footer do not. On a long configuration that
            // is the whole point: Save stays where it was put rather than living at the far
            // end of a list the user has to reach the bottom of to find it.
            Column(
                modifier = Modifier
                    .weight(1f)
                    .then(
                        if (scrollableBody) {
                            Modifier.verticalScroll(rememberScrollState())
                        } else {
                            Modifier
                        },
                    )
                    .padding(horizontal = 12.dp, vertical = 12.dp),
                content = content,
            )

            HorizontalDivider()

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 12.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically,
                content = actions,
            )

            Spacer(modifier = Modifier.height(4.dp))
        }
    }
}
