#!/usr/bin/env python3
"""v3-r4q — two changes to the Support dialog's note.

    "underline the bold lines 'support this project' 'keep it alive'"
    "replace 'a more capable developer' with 'more capable developers'"

## The underline

The third paragraph - *"You can do these for free, if you want to support this project and keep
it alive."* - is already bold in full. The author wants those two phrases underlined **within**
it, so `underlined` joins `emphasised` and `highlighted` in `Emphasis.kt`, built the same way and
for the same three reasons written down there: the translator gets a whole sentence, a
translation that reorders it still gets the marks in the right places, and a phrase a translation
phrases around is skipped rather than breaking the line.

⚠ **The phrases are their own string resources.** Searching for an English substring inside a
translated sentence finds nothing, so each locale needs to be able to say what its own version of
*"support this project"* is - the same arrangement every other `emphasised` call site in this app
already uses.

## ⚠ `Paragraph` gains an overload rather than changing shape

Three of the four paragraphs are plain strings and stay plain strings. Changing the existing
function to take an `AnnotatedString` would have meant wrapping all three at their call sites for
the benefit of the fourth.

## The replacement

`support_intro_4`, verbatim: *"a more capable developer"* becomes *"more capable developers"*.
The rest of the sentence is untouched.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EMPHASIS = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Emphasis.kt"

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SupportDialog.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    # 1. The helper, beside the two it is built from.
    (
        EMPHASIS,
        """/**
 * The same, in the theme's own accent colour as well as bold.""",
        """/**
 * Underlines the named phrases wherever they appear in a sentence.
 *
 * The third of this file's three marks, and the one for a phrase inside a line that is already
 * emphasised as a whole - underlining what the sentence is *about* when bolding it again would
 * say nothing, because the line around it is bold too.
 *
 * Built exactly like [emphasised], and the reasons there are the reasons here: the translator
 * gets a whole sentence rather than fragments, a translation that reorders it still gets its
 * marks in the right places, and a phrase a translation phrases around is skipped rather than
 * treated as an error.
 */
@Composable
fun underlined(text: String, names: List<String>): AnnotatedString = remember(text, names) {
    buildAnnotatedString {
        append(text)

        names.forEach { name ->
            val start = text.indexOf(name)

            if (start >= 0) {
                addStyle(
                    style = SpanStyle(textDecoration = TextDecoration.Underline),
                    start = start,
                    end = start + name.length,
                )
            }
        }
    }
}

/**
 * The same, in the theme's own accent colour as well as bold.""",
    ),
    (
        EMPHASIS,
        """import androidx.compose.ui.text.font.FontWeight""",
        """import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextDecoration""",
    ),
    # 2. The two phrases, as resources a translation can answer.
    (
        STRINGS,
        """    <string name="support_intro_3">""",
        """    <!-- Underlined inside support_intro_3. Their own resources so a translation can say
         what its version of each phrase is - a search for the English inside a translated
         sentence finds nothing. -->
    <string name="support_name_project">support this project</string>
    <string name="support_name_alive">keep it alive</string>
    <string name="support_intro_3">""",
    ),
    # 3. The author's replacement.
    (
        STRINGS,
        """<string name="support_intro_4">I want it to be taken over by a more capable developer in future,""",
        """<string name="support_intro_4">I want it to be taken over by more capable developers in future,""",
    ),
    # 4. The paragraph that carries the marks.
    (
        DIALOG,
        """            Paragraph(
                text = stringResource(R.string.support_intro_3),
                bold = true,
            )""",
        """            // ⚠ **Bold *and* underlined, and the two are doing different jobs.** The whole
            // line is the turn from "why" to "how you can help", which is what the bold says;
            // the two underlined phrases are what the help is *for*, which bolding again could
            // not have said inside a line that is already bold.
            Paragraph(
                text = underlined(
                    text = stringResource(R.string.support_intro_3),
                    names = listOf(
                        stringResource(R.string.support_name_project),
                        stringResource(R.string.support_name_alive),
                    ),
                ),
                bold = true,
            )""",
    ),
    # 5. The overload it needs.
    (
        DIALOG,
        """/** One paragraph of the note, with a little air under it so the four read as separate. */
@Composable
private fun Paragraph(
    text: String,
    bold: Boolean = false,
) {""",
        """/**
 * The same paragraph, already marked up.
 *
 * An overload rather than a change of shape: three of the four paragraphs are plain strings and
 * have no reason to be wrapped at their call sites for the sake of the fourth.
 */
@Composable
private fun Paragraph(
    text: AnnotatedString,
    bold: Boolean = false,
) {
    Text(
        modifier = Modifier.padding(bottom = 10.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
        fontWeight = if (bold) FontWeight.Bold else null,
    )
}

/** One paragraph of the note, with a little air under it so the four read as separate. */
@Composable
private fun Paragraph(
    text: String,
    bold: Boolean = false,
) {""",
    ),
    # 6. Deferred, under the standing rule.
    (
        TRANSLATIONS,
        """    # r4p: the settings manager's four-word scope note.""",
        """    # r4q: the two phrases underlined inside the Support dialog's third paragraph.
    "support_name_project",
    "support_name_alive",
    # r4p: the settings manager's four-word scope note.""",
    ),
]

IMPORTS = [
    (DIALOG, "import androidx.compose.ui.text.AnnotatedString"),
    (DIALOG, "import com.android.geto.designsystem.component.underlined"),
]

AFTER = [
    (EMPHASIS, "fun underlined(", 1),
    (EMPHASIS, "TextDecoration.Underline", 1),
    (DIALOG, "underlined(", 1),
    (DIALOG, "private fun Paragraph(", 2),
    (DIALOG, "R.string.support_name_project", 1),
    (DIALOG, "R.string.support_name_alive", 1),
    (STRINGS, 'name="support_name_project"', 1),
    (STRINGS, 'name="support_name_alive"', 1),
    (STRINGS, "a more capable developer", 0),
    (STRINGS, "more capable developers", 1),
    (TRANSLATIONS, '"support_name_project"', 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import ")]

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

    print(f"  ok        {EMPHASIS}  :: underlined, beside emphasised and highlighted")
    print(f"  ok        {STRINGS}  :: two phrase resources; 'more capable developers'")
    print(f"  ok        {DIALOG}  :: the third paragraph is bold with two underlines")
    print(f"  ok        {TRANSLATIONS}  :: both phrases deferred")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
