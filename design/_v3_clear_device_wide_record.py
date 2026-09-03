#!/usr/bin/env python3
"""
v3 — a completed memory revert clears the device-wide record it restored from.

**The bug, found while wiring the debt rule.** `settingStateBefore[DEVICE_WIDE_HOLD]` has
exactly one writer — `ApplySettingsToHideUseCase.recordDeviceWideValues` — and one reader,
`RevertToDefaultRunner`. Nothing anywhere clears it. `RevertToDefaultUseCase` sets
`settingsHiddenDeviceWide = false` and leaves the record standing, and
`restoreSettingsOutsideDefaults` prunes only settings *outside* the six targets, so the three
keyed ones are never pruned.

The failure, which needs two hides to show:

  1. Hide device-wide under Memory with developer options and USB debugging on → `{dev:1,
     usb:1}`.
  2. Revert → both switched back on. **Record untouched.**
  3. The user switches developer options off themselves.
  4. Hide again. `recordDeviceWideValues` skips developer options (already off) and skips USB
     debugging (`if (id in existing) continue`). Record still `{dev:1, usb:1}`.
  5. Revert → drives developer options **on**, restoring the world of step 1.

So a device-wide memory revert restores what was true at the *first* hide, permanently.

⚠ **The debt rule makes it worse, which is why it is fixed in the same build.** A manual
settings-manager change now writes into the same record, so without this every key a person
ever touched while a revert was pending would keep coming back on every later memory revert.

**The fix**, in the runner that already holds both the override and the result: once the
revert returns, drop the ids it drove. `RevertAppSettingsUseCase`'s discipline, verbatim —

  * only ids this revert actually drove, read from the override rather than from the enum, so
    a target the record said nothing about is not invented;
  * **a failed target is left recorded**, because a record left behind after a failure is what
    lets a retry still put the right value back;
  * the holder key is dropped entirely once nothing is left under it, rather than left as an
    empty map that reads as a debt to anything counting keys.

⚠ **Only when `wantedOverride` was non-null.** An explicit `Revert to default` never passes
one and never reads the record, so it has nothing to clear — and clearing it there would throw
away a memory debt that a later unhide still owes.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNNER = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
          "RevertToDefaultRunner.kt")
HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"
FRAMEWORKS = "domain/model/src/main/kotlin/com/android/geto/domain/model/Frameworks.kt"

FRAMEWORKS_ADDITION = '''
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
'''

HOST_ANCHOR = """    check(
        "the pill order covers every target exactly once",
"""

HOST_ADDITION = '''    // Clearing the device-wide record after a memory revert. Until v3 nothing cleared it at
    // all, so a second hide reverted to the state measured at the first one - for ever.
    val recordBefore = mapOf(
        deviceWideHoldKey to mapOf(
            devId(ManualRevertTarget.UsbDebugging) to "1",
            devId(ManualRevertTarget.WirelessDebugging) to "1",
        ),
    )

    check(
        "a revert that drove everything leaves no device-wide record",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = emptySet(),
        ).isEmpty(),
    )

    check(
        "a failed target stays recorded so a retry can still put it back",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = setOf(ManualRevertTarget.WirelessDebugging),
        ) == mapOf(
            deviceWideHoldKey to mapOf(devId(ManualRevertTarget.WirelessDebugging) to "1"),
        ),
    )

    check(
        "a target the revert never drove is left recorded",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(ManualRevertTarget.UsbDebugging),
            failed = emptySet(),
        ) == mapOf(
            deviceWideHoldKey to mapOf(devId(ManualRevertTarget.WirelessDebugging) to "1"),
        ),
    )

    check(
        "another holder's record is untouched",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore +
                mapOf("com.example/.Main" to mapOf(devId(ManualRevertTarget.UsbDebugging) to "1")),
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = emptySet(),
        ) == mapOf(
            "com.example/.Main" to mapOf(devId(ManualRevertTarget.UsbDebugging) to "1"),
        ),
    )

    check(
        "a revert that drove nothing changes nothing",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = emptySet(),
            failed = emptySet(),
        ) == recordBefore,
    )

    check(
        "no device-wide record at all is left alone",
        deviceWideRecordAfterRevert(
            settingStateBefore = emptyMap(),
            driven = setOf(ManualRevertTarget.UsbDebugging),
            failed = emptySet(),
        ).isEmpty(),
    )

    check(
        "the pill order covers every target exactly once",
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (RUNNER, [
        (
            """import com.android.geto.domain.model.deviceWideMemoryWanted
""",
            """import com.android.geto.domain.model.deviceWideMemoryWanted
import com.android.geto.domain.model.deviceWideRecordAfterRevert
""",
            1,
        ),
        (
            """            revertToDefaultUseCase(wantedOverride = wantedOverride).also { result ->
                // After cancelAll, so the report is not swept away by the same run that
                // produced it.
                if (result.overlayRestoreFailed) overlayRestoreRunner.report()
""",
            """            revertToDefaultUseCase(wantedOverride = wantedOverride).also { result ->
                // ⚠ **The record this revert restored from is now spent, and nothing else
                // clears it.** Before v3 nothing did at all, so a second device-wide hide
                // reverted to the state measured at the *first* one — `recordDeviceWideValues`
                // skips any key it already holds, so the stale reading simply survived. The
                // debt rule writes into the same record, which is what made this urgent.
                //
                // Failed targets are left recorded, exactly as `RevertAppSettingsUseCase`
                // leaves a failed per-app id: the record is what lets a retry put the right
                // value back.
                if (wantedOverride != null) clearDeviceWideRecord(wanted = wantedOverride, result = result)

                // After cancelAll, so the report is not swept away by the same run that
                // produced it.
                if (result.overlayRestoreFailed) overlayRestoreRunner.report()
""",
            1,
        ),
    ]),
    (HOST_TESTS, [
        (
            """import com.android.geto.domain.model.deviceWideSnapshotId
""",
            """import com.android.geto.domain.model.deviceWideRecordAfterRevert
import com.android.geto.domain.model.deviceWideSnapshotId
""",
            1,
        ),
        (HOST_ANCHOR, HOST_ADDITION, 1),
        # the holder key the new block names, beside the one the debt-rule block already added
        (
            """    val deviceWideHold = AccessibilityServicePlan.DEVICE_WIDE_HOLD
""",
            """    val deviceWideHold = AccessibilityServicePlan.DEVICE_WIDE_HOLD
""",
            1,
        ),
    ]),
]

# The private helper, appended inside the runner class. Kept out of EDITS because it is an
# insertion before the class's closing brace rather than a replacement.
RUNNER_HELPER = '''
    /**
     * Drops the device-wide memory record this revert has just restored from.
     *
     * See [deviceWideRecordAfterRevert] for what survives and why. Best-effort: a revert that
     * put the device back and then failed to tidy its own bookkeeping has still done the thing
     * the user asked for, and throwing here would skip the toast and the notifications below.
     */
    private suspend fun clearDeviceWideRecord(
        wanted: Map<ManualRevertTarget, Boolean>,
        result: RevertToDefaultResult,
    ) {
        runCatching {
            val userData = userDataRepository.userData.first()

            val cleared = deviceWideRecordAfterRevert(
                settingStateBefore = userData.settingStateBefore,
                driven = wanted.keys,
                failed = result.failed,
            )

            if (cleared !== userData.settingStateBefore) {
                userDataRepository.updateSettingStateBefore(states = cleared)
            }
        }
    }
'''


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    frameworks = ROOT / FRAMEWORKS

    if not frameworks.exists():
        problems.append(f"{FRAMEWORKS}: missing")
    elif "deviceWideRecordAfterRevert" in frameworks.read_text(encoding="utf-8"):
        problems.append(f"{FRAMEWORKS}: deviceWideRecordAfterRevert already present")
    else:
        staged[frameworks] = (
            frameworks.read_text(encoding="utf-8").rstrip("\n") + "\n" + FRAMEWORKS_ADDITION
        )

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

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # The helper goes before the class's final brace. The file ends with the class close on
    # its own line, so the last two closing braces are the function's and the class's.
    runner = staged[ROOT / RUNNER]

    if not runner.rstrip().endswith("}\n}".strip()):
        problems.append(f"{RUNNER}: unexpected tail, refusing to guess where the class ends")
    else:
        head = runner.rstrip("\n")
        staged[ROOT / RUNNER] = head[: head.rfind("}")].rstrip("\n") + "\n" + RUNNER_HELPER + "}\n"

    # The host block names deviceWideHoldKey; the debt-rule block above it named the same
    # holder deviceWideHold. One name, so the two blocks cannot drift apart.
    host = staged[ROOT / HOST_TESTS]

    staged[ROOT / HOST_TESTS] = host.replace("deviceWideHoldKey", "deviceWideHold")

    host = staged[ROOT / HOST_TESTS]

    if "deviceWideHoldKey" in host:
        problems.append(f"{HOST_TESTS}: the holder name was not unified")

    added = host.count("    check(") - (ROOT / HOST_TESTS).read_text(
        encoding="utf-8",
    ).count("    check(")

    if added != 6:
        problems.append(f"added {added} checks, expected 6")

    # ⚠ The new host block sits *above* the pill block, which is where `deviceWideHold` and
    # `devId` are declared - so it would reference them before their declaration. Asserted
    # rather than assumed, because Kotlin allows neither.
    if host.index("val deviceWideHold =") > host.index("deviceWideRecordAfterRevert("):
        problems.append(
            f"{HOST_TESTS}: the new block uses deviceWideHold before it is declared",
        )

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

    print(f"ok — a memory revert now clears what it restored from, {added} assertions")

    return 0


if __name__ == "__main__":
    sys.exit(main())
