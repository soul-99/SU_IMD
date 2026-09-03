/*
 *
 *   Copyright 2023 Einstein Blanco
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
package com.android.geto.feature.home

import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.BoxScope
import androidx.compose.foundation.layout.WindowInsets
import androidx.compose.foundation.layout.asPaddingValues
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.statusBars
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.layout.wrapContentHeight
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.saveable.listSaver
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.snapshots.SnapshotStateList
import androidx.compose.runtime.toMutableStateList
import androidx.compose.runtime.setValue
import androidx.compose.ui.ExperimentalComposeUiApi
import androidx.compose.ui.Modifier
import androidx.compose.ui.input.nestedscroll.NestedScrollConnection
import androidx.compose.ui.input.nestedscroll.NestedScrollSource
import androidx.compose.ui.input.nestedscroll.nestedScroll
import androidx.compose.ui.res.stringResource
import androidx.navigation.NavDestination
import androidx.navigation.NavDestination.Companion.hasRoute
import androidx.navigation.NavDestination.Companion.hierarchy
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.compose.animation.AnimatedContentTransitionScope
import androidx.compose.animation.EnterTransition
import androidx.compose.animation.ExitTransition
import androidx.compose.animation.core.tween
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.slideInHorizontally
import androidx.compose.animation.slideInVertically
import androidx.compose.animation.slideOutHorizontally
import androidx.compose.animation.slideOutVertically
import androidx.compose.ui.Alignment
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.TransformOrigin
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.lerp
import com.android.geto.designsystem.component.GetoFloatingNavBar
import com.android.geto.designsystem.component.GetoFloatingNavRail
import com.android.geto.designsystem.component.GetoNavItem
import com.android.geto.designsystem.component.GetoLargeTopBarHeight
import com.android.geto.designsystem.component.GetoNavRailReservedWidth
import com.android.geto.designsystem.component.getoUsesSideRail
import com.android.geto.designsystem.component.LocalFloatingHeaderHeight
import com.android.geto.designsystem.component.HeaderMetrics
import com.android.geto.designsystem.component.LocalHeaderMetrics
import kotlin.math.abs
import androidx.navigation.NavBackStackEntry
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.android.geto.designsystem.component.LocalAdvancedSettingsRequest
import com.android.geto.designsystem.component.LocalRevertConfigurationRequest
import com.android.geto.feature.home.navigation.HomeDestination
import kotlin.reflect.KClass

@Composable
internal fun HomeRoute(
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState,
    topLevelDestinations: List<HomeDestination>,
    startDestination: KClass<*>,
    onClickHomeDestination: (NavHostController, HomeDestination) -> Unit,
    onSettingsTabRequest: (NavHostController) -> Unit,
    floatingActions: @Composable BoxScope.(HomeDestination?) -> Unit = {},
    builder: NavGraphBuilder.() -> Unit,
) {
    HomeScreen(
        modifier = modifier,
        snackbarHostState = snackbarHostState,
        topLevelDestinations = topLevelDestinations,
        startDestination = startDestination,
        onClickHomeDestination = onClickHomeDestination,
        onSettingsTabRequest = onSettingsTabRequest,
        floatingActions = floatingActions,
        builder = builder,
    )
}

@OptIn(ExperimentalMaterial3Api::class, ExperimentalComposeUiApi::class)
@Composable
internal fun HomeScreen(
    modifier: Modifier = Modifier,
    snackbarHostState: SnackbarHostState,
    topLevelDestinations: List<HomeDestination>,
    startDestination: KClass<*>,
    onClickHomeDestination: (NavHostController, HomeDestination) -> Unit,
    onSettingsTabRequest: (NavHostController) -> Unit,
    floatingActions: @Composable BoxScope.(HomeDestination?) -> Unit = {},
    builder: NavGraphBuilder.() -> Unit,
) {
    val navController = rememberNavController()

    // Something outside the graph has asked for a particular tab. The nav controller is
    // created here and not exposed, so the request comes in as a value and the navigating
    // is done here rather than by the caller reaching in.
    //
    // The high-water mark is what makes these fire once per request rather than once per
    // visit. This screen leaves composition whenever the per-app configuration page is opened
    // - that page is a destination in the graph *above* this one - so coming back builds a
    // fresh LaunchedEffect, which without this would re-run against the same standing value
    // and bounce the user onto Settings every time they backed out of an app's settings.
    // Saved rather than remembered, so it survives that round trip as the counter does.
    var handled by rememberSaveable { mutableIntStateOf(0) }

    val revertConfigurationRequest = LocalRevertConfigurationRequest.current

    // The other request that wants this tab: a re-launch after the hiding-unhiding mechanism
    // was changed, which opens Settings with Advanced already expanded. Both land on the same
    // tab and are told apart by the Settings screen, which reads the two counts separately -
    // one opens a dialog, the other expands a section.
    val advancedSettingsRequest = LocalAdvancedSettingsRequest.current

    // One mark for both, because both do the same thing to this screen and the counts cannot
    // rise at the same moment: one comes from a dialog in a running app, the other from the
    // intent that started it.
    val pending = maxOf(revertConfigurationRequest, advancedSettingsRequest)

    LaunchedEffect(pending) {
        if (pending > handled) {
            handled = pending

            onSettingsTabRequest(navController)
        }
    }

    val currentDestination = navController.currentBackStackEntryAsState().value?.destination

    val topBarTitleStringResource = topLevelDestinations.find { destination ->
        currentDestination.isTopLevelDestinationInHierarchy(destination.route)
    }?.label ?: topLevelDestinations.first().label

    // Which way the tab bar reads. Three things follow from it and nothing else decides them:
    // whether the bar is drawn along the bottom or down the left, which way a tab change
    // slides, and whether a sideways drag changes tab at all.
    //
    // ⚠ **This used to be a second opinion; since r10 it is the only one.** The navigation
    // suite chose the layout by itself and would not say which it had chosen, so this
    // computation existed alongside it purely to keep the slide travelling the right way -
    // two answers that could disagree. The suite is gone and the bar is drawn from this value,
    // so they cannot.
    //
    // ⚠ **The breakpoints moved to :design-system in r12b.** The floating buttons need this same
    // answer — a window with no bar along its foot must not keep the bar's height clear of one —
    // and a second copy of a breakpoint is a second answer that can disagree with this one.
    val sideRail = getoUsesSideRail()

    // Which tab is showing, as a position in the bar rather than a route. The swipe needs a
    // number to add one to; nothing else does.
    val selectedIndex = topLevelDestinations.indexOfFirst { destination ->
        currentDestination.isTopLevelDestinationInHierarchy(destination.route)
    }

    // ⚠ **Material's scroll behaviours are gone — r13c, and the author's video is why.** Both of
    // them *consume* the drag in `onPreScroll`: the bar helps itself to the first 120 dp of every
    // downward gesture and passes on what is left, so the header moves, finishes, and only then
    // does the list start. He described it exactly: *"when i first scroll up the header and
    // search bar moves first then the page contents, can't they all move together?"*
    //
    // Collapsing reads `consumed` — what the list actually took — so the header travels with the
    // page rather than ahead of it. **Expanding reads `available`, which r14 changed:** that is
    // what is left over after the list has taken its share, and mid-list it is zero, so an upward
    // drag moves only the page. It becomes non-zero exactly when the list has run out of room —
    // the author's *"the header and search bar should only move when i reach the top of the
    // page"*. The leftover is consumed while the header opens, so the overscroll stretch does not
    // start until the header is fully out.
    //
    // ⚠ **One offset per tab — r16.** It was a single number for the whole scaffold, so scrolling
    // All apps collapsed the header that Favourites came back to, and Favourites — a short list
    // with nothing to scroll — had no way to give it back: *"i cannot scroll it up to uncollapse
    // it"*. A tab's header is now its own, remembered while the other tabs move.
    val density = LocalDensity.current

    val collapseRange = with(density) { (GetoLargeTopBarHeight - COLLAPSED_TITLE_HEIGHT).toPx() }

    val headerOffsets = rememberSaveable(
        topLevelDestinations.size,
        // ⚠ **Both type arguments spelled out.** `saver` is declared before `init`, so leaving
        // them to inference asks the compiler to work out the element type from a lambda it has
        // not reached yet.
        saver = listSaver<SnapshotStateList<Float>, Float>(
            save = { it.toList() },
            restore = { it.toMutableStateList() },
        ),
    ) {
        List(topLevelDestinations.size) { 0f }.toMutableStateList()
    }

    // -1 while the back stack settles on a destination; the scaffold still draws, so it needs an
    // answer rather than a crash.
    val headerOffset = headerOffsets.getOrElse(selectedIndex) { 0f }

    val headerScroll = remember(collapseRange, selectedIndex) {
        object : NestedScrollConnection {
            override fun onPostScroll(
                consumed: Offset,
                available: Offset,
                source: NestedScrollSource,
            ): Offset {
                if (selectedIndex !in headerOffsets.indices) return Offset.Zero

                // Downwards, follow the page. Upwards, follow only what the page could not use.
                val delta = if (consumed.y < 0f) consumed.y else available.y

                if (delta == 0f) return Offset.Zero

                val before = headerOffsets[selectedIndex]

                val after = (before + delta).coerceIn(-collapseRange, 0f)

                headerOffsets[selectedIndex] = after

                // Collapsing takes nothing: the page has already scrolled by that much and the
                // header is only keeping pace. Opening takes what it used, so the list's
                // overscroll does not stretch at the same time.
                return if (delta > 0f) Offset(0f, after - before) else Offset.Zero
            }
        }
    }

    val collapsedFraction = if (collapseRange > 0f) -headerOffset / collapseRange else 0f

    val navItems = topLevelDestinations.mapIndexed { index, destination ->
        GetoNavItem(
            icon = destination.icon,
            label = stringResource(id = destination.label),
            contentDescription = stringResource(id = destination.contentDescription),
            selected = index == selectedIndex,
            onClick = {
                onClickHomeDestination(navController, destination)
            },
        )
    }

    // ⚠ **The last destination is pulled into its own pill** — the author's "disconnect setting
    // as a pill from tab bar on phones". Expressed as "the last one" rather than as "Settings"
    // because this module cannot see the app's destination enum; the app decides the order and
    // Settings is last in it. A single-tab bar would otherwise be split into a pill and an empty
    // one, so that case is answered before the split.
    val navGroups = if (navItems.size > 1) {
        listOf(navItems.dropLast(1), listOf(navItems.last()))
    } else {
        listOf(navItems)
    }

    // How tall the header is right now, status bar included. The two app tabs hang their search
    // field off this so it travels with the title instead of staying where the title used to be.
    val headerHeight = WindowInsets.statusBars.asPaddingValues().calculateTopPadding() +
        lerp(GetoLargeTopBarHeight, COLLAPSED_TITLE_HEIGHT, collapsedFraction)

    // ⚠ **Pinned by `remember`, written in a `SideEffect` — r29.** The object must outlive every
    // recomposition or a page's reference goes stale, and the two numbers must be written after
    // the composition that produced them rather than during it. Writing them here rather than
    // providing them as values is what stops a scroll invalidating every page that reads them.
    val headerMetrics = remember { HeaderMetrics() }

    SideEffect {
        headerMetrics.fraction = collapsedFraction

        headerMetrics.height = headerHeight
    }

    CompositionLocalProvider(
        // Still a value, and still read during composition by the two app tabs: their search
        // field is laid out against it and has to move with the title. That is a layout read,
        // not a draw one, and it is left alone.
        LocalFloatingHeaderHeight provides headerHeight,
        LocalHeaderMetrics provides headerMetrics,
    ) {
    Box(modifier = Modifier.fillMaxSize()) {
        // The page, indented on a tablet so the rail has somewhere to float. ⚠ **The rail floats
        // over the window rather than displacing it**, so this indent and
        // GetoNavRailReservedWidth are two numbers that have to agree - which is why there is
        // only one of them.
        Box(
            modifier = if (sideRail) {
                Modifier
                    .fillMaxSize()
                    .padding(start = GetoNavRailReservedWidth)
            } else {
                Modifier.fillMaxSize()
            },
        ) {
        Scaffold(
            // ⚠ **No topBar slot, and no window insets — r11.** Both of those are *layout*: the
            // slot pushes the content down and the insets pad it in, and between them they are
            // the background the author asked to remove from behind the title. The bar is drawn
            // below as an overlay instead, and it applies the status-bar inset itself; the tab
            // bar applies the navigation-bar one. Nothing is lost except the displacement.
            contentWindowInsets = WindowInsets(0, 0, 0, 0),
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
            NavHost(
                modifier = modifier
                    .nestedScroll(headerScroll)
                    .padding(paddingValues)
                    .consumeWindowInsets(paddingValues)
                    // ⚠ **Phones only, and gated on the same value the slide direction reads.**
                    // Down the side the tabs are stacked, so a sideways drag crosses the bar
                    // instead of running along it and would mean nothing.
                    .tabSwipe(enabled = !sideRail, selectedIndex = selectedIndex) { target ->
                        onClickHomeDestination(navController, topLevelDestinations[target])
                    },
                navController = navController,
                startDestination = startDestination,
                // The tabs slide the way the bar reads. Every destination in this host is a
                // top-level tab sitting beside the others, so the honest motion is along the
                // bar - lateral while the bar is at the bottom, vertical once it becomes a
                // rail down the side - and which way it goes is worked out from the two
                // entries themselves rather than from remembered state, which cannot disagree
                // with what is on screen.
                //
                // A fraction of the pane rather than the whole of it, and this is what makes
                // it work on a tablet as well as a phone: a full-pane slide is a fixed
                // *distance*, so the wider the pane the further and the slower the content
                // travels for the same duration. A sixth of the pane is the same gesture at
                // any size. The fade does most of the work; the offset only says which way.
                enterTransition = { slideIntoTab(isForward(topLevelDestinations), sideRail) },
                exitTransition = { slideOutOfTab(isForward(topLevelDestinations), sideRail) },
                // Popping is the same movement backwards - the tabs have no depth to go into.
                popEnterTransition = { slideIntoTab(isForward(topLevelDestinations), sideRail) },
                popExitTransition = { slideOutOfTab(isForward(topLevelDestinations), sideRail) },
                builder = builder,
            )
        }

        // ⚠ **Drawn here rather than put in a `topBar` slot**, so the list runs underneath it —
        // the author's "display swiped up app list behind them". What keeps it readable is the
        // blurred band each tab draws at its own top edge, not a container colour.
        CollapsingTitle(
            modifier = Modifier.align(Alignment.TopStart),
            title = stringResource(id = topBarTitleStringResource),
            collapsedFraction = collapsedFraction,
        )
        }

        // Drawn after the scaffold and so over it, which is what makes it float. On a phone that
        // is the whole reason the blurred band beneath it has anything to blur.
        if (sideRail) {
            GetoFloatingNavRail(
                groups = navGroups,
                modifier = Modifier.align(Alignment.CenterStart),
            )
        } else {
            GetoFloatingNavBar(
                groups = navGroups,
                modifier = Modifier.align(Alignment.BottomCenter),
            )
        }

        // ⚠ **Outside the tab host, so a swipe does not carry them with it** — the author's "do
        // not move them when swiping away from one tab to another". Drawn before the bar and the
        // rail so those stay on top; the caller pads them clear of whichever one is showing.
        floatingActions(
            topLevelDestinations.getOrNull(selectedIndex),
        )
    }
    }
}

/**
 * A sideways drag changes tab, at the author's instruction and on phones alone.
 *
 * ⚠ **Fires once, on release, rather than following the finger.** A pager would have to own the
 * three destinations itself, and they are a navigation graph with a back stack, deep links and an
 * outside caller that asks for the Settings tab by name. Reading the gesture and pressing the tab
 * the user would have pressed keeps one source of truth for where the app is, and the existing
 * slide animation is already the movement a pager would have drawn.
 *
 * ⚠ **Keyed on [selectedIndex].** `pointerInput` captures its block once per key, so a stale key
 * would leave the gesture computing its neighbour from whichever tab was showing when the handler
 * was installed - a swipe that worked once and then went nowhere.
 *
 * ⚠ **An unknown tab does nothing.** [selectedIndex] is -1 while something outside the three is
 * showing; adding one to that is a real index and would navigate somewhere the user did not ask
 * for.
 */
