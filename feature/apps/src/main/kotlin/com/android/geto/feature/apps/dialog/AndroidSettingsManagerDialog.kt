/*
 *
 *   Copyright 2023 Einstein Blanco
 *   Modifications Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 *   Unless required by applicable law or agreed to in writing, software
 *   distributed under the License is distributed on an "AS IS" BASIS,
 *   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *   See the License for the specific language governing permissions and
 *   limitations under the License.
 *
 */
package com.android.geto.feature.apps.dialog

import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
import androidx.compose.foundation.ExperimentalFoundationApi
import androidx.compose.foundation.clickable
import androidx.compose.foundation.combinedClickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import kotlinx.coroutines.delay
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.compositeOver
import androidx.compose.ui.graphics.Shape
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.android.geto.designsystem.component.GetoSwitch
import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer
import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.theme.GetoRed
import com.android.geto.domain.model.ManagerRows
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.ManualTargetStates
import com.android.geto.domain.usecase.SettingsWorkKind
import com.android.geto.feature.apps.R
import com.android.geto.designsystem.R as designR

/** Enough failed attempts to conclude the user is not going to succeed by trying again. */
private const val SHIZUKU_ATTEMPTS_BEFORE_HELP = 2

/**
 * Where each row is drawn in the settings manager, top to bottom.
 *
 * ⚠ **Display order only.** [ManualRevertTarget.entries] is what every *apply* path
 * follows - `masterPillOnOrder` in :domain:model above all, which puts Shizuku before
 * Display over other apps because the overlay write goes *through* Shizuku, and which
 * nine host assertions guard. Rearranging what is on screen says nothing about the order
 * they are switched in, and the enum is deliberately not reordered.
 *
 * ⚠ **r8 took this up on its offer and r11 split it in two**, both at the author's instruction
 * and with his own emphasis that it is *"just visually reordering things not their functions, or
 * logics"*. Which order is drawn follows the configured service; see [nestingLevel] for the one
 * row that is also drawn indented, and only in one of the two.
 *
 * An exhaustive `when` rather than a `listOf`: a seventh target cannot then be added
 * without a decision about where it goes. A list would simply leave it out, and nothing
 * in the audit suite reads this file.
 */
private fun ManualRevertTarget.rowPosition(isShevery: Boolean): Int = if (isShevery) {
    // The author's Shevery order: the two debugging rows the other way round, the service
    // fifth, and overlay access hanging off it.
    when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.WirelessDebugging -> 1
        ManualRevertTarget.UsbDebugging -> 2
        ManualRevertTarget.AccessibilityServices -> 3
        ManualRevertTarget.Shizuku -> 4
        ManualRevertTarget.DisplayOverOtherApps -> 5
    }
} else {
    // And his Shizuku order, flat.
    when (this) {
        ManualRevertTarget.DeveloperSettings -> 0
        ManualRevertTarget.UsbDebugging -> 1
        ManualRevertTarget.WirelessDebugging -> 2
        ManualRevertTarget.Shizuku -> 3
        ManualRevertTarget.AccessibilityServices -> 4
        ManualRevertTarget.DisplayOverOtherApps -> 5
    }
}

/**
 * How far in a row is drawn, in levels of [MANAGER_ROW_INDENT] — which since r11 is at most one.
 *
 * ⚠ **Decoration, and only decoration — the author's *"we are just visually reordering things not
 * their functions, or logics"*.** Nothing is gated on a parent, no switch does anything different,
 * and the order things are *applied* in is untouched.
 *
 * ⚠ **One indent, and only under Shevery.** r8 indented Shizuku under the debugging rows and
 * overlay access under Shizuku; the author has since looked at both and asked for a flat list
 * except for this one pair. Under Shevery the configured service sits directly above overlay
 * access and is what the overlay write goes through, so the indent is saying something true about
 * two adjacent rows. Under Shizuku the same relationship holds but the rows are not adjacent, and
 * an indent that reaches across the list draws a line nobody can follow — which is why the flat
 * order is not a loss.
 */
private fun ManualRevertTarget.nestingLevel(isShevery: Boolean): Int =
    if (isShevery && this == ManualRevertTarget.DisplayOverOtherApps) 1 else 0

/**
 * Which rows this dialog draws.
 *
 * Every target, minus overlay access when the master switch in Advanced is off - the same
 * rule the three rows in Settings follow, so the feature is either present everywhere or
 * nowhere rather than hidden in one place and live in another.
 *
 * Removing it costs the red row that a failed restore used to turn on, so the two ways back
 * are worth naming here because this function is what takes the third one away:
 *
 *  1. The revert failure notification. It is ongoing and `setAutoCancel(false)`, so the tap
 *     that opens this dialog does not clear it: Shizuku can be started from the row below,
 *     or from its arrow out to the Shizuku app, and the notification is still in the shade
 *     afterwards with **Try again** on it. That retry restores from the persisted debt and
 *     does not go through this dialog at all.
 *  2. **Revert to default**, at the bottom of this dialog. A debt taken while the switch was
 *     on is still owed after it is switched off, so the revert still hands overlay access
 *     back - see UserData.effectiveRevertDefaults. This is the way back if the notification
 *     has been swiped away, which the user can do from Android 14 even on an ongoing one.
 */
private fun rows(
    manageShizuku: Boolean,
    shown: Map<ManualRevertTarget, Boolean>,
    /** Which of the two orders to draw — see [rowPosition]. */
    isShevery: Boolean,
): List<ManualRevertTarget> {
    val drawn = if (manageShizuku) {
        ManualRevertTarget.entries
    } else {
        // ⚠ **Both rows, at the author's instruction.** Overlay access is written through
        // Shizuku and through nothing else, so with Manage Shizuku off that row is a switch
        // for a mechanism the user has turned off. Unlike a row that is merely unusable there
        // is no live state worth showing and no configuring that would make it movable while
        // the master switch is down, so it leaves rather than sitting there refusing.
        //
        // `usableTargets` is filtered from what is drawn, so the master pill stops touching
        // overlay access as a consequence of this rather than needing to be told.
        ManualRevertTarget.entries.filter {
            it != ManualRevertTarget.Shizuku &&
                it != ManualRevertTarget.DisplayOverOtherApps
        }
    }

    // ⚠ **A second removal, not a second opinion — r9.** Above decides what IMD is managing at
    // all; this decides what the user asked to look at. A row has to survive both, and neither
    // knows about the other.
    //
    // `!= false` rather than `== true`: a target with no stored answer is one this build knows
    // and the store has not been asked about, and the safe direction there is to draw it. See
    // ManagerRows.decode, which resolves the same case the same way.
    return drawn.filter { shown[it] != false }.sortedBy { it.rowPosition(isShevery) }
}

/**
 * Manage the settings this app switches off, from one place.
 *
 * It began as a rescue hatch — once developer options are off there is no system screen
 * left to switch them back on from, and the ongoing notification can be swiped away. It is
 * now simply a control panel: every row shows what that setting is really set to and
 * switches it either way, with an arrow out to the system screen or app that owns it.
 *
 * The batch selection it used to carry is gone. Ticking boxes and then pressing a second
 * button was two steps to do what one switch now does directly, and the switches have to
 * exist anyway to show the live state.
 */
@OptIn(ExperimentalFoundationApi::class)
/**
 * How wide this dialog is allowed to get, on any screen.
 *
 * ⚠ **Narrower than the app-wide `DIALOG_MAX_WIDTH`, on purpose.** Every other dialog is opened
 * from inside IMD with the app behind it; this one is opened from a tile or a shortcut, over
 * somebody else's app, and a card that fills the screen reads as having replaced that app rather
 * than as sitting on top of it. The author asked for it smaller on phone and tablet alike.
 */
