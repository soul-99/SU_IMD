#!/usr/bin/env python3
"""
v3-r2h — the watermarks come back out, and a pending revert turns the unhide button red.

Two instructions, one visual idea between them.

### 1. Icons where they were

The watermark went in one build and comes out the next, at the author's word: both buttons go
back to a leading 18dp glyph beside the label, which is what `Revert to default` had before
r2g. Nothing else about the pair changes — still equal width, still side by side, still not
dismissing the dialog.

### 2. Red means there is something to undo

`#B71C1C` with white content — **the Support button's red**, at the author's instruction, so
the app has one "this matters" colour rather than two that nearly match.

⚠ **Lifted into `design-system` rather than copied.** It was a `private val` in
`SettingsScreen.kt`; three screens need it now, and three literals of the same hex is how two of
them end up different. `SettingsScreen` reads the shared one, so the Support button and these
two cannot drift.

The unhide button has **two** states and no third: red when something is outstanding, greyed
when nothing is. There is no neutral middle, because the button has no neutral meaning — it
either has work to do or it does not. `Revert to default` keeps its tonal green throughout,
because it always has work to do.

⚠ **Greyed still takes the press**, unchanged from r2g: `unhidePending` is the single thing
that decides whether there was anything to do, and it answers with the toast. The flag only
picks the colour.

The Favourites FAB gets the same pair, greyed included — the author's call, made after seeing
both drawn.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps"

DIALOG = f"{APPS}/dialog/AndroidSettingsManagerDialog.kt"

FAV_SCREEN = f"{APPS}/FavouriteAppsScreen.kt"

FAV_VIEW_MODEL = f"{APPS}/FavouriteAppsViewModel.kt"

SETTINGS_SCREEN = (
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
)

ACCENTS = (
    "design-system/src/main/kotlin/com/android/geto/designsystem/theme/AccentColours.kt"
)

ACCENTS_BODY = '''/*
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
package com.android.geto.designsystem.theme

import androidx.compose.ui.graphics.Color

/**
 * The one red in the app, and the reason it lives here rather than beside any of its uses.
 *
 * The author chose it for the Support button, where it was a `private val` in
 * `SettingsScreen.kt`. It now also marks a revert that is still owed — on the settings
 * manager's unhide button and on the Favourites tab's button — and three copies of a hex
 * literal is how two of them come to differ by a shade nobody meant.
 *
 * **Fixed rather than themed, in both light and dark.** It is not a role in the colour scheme;
 * it is a flag, and a flag that changes shade with the theme stops reading as one. White
 * content clears AA contrast on it either way, which is why every use pairs it with white
 * rather than with `onError` or a scheme colour.
 */
val GetoRed = Color(0xFFB71C1C)
'''

DIALOG_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.designsystem.icon.GetoIcons
""",
        """import com.android.geto.designsystem.icon.GetoIcons
import com.android.geto.designsystem.theme.GetoRed
""",
    ),
    (
        """import androidx.compose.ui.draw.clip
""",
        """import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
""",
    ),
    # The unhide button gains the red half of the pair.
    (
        """                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_hide_glyph,
                    label = stringResource(R.string.unhide_settings),
                    dimmed = !anythingHidden,
                    onClick = onUnhideSettings,
                )
""",
        """                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_hide_glyph,
                    label = stringResource(R.string.unhide_settings),
                    pending = anythingHidden,
                    dimmed = !anythingHidden,
                    onClick = onUnhideSettings,
                )
""",
    ),
    # The button itself: watermark out, leading glyph back, three colour pairs.
    (
        """/**
 * One of the dialog's two filled actions, with its own glyph drawn large behind the label.
 *
 * **The watermark is the icon, not a decoration.** A leading glyph beside the text costs the
 * label horizontal room in a button that is already sharing the row, and pushes it off centre;
 * drawn behind at [WATERMARK_SIZE] and [WATERMARK_ALPHA] it says the same thing, is readable at
 * a glance, and leaves the label centred in its own button.
 *
 * ⚠ **[dimmed] does not disable anything.** The author asked for `Unhide settings` to be greyed
 * out with nothing outstanding *and* to answer with a toast when pressed, which a disabled
 * control cannot do — it swallows the press in silence, which is this screen's least legible
 * failure and the reason the unusable switches above are wrapped rather than disabled. So this
 * takes the press whatever it looks like, and the call underneath — `unhidePending` — is the
 * single thing that decides whether there was anything to do. Two tests that could disagree
 * would be one too many.
 *
 * A Surface rather than a Button, because Button has no long press and Revert to default needs
 * one: holding it opens the configuration that decides what the short press will do.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ActionButton(
    modifier: Modifier = Modifier,
    @DrawableRes glyph: Int,
    label: String,
    dimmed: Boolean = false,
    onClick: () -> Unit,
    onLongClick: (() -> Unit)? = null,
    onLongClickLabel: String? = null,
) {
    // Material's own disabled pair, restated rather than borrowed from ButtonDefaults: these
    // are the colours a genuinely disabled button would take, and the point of this control is
    // that it looks disabled without being it.
    val container = if (dimmed) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    } else {
        MaterialTheme.colorScheme.secondaryContainer
    }

    val content = if (dimmed) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    } else {
        MaterialTheme.colorScheme.onSecondaryContainer
    }

    Surface(
        modifier = modifier
            .height(ACTION_BUTTON_HEIGHT)
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
        Box(contentAlignment = Alignment.Center) {
            Icon(
                modifier = Modifier.size(WATERMARK_SIZE),
                painter = painterResource(glyph),
                // Null, and deliberately: the label beside it already says what this button
                // is, and a screen reader announcing the glyph as well would say it twice.
                contentDescription = null,
                tint = content.copy(alpha = WATERMARK_ALPHA),
            )

            Text(
                modifier = Modifier.padding(horizontal = 8.dp),
                text = label,
                style = MaterialTheme.typography.labelLarge,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/** Tall enough to hold a two-line label and a watermark without either crowding the other. */
private val ACTION_BUTTON_HEIGHT = 52.dp

private val WATERMARK_SIZE = 44.dp

/** Visible as a shape, never as competition for the label sitting on top of it. */
private const val WATERMARK_ALPHA = 0.16f

private const val DIMMED_CONTAINER_ALPHA = 0.12f

private const val DIMMED_CONTENT_ALPHA = 0.38f
""",
        """/**
 * One of the dialog's two filled actions: a leading glyph, then the label.
 *
 * ⚠ **The glyph is beside the label, not behind it.** r2g drew it enlarged as a watermark and
 * the author took it back out the following build; this is the arrangement `Revert to default`
 * has always had, and the one the rows above it use.
 *
 * ### The three colour pairs
 *
 * [pending] and [dimmed] are complements on the one button that uses them — `Unhide settings`
 * is red when something is outstanding and greyed when nothing is, with no neutral state in
 * between, because the button has no neutral meaning. `Revert to default` passes neither and
 * stays tonal, because it always has something to do.
 *
 * ⚠ **[dimmed] does not disable anything.** The author asked for the unhide button to be greyed
 * out with nothing outstanding *and* to answer with a toast when pressed, which a disabled
 * control cannot do — it swallows the press in silence, which is this screen's least legible
 * failure and the reason the unusable switches above are wrapped rather than disabled. So this
 * takes the press whatever colour it is wearing, and the call underneath — `unhidePending` — is
 * the single thing that decides whether there was anything to do. Two tests that could disagree
 * would be one too many.
 *
 * A Surface rather than a Button, because Button has no long press and Revert to default needs
 * one: holding it opens the configuration that decides what the short press will do.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ActionButton(
    modifier: Modifier = Modifier,
    @DrawableRes glyph: Int,
    label: String,
    pending: Boolean = false,
    dimmed: Boolean = false,
    onClick: () -> Unit,
    onLongClick: (() -> Unit)? = null,
    onLongClickLabel: String? = null,
) {
    // Subjectless `when`, deliberately: `check16_when` reads `when (x)` against an enum's
    // labels, and these are two independent booleans rather than one state with three names.
    //
    // The dimmed pair is Material's own disabled palette, restated rather than borrowed from
    // ButtonDefaults — they are the colours a genuinely disabled button would take, and the
    // whole point of this control is that it looks disabled without being it.
    val container = when {
        pending -> GetoRed
        dimmed -> MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
        else -> MaterialTheme.colorScheme.secondaryContainer
    }

    val content = when {
        pending -> Color.White
        dimmed -> MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
        else -> MaterialTheme.colorScheme.onSecondaryContainer
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
            modifier = Modifier.padding(ButtonDefaults.ContentPadding),
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
                style = MaterialTheme.typography.labelLarge,
                textAlign = TextAlign.Center,
            )
        }
    }
}

private const val DIMMED_CONTAINER_ALPHA = 0.12f

private const val DIMMED_CONTENT_ALPHA = 0.38f
""",
    ),
]

