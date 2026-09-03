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
package com.android.geto.feature.apps

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.HidingFramework
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.leftSettingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetLauncherAppsActivityInfosUseCase
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AppsViewModel @Inject constructor(
    shizukuStartTracker: ShizukuStartTracker,
    getLauncherAppsActivityInfosUseCase: GetLauncherAppsActivityInfosUseCase,
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val applySettingsToHideUseCase: ApplySettingsToHideUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    /**
     * Whether a launch is currently waiting on Shizuku so it can hide overlay access.
     *
     * Read from the shared tracker rather than kept here, because the wait runs in an
     * application-scoped, non-cancellable block: it outlives this ViewModel if the user
     * switches tabs, and the spinner has to be right either way.
     */
    val overlayStart = shizukuStartTracker.overlayStart
    private var _textFlow = MutableStateFlow<String?>(null)

    private val _appLaunch = MutableStateFlow<FavouriteAppLaunch?>(null)
    val appLaunch = _appLaunch.asStateFlow()

    /**
     * Which mode the list is in, for deciding what a long press offers.
     *
     * Exposed on its own rather than folded into [appsUiState] because it changes nothing
     * about the list itself -- the rows, their order and their search are identical either
     * way, and only the gesture behind them differs.
     */
    val hidingFramework = userDataRepository.userData
        .map { it.hidingFramework }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000),
            HidingFramework.Default,
        )

    val appsUiState =
        getLauncherAppsActivityInfosUseCase(textFlow = _textFlow).map(AppsUiState::Success).stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000),
            AppsUiState.Loading,
        )

    /**
     * The same launch the Favourites tab performs, for the same reason: opening an app from
     * a list inside this app without first hiding what it objects to would look exactly
     * like the app not working.
     *
     * All apps could not launch anything before -- tapping a row opened its profile screen.
     * With one device-wide configuration there is no profile to open for most people, so
     * the tap has to do the useful thing instead.
     */
    fun launchApp(componentName: String) {
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

            val result = when (hidingFramework) {
                HidingFramework.ImdDefaults -> applySettingsToHideUseCase()

                HidingFramework.PerApp -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }

            AutoUnhideWatch.armIfApplied(
                applied = result.leftSettingsHidden,
                componentName = componentName,
                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
                collapsed = collapsed,
            )

            // Fetched before the update: update re-runs its block on a compare-and-set
            // failure, and getActivityLabel is a real binder call.
            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)

            _appLaunch.update {
                FavouriteAppLaunch(
                    componentName = componentName,
                    result = result,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
            }
        }
    }


    /**
     * The popup's two answers, both of which end in launching the app that raised it.
     *
     * ⚠ **Restore only goes on if the device is actually clear.** `flushPendingReverts` reports
     * that by looking at what the revert said *and* at what the records say afterwards. A revert
     * that could not put Shizuku or overlay access back has already raised its own notification
     * from `RevertToDefaultRunner`, so the launch is abandoned in silence rather than adding a
     * second one saying the same thing.
     *
     * ⚠ **Ignore is permanent.** It throws the old record away and takes the device as it
     * stands; nothing afterwards knows those settings were ever on. The button says so.
     *
     * On the application scope, not [viewModelScope]: a restore can wait on Shizuku for seconds
     * and the user may well leave the tab while it does.
     */
    fun restoreThenLaunch(componentName: String) {
        appScope.launch {
            // Wrapped so the screen can say what is happening: this call writes overlay
            // AppOps, the accessibility list, four settings and every per-app snapshot, and
            // the dialog that explained it has already gone.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) launchApp(componentName = componentName)
        }
    }

    fun discardThenLaunch(componentName: String) {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            launchApp(componentName = componentName)
        }
    }

    fun consumeAppLaunch() {
        _appLaunch.update { null }
    }

    fun search(text: String) {
        _textFlow.update { text }
    }

    fun updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo) {
        viewModelScope.launch {
            userDataRepository.updateSortLauncherAppsActivityInfo(sortLauncherAppsActivityInfo = sortLauncherAppsActivityInfo)
        }
    }

    fun updateSortOrderLauncherAppsActivityInfo(sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo) {
        viewModelScope.launch {
            userDataRepository.updateSortOrderLauncherAppsActivityInfo(
                sortOrderLauncherAppsActivityInfo = sortOrderLauncherAppsActivityInfo,
            )
        }
    }

    fun updateShowSystem(showSystem: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateShowSystem(showSystem = showSystem)
        }
    }

    fun updateFavourite(componentName: String, favourite: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateFavourite(
                componentName = componentName,
                favourite = favourite,
            )
        }
    }
}
