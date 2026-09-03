#!/usr/bin/env python3
"""One-off: the third v2.2 string pass.

* `revert_defaults_shizuku_note` — English drops the stray "modify"; the translations already
  said "enable or disable" and are left alone.
* `help_general_revert` — now names the Hide settings quick toggle as a second way back. The
  tile's name is spelled exactly as `help_launch_tile_name` holds it in that locale, or the
  highlighting in SetupHelp would find nothing to colour.

Every replacement asserts its match count.
"""
import os
import re
import sys

SETTINGS = 'feature/settings/src/main/res'

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

REPLACE = {
    'revert_defaults_shizuku_note': {
        'values': "Depending on which method Shizuku uses to keep service alive, it will enable/disable USB or wireless debugging.",
    },
    'help_general_revert': {
        'values': "3. After you are done using your app, use the Revert / Revert to default button or Hide settings quick toggle to unhide/ re-enable your previous settings.",
        'values-ar': "٣. بعد انتهائك من استخدام تطبيقك، اضغط على زر استعادة / استعادة الوضع الافتراضي أو استخدم مفتاح إخفاء الإعدادات السريع لإظهار إعداداتك السابقة أو تفعيلها من جديد.",
        'values-b+pt+BR': "3. Quando terminar de usar o seu app, use o botão Reverter / Reverter para o padrão ou o Bloco rápido Ocultar configurações para reexibir/reativar as suas configurações anteriores.",
        'values-b+zh+Hans': "3. 用完您的应用之后，请使用还原 / 还原为默认按钮或“隐藏设置”快捷开关，取消隐藏并重新启用您之前的设置。",
        'values-de': "3. Wenn du mit deiner App fertig bist, blende deine vorherigen Einstellungen mit der Schaltfläche Wiederherstellen / Standard wiederherstellen oder der Schnelleinstellung „Einstellungen ausblenden“ wieder ein bzw. aktiviere sie erneut.",
        'values-es': "3. Cuando termines de usar tu app, usa el botón Revertir / Revertir a valores predeterminados o el Ajuste rápido Ocultar ajustes para volver a mostrar o activar tus ajustes anteriores.",
        'values-fr': "3. Une fois que vous avez fini d\\'utiliser votre application, utilisez le bouton Rétablir / Rétablir par défaut ou la Tuile Masquer les paramètres pour réafficher et réactiver vos paramètres précédents.",
        'values-hi': "3. अपना ऐप इस्तेमाल कर लेने के बाद, अपनी पिछली सेटिंग्स फिर से दिखाने/चालू करने के लिए वापस लाएँ / डिफ़ॉल्ट पर वापस लाएँ बटन या ‘सेटिंग्स छिपाएँ’ क्विक टॉगल का उपयोग करें।",
        'values-ja': "3. アプリを使い終わったら、「元に戻す / デフォルトに戻す」ボタンまたは「設定を非表示」クイック設定タイルで、以前の設定を再表示または再度有効化してください。",
        'values-ko': "3. 앱 사용을 마친 뒤에는 되돌리기 / 기본값으로 되돌리기 버튼이나 ‘설정 숨기기’ 빠른 설정 타일을 눌러 이전 설정을 다시 표시하거나 다시 켜세요.",
        'values-ru': "3. Закончив работу с приложением, нажмите кнопку «Вернуть / Вернуть по умолчанию» или Быструю кнопку «Скрыть настройки», чтобы снова показать и включить прежние настройки.",
    },
}

if __name__ == '__main__':
    problems = []

    for key, per_loc in REPLACE.items():
        for loc, value in per_loc.items():
            path = os.path.join(SETTINGS, loc, 'strings.xml')
            src = open(path, encoding='utf-8').read()

            pattern = re.compile(r'<string name="%s">.*?</string>' % re.escape(key), re.S)
            hits = pattern.findall(src)

            if len(hits) != 1:
                problems.append(f'{loc}/{key}: matched {len(hits)}x')
                continue

            src = pattern.sub(
                lambda _m, v=value, k=key: f'<string name="{k}">{v}</string>',
                src,
                count=1,
            )
            open(path, 'w', encoding='utf-8').write(src)
            print(f'{key:32s} {loc}')

    # The tile name has to appear verbatim in the revert line, or nothing gets highlighted.
    for loc in L:
        path = os.path.join(SETTINGS, loc, 'strings.xml')
        src = open(path, encoding='utf-8').read()

        name = re.search(r'<string name="help_launch_tile_name">(.*?)</string>', src, re.S)
        line = re.search(r'<string name="help_general_revert">(.*?)</string>', src, re.S)

        if not name or not line:
            problems.append(f'{loc}: missing one of the two strings')
            continue

        if name.group(1) not in line.group(1):
            problems.append(f'{loc}: revert line does not contain "{name.group(1)}"')

    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print('OK - every locale names the tile exactly as its own label spells it')
