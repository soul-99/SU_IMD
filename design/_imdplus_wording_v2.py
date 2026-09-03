#!/usr/bin/env python3
"""The user's own wording for the IMD+ row and page, replacing the first draft.

Three operations, all on feature/settings:
  REPLACE - keys that exist and whose text the user rewrote
  ADD     - the intro block and the three flow steps that finish the chart
  DROP    - the descriptions the user asked to be removed

English is the user's text verbatim, including its own punctuation and spacing. The other ten
locales say the same thing in their own words.
"""
import os
import re
import sys

BASE = 'feature/settings/src/main/res'

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

REPLACE = {
    # The row in the settings list: two lines of title, one line of description.
    'auto_hide': {
        'values': "Auto hide settings\\n(IMD+ for advanced users only)",
        'values-ar': "إخفاء الإعدادات تلقائيًا\\n‏(IMD+ للمستخدمين المتقدمين فقط)",
        'values-b+pt+BR': "Ocultar configurações automaticamente\\n(IMD+ apenas para usuários avançados)",
        'values-b+zh+Hans': "自动隐藏设置\\n（IMD+，仅限高级用户）",
        'values-de': "Einstellungen automatisch ausblenden\\n(IMD+, nur für erfahrene Nutzer)",
        'values-es': "Ocultar ajustes automáticamente\\n(IMD+, solo para usuarios avanzados)",
        'values-fr': "Masquage automatique des paramètres\\n(IMD+, utilisateurs avancés uniquement)",
        'values-hi': "सेटिंग्स अपने आप छिपाएँ\\n(IMD+ केवल उन्नत उपयोगकर्ताओं के लिए)",
        'values-ja': "設定を自動で非表示\\n（IMD+、上級者向け）",
        'values-ko': "설정 자동 숨기기\\n(IMD+, 고급 사용자 전용)",
        'values-ru': "Автоскрытие настроек\\n(IMD+, только для опытных пользователей)",
    },
    'auto_hide_setup': {
        'values': "click to setup",
        'values-ar': "انقر للإعداد",
        'values-b+pt+BR': "toque para configurar",
        'values-b+zh+Hans': "点按进行设置",
        'values-de': "zum Einrichten tippen",
        'values-es': "toca para configurar",
        'values-fr': "appuyez pour configurer",
        'values-hi': "सेटअप के लिए टैप करें",
        'values-ja': "タップして設定",
        'values-ko': "눌러서 설정",
        'values-ru': "нажмите, чтобы настроить",
    },

    'auto_hide_req_accessibility_note': {
        'values': "to detect app launches",
        'values-ar': "لاكتشاف فتح التطبيقات",
        'values-b+pt+BR': "para detectar a abertura de apps",
        'values-b+zh+Hans': "用于检测应用启动",
        'values-de': "um App-Starts zu erkennen",
        'values-es': "para detectar la apertura de apps",
        'values-fr': "pour détecter le lancement des applications",
        'values-hi': "ऐप खुलने का पता लगाने के लिए",
        'values-ja': "アプリの起動を検知するため",
        'values-ko': "앱 실행을 감지하기 위해",
        'values-ru': "чтобы обнаруживать запуск приложений",
    },
    'auto_hide_req_shizuku_permission_note': {
        'values': "to kill app on first launch",
        'values-ar': "لإنهاء التطبيق عند التشغيل الأول",
        'values-b+pt+BR': "para encerrar o app na primeira abertura",
        'values-b+zh+Hans': "用于在首次启动时结束应用",
        'values-de': "um die App beim ersten Start zu beenden",
        'values-es': "para cerrar la app en el primer arranque",
        'values-fr': "pour fermer l\\'application au premier lancement",
        'values-hi': "पहली बार खुलने पर ऐप बंद करने के लिए",
        'values-ja': "最初の起動でアプリを終了するため",
        'values-ko': "첫 실행에서 앱을 종료하기 위해",
        'values-ru': "чтобы закрыть приложение при первом запуске",
    },
    'auto_hide_req_shizuku_configured': {
        'values': "Shizuku configuration in IMD",
        'values-ar': "‏إعداد Shizuku في IMD",
        'values-b+pt+BR': "Configuração do Shizuku no IMD",
        'values-b+zh+Hans': "IMD 中的 Shizuku 配置",
        'values-de': "Shizuku-Konfiguration in IMD",
        'values-es': "Configuración de Shizuku en IMD",
        'values-fr': "Configuration Shizuku dans IMD",
        'values-hi': "IMD में Shizuku कॉन्फ़िगरेशन",
        'values-ja': "IMD 内の Shizuku 設定",
        'values-ko': "IMD의 Shizuku 설정",
        'values-ru': "Настройка Shizuku в IMD",
    },
    'auto_hide_req_shizuku_configured_note': {
        'values': "to start shizuku if not running ",
        'values-ar': "‏لبدء Shizuku إن لم يكن يعمل",
        'values-b+pt+BR': "para iniciar o Shizuku se não estiver em execução",
        'values-b+zh+Hans': "用于在 Shizuku 未运行时启动它",
        'values-de': "um Shizuku zu starten, falls es nicht läuft",
        'values-es': "para iniciar Shizuku si no está en marcha",
        'values-fr': "pour démarrer Shizuku s\\'il ne tourne pas",
        'values-hi': "Shizuku न चल रहा हो तो उसे शुरू करने के लिए",
        'values-ja': "Shizuku が動いていないときに起動するため",
        'values-ko': "Shizuku가 실행 중이 아니면 시작하기 위해",
        'values-ru': "чтобы запустить Shizuku, если он не работает",
    },
    'auto_hide_req_battery': {
        'values': "Disable battery optimisation",
        'values-ar': "تعطيل تحسين البطارية",
        'values-b+pt+BR': "Desativar otimização de bateria",
        'values-b+zh+Hans': "关闭电池优化",
        'values-de': "Akku-Optimierung deaktivieren",
        'values-es': "Desactivar la optimización de batería",
        'values-fr': "Désactiver l\\'optimisation de la batterie",
        'values-hi': "बैटरी ऑप्टिमाइज़ेशन बंद करें",
        'values-ja': "電池の最適化を無効にする",
        'values-ko': "배터리 최적화 끄기",
        'values-ru': "Отключить оптимизацию батареи",
    },
    'auto_hide_req_battery_note': {
        'values': "to keep IMD alive",
        'values-ar': "‏لإبقاء IMD نشطًا",
        'values-b+pt+BR': "para manter o IMD ativo",
        'values-b+zh+Hans': "用于让 IMD 保持运行",
        'values-de': "damit IMD am Leben bleibt",
        'values-es': "para mantener IMD activo",
        'values-fr': "pour garder IMD actif",
        'values-hi': "IMD को चालू रखने के लिए",
        'values-ja': "IMD を動き続けさせるため",
        'values-ko': "IMD를 계속 살아 있게 하려고",
        'values-ru': "чтобы IMD оставался активным",
    },
    'auto_hide_req_notifications': {
        'values': "Notification permission",
        'values-ar': "إذن الإشعارات",
        'values-b+pt+BR': "Permissão de notificação",
        'values-b+zh+Hans': "通知权限",
        'values-de': "Benachrichtigungsberechtigung",
        'values-es': "Permiso de notificaciones",
        'values-fr': "Autorisation de notification",
        'values-hi': "सूचना अनुमति",
        'values-ja': "通知の権限",
        'values-ko': "알림 권한",
        'values-ru': "Разрешение на уведомления",
    },
    'auto_hide_req_notifications_note': {
        'values': "to send revert notification",
        'values-ar': "لإرسال إشعار الاستعادة",
        'values-b+pt+BR': "para enviar a notificação de reversão",
        'values-b+zh+Hans': "用于发送还原通知",
        'values-de': "um die Zurücksetzen-Benachrichtigung zu senden",
        'values-es': "para enviar la notificación de reversión",
        'values-fr': "pour envoyer la notification de restauration",
        'values-hi': "वापसी की सूचना भेजने के लिए",
        'values-ja': "復元の通知を送るため",
        'values-ko': "되돌리기 알림을 보내기 위해",
        'values-ru': "чтобы отправить уведомление о возврате",
    },
    'auto_hide_no_kill_launch': {
        'values': "Do not kill app on first launch(recommended off)",
        'values-ar': "لا تُنهِ التطبيق عند التشغيل الأول (يُنصح بإبقائه معطّلًا)",
        'values-b+pt+BR': "Não encerrar o app na primeira abertura (recomendado desligado)",
        'values-b+zh+Hans': "首次启动时不要结束应用（建议关闭）",
        'values-de': "Die App beim ersten Start nicht beenden (empfohlen: aus)",
        'values-es': "No cerrar la app en el primer arranque (recomendado desactivado)",
        'values-fr': "Ne pas fermer l\\'application au premier lancement (recommandé : désactivé)",
        'values-hi': "पहली बार खुलने पर ऐप बंद न करें (बंद रखना बेहतर)",
        'values-ja': "最初の起動でアプリを終了しない（オフ推奨）",
        'values-ko': "첫 실행에서 앱을 종료하지 않기 (끄는 것을 권장)",
        'values-ru': "Не закрывать приложение при первом запуске (рекомендуется выкл.)",
    },
    'auto_hide_no_kill_launch_note': {
        'values': "your apps might detect settings before they are hidden by IMD+",
        'values-ar': "‏قد تكتشف تطبيقاتك الإعدادات قبل أن يُخفيها IMD+",
        'values-b+pt+BR': "os seus apps podem detectar as configurações antes de o IMD+ ocultá-las",
        'values-b+zh+Hans': "你的应用可能在 IMD+ 隐藏设置之前就发现它们",
        'values-de': "Deine Apps könnten die Einstellungen sehen, bevor IMD+ sie ausblendet",
        'values-es': "tus apps podrían detectar los ajustes antes de que IMD+ los oculte",
        'values-fr': "vos applications risquent de voir les paramètres avant qu\\'IMD+ ne les masque",
        'values-hi': "IMD+ के छिपाने से पहले ही आपके ऐप्स सेटिंग्स पकड़ सकते हैं",
        'values-ja': "IMD+ が隠す前にアプリが設定を検知するおそれがあります",
        'values-ko': "IMD+가 숨기기 전에 앱이 설정을 감지할 수 있습니다",
        'values-ru': "ваши приложения могут заметить настройки до того, как IMD+ их скроет",
    },
}

