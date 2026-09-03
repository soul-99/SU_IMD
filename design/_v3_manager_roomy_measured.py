#!/usr/bin/env python3
"""
v3-r6 — the roomy tier, decided from three screens that have now actually been measured.

Three screenshots arrived at last, and both standing assumptions about the author's foldable were
wrong. The density falls straight out of [PILL_GAP], which is 4 dp of card showing between the two
halves of the master pill and is the smallest exact number on the screen:

    screenshot          pixels        pill gap    density        window
    fold, inner screen  2232 x 2484     11 px      2.75      811.6 x 903.3 dp
    fold, cover screen  1080 x 2520     11 px      2.75      392.7 x 916.4 dp
    S22 Ultra           1440 x 3088     15 px      3.75      384.0 x 823.5 dp

**It is not a clamshell.** The inner screen is 812 dp wide and very nearly square — a book-style
fold, not a tall narrow one. And the *cover* screen is an ordinary tall phone window at 2.33.

Which kills `_v3_manager_roomy_by_aspect.py` outright, and the wrong way round: the shape test was
written to catch a tall narrow inner screen, and on this device it catches the **cover** screen
(2.33 >= 2.30) while missing the inner one (1.11). It would have made the one screen he says looks
right into the roomy card, and left the one he says is too small exactly as it is.

The inner screen is 812 dp wide, so the plain width breakpoint that was already sitting beside the
aspect clause does the whole job on its own. The clause goes.

    fold inner   812 dp  >= 600  ->  Roomy    376 dp, margin 16   (was 305 — "too small")
    fold cover   393 dp   < 600  ->  Compact  316 dp              (was 325 — he says good)
    S22 Ultra    384 dp   < 600  ->  Compact  316 dp              (was 316 — he says good)

⚠ **The two compact answers are what the author already has and calls good**, which is the useful
part of measuring rather than guessing: r4z's physical rule was landing on 316 and 325 dp on those
two screens by itself. r6 pins them at 316 by name instead of by arithmetic, and only the inner
screen changes.

Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

WIDTH_KDOC_OLD = '''/**
 * A window wide enough to be roomy on width alone.
 *
 * The platform's own compact/medium breakpoint: past it there is a tablet or an unfolded
 * book-style foldable on the other side of the glass, whatever its shape.
 */
private const val ROOMY_WINDOW_WIDTH_DP = 600
'''

WIDTH_KDOC_NEW = '''/**
 * A window wide enough to be roomy, and the whole of the test.
 *
 * The platform's own compact/medium breakpoint: past it there is a tablet or an unfolded
 * book-style foldable on the other side of the glass, whatever its shape.
 *
 * ⚠ **Measured, finally.** Three of the author's screenshots were read for their density — which
 * falls straight out of [PILL_GAP], 4 dp of card showing between the halves of the master pill and
 * the smallest exact number on the screen — and both standing guesses about his foldable were
 * wrong:
 *
 * ```
 * screen              pixels        gap    density        window          tier
 * fold, inner        2232 x 2484   11 px    2.75     811.6 x 903.3 dp     Roomy
 * fold, cover        1080 x 2520   11 px    2.75     392.7 x 916.4 dp     Compact
 * S22 Ultra          1440 x 3088   15 px    3.75     384.0 x 823.5 dp     Compact
 * ```
 *
 * It is a **book-style** fold, not a clamshell: the inner screen is 812 dp wide and very nearly
 * square. So it clears this breakpoint by two hundred dp and needs nothing else — where the aspect
 * clause r5 carried alongside this one had it exactly backwards, catching the *cover* screen at
 * 2.33 and missing the inner one at 1.11.
 *
 * ⚠ The two compact answers are what he already has and calls good: r4z's physical rule was
 * landing on 316 and 325 dp on those two screens by arithmetic. Only the inner screen changes.
 */
private const val ROOMY_WINDOW_WIDTH_DP = 600
'''

ASPECT_OLD = '''/**
 * And the tall, narrow window that is also roomy: a clamshell foldable opened up.
 *
 * ⚠ **Its shape, not its height, and that is what makes this test trustworthy.** A ratio is the
 * same at every density, so unlike a dp threshold it does not rest on a guess at what density
 * Motorola chose — which had been load-bearing for three rounds and wrong at least once.
 *
 * ```
 * razr fold, inner   2640 / 1080  =  2.44      ordinary 20:9   2400 / 1080  =  2.22
 * Xperia-class 21:9  3840 / 1644  =  2.33      S22 Ultra       3088 / 1440  =  2.14
 *                                              razr, cover      484 /  411  =  1.18
 * ```
 *
 * 2.30 clears every ordinary phone with room for the system bars `screenHeightDp` may or may not
 * be leaving out: the razr reads 2.44 on the whole panel and about 2.34 without them, and both are
 * over. A height threshold cannot do this — an ordinary 20:9 phone at density 2.625 is 411 x 914
 * dp, so any line low enough to catch the razr catches half the phones on sale, and a 376 dp card
 * on a 411 dp window is 91% of the width, which is the *too big* complaint that started r4z.
 *
 * ⚠ **This does not prove the device is a foldable.** The honest test is `androidx.window`'s
 * `FoldingFeature`, which is a dependency and a lifecycle-scoped flow this module does not have. A
 * 21:9 phone sits 0.03 under the line; if one ever turns up drawing the roomy card, that
 * dependency is the answer and this constant is not.
 */
private const val ROOMY_ASPECT = 2.30f

/**
 * And enough width left to draw the thing on.
 *
 * [MANAGER_MAX_WIDTH] is the floor the roomy card is coerced up to, so a window narrower than this
 * has nothing to gain from the tier and would only push a card wider than itself.
 */
private const val ROOMY_TALL_MIN_WIDTH_DP = 340

'''

ASPECT_NEW = ""

TEST_OLD = '''    val windowHeightDp = configuration.screenHeightDp

'''

TEST_NEW = ""

ROOMY_OLD = '''    // How much taller than wide the window is. Guarded against a zero width, which is not a real
    // window but is what a measurement taken too early can be.
    val aspect = if (windowWidthDp > 0) windowHeightDp.toFloat() / windowWidthDp else 0f

    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP ||
        (windowWidthDp >= ROOMY_TALL_MIN_WIDTH_DP && aspect >= ROOMY_ASPECT)
'''

ROOMY_NEW = '''    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP
'''

# The metrics function's own KDoc still describes the clamshell reasoning.
DOC_OLD = '''
 *  1. **Roomy**, decided from the window alone. First, because it is what takes a clamshell's
 *     inner screen out of the physical test — the one place r4z's boundary was two dp from a real
 *     answer.
'''

DOC_NEW = '''
 *  1. **Roomy**, decided from the window's width alone. First, because it is what takes an
 *     unfolded foldable's inner screen out of the physical test, which on that screen was
 *     answering 305 dp — the author's *"looks too small"*.
'''

EDITS = [
    (WIDTH_KDOC_OLD, WIDTH_KDOC_NEW),
    (ASPECT_OLD, ASPECT_NEW),
    (ROOMY_OLD, ROOMY_NEW),
    (TEST_OLD, TEST_NEW),
    (DOC_OLD, DOC_NEW),
]

CHECKS = [
    ("ROOMY_ASPECT", 0, "the aspect clause is gone"),
    ("ROOMY_TALL_MIN_WIDTH_DP", 0, "and its width guard with it"),
    ("windowHeightDp", 0, "height is no longer read at all"),
    ("screenHeightDp", 0, "nor asked of the configuration"),
    ("val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP\n", 1, "one test, one line"),
    ("ROOMY_WINDOW_WIDTH_DP", 2, "declared once, used once"),
    # Untouched by design.
    ("MANAGER_ROOMY_WIDTH = 376.dp", 1, "the roomy width is unchanged"),
    ("MANAGER_COMPACT_WIDTH = 316.dp", 1, "the compact width is unchanged"),
    ("MANAGER_MAX_WIDTH = 340.dp", 1, "the regular width is unchanged"),
    ("COMPACT_WINDOW_WIDTH_DP = 400", 1, "the backstop is unchanged"),
]


def main() -> int:
    path = ROOT / DIALOG

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: anchor {old.strip()[:70]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new and new in original:
            print("REFUSED: already applied — has this run before?")
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:52]!r}")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    added = over(text) - over(original)

    if added:
        print(f"REFUSED: would gain lines over 120 chars: {sorted(added)}")
        return 1

    path.write_text(text, encoding="utf-8")

    print("\n  ok  roomy is the width breakpoint, and the three screens are measured")

    return 0


if __name__ == "__main__":
    sys.exit(main())
