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
package com.android.geto.feature.settings

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.Theme
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.GetAccessibilityServicesUseCase
import com.android.geto.domain.usecase.GetInstalledAppsUseCase
import com.android.geto.service.SettingsObserverService
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted.Companion.WhileSubscribed
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val getAccessibilityServicesUseCase: GetAccessibilityServicesUseCase,
    private val getInstalledAppsUseCase: GetInstalledAppsUseCase,
) : ViewModel() {
    val settingsUiState = userDataRepository.userData.map(SettingsUiState::Success).stateIn(
        scope = viewModelScope,
        started = WhileSubscribed(5_000),
        initialValue = SettingsUiState.Loading,
    )

    val isServiceRunning = SettingsObserverService.isRunning.stateIn(
        scope = viewModelScope,
        started = WhileSubscribed(5_000),
        initialValue = false,
    )

    private val _accessibilityServices =
        MutableStateFlow<List<AccessibilityServiceData>>(emptyList())
    val accessibilityServices = _accessibilityServices.asStateFlow()

    private val _installedApps = MutableStateFlow<List<InstalledAppData>>(emptyList())
    val installedApps = _installedApps.asStateFlow()

    fun updateTheme(theme: Theme) {
        viewModelScope.launch {
            userDataRepository.updateTheme(theme = theme)
        }
    }

    fun updateDynamicTheme(dynamicTheme: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateDynamicTheme(dynamicTheme = dynamicTheme)
        }
    }

    fun updateRestartShizuku(restartShizuku: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateRestartShizuku(restartShizuku = restartShizuku)
        }
    }

    fun updateShizukuForkMode(shizukuForkMode: ShizukuForkMode) {
        viewModelScope.launch {
            userDataRepository.updateShizukuForkMode(shizukuForkMode = shizukuForkMode)
        }
    }

    fun updateShizukuAuthKey(shizukuAuthKey: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuAuthKey(shizukuAuthKey = shizukuAuthKey)
        }
    }

    fun updateShizukuPackageName(shizukuPackageName: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuPackageName(shizukuPackageName = shizukuPackageName)
        }
    }

    fun updateShizukuStartAction(shizukuStartAction: String) {
        viewModelScope.launch {
            userDataRepository.updateShizukuStartAction(shizukuStartAction = shizukuStartAction)
        }
    }

    fun updateManagedAccessibilityServices(components: List<String>) {
        viewModelScope.launch {
            userDataRepository.updateManagedAccessibilityServices(components = components)
        }
    }

    fun updateNotificationFunction(notificationFunction: NotificationFunction) {
        viewModelScope.launch {
            userDataRepository.updateNotificationFunction(notificationFunction = notificationFunction)
        }
    }

    fun updateRevertDefaults(states: Map<ManualRevertTarget, Boolean>) {
        viewModelScope.launch {
            userDataRepository.updateRevertDefaults(states = states)
        }
    }

    /**
     * Read on demand rather than observed. There is no content observer for the
     * installed-services list, and re-reading when the picker opens is both cheaper and
     * more accurate than a stale cached copy.
     */
    fun refreshAccessibilityServices() {
        viewModelScope.launch {
            _accessibilityServices.update { getAccessibilityServicesUseCase() }
        }
    }

    /**
     * Enumerating every installed package and rasterising an icon each is far too heavy to
     * do on the way into Settings, so the picker asks for it when it is first opened and
     * the answer is kept for the rest of the screen's life.
     */
    fun refreshInstalledApps() {
        if (_installedApps.value.isNotEmpty()) return

        viewModelScope.launch {
            _installedApps.update { getInstalledAppsUseCase() }
        }
    }
}
