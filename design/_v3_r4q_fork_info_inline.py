#!/usr/bin/env python3
"""v3-r4q — the Thedjchi ⓘ moves into the text, after the last word.

    "the i logo button in thedjchi toggle move it to where the toggle text ends i.e. after
     '...intents' same for the new screen at initialisation"

## Why it was not there already

`ForkModeRow` draws the label as a `Text` with `weight(1f, fill = false)` and the ⓘ as a
*sibling* after it. On a row whose label fits one line those two read as one thing; the Thedjchi
label is *"Thedjchi / other forks of Shizuku that support start-stop intents"*, which wraps to
two or three lines, and a sibling is then vertically centred against the whole block rather than
sitting after the last word.

⚠ **A sibling can never do this.** Following the end of wrapped text is not a layout a `Row` can
express - the icon has to be part of the text run. `AnnotatedString`'s inline content is exactly
that: a placeholder in the string, filled by a composable, wrapped and positioned by the text
layout.

⚠ **It is still its own tap target.** The inline composable carries its own `clickable`, so
tapping the ⓘ opens the checklist and tapping anywhere else in the row chooses the fork - the
arrangement the sibling had, kept.

## ⚠ The setup page gets this for nothing

*"same for the new screen at initialisation"* - the onboarding page draws `ShizukuSection`, which
draws `ForkModeSelector`, which is this row. There is one of it, which is the whole reason the
page was made to share the section rather than copy it.

## Shevery is untouched

Its caution is a *phrase* with an icon, not an icon alone, and its label is one short word - so
its trailing slot already sits where the author is asking the other one to go. `trailing` stays
on the row for it.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. The label carries a placeholder where the icon goes.
    (
        """/** The linked fork name, then what the family covers. */
@Composable
private fun thedjchiForkLabel(): AnnotatedString {
    val linkStyles = linkStyles()

    val thedjchi = stringResource(R.string.shizuku_fork_thedjchi)

    val suffix = stringResource(R.string.shizuku_fork_mode_thedjchi_suffix)

    return remember(thedjchi, suffix, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_URL, styles = linkStyles)) {
                append(thedjchi)
            }
            append(" ")
            append(suffix)
        }
    }
}""",
        """/**
 * The linked fork name, what the family covers, and the ⓘ after the last word of it.
 *
 * ⚠ **The ⓘ is a placeholder in the string, not a sibling of it** - the author's *"move it to
 * where the toggle text ends i.e. after '...intents'"*. This label wraps to two or three lines,
 * and an icon drawn beside the `Text` is centred against the whole block; only inline content is
 * carried by the text layout to the end of the last line.
 */
@Composable
private fun thedjchiForkLabel(): AnnotatedString {
    val linkStyles = linkStyles()

    val thedjchi = stringResource(R.string.shizuku_fork_thedjchi)

    val suffix = stringResource(R.string.shizuku_fork_mode_thedjchi_suffix)

    return remember(thedjchi, suffix, linkStyles) {
        buildAnnotatedString {
            withLink(LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_URL, styles = linkStyles)) {
                append(thedjchi)
            }
            append(" ")
            append(suffix)
            // The space is part of the run rather than padding on the icon, so a line that
            // breaks here breaks between the words and the ⓘ rather than orphaning it.
            append(" ")
            appendInlineContent(FORK_INFO_ID, "\\u24d8")
        }
    }
}

/**
 * The id the placeholder above and the composable below agree on.
 *
 * ⚠ A placeholder whose id is not in the `inlineContent` map is drawn as its alternate text -
 * here the ⓘ character itself, which would look almost right and do nothing when tapped. The
 * constant is what stops the two from being spelled differently.
 */
