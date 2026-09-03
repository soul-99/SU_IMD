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
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.service.quicksettings.TileService
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
import com.android.geto.feature.apps.PermissionsLostDialog
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
    /**
     * What the app icon on the dialog's title line does.
     *
     * ⚠ **The two callers answer it differently, and that is the point of it being here.** Over
     * somebody else's app it has to start IMD and then close this window, in that order; on the
     * Favourites tab IMD is already behind the dialog, so closing the dialog is the whole of it.
     */
    onOpenImdApp: () -> Unit,
    viewModel: SettingsManagerViewModel = hiltViewModel(),
) {
    val context = LocalContext.current

    val states by viewModel.targetStates.collectAsStateWithLifecycle()

    val shizukuLaunchPackage by viewModel.shizukuLaunchPackage.collectAsStateWithLifecycle()

    val shizukuStarting by viewModel.shizukuStarting.collectAsStateWithLifecycle()

    val shizukuStartFailed by viewModel.shizukuStartFailed.collectAsStateWithLifecycle()

    val overlayRestoreFailed by viewModel.overlayRestoreFailed.collectAsStateWithLifecycle()

    val manageShizuku by viewModel.manageShizuku.collectAsStateWithLifecycle()

    val managerRows by viewModel.managerRows.collectAsStateWithLifecycle()

    val overlayBlocked by viewModel.overlayBlocked.collectAsStateWithLifecycle()

    val isShevery by viewModel.isShevery.collectAsStateWithLifecycle()

    val sheveryWait by viewModel.sheveryWait.collectAsStateWithLifecycle()

    val serviceStarting by viewModel.serviceStarting.collectAsStateWithLifecycle()

    val overlayWriteInFlight by viewModel.overlayWriteInFlight
        .collectAsStateWithLifecycle()

    val infoShown by viewModel.infoShown.collectAsStateWithLifecycle()

    val settingsWork by viewModel.settingsWork.collectAsStateWithLifecycle()

    val settingsWorkInFlight by viewModel.settingsWorkInFlight
        .collectAsStateWithLifecycle()

    val permissionsLost by viewModel.permissionsLost.collectAsStateWithLifecycle()

    val anythingHidden by viewModel.anythingHidden.collectAsStateWithLifecycle()

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
        // Was hardcoded false, which meant the parameter existed and did nothing: every row
        // here stayed pressable while a hide or a revert was running somewhere else, and a
        // press landing mid-change started a second change over the top of the first.
        busy = settingsWorkInFlight,
        settingsWork = settingsWork,
        shizukuStarting = shizukuStarting,
        shizukuStartFailed = shizukuStartFailed,
        overlayRestoreFailed = overlayRestoreFailed,
        overlayWriteInFlight = overlayWriteInFlight,
        manageShizuku = manageShizuku,
        managerRows = managerRows,
        overlayBlocked = overlayBlocked,
        isShevery = isShevery,
        sheveryWait = sheveryWait,
        serviceStarting = serviceStarting,
        infoShown = infoShown,
        anythingHidden = anythingHidden,
        onInfoShown = viewModel::markInfoShown,
        onDismissRequest = onDismissRequest,
        onOpenImdApp = onOpenImdApp,
        // A plain forward now. It used to raise the Shizuku wait toast alongside, which the
        // author removed — the switch flipping back while a slow fork starts is explained by
        // the switch itself and by the manager's own busy state.
        onSetEnabled = { target, enabled ->
            viewModel.setTargetEnabled(target, enabled)
        },
        // The dialog hands over the rows it considers operable, so the pill moves exactly
        // what the user could have moved by hand and nothing else.
        onSetAll = { enabled, targets ->
            viewModel.setAllTargets(enabled = enabled, targets = targets)
        },
        onOpen = { target ->
            context.openTarget(
                target = target,
                shizukuPackage = shizukuLaunchPackage,
                // Only meaningful for the wireless row, and read here rather than inside
                // `openTarget` so that function stays a pure intent-builder with no opinion
                // about where the device's state comes from.
                wirelessDebuggingOn = states.isEnabled(
                    ManualRevertTarget.WirelessDebugging,
                ),
            )
        },
        // Not a revert to default: this settles what is actually outstanding and says so
        // when nothing is. See the ViewModel.
        onUnhideSettings = viewModel::unhideSettings,
        // The other half of the same button. Which one a press reaches is decided by
        // `anythingHidden`, one floor up, from the value that also picks the label.
        onHideSettings = viewModel::hideSettings,
        // Straight to the turn-off path: cancelling a start and switching the service off are
        // the same behaviour, so they are the same call.
        onCancelShevery = viewModel::cancelSheveryService,
        onRevertToDefault = viewModel::revertToDefault,
        onOpenRevertConfiguration = {
            // ⚠ **Started first, dismissed second — r5, and the order is the whole of it.**
            // This used to dismiss first, on the reasoning that the dialog is the thing being
            // navigated away from. That reasoning holds; the ordering it produced does not.
            // Opened from the tile this dialog is a translucent activity in a task of its own,
            // and asking the window manager to tear that task down in the same breath as
            // raising another one is a race — which the author saw on the icon beside this one
            // as IMD arriving *behind* the manager. Starting while this window is still up
            // leaves one ordinary transition to draw and nothing to get wrong.
            context.openRevertConfiguration()

            onDismissRequest()
        },
    )

    // Over the manager rather than inside it, so the row the user pressed stays visible
    // behind the explanation. A switch that moves and springs straight back is the least
    // legible failure this screen can produce, and a lost grant makes every row do it.
    if (permissionsLost) {
        PermissionsLostDialog(onDismissRequest = viewModel::dismissPermissionsLost)
    }
}