private fun Modifier.tabSwipe(
    enabled: Boolean,
    selectedIndex: Int,
    onChangeTab: (Int) -> Unit,
): Modifier = if (!enabled) {
    this
} else {
    pointerInput(selectedIndex) {
        var travelled = 0f

        val threshold = SWIPE_THRESHOLD.toPx()

        detectHorizontalDragGestures(
            onDragStart = { travelled = 0f },
            onDragEnd = {
                if (selectedIndex >= 0 && abs(travelled) >= threshold) {
                    // Dragging left reveals what is to the right, which is the next tab.
                    val target = selectedIndex + if (travelled < 0f) 1 else -1

                    if (target >= 0 && target < TAB_COUNT_CEILING) {
                        onChangeTab(target)
                    }
                }
            },
            onDragCancel = { travelled = 0f },
            onHorizontalDrag = { _, amount -> travelled += amount },
        )
    }
}

/**
 * How far a finger has to travel before a drag counts as a tab change.
 *
 * Well past the touch slop that started the gesture, because the two lazy lists underneath are
 * scrolled vertically all day and a short diagonal flick should stay a scroll.
 */
private val SWIPE_THRESHOLD: Dp = 72.dp

/**
 * The number of tabs a swipe may land on.
 *
 * ⚠ **A guard, not a count.** The real list is the caller's and the target is checked against it
 * by indexing; this stops a target beyond the end from being handed over in the first place. It is
 * three because the app has three top-level destinations, and if a fourth is ever added the swipe
 * would simply stop at the third until this follows - which is a visible, harmless failure rather
 * than a crash.
 */
