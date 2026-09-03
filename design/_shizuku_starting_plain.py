#!/usr/bin/env python3
"""One-off: the plain 'Starting Shizuku service' line for the IMD+ spinner.

An IMD+ run can wait on Shizuku twice - once to close the app, once for the hide's own overlay
step - so naming either would describe one half of a wait the user experiences as one thing.
"""
import os
import sys

BASE = 'feature/apps/src/main/res'

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

NEW = {
    'shizuku_starting': {
        'values': "Starting Shizuku service",
        'values-ar': "‏جارٍ بدء خدمة Shizuku",
        'values-b+pt+BR': "Iniciando o serviço Shizuku",
        'values-b+zh+Hans': "正在启动 Shizuku 服务",
        'values-de': "Shizuku-Dienst wird gestartet",
        'values-es': "Iniciando el servicio Shizuku",
        'values-fr': "Démarrage du service Shizuku",
        'values-hi': "Shizuku सेवा शुरू हो रही है",
        'values-ja': "Shizuku サービスを開始しています",
        'values-ko': "Shizuku 서비스를 시작하는 중",
        'values-ru': "Запуск службы Shizuku",
    },
}

if __name__ == '__main__':
    added = 0

    for loc in L:
        path = os.path.join(BASE, loc, 'strings.xml')

        if not os.path.exists(path):
            print(f'missing {path}')
            sys.exit(1)

        src = open(path, encoding='utf-8').read()

        add = [
            f'    <string name="{k}">{t[loc]}</string>'
            for k, t in NEW.items() if f'name="{k}">' not in src
        ]

        if add:
            src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
            open(path, 'w', encoding='utf-8').write(src)
            added += len(add)

        print(f'{loc:18s} +{len(add)}')

    print(f'OK, {added} added')
