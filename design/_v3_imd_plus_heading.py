#!/usr/bin/env python3
"""
v3-r2b3c — what the IMD+ section heading warns about.

**The author's instruction**, after one revision of his own: replace the bracket in the heading
with `'needs background service'`, and put EXPERIMENTAL in the expanded section's description
rather than on a second line of the heading.

    IMD+ (EXPERIMENTAL)            ->  IMD+ (needs background service)
    click to setup                 ->  EXPERIMENTAL - click to setup

**Why this is the right place for each.** The bracket in a collapsed heading is the only thing a
reader sees before deciding whether to open the section, and "needs a background service" is the
fact that decides it — it is the cost, and it is the one thing about IMD+ that is true whatever
the user does with it. EXPERIMENTAL is a warning about the feature itself, so it belongs where
somebody is about to switch it on.

⚠ **The subtitle is the description this section has.** `CollapsibleSection` takes a title and
content, and no description; the description shown when the section opens is the subtitle of the
row inside it. Adding a description parameter to the component would be a new UI element across
all six sections, which is the author's call rather than mine — so this uses the line that is
already there.

⚠ **The code comment above the section is corrected with it.** It currently reads "The heading is
where the warning now lives, which is what lets the row inside go back to being called simply
'Auto hide settings'", which stops being true the moment the warning moves back down.

⚠ **`values-es` and `values-b+pt+BR` still carry the old English sentence.** Neither is in the
sweep — `check_translations` reads `hi` only — and translations are deferred to the end of the
build on the author's own instruction, so they are left for that pass rather than half-done here.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

STRINGS_EDITS: list[tuple[str, str]] = [
    (
        """    <string name="section_imd_plus">IMD+ (EXPERIMENTAL)</string>""",
        """    <!--
      The bracket names the cost rather than the risk. It is the only thing a reader sees
      before deciding whether to open the section, and needing a background service is what
      decides it; EXPERIMENTAL moved down to auto_hide_setup, which is read by somebody who
      has already opened the section and is about to switch the feature on.
    -->
    <string name="section_imd_plus">IMD+ (needs background service)</string>""",
    ),
    (
        """    <string name="auto_hide_setup">click to setup</string>""",
        """    <string name="auto_hide_setup">EXPERIMENTAL - click to setup</string>""",
    ),
]

SCREEN_EDITS: list[tuple[str, str]] = [
    (
        """        // A section of its own rather than a last row under Default IMD settings, because it
        // is the only thing in these settings that is a feature rather than a setting:
        // everything above says *what* is hidden, this says that IMD may decide *when* on its
        // own. The heading is where the warning now lives, which is what lets the row inside
        // go back to being called simply "Auto hide settings".
""",
        """        // A section of its own rather than a last row under Default IMD settings, because it
        // is the only thing in these settings that is a feature rather than a setting:
        // everything above says *what* is hidden, this says that IMD may decide *when* on its
        // own.
        //
        // The two warnings are split, and deliberately. The heading's bracket names what IMD+
        // *costs* — a background service — because that is what a reader decides on before
        // opening the section at all. EXPERIMENTAL is a warning about the feature rather than
        // about its price, so it sits in the row's subtitle inside, where it is read by
        // somebody who has opened the section and is about to move the switch.
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120 and not line.lstrip().startswith("<string"):
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    written: list[tuple[Path, str]] = []

    for relative, edits in ((STRINGS, STRINGS_EDITS), (SCREEN, SCREEN_EDITS)):
        path = ROOT / relative

        text = apply(path, edits, problems)

        if text is not None:
            written.append((path, text))

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in written:
        path.write_text(text, encoding="utf-8")

    print("ok — the heading names the cost, the row inside carries the warning")

    return 0


if __name__ == "__main__":
    sys.exit(main())