private const val TAB_COUNT_CEILING = 3

/**
 * The tab's name, shrinking as the page scrolls and growing back as it returns.
 *
 * ⚠ **Drawn by hand rather than by `LargeTopAppBar`, and the author's video is why.** Material's
 * large bar collapses by cross-fading two `Text` nodes at two different type scales, which on his
 * recording reads as a ghost of the title hanging above the title. He asked for the size itself to
 * change — *"minimise to the smaller size and maximise when scrolled up with zoom animation"* — so
 * there is one Text here and it is scaled.
 *
 * ⚠ **Scaled from its own bottom-left corner.** `graphicsLayer` changes what is drawn without
 * re-measuring anything, so the text stays on one baseline and one left edge while its size moves
 * continuously with the scroll. Anchoring anywhere else would make the title drift sideways or
 * upwards as it shrank.
 *
 * ⚠ **No container colour.** The list runs underneath; the blurred band each tab draws is what
 * keeps this readable.
 */
@Composable
private fun CollapsingTitle(
    modifier: Modifier = Modifier,
    title: String,
    collapsedFraction: Float,
) {
    // ⚠ **Not `lerp`.** The two lines below interpolate `Dp` and need
    // `androidx.compose.ui.unit.lerp`; this one is a `Float` and would need
    // `androidx.compose.ui.util.lerp`. One file, one name, two packages — so this one is
    // spelled out and the import stays unambiguous. `lerp(a, b, t)` is `a + (b - a) * t`.
    val scale = 1f + (COLLAPSED_TITLE_SCALE - 1f) * collapsedFraction

    Box(
        modifier = modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .height(lerp(GetoLargeTopBarHeight, COLLAPSED_TITLE_HEIGHT, collapsedFraction)),
    ) {
        Text(
            // ⚠ **`unbounded`, and this is what was cutting the title — r14.** A `Box` measures
            // its children against its own maximum, so once the header collapsed to 32 dp the
            // 36 dp line of `headlineMedium` was measured with `maxHeight = 32 dp` and the `Text`
            // clipped its own glyphs — the author's *"tab header font is cut from bottom"*.
            // Nothing was drawing over it; it was never drawn. Measured unbounded it takes its
            // natural height and hangs out of the box, which is exactly what a title scaled about
            // its own bottom edge is meant to do.
            modifier = Modifier
                .align(Alignment.BottomStart)
                .wrapContentHeight(align = Alignment.Bottom, unbounded = true)
                .padding(start = TITLE_START_PADDING, bottom = TITLE_BOTTOM_PADDING)
                .graphicsLayer {
                    scaleX = scale

                    scaleY = scale

                    transformOrigin = TransformOrigin(pivotFractionX = 0f, pivotFractionY = 1f)
                },
            text = title,
            style = MaterialTheme.typography.headlineMedium,
            color = MaterialTheme.colorScheme.onSurface,
            maxLines = 1,
        )
    }
}

