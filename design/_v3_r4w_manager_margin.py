#!/usr/bin/env python3
"""v3-r4w — the settings manager keeps more room at its sides on a phone.

    "also narrow the settings manager dialog width in phones i know that hide settings button will
     get wraped it's ok currently it leaves too les space on either sides"

## ⚠ It is the margin that changes, not a width

Every dialog in the app fills the screen minus **16.dp** each side, and stops at 580.dp on
anything wide enough for that to bite. On a phone the cap never bites, so the only number that
decides how much room is left beside a dialog is that margin. Setting a width here instead would
have been a second rule fighting the cap on a tablet — where the author has not complained and
where nothing should move.

So `DialogContainer` takes the margin as a parameter, defaulting to what every dialog has always
had, and the settings manager asks for **32.dp**. On a 360dp phone that is 296dp of dialog instead
of 328dp.

⚠ **The button row will wrap, and he has said that is fine** — *"i know that hide settings button
will get wraped it's ok"*. It is recorded here because it is the visible cost of the change and
the first thing a later reader would try to "fix".

⚠ **Both padded branches take it.** The container has two — one that dismisses on an outside tap
and one that does not — and changing the number in one of them would give the same dialog two
different widths depending on whether it happened to be dismissible.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTAINER = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

MANAGER = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

EDITS: list[tuple[str, str, str]] = [
    (
        CONTAINER,
        "private val DIALOG_MAX_WIDTH = 580.dp",
        """private val DIALOG_MAX_WIDTH = 580.dp

/**
 * How much room is left beside a dialog.
 *
 * ⚠ **On a phone this, not [DIALOG_MAX_WIDTH], is what decides a dialog's width.** The cap only
 * bites on a screen wider than 580.dp, so everywhere else a dialog is the screen minus twice
 * this.
 */
private val DIALOG_MARGIN = 16.dp""",
    ),
    (
        CONTAINER,
        "    maxWidth: Dp = DIALOG_MAX_WIDTH,",
        """    maxWidth: Dp = DIALOG_MAX_WIDTH,
    /**
     * How much room to leave at each side.
     *
     * The default is what every dialog in the app has always had. The settings manager asks for
     * more, at the author's request — it opens over somebody else's app and was reaching almost
     * to the edges of a phone.
     */
    horizontalMargin: Dp = DIALOG_MARGIN,""",
    ),
    (
        CONTAINER,
        """                Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 24.dp)
            } else {
                Modifier
                    .fillMaxSize()
                    .pointerInput(onDismissRequest) {
                        detectTapGestures { onDismissRequest() }
                    }
                    .padding(horizontal = 16.dp, vertical = 24.dp)""",
        """                Modifier
                    .fillMaxSize()
                    .padding(horizontal = horizontalMargin, vertical = 24.dp)
            } else {
                Modifier
                    .fillMaxSize()
                    .pointerInput(onDismissRequest) {
                        detectTapGestures { onDismissRequest() }
                    }
                    // ⚠ Both branches, always. They differ only in whether a tap beside the
                    // dialog closes it; a margin applied to one of them would give the same
                    // dialog two widths depending on whether it happened to be dismissible.
                    .padding(horizontal = horizontalMargin, vertical = 24.dp)""",
    ),
    (
        MANAGER,
        """        compact = false,
        onDismissRequest = onDismissRequest,""",
        """        compact = false,
        // ⚠ **Twice the usual margin, at the author's request.** This dialog was reaching
        // almost to the edges of a phone — *"currently it leaves too les space on either
        // sides"* — and it opens over somebody else's app, where a card that nearly fills the
        // screen reads as having replaced it rather than as sitting on top of it.
        //
        // The button row wraps at this width. He has said that is fine: *"i know that hide
        // settings button will get wraped it's ok"*. Recorded because it is the visible cost of
        // this line and the first thing a later reader would try to undo.
        horizontalMargin = 32.dp,
        onDismissRequest = onDismissRequest,""",
    ),
]

AFTER = [
    (CONTAINER, "private val DIALOG_MARGIN = 16.dp", 1),
    (CONTAINER, "horizontalMargin: Dp = DIALOG_MARGIN,", 1),
    (CONTAINER, "padding(horizontal = horizontalMargin, vertical = 24.dp)", 2),
    # ⚠ No hardcoded side margin survives in the container.
    (CONTAINER, "padding(horizontal = 16.dp, vertical = 24.dp)", 0),
    (MANAGER, "horizontalMargin = 32.dp,", 1),
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
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ **The manager must be on the container's own width path for this to reach it.** It kept
    # the platform width until r4k, where `compact = false` put it here; passing a margin to a
    # dialog the platform is still sizing would do nothing at all.
    if "compact = false," not in staged[MANAGER]:
        print(f"REFUSED: {MANAGER}\n  this dialog is not on DialogContainer's own width path")
        return 1

    if "import androidx.compose.ui.unit.Dp" not in staged[CONTAINER]:
        print(f"REFUSED: {CONTAINER}\n  Dp is not imported")
        return 1

    if "import androidx.compose.ui.unit.dp" not in staged[MANAGER]:
        print(f"REFUSED: {MANAGER}\n  dp is not imported")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {CONTAINER}  :: the side margin is a parameter, default unchanged")
    print(f"  ok        {MANAGER}  :: 32.dp each side on a phone")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
