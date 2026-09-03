#!/usr/bin/env python3
"""
The wording batch that goes with the IMD+ section, the requirement buttons and the Shizuku
service notice.

REPLACE existing keys, ADD new ones, across all eleven locales. Asserts before it writes:
every key must exist (or not) as expected in every locale, every English value the user
supplied must land verbatim, and no value may carry an unescaped apostrophe.
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

# ---------------------------------------------------------------- replacements

REPLACE = {
    "auto_hide": {
        "values": "Auto hide settings",
        "values-ar": "الإخفاء التلقائي للإعدادات",
        "values-b+pt+BR": "Ocultar configurações automaticamente",
        "values-b+zh+Hans": "自动隐藏设置",
        "values-de": "Einstellungen automatisch ausblenden",
        "values-es": "Ocultar ajustes automáticamente",
        "values-fr": "Masquage automatique des paramètres",
        "values-hi": "सेटिंग्स अपने आप छिपाएँ",
        "values-ja": "設定の自動非表示",
        "values-ko": "설정 자동 숨기기",
        "values-ru": "Автоскрытие настроек",
    },
    "auto_hide_title": {
        "values": "Auto hide settings",
        "values-ar": "الإخفاء التلقائي للإعدادات",
        "values-b+pt+BR": "Ocultar configurações automaticamente",
        "values-b+zh+Hans": "自动隐藏设置",
        "values-de": "Einstellungen automatisch ausblenden",
        "values-es": "Ocultar ajustes automáticamente",
        "values-fr": "Masquage automatique des paramètres",
        "values-hi": "सेटिंग्स अपने आप छिपाएँ",
        "values-ja": "設定の自動非表示",
        "values-ko": "설정 자동 숨기기",
        "values-ru": "Автоскрытие настроек",
    },
    "auto_hide_flow_7": {
        "values": "You press the notification or Revert function is used.",
        "values-ar": "تضغط على الإشعار أو تُستخدَم وظيفة الاستعادة.",
        "values-b+pt+BR": "Você toca na notificação ou a função Reverter é usada.",
        "values-b+zh+Hans": "你点击通知，或者使用了还原功能。",
        "values-de": "Du tippst auf die Benachrichtigung, oder die Revert-Funktion wird genutzt.",
        "values-es": "Tocas la notificación o se usa la función Revertir.",
        "values-fr": "Vous appuyez sur la notification ou la fonction Rétablir est utilisée.",
        "values-hi": "आप सूचना दबाते हैं या रिवर्ट फ़ंक्शन का उपयोग होता है।",
        "values-ja": "通知を押すか、復元機能が使われます。",
        "values-ko": "알림을 누르거나 되돌리기 기능이 사용됩니다.",
        "values-ru": "Вы нажимаете уведомление, или используется функция возврата.",
    },
    "accessibility_service_own": {
        "values": "IMD\\'s own detector - managed by IMD+",
        "values-ar": "كاشف IMD الخاص - تديره ميزة IMD+",
        "values-b+pt+BR": "Detector do próprio IMD - gerenciado pelo IMD+",
        "values-b+zh+Hans": "IMD 自己的检测器 - 由 IMD+ 管理",
        "values-de": "IMDs eigener Detektor - von IMD+ verwaltet",
        "values-es": "Detector propio de IMD - gestionado por IMD+",
        "values-fr": "Détecteur propre à IMD - géré par IMD+",
        "values-hi": "IMD का अपना डिटेक्टर - IMD+ द्वारा प्रबंधित",
        "values-ja": "IMD 自身の検出サービス - IMD+ が管理",
        "values-ko": "IMD 자체 감지기 - IMD+가 관리",
        "values-ru": "Собственный детектор IMD - управляется IMD+",
    },
    "restart_shizuku_service": {
        "values": "Restart Shizuku service (for Memory function mechanism)",
        "values-ar": "إعادة تشغيل خدمة Shizuku (لآلية وظيفة الذاكرة)",
        "values-b+pt+BR": "Reiniciar o serviço Shizuku (para o mecanismo da função Memória)",
        "values-b+zh+Hans": "重启 Shizuku 服务（用于记忆功能机制）",
        "values-de": "Shizuku-Dienst neu starten (für den Speicherfunktions-Mechanismus)",
        "values-es": "Reiniciar el servicio Shizuku (para el mecanismo de la función Memoria)",
        "values-fr": "Redémarrer le service Shizuku (pour le mécanisme de la fonction Mémoire)",
        "values-hi": "Shizuku सेवा फिर से शुरू करें (मेमोरी फ़ंक्शन तंत्र के लिए)",
        "values-ja": "Shizuku サービスを再起動（メモリー機能の仕組み用）",
        "values-ko": "Shizuku 서비스 재시작 (메모리 기능 방식용)",
        "values-ru": "Перезапуск службы Shizuku (для механизма функции памяти)",
    },
    "restart_shizuku_service_description": {
        "values": "On reverting USB debugging, auto restart Shizuku service via intents",
        "values-ar": "عند استعادة تصحيح USB، أعد تشغيل خدمة Shizuku تلقائيًا عبر الـ intents",
        "values-b+pt+BR": "Ao reverter a depuração USB, reiniciar o serviço Shizuku automaticamente via intents",
        "values-b+zh+Hans": "还原 USB 调试时，通过 intent 自动重启 Shizuku 服务",
        "values-de": "Beim Zurücksetzen des USB-Debuggings den Shizuku-Dienst automatisch per Intent neu starten",
        "values-es": "Al revertir la depuración USB, reiniciar automáticamente el servicio Shizuku mediante intents",
        "values-fr": "Lors du rétablissement du débogage USB, redémarrer automatiquement le service Shizuku via des intents",
        "values-hi": "USB डिबगिंग वापस करते समय, intents के ज़रिए Shizuku सेवा अपने आप फिर से शुरू करें",
        "values-ja": "USB デバッグを戻すときに、インテント経由で Shizuku サービスを自動的に再起動します",
        "values-ko": "USB 디버깅을 되돌릴 때 인텐트로 Shizuku 서비스를 자동 재시작",
        "values-ru": "При возврате отладки по USB автоматически перезапускать службу Shizuku через intents",
    },
}

# ---------------------------------------------------------------- additions

ADD = {
    "section_imd_plus": {
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
    },
    "auto_hide_how_it_works_button": {
        "values": "HOW THIS WORKS (⚠️ please read)",
        "values-ar": "‏كيف يعمل هذا (⚠️ يُرجى القراءة)",
        "values-b+pt+BR": "COMO ISSO FUNCIONA (⚠️ leia por favor)",
        "values-b+zh+Hans": "工作原理（⚠️ 请阅读）",
        "values-de": "SO FUNKTIONIERT ES (⚠️ bitte lesen)",
        "values-es": "CÓMO FUNCIONA (⚠️ léelo, por favor)",
        "values-fr": "COMMENT ÇA MARCHE (⚠️ à lire)",
        "values-hi": "यह कैसे काम करता है (⚠️ कृपया पढ़ें)",
        "values-ja": "しくみ（⚠️ 必ずお読みください）",
        "values-ko": "작동 방식 (⚠️ 꼭 읽어 주세요)",
        "values-ru": "КАК ЭТО РАБОТАЕТ (⚠️ прочтите)",
    },
    "auto_hide_battery_disable": {
        "values": "Disable battery optimisations",
        "values-ar": "تعطيل تحسينات البطارية",
        "values-b+pt+BR": "Desativar otimizações de bateria",
        "values-b+zh+Hans": "关闭电池优化",
        "values-de": "Akkuoptimierung deaktivieren",
        "values-es": "Desactivar optimizaciones de batería",
        "values-fr": "Désactiver les optimisations de batterie",
        "values-hi": "बैटरी ऑप्टिमाइज़ेशन बंद करें",
        "values-ja": "電池の最適化を無効にする",
        "values-ko": "배터리 최적화 해제",
        "values-ru": "Отключить оптимизацию батареи",
    },
    "auto_hide_notification_grant": {
        "values": "Grant notification permission",
        "values-ar": "منح إذن الإشعارات",
        "values-b+pt+BR": "Conceder permissão de notificação",
        "values-b+zh+Hans": "授予通知权限",
        "values-de": "Benachrichtigungsberechtigung erteilen",
        "values-es": "Conceder permiso de notificaciones",
        "values-fr": "Accorder l\\'autorisation de notification",
        "values-hi": "सूचना अनुमति दें",
        "values-ja": "通知の権限を許可",
        "values-ko": "알림 권한 허용",
        "values-ru": "Выдать разрешение на уведомления",
    },
    "auto_hide_notification_granted": {
        "values": "Permission granted",
        "values-ar": "تم منح الإذن",
        "values-b+pt+BR": "Permissão concedida",
        "values-b+zh+Hans": "已授予权限",
        "values-de": "Berechtigung erteilt",
        "values-es": "Permiso concedido",
        "values-fr": "Autorisation accordée",
        "values-hi": "अनुमति दे दी गई",
        "values-ja": "権限を許可済み",
        "values-ko": "권한 허용됨",
        "values-ru": "Разрешение выдано",
    },
    "auto_hide_notification_denied": {
        "values": "Permission denied",
        "values-ar": "تم رفض الإذن",
        "values-b+pt+BR": "Permissão negada",
        "values-b+zh+Hans": "权限被拒绝",
        "values-de": "Berechtigung verweigert",
        "values-es": "Permiso denegado",
        "values-fr": "Autorisation refusée",
        "values-hi": "अनुमति अस्वीकृत",
        "values-ja": "権限が拒否されました",
        "values-ko": "권한 거부됨",
        "values-ru": "Разрешение отклонено",
    },
    "shizuku_service_notice_watchdog": {
        "values": (
            "If using thedjchi Shizuku, please disable Watchdog in Shizuku app settings, "
            "otherwise it will not work (IMD uses intents to start-stop Shizuku; If you keep "
            "Watchdog on it won\\'t allow IMD to hide USB debugging)"
        ),
        "values-ar": (
            "إذا كنت تستخدم Shizuku من thedjchi، فيرجى تعطيل Watchdog في إعدادات تطبيق "
            "Shizuku، وإلا فلن يعمل (يستخدم IMD الـ intents لتشغيل وإيقاف Shizuku؛ وإذا "
            "أبقيت Watchdog مفعّلًا فلن يسمح لـ IMD بإخفاء تصحيح USB)"
        ),
        "values-b+pt+BR": (
            "Se estiver usando o Shizuku do thedjchi, desative o Watchdog nas configurações "
            "do app Shizuku, caso contrário não vai funcionar (o IMD usa intents para iniciar "
            "e parar o Shizuku; com o Watchdog ligado ele não deixa o IMD ocultar a "
            "depuração USB)"
        ),
        "values-b+zh+Hans": (
            "如果使用 thedjchi 版 Shizuku，请在 Shizuku 应用设置中关闭 Watchdog，否则无法生效"
            "（IMD 通过 intent 启动和停止 Shizuku；保持 Watchdog 开启会导致 IMD 无法隐藏 "
            "USB 调试）"
        ),
        "values-de": (
            "Bei Verwendung von thedjchis Shizuku bitte den Watchdog in den Shizuku-"
            "App-Einstellungen deaktivieren, sonst funktioniert es nicht (IMD startet und "
            "stoppt Shizuku per Intent; bleibt der Watchdog an, lässt er IMD das "
            "USB-Debugging nicht ausblenden)"
        ),
        "values-es": (
            "Si usas el Shizuku de thedjchi, desactiva Watchdog en los ajustes de la "
            "aplicación Shizuku; de lo contrario no funcionará (IMD usa intents para iniciar "
            "y detener Shizuku; con Watchdog activado no dejará que IMD oculte la depuración "
            "USB)"
        ),
        "values-fr": (
            "Si vous utilisez le Shizuku de thedjchi, désactivez Watchdog dans les réglages "
            "de l\\'application Shizuku, sinon cela ne fonctionnera pas (IMD utilise des "
            "intents pour démarrer et arrêter Shizuku ; si Watchdog reste actif, il "
            "empêchera IMD de masquer le débogage USB)"
        ),
        "values-hi": (
            "अगर thedjchi वाला Shizuku इस्तेमाल कर रहे हैं, तो Shizuku ऐप सेटिंग्स में Watchdog बंद "
            "करें, वरना यह काम नहीं करेगा (IMD, Shizuku को शुरू और बंद करने के लिए intents का "
            "उपयोग करता है; Watchdog चालू रहने पर वह IMD को USB डिबगिंग छिपाने नहीं देगा)"
        ),
        "values-ja": (
            "thedjchi 版 Shizuku を使う場合は、Shizuku アプリの設定で Watchdog を無効にして"
            "ください。無効にしないと動作しません（IMD はインテントで Shizuku を起動・停止"
            "します。Watchdog を有効のままにすると、IMD は USB デバッグを隠せません）"
        ),
        "values-ko": (
            "thedjchi Shizuku를 사용한다면 Shizuku 앱 설정에서 Watchdog을 꺼 주세요. 그렇지 "
            "않으면 동작하지 않습니다(IMD는 인텐트로 Shizuku를 시작·중지합니다. Watchdog을 "
            "켜 두면 IMD가 USB 디버깅을 숨길 수 없습니다)"
        ),
        "values-ru": (
            "Если вы используете Shizuku от thedjchi, отключите Watchdog в настройках "
            "приложения Shizuku, иначе это не сработает (IMD запускает и останавливает "
            "Shizuku через intents; при включённом Watchdog он не даст IMD скрыть отладку "
            "по USB)"
        ),
    },
    "shizuku_service_notice_shevery": {
        "values": (
            "If using Shevery, please enable ErrorReporting in Shevery app settings, "
            "otherwise IMD will not be able to restore Shizuku service on unhiding."
        ),
        "values-ar": (
            "إذا كنت تستخدم Shevery، فيرجى تفعيل ErrorReporting في إعدادات تطبيق Shevery، "
            "وإلا فلن يتمكن IMD من استعادة خدمة Shizuku عند إلغاء الإخفاء."
        ),
        "values-b+pt+BR": (
            "Se estiver usando o Shevery, ative o ErrorReporting nas configurações do app "
            "Shevery, caso contrário o IMD não conseguirá restaurar o serviço Shizuku ao "
            "reexibir."
        ),
        "values-b+zh+Hans": (
            "如果使用 Shevery，请在 Shevery 应用设置中启用 ErrorReporting，否则 IMD 在取消"
            "隐藏时将无法恢复 Shizuku 服务。"
        ),
        "values-de": (
            "Bei Verwendung von Shevery bitte ErrorReporting in den Shevery-App-Einstellungen "
            "aktivieren, sonst kann IMD den Shizuku-Dienst beim Einblenden nicht "
            "wiederherstellen."
        ),
        "values-es": (
            "Si usas Shevery, activa ErrorReporting en los ajustes de la aplicación Shevery; "
            "de lo contrario IMD no podrá restaurar el servicio Shizuku al volver a mostrar."
        ),
        "values-fr": (
            "Si vous utilisez Shevery, activez ErrorReporting dans les réglages de "
            "l\\'application Shevery, sinon IMD ne pourra pas rétablir le service Shizuku "
            "lors du démasquage."
        ),
        "values-hi": (
            "अगर Shevery इस्तेमाल कर रहे हैं, तो Shevery ऐप सेटिंग्स में ErrorReporting चालू करें, "
            "वरना अनहाइड करते समय IMD, Shizuku सेवा बहाल नहीं कर पाएगा।"
        ),
        "values-ja": (
            "Shevery を使う場合は、Shevery アプリの設定で ErrorReporting を有効にしてください。"
            "有効にしないと、再表示時に IMD は Shizuku サービスを復元できません。"
        ),
        "values-ko": (
            "Shevery를 사용한다면 Shevery 앱 설정에서 ErrorReporting을 켜 주세요. 그렇지 "
            "않으면 숨김 해제 시 IMD가 Shizuku 서비스를 복원할 수 없습니다."
        ),
        "values-ru": (
            "Если вы используете Shevery, включите ErrorReporting в настройках приложения "
            "Shevery, иначе IMD не сможет восстановить службу Shizuku при отмене скрытия."
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

    # --- replacements -------------------------------------------------
    for key, values in REPLACE.items():
        if set(values) != set(LOCALES):
            errors.append("REPLACE %s: locale set mismatch" % key)

            continue

        for locale in LOCALES:
            path = path_for(locale)
            text = pending[path]

            old = body(text, key)

            if old is None:
                errors.append("REPLACE %s/%s: key absent" % (key, locale))

                continue

            new = values[locale]

            if re.search(r"(?<!\\)'", new):
                errors.append("REPLACE %s/%s: unescaped apostrophe" % (key, locale))

                continue

            pending[path] = text.replace(
                '<string name="%s">%s</string>' % (key, old),
                '<string name="%s">%s</string>' % (key, new),
                1,
            )

    # --- additions ----------------------------------------------------
    for locale in LOCALES:
        path = path_for(locale)
        text = pending[path]

        block = ""

        for key, values in ADD.items():
            if set(values) != set(LOCALES):
                errors.append("ADD %s: locale set mismatch" % key)

                continue

            if ('name="%s"' % key) in text:
                errors.append("ADD %s/%s: already present" % (key, locale))

                continue

            value = values[locale]

            if re.search(r"(?<!\\)'", value):
                errors.append("ADD %s/%s: unescaped apostrophe" % (key, locale))

                continue

            block += '    <string name="%s">%s</string>\n' % (key, value)

        if text.count("</resources>") != 1:
            errors.append("%s: expected one </resources>" % locale)

            continue

        pending[path] = text.replace("</resources>", block + "</resources>", 1)

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation ---------------------------------------------------
    problems = []

    for locale in LOCALES:
        text = pending[path_for(locale)]

        for key in list(REPLACE) + list(ADD):
            got = body(text, key)

            if got is None:
                problems.append("%s: %s missing after write" % (locale, key))

                continue

            want = (REPLACE.get(key) or ADD.get(key))[locale]

            if got != want:
                problems.append("%s: %s does not match intended value" % (locale, key))

        # No literal newlines, and no unescaped apostrophes, anywhere in the file.
        for m in re.finditer(r'<string name="([^"]+)"(?: [^>]*)?>(.*?)</string>', text, re.S):
            if "\n" in m.group(2):
                problems.append("%s: %s holds a literal newline" % (locale, m.group(1)))

            if re.search(r"(?<!\\)'", m.group(2)):
                problems.append("%s: %s unescaped apostrophe" % (locale, m.group(1)))

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print(
        "\nreplaced %d key(s), added %d key(s), across %d locales"
        % (len(REPLACE), len(ADD), len(LOCALES))
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
