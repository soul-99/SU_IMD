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
package com.android.geto.activity.hide

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.domain.model.UserData
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.stateIn
import javax.inject.Inject

/**
 * One value, for the one thing [HideActivity] draws.
 *
 * **It used to run the whole tile press**, because the window was opened by the call that
 * collapses the shade and the shade collapsed at the press. It no longer does: the press runs in
 * `HideTileService` and the window is opened at the end, purely to close the shade — see
 * [HideActivity]. What is left is the theme for the one dialog that still appears here.
 *
 * Kept as a ViewModel rather than folded into the activity so the read survives a configuration
 * change: the dialog is dismissable and can sit on screen while the device is rotated, and
 * re-reading the preference file on every rotation would flash the wrong theme through it.
 */
@HiltViewModel
class HideViewModel @Inject constructor(
    userDataRepository: UserDataRepository,
) : ViewModel() {
    /**
     * The theme, for the one case where this window draws something.
     *
     * Null until the first read lands, which the activity reads as "follow the system" — a
     * momentary wrong theme beats a blank frame while a preference file is opened.
     */
    val userData = userDataRepository.userData.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = null as UserData?,
    )
}
