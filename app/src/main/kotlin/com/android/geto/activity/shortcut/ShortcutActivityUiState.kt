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

import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework

sealed interface ShortcutActivityUiState {
    data object Loading : ShortcutActivityUiState

    /**
     * ⚠ **It carried `applicationIcon` and `unhidingFramework` until r3**, both only so the
     * shortcut route could post a per-app revert notification with the launched app's icon.
     * Every launch posts the one generic notification now, so neither is read any more — and
     * the icon was a bitmap fetched over binder on every shortcut press.
     *
     * ⚠ **The hand-written `equals`/`hashCode` went with the icon**, which is the only reason
     * they existed: a `ByteArray` property gives a data class identity-based equality, so both
     * had to be spelled out. What is left is a nullable enum, an enum and a `String?`, for
     * which the generated implementations are exactly what those overrides wrote by hand.
     */
    data class Success(
        val appSettingsResult: AppSettingsResult?,
        val hidingFramework: HidingFramework = HidingFramework.Default,
        val appName: String? = null,
    ) : ShortcutActivityUiState
}
