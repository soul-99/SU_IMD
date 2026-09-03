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
 * What Auto-hide settings (IMD+) needs from the system before it can run.
 *
 * Every one of these is read live rather than stored, because every one of them can be taken
 * away by somebody who is not this app: a permission revoked in Android's settings, an
 * accessibility service switched off by the system after an update, a battery optimiser that
 * re-restricts an app it has not seen for a while. A stored copy would say IMD+ was on long
 * after it had stopped working, which is the one thing a feature like this must never do.
 *
 * [shizukuPermission] is the exception to "all of them are required" — see [satisfied].
 */
data class AutoHideRequirements(
    /** Shizuku has granted IMD its permission, so IMD can ask it to kill an app. */
    val shizukuPermission: Boolean = false,
    /**
     * Shizuku is not running, so its permission cannot be read at all — as opposed to having
     * been read and refused.
     *
     * The difference decides whether the IMD+ switch may stay on. A Shizuku that is simply
     * asleep answers "no permission" to every question, and treating that as a missing
     * requirement would switch IMD+ off on every device whose fork is not currently up — for a
     * permission that is very probably granted, and that IMD starts Shizuku to use anyway.
     */
    val shizukuUnreachable: Boolean = false,
    /**
     * Shizuku is configured **and** 'Manage Shizuku' is on — `UserData.manageShizukuEffective`.
     *
     * ⚠ **Not `isShizukuConfigured`, which is what this used to be fed.** With the master
     * switch off, every other gate in the app refuses to touch Shizuku while this row read
     * "met" and let IMD+ switch on: *"why is imd+ on if manage shizuku is off, should not its
     * shizuku config requirement also cover it?"* Named for what it means so the two cannot
     * drift apart again.
     */
    val shizukuManageable: Boolean = false,
    /**
     * The chosen fork answers start-stop intents — that is, it is Thedjchi.
     *
     * ⚠ **Its own field rather than folded into [shizukuManageable]**, because the row has to
     * tell the two refusals apart: 'Manage Shizuku' off is something the user can go and
     * switch on, and Shevery is not. The page reads this to decide whether to say so in red.
     */
    val forkSupported: Boolean = false,
    /** IMD's own accessibility service is enabled, which is what detects a launch. */
    val accessibilityEnabled: Boolean = false,
    /** IMD is exempt from battery optimisation, so it survives long enough to see the close. */
    val batteryUnrestricted: Boolean = false,
    /** IMD may post notifications, which is how the revert is offered. */
    val notificationsAllowed: Boolean = false,
    /** At least one app has been chosen for IMD+ to watch. */
    val appsChosen: Boolean = false,
    /** "Do not kill app on first launch" — from the user's configuration, not the system. */
    val noKillOnLaunch: Boolean = false,
) {
    /**
     * Whether Shizuku is needed at all.
     *
     * Force-stopping the launched app is the only thing IMD+ asks Shizuku for on its own
     * account — the revert hands straight over to "Revert to default" and closes nothing — so
     * this one checkbox decides the whole Shizuku question. Hiding "Display over other apps"
     * still needs Shizuku, but that is the hide's own requirement and it is enforced where the
     * hide happens: a device whose "Settings to hide" does not name overlay access can run
     * IMD+ with no Shizuku at all, and refusing to let it would be inventing a rule.
     */
    val shizukuNeeded: Boolean get() = !noKillOnLaunch

    /**
     * Whether Shizuku's side of the requirements is met.
     *
     * The configuration is always required when Shizuku is needed at all — without it IMD does
     * not know which fork to start. The permission is required only when it could actually be
     * read: see [shizukuUnreachable].
     *
     * ⚠ **[forkSupported] is deliberately not part of this.** It is not conditional on the
     * kill checkbox — see [satisfied].
     */
    val shizukuSatisfied: Boolean
        get() = !shizukuNeeded ||
            (shizukuManageable && (shizukuPermission || shizukuUnreachable))

    /**
     * Whether IMD+ may be switched on right now.
     *
     * ⚠ **[forkSupported] sits here, outside [shizukuSatisfied], and that is a decision rather
     * than an oversight.** Inside, it would only apply when a kill is wanted — and a Shevery
     * user who ticks "Do not kill app on first launch" asks Shizuku for nothing, so IMD+ would
     * run. The author was asked in those words and chose to block always: *"Also strip the
     * ability to use shevery for IMD+."* This overrides the argument in [shizukuNeeded]'s KDoc
     * that a device needing no Shizuku may run IMD+ with none.
     */
    val satisfied: Boolean
        get() = accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            forkSupported &&
            shizukuSatisfied

    /**
     * Everything is in place except IMD's own accessibility service.
     *
     * The one unmet requirement IMD can do something about on its own: the others are a
     * permission, a battery exemption, a Shizuku configuration or a list of apps, and every
     * one of those needs the user somewhere else. The detector is a secure setting IMD already
     * knows how to write — see `EnableAutoHideServiceUseCase`.
     *
     * Deliberately **not** `!satisfied && !accessibilityEnabled`: that is also true when three
     * other things are missing too, and silently switching the detector on then would leave
     * the feature just as off while claiming to have fixed it.
     */
    val onlyAccessibilityMissing: Boolean
        get() = !accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            // ⚠ The same term [satisfied] gained, and for the same reason: offering to switch
            // the detector on for a fork IMD+ will refuse anyway is offering nothing.
            forkSupported &&
            shizukuSatisfied
}