private val MANAGER_MAX_WIDTH = 340.dp

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
 * The width of a Material switch's track, which is what puts the ⓘ over the switches.
 *
 * ⚠ **A layout width, not a drawn one, and that is the point.** `Modifier.scale` is a draw
 * transform: a scaled switch still occupies all 52 dp of layout and still scales about its own
 * centre. The rows carry no end padding, so every switch's box ends exactly at the card's content
 * edge — put a box of this width at the end of the title row and its centre is on theirs, at every
 * tier and every scale, with no offset to go stale.
 */
private val SWITCH_TRACK_WIDTH = 52.dp

/**
 * How big the IMD gear on the title line is drawn.
 *
 * ⚠ **48 dp costs nothing, and that is why it is the author's pick.** The ⓘ beside it is an
 * `IconButton`, which Material floors at a 48 dp touch target, so this row is already 48 dp tall
 * whatever this number is. Anything past 48 makes the row grow and pushes the whole card down.
 *
 * ⚠ **One size on every tier**, at his instruction — where the title, the rows, the pill and the
 * switches all step with [ManagerSize]. His reasoning stands on its own: the glyph is an identity
 * mark rather than type, and identity does not get bigger because the screen did.
 *
 * ⚠ **The gear is inset in its own viewport** — it fills about 48% of the 108-unit box, so this
 * draws a gear roughly 23 dp across. That is what the r6 size template rendered and what he chose
 * from; cropping the viewport to make the glyph fill the box would quietly give him something
 * larger than he approved.
 */
private val MANAGER_GLYPH_SIZE = 48.dp

/**
 * How far one level of [ManualRevertTarget.nestingLevel] moves a row across.
 *
 * ⚠ **The offset is the whole treatment**, at the author's pick from the r8 template: no rail down
 * the left, no elbow into each child, no recessed panel behind the group. He asked for *"only
 * slight indent not too big not too small to notice"*, and 16 dp is Material's own list-indent
 * step — the first level is unmistakable, and the second lands at 32 dp, which "Display over other
 * apps" still clears on the narrowest card the dialog draws.
 *
 * ⚠ **It moves the row's content, not the row.** The whole row still takes the press across the
 * full width — see [TargetRow] — so an indented child is no harder to hit than a top-level one.
 */
private val MANAGER_ROW_INDENT = 16.dp

/**
 * How strongly the scope note under a row is drawn.
 *
 * ⚠ **An alpha on [ManagerSize.rowStyle]'s neighbour token, not a fourth colour.** The note is
 * already a step below its row label — `onSurfaceVariant` against `onSurface` — and the author
 * asked for one more: *"make the font less visible (less contrast)"*. Fading the token it already
 * shares with the ⓘ and the open-link arrows keeps all three in step through every theme, dynamic
 * ones included, where a hand-picked colour would drift out of one.
 *
 * 0.75 is his pick, drawn in both themes before it landed. Alpha is not symmetrical between them —
 * in dark it fades a light note *towards* the card, in light it fades a dark note towards a light
 * card, which is the larger perceived step — and 75 holds in both.
 */
