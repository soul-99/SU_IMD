#!/usr/bin/env python3
"""
r13 strings.

ADD 18 keys across all 11 locales - the auto unhide "Used for" section, the author's green
third line, the diagnostics dialog and its button, the two halves of the Help button, and the
second line of the About screen's logics link.

REPLACE `about_contributor_scope`, which grows from a two-word aside into a sentence:
"(Display over other apps)" -> "(Display over other apps initial framework)".

DROP `help_button`, now split into `help_button_label` + `help_button_scope` so the question
mark icon can sit between them, and the three r12 probe strings, whose feature the diagnostics
dialog replaces. The probe keys are translatable="false" and live in values/ only, so they are
dropped from there alone.

Four of the additions are the author's own English and go in verbatim:

    auto_unhide_intro_battery       the green line, "battery optimisation disabled" and all
    auto_unhide_used_for            including the space before the colon
    auto_unhide_used_for_launch
    auto_unhide_used_for_tile

plus the replacement above. All five are asserted against their exact text before anything is
written.
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
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

AUTHOR_VERBATIM = {
    "auto_unhide_intro_battery":
        "3. Even when battery optimisation disabled, IMD app only runs in the background when "
        "settings are hidden by IMD with Auto unhide enabled or you use IMD+.",
    "auto_unhide_used_for": "Used for, when settings are hidden by :",
    "auto_unhide_used_for_launch": "App launches",
    "auto_unhide_used_for_tile": "Hide settings quick settings toggle",
    "about_contributor_scope": "(Display over other apps initial framework)",
}

DROP = ["help_button"]

DROP_VALUES_ONLY = [
    "auto_unhide_diag_title",
    "auto_unhide_diag_note",
    "auto_unhide_diag_copy",
]

REPLACE = {"about_contributor_scope": {}}

ADD = {}

REPLACE["about_contributor_scope"] = {
    "values": "(Display over other apps initial framework)",
    "values-ar": "‏(الإطار الأولي لميزة العرض فوق التطبيقات الأخرى)",
    "values-b+pt+BR": "(Estrutura inicial de sobreposição a outros apps)",
    "values-b+zh+Hans": "（“显示在其他应用上层”的初始框架）",
    "values-de": "(Erstes Grundgerüst für „Über anderen Apps anzeigen“)",
    "values-es": "(Estructura inicial de «Mostrar sobre otras apps»)",
    "values-fr": "(Base initiale de l\\'affichage par-dessus les autres applications)",
    "values-hi": "(‘अन्य ऐप्स के ऊपर दिखाएँ’ का प्रारंभिक ढाँचा)",
    "values-ja": "（「他のアプリの上に重ねて表示」の初期フレームワーク）",
    "values-ko": "(‘다른 앱 위에 표시’ 초기 프레임워크)",
    "values-ru": "(первоначальная основа «Поверх других приложений»)",
}

ADD["auto_unhide_intro_battery"] = {
    "values":
        "3. Even when battery optimisation disabled, IMD app only runs in the background when "
        "settings are hidden by IMD with Auto unhide enabled or you use IMD+.",
    "values-ar":
        "‏3. حتى مع تعطيل تحسين البطارية، لا يعمل تطبيق IMD في الخلفية إلا عندما تكون الإعدادات "
        "مخفية بواسطة IMD مع تفعيل الإظهار التلقائي، أو عند استخدام IMD+.",
    "values-b+pt+BR":
        "3. Mesmo com a otimização de bateria desativada, o IMD só roda em segundo plano quando "
        "as configurações estão ocultas pelo IMD com a reexibição automática ativada, ou quando "
        "você usa o IMD+.",
    "values-b+zh+Hans":
        "3. 即使关闭了电池优化，IMD 也只在设置被 IMD 隐藏且已启用自动取消隐藏时，"
        "或你使用 IMD+ 时，才会在后台运行。",
    "values-de":
        "3. Auch bei deaktivierter Akkuoptimierung läuft IMD nur dann im Hintergrund, wenn "
        "Einstellungen von IMD ausgeblendet sind und das automatische Einblenden aktiv ist, "
        "oder wenn du IMD+ verwendest.",
    "values-es":
        "3. Incluso con la optimización de batería desactivada, IMD solo se ejecuta en segundo "
        "plano cuando los ajustes están ocultos por IMD con la reexhibición automática "
        "activada, o cuando usas IMD+.",
    "values-fr":
        "3. Même avec l\\'optimisation de la batterie désactivée, IMD ne tourne en arrière-plan "
        "que lorsque des paramètres sont masqués par IMD avec le réaffichage automatique "
        "activé, ou lorsque vous utilisez IMD+.",
    "values-hi":
        "3. बैटरी ऑप्टिमाइज़ेशन बंद होने पर भी, IMD ऐप बैकग्राउंड में तभी चलता है जब सेटिंग्स IMD द्वारा "
        "छिपाई गई हों और ऑटो अनहाइड चालू हो, या जब आप IMD+ का उपयोग करें।",
    "values-ja":
        "3. バッテリー最適化を無効にしていても、IMD がバックグラウンドで動くのは、"
        "IMD によって設定が非表示になっていて自動再表示が有効なときか、IMD+ を使うときだけです。",
    "values-ko":
        "3. 배터리 최적화를 꺼도, IMD는 IMD가 설정을 숨긴 상태에서 자동 표시가 켜져 있을 때나 "
        "IMD+를 사용할 때만 백그라운드에서 실행됩니다.",
    "values-ru":
        "3. Даже при отключённой оптимизации батареи IMD работает в фоне только тогда, когда "
        "настройки скрыты приложением IMD и включён автопоказ, либо когда вы используете IMD+.",
}

ADD["auto_unhide_used_for"] = {
    "values": "Used for, when settings are hidden by :",
    "values-ar": "يُستخدم عندما تُخفى الإعدادات بواسطة :",
    "values-b+pt+BR": "Usado quando as configurações forem ocultas por :",
    "values-b+zh+Hans": "在设置被以下方式隐藏时使用：",
    "values-de": "Gilt, wenn Einstellungen ausgeblendet wurden durch :",
    "values-es": "Se usa cuando los ajustes se ocultan mediante :",
    "values-fr": "Utilisé quand les paramètres sont masqués par :",
    "values-hi": "तब उपयोग करें, जब सेटिंग्स इनके द्वारा छिपाई जाएँ :",
    "values-ja": "設定が次の方法で非表示にされたとき :",
    "values-ko": "설정이 다음으로 숨겨졌을 때 사용 :",
    "values-ru": "Применяется, когда настройки скрыты через :",
}

ADD["auto_unhide_used_for_launch"] = {
    "values": "App launches",
    "values-ar": "عمليات فتح التطبيقات",
    "values-b+pt+BR": "Aberturas de apps",
    "values-b+zh+Hans": "应用启动",
    "values-de": "App-Starts",
    "values-es": "Aperturas de apps",
    "values-fr": "Lancements d\\'applications",
    "values-hi": "ऐप लॉन्च",
    "values-ja": "アプリの起動",
    "values-ko": "앱 실행",
    "values-ru": "Запуски приложений",
}

ADD["auto_unhide_used_for_launch_note"] = {
    "values": "IMD, app shortcuts and IMD+ auto hide",
    "values-ar": "‏IMD واختصارات التطبيقات والإخفاء التلقائي في IMD+",
    "values-b+pt+BR": "IMD, atalhos de apps e a ocultação automática do IMD+",
    "values-b+zh+Hans": "IMD、应用快捷方式，以及 IMD+ 自动隐藏",
    "values-de": "IMD, App-Verknüpfungen und das automatische Ausblenden von IMD+",
    "values-es": "IMD, accesos directos de apps y la ocultación automática de IMD+",
    "values-fr": "IMD, raccourcis d\\'applications et le masquage automatique d\\'IMD+",
    "values-hi": "IMD, ऐप शॉर्टकट और IMD+ ऑटो हाइड",
    "values-ja": "IMD、アプリのショートカット、IMD+ の自動非表示",
    "values-ko": "IMD, 앱 바로가기, IMD+ 자동 숨기기",
    "values-ru": "IMD, ярлыки приложений и автоскрытие IMD+",
}

ADD["auto_unhide_used_for_tile"] = {
    "values": "Hide settings quick settings toggle",
    "values-ar": "مفتاح «إخفاء الإعدادات» في الإعدادات السريعة",
    "values-b+pt+BR": "Bloco de configurações rápidas Ocultar configurações",
    "values-b+zh+Hans": "“隐藏设置”快捷设置磁贴",
    "values-de": "Schnelleinstellungs-Kachel „Einstellungen ausblenden“",
    "values-es": "Mosaico de ajustes rápidos Ocultar ajustes",
    "values-fr": "Tuile de réglages rapides Masquer les paramètres",
    "values-hi": "‘सेटिंग्स छिपाएँ’ क्विक सेटिंग्स टॉगल",
    "values-ja": "「設定を非表示」のクイック設定タイル",
    "values-ko": "‘설정 숨기기’ 빠른 설정 타일",
    "values-ru": "Плитка быстрых настроек «Скрыть настройки»",
}

ADD["auto_unhide_used_for_tile_note"] = {
    "values": "the tile names no app, so only the screen lock timer can end it",
    "values-ar": "لا يحدد المربّع أي تطبيق، لذا لا ينهيه سوى مؤقّت قفل الشاشة",
    "values-b+pt+BR": "o bloco não indica um app, então só o tempo de bloqueio de tela o encerra",
    "values-b+zh+Hans": "磁贴不指明应用，因此只有锁屏计时器能结束它",
    "values-de": "die Kachel nennt keine App, daher beendet nur der Sperrbildschirm-Timer sie",
    "values-es": "el mosaico no indica una app, así que solo el temporizador de bloqueo lo cierra",
    "values-fr": "la tuile ne nomme aucune appli : seul le minuteur de verrouillage y met fin",
    "values-hi": "टाइल किसी ऐप का नाम नहीं देती, इसलिए इसे केवल स्क्रीन लॉक टाइमर समाप्त कर सकता है",
    "values-ja": "タイルはアプリを指定しないため、画面ロックのタイマーだけが終了できます",
    "values-ko": "타일은 앱을 지정하지 않으므로 화면 잠금 타이머만 끝낼 수 있습니다",
    "values-ru": "плитка не называет приложение, поэтому завершить может только таймер блокировки",
}

ADD["auto_unhide_used_for_blocked"] = {
    "values": "At least one of these has to stay ticked, or auto unhide has nothing to act on.",
    "values-ar": "يجب أن يظل أحدهما محدّدًا على الأقل، وإلا لن يكون للإظهار التلقائي ما يعمل عليه.",
    "values-b+pt+BR": "Pelo menos um destes precisa ficar marcado, senão a reexibição não tem o que fazer.",
    "values-b+zh+Hans": "至少要保留一项勾选，否则自动取消隐藏无事可做。",
    "values-de": "Mindestens eines muss angehakt bleiben, sonst hat das Einblenden nichts zu tun.",
    "values-es": "Al menos uno debe seguir marcado, o la reexhibición no tendrá nada que hacer.",
    "values-fr": "Au moins l\\'un doit rester coché, sinon le réaffichage n\\'a rien à faire.",
    "values-hi": "इनमें से कम से कम एक चुना रहना चाहिए, वरना ऑटो अनहाइड के पास करने को कुछ नहीं होगा।",
    "values-ja": "少なくとも一つは選んだままにしてください。両方外すと自動再表示は何もできません。",
    "values-ko": "적어도 하나는 선택된 상태여야 합니다. 모두 해제하면 자동 표시가 할 일이 없습니다.",
    "values-ru": "Хотя бы один должен остаться отмеченным, иначе автопоказу не с чем работать.",
}

ADD["diagnostics_title"] = {
    "values": "Diagnostics",
    "values-ar": "التشخيص",
    "values-b+pt+BR": "Diagnóstico",
    "values-b+zh+Hans": "诊断",
    "values-de": "Diagnose",
    "values-es": "Diagnóstico",
    "values-fr": "Diagnostic",
    "values-hi": "डायग्नोस्टिक्स",
    "values-ja": "診断",
    "values-ko": "진단",
    "values-ru": "Диагностика",
}

ADD["diagnostics_switch"] = {
    "values": "Record diagnostic log",
    "values-ar": "تسجيل سجل التشخيص",
    "values-b+pt+BR": "Gravar registro de diagnóstico",
    "values-b+zh+Hans": "记录诊断日志",
    "values-de": "Diagnoseprotokoll aufzeichnen",
    "values-es": "Registrar el diagnóstico",
    "values-fr": "Enregistrer le journal de diagnostic",
    "values-hi": "डायग्नोस्टिक लॉग रिकॉर्ड करें",
    "values-ja": "診断ログを記録",
    "values-ko": "진단 로그 기록",
    "values-ru": "Записывать журнал диагностики",
}

ADD["diagnostics_switch_on"] = {
    "values": "On. Kept for 7 days, then deleted.",
    "values-ar": "مفعّل. يُحتفظ به 7 أيام ثم يُحذف.",
    "values-b+pt+BR": "Ativado. Mantido por 7 dias e depois apagado.",
    "values-b+zh+Hans": "已开启。保留 7 天后删除。",
    "values-de": "An. Wird 7 Tage aufbewahrt und dann gelöscht.",
    "values-es": "Activado. Se conserva 7 días y luego se borra.",
    "values-fr": "Activé. Conservé 7 jours, puis supprimé.",
    "values-hi": "चालू। 7 दिन तक रखा जाता है, फिर हटा दिया जाता है।",
    "values-ja": "オン。7 日間保存され、その後削除されます。",
    "values-ko": "켜짐. 7일간 보관한 뒤 삭제됩니다.",
    "values-ru": "Включено. Хранится 7 дней, затем удаляется.",
}

ADD["diagnostics_switch_off"] = {
    "values": "Off. Nothing is being recorded.",
    "values-ar": "معطّل. لا يجري تسجيل أي شيء.",
    "values-b+pt+BR": "Desativado. Nada está sendo gravado.",
    "values-b+zh+Hans": "已关闭。当前不记录任何内容。",
    "values-de": "Aus. Es wird nichts aufgezeichnet.",
    "values-es": "Desactivado. No se está registrando nada.",
    "values-fr": "Désactivé. Rien n\\'est enregistré.",
    "values-hi": "बंद। कुछ भी रिकॉर्ड नहीं हो रहा।",
    "values-ja": "オフ。何も記録していません。",
    "values-ko": "꺼짐. 아무것도 기록하지 않습니다.",
    "values-ru": "Выключено. Ничего не записывается.",
}

ADD["diagnostics_empty"] = {
    "values": "No log yet. Switch recording on, reproduce the problem, then come back.",
    "values-ar": "لا يوجد سجل بعد. فعّل التسجيل، وأعد إحداث المشكلة، ثم عد إلى هنا.",
    "values-b+pt+BR": "Ainda sem registro. Ative a gravação, reproduza o problema e volte aqui.",
    "values-b+zh+Hans": "还没有日志。先开启记录，重现问题，然后回到这里。",
    "values-de": "Noch kein Protokoll. Aufzeichnung einschalten, das Problem auslösen, dann zurückkommen.",
    "values-es": "Aún no hay registro. Activa la grabación, reproduce el problema y vuelve aquí.",
    "values-fr": "Pas encore de journal. Activez l\\'enregistrement, reproduisez le problème, puis revenez.",
    "values-hi": "अभी कोई लॉग नहीं। रिकॉर्डिंग चालू करें, समस्या दोहराएँ, फिर वापस आएँ।",
    "values-ja": "まだログがありません。記録をオンにし、問題を再現してから戻ってください。",
    "values-ko": "아직 로그가 없습니다. 기록을 켜고 문제를 재현한 뒤 다시 오세요.",
    "values-ru": "Журнала пока нет. Включите запись, воспроизведите проблему и вернитесь.",
}

ADD["diagnostics_copy"] = {
    "values": "Copy log",
    "values-ar": "نسخ السجل",
    "values-b+pt+BR": "Copiar registro",
    "values-b+zh+Hans": "复制日志",
    "values-de": "Protokoll kopieren",
    "values-es": "Copiar registro",
    "values-fr": "Copier le journal",
    "values-hi": "लॉग कॉपी करें",
    "values-ja": "ログをコピー",
    "values-ko": "로그 복사",
    "values-ru": "Скопировать журнал",
}

ADD["diagnostics_save"] = {
    "values": "Save log file",
    "values-ar": "حفظ ملف السجل",
    "values-b+pt+BR": "Salvar arquivo de registro",
    "values-b+zh+Hans": "保存日志文件",
    "values-de": "Protokolldatei speichern",
    "values-es": "Guardar archivo de registro",
    "values-fr": "Enregistrer le fichier journal",
    "values-hi": "लॉग फ़ाइल सहेजें",
    "values-ja": "ログファイルを保存",
    "values-ko": "로그 파일 저장",
    "values-ru": "Сохранить файл журнала",
}

ADD["diagnostics_clear"] = {
    "values": "Clear log",
    "values-ar": "مسح السجل",
    "values-b+pt+BR": "Limpar registro",
    "values-b+zh+Hans": "清除日志",
    "values-de": "Protokoll löschen",
    "values-es": "Borrar registro",
    "values-fr": "Effacer le journal",
    "values-hi": "लॉग साफ़ करें",
    "values-ja": "ログを消去",
    "values-ko": "로그 지우기",
    "values-ru": "Очистить журнал",
}

ADD["help_button_label"] = {
    "values": "Help",
    "values-ar": "مساعدة",
    "values-b+pt+BR": "Ajuda",
    "values-b+zh+Hans": "帮助",
    "values-de": "Hilfe",
    "values-es": "Ayuda",
    "values-fr": "Aide",
    "values-hi": "सहायता",
    "values-ja": "ヘルプ",
    "values-ko": "도움말",
    "values-ru": "Помощь",
}

ADD["help_button_scope"] = {
    "values": "(readme)",
    "values-ar": "‏(اقرأني)",
    "values-b+pt+BR": "(leia-me)",
    "values-b+zh+Hans": "（自述文件）",
    "values-de": "(Liesmich)",
    "values-es": "(léeme)",
    "values-fr": "(lisez-moi)",
    "values-hi": "(रीडमी)",
    "values-ja": "（説明）",
    "values-ko": "(설명서)",
    "values-ru": "(readme)",
}

ADD["about_logics_how"] = {
    "values": "(How this app works)",
    "values-ar": "‏(كيف يعمل هذا التطبيق)",
    "values-b+pt+BR": "(Como este app funciona)",
    "values-b+zh+Hans": "（这个应用如何运作）",
    "values-de": "(Wie diese App funktioniert)",
    "values-es": "(Cómo funciona esta app)",
    "values-fr": "(Comment cette application fonctionne)",
    "values-hi": "(यह ऐप कैसे काम करता है)",
    "values-ja": "（このアプリのしくみ）",
    "values-ko": "(이 앱의 작동 방식)",
    "values-ru": "(Как работает это приложение)",
}


EXPECTED_ADDED_KEYS = 18


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def unsafe(value):
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
    if len(ADD) != EXPECTED_ADDED_KEYS:
        errors.append("ADD has %d keys, expected %d" % (len(ADD), EXPECTED_ADDED_KEYS))

    for table_name, table in (("add", ADD), ("replace", REPLACE)):
        for key, values in table.items():
            missing = [locale for locale in LOCALES if locale not in values]

            if missing:
                errors.append("%s/%s: missing %s" % (table_name, key, ", ".join(missing)))

            for locale, value in values.items():
                bad = unsafe(value)

                if bad:
                    errors.append("%s/%s/%s: %s" % (table_name, key, locale, ", ".join(bad)))

                if not value.strip():
                    errors.append("%s/%s/%s: empty" % (table_name, key, locale))

    for key, expected in AUTHOR_VERBATIM.items():
        table = ADD if key in ADD else REPLACE

        actual = table.get(key, {}).get("values")

        if actual != expected:
            errors.append("author string %s is %r, expected %r" % (key, actual, expected))


def main():
    print("ROOT = %s" % ROOT)

    errors = []

    check_tables(errors)

    pending = {}

    if not errors:
        for locale in LOCALES:
            path = os.path.join(SETTINGS_RES, locale, "strings.xml")

            if not os.path.exists(path):
                errors.append("%s: missing %s" % (locale, path))

                continue

            text = open(path, encoding="utf-8").read()

            # --- REPLACE ---
            for key, values in REPLACE.items():
                current = body(text, key)

                if current is None:
                    errors.append("%s: %s absent, cannot replace" % (locale, key))

                    continue

                old = '<string name="%s">%s</string>' % (key, current)

                new = '<string name="%s">%s</string>' % (key, values[locale])

                if text.count(old) != 1:
                    errors.append("%s: %s matched %d times" % (locale, key, text.count(old)))

                    continue

                text = text.replace(old, new, 1)

            # --- DROP, every locale ---
            for key in DROP:
                current = body(text, key)

                if current is None:
                    errors.append("%s: %s absent, cannot drop" % (locale, key))

                    continue

                line = '    <string name="%s">%s</string>\n' % (key, current)

                if text.count(line) != 1:
                    errors.append("%s: %s drop matched %d" % (locale, key, text.count(line)))

                    continue

                text = text.replace(line, "", 1)

            # --- DROP, values/ only: translatable="false" never reached the others ---
            if locale == "values":
                for key in DROP_VALUES_ONLY:
                    m = re.search(
                        r'    <string name="%s"[^>]*>.*?</string>\n' % re.escape(key),
                        text,
                        re.S,
                    )

                    if m is None:
                        errors.append("values: %s absent, cannot drop" % key)

                        continue

                    text = text.replace(m.group(0), "", 1)
            else:
                for key in DROP_VALUES_ONLY:
                    if body(text, key) is not None:
                        errors.append("%s: %s should never have been translated" % (locale, key))

            # --- ADD ---
            additions = []

            for key in sorted(ADD):
                if body(text, key) is not None:
                    errors.append("%s: %s already present" % (locale, key))

                    continue

                additions.append(
                    '    <string name="%s">%s</string>' % (key, ADD[key][locale])
                )

            if additions:
                if text.count("</resources>") != 1:
                    errors.append("%s: expected one </resources>" % locale)

                    continue

                text = text.replace(
                    "</resources>", "\n".join(additions) + "\n</resources>", 1,
                )

            pending[path] = text

    if errors:
        for error in errors:
            print("  ! %s" % error)

        print("REFUSED, nothing written")

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print(
        "wrote %d files: +%d keys x %d locales, 1 replaced, %d dropped everywhere, "
        "%d dropped from values/" % (
            len(pending), len(ADD), len(LOCALES), len(DROP), len(DROP_VALUES_ONLY),
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
