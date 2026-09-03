/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * The two floating buttons' whole state: one boolean and one call.
 *
 * ⚠ **Separate from [FavouriteAppsViewModel] because of where the buttons are composed.** They are
 * drawn above the navigation graph now, where `hiltViewModel()` resolves against the activity
 * rather than a back-stack entry - so asking there for the Favourites view model would construct a
 * *second* one, loading the app list again to read `anythingHidden`. Both members below are lifted
 * from it verbatim; if either changes there, it changes here.
 */
@HiltViewModel
class AppsFloatingActionsViewModel @Inject constructor(
    userDataRepository: UserDataRepository,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    @ApplicationScope private val appScope: CoroutineScope,
) : ViewModel() {
    /**
     * Whether anything IMD did is still outstanding, by any of the routes it can owe on.
     *
     * ⚠ **The same question [unhideSettings] will ask**, derived from the same stored values
     * rather than from a flag of its own - a separate test here could disagree with the one doing
     * the work, and the way it would show is a red button that then says there is nothing to
     * restore.
     */
    val anythingHidden = userDataRepository.userData
        .map { it.autoHideRunning || it.settingsHidden }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = false,
        )

    /**
     * Put back whatever is outstanding, the way the Unhiding framework says.
     *
     * On the application scope rather than this view model's: the press must finish even if the
     * screen that raised it goes.
     */
    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }
}