private const val MANAGER_NOTE_ALPHA = 0.75f

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
 *  1. **Roomy**, decided from the window's width alone. First, because it is what takes an
 *     unfolded foldable's inner screen out of the physical test, which on that screen was
 *     answering 305 dp — the author's *"looks too small"*.
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

    // dp to the inch: xdpi is pixels to the inch, density is pixels to the dp.
    val xdpi = LocalContext.current.resources.displayMetrics.xdpi

    val dpPerInch = if (xdpi > 0f) xdpi / LocalDensity.current.density else 0f

    val believable = dpPerInch > MIN_PLAUSIBLE_DP_PER_INCH &&
        dpPerInch < MAX_PLAUSIBLE_DP_PER_INCH

    val roomy = windowWidthDp >= ROOMY_WINDOW_WIDTH_DP

    if (roomy) {
        // What the window can actually give at the roomy margin, which on a clamshell's inner
        // screen is less than the cap and is the reason this is a `minOf` and not the cap alone.
        val available = windowWidthDp.dp - MANAGER_ROOMY_MARGIN * 2

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

@Composable
internal fun AndroidSettingsManagerDialog(
    modifier: Modifier = Modifier,
    states: ManualTargetStates,
    busy: Boolean,
    /**
     * Which way the work behind [busy] is going, or null when there is none — or when a press
     * has claimed the tracker but not yet read which way it is about to go.
     *
     * Only decides what the note under the title says. The rows go dead on [busy] alone, so a
     * direction arriving a moment late cannot let a press through.
     */
    settingsWork: SettingsWorkKind? = null,
    shizukuStarting: Boolean,
    shizukuStartFailed: Boolean,
    overlayRestoreFailed: Boolean,
    overlayWriteInFlight: Boolean,
    /**
     * The master switch in Advanced settings. With it off the overlay row is not drawn,
     * matching the three rows it already removes from Settings; the revert failure
     * notification carries the restore instead - see [rows].
     */
    manageShizuku: Boolean = true,
    /**
     * Which rows the user chose to see, from "Settings manager options" in Settings.
     *
     * ⚠ **Defaulted to every row**, and that default is doing real work: a caller that has not
     * been told draws what this dialog has always drawn rather than an empty card. It is also
     * what the value starts as while the store is being read.
     *
     * ⚠ **Drawing only.** See `ManagerRows` — a row missing from here is not switched off, not
     * excluded from a hide, and not skipped by Revert to default.
     */
    managerRows: Map<ManualRevertTarget, Boolean> = ManagerRows.Default,
    /**
     * Why the Display over other apps row will not move, or empty while it will.
     *
     * Decided by `overlayBlockReasons` in `:domain:model` and collected by the view model, so
     * this dialog and the two configuration dialogs cannot disagree about the same row.
     */
    overlayBlocked: List<OverlayBlockReason> = emptyList(),
    /**
     * Whether Shevery is the selected fork, which renames one row and changes what two of them
     * are allowed to do. See `SettingsManagerViewModel.setSheveryService`.
     */
    isShevery: Boolean = false,
    /** Seconds left of the Shevery wait, or null when nothing is waiting. */
    sheveryWait: Int? = null,
    /**
     * Whether a fork start begun from this dialog is in flight.
     *
     * Holds the **USB debugging** row for the whole of it, at the author's instruction: that is
     * the transport the start depends on, so switching it off mid-start would undo the thing
     * being waited for. Wireless debugging is free throughout — r4b held that one instead, and
     * he reversed it.
     *
     * Separate from [sheveryWait], which holds the same row but for forty seconds, with a
     * countdown, and holds the service row with it.
     */
    serviceStarting: Boolean = false,
    /** Null while the stored answer is still being read; see the ViewModel. */
    infoShown: Boolean? = true,
    onInfoShown: () -> Unit = {},
    /**
     * Whether anything IMD did is still outstanding — a device-wide hide, per-app records, or
     * an IMD+ run.
     *
     * ⚠ **Decides the whole of the first action button: its label, its glyph, its colour and
     * which call the press makes.** One value for all four, deliberately. A button that took
     * its label from one test and its behaviour from another could say `Unhide settings` and
     * hide, which is the one way this control can lie to somebody.
     */
    anythingHidden: Boolean = false,
    onDismissRequest: () -> Unit,
    /**
     * The app icon on the title line.
     *
     * ⚠ **Hoisted in r5, and it had to be.** It used to call `onDismissRequest` and then start
     * IMD, from in here — and that order is what put the app behind the dialog on the author's
     * razr and broke the transition into it. Only the caller knows what dismissal means, and so
     * only the caller can put the two in the right order: see [SettingsManagerRoute]'s two
     * callers for the two answers.
     */
    onOpenImdApp: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    /**
     * The master pill. The list is every row this dialog considers operable right now, so the
     * ViewModel never has to ask that question a second way — see [SettingsManagerViewModel].
     */
    onSetAll: (Boolean, List<ManualRevertTarget>) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
    onUnhideSettings: () -> Unit,
    onHideSettings: () -> Unit,
    /**
     * A press on the Shevery switch while its own start has it locked.
     *
     * The switch is drawn unusable so it greys and carries the spinner, but the press still
     * arrives here and stops the start — *"Block it, but a press cancels"*.
     */
    onCancelShevery: () -> Unit = {},
    onRevertToDefault: () -> Unit,
    onOpenRevertConfiguration: () -> Unit,
) {
    var showShizukuHelp by rememberSaveable { mutableStateOf(false) }

    // Shizuku is running but IMD has no configuration to send start and stop intents through,
    // so the row shows the live state and refuses to be operated. Its own message rather than
    // the help dialog: nothing here is broken, there is simply one screen to fill in first.
    var showShizukuUnmanageable by rememberSaveable { mutableStateOf(false) }

    // Shevery: the row reports the live service but can never be operated from here.
    var showSheveryToggle by rememberSaveable { mutableStateOf(false) }

    // Nothing selected for IMD to manage, so the accessibility row stands for nothing.
    // Null while nothing is blocked; the location trees otherwise; and empty for the one
    // case with nothing to point at - Shevery, where Display over other apps is unsupported
    // rather than unconfigured. Same three-way shape as the two configuration dialogs.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    // Shevery's service is down and this row needs it up. Its own flag rather than a path,
    // because the fix is one press on the row above rather than a screen to go to.
    var showSheveryServiceFirst by remember { mutableStateOf(false) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val overlayPaths = overlayBlockedPaths(reasons = overlayBlocked)

    // The same for overlay access: nothing picked, so the row stands for nothing.
    var showInfo by rememberSaveable { mutableStateOf(false) }

    // Opened for the first time, so say what this dialog is before the user reads the
    // switches as the configuration. Recorded as shown at the moment it appears rather than
    // when it is dismissed: the requirement is that it is shown once, and a dismissal that
    // never reaches the store would show it again on the next open.
    LaunchedEffect(infoShown) {
        if (infoShown == false) {
            showInfo = true

            onInfoShown()
        }
    }

    // Counts attempts to switch Shizuku on that have not taken effect yet. Shizuku can be
    // slow to come up, so the first couple of presses are simply impatience; past that it
    // is not going to work and the user needs telling why rather than a switch that keeps
    // springing back.
    var shizukuAttempts by remember { mutableIntStateOf(0) }

    val shizukuRunning = states.isEnabled(ManualRevertTarget.Shizuku)

    LaunchedEffect(shizukuRunning) {
        if (shizukuRunning) shizukuAttempts = 0
    }

    // ⚠ **How big this card is, asked once and handed down.** See [managerMetrics] for the three
    // tiers and why the question is put in inches rather than in dp. The switches, the type, the
    // row padding, the pill and the app icon all follow `metrics.size` rather than testing the
    // screen again for themselves.
    val metrics = managerMetrics()

    DialogContainer(
        modifier = modifier.verticalScroll(rememberScrollState()),
        // ⚠ **On the app's own width rule since r4k, and it used to be the exception.**
        // `compact` kept `usePlatformDefaultWidth`, which `DialogContainer` describes as
        // "capping dialogs below the screen width on a phone and letting them grow with the
        // screen on a tablet - both the wrong way round". This dialog was the last one still
        // getting both, and the author reported them a day apart: too wide on his tablet,
        // too narrow for its own buttons on his phone.
        //
        // The earlier reasoning - that it should stay a small centred card on every device,
        // because it opens over somebody else's app - is retired rather than contradicted in
        // silence. He has asked for the opposite on a phone.
        compact = false,
        // ⚠ **A cap of its own, and it is the lever r4w should have reached for.** A margin
        // narrows a dialog in proportion to the screen, so 32.dp did nothing on a tablet — where
        // the app-wide 580.dp cap decides the width — and not enough on a large phone. The
        // author saw both: *"too wide … on phones as well as tablets"*.
        //
        // At this width the dialog is the same small card on a folded razr, an S22 Ultra and a
        // tablet, because the cap binds on all three.
        maxWidth = metrics.width,
        // Still here, and not redundant: in a narrow or split-screen window the cap never binds
        // and this is again the only thing keeping the card off the edges.
        //
        // ⚠ **The roomy tier asks for less of it — r5.** A clamshell's inner screen is tall but
        // no wider than a large phone, so at 24 dp a side there is not enough left for the wider
        // card that tier exists to draw. See [MANAGER_ROOMY_MARGIN].
        horizontalMargin = metrics.margin,
        // ⚠ **The one dialog that frosts its own card — r19, at the author's request, and
        // corrected in r20b.** It is opened over somebody else's app as often as over IMD's own
        // list, and the frosting is what says the manager is the subject rather than a card that
        // happened to land there. The page *around* it is left alone — the author's *"keep
        // outside BG as it was"*. Does nothing while Progressive UI blur is off.
        frostedWindow = true,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                // No cap here. r4i put one on because this dialog kept the platform width;
                // since r4k it is on `DialogContainer`'s own path and the cap is passed to the
                // container above — two caps on one dialog is two places to change a number and
                // one of them to forget.
                .fillMaxWidth()
                .padding(8.dp),
        ) {
            // A plain Row again. r2's centred logo button is gone and its job has moved
            // onto the glyph below, at the author's instruction — it was already there,
            // already says which app put this dialog in front of you, and one glyph on this
            // line is easier to aim at than two.
            //
            // ⚠ **No padding at the end — r6, and it is load-bearing.** The rows below carry
            // none either, so their switches finish exactly at the card's content edge. Ten dp
            // here would end this row ten dp short of that, and the ⓘ would sit that far inside
            // the switches it is supposed to be centred on.
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(start = 10.dp, top = 10.dp, bottom = 10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // ⚠ **The gear with the key hollow, not the launcher icon — r6.** The author
                // asked for "a imd settings gear icon ... with the key area in center hollow",
                // in the ⓘ's colour, and bigger. `Icon` rather than `Image` because `Icon` is
                // what applies a tint; see `ic_imd_mono` for why the shape is a copy of the
                // launcher's themed-icon layer and not a new drawing.
                //
                // Still the button, and still clipped to a circle so the ripple is a disc
                // around the glyph rather than a square behind it.
                Icon(
                    modifier = Modifier
                        .size(MANAGER_GLYPH_SIZE)
                        .clip(CircleShape)
                        .clickable(onClick = onOpenImdApp),
                    painter = painterResource(designR.drawable.ic_imd_mono),
                    contentDescription = stringResource(
                        R.string.settings_manager_open_settings,
                    ),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )

                Spacer(modifier = Modifier.width(12.dp))

                Text(
                    // ⚠ **Weighted, so the title takes the slack** rather than the ⓘ being
                    // pushed along by it. Every tier has room for this title today — the
                    // tightest is the compact card, 178 dp of space for about 114 dp of text —
                    // but translations are deferred, and this is the shape that survives the
                    // first one that is longer: it wraps instead of shoving the ⓘ off the end.
                    modifier = Modifier.weight(1f),
                    text = stringResource(R.string.settings_manager_title),
                    // One step down, with everything else on this dialog — r4y — and a step
                    // either way from there with the tier, r5.
                    style = metrics.size.titleStyle(),
                )

                // ⚠ **The ⓘ, moved and nothing else — r6.** *"do not touch i logo icon photo or
                // its size, only its position"*: the button, the glyph and its 18 dp are exactly
                // as they were. What is new is the box around it, which is a switch's track wide
                // and sits at the very end of the row — so the ⓘ lands on the switches' own
                // centre line. See [SWITCH_TRACK_WIDTH] for why that is a width rather than an
                // offset.
                Box(
                    modifier = Modifier.width(SWITCH_TRACK_WIDTH),
                    contentAlignment = Alignment.Center,
                ) {
                    IconButton(onClick = { showInfo = true }) {
                        Icon(
                            modifier = Modifier.size(18.dp),
                            imageVector = GetoIcons.Info,
                            contentDescription = stringResource(
                                R.string.settings_manager_info,
                            ),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }
            }

            // Why every row has just gone dead. Without it the dialog looks broken rather than
            // busy: six switches that do not move and nothing on screen saying why.
            //
            // Drawn only once the direction is known. In the moment between a press claiming
            // the tracker and the use case underneath naming a direction there is nothing
            // honest to say, and guessing would sometimes say the opposite of what is running.
            // ⚠ **Never drawn beside the busy note below**, which sits in this same slot and
            // opens with the same five words. They mean different things — that one is work
            // running now, this one is a hide that finished with its revert still owing — and
            // the author's rule is that this one waits.
            //
            // Suppressed on `busy` rather than on `settingsWork`: the rows go dead on `busy`
            // alone, and there is a moment where work has started and has not yet named a
            // direction, in which neither line has anything honest to say.
            //
            // The glyph is an Icon and not an IconButton, at the author's instruction — "a red
            // i logo not button". Nothing opens.
            if (anythingHidden && !busy) {
                Spacer(modifier = Modifier.height(8.dp))

                Row(modifier = Modifier.fillMaxWidth()) {
                    Icon(
                        modifier = Modifier.size(15.dp),
                        imageVector = GetoIcons.Info,
                        contentDescription = null,
                        tint = MaterialTheme.colorScheme.error,
                    )

                    Spacer(modifier = Modifier.width(8.dp))

                    Text(
                        text = stringResource(R.string.settings_manager_pending),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
            }

            settingsWork?.let { work ->
                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = stringResource(
                        when (work) {
                            SettingsWorkKind.Hiding -> R.string.settings_manager_busy_hiding
                            SettingsWorkKind.Unhiding -> R.string.settings_manager_busy_unhiding
                        },
                    ),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            val drawnRows = rows(
                manageShizuku = manageShizuku,
                shown = managerRows,
                isShevery = isShevery,
            )

            // ⚠ **One test, read twice.** The rows use it to decide whether a switch moves,
            // and the master pill uses it to decide which rows it is allowed to move — which
            // is the whole of the author's rule that the pill "does not touch untogglable
            // toggles". Computing it separately for the pill would be a second answer to a
            // question this dialog has already answered, and the two would eventually differ.
            val usableOf = { target: ManualRevertTarget ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                val isAccessibility = target == ManualRevertTarget.AccessibilityServices

                // Starting a Shizuku fork switches the debugging transport on by itself, so
                // while an overlay write is running these rows are about to move without the
                // user touching them. Locked rather than left live, because a press in that
                // window races the write that puts them back.
                val disturbedByOverlayWrite = overlayWriteInFlight &&
                    (isShizuku || target.usesDebuggingTransport)

                // ⚠ **USB debugging and the Shevery row itself, and wireless debugging not
                // at all.** r4b had this the other way round on both counts; the author
                // reversed it after using it. The transport is what is holding the service
                // up, so touching USB mid-wait would undo the very thing being waited for,
                // and the service row goes with it so a second press cannot queue a second
                // start - but that row is *wrapped* rather than disabled, and its press
                // cancels, which is the escape hatch he asked for in r4b kept intact.
                //
                // Wireless debugging is free the whole wait: forty seconds is a long time to
                // be locked out of a switch, and it is put back afterwards only if Shevery
                // moved it.
                val heldBySheveryWait = sheveryWait != null &&
                    (
                        target == ManualRevertTarget.UsbDebugging ||
                            target == ManualRevertTarget.Shizuku
                        )

                // ⚠ **USB debugging, not wireless debugging** — the author reversed r4b's
                // choice: *"when shizuku toggle is turned on in settings manager no need to
                // block access to wireless debugging settings, instead block usb debugging
                // toggle until shizuku starts"*. Both forks now hold the same row while a
                // start is in flight, which is also the transport the start actually depends
                // on: switching it off mid-start would undo the thing being waited for.
                //
                // Separate from [heldBySheveryWait] above even though they now name the same
                // target, because they are two different things: that one runs for forty
                // seconds, shows a countdown, and holds the service row as well.
                val heldByServiceStart = serviceStarting &&
                    target == ManualRevertTarget.UsbDebugging

                !busy && !disturbedByOverlayWrite && !heldBySheveryWait &&
                    !heldByServiceStart &&
                    (!isOverlay || !overlayWriteInFlight) &&
                    (
                        !isShizuku ||
                            (
                                states.shizukuAvailable &&
                                    // Shevery has no intents and does not need any: the row
                                    // writes the debugging transport instead. It is held by
                                    // its own wait rather than by `shizukuStarting`, above.
                                    (isShevery || states.shizukuSupportsIntents) &&
                                    (isShevery || !shizukuStarting)
                                )
                        ) &&
                    (!isAccessibility || states.accessibilityManaged) &&
                    (!isOverlay || states.overlayManaged)
            }

            val usableTargets = drawnRows.filter(usableOf)

            // ⚠ **What a bulk button is about to move — r26.** `All on`, `All off`, `Hide` /
            // `Unhide settings` and `Revert to default` change rows without touching any row's own
            // press, so before r26 only Shizuku ticked — and only because its `starting` flag
            // armed it by accident. This is the deliberate version.
            //
            // ⚠ **Every row that is currently *off*, not every row that will end up on.** The
            // second is a guess made before the states have been re-read; the first is a fact. A
            // row that stays off never ticks anyway, because a switch ticks only when it is armed
            // *and* becomes checked — so arming the wider set is both simpler and race-free.
            var bulkArmed by remember { mutableStateOf(emptySet<ManualRevertTarget>()) }

            val armBulk = {
                bulkArmed = drawnRows.filterNot(states::isEnabled).toSet()
            }

            // ⚠ **Two ways in, on purpose.** Every one of these buttons should raise `busy`, and
            // if they all do then this effect alone would be enough; each button also arms
            // directly, because belt-and-braces here is cheaper than another round spent finding
            // out that one of them does not.
            //
            // Cleared a beat after the work ends rather than immediately: the switches latch the
            // arm into their own state, so this only has to stay up long enough to be seen, and
            // leaving it up for ever would make a later unrelated turn-on tick.
            LaunchedEffect(busy) {
                if (busy) {
                    armBulk()

                    return@LaunchedEffect
                }

                if (bulkArmed.isEmpty()) return@LaunchedEffect

                delay(BULK_ARM_GRACE_MILLIS)

                bulkArmed = emptySet()
            }

            // The master pill, above the first switch at the author's instruction rather
            // than below the last. It belongs to the switches it operates either way; at the
            // top it is read before them, which is the order someone reaches for "all off"
            // in - decide the lot, then correct the one or two that need it.
            MasterPill(
                size = metrics.size,
                enabled = usableTargets.isNotEmpty(),
                onAllOn = {
                    armBulk()

                    onSetAll(true, usableTargets)
                },
                onAllOff = {
                    armBulk()

                    onSetAll(false, usableTargets)
                },
            )

            Spacer(modifier = Modifier.height(10.dp))

            drawnRows.forEach { target ->
                val isShizuku = target == ManualRevertTarget.Shizuku

                val isOverlay = target == ManualRevertTarget.DisplayOverOtherApps

                val isAccessibility = target == ManualRevertTarget.AccessibilityServices

                TargetRow(
                    size = metrics.size,
                    isShevery = isShevery,
                    target = target,
                    // Shizuku is the one target the app can ask for but not make happen, so
                    // it reports back. Overlay is the one whose restore can fail long after
                    // anybody was looking, so it does too.
                    starting = (isShizuku && shizukuStarting) ||
                        (isOverlay && overlayWriteInFlight),
                    failed = (isShizuku && shizukuStartFailed && !shizukuStarting) ||
                        (isOverlay && overlayRestoreFailed && !overlayWriteInFlight),
                    failureMessage = if (isOverlay) {
                        R.string.settings_manager_overlay_restore_failed
                    } else {
                        R.string.settings_manager_shizuku_failed
                    },
                    failureOpen = if (isOverlay) {
                        R.string.settings_manager_overlay_restore_failed_open
                    } else {
                        R.string.settings_manager_shizuku_failed_open
                    },
                    // Absent means the first poll has not landed yet. Off is the safer of
                    // the two to show for a beat: it invites a press that helps, where a
                    // wrong "on" invites the user to walk away from a device still locked
                    // down.
                    enabled = states.isEnabled(target),
                    // Shizuku is the only row that can be switched off in the sense of
                    // "there is nothing here to control".
                    // Locked while an attempt is in flight. The switch already reads on and
                    // the outcome is a few seconds away; letting it be pressed again would
                    // queue a second attempt against a service that is still deciding.
                    usable = usableOf(target),
                    // r26: this row was off when a bulk button was pressed, so if it comes on it
                    // has something to say about it.
                    bulkArmed = target in bulkArmed,
                    onClickWhenUnusable = when {
                        // ⚠ **Before every other Shevery branch.** Those answer "this fork has
                        // no intents", which is true and useless while a start is running.
                        // The author asked for the switch to look blocked and still cancel.
                        isShizuku && isShevery && sheveryWait != null -> onCancelShevery

                        // ⚠ **Above every explanation below, and the author's report.** With a
                        // start in flight the row is busy, not misconfigured - but
                        // `states.shizukuAvailable` is a package query that `runCatching`
                        // turns into false when the platform declines to answer, so the
                        // *unavailable* dialog could fire mid-start and tell somebody to go
                        // and check a configuration that is perfectly correct.
                        //
                        // Nothing, rather than a different dialog: the countdown under the row
                        // already says what is happening, and a pop-up repeating it would be
                        // the same news twice. Shevery keeps its cancel, one branch above.
                        isShizuku && shizukuStarting -> null

                        // Shevery first, because it is the permanent one: the switch is
                        // reporting the service honestly and no amount of configuring will
                        // make it movable, since that fork has no intents to send.
                        isShizuku && !states.shizukuSupportsIntents -> {
                            { showSheveryToggle = true }
                        }

                        // Unconfigured is its own answer: the switch is showing the service's
                        // real state and the only thing missing is the configuration that
                        // start and stop intents are sent through. The help dialog is about a
                        // switch that will not move despite being set up, which is not this.
                        isShizuku && !states.shizukuAvailable -> {
                            { showShizukuUnmanageable = true }
                        }

                        isShizuku -> {
                            { showShizukuHelp = true }
                        }

                        // Nothing picked to manage, so the row stands for nothing and says so
                        // rather than sitting there refusing to move for no stated reason.
                        isAccessibility && !states.accessibilityManaged -> {
                            { blockedPaths = listOf(accessibilityPath) }
                        }

                        // The same again for overlay access, and the same reasoning: with no
                        // app picked there is nothing for this row to withdraw or hand back,
                        // so it says which screen to go to rather than refusing in silence.
                        // Shevery first: with the service down this row is not
                        // unconfigured, it is waiting on something the user can do in one
                        // press, and a location tree would send them somewhere else entirely.
                        isOverlay && isShevery &&
                            !states.isEnabled(ManualRevertTarget.Shizuku) -> {
                            { showSheveryServiceFirst = true }
                        }

                        isOverlay && !states.overlayManaged -> {
                            { blockedPaths = overlayPaths }
                        }

                        else -> null
                    },
                    onSetEnabled = { wanted ->
                        if (isShizuku && wanted) {
                            shizukuAttempts += 1

                            if (shizukuAttempts > SHIZUKU_ATTEMPTS_BEFORE_HELP) {
                                showShizukuHelp = true

                                shizukuAttempts = 0
                            }
                        }

                        onSetEnabled(target, wanted)
                    },
                    onOpen = { onOpen(target) },
                )

                // ⚠ **Under the row it explains, at the author's instruction**, rather than in
                // the header slot it used to share with the pending note. It is still the most
                // immediate thing on screen while it counts; it is now also attached to the
                // switch that has just gone dead, which is what it is about.
                //
                // Inside the loop rather than after it, so it follows the service row wherever
                // that row is drawn - `rows(manageShizuku)` can leave it out altogether, and a
                // countdown pinned below a fixed position would then explain a row that is not
                // on screen.
                if (isShizuku && sheveryWait != null) {
                    Text(
                        // ⚠ **Indented with the row it explains — r8.** This is a footnote to
                        // the service row directly above it, so it takes that row's own depth;
                        // left at 4 dp it would sit under the *previous* row's left edge and
                        // read as belonging to that one instead.
                        modifier = Modifier.padding(
                            start = 4.dp + MANAGER_ROW_INDENT * target.nestingLevel(isShevery),
                            bottom = 6.dp,
                        ),
                        // One countdown, two names. Only one fork start can be in flight, so
                        // the value has a single owner; which service it is waiting for is the
                        // same question that renames the row above it.
                        text = stringResource(
                            if (isShevery) {
                                R.string.shevery_wait_countdown
                            } else {
                                R.string.shizuku_wait_countdown
                            },
                            sheveryWait,
                        ),
                        // The author's "make shizuku/shevery countdown lines to this small
                        // size" - the same style as the note above, so the two small lines in
                        // this dialog cannot end up at two different sizes.
                        style = managerNoteStyle(),
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }

            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))

            // Both filled, unlike Close, because both do something to the device while Close
            // only shuts the dialog. Neither dismisses: the rows above are polled live, so
            // staying open is what shows the work happening, and closing would hide the one
            // piece of feedback either action has.
            //
            // Equal width rather than each at its natural size. Two watermarked buttons of
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
                // Hide and unhide in one button, at the author's instruction, and it is
                // first for the reason unhide alone was: it is the one people reach for, and
                // it is the reversible one — it puts back what a hide took, where Revert to
                // default drives the configured list whatever was there before.
                //
                // ⚠ **The glyph names the outcome, not the mechanism.** Press the struck-out
                // eye and the settings end up hidden; press the open one and they end up
                // visible. That reading is `_v3_fav_hide_glyph.py`'s, settled in r2e for the
                // open eye alone, and its sibling now follows it.
                ActionButton(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    size = metrics.size,
                    glyph = if (anythingHidden) {
                        designR.drawable.ic_hide_glyph
                    } else {
                        designR.drawable.ic_hidden_glyph
                    },
                    label = if (anythingHidden) {
                        stringResource(R.string.unhide_settings)
                    } else {
                        stringResource(R.string.hide_settings)
                    },
                    pending = anythingHidden,
                    onClick = {
                        armBulk()

                        if (anythingHidden) onUnhideSettings() else onHideSettings()
                    },
                )

                ActionButton(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxHeight(),
                    size = metrics.size,
                    glyph = designR.drawable.ic_revert_glyph,
                    label = stringResource(R.string.revert_to_default),
                    onClick = {
                        armBulk()

                        onRevertToDefault()
                    },
                    onLongClick = onOpenRevertConfiguration,
                    onLongClickLabel = stringResource(
                        R.string.settings_manager_configure_revert,
                    ),
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Its own row, right-aligned, at the author's instruction. Below the two rather
            // than beside them: with both of those filled and equal width, a third control on
            // the same line would have to be squeezed in, and the one that only closes the
            // dialog is the one that should give way.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
        }
    }

    if (showInfo) {
        SettingsManagerInfoDialog(onDismissRequest = { showInfo = false })
    }

    if (showShizukuUnmanageable) {
        ShizukuUnmanageableDialog(onDismissRequest = { showShizukuUnmanageable = false })
    }

    if (showSheveryToggle) {
        SheveryToggleDialog(onDismissRequest = { showSheveryToggle = false })
    }

    if (showSheveryServiceFirst) {
        ConfigureFirstDialog(
            message = stringResource(R.string.shevery_service_first),
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { showSheveryServiceFirst = false },
        )
    }

    blockedPaths?.let { paths ->
        ConfigureFirstDialog(
            message = if (paths.isEmpty()) {
                stringResource(R.string.dooa_thedjchi_only)
            } else {
                stringResource(R.string.configure_first)
            },
            paths = paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blockedPaths = null },
        )
    }

    if (showShizukuHelp) {
        ShizukuHelpDialog(onDismissRequest = { showShizukuHelp = false })
    }
}

/**
 * The size of the two small lines in this dialog: the scope note under a row, and the fork
 * start countdown.
 *
 * ⚠ **10sp is not one of Material's steps**, so this is `labelSmall` - the smallest that is, at
 * 11sp - copied down rather than a style invented beside the scheme. One function for both, so
 * "very small" cannot come to mean two different things in one dialog.
 *
 * ⚠ **The line height moves with it.** `labelSmall` carries 16sp; a 10sp line left in a 16sp box
 * reads as a gap rather than as small type.
 */
@Composable
private fun managerNoteStyle() = MaterialTheme.typography.labelSmall.copy(
    fontSize = 10.sp,
    lineHeight = 13.sp,
)

/**
 * Whether this target manages a list the user chose rather than the whole of something.
 *
 * The two that do are the ones the author asked to carry *Only selected ones*: accessibility
 * services and display-over-other-apps are both driven by a selection made in IMD's settings,
 * where Shizuku and the debugging toggles are all-or-nothing.
 */
private val ManualRevertTarget.readsASelection: Boolean
    get() = this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps

@Composable
private fun TargetRow(
    modifier: Modifier = Modifier,
    /**
     * Which tier the card is in — see `managerMetrics`.
     *
     * ⚠ **Passed in, like [isShevery] and for the same reason.** The dialog asks the screen
     * once; a row that measured for itself could draw at a size the card beneath it is not.
     */
    size: ManagerSize,
    target: ManualRevertTarget,
    enabled: Boolean,
    usable: Boolean,
    /**
     * Whether Shevery is the selected fork, which is what renames the Shizuku row.
     *
     * ⚠ **Passed in rather than read here.** The dialog above collects it once and hands the
     * same answer to every row; a row that read it for itself could disagree with the
     * usability test that was computed from it a few lines earlier.
     */
    isShevery: Boolean = false,
    starting: Boolean = false,
    /** A bulk button was pressed while this row was off — see the dialog's `bulkArmed`. */
    bulkArmed: Boolean = false,
    failed: Boolean = false,
    @StringRes failureMessage: Int = R.string.settings_manager_shizuku_failed,
    @StringRes failureOpen: Int = R.string.settings_manager_shizuku_failed_open,
    onClickWhenUnusable: (() -> Unit)?,
    onSetEnabled: (Boolean) -> Unit,
    onOpen: () -> Unit,
) {
    var showFailureHelp by rememberSaveable { mutableStateOf(false) }

    // ⚠ **The last thing the user asked this row for — r25, and it exists because the press does
    // not go through the switch.** The whole row is clickable and calls `onSetEnabled` directly,
    // so `GetoSwitch` never hears about the press the author actually makes and could not know
    // that a turn-on was outstanding. Saveable because `Display over other apps` leaves for a
    // system settings screen between the press and the result.
    var requestedOn by rememberSaveable { mutableStateOf(false) }

    val request: (Boolean) -> Unit = { want ->
        requestedOn = want

        onSetEnabled(want)
    }

    val switchScale = size.switchScale

    val rowPadding = size.rowPadding

    // ⚠ **Read from the target rather than passed in**, unlike `size` and `isShevery`. Those two
    // are answers the dialog works out once and hands down, and a row that recomputed them could
    // disagree with the card it is drawn on. This is not one of those: how deep a row sits is a
    // fact about the target itself, like `readsASelection` and `opensSomewhere` just below, and
    // there is nothing for it to disagree with.
    val indent = MANAGER_ROW_INDENT * target.nestingLevel(isShevery)

    Row(
        modifier = modifier
            .fillMaxWidth()
            // ⚠ **The whole row, at the author's instruction** - label, switch and the gap
            // between them. On the width this dialog is capped at, a switch at the far right
            // is a small target at the end of a long reach, and every settings list on the
            // platform takes the row.
            //
            // The switch keeps its own handler and the open-link button and the failure ⓘ keep
            // theirs; a press that lands on any of them is handled there and never arrives
            // here, which is Compose's innermost-first dispatch. This is for everything else.
            //
            // It calls the same two lambdas the switch does rather than deciding anything of
            // its own, so the row and the switch cannot come to disagree about what a press
            // means.
            .clickable(enabled = usable || onClickWhenUnusable != null) {
                if (usable) request(!enabled) else onClickWhenUnusable?.invoke()
            }
            // ⚠ **The indent goes inside the clickable**, which is what keeps a nested row as
            // easy to hit as a top-level one: the press area is still the full width of the card
            // and only the content moves across.
            .padding(start = 4.dp + indent, top = rowPadding, bottom = rowPadding),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                // Weighted, so it is measured after the spinner and the icon rather than
                // before them. Unweighted, a long title - "Display over other apps" is the
                // longest here - eats the whole row and leaves the icon a few pixels to
                // draw 18.dp into, which Modifier.size honours by shrinking it. That is why
                // the overlay row's red icon came out smaller than the Shizuku row's when
                // both asked for exactly the same size. fill = false so a short title still
                // sits beside its icon instead of being pushed away from it.
                Text(
                    modifier = Modifier.weight(1f, fill = false),
                    text = target.getTitle(isShevery = isShevery),
                    style = size.rowStyle(),
                )

                // ⚠ **The spinner used to be here — r24 moved it into the switch's thumb**, at
                // the author's instruction. It said the same thing either way, but beside the
                // title it was a ring next to a label and the user had pressed a switch. See
                // `GetoSwitch`'s `busy`.

                if (failed) {
                    Spacer(modifier = Modifier.width(6.dp))

                    Icon(
                        modifier = Modifier
                            .size(18.dp)
                            .clickable { showFailureHelp = true },
                        imageVector = GetoIcons.Info,
                        contentDescription = stringResource(failureOpen),
                        tint = MaterialTheme.colorScheme.error,
                    )
                }
            }

            // The two scope descriptions that used to sit here — "only services selected in
            // the IMD app settings are managed" and its overlay twin — are gone at the
            // author's instruction. Their strings are kept: the ⓘ dialog covers the same
            // ground, and a removed line is cheaper to put back than to re-translate.
            //
            // ⚠ **What is here instead is four words, and that is the difference.** The
            // sentences that were removed explained the scope; this only names it, at a size
            // that reads as a footnote to the row rather than as a second line of the row.
            // Only the two targets that actually read a selection list carry it.
            if (target.readsASelection) {
                Text(
                    text = stringResource(R.string.settings_manager_only_selected),
                    style = managerNoteStyle(),
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                        .copy(alpha = MANAGER_NOTE_ALPHA),
                )
            }
        }

        if (target.opensSomewhere) {
            IconButton(onClick = onOpen) {
                Icon(
                    modifier = Modifier.size(18.dp),
                    imageVector = GetoIcons.OpenInNew,
                    contentDescription = stringResource(
                        R.string.settings_manager_open,
                        target.getTitle(isShevery = isShevery),
                    ),
                    tint = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }

        // ⚠ **One switch, not one per branch — r25, and the split was a real bug.** This used to
        // be `if (usable) GetoSwitch(…) else Box { GetoSwitch(…) }`, and Compose treats two call
        // sites as two nodes: a row that became usable threw its switch away and composed a new
        // one, losing everything the old one remembered. That is why the Shizuku toggle only
        // sometimes showed its tick — it is unusable while `shizukuStarting` — and why `Display
        // over other apps`, which goes through the same swap on every press, never showed one at
        // all. Varying the *modifier* keeps the node.
        Box(
            modifier = if (usable) {
                Modifier
            } else {
                // A disabled Switch swallows taps, so an unusable row would look simply
                // broken. The box takes the press instead and explains itself, which works
                // because the switch below is handed a null onCheckedChange and so has no
                // input modifier of its own for the press to be caught by.
                Modifier.clickable(enabled = onClickWhenUnusable != null) {
                    onClickWhenUnusable?.invoke()
                }
            },
        ) {
            GetoSwitch(
                // ⚠ **Scaled, and this is what actually takes the height out of the dialog.** A
                // Material switch has no size to set and reserves a 48.dp minimum, which six
                // rows of turned into the height the author reported.
                //
                // ⚠ Its touch target shrinks with it, and that is safe **here only** because the
                // whole row already takes the press — see the row's own comment above. A switch
                // standing on its own must not copy this.
                modifier = Modifier.scale(switchScale),
                checked = enabled,
                // ⚠ **The off state in the error palette when the service failed to start.**
                // One flag rather than the three colour overrides this used to be: the switch
                // takes the decision and derives the palette, so there is nothing to keep in
                // step when the scheme changes.
                error = failed,
                // r24: the ring that used to sit beside the title above.
                busy = starting,
                // r25: the press this switch never heard, because the row took it.
                // r26: or the bulk button that moved this row without pressing it at all.
                armed = requestedOn || bulkArmed,
                // Only reaches the drawing while the switch is disabled, which is this row's
                // unusable state. Not greyed into nothing: the row is still reporting a real
                // state — a Shevery service that is genuinely running — and the stock disabled
                // palette makes a true "on" look like a dead control.
                liveWhileDisabled = true,
                enabled = usable,
                onCheckedChange = if (usable) request else null,
            )
        }
    }

    if (showFailureHelp) {
        RowFailureDialog(
            message = failureMessage,
            onDismissRequest = { showFailureHelp = false },
        )
    }
}

/**
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
 */
@Composable
private fun MasterPill(
    modifier: Modifier = Modifier,
    /** Which tier the card is in — see `managerMetrics`. */
    size: ManagerSize,
    enabled: Boolean,
    onAllOn: () -> Unit,
    onAllOff: () -> Unit,
) {
    // ⚠ **The ink lifted over the top container, opaque — r24, at the author's word:** *"remove
    // them, instead increase their alpha to increase their visibility and make them opaque"*.
    //
    // r23 put a hairline here because this row sits on a card that is now translucent and a
    // subtle fill has nothing solid to be subtle against. Right about the problem, wrong about
    // the remedy — it was a fourth line in a dialog that already has a card edge, a gap through
    // this pill and six row separators.
    //
    // The fill has to do it instead, and the neutral ladder has no rung above
    // `surfaceContainerHighest` to climb to. So the scheme's own ink goes over that top container
    // at a low alpha, which is brighter than the card in dark mode and darker than it in light —
    // the ink is the opposite of the page in both, so one number serves both themes.
    //
    // ⚠ **`compositeOver`, not `copy(alpha = …)`, and that is the author's "opaque".** A copy
    // carries its alpha into the draw, so on the frosted manager the wallpaper shows through the
    // pill; compositing resolves it here and hands the Surface a solid colour. The shade stays
    // neutral either way, because the author's r2b3d pick was that this row belongs to the
    // switches beside it rather than to the filled pair at the foot of the dialog.
    val container = if (enabled) {
        MaterialTheme.colorScheme.onSurface
            .copy(alpha = PILL_LIFT)
            .compositeOver(MaterialTheme.colorScheme.surfaceContainerHighest)
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    }

    val content = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            .height(size.pillHeight),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        // All off first, at the author's instruction, which reverses the order this row had.
        PillHalf(
            modifier = Modifier.weight(1f),
            size = size,
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
            size = size,
            label = stringResource(R.string.settings_manager_all_on),
            shape = PILL_END_SHAPE,
            container = container,
            content = content,
            enabled = enabled,
            onClick = onAllOn,
        )
    }
}

/**
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
    size: ManagerSize,
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
            Text(text = label, style = size.pillStyle())
        }
    }
}

/** What a red switch means. One dialog, because both red switches mean "read this line". */
@Composable
private fun RowFailureDialog(
    modifier: Modifier = Modifier,
    @StringRes message: Int,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(20.dp),
        ) {
            Text(
                text = stringResource(message),
                style = MaterialTheme.typography.bodyMedium,
            )

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}

/**
 * What to do when the Shizuku switch will not move.
 *
 * Three points because there are three different things people get wrong here, and the
 * second is the one nobody guesses: this app asks Shizuku for one permission, once, and
 * has no privileged channel to Shizuku afterwards. Everything else it does with Shizuku is
 * a broadcast that Shizuku is free to ignore.
 */
@Composable
private fun ShizukuHelpDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shizuku_help_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            listOf(
                R.string.shizuku_help_point_setup,
                R.string.shizuku_help_point_permission,
                R.string.shizuku_help_point_restart,
            ).forEachIndexed { index, point ->
                if (index > 0) Spacer(modifier = Modifier.height(8.dp))

                Row {
                    Text(
                        text = stringResource(R.string.shizuku_help_bullet, index + 1),
                        style = MaterialTheme.typography.bodyMedium,
                    )

                    Text(
                        modifier = Modifier.padding(start = 6.dp),
                        text = stringResource(point),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.ok))
                }
            }
        }
    }
}

/**
 * Why the Shizuku row shows a state it will not let you change.
 *
 * The switch reports the service honestly — running is running, whatever IMD has been told —
 * but operating it means broadcasting the fork's own start and stop intents, and there is no
 * action to send until Shizuku has been configured in IMD's settings. One line, because there
 * is exactly one thing to do about it.
 */
@Composable
private fun ShizukuUnmanageableDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shizuku_unmanageable),
                style = MaterialTheme.typography.bodyLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.ok))
                }
            }
        }
    }
}

