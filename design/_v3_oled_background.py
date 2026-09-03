#!/usr/bin/env python3
"""
v3-r10 — OLED background mode: *"pure black UI background"*, in the author's words.

⚠ **Four tokens, not the whole scheme.** `background`, `surface`, `surfaceDim` and
`surfaceContainerLowest` go to true black; every container above them keeps the green scheme's own
tint. That split is what makes the mode useful rather than merely dark: on an OLED panel a black
pixel is an unlit pixel, so the page behind the content is what there is to gain, and blacking the
cards as well would erase the only thing separating a dialog from the page it sits on. `surfaceLow`
is pulled down with them because it is drawn as page furniture in a few places and a #1A1C16 strip
against #000000 reads as a seam.

⚠ **Dark only, and it does not force dark.** A light scheme is returned untouched, which is why the
row that sets it is not drawn while the app is light - the author's own choice from the r10
questions. Nothing here consults [Theme]; the scheme has already been chosen by the time this runs,
and dynamic-colour schemes get the same treatment as the green one.

⚠ **All five activities, and the settings manager is the reason.** The author asked for this to
apply *"also for settings manager"*, which is `ServicesActivity` - a separate activity with its own
window over whatever app is in front. Every other entry point gets it too, because a black manager
over a near-black hide dialog would be worse than either.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME = "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

ACTIVITIES = [
    "app/src/main/kotlin/com/android/geto/activity/hide/HideActivity.kt",
    "app/src/main/kotlin/com/android/geto/activity/services/ServicesActivity.kt",
    "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt",
    "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt",
]

MAIN = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"

# --- Theme.kt: the signature ---------------------------------------------------------------

SIG_OLD = '''@Composable
fun GetoTheme(
    theme: Theme,
    dynamicTheme: Boolean,
    content: @Composable () -> Unit,
) {
    val colorScheme = if (supportsDynamicTheming() && dynamicTheme) {
        getDynamicColorScheme(
            theme = theme,
        )
    } else {
        getGreenColorScheme(
            theme = theme,
        )
    }
'''

SIG_NEW = '''@Composable
fun GetoTheme(
    theme: Theme,
    dynamicTheme: Boolean,
    /**
     * The author's "OLED background mode" - "pure black UI background".
     *
     * ⚠ **Ignored by a light scheme**, so a caller never has to ask which scheme it is about to
     * get. See [asOledBackground] for which four tokens move and why the containers do not.
     *
     * ⚠ **Defaulted, and only for the callers that genuinely have no user data.** Every activity
     * in this app passes it; the default is here so that a preview or a test harness building a
     * theme out of nothing gets the ordinary scheme rather than a compile error.
     */
    oledBackground: Boolean = false,
    content: @Composable () -> Unit,
) {
    val chosen = if (supportsDynamicTheming() && dynamicTheme) {
        getDynamicColorScheme(
            theme = theme,
        )
    } else {
        getGreenColorScheme(
            theme = theme,
        )
    }

    val colorScheme = if (oledBackground) chosen.asOledBackground() else chosen
'''

# --- Theme.kt: the transform ----------------------------------------------------------------

TRANSFORM_OLD = '''@ChecksSdkIntAtLeast(api = Build.VERSION_CODES.S)
fun supportsDynamicTheming() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
'''

TRANSFORM_NEW = '''@ChecksSdkIntAtLeast(api = Build.VERSION_CODES.S)
fun supportsDynamicTheming() = Build.VERSION.SDK_INT >= Build.VERSION_CODES.S

/** True black, which on an OLED panel is an unlit pixel. That is the whole point of the mode. */
private val Oled = Color(0xFF000000)

/**
 * The page behind everything, taken to true black.
 *
 * ⚠ **A light scheme is returned as it came.** The mode is about unlit pixels, and a light theme
 * has none to give; forcing black there would be a second dark theme wearing the wrong text
 * colours. The switch that sets it is not even drawn while the app is light.
 *
 * ⚠ **Four tokens and one near-miss, deliberately not the containers.** `background`, `surface`
 * and `surfaceDim` are the page; `surfaceContainerLowest` is what sits directly on it and would
 * otherwise draw a #0C0F09 rectangle on #000000. `surfaceContainerLow` follows them down but not
 * all the way, because it is used as page furniture in a few places where a hard edge against
 * black would read as a seam. Everything above it keeps its tint - that is what still separates a
 * card, a dialog or the settings manager from the page it is drawn on.
 */
private fun ColorScheme.asOledBackground(): ColorScheme {
    // Luminance rather than a flag: this is asked of dynamic schemes too, and there is no
    // "isDark" on a ColorScheme. A dark scheme is one whose page is darker than its ink.
    val dark = surface.luminance() < onSurface.luminance()

    if (!dark) return this

    return copy(
        background = Oled,
        surface = Oled,
        surfaceDim = Oled,
        surfaceContainerLowest = Oled,
        surfaceContainerLow = Color(0xFF0A0A0A),
    )
}
'''

IMPORT_OLD = "import androidx.compose.ui.graphics.Color\n"

IMPORT_NEW = (
    "import androidx.compose.ui.graphics.Color\n"
    "import androidx.compose.ui.graphics.luminance\n"
)

# --- the activities ---------------------------------------------------------------------

ACT_OLD = '''                dynamicTheme = userData?.dynamicTheme ?: false,
'''

ACT_NEW = '''                dynamicTheme = userData?.dynamicTheme ?: false,
                oledBackground = userData?.oledBackground ?: false,
'''

MAIN_OLD = '''                            dynamicTheme = uiState.userData.dynamicTheme,
'''

MAIN_NEW = '''                            dynamicTheme = uiState.userData.dynamicTheme,
                            oledBackground = uiState.userData.oledBackground,
'''


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    edits = [
        (THEME, IMPORT_OLD, IMPORT_NEW),
        (THEME, SIG_OLD, SIG_NEW),
        (THEME, TRANSFORM_OLD, TRANSFORM_NEW),
        (MAIN, MAIN_OLD, MAIN_NEW),
    ] + [(rel, ACT_OLD, ACT_NEW) for rel in ACTIVITIES]

    for rel, old, new in edits:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip()[:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already carries the replacement")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:28s} {old.strip().splitlines()[0][:44]}")

    checks = [
        (THEME, "oledBackground: Boolean = false,", 1, "the parameter is declared once"),
        (THEME, "asOledBackground()", 2, "declared and called"),
        (THEME, "private val Oled = Color(0xFF000000)", 1, "one black"),
        (THEME, "if (!dark) return this", 1, "a light scheme is returned untouched"),
        (MAIN, "oledBackground = uiState.userData.oledBackground,", 1, "MainActivity passes it"),
    ] + [
        (rel, "oledBackground = userData?.oledBackground ?: false,", 1, f"{Path(rel).name} passes it")
        for rel in ACTIVITIES
    ]

    for rel, token, want, why in checks:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:28s} x{got}  {token[:40]!r}")

    # ⚠ Every GetoTheme call site must pass it. Five activities build a theme; if one were
    # missed the settings manager or a dialog would stay near-black while the app went black,
    # which is exactly the kind of miss that only shows up on a device.
    call_sites = 0

    for path, text in planned.items():
        call_sites += text.count("oledBackground = ")

    # Exactly five: the four dialog activities and MainActivity. Theme.kt's own mentions are
    # spelled `oledBackground: Boolean` and `if (oledBackground)` and so are not counted here -
    # they have their own assertions above.
    if call_sites != 5:
        print(f"REFUSED: found {call_sites} `oledBackground = ` call sites, expected 5")
        return 1

    theme_reads = planned[ROOT / THEME].count("if (oledBackground)")

    if theme_reads != 1:
        print(f"REFUSED: Theme.kt reads the flag {theme_reads} time(s), expected 1")
        return 1

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, text in planned.items():
        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s) — 5 activities, one scheme transform")

    return 0


if __name__ == "__main__":
    sys.exit(main())
