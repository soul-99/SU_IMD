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
 * What the "Manage Display over other apps" switch in Advanced actually does.
 *
 * Overlay access is the one thing IMD touches that cannot be written at all without a
 * correctly configured Shizuku service. On a device without one every overlay row is a
 * control that can only fail, so the whole feature is off by default and the rows for it
 * only appear once someone has said they want it.
 *
 * The asymmetry below is the important part: hiding is gated on the switch and restoring is
 * not. Switching the feature off has to stop IMD taking overlay access away, but it must
 * never abandon access already taken - an app left without a permission IMD withdrew, with
 * every screen that could give it back now hidden, is a worse outcome than the feature being
 * on.
 */

/**
 * The rows a configuration dialog shows, and the denominator of its "x of y" summary.
 *
 * Removing the entry rather than forcing it to false is deliberate: `size` is what the
 * summary counts, so a row that is not shown must not be counted either.
 */
fun Map<ManualRevertTarget, Boolean>.withoutOverlayWhenUnmanaged(
    manageOverlay: Boolean,
): Map<ManualRevertTarget, Boolean> = if (manageOverlay) {
    this
} else {
    this - ManualRevertTarget.DisplayOverOtherApps
}

/**
 * The stored hide configuration, or what this install has been behaving as while it has none.
 *
 * v2.1 changed what a never-configured install falls back to, from the four secure settings to
 * nothing. MigrateRevertDefaultsUseCase writes the old map down for every install that
 * predates the change, so the change only ever reaches a first run — but that migration runs
 * on a coroutine at process start, and a shortcut can fire a launch in the same instant. This
 * says the same thing the migration is about to persist, so the two cannot disagree in the
 * window between the process starting and the write landing.
 *
 * Three questions, in order: has the dialog ever been saved (then that answer wins); has the
 * migration already run (then the stored fallback is the answer it left); and did this install
 * exist before the change (then the old default is what it has been doing all along). A first
 * run answers no to all three and gets the new default, which is the point.
 */
private val UserData.settingsToHideOrLegacy: Map<ManualRevertTarget, Boolean>
    get() = if (
        !settingsToHideConfigured &&
        !settingsToHideDefaultsV21 &&
        setupNoticeVersion != 0
    ) {
        SettingsToHide.LegacyDefault
    } else {
        settingsToHide
    }

/**
 * Whether IMD can act on [target] at all right now - the same tests the greyed rows in the two
 * configuration dialogs, the settings manager and the per-app config page all ask.
 *
 * ⚠ **One answer, read by the drawing and by the engine.** A row that greys and a hide that
 * skips have to agree, and they only agree for certain when they are the same expression.
 * Every gap this closed was a place where the dialog knew and the use case did not: with
 * 'Manage Shizuku' off a device-wide hide still stopped the service, and with the
 * accessibility picker empty it still wrote `accessibility_enabled`. Both reach IMD+, which
 * runs this map like every other launch route.
 *
 * ⚠ **Hiding, not reverting.** Restoring something IMD has already switched off is never
 * gated - the asymmetry this file opens with, and [effectiveRevertDefaults] keeps it.
 *
 * ⚠ **An exhaustive `when`, so a seventh target cannot arrive without a decision.** The three
 * unconditional ones are Settings rows IMD writes directly and needs nothing else for.
 */
fun UserData.canHide(target: ManualRevertTarget): Boolean = when (target) {
    ManualRevertTarget.DisplayOverOtherApps -> overlayManageable

    ManualRevertTarget.AccessibilityServices -> accessibilityManageable

    ManualRevertTarget.Shizuku -> manageShizukuEffective && shizukuForkMode.supportsIntents

    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.WirelessDebugging,
    -> true
}

/**
 * "Settings to hide" as the launch path should read it.
 *
 * ⚠ **Every target [canHide] refuses is forced to false here**, which is what makes the
 * author's rule - a disabled toggle does not run - true of the engine and not only of the
 * dialog. It used to gate the overlay entry alone.
 *
 * False rather than dropped, as the overlay entry always was: the hide loop asks each target
 * whether it is wanted and an absent entry already means no, so the explicit false says the
 * same thing and keeps the map's shape stable.
 *
 * ⚠ **And that now holds for every target, including Shizuku on a fork with no intents.** This
 * used to end with [withoutShizukuWhenNoIntents], which dropped that entry and contradicted the
 * paragraph above. It only mattered because the Shizuku row was not drawn on Shevery - r4n
 * draws it, and this map is what the dialog's "x of y switched on" line counts, so a dropped
 * entry would say "of five" under six rows. Exactly the defect [withoutOverlayWhenUnmanaged]
 * used to cause for Display over other apps.
 *
 * Safe because every reader asks `== true` or `none { it.value }`, for which absent and false
 * are the same answer. ⚠ **[effectiveRevertDefaults] keeps its drop and must**: the revert path
 * asks `wanted[target]?.let`, where a false entry *would* enter the branch and try to restart a
 * service IMD has no intent for.
 *
 * ⚠ **Hiding only.** [effectiveRevertDefaults] is deliberately not gated the same way.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = ManualRevertTarget.entries
        .fold(settingsToHideOrLegacy) { map, target ->
            if (canHide(target)) map else map + (target to false)
        }

/**
 * "Revert to default" as the revert path should read it.
 *
 * Three cases rather than two. With the feature on the stored answer wins. With it off and
 * nothing owed the entry disappears, so the revert neither hides nor restores and does not
 * report the target at all. With it off and a debt outstanding the entry reads true, which
 * is what makes a revert still hand back access taken while the feature was on - a restore
 * can only put back what IMD itself withdrew, so it can never grant anything new.
 */
