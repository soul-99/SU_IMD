#!/usr/bin/env python3
"""
v3-r10 — the floating tab bar replaces the navigation suite, and a swipe changes tabs on phones.

The author asked for *"a mini tab bar with fluid animations like obtain x"*, for the same bar
*"for tablets"* but *"vertical ... on left side"* with *"labels for all tabs always"*, for Settings
*"disconnect[ed] ... as a pill from tab bar on phones"*, and for swiping between tabs on phones
only - later widened to *"in phones allow swiping to settings forget my old instruction"*, so the
swipe reaches all three rather than the two app tabs.

⚠ **`NavigationSuiteScaffold` goes, and with it the thing that was choosing the layout.** The suite
picked a bottom bar or a side rail by itself and did not report which; this file already computed
[sideRail] separately so the tab *animation* could travel the right way, and that computation is
now the single answer both the bar and the animation read. One fewer thing that can disagree with
itself.

⚠ **The bar floats over the content rather than displacing it, and that is the point.** The blurred
band under it - see `ProgressiveBottomBlur` - has nothing to blur if the list stops above the bar.
The room a list needs at its end is added as *content padding* inside each screen, not as layout
padding here.

⚠ **The swipe is gated on the same [sideRail] value**, so it can never be on while the bar is down
the side. A horizontal drag across a rail is travelling *across* the tabs rather than along them,
which is why the author asked for it on phones only.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOME = "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

# --- imports ------------------------------------------------------------------------------

IMPORT_OLD = '''import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior
import androidx.compose.material3.adaptive.navigationsuite.NavigationSuiteScaffold
import androidx.compose.runtime.Composable
'''

IMPORT_NEW = '''import androidx.compose.foundation.gestures.detectHorizontalDragGestures
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.consumeWindowInsets
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LargeTopAppBar
import androidx.compose.material3.Scaffold
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBarDefaults.exitUntilCollapsedScrollBehavior
import androidx.compose.runtime.Composable
'''

IMPORT2_OLD = '''import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.IntOffset
'''

IMPORT2_NEW = '''import androidx.compose.ui.Alignment
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalConfiguration
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import com.android.geto.designsystem.component.GetoFloatingNavBar
import com.android.geto.designsystem.component.GetoFloatingNavRail
import com.android.geto.designsystem.component.GetoNavItem
import com.android.geto.designsystem.component.GetoNavRailReservedWidth
import kotlin.math.abs
'''

# --- the scaffold -------------------------------------------------------------------------

BODY_OLD = '''    NavigationSuiteScaffold(
        navigationSuiteItems = {
            topLevelDestinations.forEach { destination ->
                item(
                    icon = {
                        Icon(
                            imageVector = destination.icon,
                            contentDescription = stringResource(id = destination.contentDescription),
                        )
                    },
                    label = { Text(stringResource(id = destination.label)) },
                    selected = currentDestination.isTopLevelDestinationInHierarchy(destination.route),
                    onClick = {
                        onClickHomeDestination(navController, destination)
                    },
                )
            }
        },
    ) {
        Scaffold(
            topBar = {
                LargeTopAppBar(
                    title = {
                        Text(
                            text = stringResource(id = topBarTitleStringResource),
                        )
                    },
                    scrollBehavior = topAppBarScrollBehavior,
                )
            },
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
            NavHost(
                modifier = modifier
                    .nestedScroll(topAppBarScrollBehavior.nestedScrollConnection)
                    .padding(paddingValues)
                    .consumeWindowInsets(paddingValues),
                navController = navController,
                startDestination = startDestination,
'''

BODY_NEW = '''    // Which tab is showing, as a position in the bar rather than a route. The swipe needs a
    // number to add one to; nothing else does.
    val selectedIndex = topLevelDestinations.indexOfFirst { destination ->
        currentDestination.isTopLevelDestinationInHierarchy(destination.route)
    }

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

    Box(modifier = Modifier.fillMaxSize()) {
        Scaffold(
            // ⚠ **The rail floats over the window, so the page is indented to make room.**
            // GetoNavRailReservedWidth is the rail's own cap, exported for exactly this: the
            // two numbers have to agree and there is only one of them.
            modifier = if (sideRail) {
                Modifier.padding(start = GetoNavRailReservedWidth)
            } else {
                Modifier
            },
            topBar = {
                LargeTopAppBar(
                    title = {
                        Text(
                            text = stringResource(id = topBarTitleStringResource),
                        )
                    },
                    scrollBehavior = topAppBarScrollBehavior,
                )
            },
            snackbarHost = {
                SnackbarHost(hostState = snackbarHostState)
            },
        ) { paddingValues ->
            NavHost(
                modifier = modifier
                    .nestedScroll(topAppBarScrollBehavior.nestedScrollConnection)
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
'''

TAIL_OLD = '''                builder = builder,
            )
        }
    }
}
'''

TAIL_NEW = '''                builder = builder,
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
'''

CHECKS = [
    ("NavigationSuiteScaffold", 0, "the navigation suite is gone"),
    ("GetoFloatingNavBar(", 1, "the phone bar is drawn once"),
    ("GetoFloatingNavRail(", 1, "and the rail once"),
    ("val sideRail =", 1, "one place decides which"),
    # Spelled with its first argument, because "private fun Modifier.tabSwipe(" below matches
    # the bare call form too - the declaration is not a second attachment.
    (".tabSwipe(enabled = ", 1, "the swipe is attached once"),
    ("private fun Modifier.tabSwipe(", 1, "and declared once"),
    # Three: the import, the comment that explains it, and the one use.
    ("GetoNavRailReservedWidth", 3, "the indent uses the rail's own cap"),
    ("Modifier.padding(start = GetoNavRailReservedWidth)", 1, "and uses it exactly once"),
    ("import androidx.compose.material3.Icon", 0, "the suite's icon import went with it"),
]


def main() -> int:
    path = ROOT / HOME

    if not path.is_file():
        print(f"REFUSED: missing {HOME}")
        return 1

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in (
        (IMPORT_OLD, IMPORT_NEW),
        (IMPORT2_OLD, IMPORT2_NEW),
        (BODY_OLD, BODY_NEW),
        (TAIL_OLD, TAIL_NEW),
    ):
        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: anchor {old.strip().splitlines()[0][:70]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in original:
            print("REFUSED: already applied — has this run before?")
            return 1

        text = text.replace(old, new, 1)

    # ⚠ **Counted on code lines only, and this is the comment trap the handover warns about.**
    # `sideRail` is named in four KDoc paragraphs in this file; a raw count would be asserting
    # how much prose is written about it rather than how many times it is read. What matters is
    # that every use is a *read* of the one computation - the bar/rail choice, the swipe gate,
    # and the two arguments to the slide helpers - and that nothing recomputes it.
    code = "\n".join(
        line
        for line in text.split("\n")
        if not line.lstrip().startswith(("*", "//", "/*"))
    )

    # One declaration; four reads in this screen (the page indent, the swipe gate, the
    # bar/rail choice, and nothing else); four hand-offs to the slide helpers, one per
    # transition; and the two helpers' own parameter and branch, two each.
    reads = code.count("sideRail")

    if reads != 1 + 3 + 4 + 4:
        print(f"REFUSED: sideRail is used {reads} time(s) in code, expected 12")
        return 1

    print(f"  checked  x{reads:<3} 'sideRail' (code lines only)")

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:54]!r}")

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

    print("\n  ok  the navigation suite is replaced, and a phone can swipe between tabs")

    return 0


if __name__ == "__main__":
    sys.exit(main())