/**
 * Why the Shizuku row cannot be operated on a Shevery install.
 *
 * Three points because there are three separate things to say, and the last is the actionable
 * one: Shevery is managed from Shevery. The row is not broken and is not misconfigured — this
 * fork simply has no start or stop intent, so the switch is a readout rather than a control.
 */
@Composable
private fun SheveryToggleDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shevery_toggle_title),
                style = MaterialTheme.typography.titleLarge,
            )

            Spacer(modifier = Modifier.height(12.dp))

            listOf(
                R.string.shevery_toggle_point_intents,
                R.string.shevery_toggle_point_status,
                R.string.shevery_toggle_point_open,
            ).forEachIndexed { index, point ->
                if (index > 0) Spacer(modifier = Modifier.height(8.dp))

                Row {
                    Text(
                        text = stringResource(R.string.shizuku_help_bullet, index + 1),
                        style = MaterialTheme.typography.bodyMedium,
                    )

                    Text(
                        modifier = Modifier.padding(start = 6.dp),
                        text = stringResource(point),
                        style = MaterialTheme.typography.bodyMedium,
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.ok))
                }
            }
        }
    }
}

/**
 * The rows a Shizuku start moves on its own.
 *
 * A fork brings the debugging transport up with it using its own WRITE_SECURE_SETTINGS, so
 * these three change without the app writing them and without the user pressing anything.
 */
