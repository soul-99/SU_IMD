#!/usr/bin/env python3
"""
v3-r5 — decide the roomy tier by the window's shape, not by its height in dp.

`_v3_manager_size_tiers.py` shipped the roomy test as `height >= 880 dp`. Exercised against a
compiled model of the same expression, that is wrong twice:

    pixel-class phone   411 x 914 dp  ->  Roomy   ✗ an ordinary phone, and a 376 dp card on a
                                                    411 dp window is 91% of the width — which is
                                                    the *too big* complaint that started r4z
    S22 Ultra at FHD+   411 x 883 dp  ->  Roomy   ✗ the very device the compact tier is for

An ordinary 20:9 phone at density 2.625 is 411 x 914, so a height threshold low enough to catch a
clamshell's inner screen catches half the phones on sale with it. Raising it does not help either:
the gap between 914 and a razr's ~960 is smaller than the error in my guess at the razr's density,
which is the third round in a row that guess has been load-bearing.

## Shape is density-independent, which is the whole point

    razr fold, inner   2640 / 1080  =  2.44        <- and the same at *any* density
    Xperia-class 21:9  3840 / 1644  =  2.33
    ordinary 20:9      2400 / 1080  =  2.22
    S22 Ultra          3088 / 1440  =  2.14
    razr fold, cover    484 /  411  =  1.18

A ratio survives whatever density Motorola picked, so it is the one test here that does not rest
on a spec sheet. 2.30 sits clear of every ordinary phone above and takes the bars `screenHeightDp`
may or may not be excluding into account — the razr reads 2.44 with the whole panel and about 2.34
without the system bars, and both are over.

⚠ **What it does not do is prove the device is a foldable.** The honest test for that is
`androidx.window`'s `FoldingFeature`, which is a dependency and a lifecycle-scoped flow this
module does not have. A 21:9 phone sits 0.03 under the line. If one ever turns up drawing the
roomy card, that dependency is the proper answer and this constant is not.

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

CONST_OLD = '''/**
 * And the tall, narrow window that is also roomy: a clamshell foldable opened up.
 *
 * ⚠ **Height is what separates it from a large phone**, and nothing else does. The author's razr
 * inner screen is about 393 x 960 dp and his S22 Ultra 384 x 823 — nine dp apart across, but a
 * hundred and forty down. The width test alongside it is only there so the card still has
 * somewhere to be drawn.
 *
 * ⚠ **Not yet measured.** These two numbers are read off the razr's spec sheet, not off a
 * screenshot, and they are the one part of this file taken on trust. 880 leaves 57 dp of daylight
 * above the S22 Ultra, which is the nearest device on the other side.
 */
private const val ROOMY_TALL_MIN_HEIGHT_DP = 880

private const val ROOMY_TALL_MIN_WIDTH_DP = 380
'''

CONST_NEW = '''/**
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

TEST_OLD = '''    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP ||
        (
            windowWidthDp >= ROOMY_TALL_MIN_WIDTH_DP &&
                windowHeightDp >= ROOMY_TALL_MIN_HEIGHT_DP
            )
'''

TEST_NEW = '''    // How much taller than wide the window is. Guarded against a zero width, which is not a real
    // window but is what a measurement taken too early can be.
    val aspect = if (windowWidthDp > 0) windowHeightDp.toFloat() / windowWidthDp else 0f

    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP ||
        (windowWidthDp >= ROOMY_TALL_MIN_WIDTH_DP && aspect >= ROOMY_ASPECT)
'''

EDITS = [
    (CONST_OLD, CONST_NEW),
    (TEST_OLD, TEST_NEW),
]

CHECKS = [
    ("ROOMY_TALL_MIN_HEIGHT_DP", 0, "the height threshold is gone"),
    ("private const val ROOMY_ASPECT = 2.30f", 1, "the shape test is declared"),
    ("aspect >= ROOMY_ASPECT", 1, "and used, once"),
    ("ROOMY_TALL_MIN_WIDTH_DP = 340", 1, "the width guard is the coercion floor"),
    ("windowHeightDp", 2, "height is read once and used once, in the ratio"),
    ("ROOMY_WINDOW_WIDTH_DP", 2, "the tablet route is untouched: declared once, used once"),
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

        if new in original:
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

    print("\n  ok  roomy is decided by the window's shape")

    return 0


if __name__ == "__main__":
    sys.exit(main())
