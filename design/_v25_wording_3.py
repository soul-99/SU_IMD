#!/usr/bin/env python3
"""
`about_logics` — the line under "App created by" that links to SUIMD.md section 2.

Two lines in one string, the bracketed aside included, because the whole thing is one link.
The `\\n` is the escape, never a wrapped line: aapt2 collapses a literal newline in an unquoted
string resource into a single space, which is how the two-line IMD+ title was lost once already.

The aside is the author's own, so the English is verbatim and the translations render the same
remark rather than a description of it. The emoji carry across unchanged.

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

KEY = "about_logics"

VALUES = {
    "values": (
        "IMD app Logics\\n"
        "(almost lost my sanity making and testing these🌙☕)"
    ),
    "values-ar": (
        "مخططات عمل تطبيق IMD\\n"
        "(كدت أفقد صوابي وأنا أصنعها وأختبرها🌙☕)"
    ),
    "values-b+pt+BR": (
        "Lógicas do app IMD\\n"
        "(quase perdi a sanidade fazendo e testando isso🌙☕)"
    ),
    "values-b+zh+Hans": (
        "IMD 应用逻辑图\\n"
        "(做这些并测试它们时我差点疯掉🌙☕)"
    ),
    "values-de": (
        "IMD-App-Logiken\\n"
        "(hat mich beim Bauen und Testen fast den Verstand gekostet🌙☕)"
    ),
    "values-es": (
        "Lógicas de la app IMD\\n"
        "(casi pierdo la cordura creándolas y probándolas🌙☕)"
    ),
    "values-fr": (
        "Logiques de l\\'application IMD\\n"
        "(j\\'ai failli y perdre la raison à les faire et les tester🌙☕)"
    ),
    "values-hi": (
        "IMD ऐप लॉजिक्स\\n"
        "(इन्हें बनाते और परखते हुए मेरा दिमाग़ लगभग चल गया था🌙☕)"
    ),
    "values-ja": (
        "IMD アプリのロジック\\n"
        "(作って試すうちに正気を失いかけました🌙☕)"
    ),
    "values-ko": (
        "IMD 앱 로직\\n"
        "(만들고 시험하다 제정신을 잃을 뻔했습니다🌙☕)"
    ),
    "values-ru": (
        "Логика приложения IMD\\n"
        "(чуть не сошёл с ума, пока делал и проверял всё это🌙☕)"
    ),
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

    if set(VALUES) != set(LOCALES):
        print("REFUSED: locale set mismatch")

        return 1

    for locale in LOCALES:
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: missing" % locale)

            continue

        text = open(path, encoding="utf-8").read()

        if ('name="%s"' % KEY) in text:
            errors.append("%s: %s already present" % (locale, KEY))

            continue

        value = VALUES[locale]

        if re.search(r"(?<!\\)'", value):
            errors.append("%s: unescaped apostrophe" % locale)

            continue

        if "\n" in value:
            errors.append("%s: literal newline - use the escape" % locale)

            continue

        if "\\n" not in value:
            errors.append("%s: no line break, the line is meant to wrap in two" % locale)

            continue

        if text.count("</resources>") != 1:
            errors.append("%s: expected one </resources>" % locale)

            continue

        pending[path] = text.replace(
            "</resources>",
            '    <string name="%s">%s</string>\n</resources>' % (KEY, value),
            1,
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

    print("\nadded %s to %d locales" % (KEY, len(pending)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
