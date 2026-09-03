#!/usr/bin/env python3
"""v3-r4r — the two SettingsPage dialogs can be setup steps.

The companion to `_v3_r4r_setup_steps_lists.py`, for the two built on `SettingsPage` rather than
on `DialogContainer` directly. Same parameter, same meaning: `onSkip` null is Settings, non-null
is a step of the setup flow.

`SettingsPage` already does the flat drawing and the Skip-left arrangement, so these two only have
to pass `flat` and emit two actions instead of one.

## ⚠ Skip means something different on the auto unhide step, and the author chose it

Every other step holds a draft, so Skip there is simply *write nothing*. `AutoUnhidePage` has no
draft - each switch writes as it is moved, and its permission grants are live acts that cannot be
taken back by a button. Skip and Next would therefore have been the same button twice.

His answer: **Skip turns auto unhide off.** So it writes `autoUnhideEnabled = false` and moves on,
which gives the button an honest meaning - "I do not want this" - rather than making it a second
Next. Anything else the page did on the way through (a permission granted, a trigger ticked) is
left alone, because none of that is auto unhide being *on*.

## ⚠ Settings to hide keeps Save's exact body

Next runs `onUpdateSettingsToHide(draft)`, `onUpdateRestoreWirelessDebugging(restoreWirelessDraft)`
and `onDismissRequest()` - the three lines Save already runs, in that order. Written as one
lambda used by both labels so the two cannot come apart.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"

UNHIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhidePage.kt"

SKIP_DOC = '''    /**
     * Non-null turns this into a step of the setup flow.
     *
     * The page is drawn flat rather than as a dialog, and its footer carries Skip at the left
     * beside Next at the right - see `SettingsPage`, which does both.
     */
    onSkip: (() -> Unit)? = null,
'''

EDITS: list[tuple[str, str, str]] = [
    # ---------------- Settings to hide ----------------
    (
        HIDE,
        """internal fun SettingsToHideDialog(""",
        """fun SettingsToHideDialog(""",
    ),
    (
        HIDE,
        """    stepTitle: String? = null,
    overlayBlockedPaths: List<String>?,""",
        SKIP_DOC + """    stepTitle: String? = null,
    overlayBlockedPaths: List<String>?,""",
    ),
    (
        HIDE,
        """        onDismissRequest = onDismissRequest,
        actions = {
            TextButton(
                onClick = {
                    onUpdateSettingsToHide(draft)

                    onUpdateRestoreWirelessDebugging(restoreWirelessDraft)

                    onDismissRequest()
                },
            ) {
                Text(text = stringResource(R.string.save))
            }
        },""",
        """        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // ⚠ **One lambda, two labels.** Save and Next do the same three things in the same
            // order, and writing them once is what stops "Next" from quietly becoming a
            // different button from "Save".
            val commit = {
                onUpdateSettingsToHide(draft)

                onUpdateRestoreWirelessDebugging(restoreWirelessDraft)

                onDismissRequest()
            }

            if (onSkip != null) {
                TextButton(onClick = onSkip) {
                    Text(text = stringResource(commonR.string.skip))
                }
            }

            TextButton(onClick = commit) {
                Text(
                    text = stringResource(
                        if (onSkip != null) commonR.string.next else R.string.save,
                    ),
                )
            }
        },""",
    ),
    # ---------------- Auto unhide ----------------
    (
        UNHIDE,
        """internal fun AutoUnhidePage(""",
        """fun AutoUnhidePage(""",
    ),
    (
        UNHIDE,
        """    stepTitle: String? = null,
    onDismissRequest: () -> Unit,""",
        SKIP_DOC + """    stepTitle: String? = null,
    onDismissRequest: () -> Unit,""",
    ),
    (
        UNHIDE,
        """        title = stepTitle ?: stringResource(R.string.auto_unhide_title),
        onDismissRequest = onDismissRequest,
    ) {""",
        """        title = stepTitle ?: stringResource(R.string.auto_unhide_title),
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
        actions = {
            // ⚠ **Skip switches auto unhide off here, and that is the author's decision.**
            // This page holds no draft - every control on it writes as it is moved, and its
            // permission grants cannot be taken back by a button - so a Skip that only advanced
            // would have been a second Next. Turning the feature off is the one thing "I do not
            // want this" can honestly mean.
            //
            // Only the master switch. A permission granted or a trigger ticked on the way
            // through is not auto unhide being *on*, and is left exactly as it was.
            if (onSkip != null) {
                TextButton(
                    onClick = {
                        onUpdateAutoUnhideEnabled(false)

                        onSkip()
                    },
                ) {
                    Text(text = stringResource(commonR.string.skip))
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(commonR.string.next))
                }
            }
        },
    ) {""",
    ),
]

IMPORTS = [
    (HIDE, "import androidx.compose.material3.TextButton"),
    (HIDE, "import com.android.geto.common.R as commonR"),
    (UNHIDE, "import androidx.compose.material3.TextButton"),
    (UNHIDE, "import com.android.geto.common.R as commonR"),
]

AFTER = [
    (HIDE, "internal fun SettingsToHideDialog(", 0),
    (HIDE, "onSkip", 5),
    (HIDE, "commonR.string.skip", 1),
    (HIDE, "commonR.string.next", 1),
    (HIDE, "R.string.save", 1),
    (UNHIDE, "internal fun AutoUnhidePage(", 0),
    # Four: the declaration, the flat argument, the guard, and the call inside Skip.
    (UNHIDE, "onSkip", 4),
    (UNHIDE, "onUpdateAutoUnhideEnabled(false)", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    # An aliased import sorts to the end of the block, where the file already keeps them.
    if " as " in statement:
        indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

        if not indices:
            raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

        lines.insert(indices[-1] + 1, statement + "\n")

        return "".join(lines)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


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

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {HIDE}  :: public, Skip beside Save renamed Next")
    print(f"  ok        {UNHIDE}  :: public, Skip turns auto unhide off")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
