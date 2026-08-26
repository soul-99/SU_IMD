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
 * "Settings to hide" as the launch path should read it.
 *
 * With the feature off the overlay entry reads false rather than being dropped, because the
 * hide loop asks each target whether it is wanted and an absent entry already means no. The
 * explicit false says the same thing and keeps the map's shape stable.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = if (manageOverlay) {
        settingsToHide
    } else {
        settingsToHide + (ManualRevertTarget.DisplayOverOtherApps to false)
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
        manageOverlay -> revertDefaults

        heldOverlayPackages.isNotEmpty() ->
            revertDefaults + (ManualRevertTarget.DisplayOverOtherApps to true)

        else -> revertDefaults - ManualRevertTarget.DisplayOverOtherApps
    }

/**
 * True for the per-app overlay marker while overlay management is switched off.
 *
 * The per-app config screen has two ways the marker reaches it - the "Hide Display over other
 * apps" template a user can add, and the row they already added - and both carry the same
 * [AppSettingKeys.SYSTEM_ALERT_WINDOW]. Both have to leave the screen when the master switch is
 * off, because [ApplyAppSettingsUseCase] no longer acts on the marker then: a row that still
 * says it hides overlay access, shown next to rows that do work, is a false promise to anyone
 * relying on the memory function.
 *
 * Hidden from the view, never removed from storage. The Room row and the asset template are
 * untouched, so the setting comes back - in every app it was added to - the moment the feature
 * is switched on again.
 */
private fun overlayMarkerHiddenWhileUnmanaged(key: String, manageOverlay: Boolean): Boolean =
    !manageOverlay && key == AppSettingKeys.SYSTEM_ALERT_WINDOW

/** The templates the per-app config screen should offer, given the master switch. */
fun List<AppSettingTemplate>.templatesForOverlayState(
    manageOverlay: Boolean,
): List<AppSettingTemplate> =
    filterNot { overlayMarkerHiddenWhileUnmanaged(key = it.key, manageOverlay = manageOverlay) }

/** The rows the per-app config screen should show, given the master switch. */
fun List<AppSetting>.appSettingsForOverlayState(
    manageOverlay: Boolean,
): List<AppSetting> =
    filterNot { overlayMarkerHiddenWhileUnmanaged(key = it.key, manageOverlay = manageOverlay) }
