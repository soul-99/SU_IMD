#!/usr/bin/env python3
"""
r11 strings: IMD+ stops being a Revert-to-default-only feature.

1. DROP the third line of `auto_hide_intro` — "Uses only Revert to default mechanism not Memory
   function." It is no longer true: IMD+ now applies the app's own saved settings when the memory
   function is the chosen notification function.

2. DROP the third bullet of `memory_hide_notice` — "Auto hide settings (IMD+)". That popup lists
   what still reads the device-wide "Settings to hide" list while the memory function is on, and
   IMD+ has just left that list.

   Both are removals of the last `\\n`-separated segment, asserted by shape rather than by
   matching eleven translations of a sentence: split, check the count, check the last piece is
   the one meant, drop it.

3. ADD `auto_hide_no_profile` — what the IMD+ window says when a watched app has no settings
   saved and the memory function is on. The author's English, verbatim, including the apostrophe
   in "app's" and the line break they asked for.

4. ADD `auto_hide_hidden_revert_memory` — the IMD+ notification's text in that mode. The existing
   `auto_hide_hidden_revert` stays for the Revert-to-default mode; this one says where the revert
   comes from, because the two undo different things.

Asserts before it writes, as the others do.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

SETTINGS_RES = os.path.join(ROOT, "feature", "settings", "src", "main", "res")

NOTIFICATION_RES = os.path.join(
    ROOT, "framework", "notification-manager", "src", "main", "res",
)

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# --- 1 and 2: the two last-segment drops --------------------------------
# key -> (segments before, segments after, what the dropped piece must contain)
DROPS = {
    "auto_hide_intro": (3, 2, "3."),
    "memory_hide_notice": (4, 3, "IMD+"),
}

# --- 3: the popup -------------------------------------------------------
NO_PROFILE = "auto_hide_no_profile"

NO_PROFILE_TEXT = {
    "values":
        "IMD+ autohide: No settings configured to be hidden for this app.\\n"
        "Please configure the settings to hide by long pressing the app icon in IMD app\\'s "
        "All apps/Favourites Tab.",
    "values-ar":
        "‏IMD+ للإخفاء التلقائي: لا توجد إعدادات مهيّأة للإخفاء لهذا التطبيق.\\n"
        "يرجى تهيئة الإعدادات المراد إخفاؤها بالضغط المطوّل على أيقونة التطبيق في تبويب "
        "«كل التطبيقات» أو «المفضّلة» داخل تطبيق IMD.",
    "values-b+pt+BR":
        "IMD+ ocultação automática: nenhuma configuração definida para ser ocultada neste app.\\n"
        "Defina o que ocultar mantendo pressionado o ícone do app na aba "
        "Todos os apps/Favoritos do IMD.",
    "values-b+zh+Hans":
        "IMD+ 自动隐藏：尚未为此应用配置要隐藏的设置。\\n"
        "请在 IMD 的“所有应用”/“收藏”标签页中长按该应用图标来配置要隐藏的设置。",
    "values-de":
        "IMD+ Auto-Ausblenden: Für diese App sind keine auszublendenden Einstellungen "
        "konfiguriert.\\n"
        "Konfiguriere sie, indem du das App-Symbol im Tab „Alle Apps“/„Favoriten“ der IMD-App "
        "lange drückst.",
    "values-es":
        "IMD+ ocultación automática: no hay ajustes configurados para ocultar en esta app.\\n"
        "Configúralos manteniendo pulsado el icono de la app en la pestaña "
        "Todas las apps/Favoritos de IMD.",
    "values-fr":
        "IMD+ masquage automatique : aucun paramètre configuré à masquer pour cette "
        "application.\\n"
        "Configurez-les en appuyant longuement sur l\\'icône de l\\'application dans l\\'onglet "
        "Toutes les applications/Favoris de l\\'app IMD.",
    "values-hi":
        "IMD+ ऑटो हाइड: इस ऐप के लिए छिपाने हेतु कोई सेटिंग कॉन्फ़िगर नहीं है।\\n"
        "IMD ऐप के ‘सभी ऐप’/‘पसंदीदा’ टैब में ऐप आइकॉन को देर तक दबाकर छिपाने वाली सेटिंग्स "
        "कॉन्फ़िगर करें।",
    "values-ja":
        "IMD+ 自動非表示: このアプリには非表示にする設定が構成されていません。\\n"
        "IMD アプリの「すべてのアプリ」/「お気に入り」タブでアプリのアイコンを長押しして"
        "設定してください。",
    "values-ko":
        "IMD+ 자동 숨기기: 이 앱에 숨길 설정이 구성되어 있지 않습니다.\\n"
        "IMD 앱의 ‘모든 앱’/‘즐겨찾기’ 탭에서 앱 아이콘을 길게 눌러 숨길 설정을 구성하세요.",
    "values-ru":
        "IMD+ автоскрытие: для этого приложения не настроены скрываемые настройки.\\n"
        "Настройте их, удерживая значок приложения на вкладке "
        "«Все приложения»/«Избранное» в IMD.",
}

# --- 4: the notification ------------------------------------------------
REVERT_MEMORY = "auto_hide_hidden_revert_memory"

REVERT_MEMORY_TEXT = {
    "values": "IMD+ hid your settings, click to revert from memory.",
    "values-ar": "‏أخفى IMD+ إعداداتك، انقر للاستعادة من الذاكرة.",
    "values-b+pt+BR": "O IMD+ ocultou suas configurações, toque para reverter pela memória.",
    "values-b+zh+Hans": "IMD+ 已隐藏你的设置，点按即可从记忆功能还原。",
    "values-de": "IMD+ hat deine Einstellungen ausgeblendet, zum Zurücksetzen aus dem Speicher tippen.",
    "values-es": "IMD+ ha ocultado tus ajustes, toca para revertir desde la memoria.",
    "values-fr": "IMD+ a masqué vos paramètres, appuyez pour restaurer depuis la mémoire.",
    "values-hi": "IMD+ ने आपकी सेटिंग्स छिपा दी हैं, मेमोरी से वापस लाने के लिए टैप करें।",
    "values-ja": "IMD+ が設定を非表示にしました。メモリーから元に戻すにはタップします。",
    "values-ko": "IMD+가 설정을 숨겼습니다. 메모리에서 되돌리려면 누르세요.",
    "values-ru": "IMD+ скрыл ваши настройки, нажмите, чтобы вернуть из памяти.",
}


def body(text, name):
    m = re.search(r'<string name="%s"(?: [^>]*)?>(.*?)</string>' % re.escape(name), text, re.S)

    return m.group(1) if m else None


def unsafe(value):
    """Everything aapt2 or the parser would refuse, or that renders wrong."""
    problems = []

    if re.search(r"(?<!\\)'", value):
        problems.append("unescaped apostrophe")

    if '"' in value:
        problems.append("straight double quote")

    if "\n" in value:
        problems.append("literal newline")

    if re.search(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", value):
        problems.append("bare ampersand")

    return problems


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}
    dropped = {}

    for locale in LOCALES:
        settings = os.path.join(SETTINGS_RES, locale, "strings.xml")

        notifications = os.path.join(NOTIFICATION_RES, locale, "strings.xml")

        for path in (settings, notifications):
            if not os.path.exists(path):
                errors.append("%s: missing %s" % (locale, path))

        if errors:
            continue

        text = open(settings, encoding="utf-8").read()

        # --- 1 and 2 ---------------------------------------------------
        for key, spec in DROPS.items():
            want_before, want_after, marker = spec

            current = body(text, key)

            if current is None:
                errors.append("%s: %s absent" % (locale, key))

                continue

            parts = current.split("\\n")

            if len(parts) != want_before:
                errors.append(
                    "%s: %s has %d segments, expected %d"
                    % (locale, key, len(parts), want_before)
                )

                continue

            if marker not in parts[-1]:
                errors.append(
                    "%s: %s last segment %r does not contain %r"
                    % (locale, key, parts[-1], marker)
                )

                continue

            dropped.setdefault(locale, {})[key] = parts[-1]

            replacement = "\\n".join(parts[:want_after])

            old = '<string name="%s">%s</string>' % (key, current)
            new = '<string name="%s">%s</string>' % (key, replacement)

            if text.count(old) != 1:
                errors.append("%s: %s matched %d times" % (locale, key, text.count(old)))

                continue

            text = text.replace(old, new, 1)

        # --- 3 ----------------------------------------------------------
        if body(text, NO_PROFILE) is not None:
            errors.append("%s: %s already present" % (locale, NO_PROFILE))
        else:
            value = NO_PROFILE_TEXT[locale]

            bad = unsafe(value)

            if bad:
                errors.append("%s: %s %s" % (locale, NO_PROFILE, ", ".join(bad)))
            elif text.count("</resources>") != 1:
                errors.append("%s: expected one </resources> in settings" % locale)
            else:
                text = text.replace(
                    "</resources>",
                    '    <string name="%s">%s</string>\n</resources>' % (NO_PROFILE, value),
                    1,
                )

        pending[settings] = text

        # --- 4 ----------------------------------------------------------
        notification_text = open(notifications, encoding="utf-8").read()

        if body(notification_text, REVERT_MEMORY) is not None:
            errors.append("%s: %s already present" % (locale, REVERT_MEMORY))
        else:
            value = REVERT_MEMORY_TEXT[locale]

            bad = unsafe(value)

            if bad:
                errors.append("%s: %s %s" % (locale, REVERT_MEMORY, ", ".join(bad)))
            elif notification_text.count("</resources>") != 1:
                errors.append("%s: expected one </resources> in notification-manager" % locale)
            else:
                notification_text = notification_text.replace(
                    "</resources>",
                    '    <string name="%s">%s</string>\n</resources>' % (REVERT_MEMORY, value),
                    1,
                )

        pending[notifications] = notification_text

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- validation ---------------------------------------------------
    problems = []

    for locale in LOCALES:
        settings = pending[os.path.join(SETTINGS_RES, locale, "strings.xml")]

        notifications = pending[os.path.join(NOTIFICATION_RES, locale, "strings.xml")]

        for key, spec in DROPS.items():
            _, want_after, marker = spec

            left = body(settings, key)

            if left is None:
                problems.append("%s: %s vanished entirely" % (locale, key))

                continue

            if len(left.split("\\n")) != want_after:
                problems.append("%s: %s did not lose exactly one segment" % (locale, key))

        # The IMD+ line is the one being removed from the memory notice, so no bracketed
        # mention of it may survive there.
        if "(IMD+)" in body(settings, "memory_hide_notice"):
            problems.append("%s: memory_hide_notice still names IMD+" % locale)

        # And the intro must no longer claim IMD+ cannot do memory.
        if body(settings, "auto_hide_intro").count("\\n") != 1:
            problems.append("%s: auto_hide_intro is not two lines" % locale)

        if body(settings, NO_PROFILE) != NO_PROFILE_TEXT[locale]:
            problems.append("%s: %s did not take" % (locale, NO_PROFILE))

        # Two sentences, one break, as the author wrote it.
        if body(settings, NO_PROFILE).count("\\n") != 1:
            problems.append("%s: %s is not two lines" % (locale, NO_PROFILE))

        if body(notifications, REVERT_MEMORY) != REVERT_MEMORY_TEXT[locale]:
            problems.append("%s: %s did not take" % (locale, REVERT_MEMORY))

        # The Revert-to-default wording is untouched and both must exist side by side.
        if body(notifications, "auto_hide_hidden_revert") is None:
            problems.append("%s: auto_hide_hidden_revert was lost" % locale)

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    print("\ndropped one line from auto_hide_intro and one bullet from memory_hide_notice,")
    print("in %d locales each" % len(LOCALES))
    print("added %s (settings) and %s (notification-manager), %d locales each"
          % (NO_PROFILE, REVERT_MEMORY, len(LOCALES)))

    print("\nwhat came out, English:")
    print("   auto_hide_intro     %s" % dropped["values"]["auto_hide_intro"])
    print("   memory_hide_notice  %s" % dropped["values"]["memory_hide_notice"])

    print("\nwhat went in, English:")

    for line in NO_PROFILE_TEXT["values"].split("\\n"):
        print("   %s" % line.replace("\\'", "'"))

    print("   %s" % REVERT_MEMORY_TEXT["values"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
