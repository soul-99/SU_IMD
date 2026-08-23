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
package com.android.geto.feature.apps.manager

import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.provider.Settings
import android.widget.Toast
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.common.openRevertConfiguration
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.feature.apps.R
import com.android.geto.feature.apps.dialog.AndroidSettingsManagerDialog

/**
 * The Android settings/services manager, wherever it is opened from.
 *
 * Public because two of its three entry points live outside this module: a Quick Settings
 * tile and a long-press shortcut, both of which show it over whatever the user was already
 * looking at. Keeping the wiring here rather than in each caller is what stops the tile and
 * the in-app dialog drifting apart.
 */
@Composable
fun SettingsManagerRoute(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
    viewModel: SettingsManagerViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val states by viewModel.targetStates.collectAsStateWithLifecycle()

    val shizukuLaunchPackage by viewModel.shizukuLaunchPackage.collectAsStateWithLifecycle()

    val shizukuStarting by viewModel.shizukuStarting.collectAsStateWithLifecycle()

    val shizukuStartFailed by viewModel.shizukuStartFailed.collectAsStateWithLifecycle()

    val accessibilityManaged by viewModel.accessibilityManaged.collectAsStateWithLifecycle()

    // Polling runs only while this is composed. DisposableEffect rather than
    // LaunchedEffect so it also stops on a back press or an outside tap, not just when the
    // composable leaves the tree.
    DisposableEffect(Unit) {
        viewModel.startWatching()

        onDispose {
            viewModel.stopWatching()

            // The red switch is a report on the last attempt. It has been shown; clearing it
            // here is what keeps it from greeting the user on every subsequent open, long
            // after it described anything current.
            viewModel.acknowledgeShizukuFailure()
        }
    }

    AndroidSettingsManagerDialog(
        modifier = modifier,
        states = states,
        busy = false,
        shizukuStarting = shizukuStarting,
        shizukuStartFailed = shizukuStartFailed,
        onDismissRequest = onDismissRequest,
        onSetEnabled = { target, enabled ->
            viewModel.setTargetEnabled(target, enabled)

            if (target == ManualRevertTarget.Shizuku && enabled) {
                context.showShizukuWaitToast()
            }
        },
        onOpen = { target ->
            context.openTarget(target = target, shizukuPackage = shizukuLaunchPackage)
        },
        onRevertToDefault = viewModel::revertToDefault,
        onOpenRevertConfiguration = {
            // Dismissed first. The dialog is the thing being navigated away from, and
            // leaving it standing over the settings screen it just opened would need
            // dismissing again before the configuration underneath could be used.
            onDismissRequest()

            context.openRevertConfiguration()
        },
        onAccessibilityUnmanaged = {
            Toast.makeText(
                context,
                R.string.settings_manager_accessibility_unmanaged,
                Toast.LENGTH_LONG,
            ).show()
        },
        accessibilityManaged = accessibilityManaged,
    )
}

/**
 * Opens the system screen or app behind one row.
 *
 * Developer options are the awkward one: when they have never been enabled the settings
 * activity is not exported on many builds, so the launch throws and there is nothing
 * useful to fall back to — the user has to go and turn them on themselves, which is what
 * the toast says.
 */
internal fun Context.openTarget(target: ManualRevertTarget, shizukuPackage: String?) {
    val intent = when (target) {
        ManualRevertTarget.DeveloperSettings -> {
            Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
        }

        ManualRevertTarget.AccessibilityServices -> {
            Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        }

        ManualRevertTarget.Shizuku -> {
            shizukuPackage?.let(packageManager::getLaunchIntentForPackage)
        }

        else -> null
    }

    if (intent == null) {
        Toast.makeText(this, R.string.settings_manager_no_shizuku, Toast.LENGTH_SHORT).show()

        return
    }

    runCatching {
        startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }.onFailure {
        if (it !is ActivityNotFoundException && it !is SecurityException) throw it

        val message = if (target == ManualRevertTarget.DeveloperSettings) {
            R.string.settings_manager_enable_developer_options
        } else {
            R.string.settings_manager_cannot_open
        }

        Toast.makeText(this, message, Toast.LENGTH_LONG).show()
    }
}

/**
 * Shizuku's own start is not instant on every fork — Shevery in particular takes a few
 * seconds to come up after the broadcast — and the switch flipping back to off in the
 * meantime looks exactly like a failure. Saying so up front is cheaper than making the
 * poll lie about it.
 */
internal fun Context.showShizukuWaitToast() {
    Toast.makeText(this, R.string.settings_manager_shizuku_wait, Toast.LENGTH_LONG).show()
}
