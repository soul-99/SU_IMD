#!/usr/bin/env python3
"""
Strings for the TEMPORARY diagnostic log (see common/DiagnosticLog.kt).

Four keys, in all eleven locales, appended to feature/settings. They exist for one build:
delete this script's four keys along with DiagnosticLog.kt, DiagnosticLogDialog.kt and the
button in SettingsScreen once the "IMD+ row invisible until clear data" report is settled.

Asserts before it writes, per the project convention: every locale must be present, every key
must be absent to begin with, and no value may carry an unescaped apostrophe.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

SETTINGS_RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

KEYS = [
    "diagnostic_log_view",
    "diagnostic_log_title",
    "diagnostic_log_copy",
    "diagnostic_log_description",
]

ADD = {
    "values": {
        "diagnostic_log_view": "Diagnostic log",
        "diagnostic_log_title": "Diagnostic log",
        "diagnostic_log_copy": "Copy",
        "diagnostic_log_description": (
            "What this app recorded since it started. Temporary, for reporting the missing "
            "IMD+ row. Copy it and paste it into the report."
        ),
    },
    "values-ar": {
        "diagnostic_log_view": "سجل التشخيص",
        "diagnostic_log_title": "سجل التشخيص",
        "diagnostic_log_copy": "نسخ",
        "diagnostic_log_description": (
            "ما سجّله التطبيق منذ بدء تشغيله. مؤقت، لأجل الإبلاغ عن اختفاء صف IMD+. "
            "انسخه وألصقه في التقرير."
        ),
    },
    "values-b+pt+BR": {
        "diagnostic_log_view": "Registro de diagnóstico",
        "diagnostic_log_title": "Registro de diagnóstico",
        "diagnostic_log_copy": "Copiar",
        "diagnostic_log_description": (
            "O que o app registrou desde que iniciou. Temporário, para relatar a linha IMD+ "
            "ausente. Copie e cole no relato."
        ),
    },
    "values-b+zh+Hans": {
        "diagnostic_log_view": "诊断日志",
        "diagnostic_log_title": "诊断日志",
        "diagnostic_log_copy": "复制",
        "diagnostic_log_description": (
            "本应用自启动以来记录的内容。这是临时功能，用于反馈 IMD+ 条目缺失的问题。"
            "请复制后粘贴到反馈中。"
        ),
    },
    "values-de": {
        "diagnostic_log_view": "Diagnoseprotokoll",
        "diagnostic_log_title": "Diagnoseprotokoll",
        "diagnostic_log_copy": "Kopieren",
        "diagnostic_log_description": (
            "Was die App seit dem Start aufgezeichnet hat. Vorübergehend, um die fehlende "
            "IMD+-Zeile zu melden. Kopieren und in den Bericht einfügen."
        ),
    },
    "values-es": {
        "diagnostic_log_view": "Registro de diagnóstico",
        "diagnostic_log_title": "Registro de diagnóstico",
        "diagnostic_log_copy": "Copiar",
        "diagnostic_log_description": (
            "Lo que la aplicación registró desde que se inició. Temporal, para informar de "
            "la fila IMD+ que falta. Cópialo y pégalo en el informe."
        ),
    },
    "values-fr": {
        "diagnostic_log_view": "Journal de diagnostic",
        "diagnostic_log_title": "Journal de diagnostic",
        "diagnostic_log_copy": "Copier",
        "diagnostic_log_description": (
            "Ce que l\\'application a enregistré depuis son démarrage. Temporaire, pour "
            "signaler la ligne IMD+ manquante. Copiez-le et collez-le dans le rapport."
        ),
    },
    "values-hi": {
        "diagnostic_log_view": "डायग्नोस्टिक लॉग",
        "diagnostic_log_title": "डायग्नोस्टिक लॉग",
        "diagnostic_log_copy": "कॉपी करें",
        "diagnostic_log_description": (
            "ऐप शुरू होने के बाद से उसने जो दर्ज किया। यह अस्थायी है, गायब IMD+ पंक्ति की "
            "रिपोर्ट करने के लिए। इसे कॉपी करके रिपोर्ट में चिपकाएँ।"
        ),
    },
    "values-ja": {
        "diagnostic_log_view": "診断ログ",
        "diagnostic_log_title": "診断ログ",
        "diagnostic_log_copy": "コピー",
        "diagnostic_log_description": (
            "アプリの起動以降に記録された内容です。IMD+ の行が表示されない問題を報告する"
            "ための一時的な機能です。コピーして報告に貼り付けてください。"
        ),
    },
    "values-ko": {
        "diagnostic_log_view": "진단 로그",
        "diagnostic_log_title": "진단 로그",
        "diagnostic_log_copy": "복사",
        "diagnostic_log_description": (
            "앱이 시작된 뒤 기록한 내용입니다. IMD+ 항목이 보이지 않는 문제를 알리기 위한 "
            "임시 기능입니다. 복사해 보고에 붙여 넣으세요."
        ),
    },
    "values-ru": {
        "diagnostic_log_view": "Журнал диагностики",
        "diagnostic_log_title": "Журнал диагностики",
        "diagnostic_log_copy": "Копировать",
        "diagnostic_log_description": (
            "Что приложение записало с момента запуска. Временно, для сообщения о пропавшей "
            "строке IMD+. Скопируйте и вставьте в сообщение."
        ),
    },
}


def path_for(locale):
    return os.path.join(SETTINGS_RES, locale, "strings.xml")


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}

    for locale, additions in ADD.items():
        path = path_for(locale)

        if not os.path.exists(path):
            errors.append("%s: strings.xml missing" % locale)

            continue

        with open(path, encoding="utf-8") as handle:
            text = handle.read()

        if set(additions) != set(KEYS):
            errors.append("%s: key set does not match KEYS" % locale)

            continue

        for key, value in additions.items():
            if ('name="%s"' % key) in text:
                errors.append("%s: %s already present" % (locale, key))

            if re.search(r"(?<!\\)'", value):
                errors.append("%s: %s carries an unescaped apostrophe" % (locale, key))

        if text.count("</resources>") != 1:
            errors.append("%s: expected exactly one </resources>" % locale)

            continue

        block = "".join(
            '    <string name="%s">%s</string>\n' % (key, additions[key]) for key in KEYS
        )

        pending[path] = text.replace(
            "</resources>",
            "\n    <!-- TEMPORARY: diagnostic log, remove with DiagnosticLog.kt -->\n"
            + block
            + "</resources>",
        )

    if errors:
        print("\nREFUSED, nothing written:")

        for error in errors:
            print("  %s" % error)

        return 1

    if len(pending) != 11:
        print("\nREFUSED: %d locales resolved, expected 11" % len(pending))

        return 1

    for path, text in sorted(pending.items()):
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)

    print("\nadded %d keys to %d locales" % (len(KEYS), len(pending)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
