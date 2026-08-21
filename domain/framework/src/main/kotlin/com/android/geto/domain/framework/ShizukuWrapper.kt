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

import com.android.geto.domain.model.ShizukuGrant

interface ShizukuWrapper {
    /**
     * Asks Shizuku to run `pm grant <packageName> android.permission.WRITE_SECURE_SETTINGS`,
     * requesting Shizuku's own permission first if it has not been given yet.
     *
     * This is the no-PC path through first-run setup. It goes entirely through the binder
     * Shizuku publishes, never through its package name, so a renamed or hidden install
     * works exactly the same — which matters here, because the people most likely to want
     * this app are also the ones most likely to be running Shizuku under another name.
     */
    suspend fun grantWriteSecureSettings(packageName: String): ShizukuGrant

    /** Whether a Shizuku binder is alive right now, without prompting for anything. */
    suspend fun isShizukuRunning(): Boolean

    /**
     * Fires the "start Shizuku" broadcast at the Shizuku manager app.
     *
     * This targets the intent API in thedjchi's Shizuku fork: an explicit broadcast
     * with action "$packageName.START" carrying the string extra "auth". The token
     * is the one shown under "View intents" in Shizuku. Vanilla RikkaApps Shizuku
     * does not listen for this, in which case the broadcast is simply ignored.
     *
     * Returns false when the manager package is not installed or the broadcast
     * could not be sent.
     */
    suspend fun startShizuku(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean

    companion object {
        const val DEFAULT_SHIZUKU_PACKAGE_NAME = "moe.shizuku.privileged.api"
        const val ACTION_START_SUFFIX = ".START"
        const val EXTRA_AUTH = "auth"
    }
}
