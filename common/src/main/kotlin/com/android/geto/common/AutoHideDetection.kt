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

/**
 * The seam between the accessibility service that notices an app opening and the code that
 * decides what to do about it.
 *
 * The same arrangement [SettingsObservationGate] uses, and for the same reason: the detector
 * lives in the service module, the run logic lives above it, and neither should have to depend
 * on the other to say one sentence. The service reports a package name here; whoever owns the
 * run registers to hear about it.
 *
 * A registered handler rather than a flow, because this has to work with no coroutine scope
 * alive to collect one — an accessibility event can arrive with nothing else of this app
 * running at all.
 */
object AutoHideDetection {
    /**
     * The class name of the accessibility service, for the modules that have to name it
     * without being able to see it: the domain, to keep it out of the managed set the user
     * picks from, and the settings screen, to report whether it is switched on.
     */
    const val SERVICE_CLASS_NAME = "com.android.geto.service.AutoHideAccessibilityService"

    /**
     * The transparent window a run happens inside, named the way [SettingsObservationGate]
     * names the observer service and for the same reason: it lives in the app module, above
     * everything that has to start it.
     *
     * A run needs a window of this app's own for two reasons that have nothing to do with
     * looks. Starting an app from the background is refused on Android 10 and up unless
     * something exempts the caller — and the run switches off the accessibility service that
     * would have been the exemption, so it cannot rely on it. And the Shizuku wait is up to
     * thirteen seconds, which is far too long for a tap on an app icon to sit silent.
     */
    const val ACTIVITY_CLASS_NAME = "com.android.geto.activity.autohide.AutoHideActivity"

    /** The watched package a run was started for. */
    const val EXTRA_PACKAGE_NAME = "auto_hide_package_name"

    private val running = AtomicBoolean(false)

    /**
     * Whether the detector is connected right now.
     *
     * The system's own answer, reported by the service as it starts and stops, rather than
     * this app's opinion of it. Something else can switch an accessibility service off at any
     * time — the user, an OS update, a battery optimiser — and the settings screen has to show
     * what is true rather than what was last asked for.
     */
    val isRunning: Boolean get() = running.get()

    fun markRunning(running: Boolean) {
        this.running.set(running)
    }

    @Volatile
    private var handler: ((String) -> Unit)? = null

    /**
     * Registers what happens when a watched app comes to the front. Set once, at application
     * start; passing null clears it.
     */
    fun setHandler(handler: ((String) -> Unit)?) {
        this.handler = handler
    }

    /**
     * Reports an app coming to the foreground.
     *
     * Every decision about whether this package matters — is IMD+ on, is this one of the
     * chosen apps, is anything already hidden — belongs to the handler, not here. This is
     * called for every window change on the device, so it does the least possible work and
     * holds no state.
     */
    fun onAppForegrounded(packageName: String) {
        handler?.invoke(packageName)
    }
}
