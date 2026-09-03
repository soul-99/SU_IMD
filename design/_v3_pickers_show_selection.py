#!/usr/bin/env python3
"""
v3-r2b3b part 3 — both pickers list what the user has selected, whatever state it is in.

**The author's report, in his words:** "the DOOAs to hide dialog box should show selected as well
as enabled apps, currently it does not show selected but off ones".

**And a correction he asked for.** He thought the accessibility picker already did this. It does
not — `accessibilityServicesForPicker` filters on `enabled || id in held`, exactly as
`GetOverlayPackagesUseCase` unions `allowed + held`. The two are the same shape and have the same
hole; his accessibility services were simply on at the time.

**The hole.** "Held by IMD" covers the ordinary case — a hide is in force, so the selection is off
*and* recorded — which is why this survived so long. It misses every case where the selection is
off with **no record**:

* the record was discarded, which is what the force-close popup's Ignore does;
* the user switched the service or the permission off themselves in the system settings;
* a hide failed part-way and the debt was never written.

In all three the row disappears from the picker for as long as the state lasts — and it is the one
row the person opening that picker came to find, because it is the one they can no longer untick.
The selection is persisted and is the user's own answer; a picker that hides it is editing their
configuration behind their back.

⚠ **Union, not a third state.** `allowed` and `enabled` still say what the device says. A selected
package that is off simply appears with its switch off, which is the truth, and the existing sort
already floats it to the top.

⚠ **The overlay list's labels come from `getAppLabels(names)`**, and `names` is what grows here, so
a selected-but-off package keeps its label rather than falling back to its package name.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PICKER = (
    "domain/model/src/main/kotlin/com/android/geto/domain/model/AccessibilityServiceData.kt"
)

OVERLAY = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetOverlayPackagesUseCase.kt"
)

SERVICES = (
    "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetAccessibilityServicesUseCase.kt"
)

PICKER_EDITS: list[tuple[str, str]] = [
    (
        """ * So the rule is enabled **or** currently held down by IMD. Everything IMD turned off is
 * something it owes back, which is exactly what the first line of the dialog now promises, and
 * a promise about services you cannot see is worth nothing.
""",
        """ * So the rule is enabled **or** currently held down by IMD. Everything IMD turned off is
 * something it owes back, which is exactly what the first line of the dialog now promises, and
 * a promise about services you cannot see is worth nothing.
 *
 * ⚠ **Or selected**, which closes the hole the two above leave between them. "Held" only covers a
 * service IMD switched off *and still has a record of*. A service the user switched off in the
 * system settings themselves, or one whose record was discarded, is selected, off and unheld —
 * and vanishes from the picker for as long as that lasts, taking with it the only control that
 * could unselect it. The selection is the user's own answer and is always worth showing; the
 * `enabled` flag on the row goes on telling the truth about the device.
""",
    ),
    (
        """fun accessibilityServicesForPicker(
    services: List<AccessibilityServiceData>,
    heldAccessibilityServices: Map<String, List<String>>,
    ownDetector: String = "",
): List<AccessibilityServiceData> {
    val held = heldAccessibilityServices.values.flatten().toSet()

    return services.filter { service ->
        service.enabled || service.id in held || (ownDetector.isNotBlank() && service.id == ownDetector)
    }
}""",
        """fun accessibilityServicesForPicker(
    services: List<AccessibilityServiceData>,
    heldAccessibilityServices: Map<String, List<String>>,
    ownDetector: String = "",
    managedAccessibilityServices: List<String> = emptyList(),
): List<AccessibilityServiceData> {
    val held = heldAccessibilityServices.values.flatten().toSet()

    val selected = managedAccessibilityServices.toSet()

    return services.filter { service ->
        service.enabled ||
            service.id in held ||
            service.id in selected ||
            (ownDetector.isNotBlank() && service.id == ownDetector)
    }
}""",
    ),
]

SERVICES_EDITS: list[tuple[str, str]] = [
    (
        """     * Narrowed to what the picker should show since v3 — see [accessibilityServicesForPicker]
     * for why that is "enabled **or** held by IMD" rather than the literal "enabled".
""",
        """     * Narrowed to what the picker should show since v3 — see [accessibilityServicesForPicker]
     * for why that is "enabled, **or** held by IMD, **or** selected" rather than the literal
     * "enabled". The third was added after the author found the overlay picker dropping his
     * selection; this list had the same hole and had simply not been caught in it.
""",
    ),
    (
        """        return accessibilityServicesForPicker(
            services = accessibilityServicesWrapper.getAccessibilityServices(),
            heldAccessibilityServices = userData.heldAccessibilityServices,
        ).sortedWith(""",
        """        return accessibilityServicesForPicker(
            services = accessibilityServicesWrapper.getAccessibilityServices(),
            heldAccessibilityServices = userData.heldAccessibilityServices,
            managedAccessibilityServices = userData.managedAccessibilityServices,
        ).sortedWith(""",
    ),
]

OVERLAY_EDITS: list[tuple[str, str]] = [
    (
        """ * Packages IMD is currently holding down are included even though the live AppOp says they
 * are not allowed. They are only off because of this app, and leaving them out would empty
 * the list for exactly as long as the hiding is in force.
""",
        """ * Packages IMD is currently holding down are included even though the live AppOp says they
 * are not allowed. They are only off because of this app, and leaving them out would empty
 * the list for exactly as long as the hiding is in force.
 *
 * ⚠ **And the selection itself**, which is the author's own report: a package that is selected,
 * off, and *not* held — because the user withdrew the permission themselves, or because the
 * hold record was discarded — was in neither of the two sets above and disappeared from the
 * list. It is the one row somebody opening this picker most needs, since it is the only place
 * it can be unselected. The `allowed` flag still reports what the device says, so the row shows
 * up with its permission off, which is the truth.
""",
    ),
    (
        """        val names = allowed + held
""",
        """        val names = allowed + held + userData.managedOverlayPackages
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    targets = [
        (ROOT / PICKER, PICKER_EDITS),
        (ROOT / SERVICES, SERVICES_EDITS),
        (ROOT / OVERLAY, OVERLAY_EDITS),
    ]

    written: list[tuple[Path, str]] = []

    for path, edits in targets:
        text = apply(path, edits, problems)

        if text is not None:
            written.append((path, text))

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in written:
        path.write_text(text, encoding="utf-8")

    print("ok — both pickers list the user's selection whatever the device has done to it")

    return 0


if __name__ == "__main__":
    sys.exit(main())
