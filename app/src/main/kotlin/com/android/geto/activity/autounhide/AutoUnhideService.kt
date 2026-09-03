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
package com.android.geto.activity.autounhide

import android.app.Notification
import android.app.NotificationManager
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import com.android.geto.broadcastreceiver.AutoUnhideWatcher
import com.android.geto.broadcastreceiver.buildAutoUnhideNotification
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.domain.common.Diagnostics
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper.Companion.AUTO_UNHIDE_NOTIFICATION_ID
import dagger.hilt.android.AndroidEntryPoint
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import javax.inject.Inject

/**
 * Keeps IMD alive for exactly as long as something is hidden, so [AutoUnhideWatcher] has a
 * process to look from.
 *
 * **A foreground service is not a choice here.** The one thing that would otherwise keep IMD
 * running — its own accessibility service — is deliberately switched off for the whole hidden
 * window, which is the constraint the entire feature is built around. Nothing else survives
 * Doze and an OEM task killer for the hours a forgotten session can last.
 *
 * **Started and stopped by the hidden state itself**, from a collector in `GetoApplication`,
 * rather than by each of the six places a hide can begin. That state is stored, so the service
 * comes back with the process after a kill, and a hide route added later is covered without
 * anyone remembering to wire it.
 */
@AndroidEntryPoint
class AutoUnhideService : Service() {

    @Inject
    lateinit var autoUnhideWatcher: AutoUnhideWatcher

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    /**
     * Whether the screen is on, which is the only time a recents swipe can happen.
     *
     * Starts true: the service is started by a hide, and a hide is something the user has just
     * done — so the screen was on a moment ago. Guessing the other way would make the first
     * swipe after every hide the slowest one.
     */
    @Volatile
    private var screenOn: Boolean = true

