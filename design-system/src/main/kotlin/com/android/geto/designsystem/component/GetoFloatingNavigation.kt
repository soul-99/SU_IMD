/*
 *
 *   Copyright 2026 soul_99 (suIMD)
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
package com.android.geto.designsystem.component

import androidx.compose.animation.AnimatedVisibility
import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.CubicBezierEasing
import androidx.compose.animation.core.animateDpAsState
import androidx.compose.animation.core.tween
import androidx.compose.animation.expandHorizontally
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.shrinkHorizontally
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.IntrinsicSize
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.navigationBars
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.runtime.setValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.Stable
import androidx.compose.runtime.compositionLocalOf
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * One tab, as the floating bar needs it.
 *
 * A plain value rather than the app's own destination type, because `:design-system` is below
 * every feature module and cannot see one. The caller turns its destinations into these.
 */
data class GetoNavItem(
    val icon: ImageVector,
    val label: String,
    val contentDescription: String,
    val selected: Boolean,
    val onClick: () -> Unit,
)

/**
 * The floating tab bar, modelled on the one the author sent as the reference.
 *
 * ⚠ **Every number here is ObtainX 2.9.91's**, read out of `lib/pages/home.dart`: pill radius 30
 * with 5 dp of padding, items at radius 22, 15 dp of side padding when selected against 11 when
 * not, 2 dp between items, icon 21, label 13.5 semibold, and 300 ms of emphasised easing. They are
 * copied rather than approximated because the author asked for *"fluid animations like obtain x"*,
 * and the fluidity is precisely that the selected item's padding and its label animate together so
 * the pill grows and shrinks instead of the label fading in place.
 *
 * ⚠ **[groups] rather than a flat list, at the author's *"disconnect setting as a pill from tab
 * bar on phones"*.** Each group is its own pill with its own background and shadow; the gap
 * between them is what makes Settings read as a separate control rather than a third tab. The
 * grouping is the caller's decision - this only draws what it is handed.
 *
 * ⚠ **Opaque, where the reference is translucent over a blur.** ObtainX puts its pill on 55%
 * `surfaceContainerHighest` behind a `BackdropFilter`; Compose has no backdrop filter, and 55%
 * over an unblurred list is a window onto the list rather than a control. `progressiveEdgeBlur`
 * already blurs what is behind the bar on the two app tabs, so the pill sits on a settled
 * background and can afford to be solid.
 */
@Composable
fun GetoFloatingNavBar(
    groups: List<List<GetoNavItem>>,
    modifier: Modifier = Modifier,
) {
    Row(
        modifier = modifier
            .navigationBarsPadding()
            .padding(bottom = BAR_BOTTOM_MARGIN),
        horizontalArrangement = Arrangement.spacedBy(GROUP_GAP),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        groups.forEach { group ->
            NavPill {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    group.forEach { item ->
                        BarItem(item = item)
                    }
                }
            }
        }
    }
}

/**
 * The same bar stood on its left edge, for a window wide enough to give up the room.
 *
 * ⚠ **Every label is drawn, always** - the author's *"on tablets show labels for all tabs always
 * not only selected one"*. That is not only a preference: it is what stops the rail changing width
 * as tabs are pressed, which on a side rail would shove the whole page sideways on every tap. What
 * animates on selection is the container behind the item and nothing else.
 *
 * ⚠ **Both pills are the width of the widest one**, at his instruction. `IntrinsicSize.Max` on the
 * column is what does it: the column measures its widest child - "Favourites" - and every pill
 * fills that. Left to themselves the Settings pill would be visibly narrower and the pair would
 * read as two unrelated controls rather than one rail with a gap in it.
 */
@Composable
fun GetoFloatingNavRail(
    groups: List<List<GetoNavItem>>,
    modifier: Modifier = Modifier,
) {
    Column(
        modifier = modifier
            .systemBarsPadding()
            .padding(start = RAIL_SIDE_MARGIN)
            // ⚠ **Capped, and the cap is the same number the caller indents its content by.**
            // The rail's width is intrinsic - as wide as the word "Favourites" in whatever
            // language is loaded - and the page beside it has to reserve room for it without
            // being able to measure it. The cap is what makes GetoNavRailReservedWidth an
            // honest promise rather than a guess that a long translation could overrun.
            .widthIn(max = GetoNavRailReservedWidth - RAIL_SIDE_MARGIN * 2)
            .width(IntrinsicSize.Max),
        verticalArrangement = Arrangement.spacedBy(GROUP_GAP),
        horizontalAlignment = Alignment.Start,
    ) {
        groups.forEach { group ->
            NavPill(modifier = Modifier.fillMaxWidth()) {
                Column(modifier = Modifier.fillMaxWidth()) {
                    group.forEach { item ->
                        RailItem(item = item)
                    }
                }
            }
        }
    }
}

