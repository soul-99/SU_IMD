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
package com.android.geto.activity.hide

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.getValue
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.common.AppLocale
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.designsystem.theme.GetoBlurSettings
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.domain.model.Theme
import com.android.geto.feature.apps.NothingToHideDialog
import com.android.geto.feature.apps.PermissionsLostDialog
import dagger.hilt.android.AndroidEntryPoint

/**
 * Names the dialog this window should draw, if any.
 *
 * `internal` rather than file-private: `HideTileService` is the only thing that sets it and it
 * lives in another file, and a `private` top-level declaration is visible to its own file alone.
 */
internal const val HIDE_EXTRA_DIALOG = "hide_dialog"

/**
 * The two things a tile press can still have to say for itself.
 *
 * Carried through the intent by [Enum.name] rather than as a serialised enum, which is the one
 * form that cannot break when a value is added or the class is minified differently on either
 * side. An unknown or missing name means "draw nothing", which is what an ordinary press wants.
 *
 * Top level rather than nested, for the same mundane reason `SettingsWorkKind` is: `check16_when`
 * cannot read an indented enum — it needs the closing brace at column 0.
 */
internal enum class HideDialog {
    /** Nothing is ticked in "Settings to hide", so there was nothing a press could do. */
    NothingToHide,

    /** `WRITE_SECURE_SETTINGS` has gone, so nothing this app writes can land anywhere. */
    PermissionsLost,
}

/**
 * What closes the notification shade, and the two dialogs a tile press can still put on screen.
 *
 * Since Android 12 an app cannot collapse the shade by asking; the only way is to launch an
 * activity from a Quick Settings tile, and this is the activity that launch names. Usually it
 * opens and closes again in the same breath, drawing nothing at all.
 *
 * **It used to run the press as well, and drew three things while it did**: a spinner for the
 * ten seconds a hide can spend waiting on Shizuku, and a dialog each for the two outcomes worth
 * saying something about. The spinner is gone and so is the overlay-failure dialog, for one
 * reason. The author asked for the shade to stay open through the press — the tile itself reads
 * "Hiding settings…" or "Unhiding settings…" and is dimmed for exactly as long as the work runs,
 * which is a better progress indicator than a spinner over a screen nobody can see behind the
 * shade — and to close a second after a press that worked. That makes the collapse the last step
 * instead of the first, and a window that only opens at the end cannot be the window the work
 * happens in. The work moved to
 * [com.android.geto.broadcastreceiver.SettingsHiddenRunner.toggle], and a press that fails
 * deliberately leaves the shade open and says so there — see `HideTileNotification`.
 *
 * ⚠ **Two outcomes are the exception, and both collapse the shade before they speak.**
 * "Nothing ticked to hide" keeps the behaviour it always had, on the author's instruction: it is
 * not a failure, nothing went wrong, the app is pointing out that nothing has been set up yet
 * and saying where to set it. A lost `WRITE_SECURE_SETTINGS` grant *is* a failure, and collapses
 * anyway — also on the author's instruction — because it is the one failure that stops every
 * route in the app at once, and the shade is not where somebody should have to read that.
 *
 * Neither waits the second a successful press waits. Both return in a moment and neither moves
 * the tile, so there is nothing to hold the shade open to watch.
 *
 * **Being invisible is a feature, and it takes three things.** `Theme.Geto.Tile` switches off the
 * background dim and the starting preview, and [finishSilently] switches off the exit transition.
 * Any one of them left on and an ordinary press greys the whole screen for a fraction of a second
 * on its way past.
 */
@AndroidEntryPoint
class HideActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    private val viewModel: HideViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val dialog = intent.dialog()

        if (dialog == null) {
            finishSilently()

            return
        }

        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            GetoTheme(
                theme = userData?.theme ?: Theme.FOLLOW_SYSTEM,
                dynamicTheme = userData?.dynamicTheme ?: false,
                oledBackground = userData?.oledBackground ?: false,
                blurSettings = GetoBlurSettings(
                    enabled = userData?.progressiveBlur ?: false,
                    radiusDp = userData?.blurRadiusDp ?: DEFAULT_RADIUS_DP,
                    tintPercent = userData?.blurTintPercent ?: DEFAULT_TINT_PERCENT,
                    fadeDp = userData?.blurFadeDp ?: DEFAULT_FADE_DP,
                ),
            ) {
                when (dialog) {
                    HideDialog.NothingToHide -> NothingToHideDialog(onDismissRequest = ::finish)

                    HideDialog.PermissionsLost -> PermissionsLostDialog(onDismissRequest = ::finish)
                }
            }
        }
    }

    /**
     * A second press arriving while the dialog is still up.
     *
     * `singleTop` means the platform delivers it here rather than building a second window, and
     * `onCreate` does not run again — so without this, a later press that merely wants the shade
     * closed would leave the earlier dialog standing, now describing a device that has since
     * been configured. Another nothing-to-hide press is the same dialog and is left alone.
     */
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)

        setIntent(intent)

        if (intent.dialog() == null) finishSilently()
    }

    private fun Intent.dialog(): HideDialog? {
        val name = getStringExtra(HIDE_EXTRA_DIALOG) ?: return null

        return HideDialog.entries.firstOrNull { it.name == name }
    }

    /**
     * Close with no transition either way.
     *
     * The usual press draws nothing at all, so the only thing an animation can animate is an
     * empty window sliding over whatever the user was looking at - which is exactly the flicker
     * this window is trying not to be. The theme suppresses the enter animation; this is the
     * other half.
     */
    private fun finishSilently() {
        finish()

        overridePendingTransitionCompat()
    }

    @Suppress("DEPRECATION")
    private fun overridePendingTransitionCompat() {
        overridePendingTransition(0, 0)
    }
}
