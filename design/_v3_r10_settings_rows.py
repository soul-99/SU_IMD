#!/usr/bin/env python3
"""
v3-r10 — the two new User interface switches, and the blurred band over the settings tab.

The author's order, in his words: *"add new setting toggle in user interface section between theme
and progressive named 'OLED background mode'"*, with *"'Progressive UI blur' ... below theme
setting"*. So Theme, then OLED background mode, then Progressive UI blur, then the rows that were
already there.

Both titles and both subtitles are his, verbatim:

    'OLED background mode'   / 'pure black UI background'
    'Progressive UI blur'    / 'applies a blur to the bottom section of app'
    'UI fade'                — the blur row's title on a device that cannot blur

⚠ **The OLED row is not drawn while the app is light**, which is the author's own pick from the
r10 questions rather than a default. The mode changes nothing in a light scheme, and a switch that
visibly does nothing is worse than a switch that is not there.

⚠ **Which "light" is asked by luminance, not `isSystemInDarkTheme()`.** The comment above
[SHELL_PROMPT_LIGHT] in this file already spells out why: the app has its own
light/dark/follow-system setting, so asking the *system* gives a light-themed app on a dark-themed
phone the wrong answer. The shell panel a thousand lines below already tests
`colorScheme.surface.luminance() < 0.5f`; this is the same test on the same value, and it keeps
working under dynamic colour where there is no scheme of ours to consult. It also stays correct
once OLED mode is on, since black is darker still.

⚠ **The blur row's *title* changes below Android 12, and only its title.** There is no blur to be
had before API 31 - `RenderEffect.createBlurEffect` does not exist - so the band is the fade alone
there. The switch still works and still turns the band on and off; calling it "Progressive UI blur"
on a device that cannot blur would be the lie. The author's instruction: *"(a) fade there, blur
12+ but rename setting to 'UI fade' on those devices"*.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

VIEWMODEL = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

STRINGS = "feature/settings/src/main/res/values/strings.xml"

# --- strings ------------------------------------------------------------------------------

STRINGS_OLD = '''    <string name="manager_rows_entry">Settings manager options</string>
'''

STRINGS_NEW = '''    <string name="manager_rows_entry">Settings manager options</string>
    <string name="oled_background_mode">OLED background mode</string>
    <string name="oled_background_mode_summary">pure black UI background</string>
    <string name="progressive_ui_blur">Progressive UI blur</string>
    <!-- The same switch on a device with no blur available. See ProgressiveBottomBlur. -->
    <string name="ui_fade">UI fade</string>
    <string name="progressive_ui_blur_summary">applies a blur to the bottom section of app</string>
'''

# --- the view model -------------------------------------------------------------------------

VM_OLD = '''    fun updateDynamicTheme(dynamicTheme: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateDynamicTheme(dynamicTheme = dynamicTheme)
        }
    }
'''

VM_NEW = '''    fun updateDynamicTheme(dynamicTheme: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateDynamicTheme(dynamicTheme = dynamicTheme)
        }
    }

    /** The bottom-edge band, on or off. Stored as its negation - see the proto comment on 75. */
    fun updateProgressiveBlur(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateProgressiveBlur(enabled = enabled)
        }
    }

    /** Pure black backgrounds in a dark scheme. */
    fun updateOledBackground(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateOledBackground(enabled = enabled)
        }
    }
'''

# --- plumbing: route -> screen -> success ---------------------------------------------------

ROUTE_OLD = '''        onUpdateDynamicTheme = viewModel::updateDynamicTheme,
'''

ROUTE_NEW = '''        onUpdateDynamicTheme = viewModel::updateDynamicTheme,
        onUpdateProgressiveBlur = viewModel::updateProgressiveBlur,
        onUpdateOledBackground = viewModel::updateOledBackground,
'''

SCREEN_PARAM_OLD = '''    onUpdateTheme: (Theme) -> Unit,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
'''

SCREEN_PARAM_NEW = '''    onUpdateTheme: (Theme) -> Unit,
    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateManageShizuku: (Boolean) -> Unit,
'''

SUCCESS_CALL_OLD = '''                    onUpdateDynamicTheme = onUpdateDynamicTheme,
                    onUpdateIconStyle = onUpdateIconStyle,
'''

SUCCESS_CALL_NEW = '''                    onUpdateDynamicTheme = onUpdateDynamicTheme,
                    onUpdateProgressiveBlur = onUpdateProgressiveBlur,
                    onUpdateOledBackground = onUpdateOledBackground,
                    onUpdateIconStyle = onUpdateIconStyle,
'''

SUCCESS_PARAM_OLD = '''    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateIconStyle: (IconStyle) -> Unit,
'''

SUCCESS_PARAM_NEW = '''    onUpdateDynamicTheme: (Boolean) -> Unit,
    onUpdateProgressiveBlur: (Boolean) -> Unit,
    onUpdateOledBackground: (Boolean) -> Unit,
    onUpdateIconStyle: (IconStyle) -> Unit,
'''

# --- the rows themselves --------------------------------------------------------------------

ROWS_OLD = '''            SettingsColumn(
                title = stringResource(R.string.theme),
                subtitle = userData.theme.getTitle(),
                onClick = { showThemeDialog = true },
            )

            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.language),
'''

ROWS_NEW = '''            SettingsColumn(
                title = stringResource(R.string.theme),
                subtitle = userData.theme.getTitle(),
                onClick = { showThemeDialog = true },
            )

            // ⚠ **Not drawn at all while the app is light**, at the author's instruction. The
            // mode blacks out a dark scheme's page and returns a light one untouched, so the row
            // would be a switch that visibly does nothing - worse than an absent one.
            //
            // Asked by luminance rather than isSystemInDarkTheme(), for the reason the comment
            // above SHELL_PROMPT_LIGHT gives: the app has its own light/dark/follow-system
            // setting, and the system's answer is the wrong one for a light-themed app on a
            // dark-themed phone. It also survives dynamic colour, where there is no scheme of
            // ours to consult, and it stays true once the mode is on - black is darker still.
            if (MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE) {
                SettingsRowDivider()

                SwitchSetting(
                    title = stringResource(R.string.oled_background_mode),
                    subtitle = stringResource(R.string.oled_background_mode_summary),
                    checked = userData.oledBackground,
                    onCheckedChange = onUpdateOledBackground,
                )
            }

            SettingsRowDivider()

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

            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.language),
'''

# --- the band over the settings tab ---------------------------------------------------------

BAND_OLD = '''    Column(
        modifier = modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState()),
    ) {
        CollapsibleSection(
            title = stringResource(R.string.section_ui),
'''

BAND_NEW = '''    Column(
        modifier = modifier
            .fillMaxSize()
            // ⚠ **A shorter band than the two app tabs get** — the author's "also apply blur to
            // settings but keep it lowered on height". This tab is a column of rows rather than a
            // scrolling wall of artwork, and the full 150 dp swallows most of the last row
            // instead of fading it.
            .progressiveBottomBlur(
                enabled = userData.progressiveBlur,
                height = ProgressiveBlurDefaults.SettingsHeight,
            )
            .verticalScroll(rememberScrollState())
            // Room at the end for the floating bar to rest over nothing. The bar is drawn over
            // this page rather than beside it, which is what gives the band something to blur.
            .padding(bottom = GetoNavBarReservedHeight),
    ) {
        CollapsibleSection(
            title = stringResource(R.string.section_ui),
'''

# ⚠ **No closing edit, and that is the point of the band being a modifier.** An earlier draft
# wrapped the Column in a composable and had to find where it ended - which it got wrong, closing
# after two dialog blocks that are siblings of the whole page. A modifier goes in the chain the
# Column already has and closes nothing.

# --- imports ---------------------------------------------------------------------------------

IMPORT_OLD = '''import androidx.compose.foundation.verticalScroll
'''

IMPORT_NEW = '''import androidx.compose.foundation.verticalScroll
import com.android.geto.designsystem.component.GetoNavBarReservedHeight
import com.android.geto.designsystem.component.ProgressiveBlurDefaults
import com.android.geto.designsystem.component.progressiveBottomBlur
'''

BUILD_IMPORT_OLD = '''import androidx.compose.foundation.verticalScroll
'''

DARK_CONST_OLD = '''private val SHELL_PROMPT_LIGHT = Color(0xFF4C662B)
'''

DARK_CONST_NEW = '''/**
 * Where a surface stops being light and starts being dark.
 *
 * Halfway, which is what the shell panel below has always used. It is written down here because
 * two unrelated things now ask the question - which prompt colour the terminal block wears, and
 * whether the OLED row is drawn at all - and a second literal 0.5 would be a second definition.
 */
private const val DARK_SURFACE_LUMINANCE = 0.5f

private val SHELL_PROMPT_LIGHT = Color(0xFF4C662B)
'''

EDITS = [
    (STRINGS, STRINGS_OLD, STRINGS_NEW),
    (VIEWMODEL, VM_OLD, VM_NEW),
    (SCREEN, IMPORT_OLD, IMPORT_NEW),
    (SCREEN, ROUTE_OLD, ROUTE_NEW),
    (SCREEN, SCREEN_PARAM_OLD, SCREEN_PARAM_NEW),
    (SCREEN, SUCCESS_CALL_OLD, SUCCESS_CALL_NEW),
    (SCREEN, SUCCESS_PARAM_OLD, SUCCESS_PARAM_NEW),
    (SCREEN, DARK_CONST_OLD, DARK_CONST_NEW),
    (SCREEN, ROWS_OLD, ROWS_NEW),
    (SCREEN, BAND_OLD, BAND_NEW),
]

CHECKS = [
    (STRINGS, '<string name="oled_background_mode">OLED background mode</string>', 1,
     "the OLED title is the author's, verbatim"),
    (STRINGS, '<string name="oled_background_mode_summary">pure black UI background</string>', 1,
     "and its subtitle"),
    (STRINGS, '<string name="progressive_ui_blur">Progressive UI blur</string>', 1,
     "the blur title"),
    (STRINGS, '<string name="ui_fade">UI fade</string>', 1, "its name on a device with no blur"),
    (STRINGS,
     '<string name="progressive_ui_blur_summary">applies a blur to the bottom section of app'
     '</string>', 1, "and its subtitle"),
    (SCREEN, "R.string.oled_background_mode)", 1, "the OLED row is drawn once"),
    (SCREEN, "R.string.progressive_ui_blur\n", 1, "and the blur row once"),
    (SCREEN, "R.string.ui_fade", 1, "with one fallback name"),
    (SCREEN, "onUpdateProgressiveBlur", 6, "two declarations, two hand-offs (named twice each), one use"),
    (SCREEN, "onUpdateOledBackground", 6, "the same for OLED"),
    (SCREEN, ".progressiveBottomBlur(", 1, "one band on this tab"),
    (SCREEN, "DARK_SURFACE_LUMINANCE", 2, "one threshold, declared and used"),
    (VIEWMODEL, "fun updateProgressiveBlur", 1, "the view model writes it"),
    (VIEWMODEL, "fun updateOledBackground", 1, "and the other"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip().splitlines()[0][:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already carries the replacement")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:24s} {old.strip().splitlines()[0][:48]}")

    # `Build` may or may not already be imported in the screen; add it only if it is not.
    screen = ROOT / SCREEN

    if "\nimport android.os.Build\n" not in planned[screen]:
        anchor = "import androidx.compose.foundation.verticalScroll\n"

        planned[screen] = planned[screen].replace(
            anchor, "import android.os.Build\n" + anchor, 1,
        )

        print("  ok        SettingsScreen.kt         + import android.os.Build")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token[:48]!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:24s} x{got}  {token[:44]!r}")

    # ⚠ **Braces balance.** The band wraps a Column that was already there, so one brace was
    # opened in one edit and closed in another; a mismatch here is a file that will not parse
    # and a very long hunt for why.
    text = planned[screen]

    if text.count("{") != text.count("}"):
        print(
            f"REFUSED: SettingsScreen.kt braces do not balance — "
            f"{text.count('{')} open, {text.count('}')} close",
        )
        return 1

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, content in planned.items():
        if over(content) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, content in planned.items():
        path.write_text(content, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s) — two switches, five strings, one band")

    return 0


if __name__ == "__main__":
    sys.exit(main())
