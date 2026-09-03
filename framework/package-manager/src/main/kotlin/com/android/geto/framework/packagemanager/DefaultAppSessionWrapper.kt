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
package com.android.geto.framework.packagemanager

import android.Manifest
import android.app.ActivityManager
import android.app.AppOpsManager
import android.app.ApplicationExitInfo
import android.app.usage.UsageEvents
import android.app.usage.UsageStatsManager
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.os.Process
import com.android.geto.domain.common.dispatcher.Dispatcher
import com.android.geto.domain.common.dispatcher.GetoDispatchers
import com.android.geto.domain.framework.AppSessionWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.withContext
import javax.inject.Inject

/**
 * [AppSessionWrapper] over `ActivityManager` and `UsageStatsManager`.
 *
 * Every call here is wrapped in `runCatching`. Both of these APIs throw rather than answer
 * when the permission behind them is missing, and a permission can be revoked between the
 * page checking it and the watcher using it — so a throw is an ordinary outcome, not a bug,
 * and the honest answer to "did the user close it" in that state is "no evidence that they
 * did".
 */
internal class DefaultAppSessionWrapper @Inject constructor(
    @param:ApplicationContext private val context: Context,
    @param:Dispatcher(GetoDispatchers.IO) private val ioDispatcher: CoroutineDispatcher,
) : AppSessionWrapper {

    override val exitReasonsSupported: Boolean
        get() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.R

    override suspend fun hasDumpPermission(): Boolean = withContext(ioDispatcher) {
        context.checkSelfPermission(Manifest.permission.DUMP) ==
            PackageManager.PERMISSION_GRANTED
    }

    override suspend fun hasUsageAccess(): Boolean = withContext(ioDispatcher) {
        val appOps = context.getSystemService(AppOpsManager::class.java)
            ?: return@withContext false

        val mode = runCatching {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                appOps.unsafeCheckOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    context.packageName,
                )
            } else {
                @Suppress("DEPRECATION")
                appOps.checkOpNoThrow(
                    AppOpsManager.OPSTR_GET_USAGE_STATS,
                    Process.myUid(),
                    context.packageName,
                )
            }
        }.getOrNull()

        // MODE_DEFAULT means "fall back to the manifest permission", which for this op is
        // how a shell grant of PACKAGE_USAGE_STATS shows up. Checking the permission is the
        // only way to tell that apart from a plain refusal.
        when (mode) {
            AppOpsManager.MODE_ALLOWED -> true

            AppOpsManager.MODE_DEFAULT -> context.checkSelfPermission(
                Manifest.permission.PACKAGE_USAGE_STATS,
            ) == PackageManager.PERMISSION_GRANTED

            else -> false
        }
    }

    override suspend fun closedByUser(
        packageName: String,
        sinceMillis: Long,
    ): Boolean = withContext(ioDispatcher) {
        exitRecords(packageName = packageName, maxNum = EXIT_RECORDS_WATCHED).any { info ->
            info.timestamp >= sinceMillis && info.reason == ApplicationExitInfo.REASON_USER_REQUESTED
        }
    }

    override suspend fun lastForegroundAt(
        packageName: String,
        sinceMillis: Long,
    ): Long? = withContext(ioDispatcher) {
        val usageStatsManager =
            context.getSystemService(UsageStatsManager::class.java) ?: return@withContext null

        runCatching {
            val events = usageStatsManager.queryEvents(sinceMillis, System.currentTimeMillis())

            val event = UsageEvents.Event()

            var latest: Long? = null

            while (events.hasNextEvent()) {
                events.getNextEvent(event)

                if (event.packageName != packageName) continue

                if (event.eventType != EVENT_ACTIVITY_RESUMED) continue

                if (latest == null || event.timeStamp > latest) latest = event.timeStamp
            }

            latest
        }.getOrNull()
    }

    override suspend fun describeExits(
        packageName: String,
    ): List<String> = withContext(ioDispatcher) {
        if (!exitReasonsSupported) return@withContext listOf(NO_EXIT_API)

        val records = exitRecords(packageName = packageName, maxNum = EXIT_RECORDS_DIAGNOSTIC)

        if (records.isEmpty()) return@withContext listOf(NO_EXIT_RECORDS)

        records.map { info ->
            "reason=${info.reason} desc=${info.description} at=${info.timestamp} " +
                "process=${info.processName} importance=${info.importance}"
        }
    }

    override suspend fun describeEvents(
        sinceMillis: Long,
    ): List<String> = withContext(ioDispatcher) {
        val usageStatsManager =
            context.getSystemService(UsageStatsManager::class.java)
                ?: return@withContext listOf(NO_USAGE_API)

        runCatching {
            val events = usageStatsManager.queryEvents(sinceMillis, System.currentTimeMillis())

            val event = UsageEvents.Event()

            val lines = mutableListOf<String>()

            while (events.hasNextEvent()) {
                events.getNextEvent(event)

                lines += "type=${event.eventType} pkg=${event.packageName} at=${event.timeStamp}"
            }

            lines.ifEmpty { listOf(NO_USAGE_EVENTS) }
        }.getOrElse { listOf(NO_USAGE_ACCESS) }
    }

    /**
     * The raw records, or an empty list on anything at all going wrong.
     *
     * Guarded on the version *and* wrapped: the version test is what keeps the API off
     * Android 10 and below, and the `runCatching` is what survives a `DUMP` permission that
     * was granted when the page was drawn and revoked before the watcher looked.
     */
    private fun exitRecords(packageName: String, maxNum: Int): List<ApplicationExitInfo> {
        if (!exitReasonsSupported) return emptyList()

        val activityManager =
            context.getSystemService(ActivityManager::class.java) ?: return emptyList()

        return runCatching {
            activityManager.getHistoricalProcessExitReasons(packageName, 0, maxNum)
        }.getOrDefault(emptyList())
    }

    private companion object {
        /**
         * `UsageEvents.Event.ACTIVITY_RESUMED`, which is API 29, and
         * `UsageEvents.Event.MOVE_TO_FOREGROUND`, which is deprecated from the same release.
         *
         * They are one constant under two names and have been `1` in every release that has
         * either, so naming the number here avoids both a version guard and a deprecation
         * warning for a value that cannot move. Unlike an AppOp number — which really does
         * change between releases, hence the named ops in `ShizukuPermission` — this is a
         * frozen part of the public API.
         */
        const val EVENT_ACTIVITY_RESUMED = 1

        /**
         * Enough records to see past an app that died twice in the hidden window.
         *
         * A watched app can be killed for memory and restarted before the user closes it, and
         * only the newest record would then be the memory kill. Five covers that without
         * reading a history nobody asked for.
         */
        const val EXIT_RECORDS_WATCHED = 5

        const val EXIT_RECORDS_DIAGNOSTIC = 10

        const val NO_EXIT_API = "exit reasons: needs Android 11 or newer"

        const val NO_EXIT_RECORDS = "exit reasons: none recorded (or DUMP not granted)"

        const val NO_USAGE_API = "usage events: no UsageStatsManager on this device"

        const val NO_USAGE_EVENTS = "usage events: none in window"

        const val NO_USAGE_ACCESS = "usage events: refused (usage access not granted)"
    }
}
