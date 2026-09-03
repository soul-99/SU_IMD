#!/usr/bin/env python3
"""v3-r4n — IMD+'s spinner stops saying "Starting Shizuku service" while Shizuku is stopping.

The author's report, with logs:

    "i deliberately put wrong shizuku start intent to check IMD+, settings to hide included
     shizuku but service was already on, so why did imd+ start shows spinner for starting
     shizuku if it is already on ... only revert should be a failure (which it was but why the
     loading spinner for starting shizuku)"

**Nothing started.** The eight seconds was `StopShizukuServiceUseCase.awaitStopped()` running
its whole budget — `serviceWaitMillis / 500` polls, 16 x 500 ms on Thedjchi — because
`ShizukuForkDefaults.stopActionFor()` derives the stop action textually from the start action,
so a deliberately wrong start intent poisons the stop broadcast too. The tracker was correctly
reporting `OverlayStart.StopShizuku`, whose string is "Attempting to stop shizuku using stop
intent".

`AutoHideActivity` collected that value and then threw it away:

    } else if (overlayStart != null) {
        ShizukuStartingDialog(reason = null)
    }

`reason = null` maps to `R.string.shizuku_starting` — "Starting Shizuku service" — so IMD+'s
window said the opposite of what was happening.

⚠ **The comment that justified the null is now wrong, and is replaced rather than left.** It
argued that a run can wait on Shizuku twice and the user experiences one wait. That reasoning
predates `StopShizuku` and `StartShizuku` joining `OverlayStart`: the reasons the tracker can
now report are not all starts, so the one word on screen can be the opposite of the truth
rather than merely vaguer than it. `AppsScreen` and `FavouriteAppsScreen` have always passed
the value through; only this window did not.

The same argument applies to the `reason` parameter's own KDoc, which names IMD+ as the caller
that passes null. Both are corrected here, because a stale comment naming a caller that no
longer behaves that way is how the next round re-introduces the bug.

⚠ **Interim.** Spec item 7's stop-intent redesign removes the stop wait entirely, at which
point `OverlayStart.StopShizuku` stops being reachable from a launch. This is still worth
doing: the label is wrong today, and the tracker keeps the reason for every other route.

Asserts every anchor matches exactly once and that no `reason = null` call site survives.
Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/autohide/AutoHideActivity.kt"
DIALOG = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/ShizukuStartingDialog.kt"

OLD_CALL = """                } else if (overlayStart != null) {
                    // The same spinner a shortcut launch shows, but with no reason named. A
                    // run can wait on Shizuku twice - to close the app, and again for the
                    // hide's own overlay step - and from where the user is standing that is
                    // one wait, so it says one thing: Shizuku is starting.
                    ShizukuStartingDialog(reason = null)
                }"""

NEW_CALL = """                } else if (overlayStart != null) {
                    // ⚠ **The reason is passed through, and used to be discarded here.** This
                    // window collected `overlayStart` and then called the dialog with null,
                    // which says "Starting Shizuku service" whatever the wait is actually
                    // for - so a run held up *stopping* Shizuku told the user the opposite.
                    //
                    // The old argument for null was that IMD+ can wait on Shizuku twice and
                    // the user experiences one wait. That was written when every reason was a
                    // start; `OverlayStart` has carried StopShizuku and StartShizuku since,
                    // and a vaguer word is not the same thing as a wrong one. Every other
                    // surface - AppsScreen, FavouriteAppsScreen - has always passed it.
                    ShizukuStartingDialog(reason = overlayStart)
                }"""

OLD_KDOC = """    /**
     * What the wait is for, or null to say only that Shizuku is starting.
     *
     * Null is what Auto-hide settings (IMD+) uses. A run can wait on Shizuku twice - once to
     * close the app, once for the hide's own overlay step - and naming either of them would be
     * describing one half of a wait the user experiences as one thing.
     */
    reason: OverlayStart?,"""

NEW_KDOC = """    /**
     * What the wait is for, or null to say only that Shizuku is starting.
     *
     * ⚠ **No caller passes null any more.** IMD+ used to, on the argument that a run can wait
     * on Shizuku twice and the user experiences one wait — but that predates StopShizuku and
     * StartShizuku joining [OverlayStart], and a null during a stop names a start that is not
     * happening. The branch is kept for a reasonless wait, not for a caller that has one and
     * declines to say it.
     */
    reason: OverlayStart?,"""


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in (
        (ACTIVITY, "the IMD+ spinner call", OLD_CALL, NEW_CALL),
        (DIALOG, "the reason parameter's KDoc", OLD_KDOC, NEW_KDOC),
    ):
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = path.read_text(encoding="utf-8")

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {rel} already carries {name} — has this run before?")
            return 1

        staged[path] = text.replace(old, new, 1)

    # ⚠ **Spelled as it can only appear in a call, not as a bare word** — the comment trap.
    # Both replacement comments above talk *about* passing null, so a bare "null" check would
    # match this script's own prose. `reason = null` is an argument and nothing else.
    for path, text in staged.items():
        if "ShizukuStartingDialog(reason = null)" in text:
            print(f"REFUSED: {path.name} still calls the dialog with reason = null")
            return 1

    # `overlayStart` must still be collected above the call site, or the new argument would
    # not compile — the value is a local, and this is the one thing the sandbox cannot check
    # by building.
    activity = staged[ROOT / ACTIVITY]

    collected = activity.index("val overlayStart by viewModel.overlayStart")
    used = activity.index("ShizukuStartingDialog(reason = overlayStart)")

    if not collected < used:
        print("REFUSED: overlayStart is used before it is collected")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {ACTIVITY}  :: reason = overlayStart")
    print(f"  ok        {DIALOG}  :: the KDoc no longer names IMD+ as the null caller")
    print("\nwrote 2 file(s), 2 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
