#!/usr/bin/env python3
"""
`about_logics_note` reflowed onto three lines, with the emoji lifted to the top.

    (🌙☕🥲
    developer lost his sanity
    creating & perfecting these.)

The breaks are `\\n` escapes, never wrapped lines: aapt2 collapses a literal newline in an
unquoted string resource into a single space, which is how the two-line IMD+ title was lost
once already. The ampersand is `&amp;` - it is XML before it is a string, and a bare `&` makes
the whole file unparseable rather than merely wrong.

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

KEY = "about_logics_note"

# The emoji line, then the remark split where the English splits it.
VALUES = {
    "values": "(🌙☕🥲\\ndeveloper lost his sanity\\ncreating &amp; perfecting these.)",
    "values-ar": "(🌙☕🥲\\nفقد المطوّر صوابه\\nوهو يصنعها ويُتقنها.)",
    "values-b+pt+BR": (
        "(🌙☕🥲\\no desenvolvedor perdeu a sanidade\\ncriando e aperfeiçoando isto.)"
    ),
    "values-b+zh+Hans": "(🌙☕🥲\\n开发者在创作与打磨这些的\\n过程中失去了理智。)",
    "values-de": (
        "(🌙☕🥲\\nder Entwickler hat den Verstand verloren\\n"
        "beim Erschaffen und Verfeinern.)"
    ),
    "values-es": (
        "(🌙☕🥲\\nel desarrollador perdió la cordura\\ncreando y perfeccionando esto.)"
    ),
    "values-fr": (
        "(🌙☕🥲\\nle développeur y a perdu la raison\\nà les créer et les perfectionner.)"
    ),
    "values-hi": "(🌙☕🥲\\nडेवलपर का दिमाग़ चल गया\\nइन्हें बनाते और निखारते हुए।)",
    "values-ja": "(🌙☕🥲\\n開発者は作り込み磨き上げるうちに\\n正気を失いました。)",
    "values-ko": "(🌙☕🥲\\n개발자는 이것들을 만들고 다듬다\\n제정신을 잃었습니다.)",
    "values-ru": "(🌙☕🥲\\nразработчик сошёл с ума,\\nсоздавая и доводя всё это.)",
}


def path_for(locale):
    return os.path.join(RES, locale, "strings.xml")


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def main():
    print("ROOT = %s" % ROOT)

    if set(VALUES) != set(LOCALES):
        print("REFUSED: locale set mismatch")

        return 1

    errors = []
    pending = {}

    for locale in LOCALES:
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: missing" % locale)

            continue

        text = open(path, encoding="utf-8").read()

        if body(text, KEY) is None:
            errors.append("%s: %s absent" % (locale, KEY))

            continue

        value = VALUES[locale]

        if re.search(r"(?<!\\)'", value):
            errors.append("%s: unescaped apostrophe" % locale)

            continue

        if "\n" in value:
            errors.append("%s: literal newline - use the escape" % locale)

            continue

        if value.count("\\n") != 2:
            errors.append(
                "%s: %d line breaks, expected 2 (three lines)" % (locale, value.count("\\n"))
            )

            continue

        if not value.startswith("(🌙☕🥲\\n"):
            errors.append("%s: does not open with the emoji line" % locale)

            continue

        if not value.endswith(")"):
            errors.append("%s: bracket not closed" % locale)

            continue

        if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", value):
            errors.append("%s: bare ampersand - XML would not parse" % locale)

            continue

        pending[path] = re.sub(
            r'(<string name="%s"((?: [^>]*)?)>).*?(</string>)' % re.escape(KEY),
            lambda m: m.group(1) + value + m.group(3),
            text,
            count=1,
            flags=re.S,
        )

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    problems = []

    for locale in LOCALES:
        text = pending[path_for(locale)]

        if body(text, KEY) != VALUES[locale]:
            problems.append("%s: value does not match" % locale)

        for m in re.finditer(r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S):
            if "\n" in m.group(2):
                problems.append("%s: %s literal newline" % (locale, m.group(1)))

            if re.search(r"(?<!\\)'", m.group(2)):
                problems.append("%s: %s unescaped apostrophe" % (locale, m.group(1)))

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print("\nreflowed %s onto three lines in %d locales" % (KEY, len(pending)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
