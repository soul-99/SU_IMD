#!/usr/bin/env python3
"""v3-r4q — the revert configuration says what it is *for*, before it says when it runs.

    "add a second paragraph in bold to rev to def config dialog and initialisation page, put it
     above the older para 'Helps you to quickly recover to a settings state you configured here
     in case of unsatisfactory outcomes.'"

The dialog opened with one paragraph, which answers *when this list runs* - and under the memory
function says something different from what it says under Revert to default. The author's new
line answers a question that comes first and has the same answer either way: **what this is for.**
So it goes above, and in bold, which is where and how he asked for it.

⚠ **Above the conditional paragraph, not merged into it.** The existing text is one of two
strings chosen by the unhiding framework; folding the new sentence into both would mean two copies
of it, and the two would drift the next time either half is reworded.

## The initialisation page

There is not one for this dialog. Page 3 of the onboarding batch was settled as **Settings to
hide only**, so nothing else draws this text today - and when a revert page is built it will draw
this dialog's own content rather than a copy, exactly as the Shizuku page draws `ShizukuSection`.
The string is the single place the sentence lives.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/RevertDefaultsDialog.kt"

TRANSLATIONS = "tools/check_translations.py"

EDITS: list[tuple[str, str, str]] = [
    (
        STRINGS,
        """    <string name="revert_defaults_desc_revert">""",
        """    <!-- Above the two below, and bold: what this list is for, which is the same answer
         under either unhiding framework. Those two say when it runs, which is not. -->
    <string name="revert_defaults_desc_recover">Helps you to quickly recover to a settings state you configured here in case of unsatisfactory outcomes.</string>
    <string name="revert_defaults_desc_revert">""",
    ),
    (
        DIALOG,
        """        // Says when this runs, which the title does not: "Revert to default" is the
        // name of five different buttons, and someone arriving here from the settings
        // list has just read "Settings to hide" one row above.
        Text(""",
        """        // ⚠ **What this is for, before what it does** - the author's placement. The
        // paragraph below answers "when does this run", and answers it differently under the
        // two unhiding frameworks; this answers "why would I fill this in", which has the same
        // answer either way. Its own Text rather than folded into both of those strings,
        // which would have been two copies of one sentence, free to drift apart.
        Text(
            modifier = Modifier.padding(horizontal = 10.dp),
            text = stringResource(R.string.revert_defaults_desc_recover),
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.Bold,
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Says when this runs, which the title does not: "Revert to default" is the
        // name of five different buttons, and someone arriving here from the settings
        // list has just read "Settings to hide" one row above.
        Text(""",
    ),
    (
        TRANSLATIONS,
        """    # r4q: the two phrases underlined inside the Support dialog's third paragraph.""",
        """    # r4q: what the revert configuration is for, above what it does.
    "revert_defaults_desc_recover",
    # r4q: the two phrases underlined inside the Support dialog's third paragraph.""",
    ),
]

AFTER = [
    (STRINGS, 'name="revert_defaults_desc_recover"', 1),
    (DIALOG, "revert_defaults_desc_recover", 1),
    (DIALOG, "FontWeight.Bold", 1),
    # The conditional paragraph below it is untouched, both arms.
    (DIALOG, "revert_defaults_desc_memory", 1),
    (DIALOG, "revert_defaults_desc_revert", 1),
    (TRANSLATIONS, '"revert_defaults_desc_recover"', 1),
]

NEEDED = [
    (DIALOG, "import androidx.compose.ui.text.font.FontWeight"),
    (DIALOG, "import androidx.compose.foundation.layout.Spacer"),
    (DIALOG, "import androidx.compose.foundation.layout.height"),
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

    for relative, statement in NEEDED:
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

    print(f"  ok        {STRINGS}  :: revert_defaults_desc_recover")
    print(f"  ok        {DIALOG}  :: bold, above the paragraph that says when this runs")
    print(f"  ok        {TRANSLATIONS}  :: deferred")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
