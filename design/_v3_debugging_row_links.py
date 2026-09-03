#!/usr/bin/env python3
"""r4h — USB debugging and Wireless debugging get the open-link the other four rows have.

The author:

    "also add external link icons in front of usb debugging and wireless debugging which leads
     to their respective settings, and if developer settings page"

The button already exists — `TargetRow` draws `GetoIcons.OpenInNew` whenever
`target.opensSomewhere`, and `openTarget` builds the intent. Four rows have it; these two were
simply not in either list. Placement is the author's pick: **trailing, like the others**, so the
six rows stay one shape.

### Where the links actually go

⚠ **Android publishes no intent for either screen.** USB debugging and Wireless debugging are
preferences *inside* Developer options; `Settings` has a constant for the page and none for
either row. So both links open Developer options with the platform's own
"scroll to and highlight this preference" extras — `:settings:fragment_args_key` and the same
key inside `:settings:show_fragment_args` — aimed at `enable_adb` and `toggle_adb_wireless`,
which are AOSP's keys for the two switches.

On AOSP and most OEM Settings apps that lands on the row with it flashed; where the extras are
ignored it lands on Developer options, which is the author's own *"and if developer settings
page"*. Either way it is one screen, and nothing about the fallback needs handling — an extra a
Settings app does not recognise is simply dropped.

⚠ **`ACTION_APPLICATION_DEVELOPMENT_SETTINGS`, the same action the Developer settings row uses**,
so all three share one failure path: the `ActivityNotFoundException` branch already answers with
`settings_manager_enable_developer_options` for that target, and it now answers for these two as
well — a device with developer options switched off cannot open any of the three, and the reason
is the same one.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (MANAGER, [
        (
            """private val ManualRevertTarget.opensSomewhere: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps ||
        this == ManualRevertTarget.Shizuku
""",
            """private val ManualRevertTarget.opensSomewhere: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.UsbDebugging ||
        this == ManualRevertTarget.WirelessDebugging ||
        this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps ||
        this == ManualRevertTarget.Shizuku
""",
            1,
        ),
    ]),

    (ROUTE, [
        (
            """    val intent = when (target) {
        ManualRevertTarget.DeveloperSettings -> {
            Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
        }
""",
            """    val intent = when (target) {
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
""",
            1,
        ),
        (
            """        val message = if (target == ManualRevertTarget.DeveloperSettings) {
""",
            """        // All three open the same page, so all three fail for the same reason: developer
        // options is switched off on this device.
        val message = if (target in DEVELOPER_OPTIONS_TARGETS) {
""",
            1,
        ),
        (
            """internal fun Context.openTarget(target: ManualRevertTarget, shizukuPackage: String?) {
""",
            """/** AOSP's preference keys for the two switches, which is what the highlight extras name. */
private const val USB_DEBUGGING_KEY = "enable_adb"

private const val WIRELESS_DEBUGGING_KEY = "toggle_adb_wireless"

/** The three rows that open Developer options, and so share one reason for failing to. */
private val DEVELOPER_OPTIONS_TARGETS = setOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * Developer options, scrolled to one of its preferences and with that preference flashed.
 *
 * ⚠ **Both extras, and both are needed.** The Settings app reads `:settings:fragment_args_key`
 * to decide what to highlight and `:settings:show_fragment_args` to pass the same key down to
 * the fragment it opens; supplying only one gets the page without the highlight on most builds.
 * Neither is public API - they are the keys Settings has used since Android 7 and the ones every
 * "open this exact toggle" link on the platform uses - so this is best-effort by construction.
 * An unrecognised extra is dropped, which leaves the page, and the page was the fallback anyway.
 */
private fun developerOptionsAt(key: String): Intent =
    Intent(Settings.ACTION_APPLICATION_DEVELOPMENT_SETTINGS)
        .putExtra(":settings:fragment_args_key", key)
        .putExtra(
            ":settings:show_fragment_args",
            Bundle().apply { putString(":settings:fragment_args_key", key) },
        )

internal fun Context.openTarget(target: ManualRevertTarget, shizukuPackage: String?) {
""",
            1,
        ),
        (
            """import android.provider.Settings
""",
            """import android.os.Bundle
import android.provider.Settings
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    manager = staged.get(ROOT / MANAGER, "")
    route = staged.get(ROOT / ROUTE, "")

    # ⚠ Asserted against code, never the prose around it.
    for rel, text, token, expected in (
        # ⚠ Nine, not six: `usesDebuggingTransport` above it names three of its own, and an
        # earlier draft of this assertion counted them and refused. The property itself is
        # pinned by the block test below rather than by a count of a phrase two properties share.
        (MANAGER, manager, "this == ManualRevertTarget.", 9),
        (ROUTE, route, "developerOptionsAt(key = ", 2),
        (ROUTE, route, "private fun developerOptionsAt(key: String): Intent", 1),
        (ROUTE, route, "target in DEVELOPER_OPTIONS_TARGETS", 1),
        (ROUTE, route, "import android.os.Bundle", 1),
        # The old single-target test must be gone, or the two new rows get the wrong toast.
        (ROUTE, route, "target == ManualRevertTarget.DeveloperSettings", 0),
        # Both extras on the one intent builder.
        (ROUTE, route, '":settings:fragment_args_key"', 2),
        (ROUTE, route, '":settings:show_fragment_args"', 1),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    opens = """private val ManualRevertTarget.opensSomewhere: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.UsbDebugging ||
        this == ManualRevertTarget.WirelessDebugging ||
        this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps ||
        this == ManualRevertTarget.Shizuku
"""

    if manager.count(opens) != 1:
        problems.append(f"{MANAGER}: opensSomewhere does not name all six targets")

    # ⚠ **Position, not presence.** The two new branches must sit inside `openTarget`'s `when`,
    # above the `else`, or they are dead code that compiles.
    when_start = route.find("    val intent = when (target) {")
    usb = route.find("        ManualRevertTarget.UsbDebugging -> developerOptionsAt")
    otherwise = route.find("        else -> null")

    if when_start < 0 or usb < 0 or otherwise < 0:
        problems.append(f"{ROUTE}: cannot locate the when, the new branch, or its else")
    elif not when_start < usb < otherwise:
        problems.append(f"{ROUTE}: the new branches are not inside openTarget's when")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - all six rows open somewhere, and the two new ones deep-link into Developer options")

    return 0


if __name__ == "__main__":
    sys.exit(main())