val UserData.effectiveRevertDefaults: Map<ManualRevertTarget, Boolean>
    get() = when {
        overlayManageable -> revertDefaults

        heldOverlayPackages.isNotEmpty() ->
            revertDefaults + (ManualRevertTarget.DisplayOverOtherApps to true)

        else -> revertDefaults - ManualRevertTarget.DisplayOverOtherApps
    }.withoutShizukuWhenNoIntents(mode = shizukuForkMode)

/**
 * Drops the Shizuku entry for a fork family that has no start or stop intent.
 *
 * Shevery cannot be told anything. Its service goes down when the debugging transport does and
 * comes back when its own ErrorProtect watchdog notices the transport again, so "hide the
 * Shizuku service" and "unhide it on revert" are not choices IMD can carry out - the debugging
 * rows already decide both. The entry is removed rather than forced false so the two paths that
 * read these maps skip the target entirely: the hide loop asks `wanted[target] == true`, and the
 * revert asks `wanted[target]?.let`, which an absent key does not enter at all.
 *
 * Removing rather than forcing also keeps the settings summaries honest, for the same reason
 * [withoutOverlayWhenUnmanaged] does it: `size` is what the "x of y" line counts, and a row that
 * is not shown must not be counted.
 */
fun Map<ManualRevertTarget, Boolean>.withoutShizukuWhenNoIntents(
    mode: ShizukuForkMode,
): Map<ManualRevertTarget, Boolean> = if (mode.supportsIntents) {
    this
} else {
    this - ManualRevertTarget.Shizuku
}

/**
 * The manual target a per-app setting key stands for, or null for an ordinary Settings row.
 *
 * Only three keys mean anything beyond "write this": the two markers, which have no Settings
 * row behind them at all, and the accessibility flag, which IMD drives through its own managed
 * list rather than by writing the flag.
 */
fun manualTargetForKey(key: String): ManualRevertTarget? = when (key) {
    AppSettingKeys.SYSTEM_ALERT_WINDOW -> ManualRevertTarget.DisplayOverOtherApps

    AppSettingKeys.SHIZUKU_SERVICE -> ManualRevertTarget.Shizuku

    AppSettingKeys.ACCESSIBILITY_ENABLED -> ManualRevertTarget.AccessibilityServices

    else -> null
}

/**
 * Whether a per-app template or row names something IMD cannot act on right now.
 *
 * ⚠ **Replaces the two filters that used to remove these rows from the page.** The author's
 * instruction is to show them and grey them - *"grey out their templates in per app config
 * page (if already added) and per app config page setting templates"* - so the page needs a
 * question it can ask per row rather than a list with holes in it.
 *
 * ⚠ **It asks [canHide], which is what the hide itself asks.** A greyed template and a skipped
 * hide cannot drift apart while they are the same expression, and drifting apart is exactly
 * what the removed filters allowed: they hid the Shizuku marker on a fork with no intents while
 * [ApplyAppSettingsUseCase] went on stopping the service anyway.
 *
 * Nothing is removed from storage either way. The Room row and the asset template are
 * untouched, so a row comes back - in every app it was added to - the moment the thing it
 * needs is configured again.
 */
fun appSettingBlocked(userData: UserData, key: String): Boolean =
    manualTargetForKey(key = key)?.let { !userData.canHide(target = it) } == true

/**
 * Whether every package IMD is set to manage already has its overlay access withdrawn by IMD.
 *
 * The repeat-launch fail-safe both hide paths share. A hold under
 * [AccessibilityServicePlan.DEVICE_WIDE_HOLD] means IMD took that package's overlay access
 * away and has not given it back — nothing else writes that record, and only a restore clears
 * it — so a selection every member of which is already held has nothing left to withdraw, and
 * the ten-second Shizuku start that withdrawing needs can be skipped.
 *
 * An empty selection is settled by definition: there is nobody to take anything away from.
 *
 * Deliberately not the live "is overlay access allowed" reading. That comes from a Shizuku
 * query which reports "nothing is allowed" when it cannot be answered at all, so trusting it
 * would skip the work and report success with overlay access still granted. This record needs
 * no Shizuku to read and cannot be wrong in that direction: at worst a package added to the
 * selection since the hide is missing from it, and the answer is then false and the full step
 * runs — a wasted start rather than a silent failure to hide.
 */
fun overlayAlreadyWithdrawn(
    managedOverlayPackages: List<String>,
    heldOverlayPackages: Map<String, List<String>>,
): Boolean {
    val held = heldOverlayPackages[AccessibilityServicePlan.DEVICE_WIDE_HOLD].orEmpty()

    return managedOverlayPackages.all { it in held }
}

