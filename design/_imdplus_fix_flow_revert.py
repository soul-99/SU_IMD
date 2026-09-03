#!/usr/bin/env python3
"""One-off: rewrite auto_hide_flow_revert.

The first version said the watched apps are closed before the settings come back. They are
not: an IMD+ revert now hands straight over to "Revert to default" and closes nothing, so
that it does not have to start Shizuku on a device whose revert has no other use for it.
"""
import os
import re
import sys

BASE = 'feature/settings/src/main/res'

KEY = 'auto_hide_flow_revert'

NEW = {
    'values': "Tapping that notification puts everything back: your defaults are restored, and the accessibility services come back with them — IMD\\'s own detector among them.",
    'values-ar': "‏النقر على ذلك الإشعار يعيد كل شيء: تُستعاد إعداداتك الافتراضية، وتعود معها خدمات إمكانية الوصول — ومنها كاشف IMD نفسه.",
    'values-b+pt+BR': "Tocar nessa notificação devolve tudo: os seus padrões são restaurados e os serviços de acessibilidade voltam junto — inclusive o detector do próprio IMD.",
    'values-b+zh+Hans': "点按该通知即可还原一切：恢复你的默认配置，各项无障碍服务也随之回来——其中包括 IMD 自己的检测器。",
    'values-de': "Ein Tippen auf diese Benachrichtigung stellt alles wieder her: Deine Standardwerte kommen zurück, und mit ihnen die Bedienungshilfen-Dienste — darunter IMDs eigener Detektor.",
    'values-es': "Al tocar esa notificación se devuelve todo: se restauran tus valores por defecto y con ellos vuelven los servicios de accesibilidad, incluido el detector del propio IMD.",
    'values-fr': "Appuyer sur cette notification remet tout en place : vos valeurs par défaut sont restaurées et les services d\\'accessibilité reviennent avec elles — dont le détecteur d\\'IMD lui-même.",
    'values-hi': "उस सूचना पर टैप करने से सब कुछ वापस आ जाता है: आपकी डिफ़ॉल्ट सेटिंग्स बहाल होती हैं और उनके साथ एक्सेसिबिलिटी सेवाएँ भी लौट आती हैं — जिनमें IMD का अपना डिटेक्टर भी शामिल है।",
    'values-ja': "その通知をタップするとすべてが戻ります。既定値が復元され、ユーザー補助サービスも一緒に戻ります — IMD 自身の検知サービスも含めて。",
    'values-ko': "그 알림을 누르면 모든 것이 되돌아갑니다. 기본값이 복원되고 접근성 서비스도 함께 돌아옵니다 — IMD 자신의 감지기도 포함해서요.",
    'values-ru': "Нажатие на это уведомление возвращает всё обратно: восстанавливаются ваши значения по умолчанию, а вместе с ними возвращаются службы специальных возможностей — включая собственный детектор IMD.",
}

if __name__ == '__main__':
    missing = [loc for loc in NEW if not os.path.exists(os.path.join(BASE, loc, 'strings.xml'))]

    if missing:
        print('missing locales:', missing)
        sys.exit(1)

    for loc, text in NEW.items():
        path = os.path.join(BASE, loc, 'strings.xml')

        src = open(path, encoding='utf-8').read()

        pattern = re.compile(rf'<string name="{KEY}">.*?</string>', re.DOTALL)

        if len(pattern.findall(src)) != 1:
            print(f'{loc}: expected exactly one {KEY}')
            sys.exit(1)

        src = pattern.sub(f'<string name="{KEY}">{text}</string>', src, count=1)

        open(path, 'w', encoding='utf-8').write(src)

        print(f'{loc:18s} rewritten')

    print('OK')
