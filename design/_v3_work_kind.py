#!/usr/bin/env python3
"""
v3-r1 — tell SettingsWorkTracker which way each piece of work is going.

The settings manager has to say 'IMD hiding settings, please wait...' or 'IMD unhiding
settings, please wait...' while its toggles are disabled, and the tracker only knew *that*
work was running, not which kind. This passes a SettingsWorkKind at every signaller.

⚠ HideViewModel is deliberately NOT in this list. It claims the tracker before it reads
whether it is about to hide or unhide, so that the tile goes unavailable from the press
rather than from the write — it genuinely does not know yet, and the use case underneath it
claims again with a kind a moment later. See SettingsWorkTracker.begin.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

USE_CASE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase"
RECEIVER = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver"

IMPORT = "import com.android.geto.domain.usecase.SettingsWorkKind"

# (path, old, new, needs_import)
EDITS = [
    # --- hiding -------------------------------------------------------------------
    (
        f"{USE_CASE}/ApplySettingsToHideUseCase.kt",
        "settingsWorkTracker.track {",
        "settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {",
        False,  # same package
    ),
    (
        f"{USE_CASE}/ApplyAppSettingsUseCase.kt",
        "settingsWorkTracker.track { applyProfile(componentName = componentName) }",
        "settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {\n"
        "            applyProfile(componentName = componentName)\n"
        "        }",
        False,
    ),
    # --- unhiding -----------------------------------------------------------------
    (
        f"{USE_CASE}/RevertToDefaultUseCase.kt",
        "settingsWorkTracker.track {",
        "settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {",
        False,
    ),
    (
        f"{USE_CASE}/RevertAppSettingsUseCase.kt",
        "settingsWorkTracker.track { revertProfile(componentName = componentName) }",
        "settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {\n"
        "            revertProfile(componentName = componentName)\n"
        "        }",
        False,
    ),
    (
        f"{RECEIVER}/OverlayRestoreRunner.kt",
        "settingsWorkTracker.track {",
        "settingsWorkTracker.track(kind = SettingsWorkKind.Unhiding) {",
        True,
    ),
    # --- IMD+: a run hides, its revert unhides ------------------------------------
    (
        f"{RECEIVER}/AutoHideRunner.kt",
        "settingsWorkTracker.begin()",
        "settingsWorkTracker.begin(kind = SettingsWorkKind.Hiding)",
        True,
    ),
    (
        f"{RECEIVER}/AutoHideRunner.kt",
        "settingsWorkTracker.end()",
        "settingsWorkTracker.end(kind = SettingsWorkKind.Hiding)",
        False,  # same file as the edit above, import added once
    ),
    # Wrapped at the argument rather than at the lambda. Putting the call on its own line
    # would push the whole block one level in, and re-indenting a body to fit an edit is the
    # exact move that broke r13's first zip. This way the body is not touched at all.
    (
        f"{RECEIVER}/AutoHideRunner.kt",
        "settingsWorkTracker.track<Unit> {",
        "settingsWorkTracker.track<Unit>(\n"
        "        kind = SettingsWorkKind.Unhiding,\n"
        "    ) {",
        False,
    ),
]


def insert_import(text: str, statement: str) -> str:
    """Put an import into the block in ASCII order, leaving the javax/java tail alone."""
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
    planned: dict[Path, str] = {}
    report: list[str] = []

    for rel, old, new, needs_import in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = planned.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  anchor {old!r}\n  matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries the replacement — has this run before?")
            return 1

        text = text.replace(old, new, 1)

        if needs_import:
            text = insert_import(text, IMPORT)
            report.append(f"  + import  {rel}")

        planned[path] = text
        report.append(f"  ok        {rel}  :: {old.strip()[:52]}")

    # Nothing is written until every anchor above has matched exactly once.
    for path, text in planned.items():
        over = [
            (n, len(line))
            for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ")
        ]

        if over:
            print(f"REFUSED: {path.relative_to(ROOT)} would carry lines over 120 chars: {over}")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print("\n".join(report))
    print(f"\nwrote {len(planned)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
