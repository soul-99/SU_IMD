#!/usr/bin/env python3
"""
r22 — the frosted manager window finished, the S22 Ultra switch, and a more saturated green.

Three things, and the first is the one with the history.

**The frosted window.** r22's mechanism was written in the previous pass and left unverified; this
script finishes it. Three faults were found by reading it back:

  1. `FrostedWindow.measure` no longer exists — the bounds-measuring `Modifier` belonged to r21's
     `setBackgroundBlurRadius` approach and went with it — but the `flat` and `compact` branches
     still say `.then(frost.measure)`. That is a compile error in two places.
  2. The `flat` branch has no window at all: it draws into the page. `applyWindowFrost` returns
     early there, correctly, but `frost.frosted` is still true, so the Surface would go
     transparent and the setup page would have no card. The flat path must never frost. It no
     longer asks.
  3. `DialogEntrance` on the frosted path is the exact trap this file already documents for the
     `compact` branch: AnimatedVisibility does not compose its content until the transition
     starts, so for one frame the content is nothing — and a `WRAP_CONTENT` window laid out at
     nothing, then regrown, is a visible snap. The frosted window is `WRAP_CONTENT`. The
     animation goes.

And one thing the mechanism never had: with the window wrapping the card, the full-screen `Box`
that used to apply `horizontalMargin` is gone, so on a display narrower than `maxWidth` the card
would reach both edges. The cap now takes the margin off the display width itself.

**The switch.** The author: *"the switch still look wierd in s22 ultra … looks fine on razr fold"*.
The geometry is identical on both — that was measured off his screenshots. What differs is the
scheme: the razr runs dynamic colour and gets a dark blue `primaryContainer` track under a light
blue `primary` thumb, which reads as a switch; the S22 Ultra's scheme puts a muted mid-tone under a
mid-tone and the thumb stops being a separate object. Material's own pairing is track = `primary`,
thumb = `onPrimary` — a filled track with its own contrast colour on top — and it is contrasty by
construction under *any* scheme, dynamic or not, because `onPrimary` is defined as the thing that
is legible on `primary`. That is the pairing this takes.

**The green.** *"for the imd with dynamic theme off green colour i need more saturated green"* —
the accents move from r18's ×1.35 to ×1.6, the "More" column of `design/template_r18_saturation.html`.
Accents only: the surface ladder, the error palette and the near-black `on…Container` inks are left
exactly where r13c and r18 put them, because the author asked for a greener green and not a greener
page.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"
TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"
THEME = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/theme/Theme.kt"

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


# ─────────────────────────────────────────────────────────────────────────────────────────────
# Dialog.kt — finish the r22 frosted window.
# ─────────────────────────────────────────────────────────────────────────────────────────────

dialog = DIALOG.read_text(encoding="utf-8")

# ── imports left behind by the mechanism swap ────────────────────────────────────────────────
#
# `Context` was the receiver spelled out before the service lookup went through `view.context`;
# the three state imports belonged to the bounds `mutableStateOf` r21 used to size an
# `InsetDrawable`. Nothing in the file says any of the four any more — asserted below rather than
# assumed, because an import that is still used is a build break and an import that is not is a
# check12 finding.
for gone in (
    "import android.content.Context\n",
    "import androidx.compose.runtime.getValue\n",
    "import androidx.compose.runtime.mutableStateOf\n",
    "import androidx.compose.runtime.setValue\n",
):
    symbol = gone.rsplit(".", 1)[1].strip()

    # ⚠ Count on the *body*, not the whole file: the import line itself says the symbol, which is
    # the comment trap that has caught this script three rounds running in another shape.
    body = dialog.replace(gone, "")

    check(
        symbol not in body,
        f"dialog: {symbol} is still used, so its import cannot be removed",
    )

    dialog = replace_once(dialog, gone, "", f"dialog: import {symbol}")

dialog = replace_once(
    dialog,
    "import androidx.compose.ui.platform.LocalDensity\n",
    "import androidx.compose.ui.platform.LocalConfiguration\nimport androidx.compose.ui.platform.LocalDensity\n",
    "dialog: LocalConfiguration import",
)

# ── the flat branch never frosts ─────────────────────────────────────────────────────────────
FLAT_OLD = """            val frost = rememberFrostedWindow(
                frostedWindow,
                containerColour = containerColor,
            )

            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize()
                    .then(frost.measure),
                color = frost.colour(containerColor),
                contentColor = frost.content,
                tonalElevation = tonalElevation,
            ) {
"""

FLAT_NEW = """            // ⚠ **`frostedWindow` is ignored here, and it has to be.** Frosting is a property
            // of a *window*: it is the window that carries `FLAG_BLUR_BEHIND` and paints the
            // card. A setup step has no window — it draws into the page it is part of — so
            // honouring the flag would mean turning this Surface transparent in exchange for a
            // blur that nothing can apply, and the step would lose its card for nothing.
            Surface(
                modifier = modifier
                    .widthIn(max = maxWidth)
                    .fillMaxSize(),
                color = containerColor,
                tonalElevation = tonalElevation,
            ) {
"""

dialog = replace_once(dialog, FLAT_OLD, FLAT_NEW, "dialog: flat branch")

# ── the compact branch: `measure` went with r21's mechanism ──────────────────────────────────
dialog = replace_once(
    dialog,
    "            Surface(\n                modifier = modifier.then(frost.measure),\n",
    "            Surface(\n                modifier = modifier,\n",
    "dialog: compact Surface modifier",
)

# ── the frosted branch: no entrance animation, and the margin comes back ─────────────────────
FROSTED_OLD = """            // ⚠ **No box behind it, and that is not a shortcut.** The window is the card here, so
            // a full-screen Box would stretch the window straight back to the whole screen and
            // take the blur's confinement with it. There is a real outside again, which is why
            // the hand-rolled tap-to-dismiss is not needed either: `dismissOnClickOutside` has
            // something to fire on.
            DialogEntrance {
                Surface(
                    modifier = Modifier
                        .widthIn(max = maxWidth)
                        .fillMaxWidth()
                        .then(modifier),
                    shape = shape,
                    color = frost.colour(containerColor),
                    contentColor = frost.content,
                    tonalElevation = tonalElevation,
                    content = content,
                )
            }

            return@Dialog
"""

FROSTED_NEW = """            // ⚠ **No box behind it, and that is not a shortcut.** The window is the card here, so
            // a full-screen Box would stretch the window straight back to the whole screen and
            // take the blur's confinement with it. There is a real outside again, which is why
            // the hand-rolled tap-to-dismiss is not needed either: `dismissOnClickOutside` has
            // something to fire on.
            //
            // ⚠ **And no `DialogEntrance` either, for the reason the `compact` branch above
            // gives.** AnimatedVisibility does not compose its content until the transition
            // starts, so there is one frame in which this window has nothing in it — and this
            // window is `WRAP_CONTENT`, so that frame lays it out at nothing and the regrow is
            // the visible snap that was measured off the services manager in r13. The platform
            // animates a wrapped window itself; there is nothing left here to add.
            //
            // ⚠ **The margin is taken off the display, not applied around the card.** The box
            // that used to pad this away is gone with the full-screen window, and padding
            // *inside* a wrapped window would only make the window bigger and let its own
            // background drawable paint the margin. So the cap absorbs it: the card stops short
            // of both edges by the same amount it did before.
            val display = LocalConfiguration.current.screenWidthDp.dp

            val frostedWidth = minOf(maxWidth, display - horizontalMargin * 2)

            Surface(
                modifier = Modifier
                    .widthIn(max = frostedWidth)
                    .fillMaxWidth()
                    .then(modifier),
                shape = shape,
                color = frost.colour(containerColor),
                contentColor = frost.content,
                tonalElevation = tonalElevation,
                content = content,
            )

            return@Dialog
"""

dialog = replace_once(dialog, FROSTED_OLD, FROSTED_NEW, "dialog: frosted branch")

check("frost.measure" not in dialog, "dialog: something still asks for the removed frost.measure")

check(dialog.count("rememberFrostedWindow(") == 3, "dialog: expected one declaration and two calls")

check(dialog.count("DialogEntrance {") == 1, "dialog: expected exactly one remaining DialogEntrance")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# GetoToggles.kt — Material's own track/thumb pairing.
# ─────────────────────────────────────────────────────────────────────────────────────────────

toggles = TOGGLES.read_text(encoding="utf-8")

TRACK_OLD = """        checked && enabled -> scheme.primaryContainer
        checked -> scheme.primaryContainer.copy(alpha = if (live) 0.45f else 0.28f)
"""

TRACK_NEW = """        // ⚠ **`primary`, not `primaryContainer` — r22.** A container tone is a *background*
        // colour: the scheme guarantees text is legible on it, and guarantees nothing at all
        // about another accent sitting on top. Under dynamic colour the pair happened to work —
        // the author's razr — and under the static scheme both tones landed mid-range and the
        // thumb dissolved into the track, which is the "weird" he saw on the S22 Ultra. `primary`
        // with `onPrimary` on it is the one pairing the scheme *defines* as contrasting, so it
        // holds under every scheme rather than under the lucky ones.
        checked && enabled -> scheme.primary
        checked -> scheme.primary.copy(alpha = if (live) 0.45f else 0.28f)
"""

toggles = replace_once(toggles, TRACK_OLD, TRACK_NEW, "toggles: checked track")

THUMB_OLD = """        checked && enabled -> scheme.primary
        checked -> scheme.primary.copy(alpha = if (live) 0.55f else 0.38f)
"""

THUMB_NEW = """        checked && enabled -> scheme.onPrimary
        checked -> scheme.onPrimary.copy(alpha = if (live) 0.55f else 0.38f)
"""

toggles = replace_once(toggles, THUMB_OLD, THUMB_NEW, "toggles: checked thumb")

toggles = replace_once(
    toggles,
    "                // ⚠ **Only while off.** A checked track is a filled `primaryContainer` and needs\n",
    "                // ⚠ **Only while off.** A checked track is a filled `primary` and needs\n",
    "toggles: rim comment",
)

# ⚠ The checkbox a hundred lines down also says `checked && enabled -> scheme.primary`, and after
# the track edit the switch says it too. Two is the correct count; one would mean the thumb edit
# hit the checkbox instead.
check(
    toggles.count("        checked && enabled -> scheme.primary\n") == 2,
    "toggles: the switch track and the checkbox should be the two users of primary",
)

check(
    toggles.count("scheme.primaryContainer") == 0,
    "toggles: primaryContainer should no longer appear",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# Theme.kt — the static green at ×1.6.
# ─────────────────────────────────────────────────────────────────────────────────────────────

theme = THEME.read_text(encoding="utf-8")

# Anchored on the property name, never on the hex: `#1A1C16` is the dark `surfaceContainerLow`
# *and* the light `onBackground`, and a hex-anchored swap in r13c changed the wrong one.
LIGHT = {
    "primary": ("0xFF4D7021", "0xFF4E7819"),
    "primaryContainer": ("0xFFCFFA96", "0xFFCFFF91"),
    "secondary": ("0xFF596645", "0xFF5A6A42"),
    "secondaryContainer": ("0xFFDEECC3", "0xFFDFF0BF"),
    "onSecondaryContainer": ("0xFF152108", "0xFF152405"),
    "tertiary": ("0xFF306E6A", "0xFF2A746F"),
    "tertiaryContainer": ("0xFFB4F4EE", "0xFFAEFAF2"),
    "inversePrimary": ("0xFFB2DD7E", "0xFFB3E675"),
}

DARK = {
    "primary": ("0xFFB2DD7E", "0xFFB3E675"),
    "primaryContainer": ("0xFF36580C", "0xFF375F05"),
    "onPrimaryContainer": ("0xFFCFFA96", "0xFFCFFF91"),
    "secondary": ("0xFFC0D0A8", "0xFFC1D4A4"),
    "onSecondary": ("0xFF2B371A", "0xFF2B3918"),
    "secondaryContainer": ("0xFF414E2F", "0xFF41512C"),
    "onSecondaryContainer": ("0xFFDEECC3", "0xFFDFF0BF"),
    "tertiary": ("0xFF98D8D2", "0xFF92DED6"),
    "tertiaryContainer": ("0xFF175652", "0xFF115C57"),
    "onTertiaryContainer": ("0xFFB4F4EE", "0xFFAEFAF2"),
    "inversePrimary": ("0xFF4D7021", "0xFF4E7819"),
}


def scheme_slice(text: str, opener: str, label: str) -> tuple[int, int]:
    start = text.find(opener)

    if not check(start != -1, f"theme: {label} not found"):
        return -1, -1

    end = text.find("\n)\n", start)

    if not check(end != -1, f"theme: {label} has no closing paren"):
        return -1, -1

    return start, end


def retint(text: str, opener: str, label: str, table: dict[str, tuple[str, str]]) -> str:
    start, end = scheme_slice(text, opener, label)

    if start == -1:
        return text

    block = text[start:end]

    for name, (old_hex, new_hex) in table.items():
        old = f"    {name} = Color({old_hex}),"

        new = f"    {name} = Color({new_hex}),"

        found = block.count(old)

        if not check(found == 1, f"theme: {label}.{name} = {old_hex} found {found}x, expected 1"):
            continue

        block = block.replace(old, new, 1)

    return text[:start] + block + text[end:]


theme = retint(theme, "private val LightGreenColorScheme = lightColorScheme(", "light", LIGHT)

theme = retint(theme, "private val DarkGreenColorScheme = darkColorScheme(", "dark", DARK)

# The surfaces the author asked for in r13c must be exactly where he left them.
for untouched in (
    "    background = Color(0xFF1B1E16),",
    "    surfaceContainerLowest = Color(0xFF14160E),",
    "    surfaceContainerLow = Color(0xFF21241C),",
    "    surfaceContainerHigh = Color(0xFF31352B),",
    "    error = Color(0xFFBA1A1A),",
):
    check(untouched in theme, f"theme: {untouched.strip()} was disturbed")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

DIALOG.write_text(dialog, encoding="utf-8")

TOGGLES.write_text(toggles, encoding="utf-8")

THEME.write_text(theme, encoding="utf-8")

for path in (DIALOG, TOGGLES, THEME):
    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
