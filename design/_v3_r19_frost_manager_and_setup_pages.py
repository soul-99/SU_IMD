#!/usr/bin/env python3
"""
r19 — a frosted backdrop behind the settings manager, the manager-toggles wording, and two more
setup pages.

  1. **Frosted backdrop.** A Compose `Dialog` is a real window of its own, so what is behind it
     cannot be sampled from inside it — but Android will blur it for us: `FLAG_BLUR_BEHIND` plus
     `blurBehindRadius`, which is the platform's own frosted-window API and the same one the
     system uses behind its notification shade. Gated on the Progressive UI blur switch, on API 31,
     and on `WindowManager.isCrossWindowBlurEnabled()` — the system turns cross-window blur off
     under battery saver and on low-end devices, and asking for it there does nothing rather than
     failing. **The card itself stays opaque**: the author's *"keep in mind we need the contents to
     be legible"*. What frosts is the page around it, and the dim scrim comes down to 0.20 because
     a blur and a heavy scrim are two answers to the same question.

  2. **The manager-toggles wording**, his text verbatim but for one typo he approved ("which are
     show" → "shown"), as two lines in the dialog. The settings row keeps `6 of 6 shown`, which he
     chose over the description: the row says the state, the dialog explains it. And 'only selected
     ones' goes under those two lines as a dimmed caption, the way the Accessibility and Display
     over other apps rows carry theirs.

  3. **Two more setup pages before "You're almost done"** — Setting manager toggles, then Customise
     UI. Both follow the rule the four steps before them follow: *the same composable Settings
     already draws*, with `stepTitle` and `onSkip` set, so a row added later appears in both places
     without anyone remembering to do it twice. That is why the four UI rows come out of
     `SettingsScreen` into one composable rather than being rebuilt on a page.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

ROWS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/ManagerRowsDialog.kt"

STRINGS = ROOT / "feature/settings/src/main/res/values/strings.xml"

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


# ------------------------------------------------------------ 1. the theme publishes the switch

theme = THEME.read_text(encoding="utf-8")

theme = swap(
    theme,
    "    oledBackground: Boolean = false,\n    content: @Composable () -> Unit,\n",
    """    oledBackground: Boolean = false,
    /**
     * The author's "Progressive UI blur", published rather than used.
     *
     * ⚠ **Nothing in this file reads it.** It is here because a *dialog* needs it — see
     * `LocalProgressiveBlur` — and a dialog has no route to user data of its own. Every activity
     * already hands this theme the user's preferences, so this is the one place that can answer
     * without a second wiring.
     */
    progressiveBlur: Boolean = false,
    content: @Composable () -> Unit,
