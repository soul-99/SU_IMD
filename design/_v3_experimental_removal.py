#!/usr/bin/env python3
"""
v3 — `EXPERIMENTAL - ` comes off the IMD+ row's subtitle, completely.

r2b3c split one warning into two: the heading's bracket took the *cost* (`IMD+ (needs
background service)`) and `EXPERIMENTAL` moved down into `auto_hide_setup`, the subtitle of
the row inside the section. The author has since asked for the second half to go entirely, so
`auto_hide_setup` returns to `click to setup` and the heading stays as it is.

Three edits, not one. The string is the change; the two comments that explain the split are
now describing something the app no longer does, and a comment that survives the code it
documents is the next reader's wrong turn.

⚠ Only `values/` carries the prefix. `values-ko`, `values-fr` and `values-es` translated
`auto_hide_setup` without it, so nothing outside English needs touching — and translations are
deferred to the end of the project on the author's instruction in any case.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STRINGS = "feature/settings/src/main/res/values/strings.xml"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            '    <string name="auto_hide_setup">EXPERIMENTAL - click to setup</string>\n',
            '    <string name="auto_hide_setup">click to setup</string>\n',
            1,
        ),
        (
            """      decides it; EXPERIMENTAL moved down to auto_hide_setup, which is read by somebody who
      has already opened the section and is about to switch the feature on.
""",
            """      decides it. The EXPERIMENTAL warning that briefly sat below in auto_hide_setup is
      gone at the author's instruction, and the row's subtitle says only what a tap does.
""",
            1,
        ),
    ]),
    (SCREEN, [
        (
            """        // The two warnings are split, and deliberately. The heading's bracket names what IMD+
        // *costs* — a background service — because that is what a reader decides on before
        // opening the section at all. EXPERIMENTAL is a warning about the feature rather than
        // about its price, so it sits in the row's subtitle inside, where it is read by
        // somebody who has opened the section and is about to move the switch.
""",
            """        // The heading's bracket names what IMD+ *costs* — a background service — because
        // that is what a reader decides on before opening the section at all. The
        // EXPERIMENTAL warning that r2b3c put in the row's subtitle below is gone at the
        // author's instruction: the bracket now carries the whole of what this heading has to
        // say, and the subtitle says only what a tap does.
""",
            1,
        ),
    ]),
]

# Nothing in the app may still say EXPERIMENTAL about IMD+ afterwards. `tasker_integration`
# is a different feature and keeps its own bracket, so it is named rather than swept.
ALLOWED_AFTER = {'<string name="tasker_integration">IMD intents (EXPERIMENTAL)</string>'}


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # Every added line under 120 characters, checked against the lines this edit introduces
    # rather than against the file — both of these files carry pre-existing long lines, and a
    # guard that polices those refuses work it did not cause. See handover_3 §4.
    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    # The point of the round, asserted rather than assumed.
    english = staged[ROOT / STRINGS]

    for line in english.splitlines():
        if "EXPERIMENTAL" in line and "<string" in line and line.strip() not in ALLOWED_AFTER:
            problems.append(f"{STRINGS}: EXPERIMENTAL survives in {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok — EXPERIMENTAL is off the IMD+ row, and both comments say so")

    return 0


if __name__ == "__main__":
    sys.exit(main())
