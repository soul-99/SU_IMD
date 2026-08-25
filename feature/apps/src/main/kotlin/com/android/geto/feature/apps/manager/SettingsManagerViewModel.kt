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
package com.android.geto.feature.apps.manager

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.RevertToDefaultRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.GetManualTargetStatesUseCase
import com.android.geto.domain.usecase.SetManualTargetUseCase
import com.android.geto.domain.usecase.ShizukuStartTracker
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Short enough to read as live, long enough that it is not doing anything expensive: the
 * reads behind it are in-process setting lookups and a binder ping, and it only runs while
 * the manager is on screen.
 */
private const val TARGET_POLL_MILLIS = 500L

/**
 * Everything the settings manager needs, independent of where it is being shown from.
 *
 * Lifted out of the Favourites screen because the manager now has three front doors — that
 * tab, a Quick Settings tile, and a long-press shortcut — and two of them open it with no
 * app UI behind it at all. One owner for the polling and the writes means the tile cannot
 * drift away from the in-app dialog.
 */
@HiltViewModel
class SettingsManagerViewModel @Inject constructor(
    private val getManualTargetStatesUseCase: GetManualTargetStatesUseCase,
    private val setManualTargetUseCase: SetManualTargetUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val shizukuStartTracker: ShizukuStartTracker,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    private val _targetStates = MutableStateFlow(ManualTargetStates())
    val targetStates = _targetStates.asStateFlow()

    private val _shizukuLaunchPackage = MutableStateFlow<String?>(null)
    val shizukuLaunchPackage = _shizukuLaunchPackage.asStateFlow()

    /**
     * Whether an attempt to start Shizuku is in flight, from anywhere.
     *
     * Off the shared tracker rather than a local flag, because the attempt is often not this
     * dialog's: a revert from the tile or a notification can begin one while the dialog is
     * shut, and opening it mid-attempt has to show what is actually happening.
     */
    val shizukuStarting = shizukuStartTracker.starting.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = false,
    )

    /**
     * Whether the last attempt timed out. Persisted, so a failure during a revert with no UI
     * on screen is still there to report when the dialog is next opened.
     */
    val shizukuStartFailed = userDataRepository.userData
        .map { it.shizukuStartFailed }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Whether the manager has already explained itself, or null while that is still being
     * read.
     *
     * Nullable on purpose. A plain false as the initial value would mean every open of this
     * dialog flashes the information popup for the moment before the stored answer arrives,
     * including for people who dismissed it months ago.
     */
    val infoShown: StateFlow<Boolean?> = userDataRepository.userData
        .map<UserData, Boolean?> { it.settingsManagerInfoShown }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = null,
        )

    fun markInfoShown() {
        viewModelScope.launch {
            userDataRepository.updateSettingsManagerInfoShown(shown = true)
        }
    }

    private var watchJob: Job? = null

    /**
     * Starts re-reading every row's real state while the manager is on screen.
     *
     * Polled rather than observed because there is nothing to observe: `Settings.Global`
     * has a content observer but Shizuku's liveness does not, and a row that updated on a
     * different schedule from its neighbours would look broken. Every one of these can be
     * changed from outside the app — including from the system screens the manager links
     * out to — so the reads have to keep happening while it is open.
     */
    fun startWatching() {
        if (watchJob?.isActive == true) return

        watchJob = viewModelScope.launch {
            _shizukuLaunchPackage.value = resolveShizukuLaunchPackage()

            while (isActive) {
                _targetStates.value = getManualTargetStatesUseCase()

                delay(TARGET_POLL_MILLIS)
            }
        }
    }

    fun stopWatching() {
        watchJob?.cancel()

        watchJob = null
    }

    /**
     * The per-row switch. Writes, then re-reads immediately rather than waiting for the
     * next poll, so the switch settles on what actually happened instead of springing back
     * a moment later.
     */
    fun setTargetEnabled(target: ManualRevertTarget, enabled: Boolean) {
        viewModelScope.launch {
            setManualTargetUseCase(target = target, enabled = enabled)

            _targetStates.value = getManualTargetStatesUseCase()
        }
    }

    /**
     * Puts the device back into the configured default, then closes.
     *
     * On the application scope, not [viewModelScope]: the dialog dismisses itself on the
     * press — and when it was opened from the tile or the shortcut, dismissing finishes the
     * activity and takes this ViewModel with it.
     */
    fun revertToDefault() {
        appScope.launch { revertToDefaultRunner() }
    }

    /**
     * Clears the recorded failure when the dialog closes.
     *
     * The red switch is a report on the last attempt, and it has now been delivered — the
     * user has seen it and can act on it. Leaving it set would greet them with the same red
     * switch every time they opened the dialog until they happened to retry, long after it
     * described anything current.
     *
     * On the application scope because this runs as the dialog is being dismissed, which for
     * the tile and the shortcut also finishes the activity holding this ViewModel.
     */
    fun acknowledgeShizukuFailure() {
        appScope.launch {
            if (shizukuStartFailed.value) {
                userDataRepository.updateShizukuStartFailed(failed = false)
            }
        }
    }

    private suspend fun resolveShizukuLaunchPackage(): String? {
        val userData = userDataRepository.userData.first()

        return packageManagerWrapper.findLaunchablePackage(
            preferredPackage = userData.shizukuPackageName,
            labels = listOf(
                ShizukuForkDefaults.SHIZUKU_LABEL,
                ShizukuForkDefaults.SHEVERY_LABEL,
            ),
        )
    }

    override fun onCleared() {
        stopWatching()

        super.onCleared()
    }
}