""",
    "theme: progressiveBlur parameter",
)

theme = swap(
    theme,
    """    CompositionLocalProvider(LocalOledBackground provides (colorScheme !== chosen)) {""",
    """    CompositionLocalProvider(
        LocalOledBackground provides (colorScheme !== chosen),
        LocalProgressiveBlur provides progressiveBlur,
    ) {""",
    "theme: provider",
)

theme = swap(
    theme,
    "val LocalOledBackground = staticCompositionLocalOf { false }\n",
    """val LocalOledBackground = staticCompositionLocalOf { false }

/**
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
    "theme: LocalProgressiveBlur",
)

pending.append((THEME, theme))

# ------------------------------------------------------------ 2. the dialog frosts its backdrop

dialog = DIALOG.read_text(encoding="utf-8")

dialog = swap(
    dialog,
    "import com.android.geto.designsystem.theme.LocalOledBackground\n",
    "import com.android.geto.designsystem.theme.LocalOledBackground\n"
    "import com.android.geto.designsystem.theme.LocalProgressiveBlur\n",
    "dialog: LocalProgressiveBlur import",
)

dialog = swap(
    dialog,
    "import androidx.compose.ui.window.Dialog\n",
    "import android.os.Build\n"
    "import android.view.WindowManager\n"
    "import androidx.compose.runtime.LaunchedEffect\n"
    "import androidx.compose.ui.platform.LocalDensity\n"
    "import androidx.compose.ui.platform.LocalView\n"
    "import androidx.compose.ui.window.Dialog\n"
    "import androidx.compose.ui.window.DialogWindowProvider\n",
    "dialog: platform imports",
)

dialog = swap(
    dialog,
    "    dismissible: Boolean = true,\n",
    """    dismissible: Boolean = true,
    /**
     * Frost the page behind this window while the Progressive UI blur switch is on.
     *
     * ⚠ **Opt-in, and so far one dialog opts in** — the settings manager, at the author's
     * request. Off elsewhere because a frosted backdrop is a statement that *this* window is the
     * subject and the app behind it is not, which is true of the manager and not of, say, a sort
     * order picker.
     */
    frostedBackdrop: Boolean = false,
""",
    "dialog: frostedBackdrop parameter",
)

# Applied inside the Dialog's own composition, which is where LocalView sees the dialog window.
for anchor, label in (
    ("""            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize(),
                color = containerColor,
                tonalElevation = tonalElevation,
            ) {""", "dialog: full-screen surface"),
    ("""            Surface(
                modifier = modifier,
                shape = shape,
                color = containerColor,
                tonalElevation = tonalElevation,
                content = content,
            )""", "dialog: flat surface"),
):
    dialog = swap(
        dialog,
        anchor,
        "            FrostedBackdrop(enabled = frostedBackdrop && LocalProgressiveBlur.current)\n\n"
        + anchor,
        label,
    )

dialog = swap(
    dialog,
    """                Surface(
                    // **The cap goes first, and that is the whole fix.**""",
    """                FrostedBackdrop(enabled = frostedBackdrop && LocalProgressiveBlur.current)

                Surface(
                    // **The cap goes first, and that is the whole fix.**""",
    "dialog: capped surface",
)

dialog += '''
/**
 * Blurs whatever is behind this dialog's window.
 *
 * ⚠ **The platform does this, not Compose, and it has to.** A `Dialog` is a window of its own; the
 * pixels behind it belong to another window and cannot be read from inside this one at any price.
 * `FLAG_BLUR_BEHIND` with a `blurBehindRadius` is Android's own answer — the same mechanism behind
 * the notification shade — and it arrived in API 31, the same release as the `RenderEffect` the
 * pages use.
 *
 * ⚠ **Three gates, and the third is not paranoia.** The switch, the API level, and
 * `isCrossWindowBlurEnabled`: the system turns cross-window blur off under battery saver, in
 * power-saving modes and on devices that cannot afford it, and a request made while it is off is
 * ignored rather than refused. Asking anyway would leave a dialog with a lowered scrim and no blur
 * to justify it, which is worse than no blur at all — hence the dim amount moving with the flag
 * rather than beside it.
 *
 * ⚠ **The card is untouched.** Only the page around it frosts; the author's *"we need the contents
 * to be legible"* is answered by leaving the container opaque and letting the blur separate the
 * window from what it is over.
 */
@Composable
private fun FrostedBackdrop(enabled: Boolean) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.S) return

    val view = LocalView.current

    val radius = with(LocalDensity.current) { DIALOG_BACKDROP_BLUR.roundToPx() }

    LaunchedEffect(view, enabled, radius) {
        // Null on the flat path, which draws into the page rather than into a window of its own.
        val window = (view.parent as? DialogWindowProvider)?.window ?: return@LaunchedEffect

        val supported = view.context.getSystemService(WindowManager::class.java)
            ?.isCrossWindowBlurEnabled == true

        if (enabled && supported) {
            window.addFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND)

            window.attributes = window.attributes.also { it.blurBehindRadius = radius }

            window.setDimAmount(DIALOG_FROSTED_DIM)
        } else {
            window.clearFlags(WindowManager.LayoutParams.FLAG_BLUR_BEHIND)

            window.attributes = window.attributes.also { it.blurBehindRadius = 0 }
        }
    }
}

/**
 * How hard the page behind a frosted dialog is blurred.
 *
 * Well above the 14 dp the page edges use, and for a different job: an edge band only has to say
 * *the list continues under here*, while a backdrop has to stop being readable so that the window
 * over it is the only thing worth reading.
 */
private val DIALOG_BACKDROP_BLUR: Dp = 32.dp

/**
 * And how much scrim is left once it is blurred.
 *
 * Material's own dialog dim is 0.32 and exists to push the page back; the blur has already done
 * that, and both at once turns the backdrop into a grey slab.
 */
private const val DIALOG_FROSTED_DIM = 0.20f
'''

pending.append((DIALOG, dialog))

manager = MANAGER.read_text(encoding="utf-8")

manager = swap(
    manager,
    "        horizontalMargin = metrics.margin,\n        onDismissRequest = onDismissRequest,\n",
    "        horizontalMargin = metrics.margin,\n"
    "        // ⚠ **The one dialog that frosts what is behind it — r19, at the author's request.**\n"
    "        // It is opened over somebody else's app as often as over IMD's own list, and the\n"
    "        // frosting is what says the manager is the subject rather than a card that happened\n"
    "        // to land there. Does nothing while Progressive UI blur is off.\n"
    "        frostedBackdrop = true,\n"
    "        onDismissRequest = onDismissRequest,\n",
    "manager: frostedBackdrop",
)

pending.append((MANAGER, manager))

# ------------------------------------------------------------ 3. the wording

strings = STRINGS.read_text(encoding="utf-8")

strings = swap(
    strings,
    '''    <string name="manager_rows_description">Only selected options are showed in the IMD\\'s Settings manager:</string>\n''',
    '''    <string name="manager_rows_description">These are the settings/ services which are shown in the IMD\\'s Settings manager window.</string>
    <string name="manager_rows_description_two">The Settings manager allows you to quickly see the live status of the current settings and toggle them on-off easily.</string>
    <string name="manager_rows_only_selected">only selected ones</string>
    <string name="manager_rows_step_title">Setting manager toggles</string>
    <string name="customise_ui_step_title">Customise UI</string>\n''',
    "strings: manager rows description",
)

pending.append((STRINGS, strings))

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
