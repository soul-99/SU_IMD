#!/usr/bin/env python3
"""
v3 — the master pill's order moves into :domain:model, where a host assertion can guard it.

It was written as a private val in `SettingsManagerViewModel`, which works and is untestable:
the host runner compiles `:domain:model` only, so nothing there could say whether the list
still covers every target. A seventh `ManualRevertTarget` added later would simply never be
moved by the pill, silently, and no check in the suite reads a list of enum members against
the enum.

Moved beside the enum itself, with two assertions that fail the moment it drifts:

  * every target appears exactly once
  * the dependency order holds — developer options before USB debugging, Shizuku before
    Display over other apps, wireless debugging last

⚠ **The order is a dependency graph, not a preference.** USB debugging needs developer
options; Display over other apps needs Shizuku alive to write its AppOps; and wireless
debugging goes last because starting a Shizuku fork brings the debugging transport up with its
own WRITE_SECURE_SETTINGS and moves wireless debugging on the way, so settling it any earlier
lets the fork overrule the press. Off is the exact reverse for the same three reasons read
backwards.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANUAL_REVERT = "domain/model/src/main/kotlin/com/android/geto/domain/model/ManualRevert.kt"
VIEW_MODEL = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
HOST_TESTS = "tools/host-tests/DomainLogicTests.kt"

DOMAIN_ADDITION = '''
/**
 * The order the settings manager's master pill switches targets **on** in; off is the exact
 * reverse.
 *
 * ⚠ **Not [ManualRevertTarget.entries], and the difference is a dependency graph rather than a
 * preference:**
 *
 *  * developer options first, because USB debugging depends on it;
 *  * Shizuku before Display over other apps, whose AppOps can only be written while Shizuku is
 *    running;
 *  * wireless debugging **last**, because starting a Shizuku fork brings the debugging
 *    transport up using its own WRITE_SECURE_SETTINGS and moves wireless debugging on the way.
 *    Settled any earlier, the fork overrules the press.
 *
 * Reversed on the way off, which puts Display over other apps before Shizuku stops and leaves
 * developer options until last — the same three reasons read backwards.
 *
 * Lives here rather than in the ViewModel that uses it so the host tests can assert it still
 * covers every target: a seventh one added later would otherwise be silently skipped by the
 * pill, with nothing in the audit suite able to see it.
 */
val masterPillOnOrder: List<ManualRevertTarget> = listOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.AccessibilityServices,
    ManualRevertTarget.Shizuku,
    ManualRevertTarget.DisplayOverOtherApps,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * The targets the master pill should move, in the order it should move them.
 *
 * [usable] is the dialog's own per-row test, handed over rather than recomputed — the pill's
 * promise is that it moves exactly the rows the user could have moved by hand.
 */
fun masterPillOrder(
    enabled: Boolean,
    usable: List<ManualRevertTarget>,
): List<ManualRevertTarget> = masterPillOnOrder.filter { it in usable }.let {
    if (enabled) it else it.reversed()
}
'''

HOST_ANCHOR = """    check(
        "no revert pending beats everything else",
"""

HOST_TESTS_ADDITION = '''    // The master pill's order. Guarded here rather than left to a reviewer, because a
    // seventh ManualRevertTarget added later would otherwise be skipped by the pill in
    // silence - nothing in the audit suite reads a list of enum members against its enum.
    check(
        "the pill order covers every target exactly once",
        masterPillOnOrder.toSet() == ManualRevertTarget.entries.toSet() &&
            masterPillOnOrder.size == ManualRevertTarget.entries.size,
    )

    val pillOn = masterPillOrder(enabled = true, usable = ManualRevertTarget.entries.toList())

    val pillOff = masterPillOrder(enabled = false, usable = ManualRevertTarget.entries.toList())

    check(
        "on: developer options before USB debugging",
        pillOn.indexOf(ManualRevertTarget.DeveloperSettings) <
            pillOn.indexOf(ManualRevertTarget.UsbDebugging),
    )

    check(
        "on: Shizuku before the overlay AppOps that need it running",
        pillOn.indexOf(ManualRevertTarget.Shizuku) <
            pillOn.indexOf(ManualRevertTarget.DisplayOverOtherApps),
    )

    check(
        "on: wireless debugging last, after the Shizuku start that moves it",
        pillOn.last() == ManualRevertTarget.WirelessDebugging,
    )

    check("off is exactly the reverse of on", pillOff == pillOn.reversed())

    check(
        "off: developer options last of all",
        pillOff.last() == ManualRevertTarget.DeveloperSettings,
    )

    // The pill never touches a row the dialog called unusable.
    val pillSome = listOf(ManualRevertTarget.WirelessDebugging, ManualRevertTarget.UsbDebugging)

    check(
        "an unusable row is never moved",
        masterPillOrder(enabled = true, usable = pillSome).none { it !in pillSome },
    )

    check(
        "a partial list keeps the canonical order",
        masterPillOrder(enabled = true, usable = pillSome) ==
            listOf(ManualRevertTarget.UsbDebugging, ManualRevertTarget.WirelessDebugging),
    )

    check(
        "nothing usable orders nothing",
        masterPillOrder(enabled = true, usable = emptyList()).isEmpty(),
    )

    check(
        "no revert pending beats everything else",
'''

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (VIEW_MODEL, [
        (
            """/**
 * The order the master pill switches things **on** in; off is the exact reverse.
 *
 * Not [ManualRevertTarget.entries]. Wireless debugging is last because starting a Shizuku fork
 * moves it, developer options is first because USB debugging depends on it, and Display over
 * other apps follows Shizuku because its AppOps can only be written while Shizuku is running.
 */
private val ALL_TARGETS_ON_ORDER = listOf(
    ManualRevertTarget.DeveloperSettings,
    ManualRevertTarget.UsbDebugging,
    ManualRevertTarget.AccessibilityServices,
    ManualRevertTarget.Shizuku,
    ManualRevertTarget.DisplayOverOtherApps,
    ManualRevertTarget.WirelessDebugging,
)

/**
 * Everything the settings manager needs, independent of where it is being shown from.""",
            """/**
 * Everything the settings manager needs, independent of where it is being shown from.""",
            1,
        ),
        (
            """            val ordered = ALL_TARGETS_ON_ORDER.filter { it in targets }.let {
                if (enabled) it else it.reversed()
            }
""",
            """            // In :domain:model, where the host tests can assert it still covers every
            // target - see masterPillOnOrder for why the order is what it is.
            val ordered = masterPillOrder(enabled = enabled, usable = targets)
""",
            1,
        ),
        (
            """import com.android.geto.domain.model.ManualTargetStates
""",
            """import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.model.masterPillOrder
""",
            1,
        ),
    ]),
    (HOST_TESTS, [
        (
            """import com.android.geto.domain.model.manualChangeRecord
""",
            """import com.android.geto.domain.model.manualChangeRecord
import com.android.geto.domain.model.masterPillOnOrder
import com.android.geto.domain.model.masterPillOrder
""",
            1,
        ),
        (HOST_ANCHOR, HOST_TESTS_ADDITION, 1),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    manual_revert = ROOT / MANUAL_REVERT

    if not manual_revert.exists():
        problems.append(f"{MANUAL_REVERT}: missing")
    else:
        text = manual_revert.read_text(encoding="utf-8")

        if "masterPillOnOrder" in text:
            problems.append(f"{MANUAL_REVERT}: masterPillOnOrder already present")
        else:
            staged[manual_revert] = text.rstrip("\n") + "\n" + DOMAIN_ADDITION

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

    # The old private val must be gone from the ViewModel, or two orders exist and only one
    # is guarded.
    view_model = staged[ROOT / VIEW_MODEL]

    if "ALL_TARGETS_ON_ORDER" in view_model:
        problems.append(f"{VIEW_MODEL}: the private order survived the move")

    host = staged[ROOT / HOST_TESTS]

    added = host.count("    check(") - (ROOT / HOST_TESTS).read_text(
        encoding="utf-8",
    ).count("    check(")

    if added != 9:
        problems.append(f"added {added} checks, expected 9")

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

    print(f"ok — the pill order is in :domain:model with {added} assertions on it")

    return 0


if __name__ == "__main__":
    sys.exit(main())
