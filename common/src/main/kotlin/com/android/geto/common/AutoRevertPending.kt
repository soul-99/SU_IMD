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
package com.android.geto.common

import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicReference

/**
 * Whether coming back to IMD should put the device back on its own.
 *
 * Two facts, and the auto revert needs both. Which app was launched from inside IMD, because
 * the memory function reverts one app's profile rather than the device. And whether IMD has
 * actually been away since - without that, arming the marker while the launch screen is still
 * in front of the user would fire the revert on the very next frame, before the launched app
 * had drawn anything.
 *
 * An object rather than an injected singleton, matching [SettingsObservationGate] and
 * [SettingsChangeLog]: the writer is a screen in the feature module and the reader is the
 * activity in the app module.
 *
 * In memory on purpose. If the process is killed while the launched app is in the foreground
 * the marker goes with it and returning to IMD reverts nothing - the settings stay hidden and
 * the notification is still there to do it by hand. That is the safe way round: a revert
 * restored from disk would fire on some later cold start, with no launch behind it and
 * nothing on screen to explain why the device just changed.
 */
object AutoRevertPending {

    private val componentName = AtomicReference<String?>(null)
    private val wentAway = AtomicBoolean(false)

    /** Armed by an in-app launch that actually applied something. */
    fun arm(componentName: String) {
        this.componentName.set(componentName)
        wentAway.set(false)
    }

    /**
     * IMD is no longer on screen, so the launch really did leave it. Called from the
     * activity's ON_STOP rather than ON_PAUSE: a dialog or the notification shade pauses the
     * activity without ever leaving it, and either would otherwise count as having gone away.
     */
    fun markWentAway() {
        if (componentName.get() != null) wentAway.set(true)
    }

    /**
     * The component to revert, or null when there is nothing to do - which is the answer on
     * every ordinary return to the app, so this has to be cheap and has to be right.
     *
     * Consuming clears the marker, so a revert cannot run twice for one launch however many
     * times the activity is brought back.
     */
    fun consume(): String? {
        if (!wentAway.get()) return null

        val pending = componentName.getAndSet(null)

        wentAway.set(false)

        return pending
    }

    /**
     * Thrown away without reverting. Used when the user reverts by hand first: the device is
     * already back, and firing again on return would be a second revert of nothing.
     */
    fun clear() {
        componentName.set(null)
        wentAway.set(false)
    }
}
