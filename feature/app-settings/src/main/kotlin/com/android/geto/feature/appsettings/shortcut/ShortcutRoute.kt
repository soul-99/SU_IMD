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
package com.android.geto.feature.appsettings.shortcut

import android.widget.Toast
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.domain.model.GetPinShortcutResult
import com.android.geto.domain.model.RequestPinShortcutResult
import com.android.geto.feature.appsettings.R
import com.android.geto.feature.appsettings.dialog.RequestPinShortcutDialog
import com.android.geto.feature.appsettings.dialog.UpdatePinShortcutDialog

/**
 * The create-shortcut dialog for one app, wherever it is opened from.
 *
 * Public and self-contained for the same reason [com.android.geto.feature.apps.manager]'s
 * manager route is: creating a shortcut is now a long press on an app in either tab, and
 * those live in another module. Keeping the use-case wiring in one place is what stops the
 * two entry points drifting from the one on the app-settings screen.
 *
 * Whether this shows "create" or "edit" is not the caller's business — it is decided by
 * whether a pinned shortcut for this component already exists, which only the use case can
 * answer.
 */
@Composable
fun ShortcutRoute(
    modifier: Modifier = Modifier,
    componentName: String,
    activityLabel: String,
    onDismissRequest: () -> Unit,
    viewModel: ShortcutViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val target by viewModel.target.collectAsStateWithLifecycle()

    val requestResult by viewModel.requestPinShortcutResult.collectAsStateWithLifecycle()

    LaunchedEffect(componentName) {
        viewModel.start(componentName = componentName)
    }

    // A launcher that cannot pin is the one outcome the user has to be told about: nothing
    // appears on the homescreen and nothing else would explain why. The supported case
    // needs no message, because the launcher puts up its own confirmation.
    LaunchedEffect(requestResult) {
        when (requestResult) {
            RequestPinShortcutResult.UnsupportedLauncher -> {
                Toast.makeText(
                    context,
                    R.string.unsupported_launcher,
                    Toast.LENGTH_LONG,
                ).show()

                viewModel.consumeRequestResult()

                onDismissRequest()
            }

            RequestPinShortcutResult.SupportedLauncher -> {
                viewModel.consumeRequestResult()

                onDismissRequest()
            }

            null -> Unit
        }
    }

    // Nothing is drawn until the lookup for *this* app has landed. The ViewModel belongs
    // to the tab and outlives the dialog, so without this check the previous app's result
    // is what the first composition sees -- and the label fields, seeded once, keep it.
    val loaded = target?.takeIf { it.componentName == componentName } ?: return

    when (val result = loaded.result) {
        GetPinShortcutResult.RequestPinShortcut -> {
            RequestPinShortcutDialog(
                modifier = modifier,
                icon = loaded.icon,
                activityLabel = activityLabel,
                onDismissRequest = onDismissRequest,
                onRequestPinShortcut = { bytes, shortLabel, longLabel ->
                    viewModel.requestPinShortcut(
                        componentName = componentName,
                        icon = bytes,
                        shortLabel = shortLabel,
                        longLabel = longLabel,
                    )
                },
            )
        }

        is GetPinShortcutResult.UpdatePinShortcut -> {
            UpdatePinShortcutDialog(
                modifier = modifier,
                icon = loaded.icon,
                getoShortcutInfoCompat = result.getoShortcutInfoCompat,
                onDismissRequest = onDismissRequest,
                onUpdatePinShortcut = { bytes, shortLabel, longLabel ->
                    viewModel.updatePinShortcut(
                        componentName = componentName,
                        icon = bytes,
                        shortLabel = shortLabel,
                        longLabel = longLabel,
                    )

                    onDismissRequest()
                },
            )
        }

        // The launcher cannot pin anything. Nothing is drawn: a dialog that appears and
        // then reports that it cannot do what it was opened for is worse than silence, and
        // the toast above covers the case where the user has already pressed Add.
        GetPinShortcutResult.UnsupportedLauncher -> Unit
    }
}