SETTINGS_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.designsystem.theme.supportsDynamicTheming
""",
        """import com.android.geto.designsystem.theme.GetoRed
import com.android.geto.designsystem.theme.supportsDynamicTheming
""",
    ),
    (
        """/** The dark red the author asked for on the Support button; white text keeps AA contrast on it. */
private val SUPPORT_BUTTON_COLOUR = Color(0xFFB71C1C)

""",
        """""",
    ),
    (
        """                containerColor = SUPPORT_BUTTON_COLOUR,
""",
        """                containerColor = GetoRed,
""",
    ),
]

FAV_VIEW_MODEL_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.domain.model.leftSettingsHidden
""",
        """import com.android.geto.domain.model.leftSettingsHidden
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (
        """    /** Cleared once handled, so tapping the same app twice emits twice. */
""",
        """    /**
     * Whether anything IMD did is still outstanding, by any of the three routes it can owe on.
     *
     * ⚠ **The same three questions [unhideSettings] will ask**, derived from the same stored
     * values rather than from a flag of its own — a separate test here could disagree with the
     * one doing the work, and the way it would show is a red button that then says there is
     * nothing to restore.
     */
    val anythingHidden = userDataRepository.userData
        .map { it.autoHideRunning || it.settingsHidden }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5000),
            initialValue = false,
        )

    /** Cleared once handled, so tapping the same app twice emits twice. */
