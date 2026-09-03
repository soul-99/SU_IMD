#!/usr/bin/env python3
"""
v3-r4m — one answer to "can IMD act on this target", read by the drawing and by the engine.

    "please make sure disabled toggles dont run for IMD+ also"

Before this, only Display over other apps was gated in `effectiveSettingsToHide`. So with
'Manage Shizuku' off a device-wide hide - tile, in-app launch, shortcut and **IMD+**, which
runs this same map - still stopped the Shizuku service; and with 'Accessibility services to
hide' empty it still drove `accessibility_enabled`. In both cases the dialog greyed the row
and the use case went ahead anyway.

`UserData.canHide(target)` is now that single expression. `effectiveSettingsToHide` forces
every target it refuses to false, generalising the one line that already did it for overlay.

⚠ **Hiding only.** `effectiveRevertDefaults` is deliberately NOT gated the same way - the
author's decision, and the asymmetry this file opens with: switching a feature off has to stop
IMD taking a setting down, but it must never abandon one IMD has already taken.

⚠ **The two per-app filters are removed, not weakened.** `templatesForOverlayState` and
`appSettingsForOverlayState` *hid* the gated rows from the per-app page; the author wants them
shown and greyed. `appSettingBlocked` is the question the page asks instead, and it asks
`canHide` - so a greyed template and a skipped hide can never disagree.

Four top-level declarations leave this file. `check_lost_declarations` reports them and each
is deliberate; they are listed in the round doc.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OVERLAY = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"

# --- the rule, inserted immediately above effectiveSettingsToHide's KDoc ----------------

CAN_HIDE = '''/**
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

'''

DOC_OPEN = '''/**
 * "Settings to hide" as the launch path should read it.
'''

OLD_EFFECTIVE = '''/**
 * "Settings to hide" as the launch path should read it.
 *
 * With the feature off the overlay entry reads false rather than being dropped, because the
 * hide loop asks each target whether it is wanted and an absent entry already means no. The
 * explicit false says the same thing and keeps the map's shape stable.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = (
        if (overlayManageable) {
            settingsToHideOrLegacy
        } else {
            settingsToHideOrLegacy + (ManualRevertTarget.DisplayOverOtherApps to false)
        }
        ).withoutShizukuWhenNoIntents(mode = shizukuForkMode)
'''

NEW_EFFECTIVE = '''/**
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
 * ⚠ **Hiding only.** [effectiveRevertDefaults] is deliberately not gated the same way.
 */
val UserData.effectiveSettingsToHide: Map<ManualRevertTarget, Boolean>
    get() = ManualRevertTarget.entries
        .fold(settingsToHideOrLegacy) { map, target ->
            if (canHide(target)) map else map + (target to false)
        }
        .withoutShizukuWhenNoIntents(mode = shizukuForkMode)
'''

# --- the two per-app filters, replaced by the question the page asks --------------------

OLD_FILTERS = '''/**
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

/**
 * True for the per-app Shizuku marker on a fork family with no stop intent.
 *
 * The same reasoning as [overlayMarkerHiddenWhileUnmanaged], for the same two entry points: a
 * "Hide Shizuku service" row on a Shevery install would promise something the apply path cannot
 * do, since stopping Shevery is a side effect of hiding debugging rather than anything IMD
 * sends. Hidden from the view, never removed from storage, so it returns intact if the user
 * switches to a fork that does speak intents.
 */
private fun shizukuMarkerHiddenWithoutIntents(key: String, mode: ShizukuForkMode): Boolean =
    !mode.supportsIntents && key == AppSettingKeys.SHIZUKU_SERVICE

/** The templates the per-app config screen should offer, given the master switch and the fork. */
fun List<AppSettingTemplate>.templatesForOverlayState(
    manageOverlay: Boolean,
    shizukuForkMode: ShizukuForkMode = ShizukuForkMode.Thedjchi,
): List<AppSettingTemplate> = filterNot {
    overlayMarkerHiddenWhileUnmanaged(key = it.key, manageOverlay = manageOverlay) ||
        shizukuMarkerHiddenWithoutIntents(key = it.key, mode = shizukuForkMode)
}

/** The rows the per-app config screen should show, given the master switch and the fork. */
fun List<AppSetting>.appSettingsForOverlayState(
    manageOverlay: Boolean,
    shizukuForkMode: ShizukuForkMode = ShizukuForkMode.Thedjchi,
): List<AppSetting> = filterNot {
    overlayMarkerHiddenWhileUnmanaged(key = it.key, manageOverlay = manageOverlay) ||
        shizukuMarkerHiddenWithoutIntents(key = it.key, mode = shizukuForkMode)
}
'''

NEW_FILTERS = '''/**
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
'''


def main() -> int:
    path = ROOT / OVERLAY

    if not path.is_file():
        print(f"REFUSED: missing {OVERLAY}")
        return 1

    text = path.read_text(encoding="utf-8")

    for name in ("canHide", "appSettingBlocked", "manualTargetForKey"):
        if name in text:
            print(f"REFUSED: {name} already present — has this run before?")
            return 1

    for name, anchor in (
        ("effectiveSettingsToHide doc", DOC_OPEN),
        ("effectiveSettingsToHide", OLD_EFFECTIVE),
        ("the two per-app filters", OLD_FILTERS),
    ):
        found = text.count(anchor)

        if found != 1:
            print(f"REFUSED: {name} matched {found} time(s), expected exactly 1")
            return 1

    text = text.replace(OLD_EFFECTIVE, CAN_HIDE + NEW_EFFECTIVE, 1)
    text = text.replace(OLD_FILTERS, NEW_FILTERS, 1)

    # --- assert POSITION, not merely presence (the r4e trap) -------------------------
    at_can_hide = text.index("fun UserData.canHide(target: ManualRevertTarget)")
    at_effective = text.index("val UserData.effectiveSettingsToHide")
    at_revert = text.index("val UserData.effectiveRevertDefaults")
    at_blocked = text.index("fun appSettingBlocked(")

    if not at_can_hide < at_effective < at_revert < at_blocked:
        print(
            "REFUSED: placement wrong — "
            f"canHide@{at_can_hide} hide@{at_effective} "
            f"revert@{at_revert} blocked@{at_blocked}"
        )
        return 1

    # The revert map must NOT have gained the gate. Bounded to its own body — the next KDoc
    # after it — because a span running to the next declaration would swallow that
    # declaration's comment, and appSettingBlocked's comment names canHide on purpose.
    revert_body = text[at_revert:text.index("\n/**", at_revert)]

    if "canHide" in revert_body:
        print("REFUSED: effectiveRevertDefaults would read canHide — reverts are not gated")
        return 1

    # Every enum constant named exactly once in canHide's when.
    when_block = text[at_can_hide:at_effective]

    for constant in (
        "DeveloperSettings",
        "UsbDebugging",
        "WirelessDebugging",
        "AccessibilityServices",
        "DisplayOverOtherApps",
        "Shizuku",
    ):
        if when_block.count(f"ManualRevertTarget.{constant}") != 1:
            print(f"REFUSED: canHide names {constant} "
                  f"{when_block.count(f'ManualRevertTarget.{constant}')} time(s)")
            return 1

    # The four declarations that leave, and nothing else.
    for gone in (
        "overlayMarkerHiddenWhileUnmanaged",
        "shizukuMarkerHiddenWithoutIntents",
        "templatesForOverlayState",
        "appSettingsForOverlayState",
    ):
        if gone in text:
            print(f"REFUSED: {gone} survives the replacement")
            return 1

    # The declarations that must survive it.
    for kept in (
        "fun Map<ManualRevertTarget, Boolean>.withoutOverlayWhenUnmanaged(",
        "fun Map<ManualRevertTarget, Boolean>.withoutShizukuWhenNoIntents(",
        "val UserData.overlayManageable: Boolean",
        "val UserData.accessibilityManageable: Boolean",
        "fun overlayBlockReasons(userData: UserData)",
        "fun overlayManageableInManager(",
        "fun overlayAlreadyWithdrawn(",
        "private val UserData.settingsToHideOrLegacy",
    ):
        if text.count(kept) != 1:
            print(f"REFUSED: {kept!r} appears {text.count(kept)} time(s), expected 1")
            return 1

    over = [
        (n, len(line))
        for n, line in enumerate(text.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ")
    ]

    if over:
        print(f"REFUSED: {OVERLAY} would carry lines over 120 chars: {over}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {OVERLAY}")
    print("  + canHide, manualTargetForKey, appSettingBlocked")
    print("  ~ effectiveSettingsToHide gates every target, not just overlay")
    print("  - overlayMarkerHiddenWhileUnmanaged, shizukuMarkerHiddenWithoutIntents,")
    print("    templatesForOverlayState, appSettingsForOverlayState")
    print("\nwrote 1 file, 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
