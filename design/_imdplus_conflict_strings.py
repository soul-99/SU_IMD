#!/usr/bin/env python3
"""One-off: the IMD+ conflict dialog (feature/apps) and its snackbar (feature/app-settings)."""
import os
import sys

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

APPS = {
    'auto_hide_conflict_title': {
        'values': "IMD+ is holding your settings",
        'values-ar': "‏يحتفظ IMD+ بإعداداتك مخفية",
        'values-b+pt+BR': "O IMD+ está mantendo as suas configurações ocultas",
        'values-b+zh+Hans': "IMD+ 正在保持你的设置处于隐藏状态",
        'values-de': "IMD+ hält deine Einstellungen ausgeblendet",
        'values-es': "IMD+ mantiene tus ajustes ocultos",
        'values-fr': "IMD+ garde vos paramètres masqués",
        'values-hi': "IMD+ ने आपकी सेटिंग्स छिपा रखी हैं",
        'values-ja': "IMD+ が設定を非表示のまま保持しています",
        'values-ko': "IMD+가 설정을 숨긴 채로 유지하고 있습니다",
        'values-ru': "IMD+ удерживает ваши настройки скрытыми",
    },
    'auto_hide_conflict_body': {
        'values': "Auto-hide settings (IMD+) has already hidden the device-wide list, and this app\\'s profile asks for something it does not cover. Hiding more on top of that would leave settings that neither revert puts back.",
        'values-ar': "‏سبق أن أخفى IMD+ القائمة العامة للجهاز، وملف هذا التطبيق يطلب شيئًا لا تشمله. إخفاء المزيد فوق ذلك سيترك إعدادات لا تعيدها أيٌّ من عمليتي الاستعادة.",
        'values-b+pt+BR': "O IMD+ já ocultou a lista de todo o aparelho, e o perfil deste app pede algo que ela não cobre. Ocultar mais por cima disso deixaria configurações que nenhuma das duas reversões devolve.",
        'values-b+zh+Hans': "IMD+ 已经隐藏了设备级列表，而此应用的配置要求的内容不在其中。在此之上再隐藏更多，会留下两种还原都无法恢复的设置。",
        'values-de': "IMD+ hat die geräteweite Liste bereits ausgeblendet, und das Profil dieser App verlangt etwas, das sie nicht abdeckt. Noch mehr darüber auszublenden hinterließe Einstellungen, die keines der beiden Zurücksetzen wiederherstellt.",
        'values-es': "IMD+ ya ha ocultado la lista de todo el dispositivo, y el perfil de esta app pide algo que esa lista no cubre. Ocultar más encima dejaría ajustes que ninguna de las dos reversiones devuelve.",
        'values-fr': "IMD+ a déjà masqué la liste valable pour tout l\\'appareil, et le profil de cette application demande quelque chose qu\\'elle ne couvre pas. En masquer davantage par-dessus laisserait des paramètres qu\\'aucune des deux restaurations ne remet en place.",
        'values-hi': "IMD+ पहले ही डिवाइस-व्यापी सूची छिपा चुका है, और इस ऐप की प्रोफ़ाइल कुछ ऐसा माँगती है जो उस सूची में नहीं है। उसके ऊपर और छिपाने से ऐसी सेटिंग्स रह जाएँगी जिन्हें कोई भी वापसी बहाल नहीं करती।",
        'values-ja': "IMD+ はすでに端末全体の一覧を非表示にしており、このアプリのプロファイルはそこに含まれないものを求めています。その上にさらに隠すと、どちらの復元でも戻せない設定が残ります。",
        'values-ko': "IMD+가 이미 기기 전체 목록을 숨겼는데, 이 앱의 프로필은 그 목록에 없는 것을 요구합니다. 그 위에 더 숨기면 어느 되돌리기로도 복원되지 않는 설정이 남습니다.",
        'values-ru': "IMD+ уже скрыл общий список для устройства, а профиль этого приложения требует того, чего в нём нет. Скрыть что-то поверх этого — значит оставить настройки, которые не вернёт ни один из возвратов.",
    },
    'auto_hide_conflict_fix': {
        'values': "Revert IMD+ first — from its notification or the Hide settings tile — then open this app again.",
        'values-ar': "‏استعِد IMD+ أولًا — من إشعاره أو من مربّع «إخفاء الإعدادات» — ثم افتح هذا التطبيق مرة أخرى.",
        'values-b+pt+BR': "Reverta o IMD+ primeiro — pela notificação dele ou pelo bloco Ocultar configurações — e depois abra este app de novo.",
        'values-b+zh+Hans': "请先还原 IMD+——通过它的通知或“隐藏设置”磁贴——然后再打开此应用。",
        'values-de': "Setze zuerst IMD+ zurück — über seine Benachrichtigung oder die Kachel „Einstellungen ausblenden“ — und öffne diese App dann erneut.",
        'values-es': "Revierte primero IMD+, desde su notificación o desde el mosaico Ocultar ajustes, y vuelve a abrir esta app.",
        'values-fr': "Restaurez d\\'abord IMD+ — depuis sa notification ou la tuile Masquer les paramètres — puis rouvrez cette application.",
        'values-hi': "पहले IMD+ को वापस लाएँ — उसकी सूचना से या “सेटिंग्स छिपाएँ” टाइल से — फिर यह ऐप दोबारा खोलें।",
        'values-ja': "まず IMD+ を元に戻してください — その通知か「設定を非表示」タイルから — そのうえでこのアプリを開き直してください。",
        'values-ko': "먼저 IMD+를 되돌리세요 — 알림이나 ‘설정 숨기기’ 타일에서 — 그런 다음 이 앱을 다시 여세요.",
        'values-ru': "Сначала верните IMD+ — из его уведомления или с плитки «Скрыть настройки» — затем откройте это приложение снова.",
    },
}

