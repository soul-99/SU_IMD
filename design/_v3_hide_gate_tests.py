#!/usr/bin/env python3
"""
v3-r4m — host assertions for the hide gate, and the two blocks the removed filters left.

`templatesForOverlayState` and `appSettingsForOverlayState` are gone (see `_v3_hide_gate.py`),
so the two blocks that exercised them are rewritten around `appSettingBlocked` — which is the
question the per-app page asks now, and which reads `canHide`, so these assertions cover the
engine and the drawing at once.

New: `hideGateTests()`, which pins the three things the gate has to get right —

  * every target the greyed rows refuse reads false in `effectiveSettingsToHide`;
  * `effectiveRevertDefaults` is NOT gated the same way (the author's decision);
  * `manualTargetForKey` maps the three keys that mean more than "write this".

⚠ **`userData(...)` gains `managedAccessibility`, defaulting to a non-empty list.** Every
existing test built a UserData with no managed accessibility services, which under the new gate
would silently force AccessibilityServices off in every hide-map assertion in the file. The
default makes those tests keep meaning what they meant; the two that want an empty selection
pass one.

⚠ **One existing assertion gains `authKey = "k"`.** "the hide config keeps shizuku on thedjchi"
built an install with a blank auth key, which is not a configured Thedjchi — so under the gate
it now reads false, correctly. The assertion is about the fork, not about the master switch, so
the fixture is corrected rather than the expectation.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

# --- 1. the fixture gains a managed accessibility selection ----------------------------

OLD_PARAM = """    manageShizuku: Boolean = true,
) = UserData("""

NEW_PARAM = """    manageShizuku: Boolean = true,
    // ⚠ **Non-empty by default, since r4m.** `canHide` refuses AccessibilityServices with an
    // empty selection, so a blank fixture would force that target off in every hide-map
    // assertion in this file and quietly change what they test. The two that want an empty
    // selection say so.
    managedAccessibility: List<String> = listOf("com.example/.Service"),
) = UserData("""

# ⚠ Anchored to its neighbours. The bare line is a substring of the deeper-indented
# `managedAccessibilityServices = emptyList(),` in accessibilityPickerTests, and a substring
# count would have matched both.
OLD_FIELD = """    shizukuStartAction = startAction,
    managedAccessibilityServices = emptyList(),
    heldAccessibilityServices = heldAccessibility,"""

NEW_FIELD = """    shizukuStartAction = startAction,
    managedAccessibilityServices = managedAccessibility,
    heldAccessibilityServices = heldAccessibility,"""

# --- 2. the fork assertion that needs a configured Thedjchi ----------------------------

OLD_FORK = """    check(
        "the hide config keeps shizuku on thedjchi",
        userData(ShizukuForkMode.Thedjchi, hideStates = both)
            .effectiveSettingsToHide[ManualRevertTarget.Shizuku] == true,
    )"""

NEW_FORK = """    check(
        "the hide config keeps shizuku on thedjchi",
        // authKey, because since r4m the gate also asks whether Shizuku is configured at all -
        // a blank key is not a configured Thedjchi, and this assertion is about the fork.
        userData(ShizukuForkMode.Thedjchi, authKey = "k", hideStates = both)
            .effectiveSettingsToHide[ManualRevertTarget.Shizuku] == true,
    )"""

# --- 3. the overlay-marker visibility block, rewritten -------------------------------

OLD_VISIBILITY = '''/**
 * The per-app config screen's view of the overlay marker. The same rule as the device-wide
 * dialogs, one level down: while overlay management is off the "Hide Display over other apps"
 * template and any row already carrying its marker leave the screen, and both come back when
 * it is switched on - the filter is on the view, never on what is stored.
 */
private fun overlayMarkerVisibilityTests() {
    val overlayKey = AppSettingKeys.SYSTEM_ALERT_WINDOW

    val templates = listOf(
        appSettingTemplate(key = AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED),
        appSettingTemplate(key = AppSettingKeys.ACCESSIBILITY_ENABLED),
        appSettingTemplate(key = overlayKey),
    )

    val rows = listOf(
        appSetting(key = AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED),
        appSetting(key = overlayKey),
    )

    // 62. Off: the marker is gone from both the picker and the added rows, and nothing else is.
    checkEquals(
        "the overlay template is hidden while unmanaged",
        listOf(AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED, AppSettingKeys.ACCESSIBILITY_ENABLED),
        templates.templatesForOverlayState(manageOverlay = false).map { it.key },
    )
    checkEquals(
        "an added overlay row is hidden while unmanaged",
        listOf(AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED),
        rows.appSettingsForOverlayState(manageOverlay = false).map { it.key },
    )

    // 63. On: everything is shown, in the order it came - the filter adds and removes nothing
    // else and does not reorder.
    checkEquals(
        "every template is shown while managed",
        templates.map { it.key },
        templates.templatesForOverlayState(manageOverlay = true).map { it.key },
    )
    checkEquals(
        "every added row is shown while managed",
        rows.map { it.key },
        rows.appSettingsForOverlayState(manageOverlay = true).map { it.key },
    )
}'''

NEW_VISIBILITY = '''/**
 * The per-app config screen's view of the overlay marker.
 *
 * ⚠ **r4m turned this from removing to greying.** The two filters that used to drop the marker
 * out of the templates and the added rows are gone; the screen now draws every row and asks
 * [appSettingBlocked] whether each one can work. What is pinned here is that the question
 * answers for exactly the three keys that mean something beyond "write this", and that it
 * answers the same way the hide itself does.
 */
private fun overlayMarkerVisibilityTests() {
    val overlayKey = AppSettingKeys.SYSTEM_ALERT_WINDOW

    val unmanaged = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = false)

    val managed = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true)

    // 62. Off: the overlay marker is blocked, and an ordinary key beside it is not.
    check(
        "the overlay marker is blocked while unmanaged",
        appSettingBlocked(userData = unmanaged, key = overlayKey),
    )
    check(
        "an ordinary key is never blocked",
        !appSettingBlocked(
            userData = unmanaged,
            key = AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED,
        ),
    )

    // 63. On: nothing is blocked, and in particular the marker comes back - the block is on
    // the drawing, never on what is stored.
    check(
        "the overlay marker is clear while managed",
        !appSettingBlocked(userData = managed, key = overlayKey),
    )

    // 64. The accessibility flag follows its own picker, not the overlay switch. This is the
    // gap r4m closed: with nothing selected a per-app profile used to write the raw
    // accessibility_enabled flag, which switches off every service including IMD+'s detector.
    check(
        "the accessibility flag is blocked with an empty selection",
        appSettingBlocked(
            userData = managed.copy(managedAccessibilityServices = emptyList()),
            key = AppSettingKeys.ACCESSIBILITY_ENABLED,
        ),
    )
    check(
        "and clear once something is selected",
        !appSettingBlocked(userData = managed, key = AppSettingKeys.ACCESSIBILITY_ENABLED),
    )

    // 65. Only three keys mean anything beyond "write this".
    checkEquals(
        "the overlay marker names its target",
        ManualRevertTarget.DisplayOverOtherApps,
        manualTargetForKey(key = overlayKey),
    )
    checkEquals(
        "the shizuku marker names its target",
        ManualRevertTarget.Shizuku,
        manualTargetForKey(key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    checkEquals(
        "the accessibility flag names its target",
        ManualRevertTarget.AccessibilityServices,
        manualTargetForKey(key = AppSettingKeys.ACCESSIBILITY_ENABLED),
    )
    check(
        "an ordinary key names none",
        manualTargetForKey(key = "screen_brightness") == null,
    )
}'''

# --- 4. the shevery per-app block, rewritten -----------------------------------------

OLD_SHEVERY = '''    // 5. The per-app marker leaves the screen on shevery, exactly as the overlay one leaves it
    //    when the master switch is off - and the overlay row is untouched by the fork.
    val templates = listOf(
        appSettingTemplate(key = AppSettingKeys.SHIZUKU_SERVICE),
        appSettingTemplate(key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
        appSettingTemplate(key = "screen_brightness"),
    )
    checkEquals(
        "shevery hides only the shizuku template",
        listOf(AppSettingKeys.SYSTEM_ALERT_WINDOW, "screen_brightness"),
        templates.templatesForOverlayState(
            manageOverlay = true,
            shizukuForkMode = ShizukuForkMode.Other,
        ).map { it.key },
    )
    checkEquals(
        "thedjchi keeps every template",
        3,
        templates.templatesForOverlayState(
            manageOverlay = true,
            shizukuForkMode = ShizukuForkMode.Thedjchi,
        ).size,
    )

    val rows = listOf(
        appSetting(key = AppSettingKeys.SHIZUKU_SERVICE),
        appSetting(key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
    )
    checkEquals(
        "shevery hides the shizuku row it already added",
        listOf(AppSettingKeys.SYSTEM_ALERT_WINDOW),
        rows.appSettingsForOverlayState(
            manageOverlay = true,
            shizukuForkMode = ShizukuForkMode.Other,
        ).map { it.key },
    )
}'''

NEW_SHEVERY = '''    // 5. The per-app markers on shevery. Since r4m they are greyed on the screen rather than
    //    removed from it, so what is asserted is the block rather than the absence - and the
    //    author's answer to which rows grey: both of them, and the ordinary key never.
    val shevery = userData(ShizukuForkMode.Other, authKey = "k", manageOverlay = true)

    val thedjchi = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true)

    check(
        "shevery blocks the shizuku marker",
        appSettingBlocked(userData = shevery, key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    check(
        "shevery blocks the overlay marker too",
        appSettingBlocked(userData = shevery, key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
    )
    check(
        "and never an ordinary key",
        !appSettingBlocked(userData = shevery, key = "screen_brightness"),
    )
    check(
        "thedjchi blocks neither marker",
        !appSettingBlocked(userData = thedjchi, key = AppSettingKeys.SHIZUKU_SERVICE) &&
            !appSettingBlocked(userData = thedjchi, key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
    )

    // 6. And with 'Manage Shizuku' off, which is the author's own wording for this round -
    //    the marker is blocked on a fork that does speak intents.
    check(
        "manage shizuku off blocks the shizuku marker on thedjchi",
        appSettingBlocked(
            userData = thedjchi.copy(manageShizuku = false),
            key = AppSettingKeys.SHIZUKU_SERVICE,
        ),
    )
}'''

# --- 5. the new suite ------------------------------------------------------------------

HIDE_GATE_TESTS = '''
// ---------------------------------------------------------------------------------
// r4m - a disabled toggle does not run, for IMD+ and for every other launch route
// ---------------------------------------------------------------------------------

/**
 * The gate that made the greyed rows true of the engine as well as of the dialog.
 *
 * Every one of these was a real gap: with 'Manage Shizuku' off a device-wide hide still
 * stopped the Shizuku service, and with the accessibility picker empty it still drove
 * accessibility_enabled. Both paths are what IMD+ runs, which is why the author asked.
 *
 * ⚠ **The last group is the one that must not be "fixed".** Reverts are deliberately not
 * gated: restoring something IMD already switched off has to keep working after the toggle
 * that hid it has greyed, or a user is left with settings down and no screen to raise them
 * from. A build that gates both directions passes the first three groups and fails this one.
 */
private fun hideGateTests() {
    val all = ManualRevertTarget.entries.associateWith { true }

    val ready = userData(
        ShizukuForkMode.Thedjchi,
        authKey = "k",
        manageOverlay = true,
        hideStates = all,
        revertStates = all,
    )

    // 1. Everything configured: the stored ticks come through untouched.
    checkEquals(
        "a fully configured install hides every target it was told to",
        ManualRevertTarget.entries.size,
        ready.effectiveSettingsToHide.count { it.value },
    )

    // 2. Manage Shizuku off. The Shizuku row leaves the manager and greys elsewhere, and the
    //    hide has to agree - this is the gap the author's "for IMD+ also" names.
    val noShizuku = ready.copy(manageShizuku = false)

    check("manage shizuku off refuses the shizuku target", !noShizuku.canHide(ManualRevertTarget.Shizuku))
    checkEquals(
        "and the hide config reads it off however it was stored",
        false,
        noShizuku.effectiveSettingsToHide[ManualRevertTarget.Shizuku],
    )
    // Overlay access goes with it, because it is written through Shizuku and nothing else.
    checkEquals(
        "overlay access goes off with the master switch",
        false,
        noShizuku.effectiveSettingsToHide[ManualRevertTarget.DisplayOverOtherApps],
    )
    // And the three settings IMD writes directly are untouched by any of it.
    check(
        "the three direct settings are never gated",
        noShizuku.canHide(ManualRevertTarget.DeveloperSettings) &&
            noShizuku.canHide(ManualRevertTarget.UsbDebugging) &&
            noShizuku.canHide(ManualRevertTarget.WirelessDebugging),
    )

    // 3. An empty accessibility picker. The row greys in both dialogs; before r4m the hide
    //    went ahead and wrote the flag anyway.
    val noAccessibility = ready.copy(managedAccessibilityServices = emptyList())

    check(
        "an empty selection refuses the accessibility target",
        !noAccessibility.canHide(ManualRevertTarget.AccessibilityServices),
    )
    checkEquals(
        "and the hide config reads it off however it was stored",
        false,
        noAccessibility.effectiveSettingsToHide[ManualRevertTarget.AccessibilityServices],
    )

    // 4. ⚠ Reverts are not gated. Both of these would fail on a build that collapsed the two
    //    directions into one rule.
    checkEquals(
        "a revert still restores shizuku with the master switch off",
        true,
        noShizuku.effectiveRevertDefaults[ManualRevertTarget.Shizuku],
    )
    checkEquals(
        "a revert still restores accessibility services with an empty selection",
        true,
        noAccessibility.effectiveRevertDefaults[ManualRevertTarget.AccessibilityServices],
    )
}
'''

RUNNER_OLD = """    firstOwnerTests()

    println(\"passed: $passed\")"""

RUNNER_NEW = """    firstOwnerTests()
    hideGateTests()

    println(\"passed: $passed\")"""

IMPORTS = (
    "import com.android.geto.domain.model.appSettingBlocked",
    "import com.android.geto.domain.model.canHide",
    "import com.android.geto.domain.model.manualTargetForKey",
)

GONE = (
    "import com.android.geto.domain.model.appSettingsForOverlayState",
    "import com.android.geto.domain.model.templatesForOverlayState",
)


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")
    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    if not idx:
        raise AssertionError("no import block")

    if statement in lines:
        return text

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    path = ROOT / TESTS

    if not path.is_file():
        print(f"REFUSED: missing {TESTS}")
        return 1

    original = path.read_text(encoding="utf-8")
    text = original

    if "hideGateTests" in text:
        print("REFUSED: hideGateTests already present — has this run before?")
        return 1

    edits = [
        ("userData signature", OLD_PARAM, NEW_PARAM),
        ("managedAccessibilityServices field", OLD_FIELD, NEW_FIELD),
        ("the thedjchi fork assertion", OLD_FORK, NEW_FORK),
        ("overlayMarkerVisibilityTests", OLD_VISIBILITY, NEW_VISIBILITY),
        ("the shevery per-app block", OLD_SHEVERY, NEW_SHEVERY),
        ("the runner", RUNNER_OLD, RUNNER_NEW),
    ]

    for name, old, _ in edits:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {name} matched {found} time(s), expected exactly 1")
            return 1

    for name, old, new in edits:
        text = text.replace(old, new, 1)

    for gone in GONE:
        if text.count(gone) != 1:
            print(f"REFUSED: {gone!r} appears {text.count(gone)} time(s), expected 1")
            return 1

        text = text.replace(gone + "\n", "", 1)

    for statement in IMPORTS:
        text = insert_import(text, statement)

    # The new suite goes at the end of the file, after everything it may reference.
    text = text.rstrip("\n") + "\n" + HIDE_GATE_TESTS

    # --- assert POSITION, not merely presence (the r4e trap) -------------------------
    at_runner = text.index("private fun hideGateTests()")
    at_call = text.index("    hideGateTests()")

    if not at_call < at_runner:
        print("REFUSED: hideGateTests is called after it is declared in the same file")
        return 1

    # Nothing may still name the two removed filters.
    for removed in ("templatesForOverlayState", "appSettingsForOverlayState"):
        if removed in text:
            print(f"REFUSED: {removed} still referenced in the tests")
            return 1

    # ⚠ **Only lines this script introduces.** DomainLogicTests.kt is a tools file, not part
    # of the app's source set, and already carries three lines over 120 that predate this
    # round. Flagging those would refuse every edit to the file for ever; what matters is that
    # nothing new joins them.
    def long_lines(source: str) -> set[str]:
        return {
            line for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    introduced = long_lines(text) - long_lines(original)

    if introduced:
        print(f"REFUSED: {TESTS} would gain lines over 120 chars: {sorted(introduced)}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {TESTS}")
    print("  + hideGateTests, and the runner calls it")
    print("  ~ overlayMarkerVisibilityTests and the shevery block use appSettingBlocked")
    print("  ~ userData() gains managedAccessibility")
    print(f"\nwrote 1 file, {len(edits)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
