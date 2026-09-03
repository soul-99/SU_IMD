#!/usr/bin/env python3
"""v3-r4t — dialogs and setup pages get 580.dp instead of 460.dp.

    "increase initialisation screens and dialog widths a bit to say 580dp?"

Two constants, one in each module, and they are already documented as having to agree — see the
KDoc on `SETUP_MAX_WIDTH`. Both move together here so that documentation stays true.

⚠ **Still no change on a phone.** 580.dp is wider than 460.dp is wider than every phone in
portrait; the cap only ever binds on a tablet, a folded-out foldable or a large freeform window,
which is the only place either number is visible at all.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EDITS: list[tuple[str, str, str]] = [
    (
        "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt",
        "private val DIALOG_MAX_WIDTH = 460.dp",
        "private val DIALOG_MAX_WIDTH = 580.dp",
    ),
    (
        "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt",
        "private val SETUP_MAX_WIDTH = 460.dp",
        "private val SETUP_MAX_WIDTH = 580.dp",
    ),
    (
        "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt",
        "    // On a phone nothing moves: 460.dp is wider than the display, so the constraint never binds.",
        "    // On a phone nothing moves: 580.dp is wider than the display, so the constraint never binds.",
    ),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {relative}\n  {old.strip()[:60]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    # ⚠ The two must agree, and this is what says so rather than the comment alone.
    for relative, token in (
        ("design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt", "460.dp"),
        ("app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt", "460.dp"),
    ):
        if token in staged[relative]:
            print(f"REFUSED: {relative}\n  a 460.dp survives the edit")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print("  ok        both width caps are 580.dp")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