private val ManualRevertTarget.usesDebuggingTransport: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.UsbDebugging ||
        this == ManualRevertTarget.WirelessDebugging

/** The three rows that have a system screen or an app behind them. */
private val ManualRevertTarget.opensSomewhere: Boolean
    get() = this == ManualRevertTarget.DeveloperSettings ||
        this == ManualRevertTarget.UsbDebugging ||
        this == ManualRevertTarget.WirelessDebugging ||
        this == ManualRevertTarget.AccessibilityServices ||
        this == ManualRevertTarget.DisplayOverOtherApps ||
        this == ManualRevertTarget.Shizuku

@Composable
internal fun ManualRevertTarget.getTitle(isShevery: Boolean = false): String = when (this) {
    ManualRevertTarget.DeveloperSettings -> stringResource(R.string.revert_developer_settings)
    ManualRevertTarget.UsbDebugging -> stringResource(R.string.revert_usb_debugging)
    ManualRevertTarget.WirelessDebugging -> stringResource(R.string.revert_wireless_debugging)
    ManualRevertTarget.AccessibilityServices -> stringResource(R.string.revert_accessibility)
    // The author's rename: with Shevery selected the row is that service, and calling it
    // Shizuku would name an app the user has not chosen.
    ManualRevertTarget.Shizuku -> stringResource(
        if (isShevery) R.string.revert_shevery else R.string.revert_shizuku,
    )
    ManualRevertTarget.DisplayOverOtherApps -> stringResource(R.string.revert_display_over_other_apps)
}

