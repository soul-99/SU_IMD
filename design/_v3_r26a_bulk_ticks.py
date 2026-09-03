#!/usr/bin/env python3
"""
r26 (part two) — every switch a bulk button turns on gets its tick, and they land together.

The author: *"when i use all on/all off/hide or unhide settings or revert to def button only shizuku
toggle shows the tick animation, in all these button presses show tick icons to every toggle which
was off before button press an turn on afterwards, show all ticks together when all settings are
restored"*.

## Why only Shizuku ticked

r25 gave a switch three ways to be armed: pressed through its own handler, told by its row
(`armed`), or already in flight (`busy`). A bulk button is none of the three for most rows — it
calls `onSetAll` / `onHideSettings` / `onRevertToDefault` and never touches any row's
`requestedOn`. Shizuku ticked because it is the one row whose `starting` flag goes up during that
work, so `busy` armed it by accident rather than by design.

## Two things had to change, and the second is the subtle one

**A · Somebody has to arm the rows a bulk button is about to move.** The dialog does, because it is
the only place that knows a bulk action started *and* what every row read beforehand. When one
begins, every row that is currently **off** is armed — not "every row that ends up on", which would
be a guess made before the states have been re-read. A row that stays off never ticks anyway,
because a switch only ticks when it is armed *and* becomes checked; so arming the wider set is both
simpler and race-free.

The arm is set from two places on purpose: the dialog's `busy` flag going up, and each of the five
buttons directly. `busy` alone would be enough if all five raised it, and belt-and-braces is cheap
compared with another round to find out that one of them does not.

**B · `GetoSwitch` could not act on an arm that arrived late, and that is the actual bug.** r25
watched with `LaunchedEffect(checked)`, which only restarts when `checked` changes. A bulk action
arms rows whose value is *about* to change — fine — but the moment the arm is late, or a row is
already on, there is no `checked` transition left to restart on and the tick never fires. Keying the
effect on `armed` too is not the fix either: it would restart *during* the one-second hold every
time `armed` or `busy` moved, and cut the tick short.

So the watching moves into a single `LaunchedEffect(Unit)` collecting a `snapshotFlow`, fed by
`rememberUpdatedState`. It never restarts, so nothing interrupts the hold; and it sees every change
to either value, so an arm that lands after the switch is already on still ticks.

**"All ticks together"** falls out of that: the rows' states arrive in one `states` update, so every
armed row sees its `checked` flip in the same snapshot and every tick starts on the same frame.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"
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


# ─────────────────────────────────────────────────────────────────────────────────────────────
# 1. GetoToggles.kt — one collector that never restarts.
# ─────────────────────────────────────────────────────────────────────────────────────────────

toggles = TOGGLES.read_text(encoding="utf-8")

WATCH_OLD_START = """    // ⚠ **Armed by a request, not inferred from an edge — r25, and r24 got this wrong.**"""

WATCH_OLD_END = """        delay(SWITCH_TICK_HOLD_MILLIS)

        ticking = false
    }
"""

start = toggles.find(WATCH_OLD_START)

end = toggles.find(WATCH_OLD_END)