APP_SETTINGS = {
    'auto_hide_conflict_snackbar': {
        'values': "IMD+ is holding your settings. Revert it first, then apply this profile.",
        'values-ar': "‏يحتفظ IMD+ بإعداداتك مخفية. استعِده أولًا ثم طبّق هذا الملف.",
        'values-b+pt+BR': "O IMD+ está mantendo as suas configurações ocultas. Reverta-o primeiro e depois aplique este perfil.",
        'values-b+zh+Hans': "IMD+ 正在保持你的设置处于隐藏状态。请先还原，再应用此配置。",
        'values-de': "IMD+ hält deine Einstellungen ausgeblendet. Setze es erst zurück und wende dieses Profil dann an.",
        'values-es': "IMD+ mantiene tus ajustes ocultos. Revierte primero y luego aplica este perfil.",
        'values-fr': "IMD+ garde vos paramètres masqués. Restaurez-le d\\'abord, puis appliquez ce profil.",
        'values-hi': "IMD+ ने आपकी सेटिंग्स छिपा रखी हैं। पहले उसे वापस लाएँ, फिर यह प्रोफ़ाइल लागू करें।",
        'values-ja': "IMD+ が設定を非表示のまま保持しています。先に元に戻してから、このプロファイルを適用してください。",
        'values-ko': "IMD+가 설정을 숨긴 채로 유지하고 있습니다. 먼저 되돌린 뒤 이 프로필을 적용하세요.",
        'values-ru': "IMD+ удерживает ваши настройки скрытыми. Сначала верните их, затем примените этот профиль.",
    },
}

TARGETS = [
    ('feature/apps/src/main/res', APPS),
    ('feature/app-settings/src/main/res', APP_SETTINGS),
]

if __name__ == '__main__':
    problems = []

    for base, table in TARGETS:
        for key, translations in table.items():
            missing = [loc for loc in L if loc not in translations]

            if missing:
                problems.append(f'{key}: missing {missing}')

    if problems:
        print('PROBLEMS (nothing written):')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    added = 0

    for base, table in TARGETS:
        for loc in L:
            path = os.path.join(base, loc, 'strings.xml')

            if not os.path.exists(path):
                print(f'missing {path}')
                sys.exit(1)

            src = open(path, encoding='utf-8').read()

            add = [
                f'    <string name="{k}">{t[loc]}</string>'
                for k, t in table.items() if f'name="{k}"' not in src
            ]

            if add:
                src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
                open(path, 'w', encoding='utf-8').write(src)
                added += len(add)

            print(f'{base.split("/")[1]:14s} {loc:18s} +{len(add)}')

    print(f'OK, {added} strings added')
