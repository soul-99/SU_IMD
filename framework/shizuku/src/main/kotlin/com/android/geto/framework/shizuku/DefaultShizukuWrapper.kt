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
package com.android.geto.framework.shizuku

import android.content.Context
import android.content.Intent
import android.util.Log
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers.IO
import com.android.geto.domain.framework.ShizukuWrapper
import com.android.geto.domain.model.ShizukuGrant
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

private const val TAG = "ShizukuWrapper"

internal class DefaultShizukuWrapper @Inject constructor(
    @param:Dispatcher(IO) private val ioDispatcher: CoroutineDispatcher,
    @param:ApplicationContext private val context: Context,
) : ShizukuWrapper {

    override suspend fun isShizukuRunning(): Boolean = withContext(ioDispatcher) {
        ShizukuPermission.isRunning()
    }

    override suspend fun grantWriteSecureSettings(packageName: String): ShizukuGrant =
        withContext(ioDispatcher) {
            ShizukuPermission.grantWriteSecureSettings(packageName = packageName)
        }

    override suspend fun getAllowedOverlayPackages(): Set<String>? = withContext(ioDispatcher) {
        ShizukuPermission.getAllowedOverlayPackages()
    }

    override suspend fun setOverlayPermission(
        packages: Set<String>,
        allowed: Boolean,
    ): Set<String>? = withContext(ioDispatcher) {
        ShizukuPermission.setOverlayPermission(packages = packages, allowed = allowed)
    }

    override suspend fun startShizuku(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean = sendShizukuBroadcast(
        packageName = packageName,
        action = action,
        authKey = authKey,
    )

    override suspend fun stopShizuku(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean = sendShizukuBroadcast(
        packageName = packageName,
        action = action,
        authKey = authKey,
    )

    private suspend fun sendShizukuBroadcast(
        packageName: String,
        action: String,
        authKey: String,
    ): Boolean = withContext(ioDispatcher) {
        if (packageName.isBlank() || action.isBlank()) {
            return@withContext false
        }

        val intent = Intent(action).apply {
            setPackage(packageName)
            // Only thedjchi's fork authenticates the broadcast. Shevery and the others
            // have no token, and sending an empty one is worse than sending none: it
            // makes an unauthenticated contract look like a misconfigured authenticated
            // one in a bug report.
            if (authKey.isNotBlank()) {
                putExtra(ShizukuWrapper.EXTRA_AUTH, authKey)
            }
            // Shizuku's manager process is very often not running at this point, and a
            // broadcast is dropped for a stopped package unless this flag is set.
            addFlags(Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
        }

        // Resolving the receiver up front turns a silent no-op into something we can
        // log, and pins the broadcast to a single component.
        val receiver = runCatching {
            context.packageManager.queryBroadcastReceivers(intent, 0)
        }.getOrDefault(emptyList()).firstOrNull()

        if (receiver == null) {
            // Vanilla Shizuku has no such receiver, and a wrong package or action lands
            // here too. Sending anyway would be a silent no-op reported as success.
            Log.w(TAG, "No receiver for $action in $packageName")

            return@withContext false
        }

        intent.setClassName(
            receiver.activityInfo.packageName,
            receiver.activityInfo.name,
        )

        runCatching {
            context.sendBroadcast(intent)
        }.onFailure {
            Log.w(TAG, "Failed to send Shizuku start broadcast", it)
        }.isSuccess
    }
}
