#!/usr/bin/env python3
"""
r3 — a memory sweep reports a failed overlay restore, now that the per-app button is gone.

The overlay step is deliberately allowed to fail without failing the rest of a profile, so its
outcome is reported by the caller or by nobody. Four routes already ask:
`AutoUnhideWatcher.revertOneProfile`, `AutoRevertRunner`'s memory branch, `AutoHideRunner`'s
per-app revert — and, until this build, `RevertSettingsBroadcastReceiver`, the per-app
notification's own button.

⚠ **That receiver is deleted by `_v3_generic_revert_notification.py`**, and with it the only
report on the sweep route. `SettingsHiddenRunner.unhide`'s memory branch calls
`revertAllMemoryUseCase()` and then says `IMD: Settings restored from memory` whatever
happened to overlay access. So a device that came out of a memory unhide without Display over
other apps back would have been told, in so many words, that everything was restored.

The gap was there before this round on two other routes through the same branch — the
Favourites `Unhide` button and a framework change, both of which reach it through
`flushPendingReverts` — so this closes three at once rather than replacing one.

⚠ **Asked only when the sweep is the whole story**, which is the same `!deviceWide` test the
toast already uses. When the device-wide revert runs too it reports for itself, inside
`RevertToDefaultRunner`, and two announcements for one press read as two things happening.

⚠ **`OverlayRestoreRunner` is in the same package**, so no import is needed, and it injects
nothing that leads back here — no Dagger cycle. Its constructor takes the context, two use
cases, the work tracker and the notification wrapper.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RUNNER = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
          "SettingsHiddenRunner.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (RUNNER, [
        (
            """    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val autoHideRunner: AutoHideRunner,
""",
            """    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val autoHideRunner: AutoHideRunner,
    private val overlayRestoreRunner: OverlayRestoreRunner,
""",
            1,
        ),
        (
            """            // Only when this is the whole story. Otherwise the revert below says its own
            // piece, and two toasts in a row for one press reads as two things happening.
            // Device-wide, with no app named: this sweep settles every outstanding per-app
            // record at once, so naming one of them would be picking a winner. The per-app
            // sentence belongs to the routes that revert exactly one app.
            if (!deviceWide) context.showRestoredToast(fromMemory = true)
""",
            """            // Only when this is the whole story. Otherwise the revert below says its own
            // piece, and two toasts in a row for one press reads as two things happening.
            // Device-wide, with no app named: this sweep settles every outstanding per-app
            // record at once, so naming one of them would be picking a winner. The per-app
            // sentence belongs to the routes that revert exactly one app.
            //
            // ⚠ **The overlay step's outcome is reported here or nowhere on this route.** It
            // is allowed to fail without failing the rest of a profile, and until r3 the only
            // caller that asked after a sweep was the per-app notification's own receiver,
            // which r3 deleted. Without this a sweep that could not put Display over other
            // apps back said "restored from memory" and nothing else — and that was already
            // true of the Favourites Unhide button and a framework change, which reach this
            // same branch through flushPendingReverts.
            //
            // Nothing is said when the report fires: the failure raises a notification of its
            // own and the completion sentence would be untrue over it. Same shape as
            // AutoRevertRunner's memory branch, deliberately.
            if (!deviceWide && !overlayRestoreRunner.reportIfFailed()) {
                context.showRestoredToast(fromMemory = true)
            }
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

    # The receiver this replaces must actually be gone, or the report would fire twice for one
    # press on the routes that still had it.
    gone = ROOT / ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
                   "RevertSettingsBroadcastReceiver.kt")

    if gone.exists():
        problems.append(f"{gone.relative_to(ROOT)}: still present — run the removal script first")

    runner = staged.get(ROOT / RUNNER, "")

    # One report on this route, not two, and it must sit on the `!deviceWide` test rather than
    # beside it — the device-wide branch below reports for itself.
    if runner.count("overlayRestoreRunner.reportIfFailed()") != 1:
        problems.append(f"{RUNNER}: expected exactly one overlay report on the sweep route")

    if runner.count("private val overlayRestoreRunner: OverlayRestoreRunner,") != 1:
        problems.append(f"{RUNNER}: the runner is not injected exactly once")

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
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

    print("ok - a memory sweep now reports a failed overlay restore")

    return 0


if __name__ == "__main__":
    sys.exit(main())