private const val FORK_INFO_ID = "forkInfo\"""",
    ),
    # 2. The row can carry inline content.
    (
        """@Composable
private fun ForkModeRow(
    modifier: Modifier = Modifier,
    label: AnnotatedString,
    selected: Boolean,
    onSelect: () -> Unit,
    trailing: (@Composable () -> Unit)? = null,
) {""",
        """@Composable
private fun ForkModeRow(
    modifier: Modifier = Modifier,
    label: AnnotatedString,
    selected: Boolean,
    onSelect: () -> Unit,
    /**
     * Filled into any placeholder [label] carries.
     *
     * Used by the Thedjchi row for its ⓘ, which has to sit after the last word of a label that
     * wraps - see [thedjchiForkLabel]. Empty for a label with no placeholder.
     */
    inlineContent: Map<String, InlineTextContent> = emptyMap(),
    trailing: (@Composable () -> Unit)? = null,
) {""",
    ),
    (
        """        Text(
            modifier = Modifier.weight(1f, fill = false),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )""",
        """        Text(
            modifier = Modifier.weight(1f, fill = false),
            text = label,
            style = MaterialTheme.typography.bodyMedium,
            inlineContent = inlineContent,
        )""",
    ),
    # 3. The selector hands it over instead of a trailing sibling.
    (
        """        ForkModeRow(
            label = thedjchiForkLabel(),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
            trailing = { ForkInfoButton(onClick = onShowThedjchiNotice) },
        )""",
        """        ForkModeRow(
            label = thedjchiForkLabel(),
            selected = selected == ShizukuForkMode.Thedjchi,
            onSelect = { onSelect(ShizukuForkMode.Thedjchi) },
            inlineContent = forkInfoInline(onClick = onShowThedjchiNotice),
        )""",
    ),
    # 4. The inline ⓘ itself, in place of the sibling button.
    (
        """/**
 * The ⓘ beside a fork's name, opening that fork's setup pop-up.
 *
 * Always visible, on the author's instruction, and outside the row's `selectable` so that
 * tapping it explains the option rather than choosing it — the same arrangement
 * [SheveryCaution] already has.
 */
@Composable
private fun ForkInfoButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {""",
        """/**
 * The ⓘ that sits *inside* the Thedjchi label, after its last word.
 *
 * ⚠ **Sized in `em`, not `dp`.** The placeholder is a hole in a line of text, so it has to scale
 * with the text - a fixed size would leave the icon too large or too small the moment the reader
 * changes their font size, and would knock the line height about while doing it.
 *
 * Still its own tap target, outside nothing: the composable filling a placeholder is a real
 * composable, so its `clickable` takes the press before the row's `selectable` sees it, and
 * tapping the ⓘ explains the option rather than choosing it - the arrangement the sibling button
 * had, kept.
 */
@Composable
private fun forkInfoInline(onClick: () -> Unit): Map<String, InlineTextContent> {
    val tint = MaterialTheme.colorScheme.primary

    return mapOf(
        FORK_INFO_ID to InlineTextContent(
            placeholder = Placeholder(
                width = 1.2.em,
                height = 1.2.em,
                placeholderVerticalAlign = PlaceholderVerticalAlign.TextCenter,
            ),
        ) {
            Icon(
                modifier = Modifier
                    .fillMaxSize()
                    .clickable(onClick = onClick),
                imageVector = GetoIcons.Info,
                contentDescription = null,
                tint = tint,
            )
        },
    )
}

/**
 * The ⓘ beside a fork's name, opening that fork's setup pop-up.
 *
 * Always visible, on the author's instruction, and outside the row's `selectable` so that
 * tapping it explains the option rather than choosing it — the same arrangement
 * [SheveryCaution] already has.
 *
 * ⚠ Unused since r4q on the Thedjchi row, which now carries its ⓘ inline - see
 * [forkInfoInline]. Kept because the Shevery row's caution is built the same way and a future
 * row with a one-line label wants exactly this.
 */
@Suppress("unused")
@Composable
private fun ForkInfoButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {""",
    ),
]

IMPORTS = [
    "import androidx.compose.foundation.layout.fillMaxSize",
    "import androidx.compose.foundation.text.InlineTextContent",
    "import androidx.compose.foundation.text.appendInlineContent",
    "import androidx.compose.ui.text.Placeholder",
    "import androidx.compose.ui.text.PlaceholderVerticalAlign",
    "import androidx.compose.ui.unit.em",
]

AFTER = [
    ("FORK_INFO_ID", 3),
    ("forkInfoInline", 3),
    # Five: the parameter, the two on the assignment line that hands it to Text, the call
    # site, and the KDoc on FORK_INFO_ID that names the map. The comment trap again, inflating.
    ("inlineContent", 5),
    # The sibling is gone from the Thedjchi row and nowhere else lost its trailing.
    ("trailing = { ForkInfoButton(onClick = onShowThedjchiNotice) },", 0),
    ("trailing = { SheveryCaution(onClick = onShowSheveryNotice) },", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SCREEN}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for statement in IMPORTS:
        text = add_import(text, statement)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SCREEN}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: the Thedjchi ⓘ is inline, after '...intents'")
    print("  ok        the setup page inherits it, drawing the same section")
    print("  ok        Shevery's caution untouched")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
