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
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
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
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
) : ViewModel() {
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

    fun applyAppSettings(componentName: String) {
        viewModelScope.launch {
            val appSettingsResult = applyAppSettingsUseCase(componentName = componentName)

            val applicationIcon = packageManagerWrapper.getActivityIcon(componentName = componentName)

            val notificationFunction = userDataRepository.userData.first().notificationFunction

            _shortcutActivityUiState.update {
                ShortcutActivityUiState.Success(
                    appSettingsResult = appSettingsResult,
                    applicationIcon = applicationIcon,
                    notificationFunction = notificationFunction,
                )
            }
        }
    }
}
