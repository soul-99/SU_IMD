#!/usr/bin/env python3
"""
r12 diagnostic probe strings.

⚠ TEMPORARY - delete these three keys in r13 along with the dialog, its use case and its row,
the way the diag1 build's log was removed in r3.

All three are translatable="false" and live in values/ only, which is the established handling
for text that is not going to survive a release - the same treatment about_shell_* has. That is
also why this is a second script rather than more keys in _r12_auto_unhide.py: the strings that
stay and the strings that go should not be removed by the same edit.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

SETTINGS_VALUES = os.path.join(
    ROOT, "feature", "settings", "src", "main", "res", "values", "strings.xml",
)

STRINGS = {
    "auto_unhide_diag_title": "Auto unhide probe (test build)",
    "auto_unhide_diag_note": "what this device reports about closed apps",
    "auto_unhide_diag_copy": "Copy report",
}


def main():
    print("ROOT = %s" % ROOT)

    errors = []

    if not os.path.exists(SETTINGS_VALUES):
        print("  ! missing %s" % SETTINGS_VALUES)

        print("REFUSED, nothing written")

        return 1

    text = open(SETTINGS_VALUES, encoding="utf-8").read()

    for key, value in STRINGS.items():
        if re.search(r'<string name="%s"' % re.escape(key), text):
            errors.append("%s already present" % key)

        if re.search(r"(?<!\\)'", value):
            errors.append("%s: unescaped apostrophe" % key)

        if '"' in value or "\n" in value:
            errors.append("%s: quote or literal newline" % key)

    if text.count("</resources>") != 1:
        errors.append("expected exactly one </resources>")

    # Only values/ - a translatable="false" key in a locale file is the mistake this guards.
    locales_dir = os.path.dirname(os.path.dirname(SETTINGS_VALUES))

    for entry in sorted(os.listdir(locales_dir)):
        if not entry.startswith("values-"):
            continue

        other = os.path.join(locales_dir, entry, "strings.xml")

        if not os.path.exists(other):
            continue

        other_text = open(other, encoding="utf-8").read()

        for key in STRINGS:
            if re.search(r'<string name="%s"' % re.escape(key), other_text):
                errors.append("%s: %s must not be translated" % (entry, key))

    if errors:
        for error in errors:
            print("  ! %s" % error)

        print("REFUSED, nothing written")

        return 1

    additions = "\n".join(
        '    <string name="%s" translatable="false">%s</string>' % (key, STRINGS[key])
        for key in sorted(STRINGS)
    )

    open(SETTINGS_VALUES, "w", encoding="utf-8").write(
        text.replace("</resources>", additions + "\n</resources>", 1)
    )

    print("wrote %d translatable=\"false\" strings into values/ only" % len(STRINGS))

    return 0


if __name__ == "__main__":
    sys.exit(main())
