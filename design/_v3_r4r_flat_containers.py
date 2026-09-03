#!/usr/bin/env python3
"""v3-r4r — the dialog containers learn to be a page.

    "instead of making new pages for the dialogs we already have just use those dialogs with
     Skip and Next buttons below"
    "flat - no scrim, filling the page ... but put skip button on left and next button as it is
     on right"

The first half of that: the two containers every configuration dialog is built on gain a **flat**
mode. Nothing about any dialog's body changes - `flat` only decides whether the body is wrapped
in a `Dialog` window with a scrim, or drawn straight into the page it is on.

## ⚠ Why a mode on the container rather than a copy of the body

Extracting each dialog's contents into a page composable was the alternative, and it means two
call sites for one list of switches - which is the drift this project has spent three rounds
removing from the Shizuku page. One composable, one body, one place a row can be added.

## What flat changes, and only this

* **`DialogContainer`**: no `Dialog`, no scrim, no card - a `Surface` filling its parent. A third
  early-return branch beside `compact`, the same shape as that one.
* **`SettingsPage`**: no outer padding (a page reaches its edges), no back arrow (there is
  nothing behind a setup step to go back to), and the footer arranged **SpaceBetween** rather
  than **End**, which is what puts Skip at the left and Next at the right.

⚠ **`shape` is deliberately ignored in the flat branch.** A surface that fills the screen has no
corners to round, and rounding them would draw the page's own background through four notches.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTAINER = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsPage.kt"

EDITS: list[tuple[str, str, str]] = [
    # ---- DialogContainer ----
    (
        CONTAINER,
        """    fullScreen: Boolean = false,""",
        """    fullScreen: Boolean = false,
    /**
     * Draw the body straight into the page instead of into a dialog window.
     *
     * ⚠ **For the setup flow, and nothing else so far.** A configuration step during
     * initialisation is a page the user is walking through, not a popup over something they
     * were already doing - so there is no scrim, no card and no outside to tap. The body is the
     * same composable either way, which is the whole reason this is a flag rather than a second
     * copy of each dialog.
     *
     * [shape] is ignored here on purpose: a surface that fills the screen has no corners, and
     * rounding them would show the page behind through four notches.
     */
    flat: Boolean = false,""",
    ),
    (
        CONTAINER,
        """    if (compact) {
        Dialog(""",
        """    // ⚠ **Before every other branch, because it is the one that is not a dialog at all.**
    // No window, no scrim, no dismissal: a setup step ends by pressing Skip or Next, and both
    // of those are the caller's business rather than this container's.
    if (flat) {
        Surface(
            modifier = modifier.fillMaxSize(),
            color = containerColor,
            tonalElevation = tonalElevation,
            content = content,
        )

        return
    }

    if (compact) {
        Dialog(""",
    ),
    # ---- SettingsPage ----
    (
        PAGE,
        """    scrollableBody: Boolean = true,
    onDismissRequest: () -> Unit,""",
        """    scrollableBody: Boolean = true,
    /**
     * Draw this as a page in the setup flow rather than as a dialog over the settings list.
     *
     * Three things follow from it and nothing else does: the outer margin goes, because a page
     * reaches its edges; the back arrow goes, because there is nothing behind a setup step to
     * go back to; and the footer is arranged **SpaceBetween** instead of **End**, which is what
     * puts the author's Skip at the left and Next at the right.
     */
    flat: Boolean = false,
    onDismissRequest: () -> Unit,""",
    ),
    (
        PAGE,
        """    DialogContainer(
        modifier = modifier
            .fillMaxSize()
            .padding(start = 8.dp, end = 8.dp, top = 40.dp, bottom = 8.dp),
        shape = MaterialTheme.shapes.extraLarge,
        fullScreen = true,
        onDismissRequest = onDismissRequest,
    ) {""",
        """    DialogContainer(
        // Flat reaches the edges: the margin above is the gap that says "this is on top of
        // something", and during setup there is nothing underneath for it to say that about.
        modifier = if (flat) {
            modifier.fillMaxSize()
        } else {
            modifier
                .fillMaxSize()
                .padding(start = 8.dp, end = 8.dp, top = 40.dp, bottom = 8.dp)
        },
        shape = MaterialTheme.shapes.extraLarge,
        fullScreen = true,
        flat = flat,
        onDismissRequest = onDismissRequest,
    ) {""",
    ),
    (
        PAGE,
        """                IconButton(onClick = onDismissRequest) {
                    Icon(
                        modifier = Modifier.size(22.dp),
                        imageVector = GetoIcons.Back,
                        contentDescription = stringResource(R.string.page_back),
                    )
                }

                Spacer(modifier = Modifier.width(4.dp))""",
        """                // No way back out of a setup step - Skip is the way past it, and it is in
                // the footer with Next.
                if (!flat) {
                    IconButton(onClick = onDismissRequest) {
                        Icon(
                            modifier = Modifier.size(22.dp),
                            imageVector = GetoIcons.Back,
                            contentDescription = stringResource(R.string.page_back),
                        )
                    }
                }

                Spacer(modifier = Modifier.width(4.dp))""",
    ),
    (
        PAGE,
        """                horizontalArrangement = Arrangement.End,
                verticalAlignment = Alignment.CenterVertically,
                content = actions,""",
        """                // ⚠ **SpaceBetween is what puts Skip on the left.** With two actions the
                // first goes to one edge and the second to the other, which is the author's
                // *"skip button on left and next button as it is on right"* - no alignment
                // modifiers on the buttons themselves, so the caller passes them in reading
                // order and the row does the rest.
                horizontalArrangement = if (flat) {
                    Arrangement.SpaceBetween
                } else {
                    Arrangement.End
                },
                verticalAlignment = Alignment.CenterVertically,
                content = actions,""",
    ),
]

AFTER = [
    (CONTAINER, "flat: Boolean = false,", 1),
    (CONTAINER, "if (flat) {", 1),
    # The two branches that were already here are untouched.
    (CONTAINER, "if (compact) {", 1),
    # Two, both pre-existing: the Box modifier branch and the Surface one below it. Counted
    # from the file rather than assumed.
    (CONTAINER, "if (fullScreen) {", 2),
    (PAGE, "flat: Boolean = false,", 1),
    (PAGE, "flat = flat,", 1),
    (PAGE, "if (!flat) {", 1),
    (PAGE, "Arrangement.SpaceBetween", 1),
    (PAGE, "Arrangement.End", 1),
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
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # Everything the flat branch reaches for is already imported by the dialog branches.
    for statement in (
        "import androidx.compose.material3.Surface",
        "import androidx.compose.foundation.layout.fillMaxSize",
    ):
        if statement not in staged[CONTAINER]:
            print(f"REFUSED: {CONTAINER}\n  {statement!r} is absent")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {CONTAINER}  :: flat draws the body into the page")
    print(f"  ok        {PAGE}  :: no margin, no back arrow, Skip left and Next right")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
