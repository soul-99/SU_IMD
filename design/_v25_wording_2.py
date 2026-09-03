#!/usr/bin/env python3
"""
Second wording pass for the IMD+ polish round.

RENAME `auto_hide_notification_granted` to `auto_hide_permission_granted`: the battery button
now reports the same state, and a key named after notifications used by both would be a trap
for the next person to read it. Same value, new key.

ADD `auto_hide_blocked_reverts`, the popup both halves of the IMD+ row raise while a revert is
outstanding.

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

RENAME = ("auto_hide_notification_granted", "auto_hide_permission_granted")

ADD = {
    "auto_hide_blocked_reverts": {
        "values": "Please perform all pending reverts before managing IMD+ settings.",
        "values-ar": "يُرجى تنفيذ جميع عمليات الاستعادة المعلّقة قبل إدارة إعدادات IMD+.",
        "values-b+pt+BR": (
            "Conclua todas as reversões pendentes antes de gerenciar as configurações do IMD+."
        ),
        "values-b+zh+Hans": "请先完成所有待处理的还原，然后再管理 IMD+ 设置。",
        "values-de": (
            "Bitte führe alle ausstehenden Reverts durch, bevor du die IMD+-Einstellungen "
            "verwaltest."
        ),
        "values-es": (
            "Realiza todas las reversiones pendientes antes de gestionar los ajustes de IMD+."
        ),
        "values-fr": (
            "Veuillez effectuer tous les rétablissements en attente avant de gérer les "
            "paramètres IMD+."
        ),
        "values-hi": "IMD+ सेटिंग्स प्रबंधित करने से पहले कृपया सभी लंबित रिवर्ट पूरे करें।",
        "values-ja": "IMD+ の設定を操作する前に、保留中の復元をすべて実行してください。",
        "values-ko": "IMD+ 설정을 관리하기 전에 대기 중인 되돌리기를 모두 완료해 주세요.",
        "values-ru": (
            "Выполните все ожидающие возвраты, прежде чем управлять настройками IMD+."
        ),
    },
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

        pending[path] = open(path, encoding="utf-8").read()

    if errors:
        print("\nREFUSED:\n  " + "\n  ".join(errors))

        return 1

    old_key, new_key = RENAME

    for locale in LOCALES:
        path = path_for(locale)
        text = pending[path]

        # --- rename ---
        value = body(text, old_key)

        if value is None:
            errors.append("%s: %s absent, cannot rename" % (locale, old_key))
        elif body(text, new_key) is not None:
            errors.append("%s: %s already exists" % (locale, new_key))
        else:
            text = text.replace(
                '<string name="%s">%s</string>' % (old_key, value),
                '<string name="%s">%s</string>' % (new_key, value),
                1,
            )

        # --- additions ---
        block = ""

        for key, values in ADD.items():
            if set(values) != set(LOCALES):
                errors.append("ADD %s: locale set mismatch" % key)

                continue

            if ('name="%s"' % key) in text:
                errors.append("%s: %s already present" % (locale, key))

                continue

            if re.search(r"(?<!\\)'", values[locale]):
                errors.append("%s: %s unescaped apostrophe" % (locale, key))

                continue

            block += '    <string name="%s">%s</string>\n' % (key, values[locale])

        if text.count("</resources>") != 1:
            errors.append("%s: expected one </resources>" % locale)

            continue

        pending[path] = text.replace("</resources>", block + "</resources>", 1)

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation ---
    problems = []

    for locale in LOCALES:
        text = pending[path_for(locale)]

        if body(text, old_key) is not None:
            problems.append("%s: %s survived the rename" % (locale, old_key))

        if body(text, new_key) is None:
            problems.append("%s: %s missing after rename" % (locale, new_key))

        for key, values in ADD.items():
            if body(text, key) != values[locale]:
                problems.append("%s: %s does not match intended value" % (locale, key))

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

    print(
        "\nrenamed %s -> %s and added %d key(s), across %d locales"
        % (old_key, new_key, len(ADD), len(LOCALES))
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
