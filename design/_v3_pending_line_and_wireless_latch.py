#!/usr/bin/env python3
"""r4f — the red line names the action, and a wireless press during the wait counts as a yes.

Two instructions.

### 1. The red line in the settings manager

    "for the red line that shows up in settings manager when settings are currently hidden IMD
     is hiding.. one replace word 'revert' with 'you unhide settings, '"

    before   IMD hiding settings currently, any changes made here before revert will be
             undone after settings restoration
    after    IMD hiding settings currently, any changes made here before you unhide settings,
             will be undone after settings restoration

⚠ **One space, not two.** The replacement text ends in a comma and a space and the sentence
already had a space before `will`, so the literal substitution doubles it. Put to the author, who
chose the single space; the wording is his, untouched.

### 2. A wireless press during the wait counts as a yes

    "if wireless debugging was previously on then turn it on again but if user himself enabled
     wireless debugging during the wait then use keep that as a yes to turn on wireless
     debugging"

So the value is not the press-time reading alone, and not the latest reading either. It is
**either** — a one-way latch:

    turn wireless debugging on after a successful start
        if it was on when Shevery was pressed
        OR the user switched it on at any point during the wait

⚠ **One way only, and that is the whole design.** A user turning wireless debugging *off* during
the wait does not clear the latch, because Shevery itself is expected to switch that row off on
its way up and there is no way here to tell one from the other. The instruction only ever names
reasons to turn it **on**, and `do not manage wireless debugging toggle` covers the rest.

⚠ **This is not r4d's `noteWirelessChosen` restored.** That one replaced the remembered value in
both directions, which r4f's press-time rule had removed. This latches true and never false, so
the two answers the author has given - the press-time value and a mid-wait switch-on - are
combined rather than one overwriting the other.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/apps/src/main/res/values/strings.xml"
TRACKER = ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/"
           "SheveryStartTracker.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            """<string name="settings_manager_pending">IMD hiding settings currently, any changes made here before revert will be undone after settings restoration</string>""",
            """<string name="settings_manager_pending">IMD hiding settings currently, any changes made here before you unhide settings, will be undone after settings restoration</string>""",
            1,
        ),
    ]),

    (TRACKER, [
        (
            """    fun begin(job: Job, seconds: Int) {
        this.job = job

        _secondsLeft.value = seconds
    }
""",
            """    /**
     * Whether wireless debugging should be switched back on once the start comes up.
     *
     * ⚠ **A latch, and it only ever goes one way.** Two things set it: wireless debugging was
     * already on when Shevery was pressed, and the user switching it on at any point during the
     * wait — the author's *"if user himself enabled wireless debugging during the wait then keep
     * that as a yes"*. Nothing clears it, because Shevery is expected to switch that row off on
     * its way up and there is no way here to tell its write from a person's.
     */
    var wirelessWanted: Boolean = false
        private set

    fun begin(job: Job, seconds: Int, wirelessOn: Boolean) {
        this.job = job

        wirelessWanted = wirelessOn

        _secondsLeft.value = seconds
    }

    /** The user switched wireless debugging on mid-wait, which is a yes however it started. */
    fun noteWirelessTurnedOn() {
        if (waiting) wirelessWanted = true
    }
""",
            1,
        ),
        (
            """    fun clear() {
        job = null

        _secondsLeft.value = null
    }
""",
            """    fun clear() {
        job = null

        wirelessWanted = false

        _secondsLeft.value = null
    }
""",
            1,
        ),
    ]),

    (MANAGER_VM, [
        (
            """        sheveryStartTracker.begin(job = job, seconds = SHEVERY_WAIT_SECONDS)
""",
            """        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessOn = wirelessBefore,
        )
""",
            1,
        ),
        (
            """                if (came && wirelessBefore) {
""",
            """                if (came && sheveryStartTracker.wirelessWanted) {
""",
            1,
        ),
        (
            """        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
""",
            """        // ⚠ **Switching wireless debugging on mid-wait is a yes.** The latch it sets is what
        // decides whether the row goes back on once Shevery comes up, and it combines with the
        // reading taken when Shevery was pressed rather than replacing it. Only the on
        // direction: Shevery switches that row off itself on the way up, and nothing here can
        // tell its write from a person's.
        if (target == ManualRevertTarget.WirelessDebugging && enabled) {
            sheveryStartTracker.noteWirelessTurnedOn()
        }

        viewModelScope.launch {
            // Before the write, and only when a revert is already pending — the author's
            // rule, and what makes the dialog's red line true. See RecordManualChangeUseCase.
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    strings = staged.get(ROOT / STRINGS, "")
    tracker = staged.get(ROOT / TRACKER, "")
    view_model = staged.get(ROOT / MANAGER_VM, "")

    # The author's wording, and no doubled space anywhere in it.
    if "before you unhide settings, will be undone" not in strings:
        problems.append(f"{STRINGS}: the replacement sentence is not what was asked for")

    if "settings,  will" in strings:
        problems.append(f"{STRINGS}: the doubled space survived")

    # ⚠ Asserted against code, never the prose around it.
    for rel, text, token, expected in (
        (TRACKER, tracker, "wirelessWanted = true", 1),
        (TRACKER, tracker, "wirelessWanted = false", 1),
        (TRACKER, tracker, "wirelessWanted = wirelessOn", 1),
        (MANAGER_VM, view_model, "noteWirelessTurnedOn()", 1),
        (MANAGER_VM, view_model, "sheveryStartTracker.wirelessWanted", 1),
        (MANAGER_VM, view_model, "wirelessOn = wirelessBefore", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # One way only: nothing may set the latch false except the clear at the end of a wait.
    if "wirelessWanted = false" in view_model:
        problems.append(f"{MANAGER_VM}: something outside the tracker clears the latch")

    if "if (waiting) wirelessWanted = true" not in tracker:
        problems.append(f"{TRACKER}: the latch is settable outside a wait")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and not path.name.endswith(".xml"):
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - the red line names the action, and a mid-wait switch-on is a yes")

    return 0


if __name__ == "__main__":
    sys.exit(main())