/**
 * The two requirements that can only be answered by asking something outside this app, and
 * that cost a binder call each to ask.
 *
 * Read together and cached for a screen rather than folded straight into
 * [AutoHideRequirements], because the settings page re-reads them on every resume and neither
 * is free: one goes through the accessibility manager, the other through Shizuku's binder.
 */
data class AutoHideServiceState(
    val accessibilityRunning: Boolean = false,
    val shizukuPermission: Boolean = false,
    /** Whether a Shizuku binder is alive right now — see [AutoHideRequirements.shizukuUnreachable]. */
    val shizukuRunning: Boolean = false,
    /**
     * The flattened component name of IMD's own detector, which only the framework layer can
     * build — half of it is this app's package name.
     *
     * Carried here rather than asked for separately because the one screen that needs it is the
     * one already reading this. Blank until the first read lands, and a blank name means "no
     * row is special", which is the safe way for the accessibility picker to start.
     */
    val ownDetector: String = "",
)

/**
 * Whether the IMD+ switch has to be held off because a hide is outstanding.
 *
 * IMD hides its own detector along with every other accessibility service, so while settings
 * are hidden IMD+ genuinely cannot work, and letting the switch be moved would only write an
 * answer that the next revert would have to undo. The switch reads off and refuses, and says
 * to finish the pending reverts first.
 *
 * Deliberately keyed on anything being hidden rather than on IMD+'s own run: a launch from
 * inside IMD, or the tile, leaves exactly the same accessibility services switched off.
 */
val UserData.autoHideBlockedByHide: Boolean get() = settingsHidden

/**
 * What the switch should read, as opposed to what the user last chose.
 *
 * Off whenever a hide is outstanding — see [autoHideBlockedByHide] — and off whenever the live
 * requirements are not met, whatever is stored. The stored answer is what a revert puts back,
 * which is why it is kept rather than overwritten.
 */
fun autoHideSwitchOn(
    userData: UserData,
    requirements: AutoHideRequirements,
): Boolean = userData.autoHideEnabled &&
    !userData.autoHideBlockedByHide &&
    requirements.satisfied

/**
 * Whether a launch from inside IMD can go ahead while IMD+ is holding settings down.
 *
 * The memory function is the awkward case. IMD+ hides the device-wide list; a per-app profile
 * asking for exactly those settings has nothing left to do, so the app is simply opened. One
 * asking for anything *else* cannot be satisfied without changing what IMD+ is holding, and
 * quietly hiding more would leave a device that neither mechanism's revert puts back — so that
 * launch is refused and says why.
 *
 * "Anything else" means anything the profile wants hidden that the device-wide list does not
 * already cover. A profile that hides *fewer* settings is not a conflict.
 */
