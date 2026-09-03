#!/usr/bin/env python3
"""v3-r4y — the settings manager is a small card again, on every screen.

    "the IMD setings manager is too wide for my current taste on phones as well as tablets can we
     shrink width? … also i tried on my s22 ultra it looks too big all aspects(height, width) and
     ui elements can it be fixed?"

## ⚠ The margin was the wrong lever, and r4w reached for it

r4w widened the side margin to 32.dp, which narrows a dialog **in proportion to the screen** — so
it did nothing at all on the tablet, where the 580.dp cap is what decides the width, and not
enough on a large phone. The author's screenshots show exactly that: still wide on the razr,
enormous on the tablet.

A **cap of its own** is the lever that answers all three at once. At `MANAGER_MAX_WIDTH` this
dialog is the same small card on a folded razr, an S22 Ultra and a tablet, because on every one of
them the cap is what binds rather than the screen.

⚠ **The margin stays**, reduced to 24.dp, and it is not redundant: on a narrow or split-screen
window the cap never binds and the margin is again the only thing keeping the card off the edges.

## ⚠ "Too big in all aspects" is a second complaint and needs a second answer

A narrower card does not make its contents smaller; on the S22 Ultra the type and the switches
were the problem as much as the width. Each element drops one step:

* the title `titleLarge` → `titleMedium`, and its app icon 32 → 28.dp;
* each row's label `bodyLarge` → `bodyMedium`;
* the switches drawn at `scale(0.85f)`, which is what actually takes the height out — a Material
  switch has no size of its own to set, and its 48.dp minimum is what made six rows this tall;
* the card's own padding 10 → 8.dp.

⚠ **Scaling a switch shrinks its touch target with it, and that is safe *here* only because the
whole row already takes the press** — see the row's own comment, which says so at length. Do not
copy this to a switch standing on its own.

⚠ **Nothing is given a hard `sp`.** Every size above is either a named type style or a `dp`, so
the dialog still follows the user's font-size setting.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

EDITS: list[tuple[str, str]] = [
    # ---------------- 1. Its own cap ----------------
    (
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
        """        compact = false,
        // ⚠ **A cap of its own, and it is the lever r4w should have reached for.** A margin
        // narrows a dialog in proportion to the screen, so 32.dp did nothing on a tablet — where
        // the app-wide 580.dp cap decides the width — and not enough on a large phone. The
        // author saw both: *"too wide … on phones as well as tablets"*.
        //
        // At this width the dialog is the same small card on a folded razr, an S22 Ultra and a
        // tablet, because the cap binds on all three.
        maxWidth = MANAGER_MAX_WIDTH,
        // Still here, and not redundant: in a narrow or split-screen window the cap never binds
        // and this is again the only thing keeping the card off the edges.
        horizontalMargin = 24.dp,
        onDismissRequest = onDismissRequest,""",
    ),
    # ---------------- 2. The card's own padding ----------------
    (
        """        Column(
            modifier = Modifier
                // No cap here any more. r4i put one on because this dialog kept the platform
                // width; now that it is on `DialogContainer`'s own path the container caps it
                // at the same 460dp, and two caps on one dialog is two places to change a
                // number and one of them to forget.
                .fillMaxWidth()
                .padding(10.dp),
        ) {""",
        """        Column(
            modifier = Modifier
                // No cap here. r4i put one on because this dialog kept the platform width;
                // since r4k it is on `DialogContainer`'s own path and the cap is passed to the
                // container above — two caps on one dialog is two places to change a number and
                // one of them to forget.
                .fillMaxWidth()
                .padding(8.dp),
        ) {""",
    ),
    # ---------------- 3. The title line ----------------
    (
        """                Image(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)""",
        """                Image(
                    modifier = Modifier
                        .size(28.dp)
                        .clip(CircleShape)""",
    ),
    (
        """                Text(
                    text = stringResource(R.string.settings_manager_title),
                    style = MaterialTheme.typography.titleLarge,
                )""",
        """                Text(
                    text = stringResource(R.string.settings_manager_title),
                    // One step down, with everything else on this dialog — r4y.
                    style = MaterialTheme.typography.titleMedium,
                )""",
    ),
    # ---------------- 4. The rows ----------------
    (
        """                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(isShevery = isShevery),
                    style = MaterialTheme.typography.bodyLarge,
                )""",
        """                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(isShevery = isShevery),
                    style = MaterialTheme.typography.bodyMedium,
                )""",
    ),
    (
        """        if (usable) {
            Switch(checked = enabled, colors = switchColors, onCheckedChange = onSetEnabled)
        } else {""",
        """        if (usable) {
            Switch(
                // ⚠ **Scaled, and this is what actually takes the height out of the dialog.** A
                // Material switch has no size to set and reserves a 48.dp minimum, which six
                // rows of turned into the height the author reported.
                //
                // ⚠ Its touch target shrinks with it, and that is safe **here only** because the
                // whole row already takes the press — see the row's own comment above. A switch
                // standing on its own must not copy this.
                modifier = Modifier.scale(SWITCH_SCALE),
                checked = enabled,
                colors = switchColors,
                onCheckedChange = onSetEnabled,
            )
        } else {""",
    ),
    (
        """                Switch(
                    checked = enabled,
                    // Disabled, but not greyed into nothing: this row is still reporting a""",
        """                Switch(
                    modifier = Modifier.scale(SWITCH_SCALE),
                    checked = enabled,
                    // Disabled, but not greyed into nothing: this row is still reporting a""",
    ),
]

CONSTANTS = """
/**
 * How wide this dialog is allowed to get, on any screen.
 *
 * ⚠ **Narrower than the app-wide `DIALOG_MAX_WIDTH`, on purpose.** Every other dialog is opened
 * from inside IMD with the app behind it; this one is opened from a tile or a shortcut, over
 * somebody else's app, and a card that fills the screen reads as having replaced that app rather
 * than as sitting on top of it. The author asked for it smaller on phone and tablet alike.
 */
private val MANAGER_MAX_WIDTH = 340.dp

/**
 * How much of its natural size each row's switch is drawn at.
 *
 * A Material switch has no size parameter and reserves a 48.dp minimum height; six of them is
 * most of this dialog. Scaling is the only lever, and it is safe here because the whole row takes
 * the press — see [SettingRow].
 */
private const val SWITCH_SCALE = 0.85f
"""

AFTER = [
    ("private val MANAGER_MAX_WIDTH = 340.dp", 1),
    ("maxWidth = MANAGER_MAX_WIDTH,", 1),
    ("horizontalMargin = 24.dp,", 1),
    ("private const val SWITCH_SCALE = 0.85f", 1),
    ("Modifier.scale(SWITCH_SCALE)", 2),
    ("typography.titleMedium,", 1),
    # ⚠ No switch is left unscaled, and no old size survives.
    ("horizontalMargin = 32.dp,", 0),
    (".size(32.dp)", 0),
    # ⚠ Two, counted from the file: the Shizuku-help and Shevery-toggle pop-ups in this same
    # file keep theirs. Only the manager card was reported as too big, and shrinking two
    # unrelated dialogs on the way past would be a change the author never asked for.
    ("typography.titleLarge,", 2),
]


def main() -> int:
    path = ROOT / MANAGER

    if not path.is_file():
        print(f"REFUSED: missing {MANAGER}")
        return 1

    text = path.read_text(encoding="utf-8")

    # ⚠ Counted before the edits: every Switch in this file must end up scaled, and the check
    # below is only meaningful if this is the number it started with.
    # ⚠ Counted as one bare token. A first draft added a 12-space match to a 16-space one and
    # got 3 from two call sites: the shorter indentation is a *substring* of the longer.
    # `SwitchDefaults.colors()` is not matched, because it has no bracket after the word.
    switches = text.count("Switch(")

    if switches != 2:
        print(f"REFUSED: {MANAGER}\n  expected 2 Switch call sites, found {switches}")
        return 1

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {MANAGER}\n  {old.strip().splitlines()[0][:70]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    anchor = "@Composable\ninternal fun AndroidSettingsManagerDialog("

    if text.count(anchor) != 1:
        print(f"REFUSED: {MANAGER}\n  nowhere to declare the constants")
        return 1

    text = text.replace(anchor, CONSTANTS.lstrip("\n") + "\n" + anchor, 1)

    lines = text.splitlines(keepends=True)

    statement = "import androidx.compose.ui.draw.scale\n"

    if statement not in text:
        indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

        target = next((i for i in indices if lines[i] > statement), indices[-1] + 1)

        lines.insert(target, statement)

        text = "".join(lines)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {MANAGER}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    for required in ("import androidx.compose.ui.unit.dp", "import androidx.compose.ui.draw.scale"):
        if required not in text:
            print(f"REFUSED: {MANAGER}\n  {required!r} is absent")
            return 1

    # ⚠ The container must still accept both parameters r4w gave it, or this is a silent no-op.
    container = (
        ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"
    ).read_text(encoding="utf-8")

    for parameter in ("maxWidth: Dp = DIALOG_MAX_WIDTH,", "horizontalMargin: Dp = DIALOG_MARGIN,"):
        if parameter not in container:
            print(f"REFUSED: Dialog.kt\n  {parameter!r} is absent")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {MANAGER}  :: 340.dp cap, one type step down, switches at 0.85")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
