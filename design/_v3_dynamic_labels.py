#!/usr/bin/env python3
"""
v3-r2 — the dynamic row labels, the two dialog descriptions, and the red ⓘ notice.

The author made both rows in Default IMD settings read differently depending on the
frameworks, and the reasoning holds up: under the memory function the hide list *is* the
unhide list, because memory restores exactly what was hidden; under Revert to default a
separate list drives the unhide, so the hide list is hide-only.

| unhiding framework | "Settings to hide" row | "Settings to unhide on Revert" row |
| --- | --- | --- |
| Revert to default | Default settings to hide | Settings to unhide on Revert /⏎Revert to default configuration |
| Memory function   | Settings to hide / unhide | Revert to default configuration |

The red ⓘ beside the first row is a *hiding* question and appears whenever the hiding
framework is Per app configuration, independently of the labels above.

Descriptions use the author's bracket style — "hidden(disabled)", "unhidden(re-enabled)" — and
the memory pair carries his clause before the full stop.

⚠ `unhiding_framework_revert_summary` bolds `revert_defaults` as a substring. Every locale is
checked here, and the pair is registered in `tools/check_translations.py` so a later wording
change cannot break it silently.
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "feature/settings/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

ADD: dict[str, dict[str, str]] = {
    # ⚠ **A template, not ten translations.** The bolded phrase must be this locale's own
    # `revert_defaults`, character for character, or emphasised() matches nothing and the
    # sentence silently loses its bold. Filled from the file below rather than typed here —
    # the first version of this script typed them and was refused in all ten locales.
    "unhiding_framework_revert_summary": {
        "values": "always reverts to {name} under default IMD settings",
        "values-ar": "يعيد دائمًا إلى {name} ضمن إعدادات IMD الافتراضية",
        "values-b+pt+BR": "sempre reverte para {name} nas configurações padrão do IMD",
        "values-b+zh+Hans": "始终还原为 IMD 默认设置中的{name}",
        "values-de": "setzt immer auf {name} in den IMD-Standardeinstellungen zurück",
        "values-es": "siempre restaura a {name} en los ajustes predeterminados de IMD",
        "values-fr": "rétablit toujours {name} dans les paramètres par défaut d’IMD",
        "values-hi": "हमेशा डिफ़ॉल्ट IMD सेटिंग में {name} पर लौटाता है",
        "values-ja": "常に IMD の既定設定にある{name}へ戻します",
        "values-ko": "항상 IMD 기본 설정의 {name}(으)로 되돌립니다",
        "values-ru": "всегда возвращает к {name} в стандартных настройках IMD",
    },
    "settings_to_hide_defaults_label": {
        "values": "Default settings to hide",
        "values-ar": "الإعدادات الافتراضية المراد إخفاؤها",
        "values-b+pt+BR": "Configurações padrão a ocultar",
        "values-b+zh+Hans": "要隐藏的默认设置",
        "values-de": "Standardmäßig auszublendende Einstellungen",
        "values-es": "Ajustes predeterminados a ocultar",
        "values-fr": "Paramètres par défaut à masquer",
        "values-hi": "छिपाने के लिए डिफ़ॉल्ट सेटिंग",
        "values-ja": "非表示にする既定の設定",
        "values-ko": "숨길 기본 설정",
        "values-ru": "Стандартные настройки для скрытия",
    },
    "settings_to_hide_both_label": {
        "values": "Settings to hide / unhide",
        "values-ar": "الإعدادات المراد إخفاؤها / إظهارها",
        "values-b+pt+BR": "Configurações a ocultar / reexibir",
        "values-b+zh+Hans": "要隐藏 / 取消隐藏的设置",
        "values-de": "Einstellungen zum Ausblenden / Einblenden",
        "values-es": "Ajustes a ocultar / mostrar",
        "values-fr": "Paramètres à masquer / réafficher",
        "values-hi": "छिपाने / दिखाने के लिए सेटिंग",
        "values-ja": "非表示 / 再表示する設定",
        "values-ko": "숨기기 / 다시 표시할 설정",
        "values-ru": "Настройки для скрытия / восстановления",
    },
    "revert_defaults_entry_both": {
        "values": "Settings to unhide on Revert /\\nRevert to default configuration",
        "values-ar": "الإعدادات المراد إظهارها عند الاستعادة /\\nاستعادة الإعدادات الافتراضية",
        "values-b+pt+BR": "Configurações a reexibir ao reverter /\\nReverter para a configuração padrão",
        "values-b+zh+Hans": "还原时要取消隐藏的设置 /\\n还原为默认配置",
        "values-de": "Beim Zurücksetzen einzublendende Einstellungen /\\nAuf Standardkonfiguration zurücksetzen",
        "values-es": "Ajustes a mostrar al restaurar /\\nRestaurar configuración predeterminada",
        "values-fr": "Paramètres à réafficher lors du rétablissement /\\nRétablir la configuration par défaut",
        "values-hi": "रिवर्ट पर दिखाने के लिए सेटिंग /\\nडिफ़ॉल्ट कॉन्फ़िगरेशन पर वापस लाएँ",
        "values-ja": "復元時に再表示する設定 /\\n既定の構成に戻す",
        "values-ko": "되돌릴 때 다시 표시할 설정 /\\n기본 구성으로 되돌리기",
        "values-ru": "Настройки для восстановления при возврате /\\nВернуть конфигурацию по умолчанию",
    },
    # --- the four Settings-to-hide dialog descriptions -------------------------------------
    "settings_to_hide_desc_defaults_revert": {
        "values": "These are the default settings which are hidden(disabled) for app launches, the Hide settings QS tile and IMD intents.",
        "values-ar": "هذه هي الإعدادات الافتراضية التي يتم إخفاؤها(تعطيلها) عند تشغيل التطبيقات ومن مربّع إخفاء الإعدادات ومن أوامر IMD.",
        "values-b+pt+BR": "Estas são as configurações padrão que são ocultadas(desativadas) ao abrir apps, pelo bloco Ocultar configurações e pelas intents do IMD.",
        "values-b+zh+Hans": "这些是启动应用、使用隐藏设置磁贴和 IMD 意图时被隐藏（停用）的默认设置。",
        "values-de": "Dies sind die Standardeinstellungen, die beim App-Start, über die Kachel „Einstellungen ausblenden“ und über IMD-Intents ausgeblendet(deaktiviert) werden.",
        "values-es": "Estos son los ajustes predeterminados que se ocultan(desactivan) al abrir apps, con el mosaico Ocultar ajustes y con las intents de IMD.",
        "values-fr": "Voici les paramètres par défaut masqués(désactivés) au lancement d’une application, par la tuile Masquer les paramètres et par les intents IMD.",
        "values-hi": "ये वे डिफ़ॉल्ट सेटिंग हैं जो ऐप लॉन्च, Hide settings QS टाइल और IMD इंटेंट के लिए छिपाई(अक्षम) जाती हैं.",
        "values-ja": "アプリの起動、設定を非表示タイル、IMD インテントで非表示(無効)になる既定の設定です。",
        "values-ko": "앱 실행, 설정 숨기기 QS 타일, IMD 인텐트에서 숨겨(비활성화)지는 기본 설정입니다.",
        "values-ru": "Это стандартные настройки, которые скрываются(отключаются) при запуске приложений, плиткой «Скрыть настройки» и интентами IMD.",
    },
    "settings_to_hide_desc_defaults_memory": {
        "values": "These are the default settings which are hidden(disabled) and unhidden(re-enabled) for app launches, the Hide settings QS tile and IMD intents, only if IMD disabled them before.",
        "values-ar": "هذه هي الإعدادات الافتراضية التي يتم إخفاؤها(تعطيلها) وإظهارها(إعادة تمكينها) عند تشغيل التطبيقات ومن مربّع إخفاء الإعدادات ومن أوامر IMD، فقط إذا كان IMD قد عطّلها من قبل.",
        "values-b+pt+BR": "Estas são as configurações padrão que são ocultadas(desativadas) e reexibidas(reativadas) ao abrir apps, pelo bloco Ocultar configurações e pelas intents do IMD, somente se o IMD as tiver desativado antes.",
        "values-b+zh+Hans": "这些是启动应用、使用隐藏设置磁贴和 IMD 意图时被隐藏（停用）并取消隐藏（重新启用）的默认设置，仅限 IMD 之前停用过的项。",
        "values-de": "Dies sind die Standardeinstellungen, die beim App-Start, über die Kachel „Einstellungen ausblenden“ und über IMD-Intents ausgeblendet(deaktiviert) und wieder eingeblendet(aktiviert) werden – nur wenn IMD sie zuvor deaktiviert hat.",
        "values-es": "Estos son los ajustes predeterminados que se ocultan(desactivan) y se muestran(reactivan) al abrir apps, con el mosaico Ocultar ajustes y con las intents de IMD, solo si IMD los desactivó antes.",
        "values-fr": "Voici les paramètres par défaut masqués(désactivés) puis réaffichés(réactivés) au lancement d’une application, par la tuile Masquer les paramètres et par les intents IMD, uniquement si IMD les avait désactivés.",
        "values-hi": "ये वे डिफ़ॉल्ट सेटिंग हैं जो ऐप लॉन्च, Hide settings QS टाइल और IMD इंटेंट के लिए छिपाई(अक्षम) और दिखाई(फिर से सक्षम) जाती हैं, केवल तभी जब IMD ने उन्हें पहले अक्षम किया हो.",
        "values-ja": "アプリの起動、設定を非表示タイル、IMD インテントで非表示(無効)になり、再表示(再有効化)される既定の設定です。IMD が以前に無効にした場合のみ。",
        "values-ko": "앱 실행, 설정 숨기기 QS 타일, IMD 인텐트에서 숨겨(비활성화)지고 다시 표시(재활성화)되는 기본 설정입니다. IMD가 이전에 비활성화한 경우에만 해당합니다.",
        "values-ru": "Это стандартные настройки, которые скрываются(отключаются) и восстанавливаются(включаются снова) при запуске приложений, плиткой «Скрыть настройки» и интентами IMD — только если их отключал IMD.",
    },
    "settings_to_hide_desc_per_app_revert": {
        "values": "These are the default settings which are hidden(disabled) only for the Hide settings QS tile and IMD intents.",
        "values-ar": "هذه هي الإعدادات الافتراضية التي يتم إخفاؤها(تعطيلها) فقط لمربّع إخفاء الإعدادات وأوامر IMD.",
        "values-b+pt+BR": "Estas são as configurações padrão ocultadas(desativadas) apenas pelo bloco Ocultar configurações e pelas intents do IMD.",
        "values-b+zh+Hans": "这些是仅在使用隐藏设置磁贴和 IMD 意图时被隐藏（停用）的默认设置。",
        "values-de": "Dies sind die Standardeinstellungen, die nur über die Kachel „Einstellungen ausblenden“ und über IMD-Intents ausgeblendet(deaktiviert) werden.",
        "values-es": "Estos son los ajustes predeterminados que se ocultan(desactivan) solo con el mosaico Ocultar ajustes y con las intents de IMD.",
        "values-fr": "Voici les paramètres par défaut masqués(désactivés) uniquement par la tuile Masquer les paramètres et par les intents IMD.",
        "values-hi": "ये वे डिफ़ॉल्ट सेटिंग हैं जो केवल Hide settings QS टाइल और IMD इंटेंट के लिए छिपाई(अक्षम) जाती हैं.",
        "values-ja": "設定を非表示タイルと IMD インテントでのみ非表示(無効)になる既定の設定です。",
        "values-ko": "설정 숨기기 QS 타일과 IMD 인텐트에서만 숨겨(비활성화)지는 기본 설정입니다.",
        "values-ru": "Это стандартные настройки, которые скрываются(отключаются) только плиткой «Скрыть настройки» и интентами IMD.",
    },
    "settings_to_hide_desc_per_app_memory": {
        "values": "These are the default settings which are hidden(disabled) and unhidden(re-enabled) only for the Hide settings QS tile and IMD intents, only if IMD disabled them before.",
        "values-ar": "هذه هي الإعدادات الافتراضية التي يتم إخفاؤها(تعطيلها) وإظهارها(إعادة تمكينها) فقط لمربّع إخفاء الإعدادات وأوامر IMD، وفقط إذا كان IMD قد عطّلها من قبل.",
        "values-b+pt+BR": "Estas são as configurações padrão ocultadas(desativadas) e reexibidas(reativadas) apenas pelo bloco Ocultar configurações e pelas intents do IMD, somente se o IMD as tiver desativado antes.",
        "values-b+zh+Hans": "这些是仅在使用隐藏设置磁贴和 IMD 意图时被隐藏（停用）并取消隐藏（重新启用）的默认设置，仅限 IMD 之前停用过的项。",
        "values-de": "Dies sind die Standardeinstellungen, die nur über die Kachel „Einstellungen ausblenden“ und über IMD-Intents ausgeblendet(deaktiviert) und wieder eingeblendet(aktiviert) werden – nur wenn IMD sie zuvor deaktiviert hat.",
        "values-es": "Estos son los ajustes predeterminados que se ocultan(desactivan) y se muestran(reactivan) solo con el mosaico Ocultar ajustes y con las intents de IMD, solo si IMD los desactivó antes.",
        "values-fr": "Voici les paramètres par défaut masqués(désactivés) puis réaffichés(réactivés) uniquement par la tuile Masquer les paramètres et par les intents IMD, et seulement si IMD les avait désactivés.",
        "values-hi": "ये वे डिफ़ॉल्ट सेटिंग हैं जो केवल Hide settings QS टाइल और IMD इंटेंट के लिए छिपाई(अक्षम) और दिखाई(फिर से सक्षम) जाती हैं, और केवल तभी जब IMD ने उन्हें पहले अक्षम किया हो.",
        "values-ja": "設定を非表示タイルと IMD インテントでのみ非表示(無効)になり、再表示(再有効化)される既定の設定です。IMD が以前に無効にした場合のみ。",
        "values-ko": "설정 숨기기 QS 타일과 IMD 인텐트에서만 숨겨(비활성화)지고 다시 표시(재활성화)되는 기본 설정입니다. IMD가 이전에 비활성화한 경우에만 해당합니다.",
        "values-ru": "Это стандартные настройки, которые скрываются(отключаются) и восстанавливаются(включаются снова) только плиткой «Скрыть настройки» и интентами IMD — и только если их отключал IMD.",
    },
    # --- the two Revert-to-default dialog descriptions -------------------------------------
    "revert_defaults_desc_revert": {
        "values": "These settings are unhidden(re-enabled) on every unhide, and whenever you use \\'Revert to default\\' anywhere.",
        "values-ar": "يتم إظهار(إعادة تمكين) هذه الإعدادات عند كل عملية إظهار، وكلما استخدمت \\'استعادة الإعدادات الافتراضية\\' في أي مكان.",
        "values-b+pt+BR": "Estas configurações são reexibidas(reativadas) em toda reexibição e sempre que você usar \\'Reverter para o padrão\\' em qualquer lugar.",
        "values-b+zh+Hans": "每次取消隐藏时，以及在任何位置使用\\'还原为默认值\\'时，这些设置都会被取消隐藏（重新启用）。",
        "values-de": "Diese Einstellungen werden bei jedem Einblenden wieder eingeblendet(aktiviert) und immer dann, wenn Sie irgendwo \\'Auf Standard zurücksetzen\\' verwenden.",
        "values-es": "Estos ajustes se muestran(reactivan) en cada restauración y siempre que uses \\'Restaurar valores predeterminados\\' en cualquier sitio.",
        "values-fr": "Ces paramètres sont réaffichés(réactivés) à chaque rétablissement et chaque fois que vous utilisez \\'Rétablir les valeurs par défaut\\' où que ce soit.",
        "values-hi": "ये सेटिंग हर बार दिखाने पर दिखाई(फिर से सक्षम) जाती हैं, और जब भी आप कहीं भी \\'डिफ़ॉल्ट पर वापस लाएँ\\' का उपयोग करते हैं.",
        "values-ja": "これらの設定は再表示のたびに、またどこかで\\'既定に戻す\\'を使うたびに再表示(再有効化)されます。",
        "values-ko": "이 설정은 다시 표시할 때마다, 그리고 어디서든 \\'기본값으로 되돌리기\\'를 사용할 때마다 다시 표시(재활성화)됩니다.",
        "values-ru": "Эти настройки восстанавливаются(включаются снова) при каждом восстановлении и всякий раз, когда вы используете \\'Вернуть настройки по умолчанию\\'.",
    },
    "revert_defaults_desc_memory": {
        "values": "These settings are unhidden(re-enabled) only when you use \\'Revert to default\\' anywhere.",
        "values-ar": "يتم إظهار(إعادة تمكين) هذه الإعدادات فقط عند استخدام \\'استعادة الإعدادات الافتراضية\\' في أي مكان.",
        "values-b+pt+BR": "Estas configurações são reexibidas(reativadas) apenas quando você usa \\'Reverter para o padrão\\' em qualquer lugar.",
        "values-b+zh+Hans": "仅当你在任何位置使用\\'还原为默认值\\'时，这些设置才会被取消隐藏（重新启用）。",
        "values-de": "Diese Einstellungen werden nur wieder eingeblendet(aktiviert), wenn Sie irgendwo \\'Auf Standard zurücksetzen\\' verwenden.",
        "values-es": "Estos ajustes solo se muestran(reactivan) cuando usas \\'Restaurar valores predeterminados\\' en cualquier sitio.",
        "values-fr": "Ces paramètres ne sont réaffichés(réactivés) que lorsque vous utilisez \\'Rétablir les valeurs par défaut\\' où que ce soit.",
        "values-hi": "ये सेटिंग केवल तभी दिखाई(फिर से सक्षम) जाती हैं जब आप कहीं भी \\'डिफ़ॉल्ट पर वापस लाएँ\\' का उपयोग करते हैं.",
        "values-ja": "これらの設定は、どこかで\\'既定に戻す\\'を使ったときにのみ再表示(再有効化)されます。",
        "values-ko": "이 설정은 어디서든 \\'기본값으로 되돌리기\\'를 사용할 때만 다시 표시(재활성화)됩니다.",
        "values-ru": "Эти настройки восстанавливаются(включаются снова) только при использовании \\'Вернуть настройки по умолчанию\\'.",
    },
    # --- the red ⓘ notice beside the hide row, under Per app configuration ----------------
    "per_app_hide_notice": {
        "values": "Using per app configuration hiding mechanism (see advanced settings in IMD)\\nOnly using these for:\\n  1. Hide settings quick setting toggle\\n  2. IMD intents (Tasker, Macrodroid... etc)",
        "values-ar": "يتم استخدام آلية الإخفاء بإعداد لكل تطبيق (راجع الإعدادات المتقدمة في IMD)\\nتُستخدم هذه فقط لـ:\\n  1. مفتاح الإعدادات السريعة لإخفاء الإعدادات\\n  2. أوامر IMD (Tasker وMacrodroid... إلخ)",
        "values-b+pt+BR": "Usando o mecanismo de ocultação por configuração por app (veja as configurações avançadas no IMD)\\nUsadas apenas para:\\n  1. Bloco de configurações rápidas Ocultar configurações\\n  2. Intents do IMD (Tasker, Macrodroid... etc)",
        "values-b+zh+Hans": "正在使用按应用配置的隐藏机制（见 IMD 高级设置）\\n这些仅用于：\\n  1. 隐藏设置快捷开关\\n  2. IMD 意图（Tasker、Macrodroid… 等）",
        "values-de": "Es wird der Ausblende-Mechanismus „Konfiguration pro App“ verwendet (siehe erweiterte Einstellungen in IMD)\\nDiese werden nur verwendet für:\\n  1. Schnelleinstellung „Einstellungen ausblenden“\\n  2. IMD-Intents (Tasker, Macrodroid... usw.)",
        "values-es": "Usando el mecanismo de ocultación por configuración por app (consulta los ajustes avanzados en IMD)\\nSolo se usan para:\\n  1. Interruptor de ajustes rápidos Ocultar ajustes\\n  2. Intents de IMD (Tasker, Macrodroid... etc.)",
        "values-fr": "Mécanisme de masquage par configuration par application (voir les paramètres avancés dans IMD)\\nUtilisés uniquement pour :\\n  1. Le réglage rapide Masquer les paramètres\\n  2. Les intents IMD (Tasker, Macrodroid... etc.)",
        "values-hi": "हर ऐप के लिए कॉन्फ़िगरेशन वाली छिपाने की व्यवस्था चल रही है (IMD में उन्नत सेटिंग देखें)\\nइनका उपयोग केवल इनके लिए:\\n  1. Hide settings क्विक सेटिंग टॉगल\\n  2. IMD इंटेंट (Tasker, Macrodroid... आदि)",
        "values-ja": "アプリごとの設定による非表示方式を使用しています（IMD の詳細設定を参照）\\nこれらは次の場合にのみ使用されます:\\n  1. 設定を非表示クイック設定トグル\\n  2. IMD インテント（Tasker、Macrodroid… など）",
        "values-ko": "앱별 구성 숨기기 방식을 사용 중입니다 (IMD의 고급 설정 참조)\\n다음에만 사용됩니다:\\n  1. 설정 숨기기 빠른 설정 토글\\n  2. IMD 인텐트 (Tasker, Macrodroid... 등)",
        "values-ru": "Используется механизм скрытия с настройкой для каждого приложения (см. расширенные настройки в IMD)\\nОни используются только для:\\n  1. Переключателя быстрых настроек «Скрыть настройки»\\n  2. Интентов IMD (Tasker, Macrodroid... и т. д.)",
    },
    "per_app_hide_notice_red": {
        "values": "These are not being used for apps when launched via IMD.",
        "values-ar": "لا تُستخدم هذه عند تشغيل التطبيقات عبر IMD.",
        "values-b+pt+BR": "Estas não são usadas para apps abertos pelo IMD.",
        "values-b+zh+Hans": "通过 IMD 启动应用时不会使用这些设置。",
        "values-de": "Für über IMD gestartete Apps werden diese nicht verwendet.",
        "values-es": "No se usan para las apps abiertas desde IMD.",
        "values-fr": "Ils ne sont pas utilisés pour les applications lancées via IMD.",
        "values-hi": "IMD के ज़रिए ऐप लॉन्च करने पर इनका उपयोग नहीं होता.",
        "values-ja": "IMD 経由で起動したアプリには使用されません。",
        "values-ko": "IMD를 통해 실행한 앱에는 사용되지 않습니다.",
        "values-ru": "Они не используются для приложений, запущенных через IMD.",
    },
}

AUTHOR_ENGLISH = {
    "settings_to_hide_defaults_label": "Default settings to hide",
    "settings_to_hide_both_label": "Settings to hide / unhide",
    "per_app_hide_notice_red": "These are not being used for apps when launched via IMD.",
}

ANCHOR = '    <string name="settings_to_hide">Settings to hide</string>'


def escape(text: str) -> str:
    # Apostrophes in these strings are already written escaped, so only the two that cannot
    # be pre-escaped in a Python literal are handled here.
    return text.replace("&", "&amp;").replace("<", "&lt;")


def main() -> int:
    problems: list[str] = []

    for key, texts in ADD.items():
        missing = [locale for locale in LOCALES if locale not in texts]

        if missing:
            problems.append(f"{key}: missing {missing}")

        expected = AUTHOR_ENGLISH.get(key)

        if expected is not None and texts.get("values") != expected:
            problems.append(
                f"{key}: English is {texts.get('values')!r}, author wrote {expected!r}",
            )

        for locale, text in texts.items():
            if "\n" in text:
                problems.append(f"{key}/{locale}: literal newline, must be \\\\n")

            # An unescaped apostrophe is the single commonest way an Android string build
            # breaks, and these descriptions are full of them.
            for match in re.finditer(r"'", text):
                if match.start() == 0 or text[match.start() - 1] != "\\":
                    problems.append(f"{key}/{locale}: unescaped apostrophe")

                    break

    # Fill the revert-summary template from each locale's own revert_defaults.
    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            continue

        match = re.search(
            r'<string name="revert_defaults">(.*?)</string>',
            path.read_text(encoding="utf-8"),
            re.S,
        )

        if match is None:
            problems.append(f"{locale}: revert_defaults missing")

            continue

        ADD["unhiding_framework_revert_summary"][locale] = (
            ADD["unhiding_framework_revert_summary"][locale].format(name=match.group(1))
        )

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")
            continue

        text = path.read_text(encoding="utf-8")

        for key in ADD:
            if re.search(rf'name="{key}"', text):
                problems.append(f"{locale}: {key} already exists")

        anchor = ANCHOR if locale == "values" else None

        if anchor is None:
            match = re.search(r'^    <string name="settings_to_hide">.*$', text, re.M)

            if match is None:
                problems.append(f"{locale}: settings_to_hide anchor not found")

                continue

            anchor = match.group(0)

        if anchor not in text:
            problems.append(f"{locale}: anchor not found")

            continue

        block = "".join(
            f'    <string name="{key}">{escape(ADD[key][locale])}</string>\n'
            for key in ADD
        )

        staged[path] = text.replace(anchor, block + anchor, 1)

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}: does not parse — {error}")

    # The bolded phrase has to occur verbatim in its own locale's sentence or it silently
    # matches nothing. Checked here as well as in check_translations, because this is the
    # round that introduces the pair.
    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if path not in staged:
            continue

        match = re.search(
            r'<string name="revert_defaults">(.*?)</string>',
            staged[path],
            re.S,
        )

        if match is None:
            problems.append(f"{locale}: revert_defaults missing")

            continue

        name = match.group(1)

        if name not in ADD["unhiding_framework_revert_summary"][locale]:
            problems.append(
                f"{locale}: '{name}' does not occur in unhiding_framework_revert_summary, "
                f"so it will not be bolded",
            )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {len(ADD)} keys across {len(staged)} locales")

    return 0


if __name__ == "__main__":
    sys.exit(main())