    /**
     * The screen going off starts the lock interval; it coming back on cancels it.
     *
     * Registered here rather than in the manifest because [Intent.ACTION_SCREEN_OFF] is only
     * delivered to receivers registered at run time — a manifest entry for it is silently
     * never called, which is the kind of bug that looks like the trigger simply not working.
     */
    private val screenReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context?, intent: Intent?) {
            when (intent?.action) {
                Intent.ACTION_SCREEN_OFF -> {
                    autoUnhideWatcher.onScreenOff()

                    screenOn = false
                }

                Intent.ACTION_SCREEN_ON -> {
                    autoUnhideWatcher.onScreenOn()

                    screenOn = true

                    // The device is demonstrably awake, which the timer below cannot count on
                    // while it is dozing. If the lock interval passed during the doze this is
                    // the first honest chance to act on it.
                    scope.launch { runTick() }
                }
            }
        }
    }

    override fun onCreate() {
        super.onCreate()

        AutoUnhideWatch.serviceRunning = true

        autoUnhideWatcher.reset()

        Diagnostics.log(tag = "svc", message = "auto unhide watcher started")

        ServiceCompat.startForeground(
            this,
            AUTO_UNHIDE_NOTIFICATION_ID,
            notification(),
            foregroundServiceType(),
        )

        registerReceiver(
            screenReceiver,
            IntentFilter().apply {
                addAction(Intent.ACTION_SCREEN_OFF)
                addAction(Intent.ACTION_SCREEN_ON)
            },
        )

        scope.launch {
            while (isActive) {
                if (runTick()) return@launch

                delay(if (screenOn) TICK_SCREEN_ON_MILLIS else TICK_SCREEN_OFF_MILLIS)
            }
        }

        // The notification comes down the moment unhiding starts, not when it finishes.
        //
        // ⚠ **Dropping out of the foreground, not stopping.** The revert runs on the scope
        // below, so stopSelf here would cancel the very work this is reacting to. Foreground
        // is given up — which is what removes the notification — and the service keeps running
        // until the tick that started the revert returns and settles it.
        //
        // Watched from a second coroutine because the first is blocked inside that revert. A
        // quarter-second poll of one volatile boolean, for as long as one revert takes.
        scope.launch {
            while (isActive) {
                if (AutoUnhideWatch.reverting) {
                    // Cleared first, so a swipe already in flight does not repost a
                    // notification this is about to take down.
                    AutoUnhideWatch.serviceRunning = false

                    ServiceCompat.stopForeground(
                        this@AutoUnhideService,
                        ServiceCompat.STOP_FOREGROUND_REMOVE,
                    )

                    Diagnostics.log(
                        tag = "svc",
                        message = "auto unhide reverting, notification withdrawn",
                    )

                    return@launch
                }

                delay(REVERT_WATCH_MILLIS)
            }
        }
    }

    /**
     * `START_STICKY`, so a service the system reclaims under pressure comes back.
     *
     * Being restarted with a null intent is fine: everything this needs is read fresh in
     * [AutoUnhideWatcher.tick], and the watch entries that did not survive the death are the
     * ones the screen-lock backup covers without them.
     */
    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int = START_STICKY

    override fun onDestroy() {
        super.onDestroy()

        // Cleared before anything else, so a swipe whose delete intent is still in flight
        // finds the answer already false rather than racing the teardown below.
        AutoUnhideWatch.serviceRunning = false

        Diagnostics.log(tag = "svc", message = "auto unhide watcher stopped")

        runCatching { unregisterReceiver(screenReceiver) }

        scope.cancel()
    }

    override fun onBind(intent: Intent?): IBinder? = null

    /** One look, stopping the service when the watcher says there is nothing left to watch. */
    private suspend fun runTick(): Boolean {
        val settled = runCatching { autoUnhideWatcher.tick() }.getOrDefault(false)

        if (settled) {
            ServiceCompat.stopForeground(this, ServiceCompat.STOP_FOREGROUND_REMOVE)

            stopSelf()

            return true
        }

        restoreNotificationIfDismissed()

        return false
    }

    /**
     * Puts the notification back after somebody has swiped it away.
     *
     * `setOngoing` holds it in place up to Android 13. From Android 14 a foreground service's
     * notification can be dismissed like any other and an app cannot opt out of that, so the
     * only honest way to keep this one on screen is to notice it has gone and post it again.
     *
     * **The backstop, not the main route.** A human swipe is caught by the `setDeleteIntent` on
     * the notification itself, which brings it back at once rather than within a tick — the
     * author asked for it to behave like the revert notifications, and a tick was visibly
     * slower. This catches every other way it can vanish: a `cancelAll` from a revert running
     * beside it, an OEM shade cleaner, a system reclaim. Both paths ask [AutoUnhideWatch] the
     * same liveness question before they post, so neither can leave an ongoing notification
     * standing with no service behind it and nothing left to ever cancel it.
     *
     * A failed query counts as "still showing" so that the one thing this can never do is post
     * a second copy.
     *
     * ⚠ **The liveness flag is checked first, and that check is not optional.** The coroutine
     * in [onCreate] takes this notification down deliberately when a revert starts, and clears
     * `serviceRunning` before it does. Without this guard the very next tick that returns
     * `false` — a partial revert with apps still watched returns exactly that — would see the
     * notification missing and post it straight back, which is the notification "returning
     * after the revert" that the withdrawal was written to prevent.
     */
    private fun restoreNotificationIfDismissed() {
        if (!AutoUnhideWatch.serviceRunning) return

        val manager = getSystemService(NotificationManager::class.java) ?: return

        val showing = runCatching {
            manager.activeNotifications.any { it.id == AUTO_UNHIDE_NOTIFICATION_ID }
        }.getOrDefault(true)

        if (showing) return

        Diagnostics.log(tag = "svc", message = "auto unhide notification dismissed, reposted")

        runCatching { manager.notify(AUTO_UNHIDE_NOTIFICATION_ID, notification()) }
    }

    /**
     * Silent, low, and collapsed — as close to out of the way as Android allows.
     *
     * It cannot be hidden. A foreground service must show a notification, and a channel at
     * `IMPORTANCE_MIN` is raised to `IMPORTANCE_LOW` by the system when a service posts to it,
     * so the floor is: no sound, no vibration, no badge, no heads-up, sorted to the bottom.
     *
     * Not ongoing-with-an-action like the revert notification: there is nothing to press. This
     * says the watcher is alive and nothing else, and the revert notification beside it is
     * still the way back by hand.
     */
    private fun notification(): Notification = buildAutoUnhideNotification(context = this)

    /**
     * `specialUse` from Android 14, where a type became mandatory and none of the named ones
     * describes "wait for the user to finish with somebody else's app".
     *
     * `dataSync` on 10 to 13 because that is what the platform offered then and what the
     * settings observer beside this already declares. Zero below 10, where the parameter did
     * not exist.
     */
    private fun foregroundServiceType(): Int = when {
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE ->
            ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE

        Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q ->
            ServiceInfo.FOREGROUND_SERVICE_TYPE_DATA_SYNC

        else -> 0
    }

    companion object {
        /** How closely the notification withdrawal watches for a revert starting. */
        private const val REVERT_WATCH_MILLIS = 250L

        /**
         * Five seconds with the screen on — **the half of the old flat fifteen that was too
         * slow**, and the only half a person can actually see.
         *
         * A recents swipe is the one trigger somebody is watching the result of: they put the
         * app away and look at the shade. Waiting up to fifteen seconds for the revert to start
         * read as it not having worked. The cost is bounded and small — one binder call for
         * exit records and one usage-events query per watched app — and it is only paid while
         * the screen is on, which is exactly when the device is not trying to sleep.
         */
        private const val TICK_SCREEN_ON_MILLIS = 5_000L

        /**
         * Thirty seconds with the screen off — **less often than the flat fifteen this
         * replaced**, not more.
         *
         * Nothing the screen-off state can produce is urgent. A recents swipe is impossible
         * with the screen off, so the only triggers left are the screen-lock and idle backups,
         * and both are measured in minutes. Polling every fifteen seconds through the night to
         * catch something that cannot happen was the wasteful half of the old interval.
         */
        private const val TICK_SCREEN_OFF_MILLIS = 30_000L

        fun start(context: Context) {
            runCatching {
                ContextCompat.startForegroundService(
                    context,
                    Intent(context, AutoUnhideService::class.java),
                )
            }
        }

        fun stop(context: Context) {
            runCatching { context.stopService(Intent(context, AutoUnhideService::class.java)) }
        }
    }
}