/**
 * Opens the system screen or app behind one row.
 *
 * Developer options are the awkward one: when they have never been enabled the settings
 * activity is not exported on many builds, so the launch throws and there is nothing
 * useful to fall back to — the user has to go and turn them on themselves, which is what
 * the toast says.
 */
/** AOSP's preference keys for the two switches, which is what the highlight extras name. */
private const val USB_DEBUGGING_KEY = "enable_adb"

private const val WIRELESS_DEBUGGING_KEY = "toggle_adb_wireless"

/** The three rows that open Developer options, and so share one reason for failing to. */
private val DEVELOPER_OPTIONS_TARGETS = setOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * Developer options, scrolled to one of its preferences and with that preference flashed.
 *
 * ⚠ **Both extras, and both are needed.** The Settings app reads `:settings:fragment_args_key`
 * to decide what to highlight and `:settings:show_fragment_args` to pass the same key down to
 * the fragment it opens; supplying only one gets the page without the highlight on most builds.
 * Neither is public API - they are the keys Settings has used since Android 7 and the ones every
 * "open this exact toggle" link on the platform uses - so this is best-effort by construction.
 * An unrecognised extra is dropped, which leaves the page, and the page was the fallback anyway.
 */
/**
 * The Settings app's own Wireless debugging screen — pairing code, port, paired devices.
 *
 * ⚠ **An internal component name, and that is the whole risk.** Android has an action for
 * Developer options and none for this page, so the only way in is the activity Settings
 * declares for it. Right on AOSP and on most OEM builds; not a promise. Whether it works is
 * asked by starting it, not by resolving it - see the loop in [openTarget].
 */
private fun wirelessDebuggingPage(): Intent = Intent().setClassName(
    "com.android.settings",
    "com.android.settings.Settings\$AdbWirelessSettingsActivity",
)

/**
 * The same screen, reached the way Shizuku reaches it — and the way that works where ours did not.
 *
 * ⚠ **The difference is who resolves the name.** [wirelessDebuggingPage] starts a Settings
 * activity by its exact class, so one OEM rename and the start throws — which is what the author
 * saw on both of his devices. This asks the Settings app for *"the preferences screen belonging to
 * this quick-settings tile"* and names a class from the platform's own development-tiles set,
 * which survives OEM reshuffling far more often than the Settings activity aliases do. Settings
 * itself then finds the screen, on the device, with its own knowledge of where it lives.
 *
 * Taken from Shizuku 13.7.0 (thedjchi), `moe.shizuku.manager.utils.SettingsPage`, which the author
 * supplied precisely because its button works where this one did not.
 *
 * ⚠ **Its `FLAG_ACTIVITY_CLEAR_TASK` is not copied.** That is right for a standalone launcher and
 * wrong here: this link is pressed from a dialog floating over somebody else's app, and clearing
 * the task would take that app with it. [openTarget]'s own `FLAG_ACTIVITY_NEW_TASK` is what every
 * other row uses and is what this uses too.
 *
 * Still not public API, and still asked by starting it rather than by resolving it.
 */
