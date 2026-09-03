#!/usr/bin/env python3
"""
v3-r4z — size the settings manager against the screen it is physically on.

The author's report, across three screens he owns:

    razr fold, inner screen   ~411 x 1005 dp, ~6.9"   good
    razr fold, cover screen   ~411 x  484 dp, ~4.0"   good
    S22 Ultra                  384 x  823 dp,  6.8"   too big

and his own observation with it: *"physically the s22 ultra screen is larger than the moto
razr fold's outer screen, thats also why the window looks too big on it"*.

⚠ **No dp rule explains those three lines**, and that is the point of this script. In dp the
three windows barely differ — 384 against 411 — so a width threshold has to sit in a 27 dp gap,
and a *height* threshold (the shape r4z first proposed) puts the cover screen on the wrong side
of the line, because it is short. In inches they differ enormously, and the odd one out is the
S22 Ultra: at WQHD+ it reports density 3.75 against a panel of roughly 500 ppi, so it draws
about 134 dp to the inch where the definition of a dp says 160. Everything measured in dp comes
out a fifth larger in the hand there than the number says. That is the whole complaint.

So the card asks for a width in **inches** and converts, with the dp cap kept as a ceiling and a
dp width threshold kept only as a backstop for displays that will not say how big they are.

The author picked size C from the r4z template: 300 dp on his S22 Ultra, with a step out of the
switches, the title, the row padding and the pill so the card shortens as well as narrows.
Everything the compact card changes hangs off one `compactCard` boolean computed from the width,
so no two parts of the dialog can disagree about which size they are drawing.

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

# --- 1. imports ----------------------------------------------------------------------

IMPORT_PLATFORM_OLD = "import androidx.compose.ui.platform.LocalContext\n"

IMPORT_PLATFORM_NEW = (
    "import androidx.compose.ui.platform.LocalConfiguration\n"
    "import androidx.compose.ui.platform.LocalContext\n"
    "import androidx.compose.ui.platform.LocalDensity\n"
)

IMPORT_UNIT_OLD = "import androidx.compose.ui.unit.dp\n"

IMPORT_UNIT_NEW = (
    "import androidx.compose.ui.unit.Dp\n"
    "import androidx.compose.ui.unit.dp\n"
)

# --- 2. the widths, and the rule that picks between them ------------------------------

WIDTH_OLD = "private val MANAGER_MAX_WIDTH = 340.dp\n"

WIDTH_NEW = '''private val MANAGER_MAX_WIDTH = 340.dp

/**
 * The same card once [managerWidth] has found this screen to be one of the inflated ones.
 *
 * The author's pick from the r4z size template, drawn on his own S22 Ultra's real window: 300 dp
 * of 384 is 78% of the width where the cap alone left it at 88.5%.
 */
private val MANAGER_COMPACT_WIDTH = 300.dp

/**
 * The floor under [managerWidth].
 *
 * A guard rather than a size: nothing has ever asked for a card this narrow, and this is only
 * here so that a display reporting a wild `xdpi` inside the believable band cannot shrink the
 * card to a strip.
 */
private val MANAGER_MIN_WIDTH = 260.dp

/**
 * How wide this card should be **in the hand**, in inches.
 *
 * ⚠ **This is the whole of r4z's fix, and it is worth reading why it is not a dp number.** The
 * manager was right on both screens of the author's razr fold and too big on his S22 Ultra, and
 * his own note said why: the S22 Ultra is the physically *larger* screen of the two he compared.
 * In dp the three windows barely differ — 384 dp against about 411 dp — so no dp threshold puts
 * all three on the right side of a line. In inches they differ a great deal, because an S22
 * Ultra at WQHD+ reports density 3.75 against a panel of about 500 ppi: **134 dp to the inch,
 * where the definition of a dp says 160**. Everything drawn in dp is a fifth larger in the hand
 * there than the number says, which is exactly the complaint and exactly what a dp cap cannot
 * see.
 *
 * 2.25 is [MANAGER_MAX_WIDTH] at an honest 160 dp to the inch, less the step the author asked
 * for. It lands on [MANAGER_COMPACT_WIDTH] on his S22 Ultra and above the cap — so unchanged —
 * on both of the razr's screens, which is what he asked for.
 */
private const val MANAGER_TARGET_INCHES = 2.25f

/**
 * The band of dp-per-inch worth believing.
 *
 * `xdpi` is the panel's own number and not every display fills it in honestly: some hand back
 * the density bucket, some report nothing usable. Outside this band the physical test is
 * abandoned rather than trusted, and [COMPACT_WINDOW_WIDTH_DP] answers instead.
 */
private const val MIN_PLAUSIBLE_DP_PER_INCH = 90f

private const val MAX_PLAUSIBLE_DP_PER_INCH = 260f

/**
 * The dp width below which the card goes compact anyway.
 *
 * ⚠ **A backstop, and deliberately the second test.** A display that reports its bucket rather
 * than its panel answers exactly 160 dp to the inch — which is not a measurement, it is the
 * definition restated — and would leave an inflated phone at the full width. So a window
 * narrower than this takes the compact card on the dp reading alone.
 *
 * 400 sits between an S22 Ultra's 384 and a razr's 411, which is the only pair of measurements
 * on record. It is a knife edge, and that is why it is reached only when the display will not
 * say how big it physically is.
 */
private const val COMPACT_WINDOW_WIDTH_DP = 400
'''

SCALE_OLD = "private const val SWITCH_SCALE = 0.85f\n"

SCALE_NEW = '''private const val SWITCH_SCALE = 0.85f

/**
 * The same switch on a compact card.
 *
 * ⚠ **This, not the width, is where the card's height comes out.** Six rows at a 48 dp minimum
 * is most of the dialog, so a step off the switch shortens it in a way no width can.
 */
private const val COMPACT_SWITCH_SCALE = 0.72f

/**
 * How wide the card is on the screen it is actually being drawn on.
 *
 * Two tests in order, and the order is the point. The first asks the display how physically wide
 * its window is and sizes the card in inches — see [MANAGER_TARGET_INCHES] for why that is the
 * honest question. The second is [COMPACT_WINDOW_WIDTH_DP], reached only when the display
 * declined to answer or answered that the cap is fine in the hand.
 *
 * ⚠ **Read once, by the dialog**, which then hands `compactCard` down to everything that
 * shrinks. Nothing else in this file tests the screen for itself, so no two parts of the card
 * can come to different conclusions about which size they are.
 */
@Composable
private fun managerWidth(): Dp {
    val windowWidthDp = LocalConfiguration.current.screenWidthDp

    // dp to the inch: xdpi is pixels to the inch, density is pixels to the dp.
    val xdpi = LocalContext.current.resources.displayMetrics.xdpi

    val dpPerInch = if (xdpi > 0f) xdpi / LocalDensity.current.density else 0f

    val believable = dpPerInch > MIN_PLAUSIBLE_DP_PER_INCH &&
        dpPerInch < MAX_PLAUSIBLE_DP_PER_INCH

    val physical = if (believable) (MANAGER_TARGET_INCHES * dpPerInch).dp else null

    return when {
        // The display answered, and what it said is that the cap is too wide in the hand here.
        physical != null && physical < MANAGER_MAX_WIDTH ->
            physical.coerceAtLeast(MANAGER_MIN_WIDTH)

        // It would not answer, or it says the cap is fine. The backstop has the last word.
        windowWidthDp < COMPACT_WINDOW_WIDTH_DP -> MANAGER_COMPACT_WIDTH

        else -> MANAGER_MAX_WIDTH
    }
}
'''

# The KDoc above SWITCH_SCALE points at a composable that was renamed. Fixed in passing
# because this script is rewriting the paragraph under it either way.
STALE_LINK_OLD = "the press — see [SettingRow].\n"

STALE_LINK_NEW = "the press — see [TargetRow].\n"

# --- 3. the dialog decides once, and passes it down ------------------------------------

DECIDE_OLD = '''    LaunchedEffect(shizukuRunning) {
        if (shizukuRunning) shizukuAttempts = 0
    }

    DialogContainer(
'''

DECIDE_NEW = '''    LaunchedEffect(shizukuRunning) {
        if (shizukuRunning) shizukuAttempts = 0
    }

    // ⚠ **How big this card is, asked once and handed down.** See [managerWidth] for why the
    // question is put in inches rather than in dp. `compactCard` is nothing more than whether
    // that answer came out under the cap — the switches, the type, the row padding and the pill
    // all follow it rather than testing the screen again for themselves.
    val cardWidth = managerWidth()

    val compactCard = cardWidth < MANAGER_MAX_WIDTH

    DialogContainer(
'''

MAXWIDTH_OLD = "        maxWidth = MANAGER_MAX_WIDTH,\n"

MAXWIDTH_NEW = "        maxWidth = cardWidth,\n"

# --- 4. the title -----------------------------------------------------------------------

TITLE_OLD = '''                Text(
                    text = stringResource(R.string.settings_manager_title),
                    // One step down, with everything else on this dialog — r4y.
                    style = MaterialTheme.typography.titleMedium,
                )
'''

TITLE_NEW = '''                Text(
                    text = stringResource(R.string.settings_manager_title),
                    // One step down, with everything else on this dialog — r4y — and one more
                    // again on a compact card, r4z.
                    style = if (compactCard) {
                        MaterialTheme.typography.titleSmall
                    } else {
                        MaterialTheme.typography.titleMedium
                    },
                )
'''

# --- 5. the master pill -----------------------------------------------------------------

PILL_CALL_OLD = '''            MasterPill(
                enabled = usableTargets.isNotEmpty(),
'''

PILL_CALL_NEW = '''            MasterPill(
                compact = compactCard,
                enabled = usableTargets.isNotEmpty(),
'''

PILL_SIG_OLD = '''private fun MasterPill(
    modifier: Modifier = Modifier,
    enabled: Boolean,
'''

PILL_SIG_NEW = '''private fun MasterPill(
    modifier: Modifier = Modifier,
    /** Whether the card was shrunk to fit this screen — see `managerWidth`. */
    compact: Boolean,
    enabled: Boolean,
'''

PILL_HEIGHT_OLD = '''            .height(PILL_HEIGHT),
'''

PILL_HEIGHT_NEW = '''            .height(if (compact) COMPACT_PILL_HEIGHT else PILL_HEIGHT),
'''

PILL_HALF_CALL_OLD = '''        PillHalf(
            modifier = Modifier.weight(1f),
            label = stringResource(R.string.settings_manager_all_'''

PILL_HALF_CALL_NEW = '''        PillHalf(
            modifier = Modifier.weight(1f),
            compact = compact,
            label = stringResource(R.string.settings_manager_all_'''

PILL_HALF_SIG_OLD = '''private fun PillHalf(
    modifier: Modifier = Modifier,
    label: String,
'''

PILL_HALF_SIG_NEW = '''private fun PillHalf(
    modifier: Modifier = Modifier,
    compact: Boolean,
    label: String,
'''

PILL_LABEL_OLD = '''            Text(text = label, style = MaterialTheme.typography.labelMedium)
'''

PILL_LABEL_NEW = '''            Text(
                text = label,
                style = if (compact) {
                    MaterialTheme.typography.labelSmall
                } else {
                    MaterialTheme.typography.labelMedium
                },
            )
'''

PILL_CONST_OLD = "private val PILL_HEIGHT = 28.dp\n"

PILL_CONST_NEW = '''private val PILL_HEIGHT = 28.dp

/**
 * The same row on a compact card.
 *
 * ⚠ **The shapes are not touched.** [PILL_START_SHAPE]'s 14 dp is half of [PILL_HEIGHT], and a
 * corner radius larger than half the height is clamped to half the height where it is drawn —
 * so at 24 dp the ends stay exactly as round as they look now, with one number to change rather
 * than five.
 */
private val COMPACT_PILL_HEIGHT = 24.dp
'''

# --- 6. the rows ------------------------------------------------------------------------

ROW_CALL_OLD = '''                TargetRow(
                    isShevery = isShevery,
'''

ROW_CALL_NEW = '''                TargetRow(
                    compact = compactCard,
                    isShevery = isShevery,
'''

ROW_SIG_OLD = '''private fun TargetRow(
    modifier: Modifier = Modifier,
    target: ManualRevertTarget,
'''

ROW_SIG_NEW = '''private fun TargetRow(
    modifier: Modifier = Modifier,
    /**
     * Whether the card was shrunk to fit this screen — see `managerWidth`.
     *
     * ⚠ **Passed in, like [isShevery] and for the same reason.** The dialog asks the screen
     * once; a row that measured for itself could draw at a size the card beneath it is not.
     */
    compact: Boolean,
    target: ManualRevertTarget,
'''

ROW_BODY_OLD = '''    var showFailureHelp by rememberSaveable { mutableStateOf(false) }

    Row(
'''

ROW_BODY_NEW = '''    var showFailureHelp by rememberSaveable { mutableStateOf(false) }

    val switchScale = if (compact) COMPACT_SWITCH_SCALE else SWITCH_SCALE

    // The row's own breathing space, and the first thing to go on a small screen: six rows of
    // it is nearly a seventh row's worth of height.
    val rowPadding = if (compact) 0.dp else 2.dp

    Row(
'''

ROW_PADDING_OLD = '''            .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
'''

ROW_PADDING_NEW = '''            .padding(start = 4.dp, top = rowPadding, bottom = rowPadding),
'''

ROW_LABEL_OLD = '''                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(isShevery = isShevery),
                    style = MaterialTheme.typography.bodyMedium,
                )
'''

ROW_LABEL_NEW = '''                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(isShevery = isShevery),
                    style = if (compact) {
                        MaterialTheme.typography.bodySmall
                    } else {
                        MaterialTheme.typography.bodyMedium
                    },
                )
'''

ROW_SWITCH_OLD = "                modifier = Modifier.scale(SWITCH_SCALE),\n"

ROW_SWITCH_NEW = "                modifier = Modifier.scale(switchScale),\n"

ROW_SWITCH_DEAD_OLD = "                    modifier = Modifier.scale(SWITCH_SCALE),\n"

ROW_SWITCH_DEAD_NEW = "                    modifier = Modifier.scale(switchScale),\n"

# --- 7. the two action buttons -----------------------------------------------------------

ACTION_HIDE_OLD = '''                    glyph = if (anythingHidden) {
                        designR.drawable.ic_hide_glyph
'''

ACTION_HIDE_NEW = '''                    compact = compactCard,
                    glyph = if (anythingHidden) {
                        designR.drawable.ic_hide_glyph
'''

ACTION_REVERT_OLD = '''                    glyph = designR.drawable.ic_revert_glyph,
'''

ACTION_REVERT_NEW = '''                    compact = compactCard,
                    glyph = designR.drawable.ic_revert_glyph,
'''

ACTION_SIG_OLD = '''private fun ActionButton(
    modifier: Modifier = Modifier,
    @DrawableRes glyph: Int,
'''

ACTION_SIG_NEW = '''private fun ActionButton(
    modifier: Modifier = Modifier,
    /** Whether the card was shrunk to fit this screen — see `managerWidth`. */
    compact: Boolean,
    @DrawableRes glyph: Int,
'''

ACTION_LABEL_OLD = '''                style = MaterialTheme.typography.labelLarge,
'''

ACTION_LABEL_NEW = '''                // ⚠ **A step down here buys two things on a narrow card, not one.** The
                // shorter label is the obvious one; the other is that `Revert to default`
                // stops wrapping to two lines sooner, and the pair is drawn at
                // `IntrinsicSize.Min`, so the taller of the two sets the height of both.
                style = if (compact) {
                    MaterialTheme.typography.labelMedium
                } else {
                    MaterialTheme.typography.labelLarge
                },
'''

# (old, new, times)
EDITS = [
    (IMPORT_PLATFORM_OLD, IMPORT_PLATFORM_NEW, 1),
    (IMPORT_UNIT_OLD, IMPORT_UNIT_NEW, 1),
    (WIDTH_OLD, WIDTH_NEW, 1),
    (STALE_LINK_OLD, STALE_LINK_NEW, 1),
    (SCALE_OLD, SCALE_NEW, 1),
    (DECIDE_OLD, DECIDE_NEW, 1),
    (MAXWIDTH_OLD, MAXWIDTH_NEW, 1),
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
    (ROW_PADDING_OLD, ROW_PADDING_NEW, 1),
    (ROW_LABEL_OLD, ROW_LABEL_NEW, 1),
    # ⚠ The dead switch's line is the live one's with four more spaces, so the live spelling
    # matches inside it. The deeper one is replaced first, and the shallower one is then
    # asserted to match exactly once — which it only can once the other is gone.
    (ROW_SWITCH_DEAD_OLD, ROW_SWITCH_DEAD_NEW, 1),
    (ROW_SWITCH_OLD, ROW_SWITCH_NEW, 1),
    (ACTION_HIDE_OLD, ACTION_HIDE_NEW, 1),
    (ACTION_REVERT_OLD, ACTION_REVERT_NEW, 1),
    (ACTION_SIG_OLD, ACTION_SIG_NEW, 1),
    (ACTION_LABEL_OLD, ACTION_LABEL_NEW, 1),
]

# Spelled the way only the statement meant can be spelled — see the handover's comment trap.
CHECKS = [
    ("private fun managerWidth(): Dp {", 1, "the rule exists"),
    ("val cardWidth = managerWidth()", 1, "the dialog asks once"),
    ("val compactCard = cardWidth < MANAGER_MAX_WIDTH", 1, "and derives compact from it"),
    ("maxWidth = cardWidth,", 1, "the container is given the computed width"),
    ("maxWidth = MANAGER_MAX_WIDTH,", 0, "and no longer the raw cap"),
    ("compact = compactCard,", 4, "row, pill and both action buttons are told"),
    ("compact = compact,", 2, "and the pill passes it to its two halves"),
    ("Modifier.scale(SWITCH_SCALE)", 0, "no switch reads the constant directly any more"),
    ("Modifier.scale(switchScale)", 2, "both switches read the row's own value"),
    ("compact: Boolean,", 4, "four composables take the flag"),
    ("if (compact)", 6, "six things shrink with it"),
    ("[SettingRow]", 0, "the stale KDoc link is gone"),
    # Untouched by design, and each is a thing a slip here would silently break.
    ("SWITCH_SCALE = 0.85f", 1, "the roomy switch scale is unchanged"),
    ("MANAGER_MAX_WIDTH = 340.dp", 1, "the cap is unchanged"),
    ("horizontalMargin = 24.dp,", 1, "the margin is unchanged"),
    ("PILL_HEIGHT = 28.dp", 1, "the roomy pill height is unchanged"),
]


def main() -> int:
    path = ROOT / DIALOG

    if not path.is_file():
        print(f"REFUSED: missing {DIALOG}")
        return 1

    original = path.read_text(encoding="utf-8")

    text = original

    report: list[str] = []

    for old, new, times in EDITS:
        found = text.count(old)

        if found != times:
            print(
                f"REFUSED: anchor {old.strip()[:66]!r}\n"
                f"  matched {found} time(s), expected {times}",
            )
            return 1

        # ⚠ Against the file as it arrived, not against the running text. Two of these edits
        # are the same statement at two indents — the deeper one carries the shallower one
        # inside it — so once the first has landed, the second's replacement is legitimately
        # already present in `text` and a check against `text` would refuse a correct run.
        if new in original:
            print(
                f"REFUSED: {new.strip()[:66]!r} is already there — has this run before?",
            )
            return 1

        text = text.replace(old, new)

        report.append(f"  ok       x{times}  {old.strip().splitlines()[0][:60]}")

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        report.append(f"  checked  x{got:<3} {token[:58]!r}")

    # ⚠ Against what the file already carried, not against zero — see the sibling script.
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

    print(f"\nwrote 1 file, {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
