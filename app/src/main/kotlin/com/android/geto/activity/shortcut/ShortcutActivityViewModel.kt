/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.activity.shortcut

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.HidingFramework
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.leftSettingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.OverlayStart
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ShortcutActivityViewModel @Inject constructor(
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val applySettingsToHideUseCase: ApplySettingsToHideUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
    shizukuStartTracker: ShizukuStartTracker,
) : ViewModel() {
    /**
     * The overlay Shizuku start, so a shortcut can show the same spinner the app does.
     *
     * A shortcut opens over whatever the user was looking at and its own window is
     * transparent, so ten seconds spent starting Shizuku to hide overlay access looked like
     * a tap that did nothing. Only the hide direction reaches a shortcut - a shortcut applies
     * settings, it never reverts - so the restore case is left where it was, inside the app.
     */
    val overlayStart = shizukuStartTracker.overlayStart.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null as OverlayStart?,
    )
    private val _shortcutActivityUiState =
        MutableStateFlow<ShortcutActivityUiState>(ShortcutActivityUiState.Loading)
    val shortcutActivityUiState = _shortcutActivityUiState.asStateFlow()

    /**
     * The theme, for the one case where this activity draws anything.
     *
     * Null until the first read lands, which the activity reads as "follow the system" — a
     * momentary wrong theme beats a blank frame while a preference file is opened.
     */
    val userData = userDataRepository.userData.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null as UserData?,
    )

    /**
     * A pinned shortcut hides whatever the current mode says to hide, then opens the app.
     *
     * The same choice the two tabs make, and it has to be the same one: a shortcut is
     * created from those tabs and is expected to behave like tapping the row it was made
     * from. Under Revert to default that means the device-wide list, so a shortcut for an
     * app with no profile works rather than landing on the "nothing configured" screen.
     */

    /**
     * The popup's two answers, both of which end in this launch running again.
     *
     * ⚠ **Restore only goes on if the device is actually clear.** `flushPendingReverts` reports
     * that from what the revert said *and* what the records say afterwards. A revert that could
     * not put Shizuku or overlay access back has already raised its own notification, so the
     * launch is abandoned rather than adding a second one saying the same thing.
     *
     * ⚠ **Ignore is permanent**: the old record is thrown away and the device is taken as it
     * stands. The button says so.
     */
    fun restoreThenApply(componentName: String) {
        appScope.launch {
            // The shortcut's window is transparent, so without this the user answers a
            // dialog, it disappears, and nothing at all is on screen while the device changes.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) {
                applyAppSettings(componentName = componentName)
            }
        }
    }

    fun discardThenApply(componentName: String) {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            applyAppSettings(componentName = componentName)
        }
    }

    fun applyAppSettings(componentName: String) {
        viewModelScope.launch {
            val userData = userDataRepository.userData.first()

            val hidingFramework = userData.hidingFramework

            val unhidingFramework = userData.unhidingFramework

            // ⚠ **Read before the apply, and that is the whole of it** — afterwards the answer
            // is always yes. True means this launch is arriving into a window something else
            // already hid: another app, a tile press, or IMD+. The debt becomes one shared
            // debt from here, so the per-app notifications are replaced by a single generic
            // one and auto unhide waits for the last of them rather than reverting each app as
            // its own session ends. See AutoUnhideWatch.collapse.
            val collapsed = userData.autoHideRunning || userData.settingsHidden

            val appSettingsResult = when (hidingFramework) {
                HidingFramework.ImdDefaults -> applySettingsToHideUseCase()

                HidingFramework.PerApp -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }

            AutoUnhideWatch.armIfApplied(
                applied = appSettingsResult.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
                collapsed = collapsed,
            )

            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)

            _shortcutActivityUiState.update {
                ShortcutActivityUiState.Success(
                    appSettingsResult = appSettingsResult,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
            }
        }
    }
}
