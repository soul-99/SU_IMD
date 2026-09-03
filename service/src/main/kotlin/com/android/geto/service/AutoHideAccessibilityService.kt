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
package com.android.geto.service

import android.accessibilityservice.AccessibilityService
import android.content.Context
import android.view.accessibility.AccessibilityEvent
import com.android.geto.common.AppLocale
import com.android.geto.common.AutoHideDetection

/**
 * The detector behind Auto-hide settings (IMD+): it notices a watched app coming to the front.
 *
 * This is the only part of IMD that runs while the user is not in IMD at all, and it is
 * deliberately the smallest part. It reads one field of one event — the package name of
 * whatever just came to the foreground — and hands it to [AutoHideDetection]. It cannot read
 * screen content: the configuration does not ask for that capability, so the system never
 * grants it.
 *
 * **Why the service disables itself mid-run.** IMD+ kills the watched app, hides the settings
 * and opens the app again — and that reopening is another app coming to the foreground, which
 * is exactly what this service listens for. Left running it would detect its own relaunch and
 * start over, forever. So the run switches this service off as soon as the kill succeeds, and
 * a revert switches it back on with the other accessibility services. That is a state, not a
 * timer: nothing depends on how long a kill or a launch happens to take on a given device.
 *
 * It also means IMD+ is deaf for as long as settings are hidden, which is correct rather than
 * unfortunate — the way back is the notification, the tile or a shortcut, none of which needs
 * a detector. The IMD+ switch in settings reads off for the same period and says why.
 */
/*
 * No @AndroidEntryPoint, unlike SettingsObserverService beside it, and that is deliberate: this
 * service injects nothing. Everything it needs to decide is held in AutoHideDetection, in
 * memory, because an accessibility event can arrive with no other part of this app alive — so
 * there is nothing for Hilt to provide, and a generated base class in the way of the one
 * component that has to be as small as possible would buy nothing.
 */
class AutoHideAccessibilityService : AccessibilityService() {
    // The chosen language, applied before anything reads a string. A no-op on Android 13
    // and up, where the platform has already applied it to this context.
    override fun attachBaseContext(newBase: Context) {
        super.attachBaseContext(AppLocale.wrap(newBase))
    }

    override fun onServiceConnected() {
        super.onServiceConnected()

        AutoHideDetection.markRunning(running = true)
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val packageName = event?.packageName?.toString() ?: return

        // Ignore this app's own windows outright. IMD raises a spinner and dialogs over the
        // launcher during a run, and each of those is a window state change carrying IMD's own
        // package - which is never something to react to.
        if (packageName == this.packageName) return

        AutoHideDetection.onAppForegrounded(packageName = packageName)
    }

    /**
     * Called when the system interrupts the service. Nothing to abandon: this service holds no
     * work of its own — it observes and hands off — so there is nothing to stop.
     */
    override fun onInterrupt() = Unit

    override fun onDestroy() {
        AutoHideDetection.markRunning(running = false)

        super.onDestroy()
    }
}
