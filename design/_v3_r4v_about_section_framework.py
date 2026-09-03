#!/usr/bin/env python3
"""v3-r4v — `AboutSection` is told the unhiding framework, because it is what opens Help.

`check_local_scope` caught this before the author's compiler did:

    SettingsScreen.kt:2808  userData  used in AboutSection, declared on Success

`_v3_r4v_location_trees.py` handed the framework to `SetupHelpDialog` at its call site, and that
call site turned out to be inside **`AboutSection`** — a private composable that takes a
`DiagnosticsHandle` and nothing else. `userData` is not in scope there, so the line as written was
a build error.

The fix is a parameter, not a wider `userData`: this section needs one enum for one path on one
page, and handing it the whole preferences object to reach that would make every future reader of
it wonder what else it depends on.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str]] = [
    (
        """private fun AboutSection(
    modifier: Modifier = Modifier,
    diagnostics: DiagnosticsHandle,
) {""",
        """private fun AboutSection(
    modifier: Modifier = Modifier,
    /**
     * Only for the Help page this section opens: two of the paths on it name a row whose label
     * follows this setting — see `SetupHelpContent`.
     *
     * One enum rather than the whole of `userData`, which this section otherwise has no use for
     * and should not start looking like it depends on.
     */
    unhidingFramework: UnhidingFramework,
    diagnostics: DiagnosticsHandle,
) {""",
    ),
    (
        "        AboutSection(diagnostics = diagnostics)",
        "        AboutSection(\n"
        "            unhidingFramework = userData.unhidingFramework,\n"
        "            diagnostics = diagnostics,\n"
        "        )",
    ),
    (
        """        SetupHelpDialog(
            unhidingFramework = userData.unhidingFramework,
            onDismissRequest = { showHelp = false },
        )""",
        """        SetupHelpDialog(
            unhidingFramework = unhidingFramework,
            onDismissRequest = { showHelp = false },
        )""",
    ),
]

AFTER = [
    # Three, counted from the file: two dialogs already read it this way, and the AboutSection
    # call added here is the third. The one inside AboutSection becomes the parameter instead.
    ("unhidingFramework = userData.unhidingFramework,", 3),
    ("unhidingFramework = unhidingFramework,", 1),
    ("unhidingFramework: UnhidingFramework,", 1),
]


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {SCREEN}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    if "import com.android.geto.domain.model.UnhidingFramework" not in text:
        print(f"REFUSED: {SCREEN}\n  UnhidingFramework is not imported")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: AboutSection takes the framework it needs for Help")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
