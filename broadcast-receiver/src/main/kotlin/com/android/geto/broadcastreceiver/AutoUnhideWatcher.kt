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
package com.android.geto.broadcastreceiver

import android.content.Context
import android.os.SystemClock
import com.android.geto.common.AutoRevertPending
import com.android.geto.common.AutoUnhideWatch
import com.android.geto.common.showRestoredToast
import com.android.geto.domain.common.Diagnostics
import com.android.geto.domain.framework.AppSessionWrapper
import com.android.geto.domain.framework.PackageManagerWrapper
import com.android.geto.domain.model.AutoUnhideReason
import com.android.geto.domain.usecase.GetAutoUnhideSettingsUseCase
import com.android.geto.domain.usecase.GetSettingsHiddenUseCase
import com.android.geto.domain.usecase.RevertAppSettingsUseCase
import com.android.geto.domain.usecase.SettingsWorkTracker
import com.android.geto.framework.notificationmanager.AndroidNotificationManagerWrapper
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Decides when a hidden session is over, and puts the settings back when it is.
 *
 * The whole feature turns on one constraint: **IMD switches its own accessibility service off
 * whenever anything is hidden**, so the obvious way to notice the user finishing with an app —
 * watch it with the detector — is exactly the thing that is not running during the window this
 * has to watch. Shizuku is very often down for the same window and is itself one of the things
 * IMD hides. So everything here is unprivileged and asked for rather than delivered: process
 * exit records, usage events, and a screen broadcast.
 *
 * [tick] is called on a timer by the service that hosts this, and again the moment the screen
 * goes off. Nothing here runs on its own.
 */
