#!/usr/bin/env python3
"""r4c — the master pill: shorter, split by a real gap, reversed, and moved above the switches.

Four instructions from the author, all about the same control:

    "and me the all on all off buttons very small in height"
    "and put that button above the first toggle i.e. developer options"
    "and reverse their order all off on left all on on right"
    "make all on all of buttons seperator full length and instead of a line display background
     there for some width and smoothen the sharp edges at the center of buttons"

and one correction, after a template drew it wrong:

    "in our original buttons the buttons dont have borders instead only bg colour so why the
     line borders?"

He is right, and nothing here adds one: `MasterPill` was and stays a filled `surfaceVariant`
Surface. The only line in it was the inset hairline, and that is the thing being removed.

### What changes

* **40dp -> 28dp**, and the label drops from `labelLarge` to `labelMedium` to sit in it. Chosen
  from the template over 24dp and 32dp.
* **The hairline becomes a 4dp gap**, full height, showing the card behind it. Not a divider
  drawn in a third colour: a gap *is* the background, at any theme, with nothing to keep in
  step.
* **Two Surfaces, not one.** A gap through the middle of a single Surface would be a hole in a
  filled shape, which Compose has no way to draw; two shapes with a space between them is what
  the picture actually shows. Outer ends stay fully round at 14dp, the two corners either side
  of the gap come in to 2dp - the author's pick from 2/4/6dp, the least of the three.
* **All off left, All on right**, which reverses today's order.
* **Above `Developer options`**, at the top of the list rather than under the last switch.

⚠ **The comment that justified one shape is now the comment that justifies two**, and it is
rewritten rather than left standing. It argued that a gap makes a pair of controls look like
two decisions and the hairline says these are two ends of one; the author has looked at both
and chosen the gap, so the file should not go on telling a reader the opposite.

⚠ **`enabled` still dims rather than disables, and the halves keep their own clickables.** Only
the shape, the size, the order and the position move here. Anything about what a press does
would be a second change hiding inside a visual one.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

OLD_PILL_DOC = """/**
 * `All on` and `All off`, as one long pill with a division down the middle.
 *
 * Shape and shade are the author's pick from the templates: a single tonal pill in the
 * theme's own neutral shade rather than the action buttons' colour, so the row reads as
 * belonging to the switches above it rather than joining the two filled buttons below.
 *
 * ⚠ **One Surface with two halves, not two buttons side by side.** Two buttons would need a
 * gap between them, and a gap is what makes a pair of controls look like two decisions; the
 * hairline says these are two ends of one.
 *
 * ⚠ **No red state and no failure reporting**, on the author's instruction. Every row this
 * moves reports for itself, and a master control that also went red would be reporting the
 * same failure twice.
 *
 * [enabled] false is the dialog's busy state, or a device where no row can be operated at
 * all. Dimmed and inert, using the same disabled palette [ActionButton] restates — but
 * genuinely inert here, unlike that one, because there is nothing useful to say about a press
 * on a control whose rows are already explaining themselves.
 */"""

NEW_PILL_DOC = """/**
 * `All off` and `All on`, as two short tonal halves with a gap of the card between them.
 *
 * Shade is the author's pick from the r2b3d templates: the theme's own neutral rather than the
 * action buttons' colour, so the row reads as belonging to the switches beside it rather than
 * joining the two filled buttons at the foot of the dialog.
 *
 * ⚠ **Two Surfaces with a gap, not one Surface with a hairline** — the author looked at both
 * and chose the gap. An earlier note here argued the opposite, that a gap makes a pair of
 * controls look like two decisions where a hairline says these are two ends of one, and it is
 * replaced rather than left standing: the file should not go on recommending the shape the
 * screen no longer has.
 *
 * ⚠ **A gap, not a divider in a third colour.** The separation *is* the card showing through,
 * so it is right at every theme with nothing to keep in step, and it runs the full height
 * because there is nothing there to inset.
 *
 * ⚠ **Nor could it be one shape.** A full-height gap through the middle of a single Surface is
 * a hole in a filled shape, which is not something Compose draws; two shapes with a space
 * between them is the picture itself.
 *
 * ⚠ **No red state and no failure reporting**, on the author's instruction. Every row this
 * moves reports for itself, and a master control that also went red would be reporting the
 * same failure twice.
 *
 * [enabled] false is the dialog's busy state, or a device where no row can be operated at
 * all. Dimmed and inert, using the same disabled palette [ActionButton] restates — but
 * genuinely inert here, unlike that one, because there is nothing useful to say about a press
 * on a control whose rows are already explaining themselves.
 */"""

OLD_PILL_BODY = """    Surface(
        modifier = modifier
            .fillMaxWidth()
            .height(PILL_HEIGHT),
        shape = CircleShape,
        color = container,
        contentColor = content,
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            PillHalf(
                modifier = Modifier.weight(1f),
                label = stringResource(R.string.settings_manager_all_on),
                enabled = enabled,
                onClick = onAllOn,
            )

            // Inset top and bottom so it reads as a division rather than as two shapes that
            // happen to touch.
            Box(
                modifier = Modifier
                    .fillMaxHeight()
                    .padding(vertical = PILL_DIVIDER_INSET)
                    .width(PILL_DIVIDER_WIDTH),
            ) {
                Surface(
                    modifier = Modifier.fillMaxHeight().fillMaxWidth(),
                    color = content.copy(alpha = PILL_DIVIDER_ALPHA),
                    content = {},
                )
            }

            PillHalf(
                modifier = Modifier.weight(1f),
                label = stringResource(R.string.settings_manager_all_off),
                enabled = enabled,
                onClick = onAllOff,
            )
        }
    }
}"""

NEW_PILL_BODY = """    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(PILL_HEIGHT),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // All off first, at the author's instruction, which reverses the order this row had.
        PillHalf(
            modifier = Modifier.weight(1f),
            label = stringResource(R.string.settings_manager_all_off),
            shape = PILL_START_SHAPE,
            container = container,
            content = content,
            enabled = enabled,
            onClick = onAllOff,
        )

        Spacer(modifier = Modifier.width(PILL_GAP))

        PillHalf(
            modifier = Modifier.weight(1f),
            label = stringResource(R.string.settings_manager_all_on),
            shape = PILL_END_SHAPE,
            container = container,
            content = content,
            enabled = enabled,
            onClick = onAllOn,
        )
    }
}"""

OLD_HALF = """/** One end of [MasterPill]. Its own clickable, so the halves are two targets in one shape. */
@Composable
private fun PillHalf(
    modifier: Modifier = Modifier,
    label: String,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Box(
        modifier = modifier
            .fillMaxHeight()
            .clickable(enabled = enabled, onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Text(text = label, style = MaterialTheme.typography.labelLarge)
    }
}"""

NEW_HALF = """/**
 * One end of [MasterPill]: its own Surface, its own shape and its own clickable.
 *
 * The shape is passed in rather than decided here, because the two halves are mirror images -
 * round on the outside, nearly square where they face each other - and a half that worked out
 * which end it was would have to be told that anyway.
 *
 * `labelMedium` rather than `labelLarge`: at 28dp the larger size leaves no room above and
 * below the text, and the author asked for this row to be short.
 */
@Composable
private fun PillHalf(
    modifier: Modifier = Modifier,
    label: String,
    shape: Shape,
    container: Color,
    content: Color,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxHeight(),
        shape = shape,
        color = container,
        contentColor = content,
    ) {
        Box(
            modifier = Modifier
                .fillMaxHeight()
                .clickable(enabled = enabled, onClick = onClick),
            contentAlignment = Alignment.Center,
        ) {
            Text(text = label, style = MaterialTheme.typography.labelMedium)
        }
    }
}"""

OLD_CONSTANTS = """private val PILL_HEIGHT = 40.dp"""

NEW_CONSTANTS = """private val PILL_HEIGHT = 28.dp

