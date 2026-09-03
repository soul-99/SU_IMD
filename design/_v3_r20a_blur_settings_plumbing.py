#!/usr/bin/env python3
"""
r20a — the blur's numbers become settings, and the theme carries them.

`LocalProgressiveBlur`, added in r19 to tell a dialog whether the switch was on, becomes
`LocalBlurSettings` — the switch *and* the three numbers behind it. Nothing else could have
carried them: the page modifier lives in `:design-system` and must not take a view model, and a
dialog is a window of its own with no route to user data at all.

Also switches the page bands over to reading those numbers instead of the constants they were
tuned against, so one slider moves the pages and the frosted window together.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

SETTINGSKT = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/BlurSettings.kt"

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


check(
    "data class GetoBlurSettings(" in SETTINGSKT.read_text(encoding="utf-8"),
    "BlurSettings.kt is missing",
)

# ------------------------------------------------------------ 1. the theme carries the settings

theme = THEME.read_text(encoding="utf-8")

theme = swap(
    theme,
    """    /**
     * The author's "Progressive UI blur", published rather than used.
     *
     * ⚠ **Nothing in this file reads it.** It is here because a *dialog* needs it — see
     * `LocalProgressiveBlur` — and a dialog has no route to user data of its own. Every activity
     * already hands this theme the user's preferences, so this is the one place that can answer
     * without a second wiring.
     */
    progressiveBlur: Boolean = false,""",
    """    /**
     * The author's "Progressive UI blur", switch and sliders both, published rather than used.
     *
     * ⚠ **Nothing in this file reads it.** It is here because a page modifier and a *dialog* both
     * need it — see [LocalBlurSettings] — and neither can reach user data: one lives in this
     * module and must not take a view model, the other is a window of its own. Every activity
     * already hands this theme the user's preferences, so this is the one place that can answer
     * without a second wiring.
     */
    blurSettings: GetoBlurSettings = GetoBlurSettings.Default,""",
    "theme: parameter",
)

theme = swap(
    theme,
    "        LocalProgressiveBlur provides progressiveBlur,\n",
    "        LocalBlurSettings provides blurSettings,\n",
    "theme: provider",
)

theme = swap(
    theme,
    """/**
 * Whether the author's "Progressive UI blur" is switched on.
 *
 * ⚠ **For windows, not for pages.** A page blurs its own edges with `Modifier.progressiveEdgeBlur`
 * and needs no help; a *dialog* is a separate window whose backdrop only the platform can blur, and
 * it has no view of user data to decide with. This is how the answer reaches it.
 *
 * False everywhere else, including in a preview or a test harness that never built a [GetoTheme].
 */
val LocalProgressiveBlur = staticCompositionLocalOf { false }
""",
    "",
    "theme: old local",
)

check("LocalProgressiveBlur" not in theme, "a LocalProgressiveBlur reference survived in the theme")

pending.append((THEME, theme))

# ------------------------------------------------------------ 2. the pages read the settings

blur = BLUR.read_text(encoding="utf-8")

blur = swap(
    blur,
    """    strength: Float = 1f,
    fadeLength: Dp = ProgressiveBlurDefaults.FadeLength,
    blurRadius: Dp = ProgressiveBlurDefaults.BlurRadius,
): Modifier {
    val surface = MaterialTheme.colorScheme.surface

    val blurring = blur && supportsProgressiveBlur()

    val dark = surface.luminance() < DARK_SURFACE_LUMINANCE""",
    """    strength: Float = 1f,
): Modifier {
    val surface = MaterialTheme.colorScheme.surface

    val blurring = blur && supportsProgressiveBlur()

    val dark = surface.luminance() < DARK_SURFACE_LUMINANCE

    // ⚠ **The three numbers come from the theme now — r20.** They used to be constants tuned in
    // this file; the author asked for sliders, and the point of the sliders is that the page
    // bands and the settings manager's frosted window move together on one set of them.
    val settings = LocalBlurSettings.current

    val fadeLength = settings.fadeDp.coerceIn(BLUR_FADE_RANGE).dp

    val blurRadius = settings.radiusDp.coerceIn(BLUR_RADIUS_RANGE).dp""",
    "blur: read the settings",
)

blur = swap(
    blur,
    """    val fade = surface.copy(
        alpha = when {
            blurring && dark -> FADE_DARK
            blurring -> FADE_LIGHT
            dark -> SHADOW_DARK
            else -> SHADOW_LIGHT
        },
    )""",
    """    // ⚠ **The slider governs the blurred band only.** With no blur under it the band is the
    // whole treatment and has a different job — the author asked for that one *"very strong and
    // dark"* — so it keeps its own pair rather than inheriting a number chosen for a different
    // situation. Light and dark stop differing under the slider for the same reason: a value the
    // user set is not a value this file may adjust behind them.
    val fade = surface.copy(
        alpha = when {
            blurring -> settings.tintAlpha
            dark -> SHADOW_DARK
            else -> SHADOW_LIGHT
        },
    )""",
    "blur: tint from the slider",
)

blur = swap(
    blur,
    """/**
 * How dark the band gets at full strength, dark scheme and light.
 *
 * Above ObtainX's own 0.34/0.30, at the author's word once he had seen both: a band that is only
 * blurred reads as a smudge, and the tint is what says *the page ends here*.
 */
private const val FADE_DARK = 0.50f

private const val FADE_LIGHT = 0.45f

""",
    "",
    "blur: old tint constants",
)

for dead in ("FADE_DARK", "FADE_LIGHT", "ProgressiveBlurDefaults.FadeLength", "ProgressiveBlurDefaults.BlurRadius"):
    check(dead not in blur, f"blur: {dead} is still referenced")

# ProgressiveBlurDefaults held the two numbers that are now settings; nothing is left in it.
start = blur.index("/**\n * The two numbers that are the same on every page.")

blur = blur[:start].rstrip() + "\n"

blur = swap(
    blur,
    "import androidx.compose.ui.graphics.luminance\n",
    "import androidx.compose.ui.graphics.luminance\n"
    "import androidx.compose.ui.unit.Dp\n",
    "blur: Dp import placeholder",
)

# Dp was already imported below; collapse the duplicate the line above just made.
blur = swap(
    blur,
    "import androidx.compose.ui.unit.Dp\nimport androidx.compose.ui.unit.Dp\n",
    "import androidx.compose.ui.unit.Dp\n",
    "blur: duplicate Dp import",
)

blur = swap(
    blur,
    "import androidx.compose.ui.unit.dp\n",
    "import androidx.compose.ui.unit.dp\n"
    "import com.android.geto.designsystem.theme.BLUR_FADE_RANGE\n"
    "import com.android.geto.designsystem.theme.BLUR_RADIUS_RANGE\n"
    "import com.android.geto.designsystem.theme.LocalBlurSettings\n",
    "blur: settings imports",
)

pending.append((BLUR, blur))

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
