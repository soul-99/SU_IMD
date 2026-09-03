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

import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.framework.ShortcutManagerCompatWrapper
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * Re-renders every pinned shortcut's icon and pushes it back to the launcher.
 *
 * ⚠ **The id of a shortcut IMD pins *is* the component name** — see `GetPinShortcutUseCase`,
 * which looks a shortcut up by exactly that. So each pinned shortcut can be re-rendered from its
 * own app's icon with nothing else stored, and `FLAG_MATCH_PINNED` returns only this app's
 * shortcuts, so there is no other kind of id to meet.
 *
 * ⚠ **The labels are carried over, not regenerated.** A user who renamed a shortcut when they
 * created it would otherwise find the app's own name back on it, which is a far more annoying
 * change than the one they asked for.
 *
 * ⚠ **A shortcut whose icon cannot be read is skipped.** `getActivityIcon` answers null for an
 * app that has been uninstalled since, and writing that null through would replace a working
 * picture with a blank one.
 *
 * Returns how many were updated, for the diagnostics log.
 *
 * ⚠ **What happens next is the launcher's business.** Some redraw a pinned shortcut the moment it
 * is updated; others hold their own copy of the bitmap until they are restarted. Nothing here
 * reaches inside a launcher's cache, so where nothing appears to change the answer is a launcher
 * restart rather than a second attempt.
 */
class RefreshShortcutIconsUseCase @Inject constructor(
    private val shortcutManagerCompatWrapper: ShortcutManagerCompatWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) {
    suspend operator fun invoke(): Int = withContext(ioDispatcher) {
        var updated = 0

        for (shortcut in shortcutManagerCompatWrapper.getShortcuts()) {
            val icon = packageManagerWrapper.getActivityIcon(componentName = shortcut.id)
                ?: continue

            val wrote = shortcutManagerCompatWrapper.updateShortcuts(
                componentName = shortcut.id,
                icon = icon,
                id = shortcut.id,
                shortLabel = shortcut.shortLabel,
                longLabel = shortcut.longLabel,
            )

            if (wrote) updated += 1
        }

        updated
    }
}
