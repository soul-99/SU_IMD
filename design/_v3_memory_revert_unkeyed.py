#!/usr/bin/env python3
"""r4g — a memory revert stops skipping accessibility services, Shizuku and overlay access.

The author, with a log:

    "i just unhid settings after all were hidden but accessibility serv, shizuku and dooa did
     not unhide after"

    09-01 19:30:41.128  hide    device-wide -> Success
    09-01 19:30:41.137  settled: live  dev=off usb=off wifi=off a11y=off shizuku=off overlay=off
    09-01 19:30:43.681  revert  revert to default explicit=false fromMemory=true
    09-01 19:30:43.741  revert  device-wide -> RevertToDefaultResult(
                                    changed=[DeveloperSettings, UsbDebugging, WirelessDebugging],
                                    failed=[], unchanged=[])
    09-01 19:30:43.745  settled: live  dev=on usb=on wifi=on a11y=off shizuku=off overlay=off

⚠ **Three targets are not in `changed`, not in `failed` and not in `unchanged`.** They were never
considered. Every explicit revert in the same log reports all six.

### The mechanism

A device-wide **memory** revert passes `wantedOverride` — built by `deviceWideMemoryWanted`, which
walks the targets and does `deviceWideSnapshotId(target) ?: continue`. Only Developer settings, USB
debugging and Wireless debugging name a global setting, so only those three can ever be in it. The
other three have nothing to record: accessibility services and Shizuku keep holds of their own, and
overlay access has no "before" value at all because switching it off is a broadcast — the
`manualChangeRecord` KDoc already says exactly this.

`RevertToDefaultUseCase` then did:

    val configured = wantedOverride ?: userData.effectiveRevertDefaults

so under a memory revert `wanted` **was** that three-entry map, and every read of it falls away:

    ordinaryTargets loop   wanted[target] ?: continue      -> AccessibilityServices skipped
    overlayEnabled         wanted[overlay]  == null        -> overlayNeedsWrite false, and the
                                                              `else if (overlayEnabled != null)`
                                                              branch is false too, so the target
                                                              is absent from the result entirely
    Shizuku settle         wanted[Shizuku]?.let { }        -> never runs

Which is the log, line for line.

### The fix

The override supplies a **destination**, and it can only speak for the targets it can measure. The
three it cannot now fall back to the configured revert defaults — the only answer that exists for
them, and the same answer an explicit revert gives:

    userData.effectiveRevertDefaults.filterKeys { deviceWideSnapshotId(it) == null } + wantedOverride

⚠ **Filtered by "can this target be recorded at all", not by "was it recorded this time".** A keyed
target missing from the record is a setting the hide never touched, and driving it to a
configuration the user may never have looked at is the thing the memory framework exists to avoid.
A target with no snapshot id is a different case: it is missing because it *cannot* be there.

⚠ **The wireless-debugging filter still sees the right map.** It tests the merged `configured`,
and wireless debugging is keyed — so it is governed by the record exactly as before, and the merge
cannot reintroduce it from the defaults.

⚠ **This is not the same as passing no override.** The keyed three still go back to what the hide
measured; only the unkeyed three change, and they change from *nothing at all* to the configured
state.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USE_CASE = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
            "RevertToDefaultUseCase.kt")
TESTS = "tools/host-tests/DomainLogicTests.kt"

OLD = """        val configured = wantedOverride ?: userData.effectiveRevertDefaults
"""

NEW = """        // ⚠ **The override speaks only for what it can measure.** `deviceWideMemoryWanted`
        // builds it by walking the targets and skipping any without a `deviceWideSnapshotId`,
        // so it can only ever carry Developer settings, USB debugging and Wireless debugging.
        // Accessibility services and Shizuku keep holds of their own and overlay access has no
        // "before" value at all, because switching it off is a broadcast.
        //
        // Until r4g the override was used as the whole destination, so those three fell out of
        // every read below - `wanted[target] ?: continue` in the ordinary loop, a null
        // `overlayEnabled` that skips the overlay block *and* its `unchanged` branch, and a
        // `wanted[Shizuku]?.let` that never runs. The author's log: a device-wide memory revert
        // reporting `changed=[DeveloperSettings, UsbDebugging, WirelessDebugging]` and nothing
        // else, on a device that had all six hidden.
        //
        // ⚠ **Filtered by "can this target be recorded at all", not by "was it recorded this
        // time".** A keyed target absent from the record is a setting the hide never touched,
        // and driving that to a configuration the user may never have looked at is the thing
        // the memory framework exists to avoid. A target with no snapshot id is absent because
        // it *cannot* be present, and the configured default is the only answer there is.
        val configured = if (wantedOverride != null) {
            userData.effectiveRevertDefaults
                .filterKeys { deviceWideSnapshotId(target = it) == null } + wantedOverride
        } else {
            userData.effectiveRevertDefaults
        }