/**
 * What the header collapses to.
 *
 * ⚠ **32 dp rather than Material's 64 — the author's r12b *"i need header and searchbar to be
 * more up after scrolling down"*, and his r13 *"move tab header, search bar a bit more up"*.** Material's small top bar is 64 dp because it holds a row of
 * icon buttons; this one holds a single 22 sp line and nothing else, so most of that height was
 * air. With [TITLE_BOTTOM_PADDING] below it the collapsed title still clears its own line box,
 * and the search field — which is drawn at the header's current height — rises by the same 24 dp.
 */
private val COLLAPSED_TITLE_HEIGHT: Dp = 32.dp

/**
 * And how small the title itself gets.
 *
 * Material's two type scales for a large bar are `headlineMedium` at 28 sp expanded and
 * `titleLarge` at 22 sp collapsed. This goes one step further, to 20 sp, and r13c is why: the
 * author found the collapsed title clipped by the search field, and it is lifted clear by giving
 * it more room below rather than by moving the field — which he said was where he wanted it. A
 * title that lifts without shrinking would reach the status bar instead. Expressed as a ratio
 * rather than as a second text style because the point is that it is continuous — every value
 * between the two is drawn.
 */
private const val COLLAPSED_TITLE_SCALE = 20f / 28f

private val TITLE_START_PADDING: Dp = 16.dp

