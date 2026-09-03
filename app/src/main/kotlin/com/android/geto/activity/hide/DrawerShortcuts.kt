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
package com.android.geto.activity.hide

import android.content.ComponentName
import android.content.Context
import android.content.pm.PackageManager
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.repository.UserDataRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.distinctUntilChanged
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Which app-drawer entries IMD publishes, kept in step with the two things that decide them.
 *
 * The author asked for a second launcher entry - *"a new app drawer thing also for hide settings
 * which dynamically updates its icon as clicked"* - and for a setting deciding which entries exist
 * at all, with only the Settings manager on a fresh install.
 *
 * ⚠ **Three aliases, at most two of them ever enabled.** Android has no way to change a launcher
 * entry's icon at runtime: an `<activity-alias>` carries its icon in the manifest, and the only
 * lever is whether it exists. So the Hide/unhide entry is *two* aliases of the same activity with
 * the same label and different icons, and exactly one of them is enabled at a time - the one whose
 * icon matches the device's current state. That is the standard technique for every icon-switching
 * app on Android, and it is why the two are declared as aliases rather than as one entry with a
 * drawable that changes.
 *
 * ⚠ **The launcher may blink.** Disabling a component the launcher is showing removes it from the
 * drawer for a moment and can lose a home-screen placement. There is no way around it; the author
 * was told before this was built.
 *
 * ⚠ **This runs in whatever process changed the state, and that is always this one.** Every route
 * that hides or unhides - the tile, the notification action, the Tasker receiver, the app itself,
 * the new drawer entry - runs in IMD's own process, so a collector started by the application sees
 * every change that can happen. It is not a background job and does not need to be.
 */
@Singleton
class DrawerShortcuts @Inject constructor(
    @ApplicationContext private val context: Context,
    private val userDataRepository: UserDataRepository,
) {
    /**
     * Applies the three enabled states for one reading of the user's data.
     *
     * Idempotent, and cheap when nothing has moved: `setComponentEnabledSetting` on a component
     * that is already in the requested state is a no-op inside the package manager.
     */
    fun apply(userData: UserData) {
        val hidden = userData.settingsHidden

        val hideUnhide = userData.drawerShortcutHideUnhide

        set(MANAGER, userData.drawerShortcutManager)

        // ⚠ **The two are mutually exclusive by construction**, not by two independent
        // conditions that could both come out true: whichever way `hidden` reads, one of these
        // is on and the other off.
        set(VISIBLE, hideUnhide && !hidden)

        set(HIDDEN, hideUnhide && hidden)
    }

    /**
     * The stream to collect for the life of the process.
     *
     * Distinct on the three inputs rather than on the whole of [UserData], which changes on every
     * write anywhere in the app: without that, an unrelated preference would re-enter the package
     * manager three times for nothing.
     */
    val states = userDataRepository.userData
        .map { Triple(it.drawerShortcutManager, it.drawerShortcutHideUnhide, it.settingsHidden) }
        .distinctUntilChanged()

    private fun set(className: String, enabled: Boolean) {
        val component = ComponentName(context.packageName, className)

        val state = if (enabled) {
            PackageManager.COMPONENT_ENABLED_STATE_ENABLED
        } else {
            PackageManager.COMPONENT_ENABLED_STATE_DISABLED
        }

        // DONT_KILL_APP, always. Without it the platform is entitled to end this process to
        // apply the change - in the middle of the hide that caused it.
        runCatching {
            context.packageManager.setComponentEnabledSetting(
                component,
                state,
                PackageManager.DONT_KILL_APP,
            )
        }
    }

    private companion object {
        /**
         * The three aliases, by name.
         *
         * ⚠ **Strings, and they have to be.** These are `<activity-alias>` entries: they have no
         * Kotlin class to take `::class.java` of. A rename in the manifest that is not made here
         * fails silently - the package manager simply reports an unknown component - so the
         * manifest carries a note pointing back at this list.
         */
        const val MANAGER = "com.android.geto.activity.services.SettingsManagerLauncher"

        const val VISIBLE = "com.android.geto.activity.hide.HideUnhideVisibleLauncher"

        const val HIDDEN = "com.android.geto.activity.hide.HideUnhideHiddenLauncher"
    }
}
