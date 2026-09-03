#!/usr/bin/env python3
"""v3-r4p — every row in the language picker reads left to right, radio button included.

    "in the languages selection page at initilisation show all languages from left and the
     toggle too, i notice one is rtl"
    "can we show arabic toggle from ltr not rtl?"

## What was there and why it is wrong

`LanguageChoice` took an `rtl` flag and the Arabic row passed `true`, so that row alone laid
itself out right to left: its radio button jumped to the right edge and its endonym sat against
it. The reasoning in the KDoc was that a language's name should be "laid out in its own script" -
which is true of the *text* and was then applied to the *row*.

⚠ **Script direction and row direction are different questions.** Arabic text renders right to
left by itself, from the characters, whatever the row does; `LayoutDirection` only decides which
end of the row the radio button sits at. Forcing the row bought nothing for the script and cost
the one thing a picker needs - a column of radio buttons the eye can run down.

The System row had the same problem from the other side: it followed the *page*, so previewing
Arabic flipped it while the endonym rows below it stayed put.

## The fix

The `rtl` parameter goes, and the list is laid out left to right in full. One column of radio
buttons down the left, every endonym still in its own script beside it.

⚠ **The page around it is untouched.** Its title, notes and Continue button still follow the
previewed language, which is the whole point of previewing - tapping Arabic still shows what the
app will look like in Arabic. Only the picker rows are pinned, because they are a control rather
than a specimen of the language.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/LanguageSetupScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. The System row stops following the page.
    (
        """                    // Its label is a translated string, so it follows the page's direction
                    // rather than forcing one of its own the way the endonym rows below do.
                    LanguageChoice(
                        label = preview.getString(commonR.string.language_system),
                        selected = draft == AppLocale.SYSTEM,
                        rtl = null,
                        onClick = { draft = AppLocale.SYSTEM },
                    )""",
        """                    LanguageChoice(
                        label = preview.getString(commonR.string.language_system),
                        selected = draft == AppLocale.SYSTEM,
                        onClick = { draft = AppLocale.SYSTEM },
                    )""",
    ),
    # 2. The endonym rows stop forcing one.
    (
        """                    AppLocale.LANGUAGES.forEach { (tag, endonym) ->
                        LanguageChoice(
                            label = endonym,
                            selected = draft == tag,
                            rtl = tag == "ar",
                            onClick = { draft = tag },
                        )
                    }""",
        """                    AppLocale.LANGUAGES.forEach { (tag, endonym) ->
                        LanguageChoice(
                            label = endonym,
                            selected = draft == tag,
                            onClick = { draft = tag },
                        )
                    }""",
    ),
    # 3. The row itself, and the KDoc that argued for the old behaviour.
    (
        """/**
 * One language, written in its own script and laid out in its own direction.
 *
 * The direction is per row rather than per screen: the page around it is still in whatever
 * language the app is currently using, and flipping the whole screen for one Arabic entry
 * in the list would move the scrollbar and the button under the reader's thumb.
 */
@Composable
private fun LanguageChoice(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    rtl: Boolean? = null,
    onClick: () -> Unit,
) {
    // null follows the page's own direction - used by the System row, whose label is one of the
    // translated strings; true/false forces this row's direction, used by the endonym rows so
    // each language's name is laid out in its own script regardless of the page around it.
    val direction = when (rtl) {
        true -> LayoutDirection.Rtl
        false -> LayoutDirection.Ltr
        null -> LocalLayoutDirection.current
    }

    CompositionLocalProvider(LocalLayoutDirection provides direction) {""",
        """/**
 * One language, written in its own script and always laid out left to right.
 *
 * ⚠ **Script direction and row direction are not the same question**, and this row used to
 * answer the first with the second. Arabic text renders right to left from its own characters
 * whatever the row does; [LayoutDirection] only decides which end of the row the radio button
 * sits at. So the Arabic entry gained nothing from a right-to-left row and lost the thing a
 * picker needs, which is one column of radio buttons the eye can run down - the author's
 * *"show all languages from left and the toggle too"*.
 *
 * Pinned rather than left to follow the page, so previewing Arabic does not flip the list under
 * the reader while they are still choosing from it. The page around it still follows the
 * preview, which is what makes the preview worth having.
 */
@Composable
private fun LanguageChoice(
    modifier: Modifier = Modifier,
    label: String,
    selected: Boolean,
    onClick: () -> Unit,
) {
    CompositionLocalProvider(LocalLayoutDirection provides LayoutDirection.Ltr) {""",
    ),
]

# Nothing may still be asking for a per-row direction after this.
#
# ⚠ `LayoutDirection.Rtl` is *not* in this list, and the first draft's refusal is why: the page
# itself still computes one, in `pageDirection`, and a file-wide absence check said so. What has
# to go is a direction chosen inside the row - so the row's own body is what is searched.
GONE = ["rtl = "]

ROW = "private fun LanguageChoice("

ROW_GONE = ["LayoutDirection.Rtl", "LocalLayoutDirection.current"]

# The page's own direction is deliberately kept.
KEPT = "LocalLayoutDirection provides pageDirection"


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    if text.count(KEPT) != 1:
        print(f"REFUSED: {SCREEN}\n  the page's own direction is not where it was")
        return 1

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SCREEN}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for token in GONE:
        if token in text:
            print(f"REFUSED: {SCREEN}\n  {token!r} survives the edits")
            return 1

    # The row's own body, from its declaration to the end of the file - the only place a
    # per-row direction could still be chosen.
    if text.count(ROW) != 1:
        print(f"REFUSED: {SCREEN}\n  {ROW!r} occurs {text.count(ROW)} time(s), expected 1")
        return 1

    body = text[text.index(ROW):]

    for token in ROW_GONE:
        if token in body:
            print(f"REFUSED: {SCREEN}\n  {token!r} survives inside LanguageChoice")
            return 1

    # And exactly one right-to-left direction is left in the file: the page's.
    if text.count("LayoutDirection.Rtl") != 1:
        print(
            f"REFUSED: {SCREEN}\n  expected exactly one LayoutDirection.Rtl (the page's), "
            f"found {text.count('LayoutDirection.Rtl')}",
        )
        return 1

    if text.count(KEPT) != 1:
        print(f"REFUSED: {SCREEN}\n  the page's own direction did not survive the edits")
        return 1

    # Three call sites lost an argument; the parameter lost its default. A row left behind
    # would be a compile failure in a module the sandbox cannot build.
    if text.count("LanguageChoice(") != 3:
        print(f"REFUSED: {SCREEN}\n  expected one declaration and two call sites of LanguageChoice")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: every picker row is left to right, radio button included")
    print("  ok        the page still previews the tapped language's own direction")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
