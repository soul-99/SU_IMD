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
package com.android.geto.feature.appsettings

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.toRoute
import com.android.geto.domain.framework.AssetManagerWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import com.android.geto.domain.model.AddAppSettingResult
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingTemplate
import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.GetPinShortcutResult
import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.RequestPinShortcutResult
import com.android.geto.domain.model.SecureSetting
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.UpdatePinShortcutResult
import com.android.geto.domain.model.appSettingBlocked
import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.repository.AppSettingsRepository
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.AddAppSettingUseCase
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.GetPinShortcutUseCase
import com.android.geto.domain.usecase.GetSecureSettingsByNameUseCase
import com.android.geto.domain.usecase.RequestPinShortcutUseCase
import com.android.geto.domain.usecase.RevertAppSettingsUseCase
import com.android.geto.domain.usecase.UpdatePinShortcutUseCase
import com.android.geto.feature.appsettings.navigation.AppSettingsRouteData
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class AppSettingsViewModel @Inject constructor(
    savedStateHandle: SavedStateHandle,
    private val appSettingsRepository: AppSettingsRepository,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val applyAppSettingsUseCase: ApplyAppSettingsUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @param:ApplicationScope private val appScope: CoroutineScope,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val requestPinShortcutUseCase: RequestPinShortcutUseCase,
    private val addAppSettingUseCase: AddAppSettingUseCase,
    private val assetManagerWrapper: AssetManagerWrapper,
    private val getSecureSettingsByNameUseCase: GetSecureSettingsByNameUseCase,
    private val getPinShortcutUseCase: GetPinShortcutUseCase,
    private val shortcutManagerCompatWrapper: ShortcutManagerCompatWrapper,
    private val updatePinShortcutUseCase: UpdatePinShortcutUseCase,
    private val userDataRepository: UserDataRepository,
) : ViewModel() {
    private val appSettingsRouteData = savedStateHandle.toRoute<AppSettingsRouteData>()

    private val componentName = appSettingsRouteData.componentName

    private var _secureSettings = MutableStateFlow<List<SecureSetting>>(emptyList())
    val secureSettings = _secureSettings.asStateFlow()

    val isFavourite = userDataRepository.userData.map {
        componentName in it.favouriteComponentNames
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = false,
    )

    private var _activityIcon = MutableStateFlow<ByteArray?>(null)
    val activityIcon = _activityIcon.onStart {
        getActivityIcon()
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.Lazily,
        initialValue = null,
    )

    private val _addAppSettingsResult = MutableStateFlow<AddAppSettingResult?>(null)
    val addAppSettingsResult = _addAppSettingsResult.asStateFlow()

    private val _applyAppSettingsResult = MutableStateFlow<AppSettingsResult?>(null)
    val applyAppSettingsResult = _applyAppSettingsResult.asStateFlow()

    private val _revertAppSettingsResult = MutableStateFlow<AppSettingsResult?>(null)
    val revertAppSettingsResult = _revertAppSettingsResult.asStateFlow()

    private val _requestPinShortcutResult = MutableStateFlow<RequestPinShortcutResult?>(null)
    val requestPinShortcutResult = _requestPinShortcutResult.asStateFlow()

    // The stored rows, minus anything IMD cannot act on right now - Display over other apps
    // without a Thedjchi Shizuku to write the AppOp through, the Shizuku service with 'Manage
    // Shizuku' off, the accessibility flag with nothing in the picker.
    //
    // The filter is on the way to the screen only: the Room rows are untouched, so a row comes
    // straight back when the thing it needs is configured again, in this app and every other
    // it was added to.
    //
    // ⚠ **Shown and greyed, not removed — every row, on every fork, since r4n.** There used
    // to be one exception: the Shizuku marker on a fork with no intents left the screen through
    // `appSettingHidden`. The author reversed that — *"greyed, unchecked (memory-preserving)
    // Shizuku service checkboxes on Shevery ... just like for DOOA"* — so nothing is filtered
    // here at all now, and `appSettingBlocked` greys whatever cannot run.
    val appSettingsUiState =
        appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName)
            .map(AppSettingsUiState::Success).stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = AppSettingsUiState.Loading,
        )

    private val _appSettingTemplates = MutableStateFlow<List<AppSettingTemplate>>(emptyList())

    // The same rule as the rows above: offered and greyed, so a press can say what to go and
    // configure. Nothing leaves the list any more — r4n took the one exception out.
    val appSettingTemplates = _appSettingTemplates.onStart {
        getAppSettingTemplates()
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = emptyList(),
    )

    private val _getPinShortcutResult = MutableStateFlow<GetPinShortcutResult?>(null)
    val getPinShortcutResult = _getPinShortcutResult.asStateFlow()

    private val _updatePinShortcutResult = MutableStateFlow<UpdatePinShortcutResult?>(null)
    val updatePinShortcutResult = _updatePinShortcutResult.asStateFlow()

    /**
     * The popup's two answers, both of which end in this screen's launch running again.
     *
     * ⚠ **Restore only goes on if the device came out clear**, and ⚠ **Ignore is permanent** —
     * see `SettingsHiddenRunner.discardPendingReverts`. On the application scope because a
     * restore can wait on Shizuku for seconds and this screen may well be left in that time.
     */
    fun restoreThenApply() {
        appScope.launch {
            // See AppsViewModel.restoreThenLaunch: the flag is what puts a spinner on the
            // screen for the seconds this call can take.
            val cleared = PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }

            if (cleared) applyAppSettings()
        }
    }

    fun discardThenApply() {
        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()

            applyAppSettings()
        }
    }

    fun applyAppSettings() {
        viewModelScope.launch {
            _applyAppSettingsResult.update { applyAppSettingsUseCase(componentName = componentName) }
        }
    }

    fun checkAppSetting(appSetting: AppSetting) {
        viewModelScope.launch {
            appSettingsRepository.upsertAppSetting(appSetting)
        }
    }

    fun deleteAppSetting(appSetting: AppSetting) {
        viewModelScope.launch {
            appSettingsRepository.deleteAppSetting(appSetting)
        }
    }

    fun addAppSetting(appSetting: AppSetting) {
        viewModelScope.launch {
            _addAppSettingsResult.update {
                addAppSettingUseCase(appSetting = appSetting)
            }
        }
    }

    fun getActivityIcon() {
        viewModelScope.launch {
            _activityIcon.update { packageManagerWrapper.getActivityIcon(componentName = componentName) }
        }
    }

    fun revertAppSettings() {
        viewModelScope.launch {
            _revertAppSettingsResult.update { revertAppSettingsUseCase(componentName = componentName) }

            // The notification offering to undo this hide is now describing a device that has
            // been put back. Nothing on this route took it down - it is one fixed id shared by
            // every hide since r3, and the per-app ids the revert paths cancelled have not
            // been posted under since. Conditional inside: another app may still be hidden.
            settingsHiddenRunner.clearRevertOfferIfSettled()
        }
    }

    /**
     * Which of the drawn keys IMD cannot act on right now, and why the overlay one cannot.
     *
     * ⚠ **The reasons rather than the sentences**, for the reason `:domain:model` returns them
     * at all: paths are resources and cannot live in the domain, and Display over other apps
     * has three ways to be unusable that are fixed in three different places. The screen maps
     * them to this module's own copy of the wording.
     *
     * ⚠ **Asked of the three keys that mean something beyond "write this".** Everything else
     * in a profile is a Settings row IMD writes directly and can always write.
     */
    val blockedAppSettings = userDataRepository.userData.map { userData ->
        BlockedAppSettings(
            keys = GATED_KEYS.filter { appSettingBlocked(userData = userData, key = it) }.toSet(),
            overlayReasons = overlayBlockReasons(userData = userData),
        )
    }.distinctUntilChanged().stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = BlockedAppSettings(),
    )

    fun requestPinShortcut(
        icon: ByteArray?,
        shortLabel: String,
        longLabel: String,
    ) {
        viewModelScope.launch {
            _requestPinShortcutResult.update {
                requestPinShortcutUseCase(
                    componentName = componentName,
                    icon = icon,
                    id = componentName,
                    shortLabel = shortLabel,
                    longLabel = longLabel,
                )
            }
        }
    }

    fun getSecureSettingsByName(settingType: SettingType, text: String) {
        viewModelScope.launch {
            _secureSettings.update {
                getSecureSettingsByNameUseCase(
                    settingType = settingType,
                    text = text,
                )
            }
        }
    }

    fun getAppSettingTemplates() {
        viewModelScope.launch {
            _appSettingTemplates.update {
                assetManagerWrapper.getAppSettingTemplates()
            }
        }
    }

    fun getPinShorcut() {
        viewModelScope.launch {
            _getPinShortcutResult.update {
                getPinShortcutUseCase(id = componentName)
            }
        }
    }

    fun updatePinShorcut(
        icon: ByteArray?,
        shortLabel: String,
        longLabel: String,
    ) {
        viewModelScope.launch {
            _updatePinShortcutResult.update {
                updatePinShortcutUseCase(
                    componentName = componentName,
                    icon = icon,
                    id = componentName,
                    shortLabel = shortLabel,
                    longLabel = longLabel,
                )
            }
        }
    }

    fun resetApplyAppSettingsResult() {
        _applyAppSettingsResult.update { null }
    }

    fun resetRequestPinShortcutResult() {
        _requestPinShortcutResult.update { null }
    }

    fun resetRevertAppSettingsResult() {
        _revertAppSettingsResult.update { null }
    }

    fun resetAddAppSettingResult() {
        _addAppSettingsResult.update { null }
    }

    fun resetGetPinShortcutResult() {
        _getPinShortcutResult.update { null }
    }

    fun resetUpdatePinShortcutResult() {
        _updatePinShortcutResult.update { null }
    }

    fun updateFavourite(favourite: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateFavourite(
                componentName = componentName,
                favourite = favourite,
            )
        }
    }
}

