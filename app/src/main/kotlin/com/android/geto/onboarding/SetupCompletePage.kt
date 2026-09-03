/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.onboarding

import android.app.StatusBarManager
import android.content.ComponentName
import android.content.Context
import android.graphics.drawable.Icon
import android.os.Build
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawing
import androidx.compose.foundation.layout.windowInsetsPadding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.FilledTonalButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.android.geto.R
import com.android.geto.activity.hide.HideTileService
import com.android.geto.activity.services.ServicesTileService

/**
 * The last page of setup, replacing the help/readme step.
 *
 * ⚠ **The help content is not gone, only this use of it.** `SetupHelpContent` still backs the
 * Help button in Settings; removing it because one of its two callers stopped using it is how a
 * Help button ends up empty.
 *
 * The list is the author's, nested numbering and all.
 */
@Composable
internal fun SetupCompletePage(
    modifier: Modifier = Modifier,
    /**
     * Null when there is nowhere to go back to.
     *
     * `remindersOnly` opens straight at this page, and a Back there would drop the user into a
     * page asking them to grant what they have already granted.
     */
    onBack: (() -> Unit)? = null,
    onContinue: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .padding(horizontal = 24.dp),
    ) {
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState()),
        ) {
            Spacer(modifier = Modifier.height(28.dp))

            Text(
                text = stringResource(R.string.setup_done_title),
                // r4t: one step up, with the rest of the page.
                style = MaterialTheme.typography.headlineMedium,
                color = MaterialTheme.colorScheme.primary,
            )

            Spacer(modifier = Modifier.height(20.dp))

            Point(text = stringResource(R.string.setup_done_1))

            Point(text = stringResource(R.string.setup_done_2))

            SubPoint(text = stringResource(R.string.setup_done_2_1))

            SubPoint(text = stringResource(R.string.setup_done_2_2))

            SubPoint(text = stringResource(R.string.setup_done_2_3))

            SubNote(text = stringResource(R.string.setup_done_2_3_tip))

            AddTileButton(
                label = stringResource(R.string.hide_tile_label),
                component = { context -> ComponentName(context, HideTileService::class.java) },
                icon = R.drawable.ic_hide_tile,
            )

            Point(text = stringResource(R.string.setup_done_3))

            SubPoint(text = stringResource(R.string.setup_done_3_1))

            SubPoint(text = stringResource(R.string.setup_done_3_2))

            AddTileButton(
                label = stringResource(R.string.services_shortcut_label),
                component = { context -> ComponentName(context, ServicesTileService::class.java) },
                icon = R.drawable.ic_services_tile,
            )

            Point(text = stringResource(R.string.setup_done_4))

            SubPoint(text = stringResource(R.string.setup_done_4_1))

            SubPoint(text = stringResource(R.string.setup_done_4_2))

            SubPoint(text = stringResource(R.string.setup_done_4_3))

            SubPoint(text = stringResource(R.string.setup_done_4_4))

            // ⚠ **At the end of the body, not in the footer.** The footer is the signature at
            // the left and "Let's go" at the right, which is the layout approved from a
            // template; a third control wedged in beside them would be redrawing that without
            // asking. Back belongs to whoever goes looking for it.
            if (onBack != null) {
                TextButton(
                    modifier = Modifier.padding(top = 12.dp),
                    onClick = onBack,
                ) {
                    Text(text = stringResource(R.string.setup_back))
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }

        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(vertical = 12.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text(
                text = stringResource(R.string.setup_done_signature),
                style = MaterialTheme.typography.bodyMedium,
                color = MaterialTheme.colorScheme.onSurfaceVariant,
            )

            Button(onClick = onContinue) {
                Text(text = stringResource(R.string.setup_done_go))
            }
        }
    }
}

/** One of the four numbered points. */
@Composable
private fun Point(text: String) {
    Text(
        modifier = Modifier.padding(top = 12.dp),
        text = text,
        // ⚠ **A named style one step up, not a literal size** — r4t. This page is the last thing
        // setup shows and the author found it small; every level moved together so it keeps its
        // hierarchy, and staying on the type scale is what keeps it following the user's own
        // font-size setting.
        style = MaterialTheme.typography.bodyLarge,
    )
}

/** One of a point's own numbered items, indented under it. */
@Composable
private fun SubPoint(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 6.dp),
        text = text,
        style = MaterialTheme.typography.bodyLarge,
    )
}

/** The parenthesised aside under 2.3, quieter than the item it belongs to. */
@Composable
private fun SubNote(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 2.dp),
        text = text,
        // Still a step below the item it belongs to, which is what makes it an aside.
        style = MaterialTheme.typography.bodyMedium,
        color = MaterialTheme.colorScheme.onSurfaceVariant,
    )
}

/**
 * Asks Android to add one of IMD's tiles to the user's quick settings.
 *
 * ⚠ **Android 13 and up, and absent below it rather than dead.** `requestAddTileService` arrives
 * in API 33 and there is no older equivalent - before that, adding a tile is something only the
 * user can do from the quick settings edit screen. A button that could never work is worse than
 * no button, so below 33 nothing is drawn and the line above it still describes the tile.
 *
 * ⚠ **The result callback is empty on purpose.** Every outcome is already in front of the user:
 * the system puts up its own confirmation, and the tile either appears or does not. A toast
 * afterwards would be the app narrating something they just watched.
 */
@Composable
private fun AddTileButton(
    label: String,
    component: (Context) -> ComponentName,
    icon: Int,
) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return

    val context = LocalContext.current

    FilledTonalButton(
        modifier = Modifier.padding(start = 20.dp, top = 8.dp),
        onClick = {
            val statusBar = context.getSystemService(StatusBarManager::class.java) ?: return@FilledTonalButton

            statusBar.requestAddTileService(
                component(context),
                label,
                Icon.createWithResource(context, icon),
                // ⚠ A real executor. Written as `{}` this compiles - Kotlin lets a
                // single-parameter lambda omit its parameter - and is an Executor that takes a
                // Runnable and never runs it, so the callback below could never fire. Harmless
                // while that callback does nothing, and exactly the kind of thing that gets
                // copied somewhere it matters.
                context.mainExecutor,
                // Deliberately empty: the system puts up its own confirmation, and the tile
                // either appears in the user's quick settings or does not. A message here would
                // be the app narrating something they just watched.
                {},
            )
        },
    ) {
        Text(text = stringResource(R.string.setup_done_add_tile))
    }
}