private fun wirelessDebuggingTilePage(): Intent {
    val settings = "com.android.settings"

    return Intent(TileService.ACTION_QS_TILE_PREFERENCES)
        .setPackage(settings)
        .putExtra(
            Intent.EXTRA_COMPONENT_NAME,
            ComponentName(
                settings,
                "$settings.development.qstile.DevelopmentTiles\$WirelessDebugging",
            ),
        )
}

private fun developerOptionsAt(key: String): Intent =
    Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
        .putExtra(":settings:fragment_args_key", key)
        .putExtra(
            ":settings:show_fragment_args",
            Bundle().apply { putString(":settings:fragment_args_key", key) },
        )

internal fun Context.openTarget(
    target: ManualRevertTarget,
    shizukuPackage: String?,
    wirelessDebuggingOn: Boolean = false,
) {
    // ⚠ **A list, because one row has a second-best answer.** Every other target has exactly
    // one place to go; wireless debugging has a real screen of its own whose activity name is
    // internal, so it offers that first and r4h's highlighted Developer options behind it.
    val candidates = when (target) {
        ManualRevertTarget.DeveloperSettings -> {
            listOf(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))
        }

        // ⚠ **Android publishes no intent for either of these screens.** They are preferences
        // inside Developer options, and `Settings` has a constant for the page and none for
        // the rows. Both therefore open that page with the platform's own scroll-to-and-
        // highlight extras aimed at the preference; where a Settings app ignores them the
        // user lands on Developer options, which is the author's own fallback.
        ManualRevertTarget.UsbDebugging -> listOf(developerOptionsAt(key = USB_DEBUGGING_KEY))

        // ⚠ **The page first, but only while the setting is on** - the author's condition, and
        // the sensible one: switched off, that screen holds nothing but the switch the user
        // has just come from. The component name is internal and may be renamed, removed or
        // guarded by a vendor, so the highlighted page stands behind it.
        // ⚠ **Three candidates since r4y, and the new one is first.** Shizuku's tile-preferences
        // route asks the Settings app to find this screen instead of naming its activity, which
        // is why its button works on devices where ours fell through to Developer options — the
        // author's report, and his source. See wirelessDebuggingTilePage.
        //
        // ⚠ **Both routes keep the author's r4h condition**: with the setting off that screen
        // holds nothing but the switch he has just come from, so the highlighted Developer
        // options page is the better landing. One `takeIf` each if that should change.
        ManualRevertTarget.WirelessDebugging -> listOfNotNull(
            wirelessDebuggingTilePage().takeIf { wirelessDebuggingOn },
            wirelessDebuggingPage().takeIf { wirelessDebuggingOn },
            developerOptionsAt(key = WIRELESS_DEBUGGING_KEY),
        )

        ManualRevertTarget.AccessibilityServices -> {
            listOf(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        ManualRevertTarget.DisplayOverOtherApps -> {
            listOf(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
        }

        ManualRevertTarget.Shizuku -> {
            listOfNotNull(shizukuPackage?.let(packageManager::getLaunchIntentForPackage))
        }

        else -> emptyList()
    }

    if (candidates.isEmpty()) {
        Toast.makeText(this, R.string.settings_manager_no_shizuku, Toast.LENGTH_SHORT).show()

        return
    }

    // ⚠ **Tried rather than resolved.** `resolveActivity` on an explicit component in another
    // package is subject to package visibility, so a perfectly good component can come back
    // null on API 30+ for a reason that has nothing to do with the device. Starting it and
    // catching the refusal asks the only question that matters.
    //
    // The fallback is silent: the user asked to see a settings screen, and landing one level
    // out is not worth a toast. The toast below is for nothing having opened at all.
    for (candidate in candidates) {
        val opened = runCatching {
            startActivity(candidate.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }.fold(
            onSuccess = { true },
            onFailure = {
                if (it !is ActivityNotFoundException && it !is SecurityException) throw it

                false
            },
        )

        if (opened) return
    }

    // All three debugging rows open the same page, so all three fail for the same reason:
    // developer options is switched off on this device.
    val message = if (target in DEVELOPER_OPTIONS_TARGETS) {
        R.string.settings_manager_enable_developer_options
    } else {
        R.string.settings_manager_cannot_open
    }

    Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
}

