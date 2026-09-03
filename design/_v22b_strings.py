#!/usr/bin/env python3
"""One-off: the v2.2b string batch, across all 11 locales.

NEW adds a string; REPLACE swaps an existing one's whole value. Every operation asserts its
match count, so a rename upstream fails here rather than silently doing nothing.
"""
import os
import re
import sys

L = ['values', 'values-ar', 'values-b+pt+BR', 'values-b+zh+Hans', 'values-de', 'values-es',
     'values-fr', 'values-hi', 'values-ja', 'values-ko', 'values-ru']

APPS = 'feature/apps/src/main/res'
SETTINGS = 'feature/settings/src/main/res'
APP = 'app/src/main/res'

NEW = {
    APPS: {
        'overlay_none_managed': {
            'values': "No Display over other apps are configured to be hidden.\\nPlease add those from IMD app settings.",
            'values-ar': "لم يتم إعداد أي تطبيقات لإخفاء «العرض فوق التطبيقات الأخرى» منها.\\nالرجاء إضافتها من إعدادات تطبيق IMD.",
            'values-b+pt+BR': "Nenhum app está configurado para ter “Sobreposição a outros apps” ocultada.\\nAdicione-os nas configurações do IMD.",
            'values-b+zh+Hans': "尚未配置要隐藏“显示在其他应用上层”的应用。\\n请在 IMD 应用设置中添加。",
            'values-de': "Es sind keine Apps für das Ausblenden von „Über anderen Apps einblenden“ eingerichtet.\\nBitte füge sie in den IMD-App-Einstellungen hinzu.",
            'values-es': "No hay apps configuradas para ocultarles “Mostrar sobre otras apps”.\\nAñádelas desde los ajustes de la app IMD.",
            'values-fr': "Aucune application n\\'est configurée pour masquer « Superposition à d\\'autres applis ».\\nAjoutez-les depuis les paramètres de l\\'application IMD.",
            'values-hi': "‘अन्य ऐप्स के ऊपर दिखाएँ’ छिपाने के लिए कोई ऐप कॉन्फ़िगर नहीं है।\\nकृपया उन्हें IMD ऐप सेटिंग्स से जोड़ें।",
            'values-ja': "「他のアプリの上に重ねて表示」を非表示にするアプリが設定されていません。\\nIMD アプリの設定から追加してください。",
            'values-ko': "‘다른 앱 위에 표시’를 숨길 앱이 설정되어 있지 않습니다.\\nIMD 앱 설정에서 추가해 주세요.",
            'values-ru': "Не выбрано ни одного приложения, для которого нужно скрывать «Поверх других приложений».\\nДобавьте их в настройках приложения IMD.",
        },
    },
    SETTINGS: {
        'help_launch_tile_name': {
            'values': "Hide settings quick toggle",
            'values-ar': "مفتاح إخفاء الإعدادات السريع",
            'values-b+pt+BR': "Bloco rápido Ocultar configurações",
            'values-b+zh+Hans': "“隐藏设置”快捷开关",
            'values-de': "Schnelleinstellung „Einstellungen ausblenden“",
            'values-es': "Ajuste rápido Ocultar ajustes",
            'values-fr': "Tuile Masquer les paramètres",
            'values-hi': "‘सेटिंग्स छिपाएँ’ क्विक टॉगल",
            'values-ja': "「設定を非表示」クイック設定タイル",
            'values-ko': "‘설정 숨기기’ 빠른 설정 타일",
            'values-ru': "Быстрая кнопка «Скрыть настройки»",
        },
    },
}