"""

IMPORT_OLD = """import com.android.geto.domain.model.effectiveRevertDefaults
"""

IMPORT_NEW = """import com.android.geto.domain.model.deviceWideSnapshotId
import com.android.geto.domain.model.effectiveRevertDefaults
"""

TEST_ANCHOR = """import com.android.geto.domain.model.deviceWideMemoryWanted
"""

TEST_BLOCK = '''
// ---------------------------------------------------------------------------------
// r4g - a device-wide memory revert covers the targets it cannot measure
// ---------------------------------------------------------------------------------

private fun memoryRevertCoverageTests() {
    // What RevertToDefaultUseCase computes as its destination, in the two shapes it takes.
    fun destination(
        defaults: Map<ManualRevertTarget, Boolean>,
        override: Map<ManualRevertTarget, Boolean>?,
    ): Map<ManualRevertTarget, Boolean> = if (override != null) {
        defaults.filterKeys { deviceWideSnapshotId(target = it) == null } + override
    } else {
        defaults
    }

    val defaults = ManualRevertTarget.entries.associateWith { true }

    // The author's log: a device-wide hide with all six hidden, then a memory revert.
    val recorded = mapOf(
        SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1",
        SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled") to "1",
        SettingSnapshot.idOf(SettingType.GLOBAL, "adb_wifi_enabled") to "1",
    )

    val override = deviceWideMemoryWanted(recorded = recorded)

    check(
        "the memory record can only ever carry the three keyed targets",
        override.keys == setOf(
            ManualRevertTarget.DeveloperSettings,
            ManualRevertTarget.UsbDebugging,
            ManualRevertTarget.WirelessDebugging,
        ),
    )

    val wanted = destination(defaults = defaults, override = override)

    // The bug: these three were absent, so the revert never considered them at all.
    for (target in listOf(
        ManualRevertTarget.AccessibilityServices,
        ManualRevertTarget.Shizuku,
        ManualRevertTarget.DisplayOverOtherApps,
    )) {
        check("a memory revert still drives $target", wanted[target] == true)
    }

    check(
        "and the keyed three still come from the record",
        wanted[ManualRevertTarget.UsbDebugging] == true,
    )

    // A keyed target the hide never touched stays absent: the memory framework's whole point.
    val partial = deviceWideMemoryWanted(
        recorded = mapOf(
            SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1",
        ),
    )

    val fromPartial = destination(defaults = defaults, override = partial)

    check(
        "an unrecorded keyed target is not driven from the defaults",
        ManualRevertTarget.UsbDebugging !in fromPartial,
    )

    check(
        "and an unkeyed one still is",
        fromPartial[ManualRevertTarget.AccessibilityServices] == true,
    )

    // A record saying a setting was off before keeps it off, over a default that wants it on.
    val wasOff = deviceWideMemoryWanted(
        recorded = mapOf(
            SettingSnapshot.idOf(SettingType.GLOBAL, "adb_wifi_enabled") to "0",
        ),
    )

    check(
        "the record beats the default where it has an opinion",
        destination(defaults = defaults, override = wasOff)[
            ManualRevertTarget.WirelessDebugging,
        ] == false,
    )

    // An explicit revert passes no override and is untouched by any of this.
    check(
        "an explicit revert still drives the configured defaults",
        destination(defaults = defaults, override = null) == defaults,
    )
}
'''


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    use_case = ROOT / USE_CASE
    tests = ROOT / TESTS

    for path in (use_case, tests):
        if not path.exists():
            print("REFUSED, nothing written")
            print(f"  {path.relative_to(ROOT)} is missing")

            return 1

    text = use_case.read_text(encoding="utf-8")

    for old, new, expected in ((OLD, NEW, 1), (IMPORT_OLD, IMPORT_NEW, 1)):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"{USE_CASE}: expected {expected} of "
                f"{old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    staged[use_case] = text

    test_text = tests.read_text(encoding="utf-8")

    if TEST_ANCHOR not in test_text:
        problems.append(f"{TESTS}: deviceWideMemoryWanted is not imported")

    if "import com.android.geto.domain.model.deviceWideSnapshotId\n" not in test_text:
        test_text = test_text.replace(
            TEST_ANCHOR,
            TEST_ANCHOR + "import com.android.geto.domain.model.deviceWideSnapshotId\n",
            1,
        )

    # The suite's runner: every test function is called from one place.
    runner = "    frameworkSplitTests()\n"

    if test_text.count(runner) != 1:
        problems.append(f"{TESTS}: cannot find the one call to frameworkSplitTests()")
    else:
        test_text = test_text.replace(runner, runner + "    memoryRevertCoverageTests()\n", 1)

    staged[tests] = test_text.rstrip("\n") + "\n" + TEST_BLOCK

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    body = staged[use_case]

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        ("wantedOverride ?: userData.effectiveRevertDefaults", 0),
        ("deviceWideSnapshotId(target = it) == null", 1),
        ("+ wantedOverride", 1),
        # The wireless filter must still read the merged map, and only once.
        ("configured[ManualRevertTarget.WirelessDebugging] == true", 1),
        ("configured - ManualRevertTarget.WirelessDebugging", 1),
    ):
        if body.count(token) != expected:
            problems.append(f"{USE_CASE}: expected {expected} of {token!r}, "
                            f"found {body.count(token)}")

    if staged[tests].count("memoryRevertCoverageTests()") != 2:
        problems.append(f"{TESTS}: the new tests are not declared and called exactly once each")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, content in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in content.splitlines():
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

    for path, content in staged.items():
        path.write_text(content, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - a memory revert now covers accessibility, Shizuku and overlay access")

    return 0


if __name__ == "__main__":
    sys.exit(main())
