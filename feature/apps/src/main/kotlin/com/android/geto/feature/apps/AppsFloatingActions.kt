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
package com.android.geto.feature.apps

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.size
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.SmallFloatingActionButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.theme.GetoRed
import com.android.geto.feature.apps.manager.SettingsManagerRoute
import com.android.geto.designsystem.R as designR

/**
 * The two buttons that hang over the app tabs: the settings manager, and put everything back.
 *
 * ⚠ **Drawn by the home scaffold, not by either tab — the author's r12 instruction.** They used to
 * live inside Favourites, which meant they slid and faded with it on every tab change (*"do not
 * move them when swiping away from one tab to another"*) and were missing from All apps entirely
 * (*"keep these two buttons on both fav and all apps tabs"*). Outside the tab host they are one
 * pair, drawn once, that simply stays where it is while the tabs move underneath.
 *
 * ⚠ **Its own small view model, rather than reaching into the Favourites one.** Composed above the
 * navigation graph, `hiltViewModel()` would resolve against the *activity* rather than a tab's
 * back-stack entry - so asking for `FavouriteAppsViewModel` here would build a second copy of it,
 * loading the whole app list again to read one boolean. This one reads that boolean and calls the
 * same runner.
 */
@Composable
fun AppsFloatingActions(
    modifier: Modifier = Modifier,
    viewModel: AppsFloatingActionsViewModel = hiltViewModel(),
) {
    val anythingHidden by viewModel.anythingHidden.collectAsStateWithLifecycle()

    var showManagerDialog by rememberSaveable { mutableStateOf(false) }

    Row(
        modifier = modifier,
        horizontalArrangement = Arrangement.spacedBy(12.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // Left of the primary one, and smaller.
        //
        // ⚠ **`primary`, up from `secondaryContainer` — r30h, at the author's word.** It opens the
        // settings manager, whose own two buttons are `primary` as of the same round, and a third
        // green for the button that opens them was the thing he was looking at. What makes the
        // pair read as one prominent action with a way in beside it is size and position, and
        // neither of those changes: this is still the small one on the left.
        SmallFloatingActionButton(
            onClick = { showManagerDialog = true },
            containerColor = MaterialTheme.colorScheme.primary,
            contentColor = MaterialTheme.colorScheme.onPrimary,
        ) {
            // The Quick Settings tile artwork rather than two stacked Material icons: the tile,
            // the launcher shortcut and this button all open the same dialog, and looking like
            // each other is how that reads as one thing rather than three.
            Icon(
                modifier = Modifier.size(24.dp),
                painter = painterResource(designR.drawable.ic_services_glyph),
                contentDescription = stringResource(R.string.settings_manager_title),
            )
        }

        // The primary one, on the right, where a thumb lands.
        //
        // ⚠ **The Hide settings tile's open eye, not the revert arrow**, and red only when
        // something is owed: greyed reads as "this has nothing to do" where green reads as "press
        // me", and on a pair that exists for a device needing to be put back, the second is a lie
        // most of the time. Still pressable while greyed - the call underneath answers with a
        // toast, and a button that swallowed the press would leave the user with no idea whether
        // anything had happened.
        FloatingActionButton(
            onClick = viewModel::unhideSettings,
            containerColor = if (anythingHidden) {
                GetoRed
            } else {
                MaterialTheme.colorScheme.surfaceContainerHighest
            },
            contentColor = if (anythingHidden) {
                Color.White
            } else {
                MaterialTheme.colorScheme.onSurfaceVariant
            },
        ) {
            Icon(
                modifier = Modifier.size(24.dp),
                painter = painterResource(designR.drawable.ic_hide_glyph),
                contentDescription = stringResource(R.string.unhide_settings),
            )
        }
    }

    if (showManagerDialog) {
        SettingsManagerRoute(
            onDismissRequest = { showManagerDialog = false },
            // ⚠ **Nothing is started here, and that is correct.** This copy of the manager is open
            // over IMD itself, so the app the icon offers to open is already the thing behind the
            // dialog: closing it *is* opening the app.
            onOpenImdApp = { showManagerDialog = false },
        )
    }
}
