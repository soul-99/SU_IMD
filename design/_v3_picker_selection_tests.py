#!/usr/bin/env python3
"""
v3-r2b3b — host assertions for the selection arm of `accessibilityServicesForPicker`.

The new arm has a default argument, so every existing assertion went on passing untouched when
the parameter was added — which is exactly why it needs assertions of its own rather than the
green run being taken as cover.

Four, and the last two are the ones that matter: a selected service must survive being neither
enabled nor held (the reported bug), and an unselected, unheld, disabled one must still stay out
(the rule the picker existed to enforce in the first place).

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

EDITS: list[tuple[str, str]] = [
    (
        """    checkEquals(
        "an empty list in, an empty list out",
        emptyList<String>(),
        accessibilityServicesForPicker(
            services = emptyList(),
            heldAccessibilityServices = mapOf("h" to listOf("a/.A")),
        ).map { it.id },
    )
}
""",
        """    checkEquals(
        "an empty list in, an empty list out",
        emptyList<String>(),
        accessibilityServicesForPicker(
            services = emptyList(),
            heldAccessibilityServices = mapOf("h" to listOf("a/.A")),
        ).map { it.id },
    )

    // r2b3b. The author reported the overlay picker dropping a package he had selected; this
    // list had the same hole. "Held" only covers a service IMD switched off *and still has a
    // record of* — so a service the user switched off themselves, or one whose record was
    // discarded by 'Ignore all previous reverts', was selected, off, unheld and invisible.
    val selected = accessibilityServicesForPicker(
        services = all,
        heldAccessibilityServices = emptyMap(),
        managedAccessibilityServices = listOf("c/.C"),
    )

    checkEquals(
        "a selected service is listed even when it is neither enabled nor held",
        listOf("a/.A", "c/.C"),
        selected.map { it.id },
    )

    check(
        "and the rule it was hiding behind still holds: unselected, unheld and off stays out",
        "b/.B" !in selected.map { it.id },
    )

    checkEquals(
        "a selected service that is also held is listed once, not twice",
        listOf("a/.A", "b/.B"),
        accessibilityServicesForPicker(
            services = all,
            heldAccessibilityServices = mapOf(
                "__device_wide_settings_to_hide__" to listOf("b/.B"),
            ),
            managedAccessibilityServices = listOf("b/.B"),
        ).map { it.id },
    )

    checkEquals(
        "an empty selection changes nothing",
        listOf("a/.A"),
        accessibilityServicesForPicker(
            services = all,
            heldAccessibilityServices = emptyMap(),
            managedAccessibilityServices = emptyList(),
        ).map { it.id },
    )
}
""",
    ),
]


def main() -> int:
    problems: list[str] = []

    path = ROOT / TESTS

    if not path.exists():
        print(f"REFUSED — {TESTS} is missing")

        return 1

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{len(line)} chars — {line.strip()[:60]}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print("ok — four assertions for the picker's selection arm")

    return 0


if __name__ == "__main__":
    sys.exit(main())
