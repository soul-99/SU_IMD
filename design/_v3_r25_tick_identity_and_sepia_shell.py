#!/usr/bin/env python3
"""
r25 — three tick bugs with one root cause, and the shell panel goes sepia in both themes.

## The three tick bugs

The author:

  1. *"whenever i launch settings manager from outside IMD app, it always shows up with the
     animation ticks drawn in the developer options, and both debugging toggles"*
  2. *"sometimes when i turn on shizuku toggle it does not show the tick animation"*
  3. *"the dooa toggle never shows tick animation"*

They look like three faults and they are two halves of one: **r24 decided "this just turned on" by
watching for a false → true edge inside the switch**, which is wrong in both directions.

**Bug 1 is a false positive.** Opening the manager over another app composes the rows before the
live states have been read, so a setting that is *already on* arrives as false and then becomes
true — a real edge, from the switch's point of view, that nobody caused. Developer settings and the
two debugging toggles are precisely the three that read fastest and are usually on, which is why
those three and no others.

**Bugs 2 and 3 are false negatives, and the cause is in the manager rather than the switch.**
`TargetRow` has *two* `GetoSwitch` call sites — `if (usable) { … } else { Box { … } }`. A row that
starts a service moves from unusable to usable when the start finishes, and Compose treats the two
call sites as different nodes: the old switch is discarded and a new one composes with `checked`
already true. There is no edge left to see. That is exactly Shizuku (`shizukuStarting` makes its
row unusable, so the tick is lost whenever the start is slow enough to register — the author's
*"sometimes"*) and exactly `Display over other apps` (`overlayWriteInFlight` and `overlayManaged`
put it through the same swap every single time — the author's *"never"*).

### The fix, in two parts

**A · One switch node per row.** The two branches merge into one `GetoSwitch` inside a `Box` whose
*modifier* varies, so the node survives a row becoming usable. The branch difference was only ever
`enabled`, `onCheckedChange` and whether the box takes the press.

**B · The tick is armed by a request, not inferred from an edge.** A switch ticks when it becomes
checked *and something asked it to* — the user pressed it, or a caller says a turn-on is
outstanding, or a `busy` period is in flight. Nothing arms a switch that is merely reading its
initial state, so bug 1 cannot happen; and because the arm is `rememberSaveable`, it survives the
trip to a system settings screen and back, which is what `Display over other apps` does every time.

The manager arms it from the row, because **the row press bypasses the switch**: the whole row is
clickable and calls `onSetEnabled` directly, so a switch that only watched its own handler would
never see the press that the author actually makes. `requestedOn` is simply the last thing the user
asked this row for.

⚠ **`previous` is gone.** With arming, the edge does not need to be detected at all: an unarmed
switch never ticks whatever its value does, and an armed one ticks the moment it reads true. That
also removes the seeded-`previous` special case r24 needed.

## The shell panel

The author: *"even for the dark mode i want to show the quirky shell output window in the sepia
colour one i use for light mode"*.

So the About screen's terminal block stops asking which theme is in force. The panel is always the
cream one, and — this is the part that has to move with it — **the prompt green goes with it**. The
dark prompt is `#B1D18A`, chosen to sit on `#212121`; on cream it is barely there. Keeping the
panel fixed while leaving the prompt on a luminance test would have made the one block in the app
that is deliberately a terminal illegible in dark mode, which is the opposite of what was asked
for. Both constants lose their `_LIGHT` suffix, because there is no longer another one to be
distinguished from.

The output amber is untouched: it was already fixed in both themes, and the KDoc above it says at
length not to quietly darken it.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"
MANAGER = ROOT / "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt"
SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

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


# ─────────────────────────────────────────────────────────────────────────────────────────────
# 1. GetoToggles.kt — the tick is armed, not inferred.
# ─────────────────────────────────────────────────────────────────────────────────────────────

toggles = TOGGLES.read_text(encoding="utf-8")

toggles = replace_once(
    toggles,
    """    busy: Boolean = false,
) {
    val scheme = MaterialTheme.colorScheme""",
    """    busy: Boolean = false,
    /**
     * A turn-on this switch did not hear about is outstanding.
     *
     * ⚠ **For callers whose press does not arrive through [onCheckedChange] — r25.** The settings
     * manager makes the *whole row* clickable and calls its own handler directly, so a switch
     * watching only its own callback never sees the press the author actually makes. This is that
     * press: the last thing the user asked this control for.
     *
     * Left false by every other call site, which arm themselves by being pressed.
     */
    armed: Boolean = false,
) {
    val scheme = MaterialTheme.colorScheme""",
    "toggles: armed parameter",
)

TICK_OLD_START = """    // ⚠ **Seeded from `checked`, so an already-on switch does not tick on first composition.** The
    // tick means *this just turned on*; six of them firing as the settings manager opens would
    // mean nothing at all."""

TICK_OLD_END = """        previous = checked
    }
"""

start = toggles.find(TICK_OLD_START)

end = toggles.find(TICK_OLD_END)

TICK_NEW = """    // ⚠ **Armed by a request, not inferred from an edge — r25, and r24 got this wrong.** r24
    // ticked whenever `checked` went false → true, which is not the same question as *did this
    // just turn on*. Opening the settings manager over another app composes its rows before the
    // live states have been read, so every setting that is already on arrives false and then
    // becomes true: three switches ticked on open for a transition nobody caused.
    //
    // A request is the honest trigger. Nothing arms a switch that is merely reading its initial
    // value, so that cannot happen; and `rememberSaveable` means an arm survives the trip to a
    // system settings screen and back, which is what `Display over other apps` does every time it
    // is pressed — the case r24 could not tick at all.
    var awaiting by rememberSaveable { mutableStateOf(false) }

    // Three things count as a request, and the switch cannot tell them apart because they are the
    // same event reaching it by different routes: pressed here, pressed on a row that owns the
    // press, or already in flight.
    LaunchedEffect(armed) {
        if (armed) awaiting = true
    }

    LaunchedEffect(busy) {
        if (busy) awaiting = true
    }

    LaunchedEffect(checked) {
        if (!checked) {
            // A request that ended up off is a request that failed, and there is nothing to
            // celebrate later. Unless one is still outstanding, in which case it is not over.
            if (!busy && !armed) awaiting = false

            return@LaunchedEffect
        }

        if (!awaiting) return@LaunchedEffect

        awaiting = false

        ticking = true

        delay(SWITCH_TICK_HOLD_MILLIS)

        ticking = false
    }
"""

if check(start != -1 and end != -1 and start < end, "toggles: the tick block was not found"):
    toggles = toggles[:start] + TICK_NEW + toggles[end + len(TICK_OLD_END):]

# ⚠ `ticking` was declared *inside* the block replaced above, between `previous` and the effect,
# so it went with it. It is put back before the effect that now sets it — and only once: the first
# draft of this script also tried to delete it from its old position, which by then was the new one,
# and removed the declaration it had just added. Same family as r24a's rename: an edit that assumes
# a state the previous edit already changed.
toggles = replace_once(
    toggles,
    """    val offInk = if (error) scheme.error else scheme.outline

""",
    """    val offInk = if (error) scheme.error else scheme.outline

    var ticking by remember { mutableStateOf(false) }

""",
    "toggles: ticking declaration",
)

# ── the press arms the switch on every ordinary call site ────────────────────────────────────
toggles = replace_once(
    toggles,
    """        // Dropped whenever the control is not operable, which is what makes the muted state
        // inert while still being drawn from the enabled palette.
        onCheckedChange = if (enabled) onCheckedChange else null,""",
    """        // ⚠ **Wrapped so that pressing the switch arms its own tick**, which is how every
        // caller outside the settings manager gets one without passing anything. Dropped
        // entirely whenever the control is not operable, which is what makes the muted state
        // inert while still being drawn from the enabled palette.
        onCheckedChange = if (enabled && onCheckedChange != null) {
            { want ->
                if (want) awaiting = true

                onCheckedChange(want)
            }
        } else {
            null
        },""",
    "toggles: self-arming handler",
)

toggles = replace_once(
    toggles,
    "import androidx.compose.runtime.remember\n",
    "import androidx.compose.runtime.remember\nimport androidx.compose.runtime.saveable.rememberSaveable\n",
    "toggles: rememberSaveable import",
)

body = code(toggles)

check("previous" not in body, "toggles: the previous-value latch should be gone")

check(body.count("var awaiting by rememberSaveable") == 1, "toggles: expected one arming latch")

check(body.count("var ticking by remember") == 1, "toggles: expected one ticking latch")

check(body.count("awaiting = true") == 3, "toggles: expected three ways to arm the tick")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 2. AndroidSettingsManagerDialog.kt — one switch node per row, and the row owns the request.
# ─────────────────────────────────────────────────────────────────────────────────────────────

manager = MANAGER.read_text(encoding="utf-8")

manager = replace_once(
    manager,
    """    var showFailureHelp by rememberSaveable { mutableStateOf(false) }

    val switchScale = size.switchScale""",
    """    var showFailureHelp by rememberSaveable { mutableStateOf(false) }

    // ⚠ **The last thing the user asked this row for — r25, and it exists because the press does
    // not go through the switch.** The whole row is clickable and calls `onSetEnabled` directly,
    // so `GetoSwitch` never hears about the press the author actually makes and could not know
    // that a turn-on was outstanding. Saveable because `Display over other apps` leaves for a
    // system settings screen between the press and the result.
    var requestedOn by rememberSaveable { mutableStateOf(false) }

    val request: (Boolean) -> Unit = { want ->
        requestedOn = want

        onSetEnabled(want)
    }

    val switchScale = size.switchScale""",
    "manager: row request",
)

manager = replace_once(
    manager,
    """            .clickable(enabled = usable || onClickWhenUnusable != null) {
                if (usable) onSetEnabled(!enabled) else onClickWhenUnusable?.invoke()
            }""",
    """            .clickable(enabled = usable || onClickWhenUnusable != null) {
                if (usable) request(!enabled) else onClickWhenUnusable?.invoke()
            }""",
    "manager: row clickable",
)

SWITCH_OLD_START = """        // Red only while the failure is being reported. Material's default colours are
        // reused otherwise rather than restated, so a theme change cannot leave this row
        // looking subtly different from its neighbours.
        if (usable) {"""

SWITCH_OLD_END = """                    onCheckedChange = null,
                )
            }
        }
    }
"""

start = manager.find(SWITCH_OLD_START)

end = manager.find(SWITCH_OLD_END)

SWITCH_NEW = """        // ⚠ **One switch, not one per branch — r25, and the split was a real bug.** This used to
        // be `if (usable) GetoSwitch(…) else Box { GetoSwitch(…) }`, and Compose treats two call
        // sites as two nodes: a row that became usable threw its switch away and composed a new
        // one, losing everything the old one remembered. That is why the Shizuku toggle only
        // sometimes showed its tick — it is unusable while `shizukuStarting` — and why `Display
        // over other apps`, which goes through the same swap on every press, never showed one at
        // all. Varying the *modifier* keeps the node.
        Box(
            modifier = if (usable) {
                Modifier
            } else {
                // A disabled Switch swallows taps, so an unusable row would look simply
                // broken. The box takes the press instead and explains itself, which works
                // because the switch below is handed a null onCheckedChange and so has no
                // input modifier of its own for the press to be caught by.
                Modifier.clickable(enabled = onClickWhenUnusable != null) {
                    onClickWhenUnusable?.invoke()
                }
            },
        ) {
            GetoSwitch(
                // ⚠ **Scaled, and this is what actually takes the height out of the dialog.** A
                // Material switch has no size to set and reserves a 48.dp minimum, which six
                // rows of turned into the height the author reported.
                //
                // ⚠ Its touch target shrinks with it, and that is safe **here only** because the
                // whole row already takes the press — see the row's own comment above. A switch
                // standing on its own must not copy this.
                modifier = Modifier.scale(switchScale),
                checked = enabled,
                // ⚠ **The off state in the error palette when the service failed to start.**
                // One flag rather than the three colour overrides this used to be: the switch
                // takes the decision and derives the palette, so there is nothing to keep in
                // step when the scheme changes.
                error = failed,
                // r24: the ring that used to sit beside the title above.
                busy = starting,
                // r25: the press this switch never heard, because the row took it.
                armed = requestedOn,
                // Only reaches the drawing while the switch is disabled, which is this row's
                // unusable state. Not greyed into nothing: the row is still reporting a real
                // state — a Shevery service that is genuinely running — and the stock disabled
                // palette makes a true "on" look like a dead control.
                liveWhileDisabled = true,
                enabled = usable,
                onCheckedChange = if (usable) request else null,
            )
        }
    }
"""

if check(start != -1 and end != -1 and start < end, "manager: the switch branches were not found"):
    manager = manager[:start] + SWITCH_NEW + manager[end + len(SWITCH_OLD_END):]

body = code(manager)

check(body.count("GetoSwitch(") == 1, "manager: expected exactly one switch call site per row")

check(body.count("onSetEnabled(!enabled)") == 0, "manager: the row should press through request")

check(body.count("armed = requestedOn") == 1, "manager: the switch should take the row's request")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 3. SettingsScreen.kt — the terminal block is sepia in both themes.
# ─────────────────────────────────────────────────────────────────────────────────────────────

settings = SETTINGS.read_text(encoding="utf-8")

settings = replace_once(
    settings,
    """    val shellDark = MaterialTheme.colorScheme.surface.luminance() < 0.5f

    val shellPrompt = if (shellDark) SHELL_PROMPT_DARK else SHELL_PROMPT_LIGHT""",
    """    // ⚠ **One prompt green now, because there is one panel — r25.** The dark prompt existed to
    // sit on the dark panel; with the panel fixed to the cream one it would be barely there. A
    // fixed panel and a themed prompt is the one combination that is worse than either.
    val shellPrompt = SHELL_PROMPT""",
    "settings: shell prompt",
)

settings = replace_once(
    settings,
    """    // Which panel goes behind it, read from the scheme that is actually in force rather than
    // from isSystemInDarkTheme(). The app has a user-selectable theme - FOLLOW_SYSTEM, LIGHT,
    // DARK - so asking the *system* would give a user on LIGHT with a dark system a grey panel
    // inside a light app, and the reverse. This is also the only form that stays right under
    // dynamic colour, where the scheme is neither of the two the app declares and no enum
    // comparison would help.
    val shellPanel = if (shellDark) {
        SHELL_PANEL_DARK
    } else {
        SHELL_PANEL_LIGHT
    }""",
    """    // ⚠ **The same panel in both themes — r25, at the author's word:** *"even for the dark mode
    // i want to show the quirky shell output window in the sepia colour one i use for light
    // mode"*. It used to be picked by a luminance test on the live scheme, which was the right
    // way to ask a question this block no longer asks. The block is an easter egg drawn as a
    // terminal, and a terminal is whatever colour its author made it — the same argument
    // [SHELL_OUTPUT_COLOUR] has carried since it was pinned.
    val shellPanel = SHELL_PANEL""",
    "settings: shell panel",
)

settings = replace_once(
    settings,
    """private val SHELL_PROMPT_LIGHT = Color(0xFF4C662B)

private val SHELL_PROMPT_DARK = Color(0xFFB1D18A)

/** The panel under the output in a dark scheme: grey, not black, and not the app's green. */
private val SHELL_PANEL_DARK = Color(0xFF212121)

/** And in a light one. */
private val SHELL_PANEL_LIGHT = Color(0xFFF2F1E9)""",
    """private val SHELL_PROMPT = Color(0xFF4C662B)

/** The sepia the author asked for in both themes — r25. Not the app's green, and not the page's. */
private val SHELL_PANEL = Color(0xFFF2F1E9)""",
    "settings: shell constants",
)

settings = replace_once(
    settings,
    """ * The same argument [SHELL_OUTPUT_COLOUR] already carries: the colour of terminal output is
 * not something a theme has an opinion about. Which of the two applies is decided by the same
 * luminance test the panel behind it uses, not by isSystemInDarkTheme() — the app has its own
 * light/dark/follow-system setting, and asking the system would give a light-themed app on a
 * dark-themed phone the wrong one.
 */""",
    """ * The same argument [SHELL_OUTPUT_COLOUR] already carries: the colour of terminal output is not
 * something a theme has an opinion about. ⚠ **And since r25 there is only one of them**, because
 * the panel behind it is the author's sepia in both themes — a dark prompt green was only ever
 * there to sit on a dark panel that no longer exists.
 */""",
    "settings: prompt KDoc",
)

settings = replace_once(
    settings,
    """    // Asked by luminance rather than isSystemInDarkTheme(), for the reason the comment above
    // SHELL_PROMPT_LIGHT gives: the app has its own light/dark/follow-system setting, and the
    // system's answer is the wrong one for a light-themed app on a dark-themed phone. It also""",
    """    // Asked by luminance rather than isSystemInDarkTheme(): the app has its own
    // light/dark/follow-system setting, and the system's answer is the wrong one for a
    // light-themed app on a dark-themed phone. It also""",
    "settings: OLED comment",
)

body = code(settings)

for gone in ("SHELL_PROMPT_DARK", "SHELL_PANEL_DARK", "SHELL_PANEL_LIGHT", "SHELL_PROMPT_LIGHT", "shellDark"):
    check(gone not in body, f"settings: {gone} should be gone from the code")

check(body.count("SHELL_PANEL") == 2, "settings: expected the declaration and one use of SHELL_PANEL")

check(body.count("SHELL_PROMPT") == 2, "settings: expected the declaration and one use of SHELL_PROMPT")

# `luminance` still has a user — the OLED row — so the import stays. Asserted rather than assumed.
check("luminance()" in body, "settings: luminance is now unused and its import should be removed")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in ((TOGGLES, toggles), (MANAGER, manager), (SETTINGS, settings)):
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