ADD = {
    # The whole of the page's description, at the top, in the user's own words.
    'auto_hide_intro': {
        'values': "1. Simply open you apps normally from launcher to hide settings and after use press revert button\\n2. IMD needs a background service for this to work.\\n3. Uses only Revert to default mechanism not Memory function.",
        'values-ar': "‏1. افتح تطبيقاتك من مشغّل التطبيقات كالمعتاد لإخفاء الإعدادات، وبعد الاستخدام اضغط زر الاستعادة\\n2. يحتاج IMD إلى خدمة تعمل في الخلفية لهذا الغرض.\\n3. يستخدم آلية «الاستعادة إلى الافتراضي» فقط، وليس وظيفة الذاكرة.",
        'values-b+pt+BR': "1. Basta abrir os seus apps normalmente pelo launcher para ocultar as configurações e, depois de usar, tocar no botão de reverter\\n2. O IMD precisa de um serviço em segundo plano para isso funcionar.\\n3. Usa apenas o mecanismo Reverter para o padrão, não a função de memória.",
        'values-b+zh+Hans': "1. 只需像平常一样从桌面打开你的应用即可隐藏设置，用完后按还原按钮\\n2. IMD 需要一个后台服务才能实现这一点。\\n3. 只使用“还原为默认”机制，不使用记忆功能。",
        'values-de': "1. Öffne deine Apps einfach wie gewohnt vom Launcher aus, um die Einstellungen auszublenden, und drücke nach der Nutzung auf Zurücksetzen\\n2. IMD braucht dafür einen Hintergrunddienst.\\n3. Nutzt nur den Mechanismus „Auf Standard zurücksetzen“, nicht die Speicherfunktion.",
        'values-es': "1. Abre tus apps normalmente desde el launcher para ocultar los ajustes y, al terminar, pulsa el botón de revertir\\n2. IMD necesita un servicio en segundo plano para que esto funcione.\\n3. Usa solo el mecanismo Revertir a los valores por defecto, no la función de memoria.",
        'values-fr': "1. Ouvrez simplement vos applications normalement depuis le lanceur pour masquer les paramètres, puis appuyez sur le bouton de restauration après usage\\n2. IMD a besoin d\\'un service en arrière-plan pour cela.\\n3. N\\'utilise que le mécanisme Restaurer les valeurs par défaut, pas la fonction mémoire.",
        'values-hi': "1. सेटिंग्स छिपाने के लिए बस अपने ऐप्स लॉन्चर से सामान्य रूप से खोलें, और इस्तेमाल के बाद रिवर्ट बटन दबाएँ\\n2. इसके काम करने के लिए IMD को एक बैकग्राउंड सेवा चाहिए।\\n3. केवल ‘डिफ़ॉल्ट पर वापस लाएँ’ तरीका इस्तेमाल करता है, मेमोरी फ़ंक्शन नहीं।",
        'values-ja': "1. 設定を隠すには、ランチャーからいつもどおりアプリを開くだけです。使い終わったら復元ボタンを押してください\\n2. これには IMD のバックグラウンドサービスが必要です。\\n3. 「既定に戻す」方式のみを使用し、メモリー機能は使いません。",
        'values-ko': "1. 설정을 숨기려면 런처에서 평소처럼 앱을 열기만 하면 됩니다. 사용 후에는 되돌리기 버튼을 누르세요\\n2. 이를 위해 IMD에는 백그라운드 서비스가 필요합니다.\\n3. ‘기본값으로 되돌리기’ 방식만 사용하며, 메모리 기능은 사용하지 않습니다.",
        'values-ru': "1. Просто открывайте приложения из лаунчера как обычно, чтобы настройки скрылись, а после использования нажмите кнопку возврата\\n2. Для этого IMD нужна фоновая служба.\\n3. Использует только механизм «Вернуть к значениям по умолчанию», а не функцию памяти.",
    },

    'auto_hide_flow_7': {
        'values': "You press the notification, or the Hide settings tile.",
        'values-ar': "تضغط على الإشعار، أو على مربّع «إخفاء الإعدادات».",
        'values-b+pt+BR': "Você toca na notificação ou no bloco Ocultar configurações.",
        'values-b+zh+Hans': "你按下该通知，或“隐藏设置”磁贴。",
        'values-de': "Du tippst auf die Benachrichtigung oder auf die Kachel „Einstellungen ausblenden“.",
        'values-es': "Pulsas la notificación o el mosaico Ocultar ajustes.",
        'values-fr': "Vous appuyez sur la notification ou sur la tuile Masquer les paramètres.",
        'values-hi': "आप उस सूचना पर, या “सेटिंग्स छिपाएँ” टाइल पर दबाते हैं।",
        'values-ja': "その通知、または「設定を非表示」タイルを押します。",
        'values-ko': "그 알림이나 ‘설정 숨기기’ 타일을 누릅니다.",
        'values-ru': "Вы нажимаете уведомление или плитку «Скрыть настройки».",
    },
    'auto_hide_flow_8': {
        'values': "IMD restores your defaults. No app is closed.",
        'values-ar': "‏يستعيد IMD إعداداتك الافتراضية. لا يُغلق أي تطبيق.",
        'values-b+pt+BR': "O IMD restaura os seus padrões. Nenhum app é fechado.",
        'values-b+zh+Hans': "IMD 恢复你的默认配置。不会关闭任何应用。",
        'values-de': "IMD stellt deine Standardwerte wieder her. Keine App wird geschlossen.",
        'values-es': "IMD restaura tus valores por defecto. No se cierra ninguna app.",
        'values-fr': "IMD restaure vos valeurs par défaut. Aucune application n\\'est fermée.",
        'values-hi': "IMD आपकी डिफ़ॉल्ट सेटिंग्स बहाल कर देता है। कोई ऐप बंद नहीं किया जाता।",
        'values-ja': "IMD が既定値を復元します。アプリは終了されません。",
        'values-ko': "IMD가 기본값을 복원합니다. 어떤 앱도 닫히지 않습니다.",
        'values-ru': "IMD восстанавливает значения по умолчанию. Ни одно приложение не закрывается.",
    },
    'auto_hide_flow_9': {
        'values': "IMD's own accessibility service comes back with the rest, and IMD+ is armed again.",
        'values-ar': "‏تعود خدمة إمكانية الوصول الخاصة بـ IMD مع البقية، ويصبح IMD+ جاهزًا من جديد.",
        'values-b+pt+BR': "O serviço de acessibilidade do próprio IMD volta junto com o resto, e o IMD+ fica pronto de novo.",
        'values-b+zh+Hans': "IMD 自己的无障碍服务随其余项目一同恢复，IMD+ 重新就绪。",
        'values-de': "IMDs eigener Bedienungshilfen-Dienst kommt mit den anderen zurück, und IMD+ ist wieder scharf.",
        'values-es': "El servicio de accesibilidad del propio IMD vuelve con los demás, e IMD+ queda listo otra vez.",
        'values-fr': "Le service d\\'accessibilité d\\'IMD revient avec les autres, et IMD+ est de nouveau actif.",
        'values-hi': "IMD की अपनी एक्सेसिबिलिटी सेवा बाकियों के साथ लौट आती है, और IMD+ फिर से तैयार हो जाता है।",
        'values-ja': "IMD 自身のユーザー補助サービスも他と一緒に戻り、IMD+ は再び待機状態になります。",
        'values-ko': "IMD 자체 접근성 서비스도 나머지와 함께 돌아오고, IMD+가 다시 준비됩니다.",
        'values-ru': "Собственная служба специальных возможностей IMD возвращается вместе с остальными, и IMD+ снова наготове.",
    },
}

