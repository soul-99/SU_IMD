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
package com.android.geto.domain.model

/**
 * What Auto unhide settings needs from the system before it can run.
 *
 * Read live rather than stored, for the same reason [AutoHideRequirements] is: every one of
 * these can be taken away by somebody who is not this app — a permission revoked in Android's
 * settings, a battery optimiser that re-restricts an app it has not seen for a while. A stored
 * copy would say auto unhide was on long after it had stopped putting anything back, and a
 * feature whose whole job is to undo a hide must never claim to be watching when it is not.
 *
 * **Which requirements apply depends on which triggers the user ticked**, which is the one
 * structural difference from IMD+. There, one checkbox decided the whole Shizuku question;
 * here each trigger brings its own requirement and drops it again when unticked. A page with
 * only the screen-lock trigger on needs no permission at all beyond the two common ones.
 */
data class AutoUnhideRequirements(
    /**
     * IMD holds `android.permission.DUMP`, which is what lets it ask Android why *another*
     * app's process died.
     *
     * Granted once by `pm grant`, either through Shizuku from inside IMD or over adb from a
     * computer, and permanent afterwards. Nothing about the detection needs Shizuku again —
     * which matters, because Shizuku is very often dead during exactly the window auto unhide
     * has to watch, and is itself one of the things IMD hides.
     */
    val dumpPermission: Boolean = false,
    /**
     * Whether this Android version has `getHistoricalProcessExitReasons` at all — API 30.
     *
     * Below it there is no unprivileged way to learn that another app's task was removed, so
     * the swipe trigger is not offered rather than offered and quietly broken. The two backup
     * triggers work on every supported version.
     */
    val exitReasonsSupported: Boolean = false,
    /** IMD has usage access, which is what tells it the watched app left the foreground. */
    val usageAccess: Boolean = false,
    /** IMD is exempt from battery optimisation, so the watcher survives the hidden window. */
    val batteryUnrestricted: Boolean = false,
    /** IMD may post notifications, which is what the watcher's foreground service runs on. */
    val notificationsAllowed: Boolean = false,
    /**
     * "Hide from IMD, a shortcut or IMD+" — one of the two conditions a session is watched
     * under.
     *
     * Carried here since r4n because [satisfied] has to ask about it. See [anyUsedFor].
     */
    val onAppLaunch: Boolean = false,
    /** "Hide settings quick settings toggle" — the other condition. */
    val onTile: Boolean = false,
    /** "Swipe away from recents" — the user's choice, not the system's. */
    val onSwipe: Boolean = false,
    /** "Screen lock" — the user's choice. */
    val onScreenLock: Boolean = false,
    /** "App not in foreground" — the user's choice. */
    val onIdle: Boolean = false,
) {
    /**
     * Whether the swipe trigger is both ticked and possible.
     *
     * Deliberately not the same as [onSwipe]. The stored answer is kept as the user left it
     * even on a device that cannot honour it, so moving the same install to a newer Android —
     * or restoring a backup onto one — brings the trigger back rather than silently having
     * forgotten it.
     */
    val swipeChosen: Boolean get() = onSwipe && exitReasonsSupported

    /**
     * Whether anything at all would end a session.
     *
     * With no trigger ticked there is nothing for the watcher to wait for, so the feature
     * would sit switched on doing nothing — which is worse than being off, because the user
     * would believe their settings were going to come back.
     */
    val anyTrigger: Boolean get() = swipeChosen || onScreenLock || onIdle

    /**
     * Whether any kind of hide is watched at all.
     *
     * ⚠ **The same rule as [anyTrigger], from the other end, and it had to be written down when
     * the v3 reset unticked both conditions.** While they arrived on this could not be false,
     * so nothing asked. Now it can: a user who ticks a trigger and no condition would have the
     * switch reading on while `AutoUnhideWatcher.tick()` finds neither condition allowed and
     * settles immediately — a feature switched on that can never act, which is what the
     * paragraph on [anyTrigger] refuses.
     */
    val anyUsedFor: Boolean get() = onAppLaunch || onTile

    /** Only the swipe trigger reads exit reasons, so only it needs `DUMP`. */
    val dumpNeeded: Boolean get() = swipeChosen

    /** Only the idle trigger reads usage events. Screen lock needs no permission of any kind. */
    val usageNeeded: Boolean get() = onIdle

    val dumpSatisfied: Boolean get() = !dumpNeeded || dumpPermission

    val usageSatisfied: Boolean get() = !usageNeeded || usageAccess

    /**
     * Whether everything auto unhide needs from *outside* the app is in place.
     *
     * ⚠ **The four terms that are not the user's own ticks**, held apart from [satisfied] so a
     * blocked switch can say which kind of blocked it is. Telling somebody standing on the Auto
     * unhide settings page to "set up Auto unhide settings" is no answer when what is actually
     * missing is a permission granted somewhere else.
     */
    val permissionsSatisfied: Boolean
        get() = dumpSatisfied && usageSatisfied && batteryUnrestricted && notificationsAllowed

    /**
     * Whether auto unhide may be switched on right now.
     *
     * ⚠ **[onScreenLock] rather than [anyTrigger], and it is the author's failsafe.** Screen lock
     * is the one trigger that needs no permission, cannot be refused by a device, and fires on a
     * session nobody named an app for — so it is the backstop under the other two rather than an
     * alternative to them, and auto unhide is not allowed on without it.
     *
     * It *replaces* the older term instead of joining it: screen lock is one of the three
     * `anyTrigger` counts, so requiring it makes that test unreachable, and an unreachable term
     * beside a live one is where the rule gets misread later. `anyTrigger` itself stays — the
     * page uses it to say what is missing.
     */
    val satisfied: Boolean
        get() = onScreenLock &&
            anyUsedFor &&
            dumpSatisfied &&
            usageSatisfied &&
            batteryUnrestricted &&
            notificationsAllowed
}