/** The container the reference calls a pill: radius 30, 5 dp of padding, elevation 6. */
@Composable
private fun NavPill(
    modifier: Modifier = Modifier,
    content: @Composable () -> Unit,
) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(PILL_RADIUS),
        color = MaterialTheme.colorScheme.surfaceContainerHighest,
        shadowElevation = PILL_ELEVATION,
    ) {
        Row(modifier = Modifier.padding(PILL_PADDING)) {
            content()
        }
    }
}

/**
 * One item in the bottom bar: icon always, label only while selected.
 *
 * The label is inside an [AnimatedVisibility] that expands horizontally rather than fading in
 * place, and the item's own side padding animates on the same curve and duration. Both together
 * are what make the pill appear to grow around the selection.
 */
@Composable
private fun BarItem(item: GetoNavItem) {
    val container by animateColorAsState(
        targetValue = if (item.selected) {
            MaterialTheme.colorScheme.primary
        } else {
            Color.Transparent
        },
        animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
        label = "navItemContainer",
    )

    val content by animateColorAsState(
        targetValue = if (item.selected) {
            MaterialTheme.colorScheme.onPrimary
        } else {
            MaterialTheme.colorScheme.onSurfaceVariant
        },
        animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
        label = "navItemContent",
    )

    val sidePadding by animateDpAsState(
        targetValue = if (item.selected) ITEM_PADDING_SELECTED else ITEM_PADDING,
        animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
        label = "navItemPadding",
    )

    Row(
        modifier = Modifier
            .padding(horizontal = ITEM_GAP)
            .clip(RoundedCornerShape(ITEM_RADIUS))
            .background(container)
            .clickable(onClick = item.onClick)
            .padding(horizontal = sidePadding, vertical = ITEM_PADDING_VERTICAL),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(ICON_SIZE),
            imageVector = item.icon,
            contentDescription = item.contentDescription,
            tint = content,
        )

        AnimatedVisibility(
            visible = item.selected,
            enter = expandHorizontally(
                animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
            ) + fadeIn(animationSpec = tween(durationMillis = MOTION_MILLIS)),
            exit = shrinkHorizontally(
                animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
            ) + fadeOut(animationSpec = tween(durationMillis = MOTION_MILLIS)),
        ) {
            Text(
                modifier = Modifier.padding(start = LABEL_GAP),
                text = item.label,
                color = content,
                fontSize = LABEL_SIZE,
                fontWeight = FontWeight.SemiBold,
                maxLines = 1,
            )
        }
    }
}

/** One item in the side rail: icon and label, both always drawn. */
@Composable
private fun RailItem(item: GetoNavItem) {
    val container by animateColorAsState(
        targetValue = if (item.selected) {
            MaterialTheme.colorScheme.primary
        } else {
            Color.Transparent
        },
        animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
        label = "railItemContainer",
    )

    val content by animateColorAsState(
        targetValue = if (item.selected) {
            MaterialTheme.colorScheme.onPrimary
        } else {
            MaterialTheme.colorScheme.onSurfaceVariant
        },
        animationSpec = tween(durationMillis = MOTION_MILLIS, easing = Emphasised),
        label = "railItemContent",
    )

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = ITEM_GAP)
            .clip(RoundedCornerShape(ITEM_RADIUS))
            .background(container)
            .clickable(onClick = item.onClick)
            .padding(horizontal = RAIL_ITEM_PADDING, vertical = ITEM_PADDING_VERTICAL),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Icon(
            modifier = Modifier.size(ICON_SIZE),
            imageVector = item.icon,
            contentDescription = item.contentDescription,
            tint = content,
        )

        Text(
            modifier = Modifier.padding(start = LABEL_GAP),
            text = item.label,
            color = content,
            fontSize = LABEL_SIZE,
            fontWeight = FontWeight.SemiBold,
            maxLines = 1,
        )
    }
}