WATCH_NEW = """    // ⚠ **Armed by a request, not inferred from an edge — r25, and r24 got this wrong.** r24
    // ticked whenever `checked` went false → true, which is not the same question as *did this
    // just turn on*. Opening the settings manager over another app composes its rows before the
    // live states have been read, so every setting that is already on arrives false and then
    // becomes true: three switches ticked on open for a transition nobody caused.
    //
    // A request is the honest trigger. Nothing arms a switch that is merely reading its initial
    // value, so that cannot happen; and `rememberSaveable` means an arm survives the trip to a
    // system settings screen and back, which is what `Display over other apps` does every time it
    // is pressed.
    var awaiting by rememberSaveable { mutableStateOf(false) }

    // ⚠ **One long-lived collector rather than an effect keyed on the values — r26, and r25's
    // shape could not have worked for a bulk action.** `LaunchedEffect(checked)` only restarts
    // when `checked` changes, so an arm that arrives *after* a switch is already on — which is
    // exactly what `All on`, `Unhide settings` and `Revert to default` produce — has nothing left
    // to fire on. Adding `armed` and `busy` to the keys is not the fix either: the effect would
    // then restart in the middle of the one-second hold every time either of them moved, and cut
    // the tick short.
    //
    // Keyed on `Unit` and fed by `rememberUpdatedState`, this sees every change to either value
    // and is interrupted by none of them.
    val liveChecked by rememberUpdatedState(checked)

    // Three routes into one flag, because they are the same event reaching the switch differently:
    // pressed here (below), pressed on a row that owns the press, or already in flight.
    val liveWanted by rememberUpdatedState(armed || busy)

    LaunchedEffect(Unit) {
        snapshotFlow { liveChecked to liveWanted }.collect { (isOn, wanted) ->
            if (wanted) awaiting = true

            // A request that ended up off is a request that failed, and there is nothing to
            // celebrate later. Unless one is still outstanding, in which case it is not over.
            if (!isOn && !wanted) awaiting = false

            if (isOn && awaiting) {
                awaiting = false

                ticking = true

                delay(SWITCH_TICK_HOLD_MILLIS)

                ticking = false
            }
        }
    }
"""

if check(start != -1 and end != -1 and start < end, "toggles: the watch block was not found"):
    toggles = toggles[:start] + WATCH_NEW + toggles[end + len(WATCH_OLD_END):]

for added, anchor in (
    ("import androidx.compose.runtime.rememberUpdatedState\n", "import androidx.compose.runtime.saveable.rememberSaveable\n"),
    ("import androidx.compose.runtime.snapshotFlow\n", "import androidx.compose.runtime.setValue\n"),
):
    symbol = added.rsplit(".", 1)[1].strip()

    if check(added not in toggles, f"toggles: {symbol} is already imported"):
        toggles = replace_once(toggles, anchor, anchor + added, f"toggles: {symbol} import")

body = code(toggles)

check(body.count("LaunchedEffect(") == 1, "toggles: the three keyed effects should be one collector")

check(body.count("snapshotFlow {") == 1, "toggles: expected one snapshotFlow")

check(body.count("rememberUpdatedState(") == 2, "toggles: both watched values should be kept live")

check("LaunchedEffect(Unit)" in body, "toggles: the collector must not be keyed on the values")

check(body.count("awaiting = true") == 2, "toggles: the collector and the press should arm it")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 2. AndroidSettingsManagerDialog.kt — the dialog arms what a bulk button is about to move.
# ─────────────────────────────────────────────────────────────────────────────────────────────

manager = MANAGER.read_text(encoding="utf-8")

manager = replace_once(
    manager,
    """            val usableTargets = drawnRows.filter(usableOf)
""",
    """            val usableTargets = drawnRows.filter(usableOf)

            // ⚠ **What a bulk button is about to move — r26.** `All on`, `All off`, `Hide` /
            // `Unhide settings` and `Revert to default` change rows without touching any row's own
            // press, so before r26 only Shizuku ticked — and only because its `starting` flag
            // armed it by accident. This is the deliberate version.
            //
            // ⚠ **Every row that is currently *off*, not every row that will end up on.** The
            // second is a guess made before the states have been re-read; the first is a fact. A
            // row that stays off never ticks anyway, because a switch ticks only when it is armed
            // *and* becomes checked — so arming the wider set is both simpler and race-free.
            var bulkArmed by remember { mutableStateOf(emptySet<ManualRevertTarget>()) }

            val armBulk = {
                bulkArmed = drawnRows.filterNot(states::isEnabled).toSet()
            }

            // ⚠ **Two ways in, on purpose.** Every one of these buttons should raise `busy`, and
            // if they all do then this effect alone would be enough; each button also arms
            // directly, because belt-and-braces here is cheaper than another round spent finding
            // out that one of them does not.
            //
            // Cleared a beat after the work ends rather than immediately: the switches latch the
            // arm into their own state, so this only has to stay up long enough to be seen, and
            // leaving it up for ever would make a later unrelated turn-on tick.
            LaunchedEffect(busy) {
                if (busy) {
                    armBulk()

                    return@LaunchedEffect
                }

                if (bulkArmed.isEmpty()) return@LaunchedEffect

                delay(BULK_ARM_GRACE_MILLIS)

                bulkArmed = emptySet()
            }
""",
    "manager: bulk arm",
)