/**
 * How far the title sits above the bottom of the header.
 *
 * ⚠ **This is what lifts the collapsed title, because it is scaled about its own bottom edge.**
 * r13 cut it to 4 dp along with the header height and put the title into the search field; 10 dp
 * takes it back out with the field left where it is.
 */
private val TITLE_BOTTOM_PADDING: Dp = 10.dp

private fun NavDestination?.isTopLevelDestinationInHierarchy(route: KClass<*>) = this?.hierarchy?.any {
    it.hasRoute(route)
} ?: false

/**
 * How far a tab slides in or out, as a fraction of the pane it is sliding across.
 *
 * Short on purpose. This is a change of tab, not a change of place: the destination is already
 * named in the bar the user just pressed, so the animation only has to acknowledge the press
 * and get out of the way. Anything longer becomes something to wait through on every tab
 * change, which is the most frequent gesture in the app.
 */
private const val TAB_SLIDE_FRACTION = 6

/** Short enough to feel immediate, long enough not to strobe. */
private const val TAB_DURATION_MILLIS = 220

/**
 * Which way this tab change is travelling, worked out from the two destinations.
 *
 * Their order in [topLevelDestinations] is the order they appear in the navigation bar, so a
 * higher index is to the right and content coming from a higher index enters from the right.
 * An unrecognised destination - anything that is not one of the tabs - answers "forward",
 * which is the neutral reading rather than a special case worth writing code for.
 */
