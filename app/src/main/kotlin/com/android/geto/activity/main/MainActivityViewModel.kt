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
package com.android.geto.activity.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.broadcastreceiver.DeveloperNoteNotification
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.common.PriorHide
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.GetInstalledAppsUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.drop
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class MainActivityViewModel @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    // r4p: the Shizuku setup page draws the real configuration section, whose package field
    // offers a picker over the installed apps.
    private val getInstalledAppsUseCase: GetInstalledAppsUseCase,
    // r4n: acknowledging the developer's note has to take down the notification the background
    // routes raised for the same message. A leaf - it depends on no runner, so no Hilt cycle.
    private val developerNoteNotification: DeveloperNoteNotification,
    @param:ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    private val _priorHide = MutableStateFlow(false)

    /**
     * Whether the settings that are down were hidden by a run of IMD that is no longer alive.
     *
     * Raised once per process, by [checkPriorHide] below.
     */
    val priorHide = _priorHide.asStateFlow()

    /**
     * Ask the gate, on arriving at the app proper.
     *
     * ⚠ **[PriorHide.suppress] with it**, as on every other surface: the flag is what stops a
     * second prompt appearing behind a dialog nobody has answered. It is cleared again by
     * [PriorHide.markHidden] on the next real hide, or by [PriorHide.settled] once the debt is
     * genuinely gone — so this is "do not ask twice", not "never ask again".
     */
    fun checkPriorHide() {
        viewModelScope.launch {
            if (PriorHide.shouldWarn(userDataRepository.userData.first().settingsHidden)) {
                PriorHide.suppress()

                _priorHide.update { true }
            }
        }
    }

    /**
     * `'Restore settings first'`, with no launch waiting behind it.
     *
     * [SettingsHiddenRunner.flushPendingReverts] rather than `unhide`: this settles the debts
     * that exist and leaves a device that owes none alone, where `unhide` would fall back to
     * applying the configured defaults. The Favourites tab's Unhide button makes the same call
     * for the same reason.
     */
    fun restorePriorHide() {
        _priorHide.update { false }

        appScope.launch {
            PriorHideRestore.track { settingsHiddenRunner.flushPendingReverts() }
        }
    }

    /** `'Ignore all previous reverts'`, and permanent here exactly as it is everywhere else. */
    fun discardPriorHide() {
        _priorHide.update { false }

        appScope.launch {
            settingsHiddenRunner.discardPendingReverts()
        }
    }
    val uiState = userDataRepository.userData.map(MainActivityUiState::Success).stateIn(
        scope = viewModelScope,
        initialValue = MainActivityUiState.Loading,
        started = SharingStarted.WhileSubscribed(5_000),
    )

    /**
     * The Shizuku page in setup: the four fields, then the master switch.
     *
     * ⚠ **In that order, and the order is the whole of it.** They are separate writes, and a
     * process death between them has to leave a filled-in configuration with Manage Shizuku
     * off — which `manageShizukuEffective` reads as "not managing", and which the user can turn
     * on in one tap — rather than a switch on over half a configuration, which every gate in
     * the app would then believe.
     */
    private val _installedApps = MutableStateFlow<List<InstalledAppData>>(emptyList())

    /**
     * The device's apps, for the Shizuku setup page's package picker.
     *
     * ⚠ Not read on the way in. Enumerating every package and rasterising an icon each is far
     * too heavy to do while somebody is being walked through permissions, so the section asks
     * for it when it is first composed - the same arrangement `SettingsViewModel` has, over the
     * same use case.
     */
    val installedApps = _installedApps.asStateFlow()

    /**
     * Bumped after the list is published, so a caller waiting on a refresh wakes to find the
     * apps already there.
     *
     * A counter rather than a wait for the list to *change*: a re-detect that finds exactly what
     * was already there changes nothing, and a waiter watching the list would wait out its
     * ceiling for an answer that had already arrived.
     */
    private val _installedAppsRevision = MutableStateFlow(0)
    val installedAppsRevision = _installedAppsRevision.asStateFlow()

    /** Guards against two enumerations running at once; only ever touched from the main thread. */
    private val installedAppsInFlight = MutableStateFlow(false)

    /**
     * ⚠ **The Shizuku picker's icons follow the Icon style too.**
     *
     * This list is cached until something forces a re-read, so without this it would go on
     * showing whichever style was in force when it was first read — for the rest of the
     * process's life.
     *
     * ⚠ **Below every property it reaches**, and that is not tidiness. r4w put it above three of
     * them; the collector body happens to run after construction, so it happened to be safe,
     * which is not a property worth relying on in a constructor.
     */
    init {
        viewModelScope.launch {
            IconStyleState.revision.drop(1).collect {
                // ⚠ **Cleared first, and that is the whole of why this did nothing.** A
                // MutableStateFlow conflates on `equals`, and `InstalledAppData.equals` compares
                // the package name and label only — so a list re-read in the other style was
                // equal to the one already there and never emitted. Emptying it first means the
                // re-read cannot compare equal to what it replaces.
                _installedApps.update { emptyList() }

                refreshInstalledApps(force = true)
            }
        }
    }

    fun refreshInstalledApps(force: Boolean = false) {
        if (installedAppsInFlight.value) return

        if (!force && _installedApps.value.isNotEmpty()) return

        installedAppsInFlight.update { true }

        viewModelScope.launch {
            try {
                _installedApps.update { getInstalledAppsUseCase() }
            } finally {
                installedAppsInFlight.update { false }

                _installedAppsRevision.update { it + 1 }
            }
        }
    }

    fun saveShizukuConfiguration(
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) {
        viewModelScope.launch {
            userDataRepository.updateShizukuForkMode(shizukuForkMode = forkMode)

            userDataRepository.updateShizukuPackageName(shizukuPackageName = packageName)

            userDataRepository.updateShizukuStartAction(shizukuStartAction = startAction)

            userDataRepository.updateShizukuAuthKey(shizukuAuthKey = authKey)

            userDataRepository.updateManageShizuku(enabled = true)
        }
    }

    fun markTipShown() {
        viewModelScope.launch {
            userDataRepository.updateTipShown(tipShown = true)
        }
    }

    fun markSetupNoticeSeen(versionCode: Int) {
        viewModelScope.launch {
            userDataRepository.updateSetupNoticeVersion(versionCode = versionCode)
        }
    }

    fun acknowledgeSettingsTabNotice() {
        viewModelScope.launch {
            userDataRepository.updateSettingsNoticeRevision(revision = SETTINGS_NOTICE_REVISION)

            // ⚠ **And the notification the background routes raised for the same message.**
            // The dialog and the notification are one piece of news; reading either has to end
            // both, or a user who opened IMD would still be looking at a note they had just
            // dismissed.
            developerNoteNotification.clear()
        }
    }

    fun acknowledgeRevertDefaultsNotice() {
        viewModelScope.launch {
            userDataRepository.updateRevertDefaultsNoticePending(pending = false)
        }
    }

    fun markObtainiumTipShown() {
        viewModelScope.launch {
            userDataRepository.updateObtainiumTipShown(obtainiumTipShown = true)
        }
    }
}


/**
 * The newest "what changed" notice.
 *
 * Bumped whenever there is something new worth pointing an existing install at; anyone whose
 * stored revision is lower sees the notice once and is then written up to this. One constant
 * rather than a fresh proto field per notice.
 */
/**
 * Which "what changed" notice the current build has.
 *
 * ⚠ **Bumped 1 → 2 by r4n**, when the developer's note replaced the Settings-tab notice.
 * Anyone who saw revision 1 sees this one too, which is right: it is a different message, and
 * the author wrote it for exactly the people who had already been through an update.
 */
internal const val SETTINGS_NOTICE_REVISION = 2
