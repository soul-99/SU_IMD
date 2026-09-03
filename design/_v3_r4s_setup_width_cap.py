#!/usr/bin/env python3
"""v3-r4s — the whole setup flow is a column on a tablet, not a display-wide page.

    "on wider/tablet displays they take up the whole screen can we make it not do that? like
     their dialog boxes we fixed earlier"

`_v3_r4s_flat_insets_and_width.py` capped the four steps that are drawn through `DialogContainer`.
It could not reach the three pages that are not: Permissions, the Shizuku page, and the closing
page, which build their own roots in `:app` and never touch that container.

So the cap goes around the `when` instead — one place, every page, including the four that already
have their own. Nesting an identical cap inside an identical cap changes nothing, and the
alternative is three more edits that have to be remembered when a fourth page is added.

## ⚠ On a phone this changes nothing at all

460.dp is wider than every phone in portrait, so the constraint never binds and not a pixel moves.
It bites on a tablet, on a foldable opened out, and in a large freeform window — which is where
the author saw a line of body text run the width of the display.

## ⚠ The number is repeated rather than shared, and that is the smaller evil

`DIALOG_MAX_WIDTH` is private to `Dialog.kt` in `:design-system`. Publishing it to give `:app` one
constant would make a layout number part of that module's API for one caller. A named constant
here, with a comment saying which value it must equal, is the cheaper of the two - and if they
ever disagree the setup flow is merely narrower or wider than the dialogs, not broken.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

CONTAINER = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

OPEN = """    when (page) {
        PERMISSIONS -> PermissionsPage("""

OPEN_NEW = """    // ⚠ **One cap for every page of the flow**, rather than three more edits in the pages that
    // build their own roots. The four steps drawn through DialogContainer already carry an
    // identical cap of their own; an identical constraint inside an identical constraint is a
    // no-op, and this way a page added later is capped without anyone remembering to do it.
    //
    // On a phone nothing moves: 460.dp is wider than the display, so the constraint never binds.
    Box(
        modifier = Modifier.fillMaxSize(),
        contentAlignment = Alignment.TopCenter,
    ) {
        Box(modifier = Modifier.widthIn(max = SETUP_MAX_WIDTH)) {
            when (page) {
                PERMISSIONS -> PermissionsPage("""

CLOSE = """            SetupCompletePage(
                modifier = modifier,
                onBack = onBack,
                onContinue = onContinue,
            )
        }
    }
}"""

CLOSE_NEW = """            SetupCompletePage(
                modifier = modifier,
                onBack = onBack,
                onContinue = onContinue,
            )
                }
            }
        }
    }
}"""

CONSTANT = """/**
 * How wide a setup page is allowed to get.
 *
 * ⚠ **Must equal `DIALOG_MAX_WIDTH` in `:design-system`'s Dialog.kt**, which is private to that
 * file. Repeated rather than published because making a layout number part of that module's API
 * for one caller costs more than this comment does; if the two ever disagree the setup flow is
 * merely a different width from the dialogs, not broken.
 */
private val SETUP_MAX_WIDTH = 460.dp

"""

IMPORTS = [
    "import androidx.compose.foundation.layout.Box",
    "import androidx.compose.foundation.layout.widthIn",
    "import androidx.compose.ui.Alignment",
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    # ⚠ The value is read out of the design system rather than trusted, so the comment above
    # SETUP_MAX_WIDTH cannot quietly become false.
    container = (ROOT / CONTAINER).read_text(encoding="utf-8")

    if "private val DIALOG_MAX_WIDTH = 460.dp" not in container:
        print(f"REFUSED: {CONTAINER}\n  DIALOG_MAX_WIDTH is not 460.dp any more")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in ((OPEN, OPEN_NEW), (CLOSE, CLOSE_NEW)):
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SCREEN}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    anchor = "/** The permissions page, which everybody starts on. */"

    if text.count(anchor) != 1:
        # Fall back to the first page constant's own declaration.
        anchor = "private const val PERMISSIONS = 0"

        if text.count(anchor) != 1:
            print(f"REFUSED: {SCREEN}\n  nowhere to declare SETUP_MAX_WIDTH")
            return 1

    text = text.replace(anchor, CONSTANT + anchor, 1)

    for statement in IMPORTS:
        text = add_import(text, statement)

    for token, expected in (
        ("private val SETUP_MAX_WIDTH = 460.dp", 1),
        ("widthIn(max = SETUP_MAX_WIDTH)", 1),
        ("Alignment.TopCenter", 1),
        # The braces balance. Counted rather than eyeballed: this edit adds two of each.
        ("{", text.count("}")),
    ):
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: every setup page is capped at 460.dp and centred")
    print("\nwrote 1 file(s), 3 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
