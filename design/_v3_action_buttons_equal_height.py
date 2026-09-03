#!/usr/bin/env python3
"""r4l — the two action buttons are the same height, whichever of them wraps.

The author, on r4k's build:

    "obviously rev to def button is long text so it didnt fit and wraped in this case can we
     match hide settings button height to match it's"

r4k widened the dialog and trimmed the button padding, and on his phone `Revert to default`
still takes two lines. That is fine — what is not fine is that its neighbour stays one line
tall, so a pair drawn deliberately at equal *width* ends up at unequal *height*.

### How

`Modifier.height(IntrinsicSize.Min)` on the Row, `fillMaxHeight()` on each button. The Row
measures the taller child and gives both that height; a button whose label fits on one line
simply centres it in the taller box.

⚠ **Intrinsics rather than a fixed height.** A hard `height(56.dp)` would be right for English
and wrong for the first translation that wraps to three lines — and translations are still
deferred, so nothing here would catch it. This asks the label how tall it needs to be.

⚠ **Everything in that row supports intrinsic measurement.** `Surface`, `Row`, `Icon` and `Text`
all do; nothing in this dialog uses `SubcomposeLayout`, which is the one thing that would refuse.
Worth stating because `feature/apps` is not a module the sandbox compiles, so this is reasoned
rather than proven here.

⚠ **The `verticalAlignment` stays.** With both children filling the height it decides nothing
about the pair, but it is still what centres a short label inside its own button.

⚠ **This is the sibling of the equal-width note already above the Row**, which says two buttons
of different widths "read as one button and one afterthought". Different heights read the same
way, and the fix belongs beside the same reasoning.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

ROW_OLD = """            // Equal width rather than each at its natural size. Two watermarked buttons of
            // different widths read as one button and one afterthought, and "Revert to
            // default" is long enough that the difference would be obvious.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
"""

ROW_NEW = """            // Equal width rather than each at its natural size. Two watermarked buttons of
            // different widths read as one button and one afterthought, and "Revert to
            // default" is long enough that the difference would be obvious.
            //
            // ⚠ **Equal height too, and for the same reason.** On a narrow phone that label
            // takes two lines and its neighbour takes one, so a pair drawn deliberately at
            // one width came out at two heights - the author's report on r4k.
            //
            // `IntrinsicSize.Min` measures the taller child and gives both that height, so a
            // one-line label centres inside the taller box. A fixed height would be right for
            // English and wrong for the first translation that wraps to three lines, and
            // translations are deferred, so nothing here would catch it.
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(IntrinsicSize.Min),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                // Decides nothing about the pair now that both fill the height; still what
                // centres a short label inside its own button.
                verticalAlignment = Alignment.CenterVertically,
            ) {
"""

FIRST_OLD = """                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = if (anythingHidden) {
"""

FIRST_NEW = """                ActionButton(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    glyph = if (anythingHidden) {
"""

SECOND_OLD = """                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_revert_glyph,
"""

SECOND_NEW = """                ActionButton(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    glyph = designR.drawable.ic_revert_glyph,
"""

# The label has to be allowed to wrap and to centre when it does.
LABEL_OLD = """            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                textAlign = TextAlign.Center,
            )
"""

LABEL_NEW = """            Text(
                text = label,
                style = MaterialTheme.typography.labelLarge,
                textAlign = TextAlign.Center,
            )
"""

IMPORT_OLD = """import androidx.compose.foundation.layout.height
"""

IMPORT_NEW = """import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.height
"""

INTRINSIC_OLD = """import androidx.compose.ui.Modifier
"""

INTRINSIC_NEW = """import androidx.compose.ui.Modifier
"""


def main() -> int:
    path = ROOT / MANAGER

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in (
        (ROW_OLD, ROW_NEW, 1),
        (FIRST_OLD, FIRST_NEW, 1),
        (SECOND_OLD, SECOND_NEW, 1),
    ):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Imports, added only if the file does not already carry them.
    for needed, anchor in (
        ("import androidx.compose.foundation.layout.fillMaxHeight\n",
         "import androidx.compose.foundation.layout.fillMaxWidth\n"),
        ("import androidx.compose.foundation.layout.IntrinsicSize\n",
         "import androidx.compose.foundation.layout.Row\n"),
    ):
        if needed in text:
            continue

        if text.count(anchor) != 1:
            problems.append(f"cannot place {needed.strip()!r}")

            continue

        # Alphabetical within the block: IntrinsicSize sorts before Row, fillMaxHeight before
        # fillMaxWidth, so both go in front of their anchor.
        text = text.replace(anchor, needed + anchor, 1)

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        (".height(IntrinsicSize.Min),", 1),
        # ⚠ Three, not two: PillHalf's Surface has carried one since r4c. The two that matter
        # are pinned by the multi-line token in the position check below, not by this count.
        (".fillMaxHeight(),", 3),
        ("import androidx.compose.foundation.layout.IntrinsicSize", 1),
        ("import androidx.compose.foundation.layout.fillMaxHeight", 1),
        # ⚠ Five: the two action buttons, the two pill halves and the row label's Column.
        # Unchanged by this edit, which is the point - the height is added, not swapped for it.
        (".weight(1f)", 5),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token!r}, found {text.count(token)}")

    # ⚠ **Position, not presence.** The intrinsic height belongs on the action row, not on the
    # master pill or a target row - both of which also call `height`.
    row = text.find("            // ⚠ **Equal height too, and for the same reason.**")
    intrinsic = text.find("                    .height(IntrinsicSize.Min),")
    first = text.find("                ActionButton(\n                    modifier = Modifier\n"
                      "                        .weight(1f)\n"
                      "                        .fillMaxHeight(),")

    if min(row, intrinsic, first) < 0:
        problems.append("cannot locate the row comment, the intrinsic height or the first button")
    elif not row < intrinsic < first:
        problems.append("the intrinsic height is not on the action row above its buttons")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  wrote {MANAGER}")
    print("ok - both action buttons take the taller one's height")

    return 0


if __name__ == "__main__":
    sys.exit(main())
