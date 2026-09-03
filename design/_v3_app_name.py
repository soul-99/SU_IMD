#!/usr/bin/env python3
"""
v3-r1 — drop "SU" and "Shut up!" from the app's name where a reader sees it.

Scope, as the author set it: the initialisation screen and the readmes, and nothing else.

NOT touched, deliberately:
  * `app_name` — already "IMD" in all 12 locale files, so there is nothing to change.
  * the About shell block — `su_imd:` and `su_imd --why` stay. The author reversed an earlier
    decision here; keeping them also means the 22-dot leader does not move.
  * every identifier: applicationId `com.soul_99.suIMD`, `rootProject.name`, the repo URLs,
    the CI workflow, and the 206 `Modifications Copyright 2026 soul_99 (suIMD)` licence
    headers. None is user-visible and changing any of them breaks upgrades or links.

⚠ The new value carries a plain ASCII apostrophe, which Android XML requires be escaped as
\\'. The line it replaces used a curly U+2019, which needs no escape. The author typed a plain
one, and the verbatim rule says their characters win over the file's previous typography.

Asserts every anchor matches exactly once. Writes nothing if any file fails.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The author's wording, chosen 30 Aug 2026: option 2 "with - instead of emdash".
AUTHOR_NAME_LINE = "IMD - It's My Device"

STRINGS = ROOT / "app/src/main/res/values/strings.xml"

# The current value uses an em-dash (U+2014) and a curly apostrophe (U+2019).
OLD_FULL_FORM = "SU IMD — Shut up! it’s my device"
NEW_FULL_FORM = "IMD - It\\'s My Device"

EDITS = [
    (
        "README.md",
        "# (SU) IMD - Shut up! it's my device",
        f"# {AUTHOR_NAME_LINE}",
    ),
    (
        "README.md",
        "- **License:** (SU) IMD is licensed under",
        "- **License:** IMD is licensed under",
    ),
    (
        "SUIMD.md",
        "**(SU) IMD - Shut up! it's my device** is a fork of",
        f"**{AUTHOR_NAME_LINE}** is a fork of",
    ),
    # ⚠ A GPL-3.0 §5(a) attribution sentence. Updated because it states the name the app
    # actually ships under, and leaving it would make the notice describe a name that is no
    # longer used. Raised with the author rather than changed quietly.
    (
        "SUIMD.md",
        "**(SU) IMD**, so this fork installs alongside the original",
        "**IMD**, so this fork installs alongside the original",
    ),
    (
        "CONTRIBUTING.md",
        "# Contributing to (SU) IMD",
        "# Contributing to IMD",
    ),
    (
        "fastlane/metadata/android/en-US/title.txt",
        "[SU] IMD - (A supercharged fork of Geto)",
        "IMD - (A supercharged fork of Geto)",
    ),
]


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def main() -> int:
    planned: dict[Path, str] = {}
    report: list[str] = []

    # --- the string resource -----------------------------------------------------------
    text = STRINGS.read_text(encoding="utf-8")

    if text.count(OLD_FULL_FORM) != 1:
        return fail(
            f"app_full_form anchor matched {text.count(OLD_FULL_FORM)} time(s), expected 1",
        )

    updated = text.replace(OLD_FULL_FORM, NEW_FULL_FORM, 1)

    # Android XML: a bare apostrophe is a hard aapt2 failure.
    if "It's My Device" in updated and "It\\'s My Device" not in updated:
        return fail("the apostrophe in the new value is not escaped")

    try:
        ET.fromstring(updated)
    except ET.ParseError as error:
        return fail(f"strings.xml would not parse: {error}")

    planned[STRINGS] = updated
    report.append(f"  ok  app/src/main/res/values/strings.xml  app_full_form -> {NEW_FULL_FORM}")

    # --- the docs ----------------------------------------------------------------------
    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            return fail(f"missing {rel}")

        body = planned.get(path, path.read_text(encoding="utf-8"))

        found = body.count(old)

        if found != 1:
            return fail(f"{rel}: anchor {old!r} matched {found} time(s), expected 1")

        planned[path] = body.replace(old, new, 1)
        report.append(f"  ok  {rel}  :: {old[:46]}")

    # --- nothing user-visible may still say SU / Shut up -------------------------------
    for path, body in planned.items():
        for banned in ("SU IMD", "(SU) IMD", "[SU] IMD", "Shut up"):
            if banned in body:
                line = next(
                    (n for n, l in enumerate(body.split("\n"), 1) if banned in l),
                    0,
                )
                return fail(f"{path.relative_to(ROOT)}:{line} still contains {banned!r}")

    for path, body in planned.items():
        path.write_text(body, encoding="utf-8")

    print("\n".join(report))
    print(f"\nwrote {len(planned)} file(s), {len(EDITS) + 1} edit(s)")
    print(f"  name line: {AUTHOR_NAME_LINE!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
