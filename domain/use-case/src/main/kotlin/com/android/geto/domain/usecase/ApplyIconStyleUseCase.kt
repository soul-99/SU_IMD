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
package com.android.geto.domain.usecase

import com.android.geto.domain.common.IconStyleState
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.repository.UserDataRepository
import javax.inject.Inject

/**
 * Saves the Icon style and makes every icon in the app — and on the home screen — catch up.
 *
 * ⚠ **The in-memory flag is set here rather than left to `GetoApplication`'s collector.** Both
 * write the same value from the same source, so this is not a second source of truth; it is
 * ordering. The redraw starts on the line after, and a redraw that overtook the collector would
 * re-render every icon in the *old* style and leave the setting looking broken.
 *
 * ⚠ **Then `invalidate()`, which is what makes a re-read produce different bytes.** The launcher
 * apps wrapper caches rendered icons under component-name-plus-package-update-time — a key that
 * is right for the package changes it was built for and blind to this one, since changing a style
 * changes no package's update time. The counter is the signal to drop that cache.
 */
class ApplyIconStyleUseCase @Inject constructor(
    private val userDataRepository: UserDataRepository,
    private val refreshShortcutIconsUseCase: RefreshShortcutIconsUseCase,
) {
    suspend operator fun invoke(iconStyle: IconStyle) {
        userDataRepository.updateIconStyle(iconStyle = iconStyle)

        IconStyleState.shapeLegacyIcons = iconStyle == IconStyle.SmartAdaptive

        IconStyleState.invalidate()

        refreshShortcutIconsUseCase()
    }
}
