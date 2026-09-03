#!/usr/bin/env python3
"""r4i — with wireless debugging on, its link opens the Wireless debugging page itself.

The author:

    "for wireless debugging toggle, if wireless debugging is enabled its external link icon
     jump directly to the wireless debugging setting page"

r4h pointed both debugging links at Developer options with the platform's highlight extras,
because Android publishes no intent for either sub-screen. Wireless debugging, though, is a real
screen of its own — pairing code, port, paired devices — and the Settings app exposes an activity
for it, just not a documented action.

### How it is reached, and why it cannot simply be called

`com.android.settings/.Settings$AdbWirelessSettingsActivity` is an internal name. It is right on
AOSP and on most OEM builds and it is not a promise: a vendor can rename it, remove it, or
refuse the caller. So `openTarget` now takes a **list** of candidate intents and tries them in
order, and the wireless row supplies two — the page, then r4h's highlighted Developer options.

⚠ **Tried rather than resolved.** `resolveActivity` on an explicit component in another package
is subject to package visibility, so a correct component can come back null on API 30+ and the
good branch would be skipped for a reason that has nothing to do with the device. Starting it and
catching `ActivityNotFoundException` (and `SecurityException`, for a vendor that guards the
activity) asks the only question that matters and gets the true answer.

⚠ **The fallback is silent.** The user asked to see a settings screen; landing one level out is
not an error worth a toast, and the toast is kept for the case where *nothing* opened.

⚠ **Only when the setting is on**, which is the author's condition and also the sensible one: with
wireless debugging off that page has nothing on it but a switch the user has just come from.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")

# The route hands the live state through, so the wireless branch can ask whether it is on.
CALL_OLD = """        onOpen = { target ->
            context.openTarget(target = target, shizukuPackage = shizukuLaunchPackage)
        },
"""

CALL_NEW = """        onOpen = { target ->
            context.openTarget(
                target = target,
                shizukuPackage = shizukuLaunchPackage,
                // Only meaningful for the wireless row, and read here rather than inside
                // `openTarget` so that function stays a pure intent-builder with no opinion
                // about where the device's state comes from.
                wirelessDebuggingOn = targetStates.isEnabled(
                    ManualRevertTarget.WirelessDebugging,
                ),
            )
        },
