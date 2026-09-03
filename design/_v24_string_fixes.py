#!/usr/bin/env python3
"""
Two string defects in the v2.4 IMD+ wording, fixed together.

1. `auto_hide_flow_9` (English only) carries an unescaped apostrophe in "IMD's own".
   aapt2 refuses that: "Apostrophe not preceded by \\". It is a hard build failure, and it
   is English-only -- French already writes `d\\'accessibilite` correctly.

2. `auto_hide` is written across two physical lines in all eleven locales, with a literal
   newline inside the element. aapt2 normalises whitespace in an unquoted string resource,
   so a literal newline is collapsed into a single space and the title renders on one line.
   The two-line title the user asked for needs the escape `\\n`, which is what
   `auto_hide_intro` two lines below it already uses -- `auto_hide` is the only string in
   the whole repository written the other way.

Asserts before it writes, per the project convention: every expected match is counted and a
mismatch exits non-zero without touching a file.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

SETTINGS_RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

LOCALES = [
    "values",
    "values-ar",
    "values-b+pt+BR",
    "values-b+zh+Hans",
    "values-de",
    "values-es",
    "values-fr",
    "values-hi",
    "values-ja",
    "values-ko",
    "values-ru",
]

# ---------------------------------------------------------------- helpers


def path_for(locale):
    return os.path.join(SETTINGS_RES, locale, "strings.xml")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def string_body(text, name):
    """The raw body of one <string>, or None. Non-greedy so it stops at its own close tag."""
    match = re.search(
        r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S
    )

    return match.group(1) if match else None


# ---------------------------------------------------------------- fix 1


def fix_flow_9(errors, pending):
    """Escape the apostrophe in the English auto_hide_flow_9."""
    path = path_for("values")
    text = pending.get(path) or read(path)

    body = string_body(text, "auto_hide_flow_9")

    if body is None:
        errors.append("values/strings.xml: auto_hide_flow_9 not found")

        return

    unescaped = re.findall(r"(?<!\\)'", body)

    if not unescaped:
        print("  auto_hide_flow_9: already escaped, nothing to do")

        return

    if len(unescaped) != 1:
        errors.append(
            "values/strings.xml: auto_hide_flow_9 has %d unescaped apostrophes, expected 1"
            % len(unescaped)
        )

        return

    fixed = re.sub(r"(?<!\\)'", r"\\'", body)

    old = '<string name="auto_hide_flow_9">%s</string>' % body
    new = '<string name="auto_hide_flow_9">%s</string>' % fixed

    if text.count(old) != 1:
        errors.append(
            "values/strings.xml: auto_hide_flow_9 element matched %d times, expected 1"
            % text.count(old)
        )

        return

    pending[path] = text.replace(old, new)

    print("  auto_hide_flow_9: escaped 1 apostrophe (values)")


# ---------------------------------------------------------------- fix 2


def fix_auto_hide_title(errors, pending):
    """Turn the literal newline inside auto_hide into the escape \\n, in every locale."""
    for locale in LOCALES:
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: strings.xml missing" % locale)

            continue

        text = pending.get(path) or read(path)

        body = string_body(text, "auto_hide")

        if body is None:
            errors.append("%s: auto_hide not found" % locale)

            continue

        if "\n" not in body:
            if "\\n" not in body:
                errors.append(
                    "%s: auto_hide has neither a literal newline nor \\n -- the two-line "
                    "title would render on one line" % locale
                )
            else:
                print("  auto_hide (%s): already uses \\n" % locale)

            continue

        if body.count("\n") != 1:
            errors.append(
                "%s: auto_hide holds %d literal newlines, expected 1"
                % (locale, body.count("\n"))
            )

            continue

        # Collapse any indentation the wrap introduced, then escape the break itself.
        first, second = body.split("\n")

        fixed = "%s\\n%s" % (first.rstrip(), second.lstrip())

        old = '<string name="auto_hide">%s</string>' % body
        new = '<string name="auto_hide">%s</string>' % fixed

        if text.count(old) != 1:
            errors.append(
                "%s: auto_hide element matched %d times, expected 1"
                % (locale, text.count(old))
            )

            continue

        pending[path] = text.replace(old, new)

        print("  auto_hide (%s): literal newline -> \\n" % locale)


# ---------------------------------------------------------------- validation


def validate(pending):
    """Nothing is written until every locale passes these."""
    problems = []

    for locale in LOCALES:
        path = path_for(locale)

        text = pending.get(path) or read(path)

        body = string_body(text, "auto_hide")

        if body is None:
            problems.append("%s: auto_hide vanished" % locale)

            continue

        if "\n" in body:
            problems.append("%s: auto_hide still holds a literal newline" % locale)

        if "\\n" not in body:
            problems.append("%s: auto_hide has no \\n break" % locale)

        # Every string in these files, not only the two edited, must be escaped: a single
        # miss anywhere fails the resource compile just as hard.
        for match in re.finditer(
            r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S
        ):
            name, value = match.group(1), match.group(2)

            if re.search(r"(?<!\\)'", value):
                problems.append("%s: %s has an unescaped apostrophe" % (locale, name))

    return problems


def main():
    print("ROOT = %s" % ROOT)

    errors = []

    # One in-memory copy per file, threaded through both fixes in order, so the two edits to
    # values/strings.xml compose instead of one overwriting the other.
    pending = {}

    print("\nfix 1 -- unescaped apostrophe")
    fix_flow_9(errors, pending)

    print("\nfix 2 -- two-line title")
    fix_auto_hide_title(errors, pending)

    if errors:
        print("\nREFUSED, nothing written:")

        for error in errors:
            print("  %s" % error)

        return 1

    problems = validate(pending)

    if problems:
        print("\nVALIDATION FAILED, nothing written:")

        for problem in problems:
            print("  %s" % problem)

        return 1

    for path, text in sorted(pending.items()):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    print("\nwrote %d file(s); validation clean" % len(pending))

    return 0


if __name__ == "__main__":
    sys.exit(main())
