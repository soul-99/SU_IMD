#!/usr/bin/env python3
"""
v3 — host assertions for `manualChangeRecord`, the debt rule's pure half.

Ten checks, placed beside the `deviceWideMemoryWanted` block they share a record with. They
cover every branch the function has plus the two the author's rule turns on:

  * nothing pending          -> no record, whichever way the switch moves
  * a revert pending         -> the value the row had *before* the press
  * first owner              -> a second press does not overwrite the first reading
  * an unrelated key present -> merged rather than replaced
  * the three hold-backed targets -> never recorded here

⚠ **The first-owner check is the one that matters most.** Without it a user who presses the
same switch twice while a revert is pending records the value IMD itself wrote a moment ago,
and the revert then restores the wrong state — the exact failure `recordDeviceWideValues`
already guards against on the hide side.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"

IMPORT_ANCHOR = """import com.android.geto.domain.model.deviceWideSnapshotId
"""

IMPORT_NEW = """import com.android.geto.domain.model.deviceWideSnapshotId
import com.android.geto.domain.model.manualChangeRecord
"""

ANCHOR = """    check(
        "an empty record drives nothing",
        deviceWideMemoryWanted(emptyMap()).isEmpty(),
    )
"""

TESTS = """    check(
        "an empty record drives nothing",
        deviceWideMemoryWanted(emptyMap()).isEmpty(),
    )

    // The debt rule: moving a settings manager switch by hand joins the outstanding revert
    // only when there is one. With nothing pending the user is managing their own device and
    // no later revert should undo it.
    val deviceWideHold = AccessibilityServicePlan.DEVICE_WIDE_HOLD

    val usbId = devId(ManualRevertTarget.UsbDebugging)

    val wifiId = devId(ManualRevertTarget.WirelessDebugging)

    check(
        "a manual change with no revert pending records nothing",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = false,
        ) == null,
    )

    check(
        "a manual change with a revert pending records the value it had",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1"),
    )

    check(
        "switching something on records that it was off",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = false,
            revertPending = true,
        ) == mapOf(usbId to "0"),
    )

    // First owner. A second press must not overwrite the first reading with the value IMD
    // itself just wrote - the same guard recordDeviceWideValues applies on the hide side.
    check(
        "a key already recorded is not re-recorded",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = false,
            revertPending = true,
        ) == null,
    )

    check(
        "a new key is merged rather than replacing the record",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.WirelessDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1", wifiId to "1"),
    )

    check(
        "another holder's record does not count as already recorded",
        manualChangeRecord(
            settingStateBefore = mapOf("com.example/.Main" to mapOf(usbId to "1")),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1"),
    )

    // The three hold-backed targets keep their own records - an accessibility or overlay
    // hold is written before the shell command for crash safety, and Shizuku has no stored
    // "before" value at all - so none of them is ever written here.
    check(
        "accessibility services are not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.AccessibilityServices,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    check(
        "Shizuku is not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.Shizuku,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    check(
        "Display over other apps is not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.DisplayOverOtherApps,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    // Belt and braces on the rule itself: a hold-backed target with nothing pending is still
    // null, so neither half of the guard is doing all the work on its own.
    check(
        "no revert pending beats everything else",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.WirelessDebugging,
            currentlyEnabled = true,
            revertPending = false,
        ) == null,
    )
"""


def main() -> int:
    path = ROOT / HOST_TESTS

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {HOST_TESTS} is missing")

        return 1

    text = path.read_text(encoding="utf-8")

    problems: list[str] = []

    for name, chunk, expected in (
        ("import anchor", IMPORT_ANCHOR, 1),
        ("test anchor", ANCHOR, 1),
    ):
        found = text.count(chunk)

        if found != expected:
            problems.append(f"{name}: expected {expected}, found {found}")

    # ⚠ The holder key is spelled out from AccessibilityServicePlan rather than reusing one
    # of the `deviceWide` locals further up the file - those are local vals inside other test
    # functions and are not in scope here. The type itself has to be imported.
    if "import com.android.geto.domain.model.AccessibilityServicePlan" not in text:
        problems.append("AccessibilityServicePlan is not imported in the host tests")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    staged = text.replace(IMPORT_ANCHOR, IMPORT_NEW, 1).replace(ANCHOR, TESTS, 1)

    before = set(text.splitlines())

    for line in staged.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    added = staged.count("    check(") - text.count("    check(")

    if added != 10:
        problems.append(f"added {added} checks, expected 10")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(staged, encoding="utf-8")

    print(f"  wrote {path.relative_to(ROOT)}")
    print(f"ok — {added} assertions for manualChangeRecord")

    return 0


if __name__ == "__main__":
    sys.exit(main())
