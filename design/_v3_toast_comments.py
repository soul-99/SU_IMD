#!/usr/bin/env python3
"""
v3-r2a — the four orphaned doc comments in RevertToasts.kt.

r2 deleted seven helpers from this file and left their KDoc behind, so the file opens with a
stack of `/** ... */` blocks describing functions that are not there. Harmless to the compiler
and confusing to read, and one of them is now actively wrong: "The two Auto-hide settings (IMD+)
runs announce themselves ... a revert kills the watched apps before it restores anything.
Without a word ... the second [reads] as the notification doing nothing" is the exact design the
author has just reversed.

Deletes only comment text. No declaration is touched, which `check_lost_declarations.py`
against the round's baseline confirms.

Computes the edit in memory, asserts each match count and that the file's declarations are
unchanged, and writes nothing if anything fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOASTS = ROOT / "common/src/main/kotlin/com/android/geto/common/RevertToasts.kt"

# Each of these describes helpers r2 removed. Verbatim, so a block that has drifted refuses
# rather than being matched loosely.
DROP = [
    """/**
 * The two reverts announce themselves, because from the outside they look identical — the
 * screen does not change, and the settings they touch are not on screen.
 *
 * Which one ran matters: one puts back what a single app switched off, the other puts the
 * whole device into the configured default. Saying which happened is the difference between
 * a user trusting the button and pressing it twice to see if it worked.
 *
 * There are six places these fire from — a tile, a notification, a shortcut, two buttons and
 * a dialog — several of which have no UI of their own to show a snackbar in. A toast is the
 * one thing that works from all of them.
 */
/**
 * The same two, for a revert nobody pressed a button for.
 *
 * Worded apart from the manual pair on purpose. A revert the user asked for needs only to
 * confirm it ran; one that happened because they came back to the app has to say why the
 * device just changed, or it reads as the app doing something at random.
 */
""",
    """/**
 * The one the Tasker integration adds: "Settings hidden", for the hide trigger.
 *
 * Hiding from a launch needs no toast - the app it hides for opens a beat later and is the
 * confirmation. Hiding from a macro opens nothing, so without a word the trigger looks like it
 * did nothing, which is the same reason the shortcut path grew its own feedback.
 */
/**
 * The two Auto-hide settings (IMD+) runs announce themselves, because both of them start with
 * something slow and invisible.
 *
 * A run kills the app the user has just tapped and may wait on Shizuku before anything appears;
 * a revert kills the watched apps before it restores anything. Without a word, the first reads
 * as the app crashing on launch and the second as the notification doing nothing.
 *
 * The revert's own confirmation still follows from the revert itself — this one says the work
 * has started, that one says what it was.
 */
""",
]

DECLARATION = re.compile(r"^(?:private )?fun Context\.(\w+)", re.M)


def main() -> int:
    problems: list[str] = []

    if not TOASTS.exists():
        print("REFUSED, nothing written")
        print(f"  {TOASTS} is missing")

        return 1

    original = TOASTS.read_text(encoding="utf-8")

    text = original

    for block in DROP:
        found = text.count(block)

        if found != 1:
            problems.append(f"{found} of the block starting {block.splitlines()[1][:60]!r}")

            continue

        text = text.replace(block, "", 1)

    before = DECLARATION.findall(original)
    after = DECLARATION.findall(text)

    if before != after:
        problems.append(f"declarations changed: {before} -> {after}")

    if "/**" not in text:
        problems.append("every doc comment is gone, which is not the edit")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    TOASTS.write_text(text, encoding="utf-8")

    print(f"ok — {len(DROP)} orphaned comment blocks removed, {len(after)} declarations intact")

    return 0


if __name__ == "__main__":
    sys.exit(main())