"""

SIGNATURE_OLD = """internal fun Context.openTarget(target: ManualRevertTarget, shizukuPackage: String?) {
    val intent = when (target) {
        ManualRevertTarget.DeveloperSettings -> {
            Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
        }

        // ⚠ **Android publishes no intent for either of these screens.** They are preferences
        // inside Developer options, and `Settings` has a constant for the page and none for
        // the rows. Both therefore open that page with the platform's own scroll-to-and-
        // highlight extras aimed at the preference; where a Settings app ignores them the
        // user lands on Developer options, which is the author's own fallback.
        ManualRevertTarget.UsbDebugging -> developerOptionsAt(key = USB_DEBUGGING_KEY)

        ManualRevertTarget.WirelessDebugging -> developerOptionsAt(key = WIRELESS_DEBUGGING_KEY)

        ManualRevertTarget.AccessibilityServices -> {
            Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)
        }

        ManualRevertTarget.DisplayOverOtherApps -> {
            Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
        }

        ManualRevertTarget.Shizuku -> {
            shizukuPackage?.let(packageManager::getLaunchIntentForPackage)
        }

        else -> null
    }

    if (intent == null) {
"""

SIGNATURE_NEW = """internal fun Context.openTarget(
    target: ManualRevertTarget,
    shizukuPackage: String?,
    wirelessDebuggingOn: Boolean = false,
) {
    // ⚠ **A list, because one row has a second-best answer.** Every other target has exactly
    // one place to go; wireless debugging has a real screen of its own whose activity name is
    // internal, so it offers that first and r4h's highlighted Developer options behind it.
    val candidates = when (target) {
        ManualRevertTarget.DeveloperSettings -> {
            listOf(Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS))
        }

        // ⚠ **Android publishes no intent for either of these screens.** They are preferences
        // inside Developer options, and `Settings` has a constant for the page and none for
        // the rows. Both therefore open that page with the platform's own scroll-to-and-
        // highlight extras aimed at the preference; where a Settings app ignores them the
        // user lands on Developer options, which is the author's own fallback.
        ManualRevertTarget.UsbDebugging -> listOf(developerOptionsAt(key = USB_DEBUGGING_KEY))

        // ⚠ **The page first, but only while the setting is on** - the author's condition, and
        // the sensible one: switched off, that screen holds nothing but the switch the user
        // has just come from. The component name is internal and may be renamed, removed or
        // guarded by a vendor, so the highlighted page stands behind it.
        ManualRevertTarget.WirelessDebugging -> listOfNotNull(
            wirelessDebuggingPage().takeIf { wirelessDebuggingOn },
            developerOptionsAt(key = WIRELESS_DEBUGGING_KEY),
        )

        ManualRevertTarget.AccessibilityServices -> {
            listOf(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }

        ManualRevertTarget.DisplayOverOtherApps -> {
            listOf(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION))
        }

        ManualRevertTarget.Shizuku -> {
            listOfNotNull(shizukuPackage?.let(packageManager::getLaunchIntentForPackage))
        }

        else -> emptyList()
    }

    if (candidates.isEmpty()) {
"""

BODY_OLD = """    runCatching {
        startActivity(intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
    }.onFailure {
        if (it !is ActivityNotFoundException && it !is SecurityException) throw it

        // All three open the same page, so all three fail for the same reason: developer
        // options is switched off on this device.
        val message = if (target in DEVELOPER_OPTIONS_TARGETS) {
            R.string.settings_manager_enable_developer_options
        } else {
            R.string.settings_manager_cannot_open
        }

        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
}
"""

BODY_NEW = """    // ⚠ **Tried rather than resolved.** `resolveActivity` on an explicit component in another
    // package is subject to package visibility, so a perfectly good component can come back
    // null on API 30+ for a reason that has nothing to do with the device. Starting it and
    // catching the refusal asks the only question that matters.
    //
    // The fallback is silent: the user asked to see a settings screen, and landing one level
    // out is not worth a toast. The toast below is for nothing having opened at all.
    for (candidate in candidates) {
        val opened = runCatching {
            startActivity(candidate.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK))
        }.fold(
            onSuccess = { true },
            onFailure = {
                if (it !is ActivityNotFoundException && it !is SecurityException) throw it

                false
            },
        )

        if (opened) return
    }

    // All three debugging rows open the same page, so all three fail for the same reason:
    // developer options is switched off on this device.
    val message = if (target in DEVELOPER_OPTIONS_TARGETS) {
        R.string.settings_manager_enable_developer_options
    } else {
        R.string.settings_manager_cannot_open
    }

    Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
}
"""

HELPER_OLD = """private fun developerOptionsAt(key: String): Intent =
"""

HELPER_NEW = """/**
 * The Settings app's own Wireless debugging screen — pairing code, port, paired devices.
 *
 * ⚠ **An internal component name, and that is the whole risk.** Android has an action for
 * Developer options and none for this page, so the only way in is the activity Settings
 * declares for it. Right on AOSP and on most OEM builds; not a promise. Whether it works is
 * asked by starting it, not by resolving it - see the loop in [openTarget].
 */
private fun wirelessDebuggingPage(): Intent = Intent().setClassName(
    "com.android.settings",
    "com.android.settings.Settings\\$AdbWirelessSettingsActivity",
)

private fun developerOptionsAt(key: String): Intent =
"""

TOAST_OLD = """    if (candidates.isEmpty()) {
        Toast.makeText(this, R.string.settings_manager_no_shizuku, Toast.LENGTH_SHORT).show()

        return
    }
"""


def main() -> int:
    path = ROOT / ROUTE

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {ROUTE}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in (
        (CALL_OLD, CALL_NEW, 1),
        (SIGNATURE_OLD, SIGNATURE_NEW, 1),
        (BODY_OLD, BODY_NEW, 1),
        (HELPER_OLD, HELPER_NEW, 1),
    ):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        ("wirelessDebuggingOn: Boolean = false,", 1),
        ("wirelessDebuggingPage().takeIf { wirelessDebuggingOn }", 1),
        ("private fun wirelessDebuggingPage(): Intent", 1),
        ("for (candidate in candidates) {", 1),
        ("if (opened) return", 1),
        # The old single-intent shape must be gone in full, or the loop reads a stale variable.
        ("val intent = when (target)", 0),
        ("if (intent == null)", 0),
        # The empty-list guard survived the rename.
        (TOAST_OLD, 1),
        # The escaped dollar is what makes the inner-class name a component and not a template.
        ('"com.android.settings.Settings\\$AdbWirelessSettingsActivity"', 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token.splitlines()[0][:58]!r}, "
                            f"found {text.count(token)}")

    # ⚠ **Position, not presence.** The loop must come after the candidate list is built and
    # after the empty guard, or it iterates something that does not exist yet.
    build = text.find("    val candidates = when (target) {")
    guard = text.find("    if (candidates.isEmpty()) {")
    loop = text.find("    for (candidate in candidates) {")

    if min(build, guard, loop) < 0:
        problems.append("cannot locate the candidate list, the empty guard or the loop")
    elif not build < guard < loop:
        problems.append("the loop does not follow the candidate list and its guard")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  wrote {ROUTE}")
    print("ok - the wireless link tries its own page first and falls through silently")

    return 0


if __name__ == "__main__":
    sys.exit(main())
