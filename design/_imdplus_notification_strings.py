#!/usr/bin/env python3
"""One-off: the IMD+ notification channel, its notification line, and the two run toasts.

Two modules, because the strings live where they are read: the channel name and the
notification text belong to framework/notification-manager, the toasts to common.

"IMD+" is a product name and stays as it is in every locale.
"""
import os
import sys

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

NOTIFICATION = {
    'auto_hide_channel': {
        'values': "Auto-hide settings (IMD+)",
        'values-ar': "‏إخفاء الإعدادات تلقائيًا (IMD+)",
        'values-b+pt+BR': "Ocultar configurações automaticamente (IMD+)",
        'values-b+zh+Hans': "自动隐藏设置（IMD+）",
        'values-de': "Einstellungen automatisch ausblenden (IMD+)",
        'values-es': "Ocultar ajustes automáticamente (IMD+)",
        'values-fr': "Masquage automatique des paramètres (IMD+)",
        'values-hi': "सेटिंग्स अपने आप छिपाएँ (IMD+)",
        'values-ja': "設定を自動で非表示（IMD+）",
        'values-ko': "설정 자동 숨기기 (IMD+)",
        'values-ru': "Автоскрытие настроек (IMD+)",
    },
    'auto_hide_hidden_revert': {
        'values': "IMD+ hid your settings, click to revert.",
        'values-ar': "أخفى IMD+ إعداداتك، انقر للاستعادة.",
        'values-b+pt+BR': "O IMD+ ocultou suas configurações, toque para reverter.",
        'values-b+zh+Hans': "IMD+ 已隐藏你的设置，点按即可还原。",
        'values-de': "IMD+ hat deine Einstellungen ausgeblendet, zum Zurücksetzen tippen.",
        'values-es': "IMD+ ha ocultado tus ajustes, toca para revertir.",
        'values-fr': "IMD+ a masqué vos paramètres, appuyez pour restaurer.",
        'values-hi': "IMD+ ने आपकी सेटिंग्स छिपा दी हैं, वापस लाने के लिए टैप करें।",
        'values-ja': "IMD+ が設定を非表示にしました。タップで元に戻します。",
        'values-ko': "IMD+가 설정을 숨겼습니다. 눌러서 되돌리세요.",
        'values-ru': "IMD+ скрыл ваши настройки, нажмите, чтобы вернуть.",
    },
}

COMMON = {
    'auto_hide_run_toast': {
        'values': "IMD+ is hiding your settings…",
        'values-ar': "يُخفي IMD+ إعداداتك…",
        'values-b+pt+BR': "O IMD+ está ocultando suas configurações…",
        'values-b+zh+Hans': "IMD+ 正在隐藏你的设置…",
        'values-de': "IMD+ blendet deine Einstellungen aus…",
        'values-es': "IMD+ está ocultando tus ajustes…",
        'values-fr': "IMD+ masque vos paramètres…",
        'values-hi': "IMD+ आपकी सेटिंग्स छिपा रहा है…",
        'values-ja': "IMD+ が設定を非表示にしています…",
        'values-ko': "IMD+가 설정을 숨기는 중…",
        'values-ru': "IMD+ скрывает ваши настройки…",
    },
    'auto_hide_revert_toast': {
        'values': "IMD+ is restoring your settings…",
        'values-ar': "يستعيد IMD+ إعداداتك…",
        'values-b+pt+BR': "O IMD+ está restaurando suas configurações…",
        'values-b+zh+Hans': "IMD+ 正在还原你的设置…",
        'values-de': "IMD+ stellt deine Einstellungen wieder her…",
        'values-es': "IMD+ está restaurando tus ajustes…",
        'values-fr': "IMD+ restaure vos paramètres…",
        'values-hi': "IMD+ आपकी सेटिंग्स वापस ला रहा है…",
        'values-ja': "IMD+ が設定を元に戻しています…",
        'values-ko': "IMD+가 설정을 되돌리는 중…",
        'values-ru': "IMD+ восстанавливает ваши настройки…",
    },
}

TARGETS = [
    ('framework/notification-manager/src/main/res', NOTIFICATION),
    ('common/src/main/res', COMMON),
]


def main():
    problems = []
    added = 0

    for base, table in TARGETS:
        # Every key must carry every locale, or a locale silently falls back to English.
        for key, translations in table.items():
            missing = [loc for loc in L if loc not in translations]

            if missing:
                problems.append(f'{key}: missing {missing}')

        for loc in L:
            path = os.path.join(base, loc, 'strings.xml')

            if not os.path.exists(path):
                problems.append(f'missing {path}')
                continue

            src = open(path, encoding='utf-8').read()

            add = [
                f'    <string name="{k}">{t[loc]}</string>'
                for k, t in table.items() if f'name="{k}"' not in src
            ]

            if add:
                if '</resources>' not in src:
                    problems.append(f'{loc}: no </resources> in {path}')
                    continue

                src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
                open(path, 'w', encoding='utf-8').write(src)
                added += len(add)

            print(f'{base.split("/")[0]:22s} {loc:18s} +{len(add)}')

    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print(f'OK, {added} strings added')


if __name__ == '__main__':
    main()
