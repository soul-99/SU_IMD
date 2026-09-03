#!/usr/bin/env python3
"""v3-r4r — the import `check_symbol_imports` caught in the new steps file.

    SetupSteps.kt:260  isShizukuConfigured  (declared in com.android.geto.domain.model)

`overlayStepApplies` reads three things off `UserData`. Two of them - `shizukuForkMode` and
`manageShizukuEffective` - were imported; `isShizukuConfigured` is an extension property in the
same package as the others and was not, so it would have been an unresolved reference in a module
this sandbox cannot compile.

⚠ **This is the check earning its place.** Four zips have historically reached the author without
compiling, and a missing import on an extension property is exactly the shape that survives a
reading: the name is spelled correctly, it is used correctly, and it is simply not in scope.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SetupSteps.kt"

ANCHOR = "import com.android.geto.domain.model.accessibilityManageable"

NEW = """import com.android.geto.domain.model.accessibilityManageable
import com.android.geto.domain.model.isShizukuConfigured"""


def main() -> int:
    path = ROOT / STEPS

    if not path.is_file():
        print(f"REFUSED: missing {STEPS}")
        return 1

    text = path.read_text(encoding="utf-8")

    if "import com.android.geto.domain.model.isShizukuConfigured" in text:
        print(f"REFUSED: {STEPS}\n  the import is already there")
        return 1

    found = text.count(ANCHOR)

    if found != 1:
        print(f"REFUSED: {STEPS}\n  the anchor matched {found} time(s), expected 1")
        return 1

    if "userData.isShizukuConfigured" not in text:
        print(f"REFUSED: {STEPS}\n  nothing here uses isShizukuConfigured")
        return 1

    path.write_text(text.replace(ANCHOR, NEW, 1), encoding="utf-8")

    print(f"  ok        {STEPS}  :: isShizukuConfigured imported")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