/** The gap between the halves: the card showing through, full height, at the author's 4dp. */
private val PILL_GAP = 4.dp

/**
 * Round on the outside, barely softened where the two halves face the gap.
 *
 * 14dp is half of [PILL_HEIGHT], which is what makes the outer ends read as the same stadium
 * they were before the row was shortened. 2dp on the inner pair is the author's pick from a
 * template of 2, 4 and 6 - the least of the three, so the gap looks cut rather than moulded.
 */
private val PILL_START_SHAPE = RoundedCornerShape(
    topStart = 14.dp,
    bottomStart = 14.dp,
    topEnd = 2.dp,
    bottomEnd = 2.dp,
)

private val PILL_END_SHAPE = RoundedCornerShape(
    topStart = 2.dp,
    bottomStart = 2.dp,
    topEnd = 14.dp,
    bottomEnd = 14.dp,
)"""

# The three constants the hairline needed and nothing else uses now.
OLD_DIVIDER_CONSTANTS = """
private val PILL_DIVIDER_WIDTH = 1.dp

private val PILL_DIVIDER_INSET = 7.dp

private const val PILL_DIVIDER_ALPHA = 0.45f
"""

# Where the row sits: out from under the last switch, in above the first.
OLD_PLACEMENT = """            // The master pill, its own row directly below the last toggle. Above the gap
            // rather than below it: it belongs to the switches it operates, and the two
            // filled buttons under the gap are a different kind of thing entirely — those
            // change the device as a whole, this one is six switches pressed at once.
            Spacer(modifier = Modifier.height(10.dp))

            MasterPill(
                enabled = usableTargets.isNotEmpty(),
                onAllOn = { onSetAll(true, usableTargets) },
                onAllOff = { onSetAll(false, usableTargets) },
            )

            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))