/**
 * Material's emphasised easing, written out rather than imported.
 *
 * The reference calls it `Curves.easeInOutCubicEmphasized`; these are the same four control points.
 * Spelled here so the bar does not depend on which Material 3 version exposes a motion scheme.
 */
private val Emphasised = CubicBezierEasing(0.2f, 0f, 0f, 1f)

private const val MOTION_MILLIS = 300

private val PILL_RADIUS = 30.dp

private val PILL_PADDING = 5.dp

private val PILL_ELEVATION = 6.dp

private val ITEM_RADIUS = 22.dp

private val ITEM_GAP = 2.dp

private val ITEM_PADDING = 11.dp

private val ITEM_PADDING_SELECTED = 15.dp

private val ITEM_PADDING_VERTICAL = 10.dp

/**
 * Wider than the bar's own, at the author's *"increase its width"*.
 *
 * A rail is read as a column of destinations rather than a row of icons, so its items want more
 * air around the words; and the extra width is what makes the two pills read as one rail.
 */
private val RAIL_ITEM_PADDING = 18.dp

private val ICON_SIZE = 21.dp

private val LABEL_GAP = 7.dp

private val LABEL_SIZE = 13.5.sp

/** Between the tab group and the Settings pill beside it. */
private val GROUP_GAP = 8.dp

private val BAR_BOTTOM_MARGIN = 14.dp

private val RAIL_SIDE_MARGIN = 12.dp

/**
 * How much room the page must leave along its left edge for [GetoFloatingNavRail].
 *
 * The rail floats over the page rather than displacing it, so nothing in the layout forces this;
 * the caller indents by it and the rail is capped to it. Two numbers that have to agree, which is
 * why they are one number.
 */
val GetoNavRailReservedWidth: Dp = 176.dp

/**
 * How far the last row of a scrolling list must be able to travel past the bottom of the window
 * so that [GetoFloatingNavBar] never comes to rest on top of it.
 *
 * The bar floats over the content on purpose - that is what the blurred band beneath it is for -
 * so this is added as content padding rather than taken out of the layout. An item ends up above
 * the bar when scrolled to the end and behind it while scrolling past, which is the intent.
 */
val GetoNavBarReservedHeight: Dp = 96.dp

/**
 * How tall the floating header is **right now**, as the collapsing top bar reports it.
 *
 * ⚠ **The search field on the two app tabs rides on this, and that is the whole reason it
 * exists.** r11 pinned the field at the *expanded* height, so when the title collapsed the field
 * stayed where it was and left the gap the author reported. The list's content padding still uses
 * the expanded height - an inset that moved would drag the list under the finger - but anything
 * *drawn* in the header has to follow the bar.
 *
 * Provided by `HomeScreen`, which owns the scroll behaviour. The default is the expanded height,
 * which is what a preview or a screen composed outside the home scaffold should get.
 */
val LocalFloatingHeaderHeight = compositionLocalOf { GetoLargeTopBarHeight }

/**
 * The floating header's live geometry, as an object whose identity never changes.
 *
 * ⚠ **This exists so that a scroll does not recompose a page — r29.** Both numbers change on
 * every frame of a collapse. Handed down as values through `compositionLocalOf`, every reader
 * is invalidated every frame, and on the settings tab that reader was `Success`: eleven hundred
 * lines, eighty-one composable calls and thirty-two remembered slots, re-executed per frame for
 * two floats. Handed down as *this*, behind a [staticCompositionLocalOf] and pinned by a
 * `remember` in `HomeScreen`, nothing is invalidated by providing it at all; a page reads the
 * numbers inside its draw lambdas, where a change costs a redraw and not a recomposition.
 *
 * ⚠ **Read these inside a draw or layout lambda, never in a composable body.** Reading
 * [fraction] during composition puts the per-frame invalidation straight back, which is the
 * whole thing this replaced.
 */
@Stable
class HeaderMetrics {
    /** How far the header has collapsed: 0 at the top of the page, 1 once the title is small. */
    var fraction: Float by mutableFloatStateOf(0f)

    /** How tall the header is right now, status bar included. */
    var height: Dp by mutableStateOf(GetoLargeTopBarHeight)
}

