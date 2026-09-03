#!/usr/bin/env python3
"""
r12 strings: Auto unhide settings.

Adds every string the new feature needs - 40 in feature/settings and 2 in
framework/notification-manager - across all 11 locales.

Five of them are the author's own English and go in **verbatim**:

    auto_unhide          "Auto unhide settings"
    auto_unhide_setup    "click to setup"
    auto_unhide_intro    the two numbered lines, including the missing full stop on line 2
    auto_unhide_channel  "Auto unhide settings service"
    auto_unhide_running  "Auto unhide service running"

Everything else was drafted to match the register of the existing IMD+ rows: a short title
and a lowercase note beginning "to ...".

Ten strings are deliberately NOT added, because auto unhide reuses IMD+'s own - it is in the
same module, so non-transitive R is not in the way:

    auto_hide_requirements, auto_hide_req_battery(+_note), auto_hide_battery_disable,
    auto_hide_battery_settings, auto_hide_req_notifications, auto_hide_notification_grant,
    auto_hide_notification_settings, auto_hide_permission_granted, auto_hide_switch_incomplete

Asserts before it writes, and writes nothing if any check fails.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

SETTINGS_RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

NOTIFICATION_RES = os.path.join(
    ROOT, "framework", "notification-manager", "src", "main", "res",
)

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# The author's own English, asserted against the values below before anything is written.
AUTHOR_VERBATIM = {
    "auto_unhide": "Auto unhide settings",
    "auto_unhide_setup": "click to setup",
    "auto_unhide_intro":
        "1. Auto unhides settings based on below triggers.\\n"
        "2. Uses dump permission along with time/screen lock based backup methods",
    "auto_unhide_channel": "Auto unhide settings service",
    "auto_unhide_running": "Auto unhide service running",
}

# key -> locale -> value. Everything in this block lands in feature/settings.
SETTINGS = {}

SETTINGS["auto_unhide"] = {
    "values": "Auto unhide settings",
    "values-ar": "إعدادات إظهار تلقائي",
    "values-b+pt+BR": "Reexibição automática",
    "values-b+zh+Hans": "自动取消隐藏设置",
    "values-de": "Automatisch einblenden",
    "values-es": "Mostrar automáticamente",
    "values-fr": "Réaffichage automatique",
    "values-hi": "ऑटो अनहाइड सेटिंग्स",
    "values-ja": "自動再表示の設定",
    "values-ko": "자동 표시 설정",
    "values-ru": "Автопоказ настроек",
}

SETTINGS["auto_unhide_setup"] = {
    "values": "click to setup",
    "values-ar": "انقر للإعداد",
    "values-b+pt+BR": "toque para configurar",
    "values-b+zh+Hans": "点击进行设置",
    "values-de": "zum Einrichten tippen",
    "values-es": "toca para configurar",
    "values-fr": "appuyez pour configurer",
    "values-hi": "सेटअप के लिए टैप करें",
    "values-ja": "タップして設定",
    "values-ko": "탭하여 설정",
    "values-ru": "нажмите для настройки",
}

SETTINGS["auto_unhide_title"] = dict(SETTINGS["auto_unhide"])

SETTINGS["auto_unhide_switch"] = dict(SETTINGS["auto_unhide"])

SETTINGS["auto_unhide_intro"] = {
    "values":
        "1. Auto unhides settings based on below triggers.\\n"
        "2. Uses dump permission along with time/screen lock based backup methods",
    "values-ar":
        "‏1. يُظهر الإعدادات تلقائيًا بناءً على المشغّلات أدناه.\\n"
        "‏2. يستخدم إذن dump مع طرق احتياطية تعتمد على الوقت أو قفل الشاشة",
    "values-b+pt+BR":
        "1. Reexibe as configurações automaticamente com base nos gatilhos abaixo.\\n"
        "2. Usa a permissão dump junto com métodos reserva por tempo ou bloqueio de tela",
    "values-b+zh+Hans":
        "1. 根据下方的触发条件自动取消隐藏设置。\\n"
        "2. 使用 dump 权限，并以时间或锁屏作为备用方式",
    "values-de":
        "1. Blendet Einstellungen anhand der Auslöser unten automatisch wieder ein.\\n"
        "2. Nutzt die dump-Berechtigung sowie Zeit- und Sperrbildschirm-Ersatzmethoden",
    "values-es":
        "1. Vuelve a mostrar los ajustes automáticamente según los activadores de abajo.\\n"
        "2. Usa el permiso dump junto con métodos de reserva por tiempo o bloqueo de pantalla",
    "values-fr":
        "1. Réaffiche les paramètres automatiquement selon les déclencheurs ci-dessous.\\n"
        "2. Utilise l\\'autorisation dump avec des méthodes de secours par temps ou verrouillage",
    "values-hi":
        "1. नीचे दिए ट्रिगर के आधार पर सेटिंग्स अपने आप अनहाइड करता है।\\n"
        "2. dump अनुमति के साथ समय/स्क्रीन लॉक आधारित बैकअप तरीकों का उपयोग करता है",
    "values-ja":
        "1. 下の条件に基づいて設定を自動的に再表示します。\\n"
        "2. dump 権限を使い、時間や画面ロックを予備の方法として併用します",
    "values-ko":
        "1. 아래 조건에 따라 설정을 자동으로 다시 표시합니다.\\n"
        "2. dump 권한을 사용하며 시간·화면 잠금 기반 백업 방식을 함께 씁니다",
    "values-ru":
        "1. Автоматически показывает настройки по указанным ниже условиям.\\n"
        "2. Использует разрешение dump и запасные способы по времени или блокировке экрана",
}

SETTINGS["auto_unhide_switch_on"] = {
    "values": "On. IMD will unhide by itself when a session ends.",
    "values-ar": "‏مفعّل. سيُظهر IMD الإعدادات تلقائيًا عند انتهاء الجلسة.",
    "values-b+pt+BR": "Ativado. O IMD reexibirá sozinho quando a sessão terminar.",
    "values-b+zh+Hans": "已开启。会话结束时 IMD 会自动取消隐藏。",
    "values-de": "An. IMD blendet nach dem Ende einer Sitzung selbst wieder ein.",
    "values-es": "Activado. IMD volverá a mostrar solo cuando termine la sesión.",
    "values-fr": "Activé. IMD réaffichera de lui-même à la fin d\\'une session.",
    "values-hi": "चालू। सत्र समाप्त होने पर IMD खुद अनहाइड कर देगा।",
    "values-ja": "オン。セッションが終わると IMD が自動で再表示します。",
    "values-ko": "켜짐. 세션이 끝나면 IMD가 스스로 다시 표시합니다.",
    "values-ru": "Включено. IMD сам вернёт настройки, когда сеанс закончится.",
}

SETTINGS["auto_unhide_switch_off"] = {
    "values": "Off. Hidden settings stay hidden until you revert them.",
    "values-ar": "معطّل. تبقى الإعدادات مخفية حتى تستعيدها بنفسك.",
    "values-b+pt+BR": "Desativado. As configurações ocultas ficam assim até você reverter.",
    "values-b+zh+Hans": "已关闭。隐藏的设置会保持隐藏，直到你手动还原。",
    "values-de": "Aus. Ausgeblendete Einstellungen bleiben es, bis du sie zurücksetzt.",
    "values-es": "Desactivado. Los ajustes ocultos siguen ocultos hasta que los revierta.",
    "values-fr": "Désactivé. Les paramètres masqués le restent jusqu\\'à restauration.",
    "values-hi": "बंद। छिपाई गई सेटिंग्स तब तक छिपी रहेंगी जब तक आप उन्हें वापस न करें।",
    "values-ja": "オフ。非表示の設定は手動で戻すまでそのままです。",
    "values-ko": "꺼짐. 숨긴 설정은 직접 되돌릴 때까지 그대로 유지됩니다.",
    "values-ru": "Выключено. Скрытые настройки останутся скрытыми до ручного возврата.",
}

SETTINGS["auto_unhide_triggers"] = {
    "values": "Triggers",
    "values-ar": "المشغّلات",
    "values-b+pt+BR": "Gatilhos",
    "values-b+zh+Hans": "触发条件",
    "values-de": "Auslöser",
    "values-es": "Activadores",
    "values-fr": "Déclencheurs",
    "values-hi": "ट्रिगर",
    "values-ja": "トリガー",
    "values-ko": "트리거",
    "values-ru": "Условия",
}

SETTINGS["auto_unhide_trigger_swipe"] = {
    "values": "Swipe away from recents",
    "values-ar": "التمرير للإزالة من التطبيقات الأخيرة",
    "values-b+pt+BR": "Deslizar para fechar nos recentes",
    "values-b+zh+Hans": "从最近任务中划掉",
    "values-de": "Aus „Zuletzt verwendet“ wischen",
    "values-es": "Deslizar para cerrar en recientes",
    "values-fr": "Balayer depuis les applis récentes",
    "values-hi": "हाल के ऐप्स से स्वाइप करना",
    "values-ja": "最近使ったアプリからスワイプ",
    "values-ko": "최근 앱에서 밀어 닫기",
    "values-ru": "Смахивание из недавних",
}

SETTINGS["auto_unhide_trigger_swipe_note"] = {
    "values": "to unhide when app is swiped away or closed from recents",
    "values-ar": "لإظهار الإعدادات عند إزالة التطبيق أو إغلاقه من التطبيقات الأخيرة",
    "values-b+pt+BR": "para reexibir quando o app for fechado nos recentes",
    "values-b+zh+Hans": "在应用被划掉或从最近任务关闭时取消隐藏",
    "values-de": "einblenden, wenn die App aus „Zuletzt verwendet“ entfernt wird",
    "values-es": "para mostrar cuando la app se cierra desde recientes",
    "values-fr": "pour réafficher quand l\\'appli est fermée depuis les récentes",
    "values-hi": "जब ऐप हाल के ऐप्स से हटाया या बंद किया जाए तब अनहाइड करने के लिए",
    "values-ja": "アプリを最近使ったアプリから消したときに再表示",
    "values-ko": "최근 앱에서 앱을 닫으면 다시 표시",
    "values-ru": "показать, когда приложение убрано из недавних",
}

SETTINGS["auto_unhide_trigger_swipe_unsupported"] = {
    "values": "needs Android 11 or newer",
    "values-ar": "‏يتطلب Android 11 أو أحدث",
    "values-b+pt+BR": "requer Android 11 ou mais recente",
    "values-b+zh+Hans": "需要 Android 11 或更高版本",
    "values-de": "erfordert Android 11 oder neuer",
    "values-es": "requiere Android 11 o posterior",
    "values-fr": "nécessite Android 11 ou plus récent",
    "values-hi": "Android 11 या नया चाहिए",
    "values-ja": "Android 11 以降が必要です",
    "values-ko": "Android 11 이상이 필요합니다",
    "values-ru": "нужен Android 11 или новее",
}

SETTINGS["auto_unhide_trigger_lock"] = {
    "values": "Screen lock",
    "values-ar": "قفل الشاشة",
    "values-b+pt+BR": "Bloqueio de tela",
    "values-b+zh+Hans": "锁屏",
    "values-de": "Bildschirmsperre",
    "values-es": "Bloqueo de pantalla",
    "values-fr": "Verrouillage de l\\'écran",
    "values-hi": "स्क्रीन लॉक",
    "values-ja": "画面ロック",
    "values-ko": "화면 잠금",
    "values-ru": "Блокировка экрана",
}

SETTINGS["auto_unhide_trigger_lock_note"] = {
    "values": "to unhide after screen stays locked, tap to set time",
    "values-ar": "لإظهار الإعدادات بعد بقاء الشاشة مقفلة، انقر لضبط المدة",
    "values-b+pt+BR": "para reexibir depois da tela ficar bloqueada, toque para definir o tempo",
    "values-b+zh+Hans": "在屏幕保持锁定后取消隐藏，点击设置时长",
    "values-de": "einblenden, wenn der Bildschirm gesperrt bleibt; tippen für die Dauer",
    "values-es": "para mostrar tras un tiempo con la pantalla bloqueada, toca para ajustarlo",
    "values-fr": "pour réafficher après un écran resté verrouillé, appuyez pour la durée",
    "values-hi": "स्क्रीन लॉक रहने के बाद अनहाइड करने के लिए, समय सेट करने हेतु टैप करें",
    "values-ja": "画面ロックが続いた後に再表示、タップで時間を設定",
    "values-ko": "화면 잠금이 유지되면 다시 표시, 탭하여 시간 설정",
    "values-ru": "показать после блокировки экрана, нажмите чтобы задать время",
}

SETTINGS["auto_unhide_trigger_idle"] = {
    "values": "App not in foreground",
    "values-ar": "التطبيق ليس في المقدمة",
    "values-b+pt+BR": "App fora de primeiro plano",
    "values-b+zh+Hans": "应用不在前台",
    "values-de": "App nicht im Vordergrund",
    "values-es": "App fuera de primer plano",
    "values-fr": "Appli pas au premier plan",
    "values-hi": "ऐप फ़ोरग्राउंड में नहीं",
    "values-ja": "アプリが前面にない",
    "values-ko": "앱이 화면에 없음",
    "values-ru": "Приложение не на экране",
}

SETTINGS["auto_unhide_trigger_idle_note"] = {
    "values": "to unhide after app is not used, tap to set time",
    "values-ar": "لإظهار الإعدادات بعد عدم استخدام التطبيق، انقر لضبط المدة",
    "values-b+pt+BR": "para reexibir depois que o app não for usado, toque para definir o tempo",
    "values-b+zh+Hans": "在应用一段时间未使用后取消隐藏，点击设置时长",
    "values-de": "einblenden, wenn die App ungenutzt bleibt; tippen für die Dauer",
    "values-es": "para mostrar tras un tiempo sin usar la app, toca para ajustarlo",
    "values-fr": "pour réafficher après une appli inutilisée, appuyez pour la durée",
    "values-hi": "ऐप का उपयोग न होने के बाद अनहाइड करने के लिए, समय सेट करने हेतु टैप करें",
    "values-ja": "アプリが使われなくなった後に再表示、タップで時間を設定",
    "values-ko": "앱을 사용하지 않으면 다시 표시, 탭하여 시간 설정",
    "values-ru": "показать, если приложение не используется, нажмите чтобы задать время",
}

SETTINGS["auto_unhide_req_dump"] = {
    "values": "Dump permission",
    "values-ar": "‏إذن dump",
    "values-b+pt+BR": "Permissão dump",
    "values-b+zh+Hans": "dump 权限",
    "values-de": "dump-Berechtigung",
    "values-es": "Permiso dump",
    "values-fr": "Autorisation dump",
    "values-hi": "dump अनुमति",
    "values-ja": "dump 権限",
    "values-ko": "dump 권한",
    "values-ru": "Разрешение dump",
}

SETTINGS["auto_unhide_req_dump_note"] = {
    "values": "to detect app close from recents",
    "values-ar": "لاكتشاف إغلاق التطبيق من التطبيقات الأخيرة",
    "values-b+pt+BR": "para detectar o fechamento do app nos recentes",
    "values-b+zh+Hans": "用于检测应用从最近任务中被关闭",
    "values-de": "um das Schließen aus „Zuletzt verwendet“ zu erkennen",
    "values-es": "para detectar el cierre de la app en recientes",
    "values-fr": "pour détecter la fermeture depuis les récentes",
    "values-hi": "हाल के ऐप्स से ऐप बंद होने का पता लगाने के लिए",
    "values-ja": "最近使ったアプリからの終了を検出するため",
    "values-ko": "최근 앱에서 앱이 닫히는 것을 감지하기 위해",
    "values-ru": "чтобы замечать закрытие приложения из недавних",
}

SETTINGS["auto_unhide_req_usage"] = {
    "values": "App usage access",
    "values-ar": "الوصول إلى بيانات استخدام التطبيقات",
    "values-b+pt+BR": "Acesso ao uso de apps",
    "values-b+zh+Hans": "使用情况访问权限",
    "values-de": "Zugriff auf Nutzungsdaten",
    "values-es": "Acceso al uso de apps",
    "values-fr": "Accès aux données d\\'utilisation",
    "values-hi": "ऐप उपयोग डेटा एक्सेस",
    "values-ja": "使用状況へのアクセス",
    "values-ko": "사용 정보 접근",
    "values-ru": "Доступ к данным об использовании",
}

SETTINGS["auto_unhide_req_usage_note"] = {
    "values": "to detect app not in foreground",
    "values-ar": "لاكتشاف عدم وجود التطبيق في المقدمة",
    "values-b+pt+BR": "para detectar quando o app sai do primeiro plano",
    "values-b+zh+Hans": "用于检测应用是否不在前台",
    "values-de": "um zu erkennen, dass die App nicht im Vordergrund ist",
    "values-es": "para detectar que la app no está en primer plano",
    "values-fr": "pour détecter que l\\'appli n\\'est pas au premier plan",
    "values-hi": "ऐप के फ़ोरग्राउंड में न होने का पता लगाने के लिए",
    "values-ja": "アプリが前面にないことを検出するため",
    "values-ko": "앱이 화면에 없음을 감지하기 위해",
    "values-ru": "чтобы замечать, что приложение не на экране",
}

SETTINGS["auto_unhide_req_notifications_note"] = {
    "values": "to keep unhide service running",
    "values-ar": "لإبقاء خدمة الإظهار قيد التشغيل",
    "values-b+pt+BR": "para manter o serviço de reexibição em execução",
    "values-b+zh+Hans": "用于保持取消隐藏服务运行",
    "values-de": "damit der Einblende-Dienst weiterläuft",
    "values-es": "para mantener el servicio en ejecución",
    "values-fr": "pour maintenir le service en fonctionnement",
    "values-hi": "अनहाइड सेवा चालू रखने के लिए",
    "values-ja": "再表示サービスを動かし続けるため",
    "values-ko": "표시 서비스를 계속 실행하기 위해",
    "values-ru": "чтобы служба возврата продолжала работать",
}

SETTINGS["auto_unhide_dump_grant"] = {
    "values": "Grant dump permission",
    "values-ar": "‏منح إذن dump",
    "values-b+pt+BR": "Conceder permissão dump",
    "values-b+zh+Hans": "授予 dump 权限",
    "values-de": "dump-Berechtigung erteilen",
    "values-es": "Conceder permiso dump",
    "values-fr": "Accorder l\\'autorisation dump",
    "values-hi": "dump अनुमति दें",
    "values-ja": "dump 権限を付与",
    "values-ko": "dump 권한 부여",
    "values-ru": "Выдать разрешение dump",
}

SETTINGS["auto_unhide_dump_adb"] = {
    "values": "Show adb command",
    "values-ar": "‏عرض أمر adb",
    "values-b+pt+BR": "Mostrar comando adb",
    "values-b+zh+Hans": "显示 adb 命令",
    "values-de": "adb-Befehl anzeigen",
    "values-es": "Mostrar comando adb",
    "values-fr": "Afficher la commande adb",
    "values-hi": "adb कमांड दिखाएँ",
    "values-ja": "adb コマンドを表示",
    "values-ko": "adb 명령 보기",
    "values-ru": "Показать команду adb",
}

SETTINGS["auto_unhide_usage_grant"] = {
    "values": "Grant usage access",
    "values-ar": "منح الوصول إلى بيانات الاستخدام",
    "values-b+pt+BR": "Conceder acesso ao uso",
    "values-b+zh+Hans": "授予使用情况访问权限",
    "values-de": "Zugriff auf Nutzungsdaten erteilen",
    "values-es": "Conceder acceso al uso",
    "values-fr": "Accorder l\\'accès à l\\'utilisation",
    "values-hi": "उपयोग डेटा एक्सेस दें",
    "values-ja": "使用状況へのアクセスを付与",
    "values-ko": "사용 정보 접근 권한 부여",
    "values-ru": "Выдать доступ к данным",
}

SETTINGS["auto_unhide_usage_settings"] = {
    "values": "Open usage access settings",
    "values-ar": "فتح إعدادات الوصول إلى بيانات الاستخدام",
    "values-b+pt+BR": "Abrir configurações de acesso ao uso",
    "values-b+zh+Hans": "打开使用情况访问设置",
    "values-de": "Einstellungen für Nutzungsdaten öffnen",
    "values-es": "Abrir ajustes de acceso al uso",
    "values-fr": "Ouvrir les paramètres d\\'accès à l\\'utilisation",
    "values-hi": "उपयोग एक्सेस सेटिंग्स खोलें",
    "values-ja": "使用状況アクセスの設定を開く",
    "values-ko": "사용 정보 접근 설정 열기",
    "values-ru": "Открыть настройки доступа к данным",
}

SETTINGS["auto_unhide_time_lock"] = {
    "values": "Unhide after screen locked for",
    "values-ar": "الإظهار بعد قفل الشاشة لمدة",
    "values-b+pt+BR": "Reexibir após a tela bloqueada por",
    "values-b+zh+Hans": "锁屏持续以下时长后取消隐藏",
    "values-de": "Einblenden nach Bildschirmsperre von",
    "values-es": "Mostrar tras pantalla bloqueada durante",
    "values-fr": "Réafficher après un écran verrouillé pendant",
    "values-hi": "स्क्रीन इतने समय लॉक रहने पर अनहाइड करें",
    "values-ja": "画面ロックが続いたら再表示",
    "values-ko": "화면 잠금이 다음 시간 지속되면 표시",
    "values-ru": "Показать после блокировки экрана в течение",
}

SETTINGS["auto_unhide_time_idle"] = {
    "values": "Unhide after app not used for",
    "values-ar": "الإظهار بعد عدم استخدام التطبيق لمدة",
    "values-b+pt+BR": "Reexibir após o app sem uso por",
    "values-b+zh+Hans": "应用未使用以下时长后取消隐藏",
    "values-de": "Einblenden, wenn die App ungenutzt ist seit",
    "values-es": "Mostrar tras la app sin usar durante",
    "values-fr": "Réafficher après une appli inutilisée pendant",
    "values-hi": "ऐप इतने समय उपयोग न होने पर अनहाइड करें",
    "values-ja": "アプリが使われなくなったら再表示",
    "values-ko": "앱을 다음 시간 사용하지 않으면 표시",
    "values-ru": "Показать, если приложение не используется",
}

SETTINGS["auto_unhide_minutes"] = {
    "values": "%1$d min",
    "values-ar": "‏%1$d دقيقة",
    "values-b+pt+BR": "%1$d min",
    "values-b+zh+Hans": "%1$d 分钟",
    "values-de": "%1$d Min.",
    "values-es": "%1$d min",
    "values-fr": "%1$d min",
    "values-hi": "%1$d मिनट",
    "values-ja": "%1$d 分",
    "values-ko": "%1$d분",
    "values-ru": "%1$d мин",
}

SETTINGS["auto_unhide_blocked"] = {
    "values": "Complete the requirements on this page before switching auto unhide on.",
    "values-ar": "أكمل المتطلبات في هذه الصفحة قبل تشغيل الإظهار التلقائي.",
    "values-b+pt+BR": "Conclua os requisitos desta página antes de ativar a reexibição automática.",
    "values-b+zh+Hans": "请先完成本页的要求，然后再开启自动取消隐藏。",
    "values-de": "Erfülle die Anforderungen auf dieser Seite, bevor du das automatische Einblenden aktivierst.",
    "values-es": "Completa los requisitos de esta página antes de activar la reexhibición automática.",
    "values-fr": "Remplissez les conditions de cette page avant d\\'activer le réaffichage automatique.",
    "values-hi": "ऑटो अनहाइड चालू करने से पहले इस पेज की आवश्यकताएँ पूरी करें।",
    "values-ja": "自動再表示をオンにする前に、このページの要件を満たしてください。",
    "values-ko": "자동 표시를 켜기 전에 이 페이지의 요건을 충족하세요.",
    "values-ru": "Выполните требования на этой странице, прежде чем включать автопоказ.",
}

SETTINGS["auto_unhide_how_it_works"] = {
    "values": "How auto unhide works",
    "values-ar": "كيف يعمل الإظهار التلقائي",
    "values-b+pt+BR": "Como a reexibição automática funciona",
    "values-b+zh+Hans": "自动取消隐藏的工作方式",
    "values-de": "So funktioniert das automatische Einblenden",
    "values-es": "Cómo funciona la reexhibición automática",
    "values-fr": "Comment fonctionne le réaffichage automatique",
    "values-hi": "ऑटो अनहाइड कैसे काम करता है",
    "values-ja": "自動再表示のしくみ",
    "values-ko": "자동 표시 작동 방식",
    "values-ru": "Как работает автопоказ",
}

SETTINGS["auto_unhide_flow_intro"] = {
    "values": "What happens after IMD hides your settings:",
    "values-ar": "‏ما يحدث بعد أن يخفي IMD إعداداتك:",
    "values-b+pt+BR": "O que acontece depois que o IMD oculta suas configurações:",
    "values-b+zh+Hans": "IMD 隐藏你的设置之后会发生什么：",
    "values-de": "Was passiert, nachdem IMD deine Einstellungen ausgeblendet hat:",
    "values-es": "Qué ocurre después de que IMD oculta tus ajustes:",
    "values-fr": "Ce qui se passe après que IMD a masqué vos paramètres :",
    "values-hi": "IMD द्वारा आपकी सेटिंग्स छिपाने के बाद क्या होता है:",
    "values-ja": "IMD が設定を非表示にした後に起きること:",
    "values-ko": "IMD가 설정을 숨긴 뒤에 일어나는 일:",
    "values-ru": "Что происходит после того, как IMD скрыл настройки:",
}

SETTINGS["auto_unhide_flow_1"] = {
    "values": "IMD hides your settings when you open an app from IMD, a shortcut, the tile or IMD+.",
    "values-ar": "‏يخفي IMD إعداداتك عند فتح تطبيق من IMD أو اختصار أو المربّع أو IMD+.",
    "values-b+pt+BR": "O IMD oculta suas configurações ao abrir um app pelo IMD, um atalho, o bloco ou o IMD+.",
    "values-b+zh+Hans": "当你从 IMD、快捷方式、磁贴或 IMD+ 打开应用时，IMD 会隐藏你的设置。",
    "values-de": "IMD blendet deine Einstellungen aus, wenn du eine App über IMD, eine Verknüpfung, die Kachel oder IMD+ öffnest.",
    "values-es": "IMD oculta tus ajustes cuando abres una app desde IMD, un acceso directo, el mosaico o IMD+.",
    "values-fr": "IMD masque vos paramètres quand vous ouvrez une appli depuis IMD, un raccourci, la tuile ou IMD+.",
    "values-hi": "जब आप IMD, शॉर्टकट, टाइल या IMD+ से कोई ऐप खोलते हैं तो IMD आपकी सेटिंग्स छिपा देता है।",
    "values-ja": "IMD、ショートカット、タイル、IMD+ からアプリを開くと、IMD が設定を非表示にします。",
    "values-ko": "IMD, 바로가기, 타일 또는 IMD+에서 앱을 열면 IMD가 설정을 숨깁니다.",
    "values-ru": "IMD скрывает настройки, когда вы открываете приложение из IMD, ярлыка, плитки или IMD+.",
}

SETTINGS["auto_unhide_flow_2"] = {
    "values": "A silent notification says the auto unhide service is running.",
    "values-ar": "يظهر إشعار صامت يفيد بأن خدمة الإظهار التلقائي قيد التشغيل.",
    "values-b+pt+BR": "Uma notificação silenciosa informa que o serviço de reexibição está ativo.",
    "values-b+zh+Hans": "一条静默通知表明自动取消隐藏服务正在运行。",
    "values-de": "Eine stumme Benachrichtigung zeigt an, dass der Dienst läuft.",
    "values-es": "Una notificación silenciosa indica que el servicio está en marcha.",
    "values-fr": "Une notification silencieuse indique que le service fonctionne.",
    "values-hi": "एक साइलेंट सूचना बताती है कि ऑटो अनहाइड सेवा चल रही है।",
    "values-ja": "自動再表示サービスが動作中であることを通知が静かに示します。",
    "values-ko": "무음 알림이 자동 표시 서비스가 실행 중임을 알려 줍니다.",
    "values-ru": "Беззвучное уведомление сообщает, что служба автопоказа работает.",
}

SETTINGS["auto_unhide_flow_3"] = {
    "values": "You use the app normally.",
    "values-ar": "تستخدم التطبيق كالمعتاد.",
    "values-b+pt+BR": "Você usa o app normalmente.",
    "values-b+zh+Hans": "你正常使用该应用。",
    "values-de": "Du benutzt die App ganz normal.",
    "values-es": "Usas la app con normalidad.",
    "values-fr": "Vous utilisez l\\'appli normalement.",
    "values-hi": "आप ऐप का सामान्य रूप से उपयोग करते हैं।",
    "values-ja": "アプリを普通に使います。",
    "values-ko": "앱을 평소처럼 사용합니다.",
    "values-ru": "Вы пользуетесь приложением как обычно.",
}

SETTINGS["auto_unhide_flow_4"] = {
    "values": "You swipe the app away from recent apps, or press close all.",
    "values-ar": "تُزيل التطبيق من التطبيقات الأخيرة أو تضغط على إغلاق الكل.",
    "values-b+pt+BR": "Você fecha o app nos recentes ou toca em fechar tudo.",
    "values-b+zh+Hans": "你从最近任务中划掉该应用，或点击全部关闭。",
    "values-de": "Du wischst die App aus „Zuletzt verwendet“ oder tippst auf Alle schließen.",
    "values-es": "Cierras la app en recientes o pulsas cerrar todo.",
    "values-fr": "Vous fermez l\\'appli depuis les récentes ou appuyez sur tout fermer.",
    "values-hi": "आप ऐप को हाल के ऐप्स से हटाते हैं, या सभी बंद करें दबाते हैं।",
    "values-ja": "最近使ったアプリからアプリを消すか、すべて閉じるを押します。",
    "values-ko": "최근 앱에서 앱을 밀어 닫거나 모두 닫기를 누릅니다.",
    "values-ru": "Вы убираете приложение из недавних или нажимаете «Закрыть все».",
}

SETTINGS["auto_unhide_flow_5"] = {
    "values": "IMD sees the app was closed and reverts your settings on its own.",
    "values-ar": "‏يلاحظ IMD إغلاق التطبيق ويستعيد إعداداتك تلقائيًا.",
    "values-b+pt+BR": "O IMD percebe que o app foi fechado e reverte suas configurações sozinho.",
    "values-b+zh+Hans": "IMD 察觉到应用已关闭，并自动还原你的设置。",
    "values-de": "IMD bemerkt das Schließen und setzt deine Einstellungen selbst zurück.",
    "values-es": "IMD detecta el cierre y revierte tus ajustes por su cuenta.",
    "values-fr": "IMD constate la fermeture et restaure vos paramètres tout seul.",
    "values-hi": "IMD देखता है कि ऐप बंद हो गया और आपकी सेटिंग्स खुद वापस कर देता है।",
    "values-ja": "IMD がアプリの終了に気づき、設定を自動で元に戻します。",
    "values-ko": "IMD가 앱이 닫힌 것을 확인하고 설정을 스스로 되돌립니다.",
    "values-ru": "IMD замечает закрытие приложения и сам возвращает настройки.",
}

SETTINGS["auto_unhide_flow_6"] = {
    "values": "If you forget, the screen lock or app not in foreground timer reverts them instead.",
    "values-ar": "إذا نسيت، يقوم مؤقّت قفل الشاشة أو عدم استخدام التطبيق بالاستعادة بدلًا من ذلك.",
    "values-b+pt+BR": "Se você esquecer, o tempo de bloqueio de tela ou de app sem uso faz isso no lugar.",
    "values-b+zh+Hans": "如果你忘了，锁屏或应用未使用的计时器会代为还原。",
    "values-de": "Vergisst du es, übernimmt der Sperrbildschirm- oder Ungenutzt-Timer.",
    "values-es": "Si lo olvidas, lo hace el temporizador de bloqueo o de app sin usar.",
    "values-fr": "Si vous oubliez, le minuteur de verrouillage ou d\\'inactivité s\\'en charge.",
    "values-hi": "अगर आप भूल जाएँ, तो स्क्रीन लॉक या ऐप अप्रयुक्त टाइमर यह काम कर देता है।",
    "values-ja": "忘れた場合は、画面ロックまたは未使用のタイマーが代わりに戻します。",
    "values-ko": "잊었더라도 화면 잠금 또는 미사용 타이머가 대신 되돌립니다.",
    "values-ru": "Если вы забудете, это сделает таймер блокировки или бездействия.",
}

SETTINGS["auto_unhide_flow_7"] = {
    "values": "The notification goes away once everything is back.",
    "values-ar": "يختفي الإشعار بمجرد استعادة كل شيء.",
    "values-b+pt+BR": "A notificação some assim que tudo volta ao normal.",
    "values-b+zh+Hans": "一切还原后，通知会自动消失。",
    "values-de": "Die Benachrichtigung verschwindet, sobald alles zurück ist.",
    "values-es": "La notificación desaparece cuando todo ha vuelto.",
    "values-fr": "La notification disparaît une fois tout restauré.",
    "values-hi": "सब कुछ वापस आने पर सूचना अपने आप हट जाती है।",
    "values-ja": "すべてが元に戻ると通知は消えます。",
    "values-ko": "모두 되돌아오면 알림이 사라집니다.",
    "values-ru": "Уведомление исчезает, когда всё возвращено.",
}

SETTINGS["auto_unhide_adb_title"] = {
    "values": "Grant dump permission over adb",
    "values-ar": "‏منح إذن dump عبر adb",
    "values-b+pt+BR": "Conceder permissão dump via adb",
    "values-b+zh+Hans": "通过 adb 授予 dump 权限",
    "values-de": "dump-Berechtigung per adb erteilen",
    "values-es": "Conceder permiso dump por adb",
    "values-fr": "Accorder l\\'autorisation dump via adb",
    "values-hi": "adb से dump अनुमति दें",
    "values-ja": "adb で dump 権限を付与",
    "values-ko": "adb로 dump 권한 부여",
    "values-ru": "Выдать разрешение dump через adb",
}

SETTINGS["auto_unhide_adb_body"] = {
    "values": "Connect your phone to a computer and run this once. It stays granted until IMD is reinstalled.",
    "values-ar": "وصّل هاتفك بحاسوب ونفّذ هذا مرة واحدة. يبقى الإذن ممنوحًا حتى إعادة تثبيت IMD.",
    "values-b+pt+BR": "Conecte o telefone a um computador e execute isto uma vez. Vale até o IMD ser reinstalado.",
    "values-b+zh+Hans": "将手机连接到电脑并执行一次。在重新安装 IMD 之前一直有效。",
    "values-de": "Verbinde dein Telefon mit einem Computer und führe dies einmal aus. Es gilt, bis IMD neu installiert wird.",
    "values-es": "Conecta el teléfono a un ordenador y ejecuta esto una vez. Sigue concedido hasta reinstalar IMD.",
    "values-fr": "Connectez votre téléphone à un ordinateur et lancez ceci une fois. Valable jusqu\\'à la réinstallation d\\'IMD.",
    "values-hi": "अपना फ़ोन कंप्यूटर से जोड़ें और इसे एक बार चलाएँ। IMD दोबारा इंस्टॉल होने तक यह बना रहता है।",
    "values-ja": "スマートフォンをパソコンにつなぎ、一度だけ実行してください。IMD を再インストールするまで有効です。",
    "values-ko": "휴대전화를 컴퓨터에 연결하고 한 번만 실행하세요. IMD를 다시 설치할 때까지 유지됩니다.",
    "values-ru": "Подключите телефон к компьютеру и выполните это один раз. Действует до переустановки IMD.",
}

SETTINGS["auto_unhide_adb_copy"] = {
    "values": "Copy command",
    "values-ar": "نسخ الأمر",
    "values-b+pt+BR": "Copiar comando",
    "values-b+zh+Hans": "复制命令",
    "values-de": "Befehl kopieren",
    "values-es": "Copiar comando",
    "values-fr": "Copier la commande",
    "values-hi": "कमांड कॉपी करें",
    "values-ja": "コマンドをコピー",
    "values-ko": "명령 복사",
    "values-ru": "Скопировать команду",
}

# --- framework/notification-manager ---------------------------------------
NOTIFICATIONS = {}

NOTIFICATIONS["auto_unhide_channel"] = {
    "values": "Auto unhide settings service",
    "values-ar": "خدمة إعدادات الإظهار التلقائي",
    "values-b+pt+BR": "Serviço de reexibição automática",
    "values-b+zh+Hans": "自动取消隐藏设置服务",
    "values-de": "Dienst für automatisches Einblenden",
    "values-es": "Servicio de reexhibición automática",
    "values-fr": "Service de réaffichage automatique",
    "values-hi": "ऑटो अनहाइड सेटिंग्स सेवा",
    "values-ja": "自動再表示設定サービス",
    "values-ko": "자동 표시 설정 서비스",
    "values-ru": "Служба автопоказа настроек",
}

NOTIFICATIONS["auto_unhide_running"] = {
    "values": "Auto unhide service running",
    "values-ar": "خدمة الإظهار التلقائي قيد التشغيل",
    "values-b+pt+BR": "Serviço de reexibição automática ativo",
    "values-b+zh+Hans": "自动取消隐藏服务运行中",
    "values-de": "Dienst für automatisches Einblenden läuft",
    "values-es": "Servicio de reexhibición automática en marcha",
    "values-fr": "Service de réaffichage automatique actif",
    "values-hi": "ऑटो अनहाइड सेवा चल रही है",
    "values-ja": "自動再表示サービスが実行中",
    "values-ko": "자동 표시 서비스 실행 중",
    "values-ru": "Служба автопоказа работает",
}


EXPECTED_SETTINGS_KEYS = 40
EXPECTED_NOTIFICATION_KEYS = 2


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def unsafe(value):
    """Everything aapt2 or the parser would refuse, or that renders wrong."""
    problems = []

    if re.search(r"(?<!\\)'", value):
        problems.append("unescaped apostrophe")

    if '"' in value:
        problems.append("straight double quote")

    if "\n" in value:
        problems.append("literal newline")

    if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", value):
        problems.append("bare ampersand")

    return problems


def check_tables(errors):
    """Shape of the two tables, before a single file is opened."""
    if len(SETTINGS) != EXPECTED_SETTINGS_KEYS:
        errors.append(
            "SETTINGS has %d keys, expected %d" % (len(SETTINGS), EXPECTED_SETTINGS_KEYS)
        )

    if len(NOTIFICATIONS) != EXPECTED_NOTIFICATION_KEYS:
        errors.append(
            "NOTIFICATIONS has %d keys, expected %d"
            % (len(NOTIFICATIONS), EXPECTED_NOTIFICATION_KEYS)
        )

    for table_name, table in (("settings", SETTINGS), ("notifications", NOTIFICATIONS)):
        for key, values in table.items():
            missing = [locale for locale in LOCALES if locale not in values]

            if missing:
                errors.append("%s/%s: missing %s" % (table_name, key, ", ".join(missing)))

            extra = [locale for locale in values if locale not in LOCALES]

            if extra:
                errors.append("%s/%s: unknown locale %s" % (table_name, key, ", ".join(extra)))

            for locale, value in values.items():
                bad = unsafe(value)

                if bad:
                    errors.append("%s/%s/%s: %s" % (table_name, key, locale, ", ".join(bad)))

                if not value.strip():
                    errors.append("%s/%s/%s: empty" % (table_name, key, locale))

    # The author's own English, which must survive this script unchanged.
    for key, expected in AUTHOR_VERBATIM.items():
        table = SETTINGS if key in SETTINGS else NOTIFICATIONS

        actual = table.get(key, {}).get("values")

        if actual != expected:
            errors.append(
                "author string %s is %r, expected %r" % (key, actual, expected)
            )

    # A format specifier dropped in translation is a crash at runtime, not a typo.
    for locale, value in SETTINGS["auto_unhide_minutes"].items():
        if "%1$d" not in value:
            errors.append("auto_unhide_minutes/%s: lost the %%1$d placeholder" % locale)


def add_all(path, table, locale, errors):
    """Returns the new file text, or None when something is wrong with it."""
    text = open(path, encoding="utf-8").read()

    if text.count("</resources>") != 1:
        errors.append("%s: expected exactly one </resources>" % path)

        return None

    additions = []

    for key in sorted(table):
        if body(text, key) is not None:
            errors.append("%s: %s already present in %s" % (locale, key, path))

            continue

        additions.append(
            '    <string name="%s">%s</string>' % (key, table[key][locale])
        )

    if not additions:
        return text

    return text.replace("</resources>", "\n".join(additions) + "\n</resources>", 1)


def main():
    print("ROOT = %s" % ROOT)

    errors = []

    check_tables(errors)

    pending = {}

    if not errors:
        for locale in LOCALES:
            for res, table in ((SETTINGS_RES, SETTINGS), (NOTIFICATION_RES, NOTIFICATIONS)):
                path = os.path.join(res, locale, "strings.xml")

                if not os.path.exists(path):
                    errors.append("%s: missing %s" % (locale, path))

                    continue

                new_text = add_all(path, table, locale, errors)

                if new_text is not None:
                    pending[path] = new_text

    if errors:
        for error in errors:
            print("  ! %s" % error)

        print("REFUSED, nothing written")

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print(
        "wrote %d files: %d settings keys + %d notification keys x %d locales = %d strings"
        % (
            len(pending),
            len(SETTINGS),
            len(NOTIFICATIONS),
            len(LOCALES),
            (len(SETTINGS) + len(NOTIFICATIONS)) * len(LOCALES),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