@Singleton
class AutoUnhideWatcher @Inject constructor(
    @param:ApplicationContext private val context: Context,
    private val getAutoUnhideSettingsUseCase: GetAutoUnhideSettingsUseCase,
    private val getSettingsHiddenUseCase: GetSettingsHiddenUseCase,
    private val revertAppSettingsUseCase: RevertAppSettingsUseCase,
    private val settingsHiddenRunner: SettingsHiddenRunner,
    private val settingsWorkTracker: SettingsWorkTracker,
    private val appSessionWrapper: AppSessionWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val overlayRestoreRunner: OverlayRestoreRunner,
    private val notificationManagerWrapper: AndroidNotificationManagerWrapper,
) {
    /**
     * When the screen went off, on the monotonic clock, or null while it is on.
     *
     * Not a timestamp of "now minus the interval" but of the moment itself, so a screen that
     * comes back on before the interval is up simply clears it — an interrupted lock is not a
     * shorter lock, it is not a lock at all.
     */
    @Volatile
    private var screenOffAt: Long? = null

    /**
     * One revert at a time.
     *
     * The timer and the screen-off broadcast can both reach [tick], and a revert takes long
     * enough — Shizuku may have to be started for the overlay step — that the next tick would
     * otherwise arrive in the middle of it and start a second one over the top.
     */
    private val mutex = Mutex()

    fun onScreenOff() {
        screenOffAt = SystemClock.elapsedRealtime()
    }

    fun onScreenOn() {
        screenOffAt = null
    }

    /** Called when the service starts, so a stale lock time cannot survive into a new session. */
    fun reset() {
        screenOffAt = null

        AutoUnhideWatch.resetSession()
    }

    /**
     * Look once, and revert whatever has finished.
     *
     * Returns **true when there is nothing left to watch** — either because everything has
     * been put back, or because the feature has been switched off underneath it. The service
     * that calls this stops itself on true; the alternative is a foreground service and its
     * notification outliving the reason they exist.
     */
    suspend fun tick(): Boolean = mutex.withLock {
        val settings = getAutoUnhideSettingsUseCase()

        if (!settings.enabled || !settings.anyTrigger) {
            AutoUnhideWatch.clear()

            return@withLock true
        }

        val hidden = getSettingsHiddenUseCase()

        // Somebody else already put it back - a press of the notification, the tile, auto
        // revert on returning to IMD. Nothing left to do and nothing left to watch.
        if (!hidden.deviceWide && !hidden.memory) {
            AutoUnhideWatch.clear()

            return@withLock true
        }

        val watched = AutoUnhideWatch.watched()

        // Which kind of session this is, and whether the user asked for that kind to be ended
        // automatically at all.
        //
        // Decided here rather than at the four places a watch entry is armed, because the
        // answer is already sitting in front of this: an entry exists only when a hide named
        // an app, so entries present means an app launch and entries absent means the tile.
        // Gating at the arm sites instead would have been four chances to forget one, and the
        // tile - which arms nothing - could not have been gated there at all.
        val allowed = if (watched.isEmpty()) settings.onTile else settings.onAppLaunch

        if (!allowed) {
            Diagnostics.log(
                tag = "unhide",
                message = "settled: session kind not enabled, watched=${watched.size} " +
                    "onAppLaunch=${settings.onAppLaunch} onTile=${settings.onTile}",
            )

            // Settled, not merely skipped, and the difference is the whole of this fix. A
            // session kind the user has switched off is one this watcher will never act on,
            // however many times it is asked: the answer cannot change while the session
            // lasts, because the kind is fixed the moment the hide names an app or does not.
            // Returning false left the service running and its notification in the shade for
            // the entire hidden window, ticking every fifteen seconds to reach this same line
            // - which is exactly what the author reported.
            //
            // The watch is deliberately **not** cleared. Its entries are still true statements
            // about what is hidden, and the session is still standing; only the watching stops.
            return@withLock true
        }

        // A hide or a revert is running right now, from wherever. Looking at exit records in
        // the middle of one would be reading a device that is halfway between two states.
        if (settingsWorkTracker.inFlightNow) return@withLock false

        val now = SystemClock.elapsedRealtime()

        // The screen-lock backup answers for the whole session rather than for one app, and
        // it is the only trigger that covers a hide with no app behind it at all - a tile
        // press names nothing to watch, so this is all it ever gets.
        if (settings.onScreenLock) {
            val since = screenOffAt

            if (since != null && now - since >= settings.screenLockMillis) {
                Diagnostics.log(
                    tag = "unhide",
                    message = "session ended reason=ScreenLocked lockedFor=${now - since}ms",
                )

                revertEverything()

                return@withLock true
            }
        }

        if (watched.isEmpty()) return@withLock false

        val ended = watched.associateWith { entry ->
            sessionEnded(entry = entry, settings = settings, now = now)
        }

        // Under the memory function each app owns its own record and its own notification, so
        // each one's session ends on its own account and takes only its own settings with it.
        // Iterated by key rather than destructured, on the standing rule in this project:
        // `(a, b) ->` on a map or a pair is the component1()/component2() ambiguity that has
        // already cost two rounds - HideTileService's flow collector, then AutoHideRunner's
        // arming collector. Cheap to avoid, and it reads no worse.
        // ⚠ **The whole loop is NonCancellable, not only the revert inside it.** This is the
        // author's report: `AutoUnhideService` drops out of the foreground the moment
        // `reverting` is set and can be destroyed within milliseconds, which cancels this
        // scope - and `revertAppSettingsUseCase` waits on adbd for over a second before it
        // returns. `revertOneProfile` guarded its own writes and toast; everything after it
        // was left outside, so the forget below and the settle at the end of this function
        // were skipped on every revert that outlived the service. His log:
        //
        //     23:39:51.913  svc auto unhide watcher stopped
        //     23:39:53.943  revert app ... -> Success
        //
        // Device restored two seconds after the scope died, with the offer still in the shade.
        withContext(NonCancellable) {
            for (watchedEntry in ended.keys) {
                val componentName = watchedEntry.componentName ?: continue

                if (ended[watchedEntry] == null) continue

                Diagnostics.log(
                    tag = "unhide",
                    message = "session ended pkg=${watchedEntry.packageName} " +
                        "reason=${ended[watchedEntry]} mode=memory",
                )

                revertOneProfile(componentName = componentName)

                AutoUnhideWatch.forget(watchedEntry.packageName)
            }
        }

        // A device-wide hide is one shared debt, so it waits for the last of them. Putting the
        // settings back while a second app that was launched into the same hidden window is
        // still open would show that app everything it was hidden from.
        val deviceWide = ended.filterKeys { it.componentName == null }

        if (deviceWide.isNotEmpty() && deviceWide.values.all { it != null }) {
            Diagnostics.log(
                tag = "unhide",
                message = "session ended apps=${deviceWide.size} mode=deviceWide " +
                    "reasons=${deviceWide.values.joinToString()}",
            )

            revertEverything()

            return@withLock true
        }

        // ⚠ **NonCancellable for the reason above.** This is the only thing on the per-app
        // path that takes the offer notification down, and it is the statement the author's
        // report landed on.
        withContext(NonCancellable) { settledIfNothingLeft() }
    }

    /**
     * Which trigger, if any, says this app is finished with.
     *
     * Swipe first because it is evidence rather than inference: the user actually ended the
     * app. The idle interval is a guess about a user who walked away, and a guess should not
     * pre-empt a fact.
     */
    private suspend fun sessionEnded(
        entry: AutoUnhideWatch.Entry,
        settings: GetAutoUnhideSettingsUseCase.Settings,
        now: Long,
    ): AutoUnhideReason? {
        if (settings.onSwipe &&
            appSessionWrapper.closedByUser(
                packageName = entry.packageName,
                sinceMillis = entry.hiddenAtWallClock,
            )
        ) {
            return AutoUnhideReason.Swiped
        }

        if (!settings.onIdle) return null

        val lastForeground = appSessionWrapper.lastForegroundAt(
            packageName = entry.packageName,
            sinceMillis = entry.hiddenAtWallClock,
        ) ?: entry.hiddenAtWallClock

        // Two clocks have to agree, and that is not belt and braces for its own sake. Usage
        // events are timestamped in wall clock, so the gap they describe can only be measured
        // in wall clock - and a user moving the device clock forward would otherwise be enough
        // to fire this on its own. The monotonic arm cannot be fooled that way, and it can
        // never hold back a real one: an app that has been unused for the interval has also
        // been hidden for at least that long, because the hide came first.
        val idleByWallClock = System.currentTimeMillis() - lastForeground >= settings.idleMillis

        val idleByElapsed = now - entry.hiddenAtElapsed >= settings.idleMillis

        return if (idleByWallClock && idleByElapsed) AutoUnhideReason.Idle else null
    }

    /**
     * One app's own record, under the memory function.
     *
     * The notification is cancelled here rather than left to the revert, for the reason
     * [AutoRevertRunner] cancels it too: it is posted under the component name's hash code and
     * would otherwise sit there offering to undo a device that has already been put back.
     *
     * ⚠ **It says so now, and r12's reasoning for silence only ever covered one trigger.** That
     * comment argued there is nobody in front of the screen — true of the screen-lock timer,
     * which does not come through here at all: it calls [revertEverything]. The two triggers
     * that do reach this are a swipe-away and an idle timeout, and both happen with the screen
     * on and the user holding the phone. The author's instruction is a completion toast on
     * every hide and every unhide.
     *
     * ⚠ **`NonCancellable`, and it is the whole point of this function finishing at all.**
     * This runs on `AutoUnhideService`'s own scope, which `onDestroy` cancels; the service
     * drops out of the foreground the moment a revert starts and can be reclaimed within
     * milliseconds of doing so. `RevertAppSettingsUseCase` writes the settings early and then
     * waits 1.5s for adbd before it returns, so a cancellation lands squarely between the
     * writes and the two statements below - leaving a restored device with its notification
     * still in the shade and nothing said about it. Measured on the author's device: every
     * auto unhide revert followed by `watcher stopped` logged no result, and the one that ran
     * while another entry kept the service alive logged its result 518ms later.
     */
    private suspend fun revertOneProfile(componentName: String) = withContext(NonCancellable) {
        // Before the work, as on the device-wide path. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        revertAppSettingsUseCase(componentName = componentName)

        // ⚠ **For a notification left standing by a build before r3**, as in AutoRevertRunner:
        // nothing posts under a component name's hash code since the per-app route went, and
        // cancelling an id nothing holds costs nothing.
        notificationManagerWrapper.cancel(componentName.hashCode())

        // Same shape as [AutoRevertRunner]'s memory branch, and for the same reason: the
        // overlay step is deliberately allowed to fail without failing the rest of the
        // profile, so its outcome is reported here or nowhere. Saying "reverted from memory"
        // over a device that did not get its overlay access back would be the wrong news.
        // Shizuku is never a target of a per-app revert, so only the one message applies.
        if (!overlayRestoreRunner.reportIfFailed()) {
            context.showRestoredToast(
                fromMemory = true,
                appName = packageManagerWrapper.getActivityLabel(componentName = componentName),
            )
        }
    }

    /**
     * Every debt that actually exists.
     *
     * [SettingsHiddenRunner.flushPendingReverts] rather than its `unhide`, and the difference
     * matters: `unhide` is the tile's behaviour, which reverts to default even when nothing is
     * hidden because a tile that did nothing would read as broken. Nobody pressed anything
     * here, so this must settle what is outstanding and otherwise leave the device alone.
     *
     * It also routes an IMD+ hide into IMD+'s own revert, which force-stops the watched apps
     * before restoring anything — so that path stays correct without this knowing about it.
     *
     * The toast comes from the revert underneath, which is the only thing that knows which
     * framework acted. On the screen-lock trigger nobody sees it, and that is fine: a toast
     * over a dark screen costs nothing, and inventing a way to suppress it per trigger would
     * mean this deciding what the revert below is allowed to say.
     *
     * ⚠ **`NonCancellable`, for the reason on [revertOneProfile].** The device-wide path
     * sweeps its notifications before the work rather than after, so what a cancellation costs
     * here is the watch and the pending-revert record never being cleared and the completion
     * toast never being said - a device that is back to normal and still believes it owes.
     */
    private suspend fun revertEverything() = withContext(NonCancellable) {
        Diagnostics.log(tag = "revert", message = "auto unhide: flushPendingReverts")

        // Before the work, not after it. See AutoUnhideWatch.reverting.
        AutoUnhideWatch.reverting = true

        // ⚠ **Swept before the revert, not after it, and the order is load-bearing.** This is a
        // cancelAll, and afterwards was late enough to catch the two notifications the revert
        // raises about *itself* — overlay access it could not give back, a Shizuku it could not
        // restart. Both were posted and then wiped a moment later by the same run, leaving a
        // failure the user was never told about. Everything this is here to clear is already
        // standing before the revert begins.
        clearRevertNotifications()

        settingsHiddenRunner.flushPendingReverts()

        AutoUnhideWatch.clear()

        // The debt this was armed for has just been paid. AutoRevertPending's own words for
        // the case: "used when the user reverts by hand first ... firing again on return would
        // be a second revert of nothing".
        AutoRevertPending.clear()
    }

    /**
     * Clears every notification that offers to undo a hide that is now undone.
     *
     * **Not left to the revert paths, and r12 shipped with that gap.** `RevertToDefaultRunner`
     * does call `cancelAll`, but the per-app memory route never reaches it: that route cancels
     * only the one app's notification, keyed on its component name's hash, so IMD+'s own —
     * posted under a fixed id — was left standing. Every auto unhide path now ends here
     * instead of relying on which revert happened to run.
     *
     * `cancelAll` rather than the two ids, because a memory sweep can leave several per-app
     * notifications up and each is keyed on a hash this does not have. The watcher's own
     * foreground-service notification survives it: Android keeps a foreground service's
     * notification regardless, and the service stops moments later anyway.
     */
    private fun clearRevertNotifications() {
        notificationManagerWrapper.cancelAll()
    }

    /**
     * Whether the per-app reverts above happened to finish the job.
     *
     * Asked rather than assumed, because a memory sweep that puts back the last outstanding
     * profile leaves nothing hidden — and the service should stop then, not on the next tick.
     */
    private suspend fun settledIfNothingLeft(): Boolean {
        // ⚠ **The same question, asked in one place.** Four revert paths needed this answer
        // and each had its own version or none - see SettingsHiddenRunner for why the offer
        // can only be cleared when nothing is left hidden.
        if (!settingsHiddenRunner.clearRevertOfferIfSettled()) return false

        // The one thing the sweep above must not take with it. [revertOneProfile] runs before
        // this line and can leave overlay access still owed; its report is the only notice the
        // user gets, and cancelAll does not know to spare it. Re-raised rather than reordered
        // because the per-app reverts happen in a loop further up, with no single point before
        // the sweep to put this at. Reads a stored flag, so it is silent unless something
        // really is outstanding.
        overlayRestoreRunner.reportIfFailed()

        AutoUnhideWatch.clear()

        AutoRevertPending.clear()

        return true
    }
}
