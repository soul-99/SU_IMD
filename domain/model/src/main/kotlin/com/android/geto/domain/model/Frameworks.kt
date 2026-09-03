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
 * The pure questions the two frameworks answer between them.
 *
 * How the pre-v3 "hiding-unhiding mechanism" pairs off into the two frameworks.
 *
 * In `:domain:model` rather than beside `MigrateFrameworksUseCase`, and deliberately: the host
 * runner compiles this module and nothing else, and this is the one piece of v3 whose mistakes
 * are invisible until somebody's device is already on the wrong framework. The same reason
 * `autoHideFailureBackoffMillis` and [AutoHideRequirements] live here.
 *
 * The old preference answered two questions with one switch and only ever offered the two
 * combinations where both answers agreed, so the mapping is a straight pair-off — and an
 * upgrading install therefore never lands in one of v3's two new combinations. Those have to
 * be chosen deliberately.
 */
fun hidingFrameworkFor(notificationFunction: NotificationFunction): HidingFramework =
    when (notificationFunction) {
        NotificationFunction.Memory -> HidingFramework.PerApp

        NotificationFunction.RevertToDefault -> HidingFramework.ImdDefaults
    }

/** The unhiding half of [hidingFrameworkFor]'s pairing. */
fun unhidingFrameworkFor(notificationFunction: NotificationFunction): UnhidingFramework =
    when (notificationFunction) {
        NotificationFunction.Memory -> UnhidingFramework.Memory

        NotificationFunction.RevertToDefault -> UnhidingFramework.RevertToDefault
    }

/**
 * Whether this pair can leave a setting hidden that nothing will put back.
 *
 * True only for [HidingFramework.PerApp] with [UnhidingFramework.RevertToDefault]: a per-app
 * profile can hide any setting by key, while *Revert to default configuration* drives only the
 * six [ManualRevertTarget]s. Anything the profile hid outside those would be left switched off
 * with nothing that clears it.
 *
 * It is not a reason to forbid the combination — the author chose to allow all four — it is
 * the flag that says a Revert to default also has to put back the extras, which is what
 * [settingsOutsideRevertDefaults] picks out.
 */
fun strandsSettings(
    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
): Boolean = hidingFramework == HidingFramework.PerApp &&
    unhidingFramework == UnhidingFramework.RevertToDefault

/**
 * The recorded settings a Revert to default will **not** drive, and so has to restore itself.
 *
 * A Revert to default drives all six [ManualRevertTarget]s to their configured state — in both
 * directions, so a target configured *off* is being driven just as much as one configured on.
 * Only three of them name a global setting key; anything else a per-app profile recorded is
 * outside the revert's reach entirely.
 *
 * ⚠ **This is why the revert does not simply flush every pending revert first.** Flushing and
 * then driving the defaults reaches the same end state, but writes the overlapping settings
 * twice — and `adb_enabled` is one of them, so a Shizuku user would watch the service start on
 * the restore and stop again on the defaults, twice over the fork's start wait. Restoring only
 * what the defaults cannot reach writes each setting once. The author's design.
 */
fun settingsOutsideRevertDefaults(
    recorded: Map<String, String?>,
): Map<String, String?> {
    val driven = ManualRevertTarget.entries.mapNotNull { it.globalSettingKey }.toSet()

    return recorded.filterKeys { key -> key !in driven }
}

fun revertNamesApp(
    hidingFramework: HidingFramework,
    unhidingFramework: UnhidingFramework,
): Boolean = hidingFramework == HidingFramework.PerApp &&
    unhidingFramework == UnhidingFramework.Memory

/**
 * **The first-owner rule.** Whether this hide is the one that owes putting [key] back.
 *
 * True only when the setting is not already at the value this hide is about to write — which
 * is to say, only when this hide is the one actually changing it.
 *
 * ### Why it exists
 *
 * A per-app record is measured at the moment of that app's hide and stored under that app's
 * component name, so a **second** app launched into an already-hidden window used to measure the
 * *hidden* values and record them as its "before". Reverting the first app then put a setting
 * back while the second was still open, and reverting the second wrote the hidden value over it
 * — leaving it stranded off with no record left that knew better.
 *
 * With this, the first hide to touch a setting is the only one that records it, and it is
 * therefore the only one that puts it back. Later hides that find it already down record
 * nothing for it and take nothing away when they revert.
 *
 * ### It also fixes a case that predates the cascade
 *
 * If the **user** had a setting off before any of this began, the first hide to want it hidden
 * also records nothing — so no revert ever switches it on. IMD only puts back what IMD took,
 * which is the same instinct as `RevertToDefaultUseCase`'s "a null recording is skipped, not
 * written".
 *
 * ⚠ **Not the same question as "is it already recorded".** Both recorders already skip a key
 * they hold a reading for, so that a repeat launch cannot overwrite the original with the value
 * the previous launch wrote. This asks whether the hide changes anything at all.
 *
 * [currentValue] is null when the setting has never been set; that is not equal to any value a
 * hide writes, so it is recorded — and the revert's own rule skips writing a null back.
 */
fun hideOwnsRevert(currentValue: String?, valueOnLaunch: String): Boolean =
    currentValue != valueOnLaunch