/**
 * One of the dialog's two filled actions: a leading glyph, then the label.
 *
 * ⚠ **The glyph is beside the label, not behind it.** r2g drew it enlarged as a watermark and
 * the author took it back out the following build; this is the arrangement `Revert to default`
 * has always had, and the one the rows above it use.
 *
 * ### The two colour pairs
 *
 * [pending] is red, for the hide/unhide button with something outstanding. Everything else is
 * tonal: that same button offering to hide, and `Revert to default`, which always has something
 * to do and so has never had a second shade.
 *
 * ⚠ **There is no greyed state any more, and its parameter is gone with it.** r2 asked for the
 * unhide button to be greyed with nothing outstanding *and* to answer with a toast when
 * pressed, which a disabled control cannot do, so this took a colour that only looked disabled.
 * r4c replaced that state with an offer to hide, in the same tonal shade as its neighbour, and
 * a `dimmed` kept for no caller would be a parameter the next reader has to work out.
 *
 * A Surface rather than a Button, because Button has no long press and Revert to default needs
 * one: holding it opens the configuration that decides what the short press will do.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ActionButton(
    modifier: Modifier = Modifier,
    /** Which tier the card is in — see `managerMetrics`. */
    size: ManagerSize,
    @DrawableRes glyph: Int,
    label: String,
    pending: Boolean = false,
    onClick: () -> Unit,
    onLongClick: (() -> Unit)? = null,
    onLongClickLabel: String? = null,
) {
    // ⚠ **`primary`, up from `primaryContainer` — r30h, at the author's word: the manager's two
    // buttons were "a diff green" from every other button in the app.** They were, and there were
    // three: a filled `Button` anywhere else is `primary`, these were `primaryContainer`, and the
    // Favourites manager button was `secondaryContainer`.
    //
    // ⚠ **This carries r23's reason further rather than reversing it.** r23 raised this pair off
    // `secondaryContainer` because against a translucent frosted card a muted olive stopped
    // reading as a button at all. `primary` is a *stronger* fill than `primaryContainer`, so the
    // constraint that produced that change is better served, not worse. These two are what the
    // dialog is *for*.
    //
    // The red pending state is untouched: it is not competing with these, it replaces one of them.
    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.primary
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onPrimary
    }

    Surface(
        modifier = modifier
            .clip(ButtonDefaults.shape)
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick,
                onLongClickLabel = onLongClickLabel,
            ),
        shape = ButtonDefaults.shape,
        color = container,
        contentColor = content,
    ) {
        Row(
            // ⚠ **Trimmed past Material's icon variant — r5, at the author's word.** The icon
            // padding is 16 dp before the glyph and 24 dp after the label, which was still not
            // enough: `Revert to default` measures about 103 dp of labelLarge, so at that padding
            // a button needs 169 dp and the pair needs a 362 dp card — wider than any tier below
            // roomy, which is why it wrapped to two lines on the author's own S22 Ultra.
            //
            // At 12 dp a side a button needs 153 dp, and every tier is set above it. See
            // [MANAGER_BUTTON_PADDING].
            modifier = Modifier.padding(MANAGER_BUTTON_PADDING),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Icon(
                modifier = Modifier.size(18.dp),
                painter = painterResource(glyph),
                // Null, and deliberately: the label beside it already says what this button
                // is, and a screen reader announcing the glyph as well would say it twice.
                contentDescription = null,
            )

            Spacer(modifier = Modifier.width(8.dp))

            Text(
                text = label,
                // ⚠ **A step down on the compact card buys two things, not one.** The shorter
                // label is the obvious one; the other is that `Revert to default` stops wrapping
                // sooner, and the pair is drawn at `IntrinsicSize.Min`, so the taller of the two
                // sets the height of both.
                style = size.buttonStyle(),
                textAlign = TextAlign.Center,
            )
        }
    }
}

