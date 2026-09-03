#!/usr/bin/env python3
"""
r13 — the shadow-fade fallback, OLED in the settings manager, and the header higher again.

  1. **A fade whatever happens.** `ProgressiveEdgeBlur`'s first parameter is renamed `enabled` →
     `blur`, because that is now all it decides. The edges are treated either way: blurred where
     the device and the switch allow it, a plain shadow fade otherwise — the author's *"when
     progressive ui blur is off / old android devices which doesnt support it, use shadow fade
     instead of blur"*. That also makes this build say why he has never seen a blur: a fade and no
     blur means the switch is off; still nothing means the component is not drawing at all.

  2. **No switch on a device that cannot blur** — *"in that case dont give the option in settings
     also"*. The row and its divider are gated on `supportsProgressiveBlur()`, which removes the
     only use of the `ui_fade` string and of `android.os.Build` in that file.

  3. **OLED reaches the settings manager.** `asOledBackground` deliberately left the containers
     alone so a dialog would still separate from the page; the author asked for the opposite in
     r10 (*"blackouts UI BG also for settings manager"*, and *"Everywhere"* when asked the scope)
     and reported it again now. `GetoTheme` publishes whether the mode is actually in force, and
     `DialogContainer` takes its card to true black when it is.

  4. **The collapsed header 8 dp higher again** — 40 → 32 dp with 4 dp under the title.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

STRINGS = ROOT / "feature/settings/src/main/res/values/strings.xml"

APPS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt"

FAVS = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

HOME = ROOT / "feature/home/src/main/kotlin/com/android/geto/feature/home/HomeScreen.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


# ------------------------------------------------------------ 0. the rewrite landed

blur = BLUR.read_text(encoding="utf-8")

check("fun supportsProgressiveBlur()" in blur, "ProgressiveBlur.kt has no support test")

check("    blur: Boolean,\n" in blur, "ProgressiveEdgeBlur still takes `enabled`")

check("private fun strengthAt(" in blur, "the quadratic ramp is missing")

# ------------------------------------------------------------ 1. the three call sites

for path, label in ((APPS, "AppsScreen"), (FAVS, "FavouriteAppsScreen")):
    text = path.read_text(encoding="utf-8")

    text = swap(
        text,
        "            enabled = ",
        "            blur = ",
        f"{label}: blur argument",
    )

    check(
        "progressiveBlur," in text,
        f"{label}: the progressiveBlur argument went missing",
    )

    pending.append((path, text))

settings = SETTINGS.read_text(encoding="utf-8")

settings = swap(
    settings,
    "        enabled = userData.progressiveBlur,\n",
    "        blur = userData.progressiveBlur,\n",
    "SettingsScreen: blur argument",
)

# ------------------------------------------------------------ 2. the settings row

OLD_ROW = """            SettingsRowDivider()

            // ⚠ **The title changes below Android 12, and nothing else does.** There is no blur
            // before API 31, so the band there is the gradient alone; the switch still turns it
            // on and off. Calling it "Progressive UI blur" on a phone that cannot blur would be
            // the lie, which is the author's own reasoning for the second name.
            SwitchSetting(
                title = stringResource(
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                        R.string.progressive_ui_blur
                    } else {
                        R.string.ui_fade
                    },
                ),
                subtitle = stringResource(R.string.progressive_ui_blur_summary),
                checked = userData.progressiveBlur,
                onCheckedChange = onUpdateProgressiveBlur,
            )
"""

NEW_ROW = """            // ⚠ **Not drawn at all on a device that cannot blur — r13.** Below API 31 there is
            // no `RenderEffect.createBlurEffect`, so those devices get the shadow fade whatever
            // this switch says, and a switch that changes nothing is worse than no switch: the
            // author's *"in that case dont give the option in settings also"*. It replaces r10's
            // answer, which was to rename the row "UI fade" there and leave it working; the fade
            // is not optional any more, so there is nothing left for it to turn off.
            //
            // The divider goes inside the test with it, or the section shows two rules with
            // nothing between them.
            if (supportsProgressiveBlur()) {
                SettingsRowDivider()

                SwitchSetting(
                    title = stringResource(R.string.progressive_ui_blur),
                    subtitle = stringResource(R.string.progressive_ui_blur_summary),
                    checked = userData.progressiveBlur,
                    onCheckedChange = onUpdateProgressiveBlur,
                )
            }
