#!/usr/bin/env python3
"""r4g — the two rows in the settings tab say what they are, over two lines.

The author:

    "in settings tab update DOOA and Access service to hide labels to
     'Accessibility services (next line)managed by IMD' and
     'Display over other apps (next line)managed by IMD'"

    Accessibility services      ->   Accessibility services
    to hide                          managed by IMD

    Display over other apps     ->   Display over other apps
    to hide                          managed by IMD

⚠ **New strings rather than an edit to the existing two.** `accessibility_services` and
`overlay_packages` are each used twice: as the row title in the settings tab, and as the heading
of the dialog the row opens. The author named the settings tab, so the rows get labels of their
own and the dialog headings keep the wording they have. Editing the shared string would have
retitled two dialogs nobody asked about.

⚠ **`\\n` in the resource, not two `Text`s.** `SettingsColumn` draws one title; two composables
would need it to learn about a second line, and the row's own spacing would have to be
rebalanced against every other row in the tab. A line break in the string is the version that
changes nothing else.

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
            """    <string name="accessibility_services">Accessibility services to hide</string>
""",
            """    <string name="accessibility_services">Accessibility services to hide</string>
    <string name="accessibility_services_row">Accessibility services\\nmanaged by IMD</string>
""",
            1,
        ),
        (
            """    <string name="overlay_packages">Display over other apps to hide</string>
""",
            """    <string name="overlay_packages">Display over other apps to hide</string>
    <string name="overlay_packages_row">Display over other apps\\nmanaged by IMD</string>
""",
            1,
        ),
    ]),

    (SCREEN, [
        (
            """            SettingsColumn(
                title = stringResource(R.string.accessibility_services),
""",
            """            SettingsColumn(
                // The row's own label, not the dialog's heading. Both said "… to hide" until
                // r4g; the author retitled the rows and left the dialogs alone.
                title = stringResource(R.string.accessibility_services_row),
""",
            1,
        ),
        (
            """                title = stringResource(R.string.overlay_packages),
""",
            """                title = stringResource(R.string.overlay_packages_row),
""",
            1,
        ),
    ]),
]


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

    strings = staged.get(ROOT / STRINGS, "")
    screen = staged.get(ROOT / SCREEN, "")

    for rel, text, token, expected in (
        (STRINGS, strings, "accessibility_services_row", 1),
        (STRINGS, strings, "overlay_packages_row", 1),
        # The dialogs keep the old wording, so each original name must still be declared and
        # still be read by exactly the one place that heads a dialog with it.
        (STRINGS, strings, '<string name="accessibility_services">', 1),
        (STRINGS, strings, '<string name="overlay_packages">', 1),
        (SCREEN, screen, "R.string.accessibility_services_row", 1),
        (SCREEN, screen, "R.string.overlay_packages_row", 1),
        (SCREEN, screen, "R.string.accessibility_services)", 0),
        (SCREEN, screen, "R.string.overlay_packages)", 0),
    ):
        if text.count(token) != expected:
            problems.append(f"{rel}: expected {expected} of {token!r}, found {text.count(token)}")

    # Both new labels break exactly once, and both second lines are the author's own words.
    for name in ("accessibility_services_row", "overlay_packages_row"):
        line = next(
            (line for line in strings.splitlines() if f'name="{name}"' in line),
            "",
        )

        if line.count("\\n") != 1:
            problems.append(f"{STRINGS}: {name} does not break exactly once")

        if not line.endswith("managed by IMD</string>"):
            problems.append(f"{STRINGS}: {name} does not end with the author's second line")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and path.suffix != ".xml":
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - the two rows carry their own two-line labels; the dialogs are unchanged")

    return 0


if __name__ == "__main__":
    sys.exit(main())