REPLACE = {
    APP: {
        # The tile's own name, as it appears in the Quick Settings tile picker. The two
        # per-state labels (Settings visible / Settings hidden) are separate and unchanged.
        'hide_tile_label': {
            'values': "Hide settings",
            'values-ar': "إخفاء الإعدادات",
            'values-b+pt+BR': "Ocultar configurações",
            'values-b+zh+Hans': "隐藏设置",
            'values-de': "Einstellungen ausblenden",
            'values-es': "Ocultar ajustes",
            'values-fr': "Masquer les paramètres",
            'values-hi': "सेटिंग्स छिपाएँ",
            'values-ja': "設定を非表示",
            'values-ko': "설정 숨기기",
            'values-ru': "Скрыть настройки",
        },
    },
    APPS: {
        'no_favourite_apps_subtitle': {
            'values': "Add apps by pressing star icon in All apps tab",
            'values-ar': "أضف التطبيقات بالضغط على أيقونة النجمة في تبويب «كل التطبيقات»",
            'values-b+pt+BR': "Adicione apps tocando no ícone de estrela na aba Todos os apps",
            'values-b+zh+Hans': "在“全部应用”标签页点击星形图标即可添加应用",
            'values-de': "Apps hinzufügen: Tippe im Tab „Alle Apps“ auf das Sternsymbol",
            'values-es': "Añade apps pulsando el icono de estrella en la pestaña Todas las apps",
            'values-fr': "Ajoutez des applis en appuyant sur l\\'étoile dans l\\'onglet Toutes les applis",
            'values-hi': "‘सभी ऐप्स’ टैब में स्टार आइकॉन दबाकर ऐप्स जोड़ें",
            'values-ja': "「すべてのアプリ」タブで星アイコンをタップして追加します",
            'values-ko': "‘모든 앱’ 탭에서 별 아이콘을 눌러 앱을 추가하세요",
            'values-ru': "Добавляйте приложения, нажимая на звёздочку на вкладке «Все приложения»",
        },
    },
    SETTINGS: {
        'revert_defaults_shizuku_note': {
            'values': "Depending on which method Shizuku uses to keep service alive, it will modify enable/disable USB or wireless debugging.",
            'values-ar': "حسب الطريقة التي يستخدمها Shizuku لإبقاء الخدمة نشطة، سيقوم بتمكين أو تعطيل تصحيح أخطاء USB أو التصحيح اللاسلكي.",
            'values-b+pt+BR': "Dependendo do método que o Shizuku usa para manter o serviço ativo, ele vai ativar ou desativar a depuração USB ou sem fio.",
            'values-b+zh+Hans': "根据 Shizuku 保持服务运行所用的方式，它会启用或停用 USB 调试或无线调试。",
            'values-de': "Je nachdem, wie Shizuku den Dienst am Leben hält, aktiviert oder deaktiviert es USB- oder WLAN-Debugging.",
            'values-es': "Según el método que use Shizuku para mantener el servicio activo, activará o desactivará la depuración por USB o inalámbrica.",
            'values-fr': "Selon la méthode utilisée par Shizuku pour maintenir le service actif, il activera ou désactivera le débogage USB ou sans fil.",
            'values-hi': "Shizuku सेवा को चालू रखने के लिए जिस तरीक़े का इस्तेमाल करता है, उसके अनुसार वह USB या वायरलेस डीबगिंग को चालू/बंद करेगा।",
            'values-ja': "Shizuku がサービスを維持するために使う方式に応じて、USB デバッグまたはワイヤレスデバッグを有効・無効にします。",
            'values-ko': "Shizuku가 서비스를 유지하는 방식에 따라 USB 디버깅 또는 무선 디버깅을 켜거나 끕니다.",
            'values-ru': "В зависимости от того, каким способом Shizuku поддерживает работу службы, он включит или отключит отладку по USB или по Wi-Fi.",
        },
        'about_version': {
            'values': "App version %1$s",
            'values-ar': "إصدار التطبيق %1$s",
            'values-b+pt+BR': "Versão do app %1$s",
            'values-b+zh+Hans': "应用版本 %1$s",
            'values-de': "App-Version %1$s",
            'values-es': "Versión de la app %1$s",
            'values-fr': "Version de l\\'application %1$s",
            'values-hi': "ऐप वर्शन %1$s",
            'values-ja': "アプリのバージョン %1$s",
            'values-ko': "앱 버전 %1$s",
            'values-ru': "Версия приложения %1$s",
        },
        'help_general_launch': {
            'values': "1. To use the blocked apps you need to launch them from one of these:\\n•  The IMD app\\n•  IMD created app shortcuts on homescreen\\n•  Normally from your launcher, if settings are hidden using Hide settings quick toggle",
            'values-ar': "١. لاستخدام التطبيقات المحجوبة عليك تشغيلها بإحدى هذه الطرق:\\n•  من تطبيق IMD\\n•  من اختصارات التطبيقات التي ينشئها IMD على الشاشة الرئيسية\\n•  من مشغّل التطبيقات كالمعتاد، إذا كانت الإعدادات مخفية عبر مفتاح إخفاء الإعدادات السريع",
            'values-b+pt+BR': "1. Para usar os apps bloqueados, abra-os de uma destas formas:\\n•  Pelo app IMD\\n•  Pelos atalhos criados pelo IMD na tela inicial\\n•  Normalmente pelo seu launcher, se as configurações estiverem ocultas pelo Bloco rápido Ocultar configurações",
            'values-b+zh+Hans': "1. 要使用被限制的应用，请通过以下任一方式启动：\\n•  IMD 应用\\n•  IMD 在主屏幕创建的应用快捷方式\\n•  在设置已通过“隐藏设置”快捷开关隐藏时，照常从桌面启动",
            'values-de': "1. Um die blockierten Apps zu nutzen, starte sie auf einem dieser Wege:\\n•  Über die IMD-App\\n•  Über die von IMD erstellten Verknüpfungen auf dem Startbildschirm\\n•  Ganz normal über deinen Launcher, wenn die Einstellungen über die Schnelleinstellung „Einstellungen ausblenden“ ausgeblendet sind",
            'values-es': "1. Para usar las apps bloqueadas debes abrirlas de una de estas formas:\\n•  Desde la app IMD\\n•  Desde los accesos directos que IMD crea en la pantalla de inicio\\n•  Con normalidad desde tu launcher, si los ajustes están ocultos mediante el Ajuste rápido Ocultar ajustes",
            'values-fr': "1. Pour utiliser les applis bloquées, lancez-les de l\\'une de ces façons :\\n•  Depuis l\\'application IMD\\n•  Depuis les raccourcis créés par IMD sur l\\'écran d\\'accueil\\n•  Normalement depuis votre lanceur, si les paramètres sont masqués via la Tuile Masquer les paramètres",
            'values-hi': "1. ब्लॉक किए गए ऐप्स इस्तेमाल करने के लिए उन्हें इनमें से किसी एक तरीक़े से खोलें:\\n•  IMD ऐप से\\n•  होमस्क्रीन पर IMD द्वारा बनाए गए ऐप शॉर्टकट से\\n•  अपने लॉन्चर से सामान्य रूप से, अगर सेटिंग्स ‘सेटिंग्स छिपाएँ’ क्विक टॉगल से छिपाई गई हों",
            'values-ja': "1. ブロックされたアプリを使うには、次のいずれかの方法で起動します:\\n•  IMD アプリから\\n•  IMD がホーム画面に作成したショートカットから\\n•  「設定を非表示」クイック設定タイルで設定を非表示にしている場合は、ランチャーから通常どおり",
            'values-ko': "1. 차단된 앱을 사용하려면 다음 중 한 가지 방법으로 실행하세요:\\n•  IMD 앱에서\\n•  IMD가 홈 화면에 만든 앱 바로가기에서\\n•  ‘설정 숨기기’ 빠른 설정 타일로 설정을 숨긴 경우에는 런처에서 평소대로",
            'values-ru': "1. Чтобы пользоваться заблокированными приложениями, запускайте их одним из этих способов:\\n•  Из приложения IMD\\n•  С ярлыков, созданных IMD на главном экране\\n•  Обычным способом из лаунчера, если настройки скрыты быстрой кнопкой «Скрыть настройки»",
        },
    },
}