manager = replace_once(
    manager,
    """                onAllOn = { onSetAll(true, usableTargets) },
                onAllOff = { onSetAll(false, usableTargets) },""",
    """                onAllOn = {
                    armBulk()

                    onSetAll(true, usableTargets)
                },
                onAllOff = {
                    armBulk()

                    onSetAll(false, usableTargets)
                },""",
    "manager: pill arming",
)

manager = replace_once(
    manager,
    """                    pending = anythingHidden,
                    onClick = if (anythingHidden) onUnhideSettings else onHideSettings,
                )""",
    """                    pending = anythingHidden,
                    onClick = {
                        armBulk()

                        if (anythingHidden) onUnhideSettings() else onHideSettings()
                    },
                )""",
    "manager: hide button arming",
)

manager = replace_once(
    manager,
    """                    label = stringResource(R.string.revert_to_default),
                    onClick = onRevertToDefault,""",
    """                    label = stringResource(R.string.revert_to_default),
                    onClick = {
                        armBulk()

                        onRevertToDefault()
                    },""",
    "manager: revert button arming",
)

manager = replace_once(
    manager,
    """                    usable = usableOf(target),""",
    """                    usable = usableOf(target),
                    // r26: this row was off when a bulk button was pressed, so if it comes on it
                    // has something to say about it.
                    bulkArmed = target in bulkArmed,""",
    "manager: row bulk arm",
)

manager = replace_once(
    manager,
    """    starting: Boolean = false,
    failed: Boolean = false,""",
    """    starting: Boolean = false,
    /** A bulk button was pressed while this row was off — see the dialog's `bulkArmed`. */
    bulkArmed: Boolean = false,
    failed: Boolean = false,""",
    "manager: TargetRow parameter",
)

manager = replace_once(
    manager,
    """                // r25: the press this switch never heard, because the row took it.
                armed = requestedOn,""",
    """                // r25: the press this switch never heard, because the row took it.
                // r26: or the bulk button that moved this row without pressing it at all.
                armed = requestedOn || bulkArmed,""",
    "manager: switch arming",
)

manager = replace_once(
    manager,
    """/** The hairline before the contributor's name. */""" if False else """private val PILL_HEIGHT = 28.dp""",
    """/**
 * How long a bulk arm stays up after the work ends.
 *
 * Long enough for the state poll that follows a bulk action to land, short enough that it is over
 * before anybody presses anything else. The switches latch the arm, so this is a window rather than
 * a flag.
 */
private const val BULK_ARM_GRACE_MILLIS = 2500L

private val PILL_HEIGHT = 28.dp""",
    "manager: BULK_ARM_GRACE_MILLIS",
)

# `LaunchedEffect` is already here; `delay` is not — the manager had no reason to suspend before.
check(
    "import androidx.compose.runtime.LaunchedEffect\n" in manager,
    "manager: LaunchedEffect is not imported and this script expected it to be",
)

DELAY = "import kotlinx.coroutines.delay\n"

if check(DELAY not in manager, "manager: delay is already imported"):
    manager = replace_once(
        manager,
        "import androidx.compose.runtime.mutableStateOf\n",
        "import androidx.compose.runtime.mutableStateOf\n" + DELAY,
        "manager: delay import",
    )

body = code(manager)

check(body.count("armBulk()") == 5, "manager: expected the effect and four button call sites")

check(body.count("bulkArmed") == 8, "manager: unexpected number of bulk-arm references")

check("armed = requestedOn || bulkArmed," in body, "manager: the switch should take both arms")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

TOGGLES.write_text(toggles, encoding="utf-8")

MANAGER.write_text(manager, encoding="utf-8")

for path in (TOGGLES, MANAGER):
    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
