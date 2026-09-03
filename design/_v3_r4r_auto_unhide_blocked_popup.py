#!/usr/bin/env python3
"""v3-r4r — the auto unhide switch inside its own page explains why it will not move.

    "do those also will test after"

The twin of `_v3_r4q_auto_hide_blocked_popup.py`, which r4q deliberately left alone because the
author had named a dialog for the IMD+ switch and not for this one. He has now asked for it.

## The same defect, exactly

`AutoUnhidePage` draws `AutoHideSwitchRow` with `enabled = true` and nothing else, so with the
requirements unmet the press is live: it stores `autoUnhideEnabled = true`, and
`autoUnhideSwitchOn` reads `autoUnhideEnabled && requirements.satisfied`, so the switch springs
back with nothing said.

## ⚠ Its own dialog, not IMD+'s

`AutoUnhideBlockedDialog` already exists for this, and already distinguishes the two refusals it
has to make - a permission granted outside the app, or a trigger nobody has ticked. Its
`permissionsMissing` flag is read at the moment it is *drawn* rather than when it was raised,
because the page behind it polls every second and a permission granted while the pop-up is up
would otherwise leave it naming a permission that is now there.

Reusing IMD+'s "Please setup Auto hide settings first" here would have been a sentence about a
different feature.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhidePage.kt"

EDITS: list[tuple[str, str]] = [
    (
        """        AutoHideSwitchRow(
            title = stringResource(R.string.auto_unhide_switch),
            checked = autoUnhideSwitchOn(userData = userData, requirements = requirements),
            enabled = true,""",
        """        AutoHideSwitchRow(
            title = stringResource(R.string.auto_unhide_switch),
            checked = autoUnhideSwitchOn(userData = userData, requirements = requirements),
            enabled = true,
            // ⚠ **The same silence the IMD+ switch had until r4q**, reported and fixed there,
            // left here until the author asked for it too. With the requirements unmet this row
            // was live: the press stored `autoUnhideEnabled = true` and the switch sprang back,
            // because autoUnhideSwitchOn reads the requirements as well as the stored answer.
            onBlocked = if (!requirements.satisfied) {
                { showBlocked = true }
            } else {
                null
            },""",
    ),
    (
        """    val context = LocalContext.current

    val packageName = remember(context) { context.packageName }""",
        """    val context = LocalContext.current

    // Raised by the master switch when it would only spring back. Its own dialog rather than
    // IMD+'s: that one's sentence is about a different feature, and this one already knows how
    // to tell a missing permission from an unticked trigger.
    var showBlocked by rememberSaveable { mutableStateOf(false) }

    if (showBlocked) {
        AutoUnhideBlockedDialog(
            // ⚠ Read as it is drawn, not as it was raised: the page behind polls every second,
            // so a permission granted while this is up must not leave it naming that permission.
            permissionsMissing = !requirements.permissionsSatisfied,
            onDismissRequest = { showBlocked = false },
        )
    }

    val packageName = remember(context) { context.packageName }""",
    ),
]

AFTER = [
    ("showBlocked", 4),
    ("AutoUnhideBlockedDialog(", 1),
    ("onBlocked = if (!requirements.satisfied)", 1),
]

NEEDED = [
    "import androidx.compose.runtime.getValue",
    "import androidx.compose.runtime.mutableStateOf",
    "import androidx.compose.runtime.saveable.rememberSaveable",
    "import androidx.compose.runtime.setValue",
]


def main() -> int:
    path = ROOT / PAGE

    if not path.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {PAGE}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {PAGE}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # The delegate imports the new state needs. Added rather than asserted: this page had no
    # local state before, so it had no reason to carry them - and check17_delegates is the
    # audit that catches exactly this omission.
    lines = text.splitlines(keepends=True)

    for statement in NEEDED:
        if statement + "\n" in text:
            continue

        indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

        target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

        lines.insert(target, statement + "\n")

    text = "".join(lines)

    for statement in NEEDED:
        if statement not in text:
            print(f"REFUSED: {PAGE}\n  {statement!r} is absent")
            return 1

    # The dialog it raises, and the property it reads, are both in the same package.
    dialogs = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhideDialogs.kt"

    if "fun AutoUnhideBlockedDialog(" not in dialogs.read_text(encoding="utf-8"):
        print("REFUSED: AutoUnhideBlockedDialog is not declared where expected")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: the auto unhide switch raises its own blocked dialog")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
