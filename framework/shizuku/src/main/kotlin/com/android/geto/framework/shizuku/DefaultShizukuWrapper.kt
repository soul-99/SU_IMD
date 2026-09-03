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

    override suspend fun hasShizukuPermission(): Boolean = withContext(ioDispatcher) {
        ShizukuPermission.isRunning() && ShizukuPermission.hasPermission()
    }

    override suspend fun requestShizukuPermission(): Boolean = withContext(ioDispatcher) {
        ShizukuPermission.requestPermission()
    }

    override suspend fun forceStop(packageName: String): Boolean = withContext(ioDispatcher) {
        ShizukuPermission.forceStop(packageName = packageName)
    }

    override suspend fun allowRestrictedSettings(packageName: String): Boolean =
        withContext(ioDispatcher) {
            ShizukuPermission.allowRestrictedSettings(packageName = packageName)
        }

    override suspend fun allowBatteryUnrestricted(packageName: String): Boolean =
        withContext(ioDispatcher) {
            ShizukuPermission.allowBatteryUnrestricted(packageName = packageName)
        }

    override suspend fun grantWriteSecureSettings(packageName: String): ShizukuGrant =
        withContext(ioDispatcher) {
            ShizukuPermission.grantWriteSecureSettings(packageName = packageName)
        }

    override suspend fun grantDumpPermission(packageName: String): ShizukuGrant =
        withContext(ioDispatcher) {
            ShizukuPermission.grantDumpPermission(packageName = packageName)
        }

    override suspend fun allowUsageAccess(packageName: String): Boolean =
        withContext(ioDispatcher) {
            ShizukuPermission.allowUsageAccess(packageName = packageName)
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
            // Wakes the fork's manifest receiver even when its package is in the stopped
            // state - freshly booted and never opened, or force-stopped.
            addFlags(Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
        }

        // Diagnostic only, and never a gate. queryBroadcastReceivers enumerates *manifest*
        // receivers, and the case that matters most here is invisible to it: a fork whose
        // app is closed but whose service is running handles start and stop through a
        // receiver that service registered at runtime. An earlier build treated an empty
        // result as "nothing will receive this" and refused to send - so a running service
        // could no longer be told to stop, a stopped one could no longer be started, and
        // overlay hiding, which starts Shizuku through this same path, failed with them.
        // Its absence is logged and nothing more.
        val hasManifestReceiver = runCatching {
            context.packageManager.queryBroadcastReceivers(intent, 0)
        }.getOrDefault(emptyList()).isNotEmpty()

        if (!hasManifestReceiver) {
            Log.i(
                TAG,
                "No manifest receiver for $action in $packageName; sending package-scoped " +
                    "in case a running service handles it",
            )
        }

        // Aimed at the whole package rather than pinned to one component with setClassName.
        // A package-scoped broadcast reaches every receiver the fork exposes - the manifest
        // one and any the running service registered at runtime - which is what the earlier
        // working builds did. Pinning it to the manifest component would exclude exactly the
        // runtime receiver the closed-app-running-service case depends on.
        //
        // Whether the broadcast is acted on is not known from here and is not claimed:
        // StartShizukuUseCase confirms a start by polling the real running state, and the
        // services manager's live poll corrects a stop. True here means only that the
        // broadcast was dispatched.
        runCatching {
            context.sendBroadcast(intent)
        }.onFailure {
            Log.w(TAG, "Failed to send Shizuku $action broadcast to $packageName", it)
        }.isSuccess
    }
}