/**
 * Whether Display over other apps is something IMD can actually manage right now.
 *
 * ⚠ **This replaces the stored `manageOverlay` switch**, which v3 removed from Advanced. The
 * author's instruction was to show the DOOA toggles to everyone and gate them on whether they
 * can work, rather than on a preference the user had to find first. Three things have to be
 * true, and each of them has a different thing wrong with it if it is not:
 *
 * * **'Manage Shizuku' is on and complete** — the AppOps behind overlay access can only be
 *   written through a running Shizuku, so with the master switch off there is nothing to write
 *   them with.
 * * **The fork is Thedjchi** — *"we are ditching shevery support from DOOA completely"*.
 *   Shevery has no start-stop intent, so IMD cannot bring the shell up on demand to write an
 *   AppOp and put it back.
 * * **'DOOAs to hide' is not empty** — with nothing selected the feature has nothing to do,
 *   and a toggle that can only ever be a no-op is worse than a toggle that says why.
 *
 * The three are deliberately not collapsed into one boolean anywhere that has to *explain* the
 * refusal — see [overlayBlockReasons], which is how a greyed row knows where to send somebody.
 */
val UserData.overlayManageable: Boolean
    get() = manageShizukuEffective &&
        shizukuForkMode == ShizukuForkMode.Thedjchi &&
        managedOverlayPackages.isNotEmpty()

/**
 * Whether hiding accessibility services is something IMD can actually do right now.
 *
 * The author's rule: *"if no DOOAs and no Accessibility services set to be hidden (do not
 * count IMD+ accessibility service) then disable the toggles and make them unclickable"*.
 *
 * ⚠ **IMD+'s own detector is not in this list and never was.** It is held under
 * `AccessibilityServicePlan.AUTO_HIDE_HOLD`, not in the user's selection, which is what makes
 * "do not count IMD+" true by construction rather than by a filter that could drift. The
 * author's other rule — that IMD+'s service is hidden and unhidden before a launch whatever
 * this says — is the same fact from the other side.
 */
val UserData.accessibilityManageable: Boolean
    get() = managedAccessibilityServices.isNotEmpty()

/**
 * Which of [overlayManageable]'s three terms is standing in the way, in the order a user
 * should be sent to fix them.
 *
 * Top level rather than nested, for the mundane reason `SettingsWorkKind` and `HideToggle`
 * are: `check16_when` cannot read an indented enum — it needs the closing brace at column 0.
 */
enum class OverlayBlockReason {
    /** Shevery. Not unconfigured but unsupported: there is nothing to go and set. */
    ForkUnsupported,

    /** 'Manage Shizuku' is off, or a field under it is blank. */
    ManageShizukuOff,

    /** Nothing is selected under 'DOOAs to hide'. */
    NothingSelected,
}

/**
 * Why a Display over other apps control will not move, or an empty list while it will.
 *
 * ⚠ **In `:domain:model` and returning reasons rather than sentences**, because two modules
 * ask this question — the settings screen's two configuration dialogs and the settings
 * manager — and neither can see the other's strings. Each maps the reasons to its own copy of
 * the author's wording.
 *
 * ⚠ **Shevery short-circuits to exactly one reason.** On that fork the feature is unsupported,
 * so the surfaces say so and offer no path; going on to report an empty picker as well would
 * be directions to a screen that can never help.
 */
fun overlayBlockReasons(userData: UserData): List<OverlayBlockReason> = when {
    userData.overlayManageable -> emptyList()

    userData.shizukuForkMode != ShizukuForkMode.Thedjchi ->
        listOf(OverlayBlockReason.ForkUnsupported)

    else -> buildList {
        if (!userData.manageShizukuEffective) add(OverlayBlockReason.ManageShizukuOff)

        if (userData.managedOverlayPackages.isEmpty()) add(OverlayBlockReason.NothingSelected)
    }
}

/**
 * Whether the **settings manager** may operate Display over other apps right now.
 *
 * ⚠ **Deliberately not [overlayManageable], and the difference is the whole of the author's
 * Shevery rule.** That property answers the *hiding* question and is Thedjchi-only, because a
 * launch has to be able to bring the shell up on demand and Shevery cannot be asked for
 * anything. This one answers the manager's question, where the user has just turned the service
 * on themselves and it is running — so the AppOp can be written after all.
 *
 * His two new points in the Shevery pop-up are this function in words: *"Managing Shevery
 * service & Display over other apps is only allowed in IMD settings manager"* and
 * *"Hiding-unhiding for app launches is not supported for both settings mentioned above"*.
 *
 * [shizukuRunning] is the live reading, not the configuration — on Shevery the row is locked to
 * whatever the user left it at until the service is actually seen.
 */
fun overlayManageableInManager(userData: UserData, shizukuRunning: Boolean): Boolean =
    userData.manageShizukuEffective &&
        userData.managedOverlayPackages.isNotEmpty() &&
        when (userData.shizukuForkMode) {
            ShizukuForkMode.Thedjchi -> true

            ShizukuForkMode.Other -> shizukuRunning

            ShizukuForkMode.Unset -> false
        }
