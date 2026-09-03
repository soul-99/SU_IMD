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

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.AutoHideOutcome
import com.android.geto.broadcastreceiver.AutoHideRunner
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.settingsHidden
import kotlinx.coroutines.flow.first
import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AutoHideViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val autoHideRunner: AutoHideRunner,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
    shizukuStartTracker: ShizukuStartTracker,
) : ViewModel() {
    /**
     * The overlay Shizuku start, so an IMD+ run shows the same spinner a shortcut launch does.
     *
     * A run can wait on Shizuku twice — once to force-stop the watched app, once for the hide's
     * own overlay step — and both are reported here as a hide, because from the user's side
     * they are one wait in the middle of one launch.
     */
    val overlayStart = shizukuStartTracker.overlayStart.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null as OverlayStart?,
    )

    /**
     * The theme, for the one thing this window ever draws.
     *
     * Null until the first read lands, which the activity reads as "follow the system" — a
     * momentary wrong theme beats a blank frame while a preference file is opened.
     */
    val userData = userDataRepository.userData.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null as UserData?,
    )

    private val _finished = MutableStateFlow(false)

    /** Set when the run is over, whatever it did. The window closes on it. */
    val finished = _finished.asStateFlow()

    private val _outcome = MutableStateFlow(AutoHideOutcome.Done)

    /**
     * What the run decided, when what it decided was worth saying.
     *
     * The outcomes that keep this window open, and the only ones. In two of the three IMD+ has
     * done nothing at all — the app was not stopped and not reopened, it simply started — so
     * unlike every other outcome there is no app arriving on screen to serve as the answer, and
     * no way for the user to tell a feature that decided to stay out of the way from one that
     * is broken.
     *
     * Which one it is decides which popup, because they send the reader to different places:
     * the device-wide list lives in IMD's settings, an app's own page behind a long press on
     * its icon, and a lost `WRITE_SECURE_SETTINGS` grant is fixed over adb and stops every
     * other route in the app at the same time.
     *
     * Held here rather than in the activity because the run outlives it: this survives the
     * rotation that recreates the window, exactly as [finished] does.
     */
    val outcome = _outcome.asStateFlow()

    /**
     * Guards against a second run. `onCreate` runs again on a configuration change and the
     * ViewModel survives it, so without this a rotation mid-run would start another.
     */
    private var started = false

    /** The app this window was opened for, kept so the popup's answers can resume its run. */
    @Volatile
    private var watched: String? = null

    /**
     * Runs on the application scope rather than [viewModelScope].
     *
     * The window closes the moment the run is done, and the run outlives it either way: it
     * force-stops an app, hides the settings, switches the detector off and opens the app
     * again. Tied to this ViewModel, closing the window would cut that sequence in half — and
     * half a run is a device with settings hidden and no app in front of the user.
     */
    fun run(packageName: String) {
        if (started) return

        started = true

        watched = packageName

        appScope.launch {
            // ⚠ **Asked before IMD+ does anything at all**, which is the author's instruction
            // and what makes both of the popup's answers mean the same here as on every other
            // surface: the app has not been force-stopped yet, so there is still a run to carry
            // on with. An earlier draft asked after the hide had already been refused.
            if (PriorHide.shouldWarn(userDataRepository.userData.first().settingsHidden)) {
                PriorHide.suppress()

                _outcome.update { AutoHideOutcome.HiddenFromPreviousUse }

                return@launch
            }

            hide()
        }
    }

    /**
     * The run itself, once nothing is standing in front of it.
     *
     * Extracted from [run] so the popup's two answers can reach it without going back through
     * the `started` guard, which has already done its job by then.
     */
    private suspend fun hide() {
        val packageName = watched ?: return

        // Declared outside the try so a run that throws still closes the window rather than
        // leaving it standing over the app, transparent and eating every touch.
        var result = AutoHideOutcome.Done

        try {
            result = autoHideRunner.run(packageName = packageName)
        } finally {
            if (result == AutoHideOutcome.Done) {
                _finished.update { true }
            } else {
                _outcome.update { result }
            }
        }
    }

    /**
     * Settle everything, then run IMD+ — but only if the device came out clear.
     *
     * ⚠ **A failed restore closes the window and leaves the app alone.** The notification
     * `RevertToDefaultRunner` raised is the report; IMD+ does not run, and [PriorHide] stays
     * suppressed so the next detection of the same app does not prompt again. Tapping *Try
     * again* on that notification restores from the debt, which clears it, which clears the
     * suppression — so the author's "IMD+ should run again once the user has sorted Shizuku out"
     * follows from the condition that actually matters.
     */
    fun restoreThenRun() {
        appScope.launch {
            _outcome.update { AutoHideOutcome.Done }

            // IMD+ draws over the app the user just opened, so this window is the only
            // surface the wait has.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) hide() else _finished.update { true }
        }
    }

    /** Throw the old record away, take the device as it stands, and run. Permanent. */
    fun discardThenRun() {
        appScope.launch {
            _outcome.update { AutoHideOutcome.Done }

            settingsHiddenRunner.discardPendingReverts()

            hide()
        }
    }

    /** The user has read it. Nothing was changed, so there is nothing to do but close. */
    fun dismissOutcome() {
        _finished.update { true }
    }
}
