#!/usr/bin/env python3
"""
v3-r2 — the Hiding framework / Unhiding framework pickers.

Spec items 3 and 4. Every English string is the author's, verbatim, including the trailing
";)" and the "(Recommended)" that moved from the Revert option to the Memory one when the
author reversed the recommendation.

⚠ `unhiding_framework_revert_summary` bolds `revert_defaults` as a substring, so the two must
move together or the emphasis silently matches nothing in some locale. The pair is added to
`tools/check_translations.py` in the same round — see _v3_framework_coupling.py.

Computes the whole edit in memory, asserts locale coverage, that no key already exists, that
the English matches the author character for character, and that every locale's revert summary
really does contain that locale's `revert_defaults`. Writes nothing if anything fails.
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
    "hiding_framework": {
        "values": "Hiding framework",
        "values-ar": "إطار الإخفاء",
        "values-b+pt+BR": "Estrutura de ocultação",
        "values-b+zh+Hans": "隐藏框架",
        "values-de": "Ausblende-Framework",
        "values-es": "Marco de ocultación",
        "values-fr": "Cadre de masquage",
        "values-hi": "छिपाने का फ़्रेमवर्क",
        "values-ja": "非表示フレームワーク",
        "values-ko": "숨기기 프레임워크",
        "values-ru": "Механизм скрытия",
    },
    "unhiding_framework": {
        "values": "Unhiding framework",
        "values-ar": "إطار إظهار الإعدادات",
        "values-b+pt+BR": "Estrutura de reexibição",
        "values-b+zh+Hans": "取消隐藏框架",
        "values-de": "Wiederherstellungs-Framework",
        "values-es": "Marco de restauración",
        "values-fr": "Cadre de réaffichage",
        "values-hi": "दिखाने का फ़्रेमवर्क",
        "values-ja": "再表示フレームワーク",
        "values-ko": "다시 표시 프레임워크",
        "values-ru": "Механизм восстановления",
    },
    "framework_using": {
        "values": "using %1$s",
        "values-ar": "يستخدم ‎%1$s",
        "values-b+pt+BR": "usando %1$s",
        "values-b+zh+Hans": "使用 %1$s",
        "values-de": "verwendet %1$s",
        "values-es": "usando %1$s",
        "values-fr": "utilise %1$s",
        "values-hi": "%1$s का उपयोग",
        "values-ja": "%1$s を使用",
        "values-ko": "%1$s 사용",
        "values-ru": "используется %1$s",
    },
    "hiding_framework_defaults": {
        "values": "IMD defaults",
        "values-ar": "الإعدادات الافتراضية لـ IMD",
        "values-b+pt+BR": "Padrões do IMD",
        "values-b+zh+Hans": "IMD 默认设置",
        "values-de": "IMD-Standards",
        "values-es": "Valores predeterminados de IMD",
        "values-fr": "Valeurs par défaut d’IMD",
        "values-hi": "IMD डिफ़ॉल्ट",
        "values-ja": "IMD の既定",
        "values-ko": "IMD 기본값",
        "values-ru": "Стандартные настройки IMD",
    },
    "hiding_framework_defaults_summary": {
        "values": "Hide same settings for every app",
        "values-ar": "إخفاء الإعدادات نفسها لكل التطبيقات",
        "values-b+pt+BR": "Ocultar as mesmas configurações para todos os apps",
        "values-b+zh+Hans": "为每个应用隐藏相同的设置",
        "values-de": "Für jede App dieselben Einstellungen ausblenden",
        "values-es": "Ocultar los mismos ajustes para todas las apps",
        "values-fr": "Masquer les mêmes paramètres pour toutes les applications",
        "values-hi": "हर ऐप के लिए एक ही सेटिंग छिपाएँ",
        "values-ja": "すべてのアプリで同じ設定を非表示にします",
        "values-ko": "모든 앱에 동일한 설정을 숨깁니다",
        "values-ru": "Скрывать одни и те же настройки для всех приложений",
    },
    "hiding_framework_per_app": {
        "values": "Per app configuration",
        "values-ar": "إعداد لكل تطبيق",
        "values-b+pt+BR": "Configuração por app",
        "values-b+zh+Hans": "按应用配置",
        "values-de": "Konfiguration pro App",
        "values-es": "Configuración por app",
        "values-fr": "Configuration par application",
        "values-hi": "हर ऐप के लिए कॉन्फ़िगरेशन",
        "values-ja": "アプリごとの設定",
        "values-ko": "앱별 구성",
        "values-ru": "Настройка для каждого приложения",
    },
    "hiding_framework_per_app_summary": {
        "values": "Hide different settings for different apps.\\nLong press app icons in IMD to set what settings to hide",
        "values-ar": "إخفاء إعدادات مختلفة لتطبيقات مختلفة.\\nاضغط مطولاً على أيقونات التطبيقات في IMD لتحديد الإعدادات المراد إخفاؤها",
        "values-b+pt+BR": "Ocultar configurações diferentes para apps diferentes.\\nPressione e segure os ícones dos apps no IMD para definir o que ocultar",
        "values-b+zh+Hans": "为不同的应用隐藏不同的设置。\\n在 IMD 中长按应用图标以设置要隐藏的设置",
        "values-de": "Für verschiedene Apps verschiedene Einstellungen ausblenden.\\nApp-Symbole in IMD lange drücken, um festzulegen, was ausgeblendet wird",
        "values-es": "Ocultar ajustes diferentes para apps diferentes.\\nMantén pulsado el icono de una app en IMD para elegir qué ocultar",
        "values-fr": "Masquer des paramètres différents selon l’application.\\nAppuyez longuement sur une icône dans IMD pour choisir ce qui est masqué",
        "values-hi": "अलग-अलग ऐप के लिए अलग-अलग सेटिंग छिपाएँ.\\nक्या छिपाना है यह तय करने के लिए IMD में ऐप आइकन को देर तक दबाएँ",
        "values-ja": "アプリごとに異なる設定を非表示にします。\\nIMD でアプリのアイコンを長押しして、非表示にする設定を指定します",
        "values-ko": "앱마다 다른 설정을 숨깁니다.\\nIMD에서 앱 아이콘을 길게 눌러 숨길 설정을 지정하세요",
        "values-ru": "Скрывать разные настройки для разных приложений.\\nУдерживайте значок приложения в IMD, чтобы выбрать, что скрывать",
    },
    "hiding_framework_per_app_extra": {
        "values": "This option allows you to hide additional settings other than the default 3-5 settings of IMD app ;)",
        "values-ar": "يتيح لك هذا الخيار إخفاء إعدادات إضافية غير الإعدادات الافتراضية من 3 إلى 5 في تطبيق IMD ;)",
        "values-b+pt+BR": "Esta opção permite ocultar configurações além das 3-5 padrão do app IMD ;)",
        "values-b+zh+Hans": "此选项可让你隐藏 IMD 应用默认 3-5 项设置以外的其他设置 ;)",
        "values-de": "Mit dieser Option lassen sich weitere Einstellungen ausblenden als die 3-5 Standardeinstellungen der IMD-App ;)",
        "values-es": "Esta opción permite ocultar ajustes adicionales además de los 3-5 predeterminados de la app IMD ;)",
        "values-fr": "Cette option permet de masquer d’autres paramètres que les 3-5 par défaut de l’application IMD ;)",
        "values-hi": "यह विकल्प आपको IMD ऐप की डिफ़ॉल्ट 3-5 सेटिंग के अलावा और सेटिंग छिपाने देता है ;)",
        "values-ja": "このオプションでは、IMD アプリの既定の 3〜5 個の設定以外も非表示にできます ;)",
        "values-ko": "이 옵션을 사용하면 IMD 앱의 기본 3-5개 설정 외의 설정도 숨길 수 있습니다 ;)",
        "values-ru": "Эта опция позволяет скрывать и другие настройки, помимо 3-5 стандартных настроек IMD ;)",
    },
    "unhiding_framework_memory": {
        "values": "Memory function (Revert to what was actually hidden)",
        "values-ar": "وظيفة الذاكرة (استعادة ما تم إخفاؤه فعليًا)",
        "values-b+pt+BR": "Função de memória (reverter ao que foi realmente ocultado)",
        "values-b+zh+Hans": "记忆功能（还原为实际被隐藏的内容）",
        "values-de": "Speicherfunktion (auf das tatsächlich Ausgeblendete zurücksetzen)",
        "values-es": "Función de memoria (restaurar lo que se ocultó realmente)",
        "values-fr": "Fonction mémoire (rétablir ce qui a réellement été masqué)",
        "values-hi": "मेमोरी फ़ंक्शन (जो वास्तव में छिपाया गया था उसे वापस लाएँ)",
        "values-ja": "メモリー機能（実際に非表示にしたものへ戻す）",
        "values-ko": "메모리 기능 (실제로 숨긴 것으로 되돌리기)",
        "values-ru": "Функция памяти (возврат к тому, что было скрыто)",
    },
    "unhiding_framework_recommended": {
        "values": "(Recommended)",
        "values-ar": "(مُستحسن)",
        "values-b+pt+BR": "(Recomendado)",
        "values-b+zh+Hans": "（推荐）",
        "values-de": "(Empfohlen)",
        "values-es": "(Recomendado)",
        "values-fr": "(Recommandé)",
        "values-hi": "(अनुशंसित)",
        "values-ja": "（推奨）",
        "values-ko": "(권장)",
        "values-ru": "(Рекомендуется)",
    },
    "unhiding_framework_memory_summary": {
        "values": "Memorises and restores to the actual settings state before hiding them",
        "values-ar": "يحفظ حالة الإعدادات الفعلية قبل إخفائها ثم يستعيدها",
        "values-b+pt+BR": "Memoriza e restaura o estado real das configurações antes de ocultá-las",
        "values-b+zh+Hans": "记录并还原隐藏前设置的实际状态",
        "values-de": "Merkt sich den tatsächlichen Zustand vor dem Ausblenden und stellt ihn wieder her",
        "values-es": "Memoriza y restaura el estado real de los ajustes antes de ocultarlos",
        "values-fr": "Mémorise l’état réel des paramètres avant de les masquer et le rétablit",
        "values-hi": "छिपाने से पहले सेटिंग की वास्तविक स्थिति याद रखता है और वापस लाता है",
        "values-ja": "非表示にする前の実際の設定状態を記憶して復元します",
        "values-ko": "숨기기 전의 실제 설정 상태를 기억했다가 복원합니다",
        "values-ru": "Запоминает фактическое состояние настроек до скрытия и восстанавливает его",
    },
    "unhiding_framework_revert": {
        "values": "Revert to default",
        "values-ar": "استعادة الإعدادات الافتراضية",
        "values-b+pt+BR": "Reverter para o padrão",
        "values-b+zh+Hans": "还原为默认值",
        "values-de": "Auf Standard zurücksetzen",
        "values-es": "Restaurar valores predeterminados",
        "values-fr": "Rétablir les valeurs par défaut",
        "values-hi": "डिफ़ॉल्ट पर वापस लाएँ",
        "values-ja": "既定に戻す",
        "values-ko": "기본값으로 되돌리기",
        "values-ru": "Вернуть настройки по умолчанию",
    },
    "framework_pending_reverts": {
        "values": "Pending reverts found, IMD will perform pending reverts then save the new settings",
        "values-ar": "تم العثور على عمليات استعادة معلّقة، سينفّذها IMD ثم يحفظ الإعدادات الجديدة",
        "values-b+pt+BR": "Reversões pendentes encontradas; o IMD fará as reversões pendentes e depois salvará as novas configurações",
        "values-b+zh+Hans": "发现待处理的还原操作，IMD 将先执行这些还原，然后保存新设置",
        "values-de": "Ausstehende Wiederherstellungen gefunden. IMD führt sie aus und speichert dann die neuen Einstellungen",
        "values-es": "Hay reversiones pendientes; IMD las realizará y luego guardará los nuevos ajustes",
        "values-fr": "Rétablissements en attente détectés : IMD va les effectuer puis enregistrer les nouveaux paramètres",
        "values-hi": "बाकी रिवर्ट मिले, IMD पहले उन्हें पूरा करेगा फिर नई सेटिंग सहेजेगा",
        "values-ja": "保留中の復元があります。IMD はそれらを実行してから新しい設定を保存します",
        "values-ko": "대기 중인 되돌리기가 있습니다. IMD가 먼저 실행한 뒤 새 설정을 저장합니다",
        "values-ru": "Найдены незавершённые возвраты. IMD выполнит их, затем сохранит новые настройки",
    },
    "framework_pending_reverts_failed": {
        "values": "Unable to perform pending reverts, please check notifications to proceed",
        "values-ar": "تعذّر تنفيذ عمليات الاستعادة المعلّقة، يرجى مراجعة الإشعارات للمتابعة",
        "values-b+pt+BR": "Não foi possível fazer as reversões pendentes; verifique as notificações para continuar",
        "values-b+zh+Hans": "无法执行待处理的还原操作，请查看通知以继续",
        "values-de": "Ausstehende Wiederherstellungen konnten nicht ausgeführt werden. Bitte die Benachrichtigungen prüfen",
        "values-es": "No se pudieron realizar las reversiones pendientes; revisa las notificaciones para continuar",
        "values-fr": "Impossible d’effectuer les rétablissements en attente : consultez les notifications pour continuer",
        "values-hi": "बाकी रिवर्ट पूरे नहीं हो सके, आगे बढ़ने के लिए सूचनाएँ देखें",
        "values-ja": "保留中の復元を実行できませんでした。続行するには通知を確認してください",
        "values-ko": "대기 중인 되돌리기를 수행하지 못했습니다. 계속하려면 알림을 확인하세요",
        "values-ru": "Не удалось выполнить незавершённые возвраты. Проверьте уведомления, чтобы продолжить",
    },
}

AUTHOR_ENGLISH = {
    "hiding_framework": "Hiding framework",
    "unhiding_framework": "Unhiding framework",
    "hiding_framework_defaults": "IMD defaults",
    "hiding_framework_defaults_summary": "Hide same settings for every app",
    "hiding_framework_per_app": "Per app configuration",
    "hiding_framework_per_app_extra": (
        "This option allows you to hide additional settings other than the default 3-5 "
        "settings of IMD app ;)"
    ),
    "unhiding_framework_memory": "Memory function (Revert to what was actually hidden)",
    "unhiding_framework_recommended": "(Recommended)",
    "unhiding_framework_memory_summary": (
        "Memorises and restores to the actual settings state before hiding them"
    ),
    "unhiding_framework_revert": "Revert to default",
    "framework_pending_reverts": (
        "Pending reverts found, IMD will perform pending reverts then save the new settings"
    ),
    "framework_pending_reverts_failed": (
        "Unable to perform pending reverts, please check notifications to proceed"
    ),
}

ANCHOR = '    <!-- suIMD: revert to default configuration -->'


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


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

        with_arg = {loc for loc, text in texts.items() if "%1$s" in text}

        if with_arg and len(with_arg) != len(LOCALES):
            problems.append(f"{key}: %1$s in {len(with_arg)} of {len(LOCALES)} locales")

        # A literal newline in an unquoted Android string collapses to a space. Only the
        # escaped form survives, and this is the one key that wants a line break.
        for locale, text in texts.items():
            if "\n" in text:
                problems.append(f"{key}/{locale}: literal newline, must be \\\\n")

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

        if ANCHOR not in text:
            problems.append(f"{locale}: anchor not found")
            continue

        block = (
            "    <!-- suIMD v3: the Hiding framework / Unhiding framework split. The two\n"
            "         questions the old hiding-unhiding mechanism answered with one switch. -->\n"
            + "".join(
                f'    <string name="{key}">{escape(ADD[key][locale])}</string>\n'
                for key in ADD
            )
            + "\n"
        )

        staged[path] = text.replace(ANCHOR, block + ANCHOR, 1)

    for path, text in staged.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            problems.append(f"{path.parent.name}: does not parse — {error}")

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
