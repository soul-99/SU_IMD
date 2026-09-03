#!/usr/bin/env python3
"""One-off: rename the tile inside the two user-facing strings that quote it.

The tile itself is now called "Hide settings" (its per-state labels, Settings visible /
Settings hidden, are unchanged). Two strings name it in prose and have to follow.

Targeted phrase substitution rather than a whole-string rewrite, so the surrounding
translation is left exactly as it was. Every substitution asserts its match count.
"""
import os
import sys

BASE = 'feature/settings/src/main/res'

# locale -> (old phrase, new phrase), applied to both strings below wherever it appears.
PHRASES = {
    'values': ("Settings visible/hidden QS toggle", "Hide settings QS toggle"),
    'values-ar': ("مفتاح «الإعدادات ظاهرة/مخفية» في الإعدادات السريعة",
                  "مفتاح «إخفاء الإعدادات» في الإعدادات السريعة"),
    'values-b+pt+BR': ("Bloco Configurações visíveis/ocultas", "Bloco Ocultar configurações"),
    'values-b+zh+Hans': ("“设置可见/已隐藏”快捷开关", "“隐藏设置”快捷开关"),
    'values-de': ("Kachel „Einstellungen sichtbar/ausgeblendet“",
                  "Kachel „Einstellungen ausblenden“"),
    'values-es': ("Ajuste rápido Ajustes visibles/ocultos", "Ajuste rápido Ocultar ajustes"),
    'values-fr': ("Tuile Paramètres visibles/masqués", "Tuile Masquer les paramètres"),
    'values-hi': ("‘सेटिंग्स दिख रही/छिपी’ QS टॉगल", "‘सेटिंग्स छिपाएँ’ QS टॉगल"),
    'values-ja': ("「設定 表示中/非表示」タイル", "「設定を非表示」タイル"),
    'values-ko': ("‘설정 표시/숨김’ 빠른 설정 타일", "‘설정 숨기기’ 빠른 설정 타일"),
    'values-ru': ("Кнопки «Настройки видимы/скрыты» в быстрых настройках",
                  "Кнопки «Скрыть настройки» в быстрых настройках"),
}

# The memory-function warning list quotes it a second time, with its own lead-in per locale.
EXTRA = {
    'values': ("Revert using the Settings visible/hidden QS toggle",
               "Revert using the Hide settings QS toggle"),
}

if __name__ == '__main__':
    problems = []

    for loc, (old, new) in PHRASES.items():
        path = os.path.join(BASE, loc, 'strings.xml')
        src = open(path, encoding='utf-8').read()

        # EXTRA first: its old text contains the plain phrase, so replacing the plain one
        # first would leave the longer form half-renamed.
        done = 0

        if loc in EXTRA:
            e_old, e_new = EXTRA[loc]
            n = src.count(e_old)
            if n != 1:
                problems.append(f'{loc}: extra phrase matched {n}x')
            else:
                src = src.replace(e_old, e_new, 1)
                done += 1

        n = src.count(old)
        if n < 1:
            problems.append(f'{loc}: phrase matched {n}x')
        else:
            src = src.replace(old, new)
            done += n

        open(path, 'w', encoding='utf-8').write(src)
        print(f'{loc:18s} {done} substitution(s)')

    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print('OK')