/**
 * What the switch should read, as opposed to what the user last chose.
 *
 * Off whenever the live requirements are not met, whatever is stored — and the stored answer
 * is kept rather than overwritten, so a permission coming back brings the feature back with
 * it.
 *
 * Unlike [autoHideSwitchOn] there is no "blocked while settings are hidden" arm, and its
 * absence is the point: a hide being outstanding is not a reason auto unhide cannot work, it
 * is the only time auto unhide has anything to do. Switching it on midway through a hidden
 * window arms the backups for that window immediately; only the per-app triggers have nothing
 * to act on, because no watch entry was recorded when the hide happened.
 */
/**
 * The tile condition after the screen-lock trigger has been set to [onScreenLock].
 *
 * ⚠ **One invariant, written from both ends** — see [screenLockAfterTile] for the other. The
 * author's rule: *"only screen lock trigger is used by that QS condition"*. A session started
 * by the Hide settings tile names no app, and `AutoUnhideWatcher.tick()` has nothing to watch
 * leaving the foreground — so the screen-lock backup is the only thing that can ever end one,
 * and a tile condition without it is a promise the watcher cannot keep.
 *
 * Two functions rather than one, because which side gives way depends on which the user just
 * touched: unticking screen lock takes the tile with it, and unticking the tile leaves screen
 * lock alone.
 */
fun tileAfterScreenLock(onTile: Boolean, onScreenLock: Boolean): Boolean = onTile && onScreenLock

/**
 * The screen-lock trigger after the tile condition has been set to [onTile].
 *
 * The same invariant as [tileAfterScreenLock], from the other side: ticking the tile ticks
 * screen lock, and ticking screen lock leaves the tile alone.
 */
fun screenLockAfterTile(onScreenLock: Boolean, onTile: Boolean): Boolean = onScreenLock || onTile

fun autoUnhideSwitchOn(
    userData: UserData,
    requirements: AutoUnhideRequirements,
): Boolean = userData.autoUnhideEnabled && requirements.satisfied

/**
 * The three answers only Android can give about auto unhide's own access.
 *
 * Read together and cached for a screen, exactly as [AutoHideServiceState] is and for the same
 * reason: the settings page re-reads them on a one-second poll, and each is a real call —
 * a permission check, an AppOps lookup, and a version test.
 */
data class AutoUnhideChecks(
    val dumpPermission: Boolean = false,
    val usageAccess: Boolean = false,
    /**
     * Whether `getHistoricalProcessExitReasons` exists here at all — API 30.
     *
     * Carried alongside the two live reads rather than tested at the call site, so that the
     * one place that knows about Android versions is the framework layer.
     */
    val exitReasonsSupported: Boolean = false,
)

/**
 * Whether this outcome left the device with settings actually hidden.
 *
 * Which is the question auto unhide asks of a launch, and it is not the same as "the hide
 * succeeded". [AppSettingsResult.AlreadyHidden] means the settings were down before this
 * launch arrived — so this app is now part of the same hidden session and has to be watched
 * like any other, even though it wrote nothing itself. Everything else either changed nothing
 * ([AppSettingsResult.NothingToHide]) or failed, and watching an app whose settings were never
 * hidden would end a session that never began.
 */
val AppSettingsResult.leftSettingsHidden: Boolean
    get() = this == AppSettingsResult.Success || this == AppSettingsResult.AlreadyHidden

/**
 * Why a watched app's session ended, for the one line the log and the toast need.
 *
 * Kept as a type rather than a boolean because the three arrive by completely different
 * routes — a process exit record, a screen broadcast, a gap in the usage events — and when
 * something goes wrong on a device nobody here owns, which of the three fired is the first
 * thing worth knowing.
 */
enum class AutoUnhideReason {
    /** The app's process died with `REASON_USER_REQUESTED`: swiped away, or Close all. */
    Swiped,

    /** The screen stayed locked for the user's interval. */
    ScreenLocked,

    /** The app stayed out of the foreground for the user's interval. */
    Idle,
}
