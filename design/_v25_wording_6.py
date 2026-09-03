#!/usr/bin/env python3
"""
The bracketed aside under "IMD app Logics" becomes a SU_IMD shell block.

    $ su_imd --why
    su_imd: 🌙☕🥲 ......................
    su_imd: developer lost his sanity
    su_imd: creating & perfecting these.

Four keys, all `translatable="false"`, all in the default locale only — the same treatment
`about_contributor_name` and `about_fork_author` already get. This is not prose: it is styled
as terminal output, the command is a literal, and the dot leader is measured in monospace
cells. Translating it would mean recomputing the leader for eleven different line lengths, and
would leave ten locales whose shell prints something the shell does not print.

The `su_imd: ` prefix is not here. It is one literal repeated on every line and belongs beside
the code that colours it, not in eleven copies of a resource file.

Drops `about_logics_note`, which this replaces, from all eleven locales.

Asserts before it writes, as the others do.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

DROP = "about_logics_note"

# 22 dots, which is what the author settled on looking at the rendered preview rather than at
# a character count. Under the usual "an emoji occupies two monospace cells" rule 21 would land
# exactly on the last line's 36 cells; the emoji's real advance is a property of the device's
# font, so the eye is the better authority here. One character either way if it ever needs it.
DOTS = 22

ADD = {
    "about_shell_command": "su_imd --why",
    "about_shell_emoji": "🌙☕🥲 " + "." * DOTS,
    "about_shell_sanity": "developer lost his sanity",
    "about_shell_creating": "creating &amp; perfecting these.",
}


def path_for(locale):
    return os.path.join(RES, locale, "strings.xml")


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}

    # --- drop the string this replaces, everywhere -------------------
    for locale in LOCALES:
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: missing" % locale)

            continue

        text = open(path, encoding="utf-8").read()

        if body(text, DROP) is None:
            errors.append("%s: %s absent, nothing to drop" % (locale, DROP))

            continue

        updated = re.sub(
            r'[ \t]*<string name="%s"(?: [^>]*)?>.*?</string>\n' % re.escape(DROP),
            "",
            text,
            count=1,
            flags=re.S,
        )

        if updated == text:
            errors.append("%s: %s line did not match for removal" % (locale, DROP))

            continue

        pending[path] = updated

    # --- add the shell block, default locale only --------------------
    path = path_for("values")

    if path in pending:
        text = pending[path]

        block = ""

        for key, value in ADD.items():
            if ('name="%s"' % key) in text:
                errors.append("values: %s already present" % key)

                continue

            if re.search(r"(?<!\\)'", value):
                errors.append("values: %s unescaped apostrophe" % key)

                continue

            if "\n" in value:
                errors.append("values: %s literal newline" % key)

                continue

            if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", value):
                errors.append("values: %s bare ampersand" % key)

                continue

            block += '    <string name="%s" translatable="false">%s</string>\n' % (key, value)

        if text.count("</resources>") != 1:
            errors.append("values: expected one </resources>")
        else:
            pending[path] = text.replace("</resources>", block + "</resources>", 1)

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation --------------------------------------------------
    problems = []

    for locale in LOCALES:
        text = pending[path_for(locale)]

        if body(text, DROP) is not None:
            problems.append("%s: %s survived" % (locale, DROP))

        for m in re.finditer(r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S):
            if "\n" in m.group(2):
                problems.append("%s: %s literal newline" % (locale, m.group(1)))

            if re.search(r"(?<!\\)'", m.group(2)):
                problems.append("%s: %s unescaped apostrophe" % (locale, m.group(1)))

    values = pending[path_for("values")]

    for key, value in ADD.items():
        if body(values, key) != value:
            problems.append("values: %s does not match" % key)

        if ('name="%s" translatable="false"' % key) not in values:
            problems.append("values: %s is not marked untranslatable" % key)

    # The leader has to be the length that was actually agreed.
    if body(values, "about_shell_emoji").count(".") != DOTS:
        problems.append("the dot leader is not %d dots long" % DOTS)

    # Only the default locale carries these, or check_translations would demand ten more.
    for locale in LOCALES:
        if locale == "values":
            continue

        for key in ADD:
            if ('name="%s"' % key) in pending[path_for(locale)]:
                problems.append("%s: %s should not exist outside values/" % (locale, key))

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print("\ndropped %s from %d locales" % (DROP, len(LOCALES)))
    print("added %d untranslatable shell strings to values/" % len(ADD))
    print("\nthe block, as it will render:")
    print("   " + ADD["about_shell_command"])

    for key in ("about_shell_emoji", "about_shell_sanity", "about_shell_creating"):
        print("   su_imd: " + ADD[key].replace("&amp;", "&"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