/**
 * How far [MasterPill]'s fill is lifted off the top of the surface ladder.
 *
 * Small on purpose: this row is a neutral that has to be *findable*, not an accent that competes
 * with the two filled buttons at the foot of the dialog.
 */
private const val PILL_LIFT = 0.18f

/**
 * How long a bulk arm stays up after the work ends.
 *
 * Long enough for the state poll that follows a bulk action to land, short enough that it is over
 * before anybody presses anything else. The switches latch the arm, so this is a window rather than
 * a flag.
 */
private const val BULK_ARM_GRACE_MILLIS = 2500L

private val PILL_HEIGHT = 28.dp

/**
 * The same row on a compact card.
 *
 * ⚠ **The shapes are not touched.** [PILL_START_SHAPE]'s 14 dp is half of [PILL_HEIGHT], and a
 * corner radius larger than half the height is clamped to half the height where it is drawn —
 * so at 24 dp the ends stay exactly as round as they look now, with one number to change rather
 * than five.
 */
private val COMPACT_PILL_HEIGHT = 24.dp

/** And on a roomy one. The shapes are untouched for the same reason. */
private val ROOMY_PILL_HEIGHT = 32.dp

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
)


private const val DIMMED_CONTAINER_ALPHA = 0.12f

private const val DIMMED_CONTENT_ALPHA = 0.38f

/**
 * The same mapping the settings screen makes, against this module's own copy of the strings.
 *
 * ⚠ **The decision is not repeated, only the wording.** `overlayBlockReasons` in
 * `:domain:model` is the single answer to why the row will not move; `feature/apps` cannot see
 * `feature/settings`' resources, so what is duplicated is five strings rather than a rule.
 */
@Composable
private fun overlayBlockedPaths(reasons: List<OverlayBlockReason>): List<String> {
    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    val dooaPath = stringResource(R.string.help_path_dooa)

    return reasons.mapNotNull { reason ->
        when (reason) {
            OverlayBlockReason.ForkUnsupported -> null

            OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

            OverlayBlockReason.NothingSelected -> dooaPath
        }
    }
}