/**
 * The one [HeaderMetrics] for the window, provided by `HomeScreen`, which owns the scroll.
 *
 * ⚠ **Static on purpose.** A non-static local would track every read and undo the point.
 */
val LocalHeaderMetrics = staticCompositionLocalOf { HeaderMetrics() }

/**
 * The expanded height of the app's large top bar.
 *
 * ⚠ **Written down because the header floats since r11** and the page beneath it therefore has to
 * reserve room it can no longer measure. Material's own large top app bar container is 152 dp
 * expanded; the value is not exported by Material 3, so it is named here rather than repeated as a
 * literal in three screens.
 */
val GetoLargeTopBarHeight: Dp = 152.dp

/** The search field's full height on the two app tabs, its own 6 dp of vertical padding included. */
val GetoSearchFieldHeight: Dp = 64.dp

/**
 * How much room a page must leave at its top for the floating header — the status bar and the
 * expanded title above it.
 *
 * ⚠ **The *expanded* height, not the current one.** The bar collapses as the page scrolls, and a
 * content inset that followed it would move the list under the finger. Fixed at the expanded
 * height, the list starts below the title and travels normally; what changes on scroll is how much
 * of it has passed underneath.
 */
@Composable
fun getoFloatingHeaderInset(): Dp =
    WindowInsets.statusBars.asPaddingValues().calculateTopPadding() + GetoLargeTopBarHeight

/**
 * Which way the tab bar reads: along the bottom of the window, or standing on its left edge.
 *
 * ⚠ **One answer, and since r12b three callers read it.** `HomeScreen` draws the bar from it and
 * decides which way a tab change slides and whether a sideways drag changes tab at all; the two
 * insets below decide how much room a page leaves at its foot; and the app's floating buttons sit
 * on the second of those. It lived in `:feature:home` as a private pair of numbers until the
 * buttons needed the same answer, and two copies of a breakpoint are two answers that can
 * disagree.
 *
 * The breakpoints are the ones the navigation suite used before r10 replaced it, kept rather than
 * re-chosen so that a device which showed a rail in r9 still shows one now.
 */
@Composable
fun getoUsesSideRail(): Boolean {
    val configuration = LocalConfiguration.current

    return configuration.screenWidthDp >= NAVIGATION_RAIL_MIN_WIDTH_DP &&
        configuration.screenHeightDp >= NAVIGATION_RAIL_MIN_HEIGHT_DP
}

/**
 * The same for the bottom: the system navigation bar, and the floating tab bar above it when
 * there is one.
 *
 * ⚠ **Nothing is reserved for the bar on a tablet — r12b.** The bar stands down the left edge
 * there, so a page that still held [GetoNavBarReservedHeight] clear at its foot was holding it
 * clear of nothing, and the author saw the two floating buttons hovering a bar's height above the
 * bottom of the screen with empty space beneath them.
 */
@Composable
fun getoFloatingBarInset(): Dp =
    WindowInsets.navigationBars.asPaddingValues().calculateBottomPadding() +
        (if (getoUsesSideRail()) 0.dp else GetoNavBarReservedHeight)

/**
 * Where the floating buttons rest above the bottom edge.
 *
 * On a phone that is exactly [getoFloatingBarInset] — flush with the top of the tab bar, which is
 * where the author put them in r12. On a tablet there is no bar underneath them, so they take the
 * ordinary margin off the window edge instead: *"keep the unhide and settings manager button at
 * bottom as previously"*.
 */
@Composable
fun getoFloatingActionInset(): Dp = getoFloatingBarInset() +
    (if (getoUsesSideRail()) FLOATING_ACTION_EDGE_MARGIN else 0.dp)

/** The window a navigation rail needs before the bar is stood on its left edge. */
private const val NAVIGATION_RAIL_MIN_WIDTH_DP = 600

/**
 * And the height below which it stays at the bottom however wide the window is.
 *
 * A phone in landscape is wide and short: there is room beside the content for a rail but not
 * enough above and below it to give up any, so the bar stays where it is. Without this test a
 * rotated phone would get a rail down the side of a 400 dp-tall window, animate vertically
 * against it, and lose the swipe it had a moment earlier in portrait.
 */
private const val NAVIGATION_RAIL_MIN_HEIGHT_DP = 480

/** The same margin the buttons already keep from the right-hand edge. */
private val FLOATING_ACTION_EDGE_MARGIN: Dp = 16.dp