"""

NEW_PLACEMENT = """            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))
"""

IMPORTS = [
    ("""import androidx.compose.foundation.shape.CircleShape
""",
     """import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
""",
     1),
    ("""import androidx.compose.ui.graphics.Color
""",
     """import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Shape
""",
     1),
]


def main() -> int:
    path = ROOT / MANAGER

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    # The pill moves before the anchor it is inserted after is searched for, so the removal is
    # done first and the insertion afterwards reads a tree the row has already left.
    subs: list[tuple[str, str, int]] = [
        (OLD_PILL_DOC, NEW_PILL_DOC, 1),
        (OLD_PILL_BODY, NEW_PILL_BODY, 1),
        (OLD_HALF, NEW_HALF, 1),
        (OLD_CONSTANTS, NEW_CONSTANTS, 1),
        (OLD_DIVIDER_CONSTANTS, "\n", 1),
        (OLD_PLACEMENT, NEW_PLACEMENT, 1),
    ] + IMPORTS

    for old, new, expected in subs:
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:64]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Now put it back, above the first switch. The anchor is the line that opens the row loop.
    anchor = """            drawnRows.forEach { target ->"""

    if text.count(anchor) != 1:
        print("REFUSED, nothing written")
        print(f"  expected 1 of {anchor.strip()!r}, found {text.count(anchor)}")

        return 1

    placed = """            // The master pill, above the first switch at the author's instruction rather
            // than below the last. It belongs to the switches it operates either way; at the
            // top it is read before them, which is the order someone reaches for "all off"
            // in - decide the lot, then correct the one or two that need it.
            MasterPill(
                enabled = usableTargets.isNotEmpty(),
                onAllOn = { onSetAll(true, usableTargets) },
                onAllOff = { onSetAll(false, usableTargets) },
            )

            Spacer(modifier = Modifier.height(10.dp))

""" + anchor

    text = text.replace(anchor, placed, 1)

    # After it all: the hairline is gone, the pill is drawn once, and it is above the loop.
    for token, expected in (
        ("PILL_DIVIDER", 0),
        ("MasterPill(", 2),
        ("PILL_START_SHAPE", 2),
        ("PILL_END_SHAPE", 2),
        ("PILL_GAP", 2),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token!r}, found {text.count(token)}")

    if text.index("MasterPill(\n                enabled") > text.index(anchor):
        problems.append("the pill is still drawn after the switches it sits above")

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
    print("ok - 28dp, a 4dp gap of card, 2dp inner corners, All off first, above the switches")

    return 0


if __name__ == "__main__":
    sys.exit(main())
