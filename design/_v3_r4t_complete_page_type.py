#!/usr/bin/env python3
"""v3-r4t — the closing page is set one step larger throughout.

    "increase the font size in setup is now almost complete page"

Every level moves up one Material step, so the page keeps its own hierarchy rather than flattening
into one size:

* the four points and their sub-points: `bodyMedium` (14sp) → `bodyLarge` (16sp);
* the parenthesised aside under 2.3 and the signature: `bodySmall` (12sp) → `bodyMedium` (14sp);
* the title: `headlineSmall` (24sp) → `headlineMedium` (28sp).

⚠ **Nothing is given a hard `sp`.** Every one of these is a named style, so the page still follows
the user's own font-size setting and still matches the rest of the app; a literal size here would
be the one page in IMD that ignored both.

The body already scrolls, so a longer page is a longer scroll and nothing is pushed off it. The
footer is pinned and unchanged apart from the signature's size.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

EDITS: list[tuple[str, str]] = [
    (
        """                text = stringResource(R.string.setup_done_title),
                style = MaterialTheme.typography.headlineSmall,""",
        """                text = stringResource(R.string.setup_done_title),
                // r4t: one step up, with the rest of the page.
                style = MaterialTheme.typography.headlineMedium,""",
    ),
    (
        """/** One of the four numbered points. */
@Composable
private fun Point(text: String) {
    Text(
        modifier = Modifier.padding(top = 12.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
    )
}""",
        """/** One of the four numbered points. */
@Composable
private fun Point(text: String) {
    Text(
        modifier = Modifier.padding(top = 12.dp),
        text = text,
        // ⚠ **A named style one step up, not a literal size** — r4t. This page is the last thing
        // setup shows and the author found it small; every level moved together so it keeps its
        // hierarchy, and staying on the type scale is what keeps it following the user's own
        // font-size setting.
        style = MaterialTheme.typography.bodyLarge,
    )
}""",
    ),
    (
        """private fun SubPoint(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 6.dp),
        text = text,
        style = MaterialTheme.typography.bodyMedium,
    )
}""",
        """private fun SubPoint(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 6.dp),
        text = text,
        style = MaterialTheme.typography.bodyLarge,
    )
}""",
    ),
    (
        """private fun SubNote(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 2.dp),
        text = text,
        style = MaterialTheme.typography.bodySmall,""",
        """private fun SubNote(text: String) {
    Text(
        modifier = Modifier.padding(start = 20.dp, top = 2.dp),
        text = text,
        // Still a step below the item it belongs to, which is what makes it an aside.
        style = MaterialTheme.typography.bodyMedium,""",
    ),
    (
        """                text = stringResource(R.string.setup_done_signature),
                style = MaterialTheme.typography.bodySmall,""",
        """                text = stringResource(R.string.setup_done_signature),
                style = MaterialTheme.typography.bodyMedium,""",
    ),
]

AFTER = [
    ("typography.headlineMedium", 1),
    ("typography.bodyLarge", 2),
    ("typography.bodyMedium", 2),
    # Nothing on this page is left at the old sizes.
    ("typography.bodySmall", 0),
    ("typography.headlineSmall", 0),
    # And nothing was given a hard size on the way.
    (".sp", 0),
]


def main() -> int:
    path = ROOT / PAGE

    if not path.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {PAGE}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        text = text.replace(old, new, 1)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(f"REFUSED: {PAGE}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {PAGE}  :: every level one step larger, all on the type scale")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
