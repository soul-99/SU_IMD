#!/usr/bin/env python3
"""One-off: the two strings Android itself shows for the IMD+ accessibility service.

The label is what appears in Settings > Accessibility, and the description is the paragraph
under it. "IMD+" is a product name and stays as it is in every locale; only the parenthetical
and the sentence are translated.
"""
import os
import sys

BASE = 'service/src/main/res'

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

NEW = {
    'auto_hide_service_label': {
        'values': "IMD+ (autohide settings)",
        'values-ar': "‏IMD+ (إخفاء الإعدادات تلقائيًا)",
        'values-b+pt+BR': "IMD+ (ocultar configurações automaticamente)",
        'values-b+zh+Hans': "IMD+（自动隐藏设置）",
        'values-de': "IMD+ (Einstellungen automatisch ausblenden)",
        'values-es': "IMD+ (ocultar ajustes automáticamente)",
        'values-fr': "IMD+ (masquage automatique des paramètres)",
        'values-hi': "IMD+ (सेटिंग्स अपने आप छिपाएँ)",
        'values-ja': "IMD+（設定を自動で非表示）",
        'values-ko': "IMD+ (설정 자동 숨기기)",
        'values-ru': "IMD+ (автоскрытие настроек)",
    },
    'auto_hide_service_description': {
        'values': "Lets IMD notice when one of your chosen apps is opened, so it can hide your settings before that app looks at them. IMD only reads which app came to the front — never anything on your screen.",
        'values-ar': "يتيح لـ IMD معرفة متى يُفتح أحد تطبيقاتك المختارة، ليُخفي إعداداتك قبل أن يطّلع عليها ذلك التطبيق. لا يقرأ IMD سوى اسم التطبيق الذي ظهر في المقدمة، ولا يقرأ أي شيء على شاشتك.",
        'values-b+pt+BR': "Permite que o IMD perceba quando um dos apps escolhidos é aberto, para ocultar as suas configurações antes que esse app as veja. O IMD lê apenas qual app veio para a frente — nunca nada da sua tela.",
        'values-b+zh+Hans': "让 IMD 知道你选定的应用何时被打开，以便在该应用查看之前隐藏你的设置。IMD 只读取哪个应用来到前台，绝不读取屏幕上的任何内容。",
        'values-de': "Damit IMD bemerkt, wenn eine deiner ausgewählten Apps geöffnet wird, und deine Einstellungen ausblenden kann, bevor diese App sie sieht. IMD liest nur, welche App in den Vordergrund kam — niemals etwas von deinem Bildschirm.",
        'values-es': "Permite que IMD detecte cuándo se abre una de tus apps elegidas, para ocultar tus ajustes antes de que esa app los vea. IMD solo lee qué app pasó a primer plano, nunca nada de tu pantalla.",
        'values-fr': "Permet à IMD de repérer l\\'ouverture d\\'une de vos applications choisies, afin de masquer vos paramètres avant que cette application ne les consulte. IMD lit uniquement quelle application est passée au premier plan, jamais le contenu de votre écran.",
        'values-hi': "इससे IMD को पता चलता है कि आपका चुना हुआ ऐप कब खोला गया, ताकि वह ऐप देखने से पहले आपकी सेटिंग्स छिपाई जा सकें। IMD सिर्फ़ यह पढ़ता है कि कौन-सा ऐप सामने आया — आपकी स्क्रीन का कुछ भी नहीं।",
        'values-ja': "選んだアプリが開かれたことを IMD が検知し、そのアプリが見る前に設定を非表示にできるようにします。IMD が読み取るのは前面に来たアプリだけで、画面の内容は一切読み取りません。",
        'values-ko': "선택한 앱이 열리는 것을 IMD가 감지해, 그 앱이 보기 전에 설정을 숨길 수 있게 합니다. IMD는 어떤 앱이 앞으로 나왔는지만 읽으며, 화면의 내용은 전혀 읽지 않습니다.",
        'values-ru': "Позволяет IMD замечать, когда открывается одно из выбранных приложений, и скрывать настройки до того, как это приложение их увидит. IMD считывает только то, какое приложение вышло на передний план, и никогда — содержимое экрана.",
    },
}

if __name__ == '__main__':
    problems = []

    for loc in L:
        path = os.path.join(BASE, loc, 'strings.xml')

        if not os.path.exists(path):
            problems.append(f'missing {path}')
            continue

        src = open(path, encoding='utf-8').read()

        add = [
            f'    <string name="{k}">{t[loc]}</string>'
            for k, t in NEW.items() if f'name="{k}"' not in src
        ]

        if add:
            if '</resources>' not in src:
                problems.append(f'{loc}: no </resources>')
                continue

            src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
            open(path, 'w', encoding='utf-8').write(src)

        print(f'{loc:18s} +{len(add)}')

    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print('OK')
