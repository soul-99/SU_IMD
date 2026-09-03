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

import android.os.SystemClock
import java.util.concurrent.ConcurrentHashMap

/**
 * Which apps auto unhide is waiting on, and since when.
 *
 * An entry is added by a hide that actually applied something *and* knew which app it was
 * for. A tile press knows no app and adds nothing — correctly, because there is no session to
 * watch, only a device the user put into a state by hand. The screen-lock backup still covers
 * that case, which is why it needs no entry.
 *
 * **An object rather than an injected singleton, and deliberately not in `domain/use-case`
 * beside [com.android.geto.domain.usecase.SettingsWorkTracker].** That tracker is signalled
 * from the four use cases, on the rule that eighteen call sites are eighteen chances to forget
 * one. This cannot follow it: the two hide use cases are pure Kotlin with no Android on the
 * classpath, and the anchors below need [SystemClock.elapsedRealtime] — while the device-wide
 * hide use case does not know the package name anyway, because a device-wide hide names no
 * app. So this is armed by the callers, which is also where the package name already is.
 *
 * The cost of missing a call site is therefore different, and much smaller: that hide is not
 * watched per app, and falls back to the screen-lock backup. Not a wrong revert — a slower
 * one.
 *
 * **In memory on purpose.** If the process is killed the entries go with it and the two
 * per-app triggers have nothing to act on, but `settingsHidden` is still stored and the
 * screen-lock backup needs no entry at all — so auto unhide degrades to slower, never to
 * never. Anchors written to disk would be worse than useless: they would outlive the session
 * they describe and fire a revert on some later cold start with nothing on screen to explain
 * why the device had just changed.
 */
object AutoUnhideWatch {

    /**
     * One watched app.
     *
     * **Two clocks, and both are needed.** [hiddenAtElapsed] measures the backup intervals,
     * on the monotonic clock, so that a time-zone change or a user setting the clock cannot
     * move them and they cannot run backwards. [hiddenAtWallClock] is compared against
     * process exit records, which Android timestamps in wall clock and which therefore cannot
     * be read with anything else. Using either one for both jobs is a bug that reads as the
     * trigger simply never firing.
     */
    data class Entry(
        val packageName: String,
        /**
         * The launcher component, and only under the memory function.
         *
         * Null means the device-wide list was hidden, whose revert names no app. Non-null is
         * that app's own record, which is what its revert has to put back — the distinction
         * r11 drew for IMD+, kept here for the same reason.
         */
        val componentName: String?,
        val hiddenAtWallClock: Long,
        val hiddenAtElapsed: Long,
    )

    private val entries = ConcurrentHashMap<String, Entry>()

    /**
     * Start watching [packageName], from now.
     *
     * Re-arming a package that is already watched replaces its anchors rather than keeping the
     * older pair. That is the answer the second launch deserves: the user has just started
     * using the app again, so the session that matters began now, and an exit record from
     * before it would otherwise end a session that has only just started.
     */
    fun arm(packageName: String, componentName: String? = null) {
        entries[packageName] = Entry(
            packageName = packageName,
            componentName = componentName,
            hiddenAtWallClock = System.currentTimeMillis(),
            hiddenAtElapsed = SystemClock.elapsedRealtime(),
        )
    }

    /**
     * Arm from a launch, given what its hide actually did.
     *
     * The three launch sites — the apps list, favourites and a pinned shortcut — read exactly
     * alike, so the shape of the call belongs here rather than being written out three times.
     * Whether [applied] is true is the one question they answer for themselves, through
     * `AppSettingsResult.leftSettingsHidden`.
     *
     * [componentName] is carried only under the memory function, because only that revert
     * needs to know which app's record to put back; a device-wide hide names no app and its
     * revert would not know what to do with one.
     */
    fun armIfApplied(
        applied: Boolean,
        componentName: String,
        memory: Boolean,
        collapsed: Boolean = false,
    ) {
        // ⚠ **Before the `applied` guard, not after it, and a standalone probe of this file
        // found the reason.** `leftSettingsHidden` is `Success || AlreadyHidden`, while the
        // notification is posted on `Success || Failure` — so a **failed** hide arriving into a
        // collapsed window posts a notification and, with the collapse behind the guard, would
        // have posted a *per-app* one beside the generic one. The collapse is a property of the
        // window rather than of what this particular hide managed to write.
        if (collapsed) collapse()

        if (!applied) return

        arm(
            packageName = componentName.substringBefore('/'),
            componentName = componentName.takeIf { memory && !collapsed },
        )
    }

