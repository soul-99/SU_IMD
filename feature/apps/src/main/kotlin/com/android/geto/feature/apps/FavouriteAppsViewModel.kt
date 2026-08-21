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
import com.android.geto.domain.model.FavouriteAppsTapAction
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.GetFavouriteAppsUseCase
import com.android.geto.domain.usecase.ManualRevertUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class FavouriteAppsViewModel @Inject constructor(
    getFavouriteAppsUseCase: GetFavouriteAppsUseCase,
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val manualRevertUseCase: ManualRevertUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
) : ViewModel() {
    private val _textFlow = MutableStateFlow<String?>(null)

    private val _appLaunch = MutableStateFlow<FavouriteAppLaunch?>(null)
    val appLaunch = _appLaunch.asStateFlow()

    private val _manualRevert = MutableStateFlow(ManualRevertState())
    val manualRevertState = _manualRevert.asStateFlow()

    val favouriteAppsUiState =
        getFavouriteAppsUseCase(textFlow = _textFlow).map(FavouriteAppsUiState::Success).stateIn(
            viewModelScope,
            SharingStarted.WhileSubscribed(5000),
            FavouriteAppsUiState.Loading,
        )

    /**
     * Applies the app's configured settings before it is opened, so a tap on the
     * Favourites tab behaves exactly like the launch arrow on the per-app screen or a
     * pinned shortcut. Opening the app without applying them would silently defeat the
     * whole point of having it here.
     */
    fun launchApp(componentName: String) {
        viewModelScope.launch {
            val result = applyAppSettingsUseCase(componentName = componentName)

            // Fetched before the update: update re-runs its block on a compare-and-set
            // failure, and getActivityIcon is a real binder call.
            val icon = packageManagerWrapper.getActivityIcon(componentName = componentName)

            _appLaunch.update {
                FavouriteAppLaunch(
                    componentName = componentName,
                    result = result,
                    icon = icon,
                )
            }
        }
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

    fun updateFavouriteAppsTapAction(favouriteAppsTapAction: FavouriteAppsTapAction) {
        viewModelScope.launch {
            userDataRepository.updateFavouriteAppsTapAction(favouriteAppsTapAction = favouriteAppsTapAction)
        }
    }

    fun updateFavouriteComponentNames(componentNames: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateFavouriteComponentNames(componentNames = componentNames)
        }
    }

    /**
     * The ticked set is the persisted one, so closing and reopening the dialog — or
     * killing the app — comes back to the same selection.
     */
    fun toggleManualRevertTarget(target: ManualRevertTarget, current: Set<ManualRevertTarget>) {
        viewModelScope.launch {
            val updated = if (target in current) current - target else current + target

            userDataRepository.updateManualRevertTargets(targets = updated)
        }
    }

    fun revertNow(targets: Set<ManualRevertTarget>) {
        if (targets.isEmpty() || _manualRevert.value.busy) return

        viewModelScope.launch {
            _manualRevert.update { ManualRevertState(busy = true, requested = targets.size) }

            val result = manualRevertUseCase(targets = targets)

            _manualRevert.update {
                ManualRevertState(busy = false, result = result, requested = targets.size)
            }
        }
    }

    /** The per-row button. Runs one target and leaves the ticked set alone. */
    fun revertOneNow(target: ManualRevertTarget) {
        revertNow(targets = setOf(target))
    }

    fun consumeManualRevertResult() {
        _manualRevert.update { it.copy(result = null, requested = 0) }
    }
}
