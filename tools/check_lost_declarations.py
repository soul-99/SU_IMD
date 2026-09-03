#!/usr/bin/env python3
"""
Reports top-level Kotlin declarations that existed in a baseline tree and are gone from this one.

    python3 tools/check_lost_declarations.py /path/to/pristine

**Why this exists.** In r2 a scripted block replacement in `SettingsToHideDialog.kt` deleted the
whole of `private fun SettingToHideRow(...)` along with the info-lines it was aiming at. Twenty
three audits passed the result, and so did the domain compile, the host tests and the
translations — the author's Gradle build was the first thing to notice, with twelve errors.

Nothing in the suite could have caught it:

* `check21_syntax` only **parses**. A file with a function removed parses perfectly.
* `check22_orphan_annotations` looks for duplicated annotations, not missing declarations.
* `check18_missing_imports` covers **internal** top-level functions across files. `SettingToHideRow`
  is `private`, so it is file-scoped and invisible to that check.
* `check23_crossmodule_visibility` is about visibility, not existence.

A reference-resolving check was tried instead and abandoned: without a classpath it produced
74 false positives on a known-good tree, and a check that cries wolf is worse than no check —
the same conclusion the indentation heuristic reached in r13.

Comparing against the round's own baseline is precise instead of clever. Every round already
keeps a pristine copy for the zip round-trip, so the input costs nothing.

**Deliberate deletions are expected.** This prints what disappeared; it does not judge. Read the
list, tick off the ones the round meant to remove, and look hard at anything else.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# A top-level declaration: at column 0, optionally preceded by annotations, optionally with a
# visibility or modifier, then the keyword and the name. Indented declarations are members and
# are not this script's business — a member cannot be deleted without its class noticing.
DECLARATION = re.compile(
    r"^(?:@\w+(?:\([^\n]*\))?\s*\n)*"
    r"(?:internal |private |public )?"
    r"(?:suspend )?(?:inline )?(?:data )?(?:sealed )?(?:abstract )?"
    r"(?:fun|class|object|interface|enum class|val|var)\s+"
    r"(?:<[^>]+>\s*)?"
    r"(?:[A-Za-z_][\w.<>, ?]*\.)?"
    r"([A-Za-z_][A-Za-z0-9_]*)",
    re.M,
)


def declarations(text: str) -> set[str]:
    return set(DECLARATION.findall(text))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)

        return 2

    baseline = Path(sys.argv[1])
    current = Path(__file__).resolve().parents[1]

    if not (baseline / "settings.gradle.kts").exists():
        print(f"{baseline} does not look like the repo (no settings.gradle.kts)", file=sys.stderr)

        return 2

    findings: list[str] = []
    scanned = 0

    for old in sorted(baseline.rglob("*.kt")):
        if "build" in old.relative_to(baseline).parts:
            continue

        scanned += 1

        new = current / old.relative_to(baseline)

        if not new.exists():
            findings.append(f"{old.relative_to(baseline)}: FILE REMOVED")

            continue

        lost = declarations(old.read_text(encoding="utf-8")) - declarations(
            new.read_text(encoding="utf-8"),
        )

        if lost:
            findings.append(f"{old.relative_to(baseline)}: lost {sorted(lost)}")

    print(f"checked {scanned} Kotlin file(s) against {baseline}")

    for finding in findings:
        print(f"  {finding}")

    print(f"{len(findings)} file(s) lost a top-level declaration — confirm each was deliberate")

    # Never non-zero: a round that deletes something on purpose is normal, and a check that
    # fails the build for it would be switched off within two rounds.
    return 0


if __name__ == "__main__":
    sys.exit(main())