private fun AnimatedContentTransitionScope<NavBackStackEntry>.isForward(
    topLevelDestinations: List<HomeDestination>,
): Boolean {
    fun index(entry: NavBackStackEntry) = topLevelDestinations.indexOfFirst { destination ->
        entry.destination.isTopLevelDestinationInHierarchy(destination.route)
    }

    val from = index(initialState)
    val to = index(targetState)

    return from == -1 || to == -1 || to >= from
}

/**
 * The tab arriving, travelling along the bar rather than across it.
 *
 * [sideRail] is the only difference between the two axes: a rail stacks its items top to
 * bottom, so a higher index is *below* rather than to the right, and content coming from a
 * higher index enters from below. The distance, the direction rule and the fade are the same
 * either way - it is one movement rotated a quarter turn, not two animations.
 */
private fun slideIntoTab(forward: Boolean, sideRail: Boolean): EnterTransition {
    val spec = tween<IntOffset>(durationMillis = TAB_DURATION_MILLIS)

    val offset: (Int) -> Int = { size ->
        if (forward) size / TAB_SLIDE_FRACTION else -size / TAB_SLIDE_FRACTION
    }

    val slide = if (sideRail) {
        slideInVertically(animationSpec = spec, initialOffsetY = offset)
    } else {
        slideInHorizontally(animationSpec = spec, initialOffsetX = offset)
    }

    return slide + fadeIn(animationSpec = tween(TAB_DURATION_MILLIS))
}

/** The tab leaving, the same movement on the same axis, in the opposite direction. */
private fun slideOutOfTab(forward: Boolean, sideRail: Boolean): ExitTransition {
    val spec = tween<IntOffset>(durationMillis = TAB_DURATION_MILLIS)

    val offset: (Int) -> Int = { size ->
        if (forward) -size / TAB_SLIDE_FRACTION else size / TAB_SLIDE_FRACTION
    }

    val slide = if (sideRail) {
        slideOutVertically(animationSpec = spec, targetOffsetY = offset)
    } else {
        slideOutHorizontally(animationSpec = spec, targetOffsetX = offset)
    }

    return slide + fadeOut(animationSpec = tween(TAB_DURATION_MILLIS))
}
