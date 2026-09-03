#!/usr/bin/env python3
"""
Wording for the failure-channel rename, the busy tile label and the split logics line.

Three modules are touched, which is why this one carries its own resource root per key:
`alert_notification_channel` lives in :framework:notification-manager (the module that
registers the channel), `hide_tile_working` in :app (the module that owns the tile, and under
non-transitive R the only module whose ids it can read by name), and the About strings in
:feature:settings.

Asserts before it writes, as the others do.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

NOTIFICATION_RES = os.path.join(
    ROOT, "framework", "notification-manager", "src", "main", "res"
)
APP_RES = os.path.join(ROOT, "app", "src", "main", "res")
SETTINGS_RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

# key -> (resource root, action, {locale: value})
REPLACE = {
    "alert_notification_channel": (NOTIFICATION_RES, {
        "values": "IMD failures",
        "values-ar": "أعطال IMD",
        "values-b+pt+BR": "Falhas do IMD",
        "values-b+zh+Hans": "IMD 故障",
        "values-de": "IMD-Fehler",
        "values-es": "Errores de IMD",
        "values-fr": "Échecs IMD",
        "values-hi": "IMD विफलताएँ",
        "values-ja": "IMD の失敗",
        "values-ko": "IMD 실패",
        "values-ru": "Сбои IMD",
    }),
    # The link is the title alone now; the aside below it is its own string.
    "about_logics": (SETTINGS_RES, {
        "values": "IMD app Logics",
        "values-ar": "مخططات عمل تطبيق IMD",
        "values-b+pt+BR": "Lógicas do app IMD",
        "values-b+zh+Hans": "IMD 应用逻辑图",
        "values-de": "IMD-App-Logiken",
        "values-es": "Lógicas de la app IMD",
        "values-fr": "Logiques de l\\'application IMD",
        "values-hi": "IMD ऐप लॉजिक्स",
        "values-ja": "IMD アプリのロジック",
        "values-ko": "IMD 앱 로직",
        "values-ru": "Логика приложения IMD",
    }),
    # "(Blanc)" dropped at the author's request; the line is plain text now either way.
    # Default locale only: this key is translatable="false", so it exists in values/ alone.
    "about_fork_author": (SETTINGS_RES, {"values": "JackEblan"}),
}

ADD = {
    "about_logics_note": (SETTINGS_RES, {
        "values": "(developer lost his sanity making-testing-forking these🌙☕🥲)",
        "values-ar": "(فقد المطوّر صوابه وهو يصنعها ويختبرها ويفرّعها🌙☕🥲)",
        "values-b+pt+BR": "(o desenvolvedor perdeu a sanidade fazendo-testando-forkando isso🌙☕🥲)",
        "values-b+zh+Hans": "(开发者在制作—测试—分叉这些的过程中失去了理智🌙☕🥲)",
        "values-de": (
            "(der Entwickler hat beim Bauen-Testen-Forken den Verstand verloren🌙☕🥲)"
        ),
        "values-es": (
            "(el desarrollador perdió la cordura creando-probando-bifurcando esto🌙☕🥲)"
        ),
        "values-fr": (
            "(le développeur y a perdu la raison à les faire-tester-forker🌙☕🥲)"
        ),
        "values-hi": "(इन्हें बनाते-परखते-फोर्क करते हुए डेवलपर का दिमाग़ चल गया🌙☕🥲)",
        "values-ja": "(開発者は作る・試す・フォークするうちに正気を失いました🌙☕🥲)",
        "values-ko": "(개발자는 만들고-시험하고-포크하다 제정신을 잃었습니다🌙☕🥲)",
        "values-ru": "(разработчик сошёл с ума, делая-проверяя-форкая всё это🌙☕🥲)",
    }),
    "hide_tile_working": (APP_RES, {
        "values": "Hiding settings…",
        "values-ar": "جارٍ إخفاء الإعدادات…",
        "values-b+pt+BR": "Ocultando configurações…",
        "values-b+zh+Hans": "正在隐藏设置…",
        "values-de": "Einstellungen werden ausgeblendet…",
        "values-es": "Ocultando ajustes…",
        "values-fr": "Masquage des paramètres…",
        "values-hi": "सेटिंग्स छिपाई जा रही हैं…",
        "values-ja": "設定を非表示にしています…",
        "values-ko": "설정을 숨기는 중…",
        "values-ru": "Скрытие настроек…",
    }),
}


def path_for(res, locale):
    return os.path.join(res, locale, "strings.xml")


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}

    def load(path):
        if path not in pending:
            if not os.path.exists(path):
                return None

            pending[path] = open(path, encoding="utf-8").read()

        return pending[path]

    for key, (res, values) in REPLACE.items():
        if not set(values) <= set(LOCALES):
            errors.append("REPLACE %s: unknown locale" % key)

            continue

        for locale in values:
            path = path_for(res, locale)
            text = load(path)

            if text is None:
                errors.append("%s/%s: file missing" % (key, locale))

                continue

            old = body(text, key)

            if old is None:
                errors.append("REPLACE %s/%s: key absent" % (key, locale))

                continue

            if re.search(r"(?<!\\)'", values[locale]):
                errors.append("REPLACE %s/%s: unescaped apostrophe" % (key, locale))

                continue

            # The attribute list is preserved: about_fork_author carries translatable="false".
            pending[path] = re.sub(
                r'(<string name="%s"((?: [^>]*)?)>).*?(</string>)' % re.escape(key),
                lambda m: m.group(1) + values[locale] + m.group(3),
                text,
                count=1,
                flags=re.S,
            )

    for key, (res, values) in ADD.items():
        # A translated key must reach every locale; an untranslatable one names its own.
        if len(values) != 1 and set(values) != set(LOCALES):
            errors.append("ADD %s: locale set mismatch" % key)

            continue

        for locale in values:
            path = path_for(res, locale)
            text = load(path)

            if text is None:
                errors.append("%s/%s: file missing" % (key, locale))

                continue

            if ('name="%s"' % key) in text:
                errors.append("ADD %s/%s: already present" % (key, locale))

                continue

            if re.search(r"(?<!\\)'", values[locale]):
                errors.append("ADD %s/%s: unescaped apostrophe" % (key, locale))

                continue

            if text.count("</resources>") != 1:
                errors.append("%s/%s: expected one </resources>" % (key, locale))

                continue

            pending[path] = text.replace(
                "</resources>",
                '    <string name="%s">%s</string>\n</resources>' % (key, values[locale]),
                1,
            )

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    problems = []

    for key, (res, values) in list(REPLACE.items()) + list(ADD.items()):
        for locale in values:
            got = body(pending[path_for(res, locale)], key)

            if got != values[locale]:
                problems.append("%s/%s: value does not match" % (key, locale))

    for path, text in pending.items():
        for m in re.finditer(r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S):
            if "\n" in m.group(2):
                problems.append("%s: %s literal newline" % (path, m.group(1)))

            if re.search(r"(?<!\\)'", m.group(2)):
                problems.append("%s: %s unescaped apostrophe" % (path, m.group(1)))

    # about_fork_author is translatable="false"; the attribute must have survived the rewrite.
    fork = pending[path_for(SETTINGS_RES, "values")]

    if 'name="about_fork_author" translatable="false"' not in fork:
        problems.append("about_fork_author lost its translatable=\"false\"")

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print(
        "\nreplaced %d key(s), added %d key(s), across %d locales in %d file(s)"
        % (len(REPLACE), len(ADD), len(LOCALES), len(pending))
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
