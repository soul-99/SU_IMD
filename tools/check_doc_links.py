#!/usr/bin/env python3
"""Every link from the app into this repo's own documents actually lands somewhere.

`ProjectLinks.kt` holds the URLs the app opens - the Logics card, the version row, the Support
dialog. Three of them point *inside* a document in this repo, at a heading anchor. Nothing has
ever checked that the heading is still there.

⚠ **The failure is silent, which is why this exists.** GitHub does not error on an anchor it
cannot find; it serves the page scrolled to the top. So a renamed heading turns a link that says
"IMD app logics" into a link that opens a 1300-line file at its title, and the only way anyone
finds out is by pressing it. `ProjectLinks.LOGICS` says as much in its own KDoc - "rename the
section and this link lands at the top of the file instead, silently, which is the failure mode
worth knowing about rather than guarding against". This is the guard.

It caught one the day it was written: `CHANGELOG` pointed at `#added-in-this-fork`, a README
heading that r30c deleted when the changelog moved into `CHANGELOG.md`.

What it checks, for every `const val` in `ProjectLinks.kt`:

* a URL into this repo's tree names a file that exists;
* an anchor on it matches a real heading, by GitHub's own slug rules;
* a bare-repository URL with an anchor is read against `README.md`, which is what GitHub serves.

External hosts (the subreddit, Obtainium) are reported and not fetched - this runs offline, and a
checker that needs the network is a checker that gets skipped.

    python3 tools/check_doc_links.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LINKS = ROOT / "common/src/main/kotlin/com/android/geto/common/ProjectLinks.kt"

REPO_PREFIX = "https://github.com/soul-99/SU_IMD"


def anchors(document: Path) -> set[str]:
    """Every heading anchor GitHub would generate for this file.

    GitHub's rule: take the heading text, lowercase it, drop everything that is not a letter,
    digit, space, hyphen or underscore, then hyphenate the spaces. `## 2. IMD app logics`
    becomes `2-imd-app-logics`.
    """
    found = set()

    for heading in re.findall(r"^#{1,6}\s+(.+?)\s*$", document.read_text(encoding="utf-8"), re.M):
        # Inline markup is not part of the slug: the text inside it is.
        text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)

        text = re.sub(r"</?[a-zA-Z][^>]*>", "", text).replace("`", "").replace("*", "")

        slug = re.sub(r"[^\w\s-]", "", text.lower(), flags=re.U)

        found.add(re.sub(r"\s+", "-", slug.strip()))

    return found


def resolve(constants: dict[str, str], value: str) -> str:
    """`"$REPOSITORY/releases"` with REPOSITORY already known."""
    for name, known in constants.items():
        value = value.replace(f"${name}", known).replace(f"${{{name}}}", known)

    return value


source = LINKS.read_text(encoding="utf-8")

constants: dict[str, str] = {}

for name, raw in re.findall(r'const val (\w+)\s*=\s*\n?\s*"([^"]*)"', source):
    constants[name] = resolve(constants, raw)

problems: list[str] = []

checked = 0

external: list[str] = []

for name, url in constants.items():
    if not url.startswith(REPO_PREFIX):
        external.append(f"{name} -> {url}")

        continue

    rest = url[len(REPO_PREFIX):]

    path, _, anchor = rest.partition("#")

    # A path into the tree is /blob/<ref>/<file>; a bare repo URL is the README as GitHub serves it.
    match = re.match(r"^/blob/[^/]+/(.+)$", path)

    if match:
        document = ROOT / match.group(1)

        if not document.exists():
            problems.append(f"{name}: {match.group(1)} does not exist")

            continue
    elif path in ("", "/"):
        document = ROOT / "README.md"
    else:
        # /releases, /issues/ and the like - a repository route, not a document.
        continue

    if not anchor:
        continue

    checked += 1

    available = anchors(document)

    if anchor not in available:
        near = sorted(one for one in available if anchor.split("-")[0] in one)[:3]

        problems.append(
            f"{name}: #{anchor} is not a heading in {document.relative_to(ROOT).as_posix()}"
            + (f" (nearest: {', '.join('#' + one for one in near)})" if near else ""),
        )

print(f"checked {len(constants)} link(s) in ProjectLinks.kt, {checked} of them anchored")

for line in external:
    print(f"  external, not checked: {line}")

if problems:
    print()

    for problem in problems:
        print(f"  {problem}")

    print(f"\n{len(problems)} broken link(s)")

    sys.exit(1)

print("every in-repo link resolves to a real heading")
