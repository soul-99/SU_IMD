#!/usr/bin/env python3
"""v3-r4q — the IMD+ switch inside its own dialog explains why it will not move.

    "i checked again when auto hide settings toggle is clicked(i mean inside its dialog box) it
     does not display popup"
    "do one thing display the same dialog we have already 'Please setup Auto hide settings first'
     one"

## The defect

`AutoHideSwitchRow` in `AutoHidePage` is `enabled = !blockedByHide` and nothing more. With the
requirements unmet the row is therefore **live**: the press calls `onUpdateAutoHideEnabled(true)`,
which is stored - and `autoHideSwitchOn` reads `autoHideEnabled && requirements.satisfied`, so the
switch springs straight back with nothing said. A control that moves and returns tells the user
less than one that refuses.

⚠ **The settings list already had this right.** `SettingsScreen` raises
[AutoHideSetupNoticeDialog] from the IMD+ row for exactly this case; only the switch *inside* the
dialog was left silent. So this reuses that dialog and its existing, already-translated string
rather than adding a second sentence that says the same thing.

## ⚠ Still pressable, not disabled

The same rule the settings manager's `TargetRow` and the Shizuku master switch follow: a disabled
Switch swallows the press inside its own bounds, and a control that does nothing at all reads as
a broken app. `onBlocked` intercepts the press instead.

⚠ **`blockedByHide` keeps its own arm and stays disabled.** That case is not "set this up first",
it is "not while a hide is outstanding", and its subtitle already says so - routing it to a
dialog about setup would be a wrong answer, not a missing one.

## ⚠ Its twin is left alone, deliberately

`AutoUnhidePage` uses the same row and has the same silence when its requirements are unmet. The
author reported the IMD+ one and named the dialog he wanted for it; the auto-unhide switch is
mentioned in the round's notes rather than changed here without being asked.

`onBlocked` defaults to null, so `AutoUnhidePage` and `DiagnosticsDialog` - the other two callers
of this row - are untouched.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHidePage.kt"

EDITS: list[tuple[str, str]] = [
    # 1. The row learns to refuse.
    (
        """internal fun AutoHideSwitchRow(
    modifier: Modifier = Modifier,
    title: String,
    checked: Boolean,
    enabled: Boolean,
    subtitle: String,
    onCheckedChange: (Boolean) -> Unit,
) {""",
        """internal fun AutoHideSwitchRow(
    modifier: Modifier = Modifier,
    title: String,
    checked: Boolean,
    enabled: Boolean,
    subtitle: String,
    /**
     * Raised instead of moving the switch, when it would only spring back.
     *
     * ⚠ **The row stays [enabled] while this is set.** A disabled Switch swallows the press
     * inside its own bounds, and a master control that does nothing at all when tapped reads as
     * a broken app - the same argument the settings manager's `TargetRow` and the Shizuku
     * master switch both make.
     *
     * Null for the two callers that have nothing to explain.
     */
    onBlocked: (() -> Unit)? = null,
    onCheckedChange: (Boolean) -> Unit,
) {""",
    ),
    (
        """    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) { onCheckedChange(!checked) }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {""",
        """    Row(
        modifier = modifier
            .fillMaxWidth()
            .clickable(enabled = enabled) {
                if (onBlocked != null) onBlocked() else onCheckedChange(!checked)
            }
            .padding(horizontal = 10.dp, vertical = 10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {""",
    ),
    (
        """        Switch(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)""",
        """        // Wrapped rather than disabled when blocked, so the press reaches the row's own
        // click above instead of dying inside the Switch.
        if (onBlocked == null) {
            Switch(checked = checked, enabled = enabled, onCheckedChange = onCheckedChange)
        } else {
            Box(modifier = Modifier.clickable(onClick = onBlocked)) {
                Switch(checked = checked, enabled = false, onCheckedChange = null)
            }
        }""",
    ),
    # 2. The page raises the dialog the settings list already raises.
    (
        """            enabled = !blockedByHide,
            subtitle = when {""",
        """            enabled = !blockedByHide,
            // ⚠ **Only for the unmet-requirements case.** `blockedByHide` keeps its own arm
            // and stays disabled: that is "not while a hide is outstanding", which its subtitle
            // already says, and answering it with a dialog about setup would be wrong rather
            // than merely missing.
            onBlocked = if (!blockedByHide && !requirements.satisfied) {
                { showSetupNotice = true }
            } else {
                null
            },
            subtitle = when {""",
    ),
    (
        """    val blockedByHide = userData.autoHideBlockedByHide""",
        """    val blockedByHide = userData.autoHideBlockedByHide

    // The author's report: the switch inside this dialog moved and sprang back with nothing
    // said, while the IMD+ row on the settings list has raised this dialog for the same case
    // all along. Same dialog, same string - not a second sentence saying the same thing.
    var showSetupNotice by rememberSaveable { mutableStateOf(false) }

    if (showSetupNotice) {
        AutoHideSetupNoticeDialog(onDismissRequest = { showSetupNotice = false })
    }""",
    ),
]

AFTER = [
    # Six: the declaration, the two in the row's click, the null check, the Box's onClick, and
    # the call site. The first draft counted a KDoc mention that was never written.
    ("onBlocked", 6),
    ("showSetupNotice", 4),
    ("AutoHideSetupNoticeDialog(", 1),
    # The other two callers of the row pass nothing, so the row must keep its default.
    ("onBlocked: (() -> Unit)? = null,", 1),
]

NEEDED = [
    "import androidx.compose.foundation.layout.Box",
    "import androidx.compose.runtime.getValue",
    "import androidx.compose.runtime.mutableStateOf",
    "import androidx.compose.runtime.saveable.rememberSaveable",
    "import androidx.compose.runtime.setValue",
    "import androidx.compose.foundation.clickable",
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

    for statement in NEEDED:
        if statement not in text:
            print(f"REFUSED: {PAGE}\n  {statement!r} is absent")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: the IMD+ switch raises the setup notice instead of springing back")
    print("  ok        blockedByHide keeps its own disabled arm")
    print("  ok        AutoUnhidePage and DiagnosticsDialog untouched (onBlocked defaults to null)")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
