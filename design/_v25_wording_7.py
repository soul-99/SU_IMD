#!/usr/bin/env python3
"""
r8 strings: the IMD+ section heading is renamed, and the empty-configuration popup arrives.

1. REPLACE `section_imd_plus` — "IMD + (pro users)" becomes "IMD+ (EXPERIMENTAL)", the author's
   wording, in all eleven locales. The bracketed word is translated the way "(pro users)"
   already was: the heading is a sentence the reader is meant to understand, not a product
   name. Note the space goes: the author writes "IMD+", not "IMD +".

2. ADD `auto_hide_nothing_to_hide` — what the IMD+ window says when a watched app is opened and
   the device-wide "Settings to hide" configuration has nothing ticked. IMD+ does not run at
   all in that state: the app is left alone, not stopped and not reopened, so this popup is the
   entire outcome and has to say where to go.

   Each locale names its own "Default IMD settings" section as that locale spells it, taken from
   `section_app_functions` and asserted against it below — a popup that sends the reader to a
   heading they cannot find in their language is worse than no popup.

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

# --- 1. the heading -------------------------------------------------------
HEADING = "section_imd_plus"

HEADING_FROM = {
    "values": "IMD + (pro users)",
    "values-ar": "‏IMD + (للمستخدمين المحترفين)",
    "values-b+pt+BR": "IMD + (usuários avançados)",
    "values-b+zh+Hans": "IMD +（高级用户）",
    "values-de": "IMD + (Profi-Nutzer)",
    "values-es": "IMD + (usuarios avanzados)",
    "values-fr": "IMD + (utilisateurs avancés)",
    "values-hi": "IMD + (प्रो उपयोगकर्ता)",
    "values-ja": "IMD +（上級ユーザー）",
    "values-ko": "IMD + (전문 사용자)",
    "values-ru": "IMD + (для опытных)",
}

HEADING_TO = {
    "values": "IMD+ (EXPERIMENTAL)",
    # The leading RLM is kept: the line still opens with Latin letters inside an RTL paragraph.
    "values-ar": "‏IMD+ (تجريبي)",
    "values-b+pt+BR": "IMD+ (EXPERIMENTAL)",
    "values-b+zh+Hans": "IMD+（实验性）",
    "values-de": "IMD+ (EXPERIMENTELL)",
    "values-es": "IMD+ (EXPERIMENTAL)",
    "values-fr": "IMD+ (EXPÉRIMENTAL)",
    "values-hi": "IMD+ (प्रयोगात्मक)",
    "values-ja": "IMD+（実験的）",
    "values-ko": "IMD+ (실험적)",
    "values-ru": "IMD+ (ЭКСПЕРИМЕНТАЛЬНО)",
}

# --- 2. the popup ---------------------------------------------------------
POPUP = "auto_hide_nothing_to_hide"

# The author's sentence, verbatim, in the default locale.
POPUP_TEXT = {
    "values": "Please set what settings to hide under IMD default settings to use IMD+ auto hide.",
    "values-ar": "يرجى تحديد الإعدادات المراد إخفاؤها ضمن إعدادات IMD الافتراضية لاستخدام الإخفاء التلقائي في IMD+.",
    "values-b+pt+BR": "Defina quais configurações ocultar em Configurações padrão do IMD para usar a ocultação automática do IMD+.",
    "values-b+zh+Hans": "请先在“默认 IMD 设置”中选择要隐藏的设置，才能使用 IMD+ 自动隐藏。",
    "values-de": "Bitte lege unter Standard-IMD-Einstellungen fest, welche Einstellungen ausgeblendet werden sollen, um das automatische Ausblenden von IMD+ zu nutzen.",
    "values-es": "Elige qué ajustes ocultar en Ajustes predeterminados de IMD para usar la ocultación automática de IMD+.",
    "values-fr": "Veuillez choisir les paramètres à masquer dans Paramètres IMD par défaut pour utiliser le masquage automatique IMD+.",
    "values-hi": "IMD+ ऑटो हाइड इस्तेमाल करने के लिए कृपया डिफ़ॉल्ट IMD सेटिंग्स में चुनें कि कौन-सी सेटिंग्स छिपानी हैं।",
    "values-ja": "IMD+ の自動非表示を使うには、デフォルト IMD 設定で非表示にする設定を選んでください。",
    "values-ko": "IMD+ 자동 숨기기를 사용하려면 기본 IMD 설정에서 숨길 설정을 선택하세요.",
    "values-ru": "Чтобы использовать автоскрытие IMD+, укажите в разделе «Стандартные настройки IMD», какие настройки скрывать.",
}

# What each locale's "Default IMD settings" heading actually reads, and what its popup has to
# name. Asserted rather than trusted: if that heading is ever reworded, this popup starts
# pointing at a section that no longer exists under that name.
#
# English is the one locale where the two differ, and deliberately: the author writes "IMD
# default settings" and the heading reads "Default IMD settings". Their sentence is verbatim and
# does not get tidied to match - so English is checked as the same three words rather than the
# same phrase, and every other locale is checked as an exact substring.
SECTION_ECHO = {
    "values": "Default IMD settings",
    "values-ar": "إعدادات IMD الافتراضية",
    "values-b+pt+BR": "Configurações padrão do IMD",
    "values-b+zh+Hans": "默认 IMD 设置",
    "values-de": "Standard-IMD-Einstellungen",
    "values-es": "Ajustes predeterminados de IMD",
    "values-fr": "Paramètres IMD par défaut",
    "values-hi": "डिफ़ॉल्ट IMD सेटिंग्स",
    "values-ja": "デフォルト IMD 設定",
    "values-ko": "기본 IMD 설정",
    "values-ru": "Стандартные настройки IMD",
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

    for locale in LOCALES:
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: missing" % locale)

            continue

        text = open(path, encoding="utf-8").read()

        # --- 1. the heading ------------------------------------------
        current = body(text, HEADING)

        if current is None:
            errors.append("%s: %s absent" % (locale, HEADING))

            continue

        if current != HEADING_FROM[locale]:
            errors.append(
                "%s: %s reads %r, expected %r"
                % (locale, HEADING, current, HEADING_FROM[locale])
            )

            continue

        old_line = '<string name="%s">%s</string>' % (HEADING, HEADING_FROM[locale])
        new_line = '<string name="%s">%s</string>' % (HEADING, HEADING_TO[locale])

        if text.count(old_line) != 1:
            errors.append("%s: %s matched %d times, expected 1" % (locale, HEADING, text.count(old_line)))

            continue

        text = text.replace(old_line, new_line, 1)

        # --- 2. the popup --------------------------------------------
        if body(text, POPUP) is not None:
            errors.append("%s: %s already present" % (locale, POPUP))

            continue

        value = POPUP_TEXT[locale]

        if re.search(r"(?<!\\)'", value):
            errors.append("%s: %s unescaped apostrophe" % (locale, POPUP))

            continue

        if '"' in value:
            errors.append("%s: %s straight double quote" % (locale, POPUP))

            continue

        if "\n" in value:
            errors.append("%s: %s literal newline" % (locale, POPUP))

            continue

        if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", value):
            errors.append("%s: %s bare ampersand" % (locale, POPUP))

            continue

        if text.count("</resources>") != 1:
            errors.append("%s: expected one </resources>" % locale)

            continue

        text = text.replace(
            "</resources>",
            '    <string name="%s">%s</string>\n</resources>' % (POPUP, value),
            1,
        )

        pending[path] = text

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation ---------------------------------------------------
    problems = []

    if len(pending) != len(LOCALES):
        problems.append("prepared %d locales, expected %d" % (len(pending), len(LOCALES)))

    for locale in LOCALES:
        text = pending[path_for(locale)]

        if body(text, HEADING) != HEADING_TO[locale]:
            problems.append("%s: %s did not take" % (locale, HEADING))

        # The author writes IMD+ closed up. A stray "IMD +" means a locale was missed.
        if "IMD +" in body(text, HEADING):
            problems.append("%s: %s still has a space before the plus" % (locale, HEADING))

        if body(text, POPUP) != POPUP_TEXT[locale]:
            problems.append("%s: %s did not take" % (locale, POPUP))

        # The popup has to name the section as this locale actually spells it.
        section = body(text, "section_app_functions")

        if section is None:
            problems.append("%s: section_app_functions absent" % locale)
        elif section != SECTION_ECHO[locale]:
            problems.append(
                "%s: section_app_functions reads %r, not the %r this popup was written against"
                % (locale, section, SECTION_ECHO[locale])
            )
        elif locale == "values":
            # Same words, the author's order. Not a substring test - see SECTION_ECHO.
            if sorted(section.lower().split()) != sorted("IMD default settings".lower().split()):
                problems.append("values: the heading and the popup no longer name the same thing")

            if "IMD default settings" not in body(text, POPUP):
                problems.append("values: %s does not name the section" % POPUP)
        elif SECTION_ECHO[locale] not in body(text, POPUP):
            problems.append("%s: %s does not name the section" % (locale, POPUP))

        # Nothing this script touched may break the resource parser.
        for m in re.finditer(r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S):
            if m.group(1) not in (HEADING, POPUP):
                continue

            if "\n" in m.group(2):
                problems.append("%s: %s literal newline" % (locale, m.group(1)))

            if re.search(r"(?<!\\)'", m.group(2)):
                problems.append("%s: %s unescaped apostrophe" % (locale, m.group(1)))

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print("\nrenamed %s in %d locales" % (HEADING, len(LOCALES)))
    print("added %s to %d locales" % (POPUP, len(LOCALES)))
    print("\nheading, per locale:")

    for locale in LOCALES:
        print("   %-18s %s" % (locale, HEADING_TO[locale]))

    print("\npopup, default locale:")
    print("   " + POPUP_TEXT["values"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