/**
 * The device-wide memory record's id for one manual target.
 *
 * The same [SettingSnapshot] encoding the per-app records use, on the Global table, which is
 * where `SetManualTargetUseCase` reads and writes all three keyed targets. Sharing the
 * encoding is what lets the device-wide record live in the same `settingStateBefore` map under
 * [AccessibilityServicePlan.DEVICE_WIDE_HOLD] instead of needing a proto field of its own.
 */
fun deviceWideSnapshotId(target: ManualRevertTarget): String? =
    target.globalSettingKey?.let { key ->
        SettingSnapshot.idOf(settingType = SettingType.GLOBAL, key = key)
    }

/**
 * The state a device-wide **memory** revert should drive each target to.
 *
 * Built from what the hide measured rather than from the configured defaults, which is the
 * whole difference between the two unhiding frameworks for a device-wide hide: the three keyed
 * targets go back to what was actually there, and a setting the user never had on before the
 * hide stays off afterwards.
 *
 * The other three targets — accessibility services, Shizuku and Display over other apps —
 * are **absent from the result on purpose**. Their device-wide holds already record exactly
 * what IMD took and give back exactly that, so they are memory-shaped already; adding them
 * here would have the revert drive them from a snapshot as well as from their hold, and the
 * two would disagree the moment anything else touched them.
 *
 * A target the record has nothing for is left out too — the revert then leaves it alone, which
 * is the right answer for a setting this hide never switched off.
 */
fun deviceWideMemoryWanted(
    recorded: Map<String, String?>,
): Map<ManualRevertTarget, Boolean> {
    val wanted = mutableMapOf<ManualRevertTarget, Boolean>()

    for (target in ManualRevertTarget.entries) {
        val id = deviceWideSnapshotId(target = target) ?: continue

        if (id !in recorded) continue

        // Anything that is not exactly "1" was off or unset before the hide, and both mean
        // the same thing to a revert: do not switch it on.
        wanted[target] = recorded[id] == "1"
    }

    return wanted
}

/**
 * The device-wide record a manual settings-manager change should leave behind, or null.
 *
 * Null means "write nothing", and it covers three separate cases that all come to the same
 * thing:
 *
 *  * **No revert is pending.** The author's rule: with nothing outstanding, a person moving a
 *    switch is managing their own device and no later revert should undo it.
 *  * **The target has no keyed setting.** Accessibility services, Shizuku and Display over
 *    other apps are not stored here at all — the first two record holds of their own and the
 *    third has no "before" value, since switching it off is a broadcast.
 *  * **The key is already recorded.** The first-owner rule, in the shape
 *    `recordDeviceWideValues` uses it: the earliest reading is the true one, and every later
 *    one is a value IMD itself wrote.
 *
 * [currentlyEnabled] is the state the row has **now**, before the press lands.
 */
fun manualChangeRecord(
    settingStateBefore: Map<String, Map<String, String?>>,
    target: ManualRevertTarget,
    currentlyEnabled: Boolean,
    revertPending: Boolean,
): Map<String, String?>? {
    if (!revertPending) return null

    val id = deviceWideSnapshotId(target = target) ?: return null

    val existing = settingStateBefore[AccessibilityServicePlan.DEVICE_WIDE_HOLD].orEmpty()

    if (id in existing) return null

    return SettingSnapshot.merge(
        existing = existing,
        measured = mapOf(id to if (currentlyEnabled) "1" else "0"),
    )
}

/**
 * The device-wide record left after a memory revert has driven what it could.
 *
 * ⚠ **Nothing cleared this record before v3, and that was a real defect**: a device-wide
 * memory revert restored the state measured at the *first* hide, for ever, because
 * `recordDeviceWideValues` skips any key it already holds and nothing ever removed one. Two
 * hides and one manual change were enough to see it.
 *
 * [driven] is what the revert was asked to drive — read from the override rather than from
 * [ManualRevertTarget.entries], so a target the record said nothing about is not invented.
 * [failed] is left recorded on purpose: a record still there after a failure is what lets a
 * retry put the right value back, which is `RevertAppSettingsUseCase`'s rule for the per-app
 * records and the same rule here.
 *
 * Returns the whole `settingStateBefore` map, with the device-wide holder dropped entirely
 * once nothing is left under it rather than left as an empty map that still reads as a key.
 */
fun deviceWideRecordAfterRevert(
    settingStateBefore: Map<String, Map<String, String?>>,
    driven: Set<ManualRevertTarget>,
    failed: Set<ManualRevertTarget>,
): Map<String, Map<String, String?>> {
    val existing = settingStateBefore[AccessibilityServicePlan.DEVICE_WIDE_HOLD]
        ?: return settingStateBefore

    val settled = driven
        .filterNot { it in failed }
        .mapNotNull { deviceWideSnapshotId(target = it) }
        .toSet()

    if (settled.isEmpty()) return settingStateBefore

    val remaining = existing.filterKeys { it !in settled }

    return if (remaining.isEmpty()) {
        settingStateBefore - AccessibilityServicePlan.DEVICE_WIDE_HOLD
    } else {
        settingStateBefore + (AccessibilityServicePlan.DEVICE_WIDE_HOLD to remaining)
    }
}