/**
 * The per-app keys that can be greyed, and why.
 *
 * A value rather than three flags so the screen asks one question per row. `overlayReasons` is
 * empty when Display over other apps is usable **and** on Shevery, where it is unsupported
 * rather than unconfigured - the empty list is what picks the author's fork sentence over his
 * configure-first one, exactly as it does in the two configuration dialogs and the settings
 * manager.
 *
 * ⚠ **Public, and it has to be.** [AppSettingsViewModel.blockedAppSettings] is a public property
 * on a public class, and Kotlin refuses a public declaration whose type argument is `internal` -
 * a caller outside the module would see the property and not the type it returns. That is a
 * compile error in Android Studio and invisible here, because the sandbox only really
 * compiles the five pure-JVM domain modules. `tools/check_exposed_internal.py` now asks the
 * question instead.
 */
data class BlockedAppSettings(
    val keys: Set<String> = emptySet(),
    val overlayReasons: List<OverlayBlockReason> = emptyList(),
)

/** The three keys that mean more to IMD than "write this value". */
private val GATED_KEYS = listOf(
    AppSettingKeys.SYSTEM_ALERT_WINDOW,
    AppSettingKeys.SHIZUKU_SERVICE,
    AppSettingKeys.ACCESSIBILITY_ENABLED,
)
