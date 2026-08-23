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
import com.android.geto.broadcastreceiver.RevertToDefaultRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetFavouriteAppsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import javax.inject.Inject
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

/**
 * Short enough to read as live, long enough that it is not doing anything expensive: the
 * reads behind it are in-process setting lookups and a binder ping, and it only runs while
 * the manager dialog is open.
 */
private const val TARGET_POLL_MILLIS = 500L

@HiltViewModel
class FavouriteAppsViewModel @Inject constructor(
    getFavouriteAppsUseCase: GetFavouriteAppsUseCase,
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val applySettingsToHideUseCase: ApplySettingsToHideUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val revertToDefaultRunner: RevertToDefaultRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    private val _textFlow = MutableStateFlow<String?>(null)

    private val _appLaunch = MutableStateFlow<FavouriteAppLaunch?>(null)
    val appLaunch = _appLaunch.asStateFlow()

    val favouriteAppsUiState =
        getFavouriteAppsUseCase(textFlow = _textFlow).map(FavouriteAppsUiState::Success).stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000),
            FavouriteAppsUiState.Loading,
        )

    /**
     * Hides whatever should be hidden before the app is opened, so a tap on the Favourites
     * tab behaves exactly like the launch arrow on the per-app screen or a pinned shortcut.
     * Opening the app without doing it would silently defeat the whole point.
     *
     * Which configuration decides that is the notification function's, because the two have
     * to agree: what is hidden on the way in is what the notification's button offers to
     * put back. Revert to default reads the one device-wide "Settings to hide" list, so an
     * app nobody has configured still opens; the memory function reads that app's own
     * profile, and having none is a real answer that the caller reports rather than
     * papering over.
     */
    fun launchApp(componentName: String) {
        viewModelScope.launch {
            // Read before applying, not after. Reading it afterwards would let a
            // preference changed in the intervening moment announce the launch under a
            // function other than the one that actually ran.
            val notificationFunction = userDataRepository.userData.first().notificationFunction

            val result = when (notificationFunction) {
                NotificationFunction.RevertToDefault -> applySettingsToHideUseCase()

                NotificationFunction.Memory -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }

            // Fetched before the update: update re-runs its block on a compare-and-set
            // failure, and getActivityIcon is a real binder call.
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

    /**
     * Puts the device back into the configured default.
     *
     * Launched on the application scope rather than [viewModelScope]: leaving the Favourites
     * tab — which is exactly what someone does after pressing this — would otherwise cancel
     * a revert that takes seconds, and can wait on adbd before it is finished.
     */
    fun revertToDefault() {
        appScope.launch { revertToDefaultRunner() }
    }

    /** Cleared once handled, so tapping the same app twice emits twice. */
    fun consumeAppLaunch() {
        _appLaunch.update { null }
    }

    fun search(text: String) {
        _textFlow.update { text }
    }

    fun updateSortFavouriteApps(sortFavouriteApps: SortFavouriteApps) {
        viewModelScope.launch {
            userDataRepository.updateSortFavouriteApps(sortFavouriteApps = sortFavouriteApps)
        }
    }

    fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        viewModelScope.launch {
            userDataRepository.updateFavouriteAppsView(favouriteAppsView = favouriteAppsView)
        }
    }

    fun updateFavouriteComponentNames(componentNames: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateFavouriteComponentNames(componentNames = componentNames)
        }
    }


}
