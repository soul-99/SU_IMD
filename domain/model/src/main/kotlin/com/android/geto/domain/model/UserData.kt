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

data class UserData(
    val theme: Theme,
    val dynamicTheme: Boolean,
    val sortLauncherAppsActivityInfo: SortLauncherAppsActivityInfo,
    val sortOrderLauncherAppsActivityInfo: SortOrderLauncherAppsActivityInfo,
    val showSystem: Boolean,
    val favouriteComponentNames: List<String>,
    val sortFavouriteApps: SortFavouriteApps,
    val favouriteAppsView: FavouriteAppsView,
    val iconStyle: IconStyle,
    val restartShizuku: Boolean,
    val shizukuForkMode: ShizukuForkMode,
    val shizukuAuthKey: String,
    val shizukuPackageName: String,
    val shizukuStartAction: String,
    val managedAccessibilityServices: List<String>,
    val heldAccessibilityServices: Map<String, List<String>>,
    val managedOverlayPackages: List<String>,
    val heldOverlayPackages: Map<String, List<String>>,
    val heldOverlayIdentities: Map<String, String>,
    val manageOverlay: Boolean,
    val taskerAuthKey: String,
    val taskerIntegrationEnabled: Boolean,
    val overlayRestoreFailed: Boolean,
    val autoRevertOnReturn: Boolean,
    val manualRevertTargets: Set<ManualRevertTarget>,
    val notificationFunction: NotificationFunction,
    /**
     * Which settings a launch hides, and how a hide is undone — the two halves v3 split
     * [notificationFunction] into.
     *
     * [notificationFunction] is **kept and still read**, but only by
     * `MigrateFrameworksUseCase`: it is the sole record of what an install chose before v3,
     * and an install can arrive from any older version at any time. Nothing else should read
     * it — a hide asks [hidingFramework], a revert asks [unhidingFramework].
     */
    val hidingFramework: HidingFramework,
    val unhidingFramework: UnhidingFramework,
    val revertDefaults: Map<ManualRevertTarget, Boolean>,
    /**
     * Which rows the settings manager draws, at the author's "Settings manager options".
     *
     * ⚠ **What is *shown*, not what is managed.** A row hidden here is not switched off, not
     * excluded from a hide, and not left out of "Revert to default" - it is simply not drawn.
     * Everything the engine does still follows [ManualRevertTarget.entries].
     *
     * One consequence is worth naming because it is the author's own instruction rather than a
     * side effect: the manager's All off / All on pill takes its list from what the card drew,
     * so a row hidden here stops being touched by the pill as well.
     */
    val managerRows: Map<ManualRevertTarget, Boolean>,
    /**
     * Whether the bottom-edge blur is drawn — the author's "Progressive UI blur".
     *
     * ⚠ **The positive reading of a field stored as its negation**, so that an install which
     * has never seen the switch gets the blur. The inversion happens once, in the data source;
     * nothing above it needs to know.
     *
     * ⚠ **Not the same question as whether a real blur is possible.** A blur of what is behind
     * needs API 31, and below that the band is the gradient alone — see `progressiveEdgeBlur`
     * in :design-system, which is where that split lives. This flag only says whether the band
     * is drawn at all.
     */
    val progressiveBlur: Boolean,
    /**
     * Pure black backgrounds instead of the dark scheme's near-black — "OLED background mode".
     *
     * ⚠ **Dark only.** It changes nothing in a light scheme, and the row that sets it is not
     * drawn while the app is light, at the author's instruction.
     */
    val oledBackground: Boolean,
    /** The author's r20 blur sliders: radius in dp, tint as a percentage, ramp length in dp. */
    val blurRadiusDp: Int,
    val blurTintPercent: Int,
    val blurFadeDp: Int,
    /**
     * Whether the Settings manager entry is published in the app drawer.
     *
     * ⚠ **On by default**, which is what the app has always done - installing IMD has put two
     * entries in the launcher since r2. Stored as its negation so that default costs nothing.
     */
    val drawerShortcutManager: Boolean,
    /**
     * And whether the Hide/unhide Settings entry is.
     *
     * ⚠ **Off by default, at the author's instruction.** It is a one-tap privileged change with
     * an exported door behind it; nobody gets it without asking for it.
     */
    val drawerShortcutHideUnhide: Boolean,
    /** Whether the one-time pass that made IMD+'s detector an ordinary selection has run. */
    val autoHideDetectorManagedV3: Boolean,
    val settingsToHide: Map<ManualRevertTarget, Boolean>,
    /**
     * Whether a **memory** restore may switch wireless debugging back on.
     *
     * Off for everybody until it is ticked, and the one setting in this app that defaults to
     * doing less than it could: a hide that is undone into wireless debugging being on leaves
     * the device listening on the network with nothing on screen saying so.
     *
     * ⚠ **Not read under [UnhidingFramework.RevertToDefault].** That framework drives
     * [revertDefaults], which carries its own wireless debugging row, and gating it here as
     * well would give one question two answers. The checkbox is drawn only under
     * [UnhidingFramework.Memory] for exactly that reason.
     *
     * ⚠ **Read by the settings manager's `All on` under both frameworks**, on the author's
     * instruction. That button is not a restore — it is a person asking for everything to be
     * switched on — but it is also the one press that could put wireless debugging back
     * without going anywhere near this setting, which is why it asks.
     */
    val restoreWirelessDebugging: Boolean,
    /**
     * Whether IMD manages Shizuku at all — the user's stored answer to the master switch.
     *
     * ⚠ **Not what the switch shows.** Read [manageShizukuEffective] for that: it is this
     * `&&` [isShizukuConfigured], so emptying a field in the Shizuku section drops the
     * switch without touching this answer, and filling it again puts the switch back where
     * the user left it. The author's "remembers the previous state", by construction.
     */
    val manageShizuku: Boolean,
    /** Whether the one-shot v3 migration for [manageShizuku] has already run. */
    val manageShizukuMigratedV3: Boolean,
    /** Whether the one-shot v3 reset of auto unhide's triggers and conditions has run. */
    val autoUnhideResetV3: Boolean,
    /**
     * Whether this install existed before v3.
     *
     * ⚠ **Not the same question as [setupNoticeVersion] being non-zero**, which is only "setup
     * has been completed once" — true of a fresh install a launch later. Decided once, by
     * `MigrateFrameworksUseCase`, at the last moment the two can still be told apart.
     */
    val upgradedToV3: Boolean,
    /**
     * Whether either configuration above was ever actually saved, as opposed to being the
     * default standing in for one that was not.
     *
     * The maps themselves cannot say: a never-saved configuration decodes to the default,
     * which is indistinguishable from somebody having saved exactly the default. Only the
     * migrations need the difference — it is what lets them tell an install that has been
     * behaving as an old default from one that chose its own answer.
     */
    val revertDefaultsConfigured: Boolean,
    val settingsToHideConfigured: Boolean,
    val settingsToHideDefaultsV21: Boolean,
    /**
     * Whether the device-wide "Settings to hide" is applied at this moment.
     *
     * Half of what [settingsHidden] answers, and the half nothing else can supply: a
     * "Settings to hide" run that named only the secure settings leaves no record behind, so
     * without this the app could not tell a hidden device from an untouched one. The other
     * half — whether the memory function is still holding an app's settings down — is derived
     * from the snapshots it stores, and so cannot fall out of step.
     */
    val settingsHiddenDeviceWide: Boolean,
    /**
     * Whether the user has switched on Auto-hide settings (IMD+).
     *
     * Their answer, and nothing more. Every requirement IMD+ depends on is read live from the
     * system, because any of them can be revoked by somebody else at any moment — so this on
     * its own never means "IMD+ is working", only "the user asked for it".
     */
    val autoHideEnabled: Boolean,
    /** The apps IMD+ watches for. It does nothing for anything not named here. */
    val autoHidePackages: List<String>,
    /**
     * "Do not kill app on first launch", off by default and recommended off.
     *
     * Also the only thing that decides whether IMD+ needs Shizuku: killing an app is the one
     * thing IMD+ asks Shizuku for on its own account.
     */
    val autoHideNoKillOnLaunch: Boolean,
    /**
     * What [autoHideEnabled] was before a hide took IMD's own accessibility service away.
     *
     * Parked rather than overwritten: the switch has to read off while the detector cannot
     * run, but the user never asked for it to be off, and a revert has to give back what they
     * chose rather than what the hide did to it.
     */
    val autoHideEnabledBeforeHide: Boolean,
    /** Whether the settings hidden right now are the ones IMD+ hid. */
    val autoHideRunning: Boolean,
    /**
     * Whether auto unhide is switched on.
     *
     * Only what the user asked for, exactly as [autoHideEnabled] is. Whether it can run is
     * read live, because every permission behind it can be taken away by somebody who is not
     * this app.
     */
    val autoUnhideEnabled: Boolean,
    /**
     * The watched app being swiped out of recents, or closed by "Close all".
     *
     * The precise trigger, and the only one that says the user is actually finished rather
     * than merely away. It is also the only one that cannot work below Android 11 — see
     * [AutoUnhideRequirements.exitReasonsSupported].
     */
    val autoUnhideOnSwipe: Boolean,
    /** The screen having stayed locked for [autoUnhideScreenLockMinutes]. */
    val autoUnhideOnScreenLock: Boolean,
    /** The watched app not having been in front for [autoUnhideIdleMinutes]. */
    val autoUnhideOnIdle: Boolean,
    /**
     * The two backup intervals, in minutes, already resolved.
     *
     * Never zero: the stored zero means "never written" and the data source substitutes the
     * defaults for it, so nothing downstream has to know that a zero was ever possible.
     */
    val autoUnhideScreenLockMinutes: Int,
    val autoUnhideIdleMinutes: Int,
    /**
     * Which kinds of hide auto unhide is allowed to end.
     *
     * [autoUnhideOnAppLaunch] covers every route that names an app — from inside IMD, from a
     * generated shortcut, and from IMD+. [autoUnhideOnTile] is the Hide settings tile, which
     * names none, so a session it starts can only ever be ended by the screen-lock backup.
     *
     * At least one is always true. Both false would be a feature switched on that can never
     * act, which is worse than off: the user would be waiting for settings that are not coming.
     */
    val autoUnhideOnAppLaunch: Boolean,
    val autoUnhideOnTile: Boolean,
    /**
     * Whether the diagnostic log is being recorded.
     *
     * Stored rather than held in memory so it survives a restart — a problem that only appears
     * after a reboot is exactly the kind worth having a log of.
     */
    val diagnosticsEnabled: Boolean,
    /**
     * Whether the user has ever switched IMD+ on themselves.
     *
     * Consent, recorded once, as opposed to [autoHideEnabled] which is the current
     * state. It is what lets the switch offer to put IMD's own detector back when the
     * detector is the only thing missing, instead of only refusing to move.
     */
    val autoHideEverEnabled: Boolean,
    val notificationFunctionResetV16: Boolean,
    val frameworksMigratedV3: Boolean,
    val revertDefaultsResetV166: Boolean,
    val revertDefaultsNoticePending: Boolean,
    val settingsManagerInfoShown: Boolean,
    val shizukuStartFailed: Boolean,
    val settingStateBefore: Map<String, Map<String, String?>>,
    val tipShown: Boolean,
    val obtainiumTipShown: Boolean,
    val setupNoticeVersion: Int,

    /**
     * Which revision of the "what changed" notice this install has already seen.
     *
     * Zero on a fresh install, which is also "never shown" — so it is always read
     * together with [setupNoticeVersion], the app's only record that an install
     * existed before today.
     */
    val settingsNoticeRevision: Int,
)