"""

settings = swap(settings, OLD_ROW, NEW_ROW, "SettingsScreen: progressive blur row")

settings = swap(
    settings,
    "import com.android.geto.designsystem.component.ProgressiveEdgeBlur\n",
    "import com.android.geto.designsystem.component.ProgressiveEdgeBlur\n"
    "import com.android.geto.designsystem.component.supportsProgressiveBlur\n",
    "SettingsScreen: supportsProgressiveBlur import",
)

# That was the file's only use of Build, and an unused import is a warning on every build.
settings = swap(settings, "import android.os.Build\n", "", "SettingsScreen: Build import")

check(
    "Build.VERSION" not in settings,
    "SettingsScreen still reads Build.VERSION after losing its import",
)

pending.append((SETTINGS, settings))

# The string had exactly one use, which has just gone. English only — it was never translated.
strings = STRINGS.read_text(encoding="utf-8")

strings = swap(
    strings,
    '    <string name="ui_fade">UI fade</string>\n',
    "",
    "strings: ui_fade",
)

pending.append((STRINGS, strings))

# ------------------------------------------------------------ 3. OLED in the manager

theme = THEME.read_text(encoding="utf-8")

theme = swap(
    theme,
    "import androidx.compose.runtime.CompositionLocalProvider\n",
    "import androidx.compose.runtime.CompositionLocalProvider\n"
    "import androidx.compose.runtime.staticCompositionLocalOf\n",
    "theme: staticCompositionLocalOf import",
)

OLD_PROVIDER = """    CompositionLocalProvider {
        MaterialTheme(
            colorScheme = colorScheme,
            content = content,
        )
    }
}
"""

NEW_PROVIDER = """    // ⚠ **Identity, not the flag.** [asOledBackground] hands a light scheme straight back, so
    // the two are the same object exactly when the mode asked for nothing — which is the honest
    // reading of "is OLED in force here", and it cannot drift from what the scheme actually says.
    CompositionLocalProvider(LocalOledBackground provides (colorScheme !== chosen)) {
        MaterialTheme(
            colorScheme = colorScheme,
            content = content,
        )
    }
}

/**
 * Whether the OLED background mode is actually in force under this theme.
 *
 * ⚠ **For the few places a colour token cannot answer, and there is one so far.** The mode takes
 * the *page* to true black and deliberately leaves the containers alone, so that a card, a dialog
 * or the settings manager still separates from what it is drawn on — see [asOledBackground]. The
 * author asked for the opposite for the manager, twice: *"blackouts UI BG also for settings
 * manager"* in r10, *"Everywhere"* when asked the scope, and again in r13 when he found it still
 * grey. A dialog cannot work that out from `surface` alone, because its own colour is a container
 * and containers did not move. So the theme says it outright.
 *
 * False everywhere else, including in a preview or a test harness that never built a [GetoTheme].
 */
val LocalOledBackground = staticCompositionLocalOf { false }
"""

theme = swap(theme, OLD_PROVIDER, NEW_PROVIDER, "theme: composition local")

pending.append((THEME, theme))

dialog = DIALOG.read_text(encoding="utf-8")

dialog = swap(
    dialog,
    "import androidx.compose.ui.window.Dialog\n",
    "import androidx.compose.ui.window.Dialog\n"
    "import com.android.geto.designsystem.theme.LocalOledBackground\n",
    "dialog: LocalOledBackground import",
)

dialog = swap(
    dialog,
    "    containerColor: Color = AlertDialogDefaults.containerColor,\n",
    """    /**
     * The card itself.
     *
     * ⚠ **True black under OLED background mode — r13.** Material's default is
     * `surfaceContainerHigh`, which the mode leaves alone on purpose so that a card still
     * separates from the page; the author wants the separation to come from the scrim and the
     * shadow instead, so that a dialog over a black page is black. Read from the theme rather
     * than passed in by each dialog, because he asked for it *"Everywhere"*.
     */
    containerColor: Color = if (LocalOledBackground.current) {
        Color.Black
    } else {
        AlertDialogDefaults.containerColor
    },
""",
    "dialog: container colour",
)

pending.append((DIALOG, dialog))

# ------------------------------------------------------------ 4. the header, higher again

home = HOME.read_text(encoding="utf-8")

home = swap(
    home,
    "private val COLLAPSED_TITLE_HEIGHT: Dp = 40.dp\n",
    "private val COLLAPSED_TITLE_HEIGHT: Dp = 32.dp\n",
    "home: collapsed title height",
)

home = swap(
    home,
    "private val TITLE_BOTTOM_PADDING: Dp = 8.dp\n",
    "private val TITLE_BOTTOM_PADDING: Dp = 4.dp\n",
    "home: title bottom padding",
)

home = swap(
    home,
    " * ⚠ **40 dp rather than Material's 64 — the author's r12b *\"i need header and searchbar to be\n"
    " * more up after scrolling down\"*.**",
    " * ⚠ **32 dp rather than Material's 64 — the author's r12b *\"i need header and searchbar to be\n"
    " * more up after scrolling down\"*, and his r13 *\"move tab header, search bar a bit more up\"*.**",
    "home: collapsed height note",
)

pending.append((HOME, home))

# ------------------------------------------------------------ commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
