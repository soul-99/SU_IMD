#!/usr/bin/env python3
"""One-off: move the three hide-tile strings from feature:settings into :app.

The tile service, its manifest entry and its labels all live in :app, and a non-transitive
R class means :app cannot read feature:settings' string ids by name. Asserts every move.
"""
import os
import re
import sys

KEYS = ['hide_tile_label', 'hide_tile_visible', 'hide_tile_hidden']
SRC = 'feature/settings/src/main/res'
DST = 'app/src/main/res'
LOCALES = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de',
           'values-es', 'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

problems = []

for loc in LOCALES:
    src_path = os.path.join(SRC, loc, 'strings.xml')
    dst_path = os.path.join(DST, loc, 'strings.xml')

    for p in (src_path, dst_path):
        if not os.path.exists(p):
            problems.append(f'{loc}: missing {p}')

    if problems:
        continue

    src = open(src_path, encoding='utf-8').read()
    dst = open(dst_path, encoding='utf-8').read()

    moved = []

    for key in KEYS:
        pattern = re.compile(r'[ \t]*<string name="%s">.*?</string>\n' % re.escape(key), re.S)
        found = pattern.findall(src)

        if len(found) != 1:
            if f'name="{key}"' in dst:
                continue
            problems.append(f'{loc}: {key} found {len(found)}x in source, 0x in destination')
            continue

        src = pattern.sub('', src, count=1)
        moved.append('    ' + found[0].strip())

    if moved:
        if '</resources>' not in dst:
            problems.append(f'{loc}: no </resources> in {dst_path}')
            continue

        dst = dst.replace('</resources>', '\n'.join(moved) + '\n</resources>', 1)
        open(dst_path, 'w', encoding='utf-8').write(dst)
        open(src_path, 'w', encoding='utf-8').write(src)

    print(f'{loc:18s} moved {len(moved)}')

if problems:
    print('PROBLEMS:')
    for p in problems:
        print('  -', p)
    sys.exit(1)

print('OK')
