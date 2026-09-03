#!/usr/bin/env python3
"""r4i — the whole row is the target, not just the switch at the end of it.

The author:

    "for settings manager can we make clicking the toggle labels also to click toggle …
     i mean the whole toggle label + toggle width"

The row is a label at one edge and a switch at the other, and until now only the switch answered
a press. On the width this dialog is capped at that is a small target at the far right of a wide
gap; every settings list on Android takes the whole row.

### What it does

`TargetRow`'s outer `Row` gains one `clickable`, which does exactly what a press on the switch
would have done:

    usable    -> onSetEnabled(!enabled)
    unusable  -> onClickWhenUnusable(), the same explanation the wrapped switch gives

⚠ **The switch keeps its own handler.** A press that lands on it is handled there and never
reaches the row, which is Compose's ordinary innermost-first dispatch; the row's handler is for
the label and the space between. Two paths, one behaviour, because both call the same lambda —
there is no second decision here that could drift from the first.

⚠ **So does the open-link button, and so does the failure ⓘ.** Both sit inside the row with
clickables of their own, so tapping the link still opens Settings rather than flipping the
switch. That is the one thing this change could plausibly have broken, and it is the reason the
row's handler is added rather than the row being made to swallow everything.

⚠ **`enabled = usable || onClickWhenUnusable != null`.** A row that is neither usable nor able to
explain itself gets no ripple and no press, rather than a target that lights up and does nothing.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

OLD = """    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
"""

NEW = """    Row(
        modifier = modifier
            .fillMaxWidth()
            // ⚠ **The whole row, at the author's instruction** - label, switch and the gap
            // between them. On the width this dialog is capped at, a switch at the far right
            // is a small target at the end of a long reach, and every settings list on the
            // platform takes the row.
            //
            // The switch keeps its own handler and the open-link button and the failure ⓘ keep
            // theirs; a press that lands on any of them is handled there and never arrives
            // here, which is Compose's innermost-first dispatch. This is for everything else.
            //
            // It calls the same two lambdas the switch does rather than deciding anything of
            // its own, so the row and the switch cannot come to disagree about what a press
            // means.
            .clickable(enabled = usable || onClickWhenUnusable != null) {
                if (usable) onSetEnabled(!enabled) else onClickWhenUnusable?.invoke()
            }
            .padding(start = 4.dp, top = 2.dp, bottom = 2.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
"""


def main() -> int:
    path = ROOT / MANAGER

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    found = text.count(OLD)

    if found != 1:
        print("REFUSED, nothing written")
        print(f"  expected 1 of the TargetRow header, found {found}")

        return 1

    text = text.replace(OLD, NEW, 1)

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        (".clickable(enabled = usable || onClickWhenUnusable != null) {", 1),
        ("if (usable) onSetEnabled(!enabled) else onClickWhenUnusable?.invoke()", 1),
        # The switch's own two paths are untouched: one live, one wrapped.
        ("Switch(checked = enabled, colors = switchColors, onCheckedChange = onSetEnabled)", 1),
        ("modifier = Modifier.clickable(enabled = onClickWhenUnusable != null) {", 1),
        # And the link button still has its own, or a tap on it would toggle the row.
        ("IconButton(onClick = onOpen) {", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token[:58]!r}, found {text.count(token)}")

    # ⚠ **Position, not presence.** The row handler must sit inside TargetRow — the dialog's
    # own Column has a `padding(10.dp)` that would match a careless anchor.
    row_fun = text.find("private fun TargetRow(")
    handler = text.find("            .clickable(enabled = usable || onClickWhenUnusable != null) {")
    switch = text.find("        if (usable) {\n            Switch(checked = enabled")

    if min(row_fun, handler, switch) < 0:
        problems.append("cannot locate TargetRow, its new handler, or the switch below it")
    elif not row_fun < handler < switch:
        problems.append("the row handler is not inside TargetRow above its switch")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  wrote {MANAGER}")
    print("ok - the whole row takes the press, and the link button still takes its own")

    return 0


if __name__ == "__main__":
    sys.exit(main())