fun autoHideCoversProfile(
    profileTargets: Set<ManualRevertTarget>,
    hiddenTargets: Map<ManualRevertTarget, Boolean>,
): Boolean = profileTargets.all { hiddenTargets[it] == true }

/**
 * Which of the manual targets a per-app profile actually hides.
 *
 * The bridge between the two vocabularies. A profile is a list of settings keys with values;
 * "Settings to hide" is a map of named targets. Comparing them is the whole of the conflict
 * test above, and it can only be done once both sides are speaking about the same things.
 *
 * Only settings that are enabled *and* switch something off count — a profile row that turns
 * developer options **on** is not something a hide could ever have covered, and treating it as
 * one would refuse a launch that has no conflict at all.
 *
 * The three keys with no target behind them are left out on purpose: the two markers
 * ([AppSettingKeys.SYSTEM_ALERT_WINDOW] and [AppSettingKeys.SHIZUKU_SERVICE]) are mapped
 * explicitly below, and anything else a profile writes is a setting IMD has no opinion about
 * and no hide would have touched either.
 */
fun profileHiddenTargets(appSettings: List<AppSetting>): Set<ManualRevertTarget> {
    val off = appSettings.filter { it.enabled && it.valueOnLaunch == "0" }.map { it.key }.toSet()

    val targets = mutableSetOf<ManualRevertTarget>()

    if (AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED in off) {
        targets += ManualRevertTarget.DeveloperSettings
    }

    if (AppSettingKeys.ADB_ENABLED in off) targets += ManualRevertTarget.UsbDebugging

    if (AppSettingKeys.ADB_WIFI_ENABLED in off) targets += ManualRevertTarget.WirelessDebugging

    if (AppSettingKeys.hidesAccessibilityServices(appSettings)) {
        targets += ManualRevertTarget.AccessibilityServices
    }

    // The two markers carry no value, so they are asked about rather than read out of `off`.
    if (AppSettingKeys.hidesOverlayAccess(appSettings)) {
        targets += ManualRevertTarget.DisplayOverOtherApps
    }

    if (AppSettingKeys.stopsShizukuService(appSettings)) targets += ManualRevertTarget.Shizuku

    return targets
}

/**
 * How long IMD+ leaves an app alone after [failures] runs in a row that hid nothing.
 *
 * A run that hides nothing leaves the detector listening and ends by relaunching the app, and
 * that relaunch is another foregrounding — so without a wait between them the two chase each
 * other with a force-stop and a Shizuku start on every lap, for as long as the cause lasts.
 *
 * One minute, then five, then thirty and no longer. The escalation is the point rather than any
 * one number: most causes are momentary — Shizuku not up yet, a write that lost a race — and a
 * minute breaks the chase without a user noticing. A cause that survives three attempts is a
 * revoked permission or a Shizuku that is not coming back, and the fourth attempt will go the
 * way of the third.
 *
 * Here rather than beside its caller because this is the part with arithmetic in it, and the
 * host tests can reach a pure function in this module — which is the only real verification
 * available for it.
 *
 * ⚠ **Clamped at both ends.** A zero or negative count is treated as the first failure rather
 * than reaching back past the start of the table, and everything past the third waits the cap.
 */
fun autoHideFailureBackoffMillis(failures: Int): Long =
    AUTO_HIDE_FAILURE_BACKOFF_MILLIS[
        (failures - 1).coerceIn(0, AUTO_HIDE_FAILURE_BACKOFF_MILLIS.lastIndex),
    ]

/**
 * The waits [autoHideFailureBackoffMillis] chooses between, shortest first.
 *
 * Thirty is the cap and matches the "nothing to hide" popup interval deliberately: both are the
 * interval for "this will still be true in a moment, and you already know".
 */
private val AUTO_HIDE_FAILURE_BACKOFF_MILLIS = longArrayOf(
    60L * 1000L,
    5L * 60L * 1000L,
    30L * 60L * 1000L,
)