if __name__ == '__main__':
    problems = []

    for base, entries in NEW.items():
        for loc in L:
            path = os.path.join(base, loc, 'strings.xml')
            src = open(path, encoding='utf-8').read()
            add = []
            for key, per_loc in entries.items():
                if f'name="{key}"' in src:
                    continue
                add.append(f'    <string name="{key}">{per_loc[loc]}</string>')
            if add:
                if '</resources>' not in src:
                    problems.append(f'{path}: no </resources>')
                    continue
                src = src.replace('</resources>', '\n'.join(add) + '\n</resources>', 1)
                open(path, 'w', encoding='utf-8').write(src)
            print(f'NEW     {base.split("/")[1]:9s} {loc:18s} +{len(add)}')

    for base, entries in REPLACE.items():
        for loc in L:
            path = os.path.join(base, loc, 'strings.xml')
            src = open(path, encoding='utf-8').read()
            done = 0
            for key, per_loc in entries.items():
                pattern = re.compile(r'<string name="%s">.*?</string>' % re.escape(key), re.S)
                hits = pattern.findall(src)
                if len(hits) != 1:
                    problems.append(f'{path}: {key} matched {len(hits)}x')
                    continue
                src = pattern.sub(
                    lambda _m, v=per_loc[loc], k=key: f'<string name="{k}">{v}</string>',
                    src,
                    count=1,
                )
                done += 1
            open(path, 'w', encoding='utf-8').write(src)
            print(f'REPLACE {base.split("/")[1]:9s} {loc:18s} {done}/{len(entries)}')

    if problems:
        print('PROBLEMS:')
        for p in problems:
            print('  -', p)
        sys.exit(1)

    print('OK')
