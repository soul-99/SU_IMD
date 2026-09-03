#!/usr/bin/env python3
"""r4k — the manager joins the app's own dialog-width rule, and its buttons stop over-padding.

The author, with two screenshots a day apart:

    "on my bigger screen the settings manager window becomes too large"      (r4i)
    "in narrow screen can we stretch settings manager dialog if the screen can fit the hide
     settings and rev to def button"                                          (this one)

Two opposite complaints about one cause, and `DialogContainer` already names it. Its non-compact
branch carries this comment:

    usePlatformDefaultWidth is off for everything else. On a phone it was capping dialogs
    below the screen width; on a tablet it was letting them grow with the screen. Both are
    the wrong way round, so the width is decided here: fill what is available, up to
    maxWidth, centred in the window.

⚠ **The manager is the one dialog still on the old path.** It passes `compact = true`, which
keeps `usePlatformDefaultWidth` — so it is the one dialog that still gets both symptoms the rest
of the app was fixed for. It now passes `compact = false` and inherits the rule.

⚠ **The r4i `widthIn` comes out with it.** The container caps at the same 460dp; two caps on one
dialog is two places to change a number and one of them to forget.

⚠ **The animation this gains is the right one, not the one that stuttered.** That regression came
from putting `DialogEntrance` on a *platform-width* window, where the window already wraps the
card and the platform is animating it — two animations on one thing. On this path the window is
screen-sized and transparent, which is exactly what `DialogEntrance` exists for.

⚠ **What is superseded, and it should be said plainly.** `compact` was chosen for this dialog so
it would "stay a small card in the middle of the screen on every device, phones included". The
author has now asked for the opposite on a phone, so that reasoning is retired rather than
quietly contradicted.

### The buttons

Even filling a phone the two labels were marginal: at 411dp screen the card gets 379dp, and
`Revert to default` in a pair of buttons at `ButtonDefaults.ContentPadding` wants about 373dp of
that with nothing to spare. They now use `ButtonDefaults.ButtonWithIconContentPadding`, which is
Material's own padding for a button with a leading icon — 16dp before the icon instead of 24 —
and saves 8dp a button.

⚠ **The right padding for what these buttons are**, not a squeeze to win an argument with a
label: every one of them has a glyph in front of its text, which is the case that padding exists
for.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

COMPACT_OLD = """        // The one dialog in the app that stays a small centred card on every screen, phones
        // included. It is opened from a tile or a shortcut over somebody else's app, and a
        // list of six switches that filled the display would read as having replaced that
        // app rather than as having been put in front of it.
        compact = true,
"""

COMPACT_NEW = """        // ⚠ **On the app's own width rule since r4k, and it used to be the exception.**
        // `compact` kept `usePlatformDefaultWidth`, which `DialogContainer` describes as
        // "capping dialogs below the screen width on a phone and letting them grow with the
        // screen on a tablet - both the wrong way round". This dialog was the last one still
        // getting both, and the author reported them a day apart: too wide on his tablet,
        // too narrow for its own buttons on his phone.
        //
        // The earlier reasoning - that it should stay a small centred card on every device,
        // because it opens over somebody else's app - is retired rather than contradicted in
        // silence. He has asked for the opposite on a phone.
        compact = false,
"""

WIDTH_OLD = """            modifier = Modifier
                // ⚠ **Before `fillMaxWidth`, and the order is the whole of it.** Constraints
                // travel outside-in: this narrows the incoming constraint and the fill below
                // then fills *that*. The other way round, fill takes the platform's width
                // first and there is nothing left to cap.
                //
                // Needed because this is the one dialog that keeps `usePlatformDefaultWidth`,
                // whose default is a fraction of the display - a small centred card on a
                // phone, and most of the screen on the author's tablet, with every row's
                // label at one edge and its switch at the other.
                //
                // The number is the app's own dialog cap. `Revert to default` needs a 192dp
                // button, so this row of two wants 414dp; 460 clears that and leaves room for
                // a longer label than English has.
                .widthIn(max = MANAGER_MAX_WIDTH)
                .fillMaxWidth()
                .padding(10.dp),
"""

WIDTH_NEW = """            modifier = Modifier
                // No cap here any more. r4i put one on because this dialog kept the platform
                // width; now that it is on `DialogContainer`'s own path the container caps it
                // at the same 460dp, and two caps on one dialog is two places to change a
                // number and one of them to forget.
                .fillMaxWidth()
                .padding(10.dp),
"""

CONSTANT_OLD = """/**
 * How wide the settings manager is allowed to get.
 *
 * The same 460dp every other dialog in the app is capped at, restated here because this one
 * keeps `usePlatformDefaultWidth` and so never reaches `DialogContainer`'s own cap. See the
 * `widthIn` call for why it is applied where it is.
 */
private val MANAGER_MAX_WIDTH = 460.dp

"""

IMPORT_OLD = """import androidx.compose.foundation.layout.widthIn
"""

PADDING_OLD = """        Row(
            modifier = Modifier.padding(ButtonDefaults.ContentPadding),
"""

PADDING_NEW = """        Row(
            // ⚠ **The icon variant, which is what these buttons are.** Material's plain
            // `ContentPadding` is 24dp on both sides and assumes text alone; every button
            // here has a glyph in front of its label, and the icon padding is 16dp before it.
            // The 8dp a button that saves is what lets `Revert to default` sit on one line on
            // a 411dp phone, where the pair had about 373dp of a 379dp card and nothing over.
            modifier = Modifier.padding(ButtonDefaults.ButtonWithIconContentPadding),
"""


def main() -> int:
    path = ROOT / MANAGER

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in (
        (COMPACT_OLD, COMPACT_NEW, 1),
        (WIDTH_OLD, WIDTH_NEW, 1),
        (CONSTANT_OLD, "", 1),
        (IMPORT_OLD, "", 1),
        (PADDING_OLD, PADDING_NEW, 1),
    ):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # ⚠ Asserted against code, never the prose around it.
    for token, expected in (
        ("compact = false,", 1),
        ("compact = true,", 0),
        # The cap and its import leave together, or one of them is dead.
        ("MANAGER_MAX_WIDTH", 0),
        ("widthIn", 0),
        ("ButtonDefaults.ButtonWithIconContentPadding", 1),
        ("ButtonDefaults.ContentPadding", 0),
        # ButtonDefaults is still used for the shape, so the import must stay.
        ("import androidx.compose.material3.ButtonDefaults", 1),
        ("ButtonDefaults.shape", 2),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token!r}, found {text.count(token)}")

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
    print("ok - the manager fills a phone, caps at 460 on a tablet, and its labels fit")

    return 0


if __name__ == "__main__":
    sys.exit(main())
