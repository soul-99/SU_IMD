#!/usr/bin/env python3
"""One-off: a third bullet in the memory-function notice, for Auto-hide settings (IMD+).

The notice lists the places the device-wide "Settings to hide" list is still read while the
memory function is chosen. IMD+ is now one of them: it applies that list, not a per-app profile,
because the app it reacts to may never have been configured in IMD at all.
"""
import os
import re
import sys

BASE = 'feature/settings/src/main/res'

KEY = 'memory_hide_notice'

BULLET = {
    'values': "\\n•  Auto hide settings (IMD+)",
    'values-ar': "\\n•  ‏إخفاء الإعدادات تلقائيًا (IMD+)",
    'values-b+pt+BR': "\\n•  Ocultar configurações automaticamente (IMD+)",
    'values-b+zh+Hans': "\\n•  自动隐藏设置（IMD+）",
    'values-de': "\\n•  Einstellungen automatisch ausblenden (IMD+)",
    'values-es': "\\n•  Ocultar ajustes automáticamente (IMD+)",
    'values-fr': "\\n•  Masquage automatique des paramètres (IMD+)",
    'values-hi': "\\n•  सेटिंग्स अपने आप छिपाएँ (IMD+)",
    'values-ja': "\\n•  設定を自動で非表示（IMD+）",
    'values-ko': "\\n•  설정 자동 숨기기 (IMD+)",
    'values-ru': "\\n•  Автоскрытие настроек (IMD+)",
}

if __name__ == '__main__':
    for loc, bullet in BULLET.items():
        path = os.path.join(BASE, loc, 'strings.xml')

        if not os.path.exists(path):
            print(f'missing {path}')
            sys.exit(1)

        src = open(path, encoding='utf-8').read()

        pattern = re.compile(rf'(<string name="{KEY}">)(.*?)(</string>)', re.DOTALL)

        found = pattern.findall(src)

        if len(found) != 1:
            print(f'{loc}: expected exactly one {KEY}, found {len(found)}')
            sys.exit(1)

        body = found[0][1]

        # Idempotent: running twice must not add the bullet twice.
        if 'IMD+' in body:
            print(f'{loc:18s} already present')
            continue

        src = pattern.sub(lambda m: m.group(1) + m.group(2) + bullet + m.group(3), src, count=1)

        open(path, 'w', encoding='utf-8').write(src)

        print(f'{loc:18s} +1 bullet')

    print('OK')
