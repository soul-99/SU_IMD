#!/usr/bin/env python3
"""
v3-r2 — the auto-unhide QS row, and the help screen's first two sections.

Two unrelated jobs in one script because both are plain string rewrites in the same module and
neither is worth its own file.

**The QS row.** Renamed to the author's `'Hide settings QS toggle'`, with his sentence
underneath. The note it replaces said the same thing in the app's voice — "the tile names no
app, so only the screen lock timer can end it" — and the author's is shorter and names the
trigger the way the trigger names itself.

**The help screen.** It documents the new-install default only, at the author's instruction: no
dynamic help. Section 1 becomes the hide/unhide list, section 2 becomes Revert to default and
gains the body it has never had, and both location trees are updated to the rows' new names.

⚠ The location trees are **not** the dynamic labels. The help describes one configuration — the
new-install default, which is IMD defaults + Memory — so it names the labels that pairing
shows, fixed.

Computes the whole edit in memory, asserts every match count and locale, and writes nothing if
anything fails.
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

REPLACE: dict[str, dict[str, str]] = {
    "auto_unhide_used_for_tile": {
        "values": "Hide settings QS toggle",
        "values-ar": "مفتاح الإعدادات السريعة لإخفاء الإعدادات",
        "values-b+pt+BR": "Bloco rápido Ocultar configurações",
        "values-b+zh+Hans": "隐藏设置快捷开关",
        "values-de": "Schnelleinstellung „Einstellungen ausblenden“",
        "values-es": "Interruptor rápido Ocultar ajustes",
        "values-fr": "Réglage rapide Masquer les paramètres",
        "values-hi": "Hide settings QS टॉगल",
        "values-ja": "設定を非表示クイック設定トグル",
        "values-ko": "설정 숨기기 QS 토글",
        "values-ru": "Переключатель «Скрыть настройки»",
    },
    "auto_unhide_used_for_tile_note": {
        "values": "Only works with Screen lock timer trigger",
        "values-ar": "يعمل فقط مع مؤقّت قفل الشاشة",
        "values-b+pt+BR": "Funciona apenas com o gatilho de tempo de bloqueio de tela",
        "values-b+zh+Hans": "仅在使用屏幕锁定计时触发器时有效",
        "values-de": "Funktioniert nur mit dem Bildschirmsperre-Timer",
        "values-es": "Solo funciona con el disparador de temporizador de bloqueo de pantalla",
        "values-fr": "Fonctionne uniquement avec le déclencheur de minuterie de verrouillage",
        "values-hi": "केवल स्क्रीन लॉक टाइमर ट्रिगर के साथ काम करता है",
        "values-ja": "画面ロックタイマーのトリガーでのみ機能します",
        "values-ko": "화면 잠금 타이머 트리거에서만 작동합니다",
        "values-ru": "Работает только с триггером таймера блокировки экрана",
    },
    "help_hide_title": {
        "values": "Setup what settings to hide / unhide (MANDATORY)",
        "values-ar": "إعداد ما يتم إخفاؤه / إظهاره من الإعدادات (إلزامي)",
        "values-b+pt+BR": "Configure o que ocultar / reexibir (OBRIGATÓRIO)",
        "values-b+zh+Hans": "设置要隐藏 / 取消隐藏的设置（必需）",
        "values-de": "Festlegen, was aus- / eingeblendet wird (ERFORDERLICH)",
        "values-es": "Configura qué ajustes ocultar / mostrar (OBLIGATORIO)",
        "values-fr": "Configurez ce qui est masqué / réaffiché (OBLIGATOIRE)",
        "values-hi": "क्या छिपाना / दिखाना है यह सेट करें (अनिवार्य)",
        "values-ja": "非表示 / 再表示する設定を指定（必須）",
        "values-ko": "숨기거나 다시 표시할 설정 지정 (필수)",
        "values-ru": "Выберите, что скрывать / показывать (ОБЯЗАТЕЛЬНО)",
    },
    "help_revert_title": {
        "values": "Setup Revert to default (RECOMMENDED)",
        "values-ar": "إعداد استعادة الإعدادات الافتراضية (مُستحسن)",
        "values-b+pt+BR": "Configure Reverter para o padrão (RECOMENDADO)",
        "values-b+zh+Hans": "设置还原为默认值（推荐）",
        "values-de": "„Auf Standard zurücksetzen“ einrichten (EMPFOHLEN)",
        "values-es": "Configura Restaurar valores predeterminados (RECOMENDADO)",
        "values-fr": "Configurez Rétablir les valeurs par défaut (RECOMMANDÉ)",
        "values-hi": "डिफ़ॉल्ट पर वापस लाएँ सेट करें (अनुशंसित)",
        "values-ja": "既定に戻すを設定（推奨）",
        "values-ko": "기본값으로 되돌리기 설정 (권장)",
        "values-ru": "Настройте «Вернуть настройки по умолчанию» (РЕКОМЕНДУЕТСЯ)",
    },
    "help_path_hide": {
        "values": "IMD Settings → Default IMD settings → Settings to hide / unhide",
        "values-ar": "إعدادات IMD ← إعدادات IMD الافتراضية ← الإعدادات المراد إخفاؤها / إظهارها",
        "values-b+pt+BR": "Configurações do IMD → Configurações padrão do IMD → Configurações a ocultar / reexibir",
        "values-b+zh+Hans": "IMD 设置 → IMD 默认设置 → 要隐藏 / 取消隐藏的设置",
        "values-de": "IMD-Einstellungen → IMD-Standardeinstellungen → Einstellungen zum Ausblenden / Einblenden",
        "values-es": "Ajustes de IMD → Ajustes predeterminados de IMD → Ajustes a ocultar / mostrar",
        "values-fr": "Paramètres IMD → Paramètres par défaut d’IMD → Paramètres à masquer / réafficher",
        "values-hi": "IMD सेटिंग → डिफ़ॉल्ट IMD सेटिंग → छिपाने / दिखाने के लिए सेटिंग",
        "values-ja": "IMD 設定 → IMD の既定設定 → 非表示 / 再表示する設定",
        "values-ko": "IMD 설정 → IMD 기본 설정 → 숨기기 / 다시 표시할 설정",
        "values-ru": "Настройки IMD → Стандартные настройки IMD → Настройки для скрытия / восстановления",
    },
    "help_path_unhide": {
        "values": "IMD Settings → Default IMD settings → Revert to default configuration",
        "values-ar": "إعدادات IMD ← إعدادات IMD الافتراضية ← استعادة الإعدادات الافتراضية",
        "values-b+pt+BR": "Configurações do IMD → Configurações padrão do IMD → Reverter para a configuração padrão",
        "values-b+zh+Hans": "IMD 设置 → IMD 默认设置 → 还原为默认配置",
        "values-de": "IMD-Einstellungen → IMD-Standardeinstellungen → Auf Standardkonfiguration zurücksetzen",
        "values-es": "Ajustes de IMD → Ajustes predeterminados de IMD → Restaurar configuración predeterminada",
        "values-fr": "Paramètres IMD → Paramètres par défaut d’IMD → Rétablir la configuration par défaut",
        "values-hi": "IMD सेटिंग → डिफ़ॉल्ट IMD सेटिंग → डिफ़ॉल्ट कॉन्फ़िगरेशन पर वापस लाएँ",
        "values-ja": "IMD 設定 → IMD の既定設定 → 既定の構成に戻す",
        "values-ko": "IMD 설정 → IMD 기본 설정 → 기본 구성으로 되돌리기",
        "values-ru": "Настройки IMD → Стандартные настройки IMD → Вернуть конфигурацию по умолчанию",
    },
}

ADD: dict[str, dict[str, str]] = {
    "help_revert_body": {
        "values": "It allows user to set a default setting state to be restored in non satisfactory cases.",
        "values-ar": "يتيح للمستخدم تحديد حالة افتراضية للإعدادات تتم استعادتها في الحالات غير المُرضية.",
        "values-b+pt+BR": "Permite ao usuário definir um estado padrão a ser restaurado em casos insatisfatórios.",
        "values-b+zh+Hans": "它允许用户设定一个默认设置状态，在情况不理想时还原为该状态。",
        "values-de": "Damit legt man einen Standardzustand fest, der in unbefriedigenden Fällen wiederhergestellt wird.",
        "values-es": "Permite al usuario definir un estado predeterminado que se restaura en casos no satisfactorios.",
        "values-fr": "Permet à l’utilisateur de définir un état par défaut à rétablir dans les cas insatisfaisants.",
        "values-hi": "यह उपयोगकर्ता को एक डिफ़ॉल्ट सेटिंग स्थिति तय करने देता है जो असंतोषजनक स्थितियों में वापस लाई जाती है.",
        "values-ja": "満足のいかない場合に復元される既定の設定状態をユーザーが指定できます。",
        "values-ko": "만족스럽지 않은 경우 복원할 기본 설정 상태를 사용자가 정할 수 있습니다.",
        "values-ru": "Позволяет задать состояние настроек по умолчанию, которое восстанавливается в неудовлетворительных случаях.",
    },
}

# The author's own words, asserted against what goes in.
AUTHOR_ENGLISH = {
    "auto_unhide_used_for_tile": "Hide settings QS toggle",
    "auto_unhide_used_for_tile_note": "Only works with Screen lock timer trigger",
    "help_revert_body": (
        "It allows user to set a default setting state to be restored in non satisfactory "
        "cases."
    ),
}


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("'", "\\'").replace("<", "&lt;")


def main() -> int:
    problems: list[str] = []

    for source in (REPLACE, ADD):
        for key, texts in source.items():
            missing = [locale for locale in LOCALES if locale not in texts]

            if missing:
                problems.append(f"{key}: missing {missing}")

            expected = AUTHOR_ENGLISH.get(key)

            if expected is not None and texts.get("values") != expected:
                problems.append(
                    f"{key}: English is {texts.get('values')!r}, author wrote {expected!r}",
                )

    # The author corrected the double space himself; make it impossible to reintroduce.
    if "  " in ADD["help_revert_body"]["values"]:
        problems.append("help_revert_body: double space is back")

    staged: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.exists():
            problems.append(f"{locale}: no strings.xml")

            continue

        text = path.read_text(encoding="utf-8")

        for key, texts in REPLACE.items():
            pattern = re.compile(rf'(<string name="{key}">)(.*?)(</string>)', re.S)

            if len(pattern.findall(text)) != 1:
                problems.append(f"{locale}: {len(pattern.findall(text))} of {key}")

                continue

            text = pattern.sub(
                lambda m, value=escape(texts[locale]): m.group(1) + value + m.group(3),
                text,
                count=1,
            )

        for key, texts in ADD.items():
            if re.search(rf'name="{key}"', text):
                problems.append(f"{locale}: {key} already exists")

                continue

            match = re.search(r'^    <string name="help_revert_title">.*$', text, re.M)

            if match is None:
                problems.append(f"{locale}: help_revert_title anchor not found")

                continue

            line = f'    <string name="{key}">{escape(texts[locale])}</string>\n'

            text = text.replace(match.group(0), match.group(0) + "\n" + line.rstrip("\n"), 1)

        staged[path] = text

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

    print(f"ok — {len(REPLACE)} reworded, {len(ADD)} added, across {len(staged)} locales")

    return 0


if __name__ == "__main__":
    sys.exit(main())
