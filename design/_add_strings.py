#!/usr/bin/env python3
"""One-off: add the v2.2 strings to feature:settings in every locale."""
import os
import re

BASE = 'feature/settings/src/main/res'
L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

NEW = {
    'memory_hide_notice': {
        'values': "Memory function is enabled, only using these for:\\n•  Settings visible/hidden QS toggle\\n•  IMD intents",
        'values-ar': "وظيفة الذاكرة مفعّلة، ولا تُستخدم هذه الإعدادات إلا مع:\\n•  مفتاح «الإعدادات ظاهرة/مخفية» في الإعدادات السريعة\\n•  نوايا IMD",
        'values-b+pt+BR': "A função de memória está ativada; estas só são usadas para:\\n•  Bloco Configurações visíveis/ocultas\\n•  Intents do IMD",
        'values-b+zh+Hans': "记忆功能已启用，这些设置仅用于：\\n•  “设置可见/已隐藏”快捷开关\\n•  IMD intents",
        'values-de': "Die Speicherfunktion ist aktiv; diese werden nur verwendet für:\\n•  Kachel „Einstellungen sichtbar/ausgeblendet“\\n•  IMD intents",
        'values-es': "La función de memoria está activada; estos solo se usan para:\\n•  Ajuste rápido Ajustes visibles/ocultos\\n•  Intents de IMD",
        'values-fr': "La fonction mémoire est activée ; ceux-ci ne servent que pour :\\n•  Tuile Paramètres visibles/masqués\\n•  Intents IMD",
        'values-hi': "मेमोरी फ़ंक्शन चालू है, ये केवल इनके लिए इस्तेमाल होते हैं:\\n•  ‘सेटिंग्स दिख रही/छिपी’ QS टॉगल\\n•  IMD intents",
        'values-ja': "メモリー機能が有効です。これらは次の場合にのみ使われます:\\n•  「設定 表示中/非表示」タイル\\n•  IMD intents",
        'values-ko': "메모리 기능이 켜져 있습니다. 이 설정은 다음에만 사용됩니다:\\n•  ‘설정 표시/숨김’ 빠른 설정 타일\\n•  IMD intents",
        'values-ru': "Функция памяти включена; эти настройки используются только для:\\n•  Кнопки «Настройки видимы/скрыты» в быстрых настройках\\n•  Интентов IMD",
    },
    'relaunch_app': {
        'values': "Re-launch app",
        'values-ar': "إعادة تشغيل التطبيق",
        'values-b+pt+BR': "Reiniciar o app",
        'values-b+zh+Hans': "重新启动应用",
        'values-de': "App neu starten",
        'values-es': "Reiniciar la app",
        'values-fr': "Relancer l\\'application",
        'values-hi': "ऐप फिर से खोलें",
        'values-ja': "アプリを再起動",
        'values-ko': "앱 다시 실행",
        'values-ru': "Перезапустить приложение",
    },
    'pending_reverts_running': {
        'values': "Performing all the pending reverts",
        'values-ar': "جارٍ تنفيذ كل عمليات الاستعادة المعلّقة",
        'values-b+pt+BR': "Executando todas as reversões pendentes",
        'values-b+zh+Hans': "正在执行所有待处理的还原",
        'values-de': "Alle ausstehenden Rücksetzungen werden ausgeführt",
        'values-es': "Realizando todas las reversiones pendientes",
        'values-fr': "Exécution de toutes les restaurations en attente",
        'values-hi': "सभी बाक़ी रिवर्ट किए जा रहे हैं",
        'values-ja': "保留中の復元をすべて実行しています",
        'values-ko': "대기 중인 되돌리기를 모두 수행하는 중",
        'values-ru': "Выполняются все отложенные возвраты",
    },
    'hide_tile_label': {
        'values': "Settings visible/hidden",
        'values-ar': "الإعدادات ظاهرة/مخفية",
        'values-b+pt+BR': "Configurações visíveis/ocultas",
        'values-b+zh+Hans': "设置可见/已隐藏",
        'values-de': "Einstellungen sichtbar/ausgeblendet",
        'values-es': "Ajustes visibles/ocultos",
        'values-fr': "Paramètres visibles/masqués",
        'values-hi': "सेटिंग्स दिख रही/छिपी",
        'values-ja': "設定 表示中/非表示",
        'values-ko': "설정 표시/숨김",
        'values-ru': "Настройки видимы/скрыты",
    },
    'hide_tile_visible': {
        'values': "Settings visible",
        'values-ar': "الإعدادات ظاهرة",
        'values-b+pt+BR': "Configurações visíveis",
        'values-b+zh+Hans': "设置可见",
        'values-de': "Einstellungen sichtbar",
        'values-es': "Ajustes visibles",
        'values-fr': "Paramètres visibles",
        'values-hi': "सेटिंग्स दिख रही हैं",
        'values-ja': "設定 表示中",
        'values-ko': "설정 표시됨",
        'values-ru': "Настройки видимы",
    },
    'hide_tile_hidden': {
        'values': "Settings hidden",
        'values-ar': "الإعدادات مخفية",
        'values-b+pt+BR': "Configurações ocultas",
        'values-b+zh+Hans': "设置已隐藏",
        'values-de': "Einstellungen ausgeblendet",
        'values-es': "Ajustes ocultos",
        'values-fr': "Paramètres masqués",
        'values-hi': "सेटिंग्स छिपी हैं",
        'values-ja': "設定 非表示",
        'values-ko': "설정 숨김",
        'values-ru': "Настройки скрыты",
    },
}

if __name__ == '__main__':
    for loc in L:
        p = os.path.join(BASE, loc, 'strings.xml')
        s = open(p, encoding='utf-8').read()
        add = [
            f'    <string name="{k}">{t[loc]}</string>'
            for k, t in NEW.items() if f'name="{k}"' not in s
        ]
        if not add:
            print(f'{loc:18s} already present')
            continue
        s = s.replace('</resources>', '\n'.join(add) + '\n</resources>')
        open(p, 'w', encoding='utf-8').write(s)
        print(f'{loc:18s} +{len(add)}')