""",
    ),
]

FAV_SCREEN_EDITS: list[tuple[str, str]] = [
    (
        """import androidx.lifecycle.compose.collectAsStateWithLifecycle
""",
        """import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.android.geto.designsystem.theme.GetoRed
""",
    ),
    # ⚠ `Color.White` needs this and the file did not have it. Nothing in the sandbox can see a
    # *missing* import - check12 finds unused ones, check18 finds internal top-level functions,
    # and neither reads a type reference - so this one was caught by reading the file's import
    # block against what the edit adds. Worth doing for every new type name a round introduces.
    (
        """import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
""",
        """import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
""",
    ),
    (
        """    val appLaunch by viewModel.appLaunch.collectAsStateWithLifecycle()
""",
        """    val appLaunch by viewModel.appLaunch.collectAsStateWithLifecycle()

    val anythingHidden by viewModel.anythingHidden.collectAsStateWithLifecycle()
""",
    ),
    (
        """        onUnhideSettings = viewModel::unhideSettings,
    )
}
""",
        """        onUnhideSettings = viewModel::unhideSettings,
        anythingHidden = anythingHidden,
    )
}
""",
    ),
    (
        """    onUnhideSettings: () -> Unit,
) {
    var showManagerDialog by rememberSaveable { mutableStateOf(false) }
""",
        """    onUnhideSettings: () -> Unit,
    /**
     * Whether anything IMD did is still outstanding. Decides only the button's colour; the
     * press runs the same call either way and answers for itself.
     */
    anythingHidden: Boolean = false,
) {
    var showManagerDialog by rememberSaveable { mutableStateOf(false) }
""",
    ),
    (
        """                FloatingActionButton(onClick = onUnhideSettings) {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_hide_glyph),
                        contentDescription = stringResource(R.string.unhide_settings),
                    )
                }
""",
                """                // Red when something is owed, greyed when nothing is — the same pair the
                // settings manager's unhide button wears, and the author's decision after
                // seeing a green idle state drawn beside a greyed one. Greyed reads as "this
                // has nothing to do" where green reads as "press me", and on a tab that
                // exists for a device needing to be put back, the second is a lie most of
                // the time.
                //
                // ⚠ Still pressable while greyed, exactly as in the dialog: the call
                // underneath answers with a toast, and a FAB that swallowed the press would
                // leave the user with no idea whether anything had happened.
                FloatingActionButton(
                    onClick = onUnhideSettings,
                    containerColor = if (anythingHidden) {
                        GetoRed
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f)
                    },
                    contentColor = if (anythingHidden) {
                        Color.White
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
                    },
                ) {
                    Icon(
                        modifier = Modifier.size(24.dp),
                        painter = painterResource(designR.drawable.ic_hide_glyph),
                        contentDescription = stringResource(R.string.unhide_settings),
                    )
                }
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {ROOT / ACCENTS: ACCENTS_BODY}

    everything = {
        DIALOG: DIALOG_EDITS,
        SETTINGS_SCREEN: SETTINGS_EDITS,
        FAV_VIEW_MODEL: FAV_VIEW_MODEL_EDITS,
        FAV_SCREEN: FAV_SCREEN_EDITS,
    }

    for name, edits in everything.items():
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        # ⚠ Only lines this edit adds — handover_3 §4.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    # Nothing may name the watermark or the old private colour any more, anywhere.
    for gone in ("WATERMARK_SIZE", "WATERMARK_ALPHA", "ACTION_BUTTON_HEIGHT",
                 "SUPPORT_BUTTON_COLOUR"):
        for kotlin in sorted(ROOT.rglob("*.kt")):
            if "build" in kotlin.relative_to(ROOT).parts:
                continue

            body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

            if gone in body:
                problems.append(f"{kotlin.relative_to(ROOT)}: still names {gone}")

    # The red is defined once and used in exactly three places.
    uses = 0

    # ⚠ The staged keys as well as what is on disk. AccentColours.kt does not exist yet, so a
    # plain rglob would miss the declaration and undercount by exactly one — which is how the
    # first run of this script refused itself.
    for kotlin in sorted(set(ROOT.rglob("*.kt")) | set(staged)):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        uses += body.count("GetoRed")

    # One declaration, three imports, three uses.
    if uses != 7:
        problems.append(f"GetoRed named {uses} times, expected 7 (1 decl + 3 imports + 3 uses)")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print("ok — glyphs back beside the labels, one shared red, both unhide buttons paired")

    return 0


if __name__ == "__main__":
    sys.exit(main())
