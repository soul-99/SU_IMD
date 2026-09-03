#!/usr/bin/env python3
"""
r23a — two faults in r23's own restructuring of `Dialog.kt`, found by reading it back.

  1. **The compact branch reads the capped branch's value.** r23 moved each branch's
     `rememberFrostedWindow` call out of its `Dialog` lambda, giving the compact branch its own
     `compactFrost` — but only the *call* was renamed. The `Surface` under it still says
     `frost.colour(...)` and `frost.content`, and `frost` is now declared eighty lines *below*,
     after the `if (compact) { … return }` block. Kotlin will not have that: a local read before
     its declaration is a build error, and `tools/check_local_scope.py` cannot see it because both
     names live in the same function.

     The lesson for the script that made it: renaming a value means finding every read of it, and
     a replacement anchored on the declaration proves nothing about the uses. r20b made exactly
     this mistake with `frostedBackdrop` — checking the file that *declared* the name and not the
     file that passed it — and r20d wrote the fix. The check below is that check applied within a
     file rather than across the repo: after the edit, no line between `if (compact)` and its
     `return` may say the bare `frost.`.

  2. **`FrostedWindowEffect(frost)` landed between a comment and the thing it explains.** The
     eleven-line note beginning *"The box is what centres it"* is about the `Box`, and there is now
     a call between them. Harmless to the compiler and misleading to the next reader, which in this
     file is the more expensive of the two.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

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


dialog = DIALOG.read_text(encoding="utf-8")

# ── 1. the compact branch reads its own frost ────────────────────────────────────────────────
dialog = replace_once(
    dialog,
    """            Surface(
                modifier = modifier,
                shape = shape,
                color = frost.colour(containerColor),
                contentColor = frost.content,
                tonalElevation = tonalElevation,
                content = content,
            )""",
    """            Surface(
                modifier = modifier,
                shape = shape,
                color = compactFrost.colour(containerColor),
                contentColor = compactFrost.content,
                tonalElevation = tonalElevation,
                content = content,
            )""",
    "dialog: compact Surface frost reads",
)

# ── 2. the effect goes after the note that belongs to the Box ────────────────────────────────
dialog = replace_once(
    dialog,
    """    ) {
        FrostedWindowEffect(frost)
        // The box is what centres it.""",
    """    ) {
        // The box is what centres it.""",
    "dialog: orphaned effect call",
)

dialog = replace_once(
    dialog,
    """        // being fixed.
        if (frost.frosted) {""",
    """        // being fixed.
        FrostedWindowEffect(frost)

        if (frost.frosted) {""",
    "dialog: effect call placement",
)

# ⚠ **The check r23 should have made.** Not "the declaration was renamed" but "nothing in this
# branch reads the other branch's value". Sliced between the branch's own `if` and its `return`,
# because `frost.` is correct everywhere below that and wrong everywhere inside it.
start = dialog.find("    if (compact) {")

end = dialog.find("\n        return\n    }\n", start)

if check(start != -1 and end != -1, "dialog: the compact branch could not be sliced"):
    branch = dialog[start:end]

    for read in ("frost.colour", "frost.content", "frost.frosted"):
        check(
            f" {read}" not in branch and f"({read}" not in branch,
            f"dialog: the compact branch still reads the capped branch's {read}",
        )

    check(
        branch.count("compactFrost") == 4,
        f"dialog: expected 4 uses of compactFrost in the compact branch, found {branch.count('compactFrost')}",
    )

check(
    dialog.count("FrostedWindowEffect(") == 3,
    "dialog: expected the declaration and one call per windowed branch",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

DIALOG.write_text(dialog, encoding="utf-8")

print(f"wrote {DIALOG.relative_to(ROOT).as_posix()}")

print("ok")
