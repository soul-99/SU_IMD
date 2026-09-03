#!/usr/bin/env python3
"""
r30l — the in-app changelog link, which r30c broke without anyone noticing.

The author asked whether the app's **Logics** card still lands on SUIMD.md's logics section. It
does: `#2-imd-app-logics` is exactly what GitHub generates for `## 2. IMD app logics`, and the new
`tools/check_doc_links.py` now proves it on every run rather than leaving it to be believed.

⚠ **Checking that turned up a different one that was broken.** `ProjectLinks.CHANGELOG` pointed at
`https://github.com/soul-99/SU_IMD#added-in-this-fork` — the README's *Added in this fork* heading,
which **r30c deleted** when the changelog moved out into `CHANGELOG.md`. GitHub does not error on
an anchor it cannot find; it serves the page scrolled to the top. So the link had quietly become
"open the repository", and nothing said so.

It is repointed at the file that now holds what it was always describing.

⚠ **Nothing calls it today.** The version row opens `RELEASES`; `CHANGELOG` is declared and unused.
That is precisely why it was still wrong — an unused constant is never pressed, so a broken one
waits for whoever wires it up next. It is corrected rather than deleted because `CHANGELOG.md`
exists now and this is the right URL for it.

Computes both edits in memory, asserts, writes nothing if any assertion fails. The link checker is
run afterwards, not by this script — a script that grades its own homework is not a check.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LINKS = ROOT / "common/src/main/kotlin/com/android/geto/common/ProjectLinks.kt"

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


source = LINKS.read_text(encoding="utf-8")

source = replace_once(
    source,
    """    /** The section the version line points at: what changed, per version. */
    const val CHANGELOG = "$REPOSITORY#added-in-this-fork\"""",
    """    /**
     * What changed, per version, written for whoever is reading it rather than for the build.
     *
     * ⚠ **A file, not an anchor, since r30.** This used to point at the README's
     * *Added in this fork* heading; r30 moved the changelog out into `CHANGELOG.md` and deleted
     * that heading, which turned this into a link that opened the repository — GitHub serves a
     * page it cannot find an anchor in scrolled to the top rather than erroring, so nothing said
     * so. `tools/check_doc_links.py` now fails on exactly this.
     *
     * ⚠ **Declared and not yet used.** The version row opens [RELEASES]. That is why it was
     * still wrong: a constant nobody presses is a constant nobody finds broken.
     */
    const val CHANGELOG = "$REPOSITORY/blob/main/CHANGELOG.md\"""",
    "the changelog link",
)

check(
    '"$REPOSITORY/blob/main/CHANGELOG.md"' in source,
    "the new changelog URL did not land",
)

check("added-in-this-fork" not in source, "the dead anchor survived")

check(
    (ROOT / "CHANGELOG.md").exists(),
    "CHANGELOG.md does not exist, and the app now links to it",
)

# ⚠ The one the author actually asked about, asserted here too rather than only in the checker:
# it is the link this round exists because of.
check(
    'const val LOGICS = "$REPOSITORY/blob/main/SUIMD.md#2-imd-app-logics"' in source,
    "the logics link moved",
)

check(
    "\n## 2. IMD app logics\n" in (ROOT / "SUIMD.md").read_text(encoding="utf-8"),
    "SUIMD.md's logics heading has been renamed — the app's Logics card no longer lands on it",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

LINKS.write_text(source, encoding="utf-8")

print("CHANGELOG  README#added-in-this-fork  ->  CHANGELOG.md")

print("LOGICS     SUIMD.md#2-imd-app-logics  (unchanged, and now checked)")

print("ok")
