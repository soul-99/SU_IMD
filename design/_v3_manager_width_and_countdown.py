#!/usr/bin/env python3
"""r4i — the manager stops filling a tablet, and the countdown moves under the row it explains.

Two instructions and a screenshot:

    "can we move these countdown lines below shizuku/shevery toggles"

    "on my bigger screen the settings manager window becomes too large - can we adjust it so
     that for large displays it shows dialog width that wide that hide settings and rev to def
     button's text dont wrap?"

### 1. Width

⚠ **The manager is the one dialog that passes `compact = true`**, which keeps
`usePlatformDefaultWidth` — and the platform's default is a *fraction of the display*. On a phone
that is the small centred card the flag exists for; on the author's tablet it is most of the
screen, with each row's label at the far left and its switch at the far right and nothing in
between. His screenshot is that.

The cap is [DIALOG_MAX_WIDTH], 460dp, which is the number every other dialog in the app already
uses. Measured against the request: `Revert to default` at `labelLarge` needs a 192dp button
(24dp + 18dp glyph + 8dp + 118dp label + 24dp), so the row of two plus its 10dp gap and the
column's 10dp padding either side wants **414dp**. 460 clears it with room for a longer label
later — translations are deferred, and `Revert to default` gets longer in most languages.

⚠ **`widthIn` before `fillMaxWidth`, and the order is the whole of it.** Constraints travel
outside-in: `widthIn(max = …)` narrows the incoming constraint and `fillMaxWidth()` then fills
*that*. The other way round, fill takes the platform's width first and the cap has nothing left
to narrow.

⚠ **`compact` stays true.** It is what keeps this a centred card rather than a page, on phones
included, and the author has not asked for that to change - only for the card to stop growing.

### 2. The countdown

Moved out of the header slot and under the Shizuku/Shevery row itself. It was written where it
was because it is "the most immediate thing on screen while it is counting"; under the row it
explains it is both immediate *and* attached to the switch that has gone dead, which is what the
author asked for.

⚠ **Drawn inside the row loop rather than after it**, so it stays with the service row wherever
that row sits — `rows(manageShizuku)` can drop the Shizuku row entirely, and a countdown pinned
to a fixed position would then explain a row that is not there.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")

# The countdown leaves the header.
HEADER_OLD = """            // The Shevery wait, in the same slot as the notes below it and above them all:
            // it is the most immediate thing on screen while it is counting, and it is the
            // explanation for the one row that has just gone dead.
            if (sheveryWait != null) {
                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = stringResource(R.string.shevery_wait_countdown, sheveryWait),
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.primary,
                )
            }

"""

HEADER_NEW = ""

# ...and arrives under the row it is about.
ROW_OLD = """                    onOpen = { onOpen(target) },
                )
            }
"""

ROW_NEW = """                    onOpen = { onOpen(target) },
                )

                // ⚠ **Under the row it explains, at the author's instruction**, rather than in
                // the header slot it used to share with the pending note. It is still the most
                // immediate thing on screen while it counts; it is now also attached to the
                // switch that has just gone dead, which is what it is about.
                //
                // Inside the loop rather than after it, so it follows the service row wherever
                // that row is drawn - `rows(manageShizuku)` can leave it out altogether, and a
                // countdown pinned below a fixed position would then explain a row that is not
                // on screen.
                if (isShizuku && sheveryWait != null) {
                    Text(
                        modifier = Modifier.padding(start = 4.dp, bottom = 6.dp),
                        text = stringResource(R.string.shevery_wait_countdown, sheveryWait),
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.primary,
                    )
                }
            }
"""

# The width cap.
WIDTH_OLD = """        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(10.dp),
        ) {
            // The app's own icon, as the launcher draws it."""

WIDTH_NEW = """        Column(
            modifier = Modifier
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
        ) {
            // The app's own icon, as the launcher draws it."""

CONSTANT_OLD = """private val PILL_HEIGHT = 28.dp
"""

CONSTANT_NEW = """/**
 * How wide the settings manager is allowed to get.
 *
 * The same 460dp every other dialog in the app is capped at, restated here because this one
 * keeps `usePlatformDefaultWidth` and so never reaches `DialogContainer`'s own cap. See the
 * `widthIn` call for why it is applied where it is.
 */
private val MANAGER_MAX_WIDTH = 460.dp

private val PILL_HEIGHT = 28.dp
"""

IMPORT_OLD = """import androidx.compose.foundation.layout.width
"""

IMPORT_NEW = """import androidx.compose.foundation.layout.width
import androidx.compose.foundation.layout.widthIn
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
        (HEADER_OLD, HEADER_NEW, 1),
        (ROW_OLD, ROW_NEW, 1),
        (WIDTH_OLD, WIDTH_NEW, 1),
        (CONSTANT_OLD, CONSTANT_NEW, 1),
        (IMPORT_OLD, IMPORT_NEW, 1),
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
        ("shevery_wait_countdown", 1),
        ("if (isShizuku && sheveryWait != null) {", 1),
        (".widthIn(max = MANAGER_MAX_WIDTH)", 1),
        ("private val MANAGER_MAX_WIDTH = 460.dp", 1),
        ("import androidx.compose.foundation.layout.widthIn", 1),
        # The cap must sit above the fill, or it caps nothing.
        (".widthIn(max = MANAGER_MAX_WIDTH)\n                .fillMaxWidth()", 1),
    ):
        if text.count(token) != expected:
            problems.append(f"expected {expected} of {token.splitlines()[0][:58]!r}, "
                            f"found {text.count(token)}")

    # ⚠ **Position, not presence.** The countdown must be inside the row loop, after the
    # TargetRow it follows and before the loop closes.
    loop = text.find("            drawnRows.forEach { target ->")
    row = text.find("                    onOpen = { onOpen(target) },")
    note = text.find("                if (isShizuku && sheveryWait != null) {")
    pill = text.find("            MasterPill(")

    if min(loop, row, note) < 0 or pill < 0:
        problems.append("cannot locate the loop, the row, the countdown or the pill")
    elif not pill < loop < row < note:
        problems.append("the countdown is not inside the row loop after its TargetRow")

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
    print("ok - capped at 460dp, and the countdown sits under the row it explains")

    return 0


if __name__ == "__main__":
    sys.exit(main())
