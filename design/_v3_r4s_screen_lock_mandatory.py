#!/usr/bin/env python3
"""v3-r4s — the screen-lock trigger is required for auto unhide, as the failsafe.

    "make screen lock a mandatory trigger to be enabled for Auto unhide service toggle, that we
     can use as a failsafe"

## ⚠ It replaces `anyTrigger` in [satisfied] rather than being added beside it

`anyTrigger` says *some* trigger can end a session — swipe, screen lock or idle, any one of them.
Requiring screen lock specifically makes that term redundant, since screen lock is one of the
three: `onScreenLock` implies `anyTrigger`. Adding `&& onScreenLock` next to it would leave two
terms where one is now unreachable, and an unreachable term is where a later reader gets the rule
wrong.

`anyTrigger` itself is **kept**: the page reads it to say which requirement is missing, and its
meaning has not changed.

## ⚠ Switching auto unhide on ticks the trigger, exactly as the tile condition already does

`screenLockAfterTile` is the same shape and the same reasoning: a control whose promise depends on
the screen-lock backup ticks it rather than refusing until the user finds it themselves. So
`updateAutoUnhideEnabled(true)` writes the trigger on with it. Switching auto unhide **off**
leaves the trigger alone - it is a statement about the feature, not about a trigger the user may
want for its own sake.

## ⚠ What happens if he unticks screen lock afterwards, and why nothing new is drawn

The master switch reads off, and the stored answers are left exactly where he put them. That is
not a new behaviour invented here: it is what `AutoUnhideRequirements` already does for every
unsatisfied term, and its KDoc says so. A refusal pop-up would be a second way of saying the same
thing, and one he has not seen a template of.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/AutoUnhide.kt"

VM = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

EDITS: list[tuple[str, str, str]] = [
    (
        MODEL,
        """    /** Whether auto unhide may be switched on right now. */
    val satisfied: Boolean
        get() = anyTrigger &&""",
        """    /**
     * Whether auto unhide may be switched on right now.
     *
     * ⚠ **[onScreenLock] rather than [anyTrigger], and it is the author's failsafe.** Screen lock
     * is the one trigger that needs no permission, cannot be refused by a device, and fires on a
     * session nobody named an app for — so it is the backstop under the other two rather than an
     * alternative to them, and auto unhide is not allowed on without it.
     *
     * It *replaces* the older term instead of joining it: screen lock is one of the three
     * `anyTrigger` counts, so requiring it makes that test unreachable, and an unreachable term
     * beside a live one is where the rule gets misread later. `anyTrigger` itself stays — the
     * page uses it to say what is missing.
     */
    val satisfied: Boolean
        get() = onScreenLock &&""",
    ),
    (
        VM,
        """    fun updateAutoUnhideEnabled(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideEnabled(enabled = enabled)
        }
    }""",
        """    /**
     * The master switch, and the trigger it cannot run without.
     *
     * ⚠ **Switching auto unhide on ticks the screen-lock trigger**, the author's failsafe — the
     * same shape as [screenLockAfterTile], and for the same reason: a control whose promise rests
     * on that backup ticks it rather than refusing until the user goes and finds it.
     *
     * Only ever on. Switching auto unhide *off* says nothing about a trigger the user may want
     * for its own sake, so the stored answer is left where they put it.
     */
    fun updateAutoUnhideEnabled(enabled: Boolean) {
        viewModelScope.launch {
            userDataRepository.updateAutoUnhideEnabled(enabled = enabled)

            if (!enabled) return@launch

            val userData = userDataRepository.userData.first()

            if (userData.autoUnhideOnScreenLock) return@launch

            userDataRepository.updateAutoUnhideTriggers(
                onSwipe = userData.autoUnhideOnSwipe,
                onScreenLock = true,
                onIdle = userData.autoUnhideOnIdle,
            )
        }
    }""",
    ),
]

AFTER = [
    (MODEL, "get() = onScreenLock &&", 1),
    (MODEL, "get() = anyTrigger &&", 0),
    # anyTrigger survives: its declaration and the KDoc reference in satisfied.
    (MODEL, "val anyTrigger: Boolean get()", 1),
    (VM, "onScreenLock = true,", 1),
    (VM, "if (!enabled) return@launch", 1),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # `first()` is what the new branch reads user data with; the file already uses it, and this
    # is what says so rather than assuming it.
    if "import kotlinx.coroutines.flow.first" not in staged[VM]:
        print(f"REFUSED: {VM}\n  'kotlinx.coroutines.flow.first' is not imported")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {MODEL}  :: screen lock is required, not merely one of three")
    print(f"  ok        {VM}  :: switching auto unhide on ticks it")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