    /**
     * Every outstanding session becomes one shared, device-wide debt.
     *
     * **Collapsing the notification and collapsing auto unhide are the same act**, which is why
     * they are one function. Nulling the component names puts every entry into
     * `AutoUnhideWatcher`'s device-wide branch, whose rule already reads: *a device-wide hide is
     * one shared debt, so it waits for the last of them.* That is the author's "auto unhide
     * should only run when all the apps with outstanding reverts are swiped away", in code that
     * has been on devices since r1 — rather than a second waiting rule beside the per-app branch
     * that reverts each app as its own session ends, which is the leak this exists to close.
     *
     * Iterated by key with a copied key list rather than over the map or by destructuring: this
     * is a `ConcurrentHashMap` the watcher reads on its own thread, and `(a, b) ->` on a map
     * entry is the `component1()/component2()` ambiguity that has already cost this project two
     * rounds.
     */
    fun collapse() {
        collapsed = true

        for (packageName in entries.keys.toList()) {
            val entry = entries[packageName] ?: continue

            if (entry.componentName == null) continue

            entries[packageName] = entry.copy(componentName = null)
        }
    }

    /** Everything currently watched. A copy, so the watcher can iterate while this changes. */
    fun watched(): List<Entry> = entries.values.toList()

    /** This app's session is over and has been dealt with. */
    fun forget(packageName: String) {
        entries.remove(packageName)
    }

    /** Nothing is hidden any more, however it came back. */
    fun clear() {
        entries.clear()

        // The chain is over with the debt. Left set, the next first launch would post the
        // generic notification instead of its own, with no cascade behind it to justify one.
        collapsed = false
    }

    /**
     * Whether the outstanding debt has been collapsed into one shared session.
     *
     * Read by `postAppliedSettingsNotification` to decide whether this hide gets its own per-app
     * notification or folds into the single generic one, and set by [collapse] a moment earlier
     * in the same launch — the arm and the notification are two steps of one flow.
     *
     * ⚠ **In memory, and the decision that sets it is not.** The launch sites derive the answer
     * from persisted records *before* they apply anything, so a process death does not break a
     * chain: the next launch reads the records, finds a debt outstanding, and collapses again.
     * This flag only has to survive the few milliseconds between the arm and the post.
     */
    @Volatile
    var collapsed: Boolean = false

    /**
     * Whether the watcher's foreground service is alive right now.
     *
     * Here rather than in the service because the thing that needs to ask is in another
     * module: when somebody swipes the service's notification away, a broadcast receiver has
     * to decide whether to put it back, and posting an **ongoing** notification for a service
     * that has since stopped would strand one in the shade with nothing left able to cancel
     * it.
     *
     * In memory, which is the safe direction: a process death resets it to false, and a
     * notification with no process behind it is exactly what must not be reposted.
     */
    @Volatile
    var serviceRunning: Boolean = false

    /**
     * Set the moment auto unhide begins putting settings back, so the service can take its
     * notification down at once rather than when the revert finishes.
     *
     * The author's rule: once unhiding has started the notification has nothing left to say,
     * and whether the revert succeeds or fails is reported by the revert's own notifications.
     * A watcher that held its "service running" entry up through eight seconds of Shizuku was
     * describing work that was already over.
     *
     * ⚠ **A signal rather than the service stopping itself**, and that distinction matters: the
     * revert runs on the service's own coroutine scope, so stopping the service here would
     * cancel the very work this is announcing. The service drops out of the foreground — which
     * is what removes the notification — and keeps running until the revert returns.
     *
     * Cleared by [reset] when a service starts, so a later session gets a fresh answer.
     */
    @Volatile
    var reverting: Boolean = false

    /** A new watcher session. Forgets whatever the last one was doing. */
    fun resetSession() {
        reverting = false
    }
}
