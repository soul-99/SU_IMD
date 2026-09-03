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
import androidx.compose.material3.LocalContentColor
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
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
    /**
     * Draw this as a page in the setup flow rather than as a dialog over the settings list.
     *
     * Three things follow from it and nothing else does: the outer margin goes, because a page
     * reaches its edges; the back arrow goes, because there is nothing behind a setup step to
     * go back to; and the footer is arranged **SpaceBetween** instead of **End**, which is what
     * puts the author's Skip at the left and Next at the right.
     */
    flat: Boolean = false,
    onDismissRequest: () -> Unit,
    actions: @Composable RowScope.() -> Unit = {},
    content: @Composable ColumnScope.() -> Unit,
) {
    // Inset rather than edge-to-edge. These pages carry a back arrow and a Save button, so
    // they read as dialogs rather than as screens, and a full-bleed one leaves nothing of the
    // settings list showing behind it to say where the user still is.
    //
    // The width cap now lives in DialogContainer and applies to every dialog in the app, so
    // there is nothing to pass here: on a large screen this page shows the same comfortable
    // phone-shaped column, centred, and on a phone it fills the width as it always has. The
    // top margin is larger than the sides on purpose - it is the gap the eye reads as "this
    // is on top of something", and it keeps the header clear of a notch or status bar.
    DialogContainer(
        // Flat reaches the edges: the margin above is the gap that says "this is on top of
        // something", and during setup there is nothing underneath for it to say that about.
        modifier = if (flat) {
            modifier.fillMaxSize()
        } else {
            modifier
                .fillMaxSize()
                .padding(start = 8.dp, end = 8.dp, top = 40.dp, bottom = 8.dp)
        },
        shape = MaterialTheme.shapes.extraLarge,
        fullScreen = true,
        flat = flat,
        onDismissRequest = onDismissRequest,
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 4.dp, vertical = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // No way back out of a setup step - Skip is the way past it, and it is in
                // the footer with Next.
                if (!flat) {
                    IconButton(onClick = onDismissRequest) {
                        Icon(
                            modifier = Modifier.size(22.dp),
                            imageVector = GetoIcons.Back,
                            contentDescription = stringResource(R.string.page_back),
                        )
                    }
                }

                Spacer(modifier = Modifier.width(4.dp))

                Text(
                    modifier = Modifier.weight(1f),
                    text = title,
                    style = MaterialTheme.typography.titleLarge,
                    // ⚠ **A rule, not a parameter.** The page already knows it is a setup step,
                    // so its heading cannot end up in the wrong colour because a caller forgot
                    // an argument. primary is what the Shizuku setup page's own heading uses.
                    color = if (flat) {
                        MaterialTheme.colorScheme.primary
                    } else {
                        LocalContentColor.current
                    },
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
                // ⚠ **SpaceBetween is what puts Skip on the left.** With two actions the
                // first goes to one edge and the second to the other, which is the author's
                // *"skip button on left and next button as it is on right"* - no alignment
                // modifiers on the buttons themselves, so the caller passes them in reading
                // order and the row does the rest.
                horizontalArrangement = if (flat) {
                    Arrangement.SpaceBetween
                } else {
                    Arrangement.End
                },
                verticalAlignment = Alignment.CenterVertically,
                content = actions,
            )

            Spacer(modifier = Modifier.height(4.dp))
        }
    }
}