DROP = [
    'auto_hide_description',
    'auto_hide_how_it_works_summary',
    'auto_hide_info_pending',
    'auto_hide_info_deaf',
    'auto_hide_info_hide_list',
    'auto_hide_info_battery',
    'auto_hide_flow_revert',
    'auto_hide_summary_blocked',
    'auto_hide_summary_incomplete',
    'auto_hide_summary_on',
]


def main():
    problems = []

    for table in (REPLACE, ADD):
        for key, t in table.items():
            missing = [loc for loc in L if loc not in t]

            if missing:
                problems.append(f'{key}: missing {missing}')

    if problems:
        print('PROBLEMS (nothing written):')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    for loc in L:
        path = os.path.join(BASE, loc, 'strings.xml')
        src = open(path, encoding='utf-8').read()

        replaced = added = dropped = 0

        for key, t in REPLACE.items():
            pattern = re.compile(rf'<string name="{key}">.*?</string>', re.DOTALL)

            if len(pattern.findall(src)) != 1:
                print(f'{loc}: expected exactly one {key}')
                sys.exit(1)

            src = pattern.sub(f'<string name="{key}">{t[loc]}</string>', src, count=1)
            replaced += 1

        for key in DROP:
            pattern = re.compile(rf'\n *<string name="{key}">.*?</string>', re.DOTALL)

            src, n = pattern.subn('', src, count=1)
            dropped += n

        add = [
            f'    <string name="{k}">{t[loc]}</string>'
            for k, t in ADD.items() if f'name="{k}"' not in src
        ]

        if add:
            src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
            added = len(add)

        open(path, 'w', encoding='utf-8').write(src)

        print(f'{loc:18s} ~{replaced}  +{added}  -{dropped}')

    print('OK')


if __name__ == '__main__':
    main()
