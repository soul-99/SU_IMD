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
package com.android.geto.feature.appsettings.shortcut

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.GetPinShortcutResult
import com.android.geto.domain.model.RequestPinShortcutResult
import com.android.geto.domain.usecase.GetPinShortcutUseCase
import com.android.geto.domain.usecase.RequestPinShortcutUseCase
import com.android.geto.domain.usecase.UpdatePinShortcutUseCase
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * What the dialog needs, and which app it belongs to.
 *
 * The component name is carried alongside rather than held separately because the two are
 * only meaningful together: an icon and a lookup result that came from different apps
 * describe nothing, and there is a window during which that is exactly what a separately
 * stored pair would hold.
 */
data class ShortcutTarget(
    val componentName: String,
    val icon: ByteArray?,
    val result: GetPinShortcutResult,
)

/**
 * Everything the standalone create-shortcut dialog needs, for one app at a time.
 *
 * The app-settings screen has its own copy of this wiring inside a much larger ViewModel;
 * this is not that one made reusable, because that one is scoped to the screen's route
 * arguments and cannot be asked about a different app. Here the component name arrives with
 * [start], since the dialog is opened from a list where the app is whichever row was held.
 *
 * The shortcut's id is the component name, matching what the app-settings screen writes —
 * that is what makes holding an app whose shortcut already exists offer to edit it rather
 * than silently creating a second one.
 */
@HiltViewModel
class ShortcutViewModel @Inject constructor(
    private val getPinShortcutUseCase: GetPinShortcutUseCase,
    private val requestPinShortcutUseCase: RequestPinShortcutUseCase,
    private val updatePinShortcutUseCase: UpdatePinShortcutUseCase,
    private val packageManagerWrapper: PackageManagerWrapper,
) : ViewModel() {
    private val _target = MutableStateFlow<ShortcutTarget?>(null)
    val target = _target.asStateFlow()

    private val _requestPinShortcutResult = MutableStateFlow<RequestPinShortcutResult?>(null)
    val requestPinShortcutResult = _requestPinShortcutResult.asStateFlow()

    /**
     * Looks up the icon and any existing shortcut for [componentName].
     *
     * Cleared first, and that clearing is the fix for a real bug rather than tidiness. This
     * ViewModel outlives the dialog — it belongs to the tab, and the dialog is opened and
     * dismissed inside it — so on the second open the previous app's icon and lookup were
     * still here. The dialog rendered from them before the new lookup landed, seeding its
     * label fields with the *other* app's name, and since those fields are only seeded once
     * the correct values arriving a moment later changed nothing.
     */
    fun start(componentName: String) {
        viewModelScope.launch {
            _target.update { null }

            // ⚠ **Both reads are guarded, and that is the whole of the intermittent bug.**
            // Unguarded, a throw from either one ends this coroutine at that line and leaves
            // the target null — and since `start` is called once per component, nothing ever
            // tries again. What the user sees is a long press that opens a spinner and never
            // leaves it, or before r4q, a long press that did nothing.
            //
            // Neither throw is exotic. The icon read catches `NameNotFoundException` and
            // nothing else, so the drawable conversion under it can still raise; and the
            // shortcut query throws while the user is locked.
            val icon = try {
                packageManagerWrapper.getActivityIcon(componentName = componentName)
            } catch (cancellation: CancellationException) {
                // ⚠ Rethrown, always. A cancelled composition is not a failed read, and
                // catching it here would leave a dead coroutine reporting success.
                throw cancellation
            } catch (_: Exception) {
                // The dialog draws a null icon already.
                null
            }

            val result = try {
                getPinShortcutUseCase(id = componentName)
            } catch (cancellation: CancellationException) {
                throw cancellation
            } catch (_: Exception) {
                // ⚠ "Offer to create one" is the honest answer to *I could not find out
                // whether one exists*. The launcher reconciles a duplicate id itself, and the
                // alternative — no dialog — is the bug this is fixing.
                GetPinShortcutResult.RequestPinShortcut
            }

            _target.update {
                ShortcutTarget(componentName = componentName, icon = icon, result = result)
            }
        }
    }

    fun requestPinShortcut(
        componentName: String,
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

    fun updatePinShortcut(
        componentName: String,
        icon: ByteArray?,
        shortLabel: String,
        longLabel: String,
    ) {
        viewModelScope.launch {
            updatePinShortcutUseCase(
                componentName = componentName,
                icon = icon,
                id = componentName,
                shortLabel = shortLabel,
                longLabel = longLabel,
            )
        }
    }

    fun consumeRequestResult() {
        _requestPinShortcutResult.update { null }
    }
}
