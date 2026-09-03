#!/usr/bin/env python3
"""
v3 — a memory restore never switches wireless debugging back on unless asked to.

The author's rule: *"if it is memory, and IMD did turn wireless debugging to off from on
during hiding, only toggle it on again during unhiding when this checkbox is on"*, and it
covers **both** memory restores — a per-app profile's and the device-wide one.

Two gates, in the two places a memory restore decides what wireless debugging should be:

  RevertAppSettingsUseCase   a per-app profile. The setting is dropped from the write loop.
  RevertToDefaultUseCase     the device-wide memory restore, which reaches this file through
                             `wantedOverride`. The entry is dropped from `wanted`, and the
                             loop there already reads `wanted[target] ?: continue`.

⚠ **Only the *on* direction is gated, in both.** A memory restore that wants wireless
debugging switched **off** still switches it off — that is the safe direction, and refusing it
would leave a device more exposed than the record says it was, which is the opposite of what
this setting is for.

⚠ **`wantedOverride != null` is the memory test in `RevertToDefaultUseCase`**, not the stored
framework. That parameter has exactly one caller — the device-wide memory revert — and the
file's own doc says the explicit `Revert to default` routes must never pass it. Reading the
stored framework instead would gate an explicit `Revert to default` pressed while the memory
function happened to be selected, which is a different function with its own configuration
row for this setting.

⚠ **Under Revert to default neither gate fires**, because that framework drives
`revertDefaults`, whose Wireless debugging row already answers this question. Gating there as
well would give one question two answers, and would silently change what upgrading installs
do — which the author was asked about and explicitly did not want.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PER_APP = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
           "RevertAppSettingsUseCase.kt")
DEVICE_WIDE = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
               "RevertToDefaultUseCase.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (PER_APP, [
        (
            """import com.android.geto.domain.model.SettingSnapshot
""",
            """import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.UnhidingFramework
""",
            1,
        ),
        (
            """            .filterNot { it.key == AppSettingKeys.SHIZUKU_SERVICE }
""",
            """            .filterNot { it.key == AppSettingKeys.SHIZUKU_SERVICE }
            // ⚠ **Wireless debugging is not switched back on by a memory restore unless the
            // user has asked for it.** A device that comes out of a hide with wireless
            // debugging on is listening on whatever network it is attached to, with nothing
            // on screen saying so, so the author made putting it back opt-in.
            //
            // Only the *on* direction. A record that says it was off before the hide still
            // switches it off here, because that is the direction this rule exists to
            // protect, and refusing it would leave the device more exposed than the record.
            //
            // Under Revert to default this never fires: that framework drives revertDefaults,
            // which carries its own Wireless debugging row and answers this question there.
            .filterNot { setting ->
                userData.unhidingFramework == UnhidingFramework.Memory &&
                    !userData.restoreWirelessDebugging &&
                    setting.key == AppSettingKeys.ADB_WIFI_ENABLED &&
                    SettingSnapshot.revertValue(
                        recorded = recorded,
                        settingType = setting.settingType,
                        key = setting.key,
                        configured = setting.valueOnRevert,
                    ) == WIRELESS_DEBUGGING_ON
            }
""",
            1,
        ),
    ]),
    (DEVICE_WIDE, [
        (
            """        val wanted = wantedOverride ?: userData.effectiveRevertDefaults
""",
            """        val configured = wantedOverride ?: userData.effectiveRevertDefaults

        // ⚠ **A memory restore does not switch wireless debugging back on unless asked to.**
        // The author's rule, and the device-wide half of it — the per-app half is the same
        // filter in RevertAppSettingsUseCase.
        //
        // `wantedOverride != null` is the memory test rather than the stored framework, and
        // deliberately: that parameter has exactly one caller, the device-wide memory revert,
        // while an explicit `Revert to default` never passes it and must keep driving its own
        // configuration whatever framework happens to be selected.
        //
        // Dropped from the map rather than forced false: the loop below reads
        // `wanted[target] ?: continue`, so an absent entry is left exactly as the device has
        // it. Only the *on* direction is dropped — a memory record asking for it to be
        // switched off still switches it off.
        val wanted = if (
            wantedOverride != null &&
            !userData.restoreWirelessDebugging &&
            configured[ManualRevertTarget.WirelessDebugging] == true
        ) {
            configured - ManualRevertTarget.WirelessDebugging
        } else {
            configured
        }
""",
            1,
        ),
    ]),
]

# The literal is spelled once, beside the filter that uses it, rather than reaching for the
# private ON in SetManualTargetUseCase - a file-level private is file-scoped, which is the
# first entry in the project's own trap table.
CONSTANT = """
/** What a switched-on global setting stores. Matches AppSettingKeys' own `valueOnRevert` test. */
private const val WIRELESS_DEBUGGING_ON = "1"
"""


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

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # The constant goes after the imports and before the first declaration, which is where
    # this file's siblings put theirs. Anchored on the KDoc that opens the class rather than
    # on a line number.
    per_app = staged[ROOT / PER_APP]
    anchor = "\n/**\n"
    head, sep, tail = per_app.partition(anchor)

    if not sep:
        problems.append(f"{PER_APP}: no KDoc block to place the constant before")
    else:
        staged[ROOT / PER_APP] = head + CONSTANT + sep + tail

    # `configured` must not survive anywhere the loop reads, or the gate is bypassed.
    device_wide = staged[ROOT / DEVICE_WIDE]

    # ⚠ Anchored on the whole statement, not on the subscript. The comment this script writes
    # quotes the subscript to explain why an absent entry is safe, so a bare substring test
    # counts its own prose and refuses - which it did, on the first run.
    if device_wide.count("val enabled = wanted[target] ?: continue") != 1:
        problems.append(f"{DEVICE_WIDE}: the ordinary-target loop no longer reads `wanted`")

    if device_wide.count("configured[ManualRevertTarget.WirelessDebugging]") != 1:
        problems.append(f"{DEVICE_WIDE}: the gate reads something other than `configured`")

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

    print("ok — both memory restores gate wireless debugging, on-direction only")

    return 0


if __name__ == "__main__":
    sys.exit(main())
