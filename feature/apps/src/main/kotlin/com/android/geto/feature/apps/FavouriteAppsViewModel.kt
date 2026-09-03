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
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
import com.android.geto.common.ApplicationScope
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.PriorHideRestore
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.leftSettingsHidden
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import com.android.geto.domain.usecase.ApplyAppSettingsUseCase
import com.android.geto.domain.usecase.ApplySettingsToHideUseCase
import com.android.geto.domain.usecase.GetFavouriteAppsUseCase
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

/**
 * Short enough to read as live, long enough that it is not doing anything expensive: the
 * reads behind it are in-process setting lookups and a binder ping, and it only runs while
 * the manager dialog is open.
 */
private const val TARGET_POLL_MILLIS = 500L

@HiltViewModel
class FavouriteAppsViewModel @Inject constructor(
    shizukuStartTracker: ShizukuStartTracker,
    getFavouriteAppsUseCase: GetFavouriteAppsUseCase,
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
     * Unhides whatever is actually outstanding, the way the Hide settings tile does.
     *
     * ⚠ **It was `Revert to default` and the author changed it.** The button sits on the tab
     * whose whole purpose is an app that has just refused to start, so what the user wants from
     * it is the hide undone — not the device driven to a configured state that may have nothing
     * to do with what was hidden. Under the memory function those are different destinations,
     * and the old behaviour would have written the defaults over remembered values.
     *
     * With nothing outstanding it says so and touches nothing. See
     * [SettingsHiddenRunner.unhidePending] for why that differs from the tile.
     *
     * Launched on the application scope rather than [viewModelScope]: leaving the Favourites
     * tab — which is exactly what someone does after pressing this — would otherwise cancel
     * a revert that takes seconds, and can wait on adbd before it is finished.
     */
    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }

    /**
     * Whether anything IMD did is still outstanding, by any of the three routes it can owe on.
     *
     * ⚠ **The same three questions [unhideSettings] will ask**, derived from the same stored
     * values rather than from a flag of its own — a separate test here could disagree with the
     * one doing the work, and the way it would show is a red button that then says there is
     * nothing to restore.
     */
    val anythingHidden = userDataRepository.userData
        .map { it.autoHideRunning || it.settingsHidden }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = false,
        )


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
