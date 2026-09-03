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
package com.android.geto.activity.autohide

import android.content.Context
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.viewModels
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.ui.res.stringResource
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.broadcastreceiver.AutoHideOutcome
import com.android.geto.common.AppLocale
import com.android.geto.common.PriorHideRestore
import com.android.geto.common.AutoHideDetection
import com.android.geto.designsystem.theme.GetoTheme
import com.android.geto.designsystem.theme.GetoBlurSettings
import com.android.geto.domain.model.DEFAULT_FADE_DP
import com.android.geto.domain.model.DEFAULT_RADIUS_DP
import com.android.geto.domain.model.DEFAULT_TINT_PERCENT
import com.android.geto.domain.model.Theme
import com.android.geto.feature.apps.PermissionsLostDialog
import com.android.geto.designsystem.component.PriorHideDialog
import com.android.geto.designsystem.component.WaitingDialog
import com.android.geto.feature.apps.dialog.ShizukuStartingDialog
import com.android.geto.feature.settings.dialog.AutoHideNoProfileDialog
import com.android.geto.feature.settings.dialog.AutoHideNothingToHideDialog
import dagger.hilt.android.AndroidEntryPoint
import com.android.geto.common.R as commonR

/**
 * The window an Auto-hide settings (IMD+) run happens inside.
 *
 * Transparent nearly all of the time, and it exists for two reasons that have nothing to do
 * with what it draws:
 *
 * - **A run has to be able to open an app.** Starting an activity from the background is
 *   refused on Android 10 and up unless something exempts the caller. An enabled accessibility
 *   service is such an exemption — and the run deliberately switches its own off part-way
 *   through, so it cannot be the one relied on. A window of this app's own, already in front,
 *   always can.
 * - **The wait has to be visible.** A run can spend the fork's whole Shizuku budget bringing
 *   the shell up before the app it stopped comes back. Silence for that long, right after
 *   tapping an app icon, reads as the app having crashed.
 *
 * There is almost nothing to report at the end. A run either hides and reopens the app — in
 * which case the app itself is the confirmation, with the IMD+ notification behind it — or it
 * changes nothing and puts the app back. Neither wants a dialog on top of the app the user asked
 * for, so this closes silently, and the outcomes worth explaining are explained where the user
 * configured IMD+ rather than over the app they just opened.
 *
 * **Two outcomes break that rule**, and only because the rule's own reasoning does not reach
 * them: nothing configured to hide means no run at all, so nothing is stopped and nothing is
 * reopened — there is no arriving app to read as the answer, and no way to tell IMD+ staying out
 * of the way from IMD+ not working. Those two say so, and say where to fix it.
 *
 * They are two rather than one because the fix is in a different place in each mode: under
 * "Revert to default" it is the device-wide list in IMD's settings, and under the memory
 * function it is that app's own page, behind a long press on its icon.
 */
@AndroidEntryPoint
class AutoHideActivity : ComponentActivity() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    private val viewModel: AutoHideViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val packageName = intent.getStringExtra(AutoHideDetection.EXTRA_PACKAGE_NAME)

        // Nothing to run for. Closed rather than left standing: this window takes every touch
        // on whatever is behind it for as long as it is up.
        if (packageName.isNullOrBlank()) {
            finishSilently()

            return
        }

        viewModel.run(packageName = packageName)

        setContent {
            val userData by viewModel.userData.collectAsStateWithLifecycle()

            val finished by viewModel.finished.collectAsStateWithLifecycle()

            val outcome by viewModel.outcome.collectAsStateWithLifecycle()

            val overlayStart by viewModel.overlayStart.collectAsStateWithLifecycle()

            val priorHideRestoring by PriorHideRestore.running.collectAsStateWithLifecycle()

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
                if (finished) {
                    LaunchedEffect(Unit) { finishSilently() }
                } else if (outcome == AutoHideOutcome.NothingToHide) {
                    // The only things this window ever has to report. IMD+ did nothing - the
                    // app opened untouched - so there is no arriving app to read as the answer,
                    // and without a word the feature looks broken rather than unconfigured.
                    //
                    // Ahead of the spinner below because they are conclusions and the spinner
                    // is a wait: neither run reached anything Shizuku could be waited on for.
                    AutoHideNothingToHideDialog(
                        onDismissRequest = viewModel::dismissOutcome,
                    )
                } else if (outcome == AutoHideOutcome.PermissionsLost) {
                    // IMD+ runs behind the app the user just tapped, so this window is the only
                    // surface it has - and this is the one failure worth interrupting them for.
                    // The same dialog every other route shows, saying the same sentence.
                    PermissionsLostDialog(onDismissRequest = viewModel::dismissOutcome)
                } else if (outcome == AutoHideOutcome.NoProfile) {
                    // The memory function's version: the device-wide list is not what this mode
                    // reads, so it sends the reader to the app's own page instead.
                    AutoHideNoProfileDialog(
                        onDismissRequest = viewModel::dismissOutcome,
                    )
                } else if (outcome == AutoHideOutcome.HiddenFromPreviousUse) {
                    // Ahead of the spinner for the same reason as the three above: this is a
                    // conclusion, and IMD+ has not started anything to wait for yet. Both
                    // answers resume the run, so neither closes this window — which is what
                    // lets the spinner below show through while a restore waits on Shizuku.
                    PriorHideDialog(
                        title = stringResource(commonR.string.prior_hide_title),
                        restoreLabel = stringResource(commonR.string.prior_hide_restore),
                        ignoreLabel = stringResource(commonR.string.prior_hide_ignore),
                        onRestore = viewModel::restoreThenRun,
                        onIgnore = viewModel::discardThenRun,
                    )
                } else if (priorHideRestoring && overlayStart == null) {
                    // The restore the popup's first answer started. Behind the Shizuku spinner
                    // where both are true, since that one names the wait.
                    WaitingDialog(
                        text = stringResource(commonR.string.prior_hide_restoring),
                    )
                } else if (overlayStart != null) {
                    // ⚠ **The reason is passed through, and used to be discarded here.** This
                    // window collected `overlayStart` and then called the dialog with null,
                    // which says "Starting Shizuku service" whatever the wait is actually
                    // for - so a run held up *stopping* Shizuku told the user the opposite.
                    //
                    // The old argument for null was that IMD+ can wait on Shizuku twice and
                    // the user experiences one wait. That was written when every reason was a
                    // start; `OverlayStart` has carried StopShizuku and StartShizuku since,
                    // and a vaguer word is not the same thing as a wrong one. Every other
                    // surface - AppsScreen, FavouriteAppsScreen - has always passed it.
                    ShizukuStartingDialog(reason = overlayStart)
                }
            }
        }
    }

    /**
     * Close with no transition either way.
     *
     * The app being reopened is already arriving on screen behind this; an exit animation over
     * the top of it is a grey rectangle sliding across the app the user asked for. The theme
     * suppresses the enter animation, this is the other half.
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
