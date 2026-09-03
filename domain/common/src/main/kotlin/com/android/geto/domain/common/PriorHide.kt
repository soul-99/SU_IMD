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
package com.android.geto.domain.common

/**
 * Whether the settings that are down were hidden by a **previous** run of this app.
 *
 * Force-stopping an app takes its notifications with it, so a hide that outlives the process
 * that made it leaves a device locked down with nothing on screen offering the way back. The
 * next launch through IMD used to hide straight over the top and say nothing.
 *
 * ⚠ **One volatile, and no service.** The author asked whether this could be done without a
 * background service. It can, and this is the whole of it: a debt is persisted, [markHidden] is
 * not, so a debt standing with [markHidden] never called in this process means the process that
 * made it is gone. Read at launch time, in the process that is already running because the user
 * has just launched something.
 *
 * ⚠ **Deliberately not "the revert notification is no longer posted"**, which was the sharper
 * variant offered and refused: on Android 13+ with notifications denied that notification is
 * *never* posted, so the condition would be permanently true and the popup would fire on every
 * launch in ordinary use — the exact failure this trigger exists to avoid.
 *
 * **An object rather than an injected singleton**, for the reason [Diagnostics] is one: the
 * askers are spread across `domain`, `broadcast-receiver`, three feature modules and `app`, and
 * two of them are pure Kotlin use cases with no injector in reach.
 */
object PriorHide {

    @Volatile
    private var hidInThisProcess: Boolean = false

    @Volatile
    private var suppressed: Boolean = false

    /**
     * A hide ran here, so anything outstanding from now on is this process's own doing.
     *
     * Clears [suppressed] with it: a real hide supersedes any earlier "do not ask again", and
     * leaving it set would silence the warning after the *next* force close.
     */
    fun markHidden() {
        hidInThisProcess = true

        suppressed = false
    }

    /**
     * Do not ask again until something changes.
     *
     * Two callers, and they want the same thing for different reasons. **The prompt itself**
     * sets it while the dialog is on screen, because IMD+ draws over the app the user just
     * opened and that is itself a window change the detector would see — without this, a dialog
     * nobody has answered yet would put up another one behind it.
     *
     * **A failed restore** sets it too, and that is the author's rule: the notification is on
     * screen, the app stays open, and IMD+ does not run. Without it the gate would still be
     * true, so the next detection would prompt, fail and prompt again.
     *
     * **Headless callers** set it as well: Tasker has no window, and an automation that stopped
     * to ask a question would simply never run. The first-owner rule makes proceeding safe.
     */
    fun suppress() {
        suppressed = true
    }

    /**
     * Everything outstanding has been settled, by whatever route.
     *
     * ⚠ **The one reset, and it covers the case the author described in terms of notifications.**
     * He asked for the IMD+ suppression to lift when the user starts Shizuku by hand and taps
     * *Try again*, or clears the failure notification. Tapping *Try again* restores from the
     * debt, which clears it, which reaches here — so the behaviour he wanted falls out of the
     * condition that actually matters, with no notification-dismissal plumbing to keep in step.
     * Starting Shizuku without retrying leaves the debt standing, and IMD+ staying blocked is
     * then correct rather than a bug.
     */
    fun settled() {
        hidInThisProcess = false

        suppressed = false
    }

    /**
     * Whether a launch should stop and say the settings predate this run of IMD.
     *
     * [settingsHidden] is asked for rather than read, because this object deliberately holds no
     * dependencies — the callers all have `UserData` in hand at the moment they ask.
     */
    fun shouldWarn(settingsHidden: Boolean): Boolean =
        settingsHidden && !hidInThisProcess && !suppressed
}
