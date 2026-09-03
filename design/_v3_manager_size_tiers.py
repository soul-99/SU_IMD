#!/usr/bin/env python3
"""
v3-r5 — three size tiers for the settings manager, and a real gap between them.

Two reports from the author on r4z:

  1. The card went *small* on the razr fold's inner display. Diagnosed: that screen is tall and
     narrow, so if it reports around 393 dp the physical rule lands at about 338 dp — **two dp
     under the cap** — and `compactCard = width < MANAGER_MAX_WIDTH` then tipped the whole card
     into the compact tier, stepping down every size in it. A one-boolean tier test with its
     boundary sitting on the cap is a knife edge by construction; that is the bug.

  2. On a big screen he wants the card to *use* the room: both action button labels on one line,
     and the elements a step larger. His words: *"on big displays (like razr fold inner screen
     and tablets etc.) it fits both buttons english labels in one line and also the ui elements
     are a bit bigger only for inner display to take advantage of big display area available"*.

So the boolean becomes [ManagerSize]: Compact, Regular, Roomy. Which one is decided **before**
any width is computed, from the window itself, so no tier boundary can sit on a width constant
again. Roomy is tested first, which takes the razr's inner screen out of the physical test
altogether and so out of the knife edge whatever it reports.

## The one-line width is measured, not estimated

Off the author's own S22 Ultra screenshot, at density 3.75:

    the two action buttons span x 120..1319   = 1200 px = 320 dp
      + the Column's 8 dp padding either side =           336 dp  ≈ the 340 dp card. ✓ model good
    ink("Revert to") 207 px, ink("default") 162 px, space advance ~13.6 px
      -> "Revert to default" is ~103 dp of labelLarge

At the button's current `ButtonWithIconContentPadding` that needs 16+18+8+103+24 = 169 dp a
button, and a 340 dp card gives each of them 157 — which is exactly why it wraps today.

The author agreed to trim the button padding to 12 dp a side ("yes lets try that but might undo
this later if i dont like it"), which brings the requirement to **153 dp**, and the tier widths
below are all set above it with headroom.

Every edit asserts its anchor matches the expected number of times. Nothing is written if any
file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = (
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
    "AndroidSettingsManagerDialog.kt"
)

# --- 1. the constants and the rule, replaced wholesale --------------------------------

OLD_RULE_START = "private val MANAGER_MAX_WIDTH = 340.dp\n"

OLD_RULE_END = """        else -> MANAGER_MAX_WIDTH
    }
}
"""

NEW_RULE = '''private val MANAGER_MAX_WIDTH = 340.dp

/**
 * The card the compact tier draws, and the floor under every computed width.
 *
 * ⚠ **Two jobs in one number, and they agree.** It is the author's 300 dp pick from the r4z
 * template rounded up to the narrowest card whose action buttons still read on one line — 316 dp
 * gives each button 145 dp against the 153 dp the pair needs, so there is about 7 dp in hand. He
 * chose 300 before asking for the one-line buttons; 16 dp of width is what they cost, and on his
 * S22 Ultra that is 4% of the window.
 */
private val MANAGER_COMPACT_WIDTH = 316.dp

/**
 * As wide as the roomy tier is ever allowed to get.
 *
 * Enough for both button labels on one line with room to spare, and no more: this is still a
 * dialog over somebody else's app, and a tablet does not want a card that grows with the screen.
 */
private val MANAGER_ROOMY_WIDTH = 376.dp

/**
 * How wide this card should be **in the hand**, in inches.
 *
 * ⚠ **Why the question is put in inches and not in dp.** The manager was right on both screens of
 * the author's razr fold and too big on his S22 Ultra, and his own note said why: the S22 Ultra is
 * the physically *larger* screen of the two he compared. In dp the windows barely differ — 384
 * against about 411 — so no dp threshold puts them on opposite sides of a line. In inches they
 * differ a great deal, because an S22 Ultra at WQHD+ reports density 3.75 against a panel of about
 * 500 ppi: **134 dp to the inch, where the definition of a dp says 160**. Everything drawn in dp
 * is a fifth larger in the hand there than the number says.
 */
private const val MANAGER_TARGET_INCHES = 2.25f

/**
 * The band of dp-per-inch worth believing.
 *
 * `xdpi` is the panel's own number and not every display fills it in honestly: some hand back the
 * density bucket, some report nothing usable. Outside this band the physical test is abandoned
 * rather than trusted, and [COMPACT_WINDOW_WIDTH_DP] answers instead.
 */
private const val MIN_PLAUSIBLE_DP_PER_INCH = 90f

private const val MAX_PLAUSIBLE_DP_PER_INCH = 260f

/**
 * Below this many dp to the inch, the display is drawing dp physically large.
 *
 * ⚠ **This is the tier boundary r4z should have used.** r4z asked instead whether the computed
 * width came out under the cap, which put the boundary two dp from a real device's answer. This
 * one is measured in the quantity the tiers are actually about, and the devices on record sit
 * well clear of it: an S22 Ultra at WQHD+ answers about 134, a razr about 150, and an honest
 * display answers 160 by definition.
 */
private const val COMPACT_DP_PER_INCH = 142f

/**
 * The dp width below which the card goes compact anyway.
 *
 * ⚠ **A backstop, and deliberately the last test.** A display that reports its bucket rather than
 * its panel answers exactly 160 dp to the inch — which is not a measurement, it is the definition
 * restated — and would leave an inflated phone at the full width. So a window narrower than this
 * takes the compact card on the dp reading alone.
 */
private const val COMPACT_WINDOW_WIDTH_DP = 400

/**
 * A window wide enough to be roomy on width alone.
 *
 * The platform's own compact/medium breakpoint: past it there is a tablet or an unfolded
 * book-style foldable on the other side of the glass, whatever its shape.
 */
private const val ROOMY_WINDOW_WIDTH_DP = 600

/**
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

/** What the roomy card leaves at each side, where the other two tiers leave 24. */
private val MANAGER_ROOMY_MARGIN = 16.dp

/** What the other two leave, unchanged since r4k. */
private val MANAGER_MARGIN = 24.dp

/**
 * How much of its natural size each row's switch is drawn at.
 *
 * A Material switch has no size parameter and reserves a 48.dp minimum height; six of them is
 * most of this dialog. Scaling is the only lever, and it is safe here because the whole row takes
 * the press — see [TargetRow].
 */
private const val SWITCH_SCALE = 0.85f

/**
 * The same switch on a compact card.
 *
 * ⚠ **This, not the width, is where the card's height comes out.** Six rows at a 48 dp minimum
 * is most of the dialog, so a step off the switch shortens it in a way no width can.
 */
private const val COMPACT_SWITCH_SCALE = 0.72f

/** And on a roomy one: its natural size, which is what the 48 dp target was drawn for. */
private const val ROOMY_SWITCH_SCALE = 1f

/**
 * What the two action buttons pad their contents with.
 *
 * ⚠ **Trimmed from `ButtonDefaults.ButtonWithIconContentPadding`, at the author's word.** That one
 * is 16 dp before the glyph and 24 dp after the label, which is 16 dp a button more than this and
 * is why `Revert to default` wrapped to two lines on every card narrower than 362 dp — including
 * the author's own S22 Ultra. At 12 dp a side the pair needs 153 dp a button, and every tier below
 * is set above that.
 *
 * ⚠ **Vertical is untouched at 8 dp**, which is Material's own: the wrap was a width problem and
 * shortening the buttons was not asked for.
 */
private val MANAGER_BUTTON_PADDING = PaddingValues(
    start = 12.dp,
    top = 8.dp,
    end = 12.dp,
    bottom = 8.dp,
)

/**
 * How much room this card has, in three named steps.
 *
 * ⚠ **A tier, not a boolean, and r4z's bug is why.** r4z asked one question — is the computed
 * width under the cap — which put the boundary between its two sizes two dp away from what a real
 * device answered, and the author's razr inner screen fell the wrong side of it. Which tier a
 * screen is in is now decided from the window before any width is computed, so no boundary sits
 * on a width constant.
 *
 * Everything that changes with the card's size hangs off here rather than being tested for
 * separately, so the rows, the pill, the title and the buttons cannot come to different
 * conclusions about which size they are drawing.
 */
private enum class ManagerSize {
    /** A display that draws dp physically large, or a window too narrow to say. */
    Compact,

    /** An ordinary phone, and the razr's cover screen. */
    Regular,

    /** A tablet, or a clamshell foldable opened up. */
    Roomy,
}

private val ManagerSize.switchScale: Float
    get() = when (this) {
        ManagerSize.Compact -> COMPACT_SWITCH_SCALE

        ManagerSize.Regular -> SWITCH_SCALE

        ManagerSize.Roomy -> ROOMY_SWITCH_SCALE
    }

/**
 * The breathing space above and below each row.
 *
 * The first thing to go on a small screen — six rows of it is nearly a seventh row's worth of
 * height — and the first thing to come back on a large one.
 */
private val ManagerSize.rowPadding: Dp
    get() = when (this) {
        ManagerSize.Compact -> 0.dp

        ManagerSize.Regular -> 2.dp

        ManagerSize.Roomy -> 4.dp
    }

private val ManagerSize.pillHeight: Dp
    get() = when (this) {
        ManagerSize.Compact -> COMPACT_PILL_HEIGHT

        ManagerSize.Regular -> PILL_HEIGHT

        ManagerSize.Roomy -> ROOMY_PILL_HEIGHT
    }

/**
 * The app icon on the title line.
 *
 * It grows only on the roomy card. On the other two it is already the largest thing on that line
 * and a step down would leave the title looking unattached to it.
 */
private val ManagerSize.appIconSize: Dp
    get() = when (this) {
        ManagerSize.Compact -> 28.dp

        ManagerSize.Regular -> 28.dp

        ManagerSize.Roomy -> 32.dp
    }

/**
 * The card's title.
 *
 * ⚠ **Material has no step between 16 and 22 sp**, so the roomy card's title is a bigger jump than
 * anything else on it. The author saw both this and the variant that left the title alone, in the
 * r5 template, and picked this one.
 */
@Composable
private fun ManagerSize.titleStyle() = when (this) {
    ManagerSize.Compact -> MaterialTheme.typography.titleSmall

    ManagerSize.Regular -> MaterialTheme.typography.titleMedium

    ManagerSize.Roomy -> MaterialTheme.typography.titleLarge
}

@Composable
private fun ManagerSize.rowStyle() = when (this) {
    ManagerSize.Compact -> MaterialTheme.typography.bodySmall

    ManagerSize.Regular -> MaterialTheme.typography.bodyMedium

    ManagerSize.Roomy -> MaterialTheme.typography.bodyLarge
}

@Composable
private fun ManagerSize.pillStyle() = when (this) {
    ManagerSize.Compact -> MaterialTheme.typography.labelSmall

    ManagerSize.Regular -> MaterialTheme.typography.labelMedium

    ManagerSize.Roomy -> MaterialTheme.typography.labelLarge
}

/**
 * The two action buttons' labels.
 *
 * ⚠ **Roomy keeps `labelLarge` rather than stepping up with everything else**, and deliberately:
 * that is Material's button size and there is nothing above it on the label scale, but more to the
 * point the roomy card's whole reason for existing is that both labels fit on one line. Growing
 * the type would spend the width that buys it.
 */
@Composable
private fun ManagerSize.buttonStyle() = when (this) {
    ManagerSize.Compact -> MaterialTheme.typography.labelMedium

    ManagerSize.Regular -> MaterialTheme.typography.labelLarge

    ManagerSize.Roomy -> MaterialTheme.typography.labelLarge
}

/** Which tier this screen is in, how wide the card is, and what it leaves at the sides. */
private data class ManagerMetrics(
    val size: ManagerSize,
    val width: Dp,
    val margin: Dp,
)

/**
 * Which of the three this screen gets, and the card that goes with it.
 *
 * Three tests, in this order, and the order is the whole design:
 *
 *  1. **Roomy**, decided from the window alone. First, because it is what takes a clamshell's
 *     inner screen out of the physical test — the one place r4z's boundary was two dp from a real
 *     answer.
 *  2. **Compact**, decided from how physically large the display draws a dp, with
 *     [COMPACT_WINDOW_WIDTH_DP] behind it for displays that will not say.
 *  3. **Regular** otherwise.
 *
 * ⚠ **Read once, by the dialog.** Nothing else in this file asks the screen anything.
 */
@Composable
private fun managerMetrics(): ManagerMetrics {
    val configuration = LocalConfiguration.current

    val windowWidthDp = configuration.screenWidthDp

    val windowHeightDp = configuration.screenHeightDp

    // dp to the inch: xdpi is pixels to the inch, density is pixels to the dp.
    val xdpi = LocalContext.current.resources.displayMetrics.xdpi

    val dpPerInch = if (xdpi > 0f) xdpi / LocalDensity.current.density else 0f

    val believable = dpPerInch > MIN_PLAUSIBLE_DP_PER_INCH &&
        dpPerInch < MAX_PLAUSIBLE_DP_PER_INCH

    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP ||
        (
            windowWidthDp >= ROOMY_TALL_MIN_WIDTH_DP &&
                windowHeightDp >= ROOMY_TALL_MIN_HEIGHT_DP
            )

    if (roomy) {
        // What the window can actually give at the roomy margin, which on a clamshell's inner
        // screen is less than the cap and is the reason this is a `minOf` and not the cap alone.
        val available = (windowWidthDp - 2 * MANAGER_ROOMY_MARGIN.value.toInt()).dp

        return ManagerMetrics(
            size = ManagerSize.Roomy,
            // Never narrower than an ordinary phone's card: a roomy screen that came out smaller
            // than a regular one would be the r4z bug over again in the other direction.
            width = minOf(MANAGER_ROOMY_WIDTH, available)
                .coerceAtLeast(MANAGER_MAX_WIDTH),
            margin = MANAGER_ROOMY_MARGIN,
        )
    }

    val inflated = believable && dpPerInch < COMPACT_DP_PER_INCH

    if (inflated || windowWidthDp < COMPACT_WINDOW_WIDTH_DP) {
        return ManagerMetrics(
            size = ManagerSize.Compact,
            // The physical answer when there is one, floored so the buttons stay on one line and
            // capped so this tier can never be wider than the regular one.
            width = if (inflated) {
                (MANAGER_TARGET_INCHES * dpPerInch).dp
                    .coerceIn(MANAGER_COMPACT_WIDTH, MANAGER_MAX_WIDTH)
            } else {
                MANAGER_COMPACT_WIDTH
            },
            margin = MANAGER_MARGIN,
        )
    }

    return ManagerMetrics(
        size = ManagerSize.Regular,
        width = MANAGER_MAX_WIDTH,
        margin = MANAGER_MARGIN,
    )
}
'''

# --- 2. the dialog reads the tier -----------------------------------------------------

DECIDE_OLD = '''    // ⚠ **How big this card is, asked once and handed down.** See [managerWidth] for why the
    // question is put in inches rather than in dp. `compactCard` is nothing more than whether
    // that answer came out under the cap — the switches, the type, the row padding and the pill
    // all follow it rather than testing the screen again for themselves.
    val cardWidth = managerWidth()

    val compactCard = cardWidth < MANAGER_MAX_WIDTH
'''

DECIDE_NEW = '''    // ⚠ **How big this card is, asked once and handed down.** See [managerMetrics] for the three
    // tiers and why the question is put in inches rather than in dp. The switches, the type, the
    // row padding, the pill and the app icon all follow `metrics.size` rather than testing the
    // screen again for themselves.
    val metrics = managerMetrics()
'''

MAXWIDTH_OLD = "        maxWidth = cardWidth,\n"

MAXWIDTH_NEW = "        maxWidth = metrics.width,\n"

MARGIN_OLD = '''        // Still here, and not redundant: in a narrow or split-screen window the cap never binds
        // and this is again the only thing keeping the card off the edges.
        horizontalMargin = 24.dp,
'''

MARGIN_NEW = '''        // Still here, and not redundant: in a narrow or split-screen window the cap never binds
        // and this is again the only thing keeping the card off the edges.
        //
        // ⚠ **The roomy tier asks for less of it — r5.** A clamshell's inner screen is tall but
        // no wider than a large phone, so at 24 dp a side there is not enough left for the wider
        // card that tier exists to draw. See [MANAGER_ROOMY_MARGIN].
        horizontalMargin = metrics.margin,
'''

# --- 3. the title row -----------------------------------------------------------------

ICON_OLD = '''                Image(
                    modifier = Modifier
                        .size(28.dp)
                        .clip(CircleShape)
'''

ICON_NEW = '''                Image(
                    modifier = Modifier
                        .size(metrics.size.appIconSize)
                        .clip(CircleShape)
'''

TITLE_OLD = '''                    // One step down, with everything else on this dialog — r4y — and one more
                    // again on a compact card, r4z.
                    style = if (compactCard) {
                        MaterialTheme.typography.titleSmall
                    } else {
                        MaterialTheme.typography.titleMedium
                    },
'''

TITLE_NEW = '''                    // One step down, with everything else on this dialog — r4y — and a step
                    // either way from there with the tier, r5.
                    style = metrics.size.titleStyle(),
'''

# --- 4. the pill ----------------------------------------------------------------------

PILL_CALL_OLD = "                compact = compactCard,\n                enabled = usableTargets.isNotEmpty(),\n"

PILL_CALL_NEW = "                size = metrics.size,\n                enabled = usableTargets.isNotEmpty(),\n"

PILL_SIG_OLD = '''    /** Whether the card was shrunk to fit this screen — see `managerWidth`. */
    compact: Boolean,
    enabled: Boolean,
'''

PILL_SIG_NEW = '''    /** Which tier the card is in — see `managerMetrics`. */
    size: ManagerSize,
    enabled: Boolean,
'''

PILL_HEIGHT_OLD = "            .height(if (compact) COMPACT_PILL_HEIGHT else PILL_HEIGHT),\n"

PILL_HEIGHT_NEW = "            .height(size.pillHeight),\n"

PILL_HALF_CALL_OLD = "            compact = compact,\n"

PILL_HALF_CALL_NEW = "            size = size,\n"

PILL_HALF_SIG_OLD = '''private fun PillHalf(
    modifier: Modifier = Modifier,
    compact: Boolean,
    label: String,
'''

PILL_HALF_SIG_NEW = '''private fun PillHalf(
    modifier: Modifier = Modifier,
    size: ManagerSize,
    label: String,
'''

PILL_LABEL_OLD = '''            Text(
                text = label,
                style = if (compact) {
                    MaterialTheme.typography.labelSmall
                } else {
                    MaterialTheme.typography.labelMedium
                },
            )
'''

PILL_LABEL_NEW = '''            Text(text = label, style = size.pillStyle())
'''

PILL_CONST_OLD = '''private val COMPACT_PILL_HEIGHT = 24.dp
'''

PILL_CONST_NEW = '''private val COMPACT_PILL_HEIGHT = 24.dp

/** And on a roomy one. The shapes are untouched for the same reason. */
private val ROOMY_PILL_HEIGHT = 32.dp
'''

# --- 5. the rows ----------------------------------------------------------------------

ROW_CALL_OLD = "                TargetRow(\n                    compact = compactCard,\n"

ROW_CALL_NEW = "                TargetRow(\n                    size = metrics.size,\n"

ROW_SIG_OLD = '''    /**
     * Whether the card was shrunk to fit this screen — see `managerWidth`.
     *
     * ⚠ **Passed in, like [isShevery] and for the same reason.** The dialog asks the screen
     * once; a row that measured for itself could draw at a size the card beneath it is not.
     */
    compact: Boolean,
'''

ROW_SIG_NEW = '''    /**
     * Which tier the card is in — see `managerMetrics`.
     *
     * ⚠ **Passed in, like [isShevery] and for the same reason.** The dialog asks the screen
     * once; a row that measured for itself could draw at a size the card beneath it is not.
     */
    size: ManagerSize,
'''

ROW_BODY_OLD = '''    val switchScale = if (compact) COMPACT_SWITCH_SCALE else SWITCH_SCALE

    // The row's own breathing space, and the first thing to go on a small screen: six rows of
    // it is nearly a seventh row's worth of height.
    val rowPadding = if (compact) 0.dp else 2.dp
'''

ROW_BODY_NEW = '''    val switchScale = size.switchScale

    val rowPadding = size.rowPadding
'''

ROW_LABEL_OLD = '''                    style = if (compact) {
                        MaterialTheme.typography.bodySmall
                    } else {
                        MaterialTheme.typography.bodyMedium
                    },
'''

ROW_LABEL_NEW = '''                    style = size.rowStyle(),
'''

# --- 6. the action buttons ------------------------------------------------------------

ACTION_HIDE_OLD = '''                    compact = compactCard,
                    glyph = if (anythingHidden) {
'''

ACTION_HIDE_NEW = '''                    size = metrics.size,
                    glyph = if (anythingHidden) {
'''

ACTION_REVERT_OLD = '''                    compact = compactCard,
                    glyph = designR.drawable.ic_revert_glyph,
'''

ACTION_REVERT_NEW = '''                    size = metrics.size,
                    glyph = designR.drawable.ic_revert_glyph,
'''

ACTION_SIG_OLD = '''    /** Whether the card was shrunk to fit this screen — see `managerWidth`. */
    compact: Boolean,
    @DrawableRes glyph: Int,
'''

ACTION_SIG_NEW = '''    /** Which tier the card is in — see `managerMetrics`. */
    size: ManagerSize,
    @DrawableRes glyph: Int,
'''

ACTION_PADDING_OLD = '''            // ⚠ **The icon variant, which is what these buttons are.** Material's plain
            // `ContentPadding` is 24dp on both sides and assumes text alone; every button
            // here has a glyph in front of its label, and the icon padding is 16dp before it.
            // The 8dp a button that saves is what lets `Revert to default` sit on one line on
            // a 411dp phone, where the pair had about 373dp of a 379dp card and nothing over.
            modifier = Modifier.padding(ButtonDefaults.ButtonWithIconContentPadding),
'''

ACTION_PADDING_NEW = '''            // ⚠ **Trimmed past Material's icon variant — r5, at the author's word.** The icon
            // padding is 16 dp before the glyph and 24 dp after the label, which was still not
            // enough: `Revert to default` measures about 103 dp of labelLarge, so at that padding
            // a button needs 169 dp and the pair needs a 362 dp card — wider than any tier below
            // roomy, which is why it wrapped to two lines on the author's own S22 Ultra.
            //
            // At 12 dp a side a button needs 153 dp, and every tier is set above it. See
            // [MANAGER_BUTTON_PADDING].
            modifier = Modifier.padding(MANAGER_BUTTON_PADDING),
'''

ACTION_LABEL_OLD = '''                // ⚠ **A step down here buys two things on a narrow card, not one.** The
                // shorter label is the obvious one; the other is that `Revert to default`
                // stops wrapping to two lines sooner, and the pair is drawn at
                // `IntrinsicSize.Min`, so the taller of the two sets the height of both.
                style = if (compact) {
                    MaterialTheme.typography.labelMedium
                } else {
                    MaterialTheme.typography.labelLarge
                },
'''

ACTION_LABEL_NEW = '''                // ⚠ **A step down on the compact card buys two things, not one.** The shorter
                // label is the obvious one; the other is that `Revert to default` stops wrapping
                // sooner, and the pair is drawn at `IntrinsicSize.Min`, so the taller of the two
                // sets the height of both.
                style = size.buttonStyle(),
'''

# --- 7. imports -----------------------------------------------------------------------

IMPORT_OLD = "import androidx.compose.foundation.layout.Row\n"

IMPORT_NEW = (
    "import androidx.compose.foundation.layout.PaddingValues\n"
    "import androidx.compose.foundation.layout.Row\n"
)

# (old, new, times)
EDITS = [
    (IMPORT_OLD, IMPORT_NEW, 1),
    (DECIDE_OLD, DECIDE_NEW, 1),
    (MAXWIDTH_OLD, MAXWIDTH_NEW, 1),
    (MARGIN_OLD, MARGIN_NEW, 1),
    (ICON_OLD, ICON_NEW, 1),
    (TITLE_OLD, TITLE_NEW, 1),
    (PILL_CALL_OLD, PILL_CALL_NEW, 1),
    (PILL_SIG_OLD, PILL_SIG_NEW, 1),
    (PILL_HEIGHT_OLD, PILL_HEIGHT_NEW, 1),
    (PILL_HALF_CALL_OLD, PILL_HALF_CALL_NEW, 2),
    (PILL_HALF_SIG_OLD, PILL_HALF_SIG_NEW, 1),
    (PILL_LABEL_OLD, PILL_LABEL_NEW, 1),
    (PILL_CONST_OLD, PILL_CONST_NEW, 1),
    (ROW_CALL_OLD, ROW_CALL_NEW, 1),
    (ROW_SIG_OLD, ROW_SIG_NEW, 1),
    (ROW_BODY_OLD, ROW_BODY_NEW, 1),
    (ROW_LABEL_OLD, ROW_LABEL_NEW, 1),
    (ACTION_HIDE_OLD, ACTION_HIDE_NEW, 1),
    (ACTION_REVERT_OLD, ACTION_REVERT_NEW, 1),
    (ACTION_SIG_OLD, ACTION_SIG_NEW, 1),
    (ACTION_PADDING_OLD, ACTION_PADDING_NEW, 1),
    (ACTION_LABEL_OLD, ACTION_LABEL_NEW, 1),
]

CHECKS = [
    ("private enum class ManagerSize {", 1, "the tier exists"),
    ("private fun managerMetrics(): ManagerMetrics {", 1, "the rule exists"),
    ("private fun managerWidth(): Dp {", 0, "r4z's two-way rule is gone"),
    ("val metrics = managerMetrics()", 1, "the dialog asks once"),
    ("compactCard", 0, "nothing reads the old boolean"),
    ("compact: Boolean,", 0, "no composable takes it any more"),
    # ⚠ Spelled with its indent and no `val`: `size: ManagerSize,` on its own also matches
    # inside `ManagerMetrics`'s own field, which is not a composable parameter.
    ("\n    size: ManagerSize,", 4, "four composables take the tier"),
    ("size = metrics.size,", 4, "row, pill and both action buttons are told"),
    ("size = size,", 2, "and the pill passes it to its two halves"),
    ("ManagerSize.Compact ->", 8, "eight things step with the tier"),
    ("ManagerSize.Regular ->", 8, "and each names all three arms"),
    ("ManagerSize.Roomy ->", 8, "with nothing left to a default"),
    ("MANAGER_BUTTON_PADDING", 3, "the trimmed padding is declared, referenced and used"),
    # Once: the KDoc on MANAGER_BUTTON_PADDING naming what it was trimmed from. Never as code.
    ("ButtonWithIconContentPadding", 1, "Material's padding is named but no longer used"),
    ("Modifier.padding(ButtonDefaults.ButtonWithIconContentPadding)", 0, "and not applied"),
    # Untouched by design.
    ("MANAGER_MAX_WIDTH = 340.dp", 1, "the regular width is unchanged"),
    ("SWITCH_SCALE = 0.85f", 1, "the regular switch scale is unchanged"),
    ("PILL_HEIGHT = 28.dp", 1, "the regular pill height is unchanged"),
]


def main() -> int:
    path = ROOT / DIALOG

    if not path.is_file():
        print(f"REFUSED: missing {DIALOG}")
        return 1

    original = path.read_text(encoding="utf-8")

    # ⚠ The rule block is replaced by span rather than by anchor: it is a hundred lines of
    # KDoc and code, and pasting it in whole would be a hundred lines of this script that
    # have to stay byte-identical to the file to match at all.
    start = original.find(OLD_RULE_START)

    end = original.find(OLD_RULE_END)

    if start < 0 or end < 0 or end < start:
        print("REFUSED: could not locate r4z's width rule to replace")
        return 1

    if original.count(OLD_RULE_START) != 1 or original.count(OLD_RULE_END) != 1:
        print("REFUSED: the rule block's bounds are not unique")
        return 1

    text = original[:start] + NEW_RULE + original[end + len(OLD_RULE_END):]

    report = [f"  ok        replaced the width rule ({end + len(OLD_RULE_END) - start} chars)"]

    for old, new, times in EDITS:
        found = text.count(old)

        if found != times:
            print(
                f"REFUSED: anchor {old.strip()[:66]!r}\n"
                f"  matched {found} time(s), expected {times}",
            )
            return 1

        if new in original:
            print(f"REFUSED: {new.strip()[:66]!r} is already there — has this run before?")
            return 1

        text = text.replace(old, new)

        report.append(f"  ok       x{times}  {old.strip().splitlines()[0][:60]}")

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        report.append(f"  checked  x{got:<3} {token[:56]!r}")

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

    print("\n".join(report))

    print(f"\nwrote 1 file, {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
