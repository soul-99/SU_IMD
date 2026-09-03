#!/usr/bin/env python3
"""v3-r4s — a flat setup step keeps out of the status bar, and stops filling a tablet.

    "the new initialisation pages take up the position of status bar position so unable to
     clearly read the text there"
    "on wider/tablet displays they take up the whole screen can we make it not do that? like
     their dialog boxes we fixed earlier"

Both are the same omission. The flat branch added in r4r was:

    Surface(modifier = modifier.fillMaxSize(), ...)

- no insets and no width cap, because it was written as "the body, with none of the dialog
  around it" and the dialog is where both of those lived.

## ⚠ The surface still fills; only its content is inset

`windowInsetsPadding` goes on a `Box` *inside* the `Surface`, not on the `Surface` itself. Put it
outside and the page's own background stops at the status bar, leaving a strip of whatever is
behind it - which on a setup step is nothing at all. Inside, the colour reaches the edges and the
text starts below the clock.

`safeDrawing` rather than `statusBars`: it covers the navigation bar and the cutout too, and the
screenshots show the footer buttons sitting on the gesture bar as well as the title under the
clock.

## ⚠ The width cap is the one the dialogs already use

`DIALOG_MAX_WIDTH`, reached through the existing `maxWidth` parameter, and centred by the same
`Box` the dialog branch centres with. A flat page on a tablet is now the same comfortable
phone-shaped column the dialogs became - the author's *"like their dialog boxes we fixed
earlier"* - rather than a line of text the width of the display.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTAINER = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

OLD = """    if (flat) {
        Surface(
            modifier = modifier.fillMaxSize(),
            color = containerColor,
            tonalElevation = tonalElevation,
            content = content,
        )

        return
    }"""

NEW = """    if (flat) {
        // ⚠ **Centred and capped, exactly as the dialog branch below.** Without this a setup
        // step was the width of the display, so on a tablet a line of body text ran the whole
        // way across - the author's "on wider/tablet displays they take up the whole screen".
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.TopCenter,
        ) {
            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize(),
                color = containerColor,
                tonalElevation = tonalElevation,
            ) {
                // ⚠ **The insets go here, inside the Surface, and that is deliberate.** On the
                // Surface itself the page's own background would stop at the status bar and
                // leave a strip of nothing above it. Inside, the colour reaches the edges and
                // the content starts below the clock - which is the author's "the new
                // initialisation pages take up the position of status bar position so unable to
                // clearly read the text there".
                //
                // safeDrawing rather than statusBars: the screenshots show the footer buttons
                // on the gesture bar as well as the title under the clock, and it covers the
                // cutout too.
                Box(modifier = Modifier.windowInsetsPadding(WindowInsets.safeDrawing)) {
                    content()
                }
            }
        }

        return
    }"""

IMPORTS = [
    "import androidx.compose.foundation.layout.WindowInsets",
    "import androidx.compose.foundation.layout.safeDrawing",
    "import androidx.compose.foundation.layout.windowInsetsPadding",
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
    path = ROOT / CONTAINER

    if not path.is_file():
        print(f"REFUSED: missing {CONTAINER}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {CONTAINER}\n  the flat branch matched {found} time(s), expected 1")
        return 1

    text = text.replace(OLD, NEW, 1)

    for statement in IMPORTS:
        text = add_import(text, statement)

    for token, expected in (
        ("windowInsetsPadding(WindowInsets.safeDrawing)", 1),
        # ⚠ **Three, and the two that were already there were counted from the file, not
        # assumed.** The dialog branch caps its width twice - once for the compact form and
        # once for the full one - so the flat branch's own cap is the third. A first draft of
        # this script said 2 and was refused, which is the assertion doing its job.
        ("widthIn(max = maxWidth)", 3),
        ("Alignment.TopCenter", 1),
        # The dialog branches below are untouched.
        ("if (compact) {", 1),
        ("DIALOG_MAX_WIDTH", 2),
    ):
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {CONTAINER}\n  {token!r} occurs {found} time(s) after the edit, "
                f"expected {expected}",
            )
            return 1

    for statement in ("import androidx.compose.foundation.layout.widthIn",
                      "import androidx.compose.ui.Alignment",
                      "import androidx.compose.foundation.layout.Box"):
        if statement not in text:
            print(f"REFUSED: {CONTAINER}\n  {statement!r} is absent")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {CONTAINER}  :: flat pages are inset and capped")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
