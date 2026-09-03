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
package com.android.geto.domain.framework

/**
 * The two questions auto unhide asks about somebody else's app: has the user closed it, and
 * when did they last have it in front of them.
 *
 * One wrapper rather than two because they are one question asked two ways, and because the
 * watcher needs both answers about the same package in the same tick. Neither can be answered
 * by the ordinary APIs an app has about other apps — `getRunningAppProcesses` has returned
 * only the caller's own processes since Android 5, and `/proc` has been hidden since
 * Android 9 — so both go through permissions granted once by shell.
 */
interface AppSessionWrapper {
    /**
     * Whether this Android version can answer [closedByUser] at all — API 30 and up.
     *
     * Below it there is no unprivileged way to learn that another app's task was removed, so
     * the swipe trigger is not offered rather than offered and quietly broken.
     */
    val exitReasonsSupported: Boolean

    /** Whether IMD holds `android.permission.DUMP`, granted once by `pm grant`. */
    suspend fun hasDumpPermission(): Boolean

    /** Whether IMD holds usage access — the AppOp, not the manifest permission. */
    suspend fun hasUsageAccess(): Boolean

    /**
     * Whether [packageName]'s process has died since [sinceMillis] *because the user ended
     * it* — swiped out of recents, cleared by "Close all", or force-stopped from Settings.
     *
     * All three arrive as the same answer and all three mean the same thing here: the user is
     * finished with the app. A process that died of anything else — low memory, a crash, the
     * system freezer — is not a session ending and must not put the settings back underneath
     * an app the user is still using.
     *
     * [sinceMillis] is **wall clock**, because the records this reads are timestamped in wall
     * clock. Everywhere else in auto unhide durations are measured on the monotonic clock;
     * this is the one place that cannot be.
     */
    suspend fun closedByUser(packageName: String, sinceMillis: Long): Boolean

    /**
     * When [packageName] was last in the foreground, in wall clock, or null if it has not
     * been since [sinceMillis].
     *
     * Null is not "never used" — it is "not in the window asked about", which is exactly what
     * the idle backup wants to know.
     */
    suspend fun lastForegroundAt(packageName: String, sinceMillis: Long): Long?

    /**
     * Every exit record held for [packageName], rendered one line each, for the diagnostic
     * screen only.
     *
     * Strings rather than a model because nothing acts on these — they exist to be read by a
     * person on a device nobody here owns, and the fields worth seeing are whichever ones
     * turn out to be wrong.
     */
    suspend fun describeExits(packageName: String): List<String>

    /** Every usage event since [sinceMillis], one line each, for the diagnostic screen only. */
    suspend fun describeEvents(sinceMillis: Long): List<String>
}
