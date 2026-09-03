#!/usr/bin/env python3
"""
r24 — the rim comes off `All off` / `All on`, and the fill does the work instead.

The author, on r23's version: *"for all all off buttons you added lines at edges remove them,
instead increase their alpha to increase their visibility and make them opaque"*.

r23 reached for a hairline because the pill sits on a card that is now translucent, and a subtle
fill has nothing solid behind it to be subtle against. That reasoning was right about the problem
and wrong about the remedy: a rim is a fourth line in a dialog that already has a card edge, a
gap through the pill and six row separators, and the author looked at it and did not want it.

So the fill goes up instead — and *opaque*, which is the word that decides how. The neutral ladder
tops out at `surfaceContainerHighest`, which r23 already used and which is still too near the card
in dark mode, so there is no higher rung to climb to. What there is, is the scheme's own ink:
`onSurface` composited over the top container at a low alpha gives a colour that is

  * **brighter than the card in dark mode** and **darker than it in light mode**, because the ink
    is the opposite of the page in both — so one number serves both themes and neither has to be
    special-cased;
  * **fully opaque**, because `compositeOver` resolves the alpha rather than carrying it. That is
    the author's *"make them opaque"*: on the frosted manager the window behind is translucent, and
    a pill that shares any of that translucency is a pill with a wallpaper behind it.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def code(text: str) -> str:
    """Just the lines the compiler reads — see the note in `_v3_r23_*.py`."""
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


manager = MANAGER.read_text(encoding="utf-8")

# ── the fill, and the rim that is no longer computed ─────────────────────────────────────────
PILL_OLD = """    // ⚠ **Top of the neutral ladder plus a rim — r23, from the author's annotated screenshot.**
    // `surfaceVariant` is a mid neutral, and this row sits on a card that is now translucent: in
    // dark mode the two were within a few points of each other and the pill all but disappeared.
    // The shade stays neutral, because the author's r2b3d pick was that this row belongs to the
    // switches beside it rather than to the filled pair at the foot of the dialog — so it climbs
    // the ladder rather than borrowing an accent, and the rim does the rest. A hairline reads at
    // any card opacity, which a fill by itself cannot.
    val container = if (enabled) {
        MaterialTheme.colorScheme.surfaceContainerHighest
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    }

    val content = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }

    val rim = if (enabled) {
        MaterialTheme.colorScheme.outline
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    }
"""

PILL_NEW = """    // ⚠ **The ink lifted over the top container, opaque — r24, at the author's word:** *"remove
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
"""

manager = replace_once(manager, PILL_OLD, PILL_NEW, "manager: pill fill")

# ── the argument each half was passed ────────────────────────────────────────────────────────
for half, label in (("off", "All off"), ("on", "All on")):
    manager = replace_once(
        manager,
        f"""            label = stringResource(R.string.settings_manager_all_{half}),
            shape = PILL_{'START' if half == 'off' else 'END'}_SHAPE,
            container = container,
            content = content,
            rim = rim,
""",
        f"""            label = stringResource(R.string.settings_manager_all_{half}),
            shape = PILL_{'START' if half == 'off' else 'END'}_SHAPE,
            container = container,
            content = content,
""",
        f"manager: {label} rim argument",
    )

# ── and the parameter and the stroke ─────────────────────────────────────────────────────────
manager = replace_once(
    manager,
    """    container: Color,
    content: Color,
    /** The hairline that makes this read as a button on a translucent card — see [MasterPill]. */
    rim: Color,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxHeight(),
        shape = shape,
        color = container,
        contentColor = content,
        border = BorderStroke(width = PILL_RIM, color = rim),
    ) {""",
    """    container: Color,
    content: Color,
    enabled: Boolean,
    onClick: () -> Unit,
) {
    Surface(
        modifier = modifier.fillMaxHeight(),
        shape = shape,
        color = container,
        contentColor = content,
    ) {""",
    "manager: PillHalf rim parameter",
)

manager = replace_once(
    manager,
    """/** The hairline around each half of [MasterPill]. One dp: a rim, not a frame. */
private val PILL_RIM = 1.dp

private val PILL_HEIGHT = 28.dp""",
    """/**
 * How far [MasterPill]'s fill is lifted off the top of the surface ladder.
 *
 * Small on purpose: this row is a neutral that has to be *findable*, not an accent that competes
 * with the two filled buttons at the foot of the dialog.
 */
private const val PILL_LIFT = 0.18f

private val PILL_HEIGHT = 28.dp""",
    "manager: PILL_LIFT",
)

# ── imports: BorderStroke was added by r23 for this and nothing else; compositeOver is new ───
body = code(manager)

BORDER = "import androidx.compose.foundation.BorderStroke\n"

check("BorderStroke" not in code(manager.replace(BORDER, "")), "manager: BorderStroke is still used")

manager = replace_once(manager, BORDER, "", "manager: BorderStroke import")

if "import androidx.compose.ui.graphics.compositeOver\n" not in manager:
    manager = replace_once(
        manager,
        "import androidx.compose.ui.graphics.Color\n",
        "import androidx.compose.ui.graphics.Color\nimport androidx.compose.ui.graphics.compositeOver\n",
        "manager: compositeOver import",
    )

body = code(manager)

check("PILL_RIM" not in body, "manager: PILL_RIM should be gone from the code")

check("rim = rim" not in body, "manager: the rim argument should be gone")

check("border = BorderStroke" not in body, "manager: the border argument should be gone")

check(body.count("PILL_LIFT") == 2, "manager: expected the declaration and one use of PILL_LIFT")

check(body.count("compositeOver") == 2, "manager: expected the import and one use of compositeOver")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

MANAGER.write_text(manager, encoding="utf-8")

print(f"wrote {MANAGER.relative_to(ROOT).as_posix()}")

print("ok")
