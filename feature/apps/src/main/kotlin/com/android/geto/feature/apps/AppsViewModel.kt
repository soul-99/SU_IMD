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
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetLauncherAppsActivityInfosUseCase
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
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
    val notificationFunction = userDataRepository.userData
        .map { it.notificationFunction }
        .stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000),
            NotificationFunction.Default,
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
            val notificationFunction = userDataRepository.userData.first().notificationFunction

            val result = when (notificationFunction) {
                NotificationFunction.RevertToDefault -> applySettingsToHideUseCase()

                NotificationFunction.Memory -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }

            val icon = packageManagerWrapper.getActivityIcon(componentName = componentName)

            _appLaunch.update {
                FavouriteAppLaunch(
                    componentName = componentName,
                    result = result,
                    icon = icon,
                    notificationFunction = notificationFunction,
                )
            }
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
