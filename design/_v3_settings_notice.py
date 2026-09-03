#!/usr/bin/env python3
"""
v3-r1 — "App settings updated, please checkout the new Settings tab".

Proto field 61 (settingsNoticeRevision) threaded through the four Kotlin layers, following how
setupNoticeVersion is wired, plus the strings.

Shown once to an install that existed before this version, never to a fresh one.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "feature/settings/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

# The author's sentence, verbatim. The bolded half is a key of its own so each locale bolds
# its own words - a phrase that is not verbatim in the sentence highlights nothing.
AUTHOR = "App settings updated, please checkout the new Settings tab"
AUTHOR_NAME = "new Settings tab"

NOTICE = {
    "values": AUTHOR,
    "values-ar": "تم تحديث إعدادات التطبيق، يرجى الاطلاع على علامة تبويب الإعدادات الجديدة",
    "values-b+pt+BR": "As configurações do app foram atualizadas, confira a nova aba Configurações",
    "values-b+zh+Hans": "应用设置已更新，请查看新的设置标签页",
    "values-de": "Die App-Einstellungen wurden aktualisiert, sehen Sie sich den neuen Einstellungen-Tab an",
    "values-es": "Los ajustes de la aplicación se han actualizado, echa un vistazo a la nueva pestaña Ajustes",
    "values-fr": "Les paramètres de l\\'appli ont été mis à jour, découvrez le nouvel onglet Paramètres",
    "values-hi": "ऐप सेटिंग्स अपडेट हो गई हैं, कृपया नया सेटिंग्स टैब देखें",
    "values-ja": "アプリの設定が更新されました。新しい設定タブをご確認ください",
    "values-ko": "앱 설정이 업데이트되었습니다. 새로운 설정 탭을 확인해 주세요",
    "values-ru": "Настройки приложения обновлены, посмотрите новую вкладку «Настройки»",
}

NAME = {
    "values": AUTHOR_NAME,
    "values-ar": "علامة تبويب الإعدادات الجديدة",
    "values-b+pt+BR": "nova aba Configurações",
    "values-b+zh+Hans": "新的设置标签页",
    "values-de": "neuen Einstellungen-Tab",
    "values-es": "nueva pestaña Ajustes",
    "values-fr": "nouvel onglet Paramètres",
    "values-hi": "नया सेटिंग्स टैब",
    "values-ja": "新しい設定タブ",
    "values-ko": "새로운 설정 탭",
    "values-ru": "новую вкладку «Настройки»",
}

KOTLIN = [
    (
        "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt",
        "    val setupNoticeVersion: Int,",
        "    val setupNoticeVersion: Int,\n"
        "\n"
        "    /**\n"
        "     * Which revision of the \"what changed\" notice this install has already seen.\n"
        "     *\n"
        "     * Zero on a fresh install, which is also \"never shown\" — so it is always read\n"
        "     * together with [setupNoticeVersion], the app's only record that an install\n"
        "     * existed before today.\n"
        "     */\n"
        "    val settingsNoticeRevision: Int,",
    ),
    (
        "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt",
        "            setupNoticeVersion = it.setupNoticeVersion,",
        "            setupNoticeVersion = it.setupNoticeVersion,\n"
        "            settingsNoticeRevision = it.settingsNoticeRevision,",
    ),
    (
        "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt",
        "            it.copy { this.setupNoticeVersion = versionCode }",
        "            it.copy { this.setupNoticeVersion = versionCode }",
    ),
]

WRITER_ANCHOR = (
    "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt",
    "    suspend fun markAutoHideEverEnabled() {",
    "    /** Records the newest \"what changed\" notice this install has been shown. */\n"
    "    suspend fun updateSettingsNoticeRevision(revision: Int) {\n"
    "        userPreferences.updateData {\n"
    "            it.copy { this.settingsNoticeRevision = revision }\n"
    "        }\n"
    "    }\n"
    "\n"
    "    suspend fun markAutoHideEverEnabled() {",
)

REPO = [
    (
        "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt",
        "    /** Records that IMD+ has been switched on by the user at least once. */",
        "    /** Records the newest \"what changed\" notice this install has been shown. */\n"
        "    suspend fun updateSettingsNoticeRevision(revision: Int)\n"
        "\n"
        "    /** Records that IMD+ has been switched on by the user at least once. */",
    ),
    (
        "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt",
        "    override suspend fun markAutoHideEverEnabled() {",
        "    override suspend fun updateSettingsNoticeRevision(revision: Int) {\n"
        "        userPreferencesDataSource.updateSettingsNoticeRevision(revision = revision)\n"
        "    }\n"
        "\n"
        "    override suspend fun markAutoHideEverEnabled() {",
    ),
]


def fail(message):
    print(f"REFUSED, nothing written: {message}")
    return 1


def main():
    if NOTICE["values"] != AUTHOR:
        return fail("the English notice is not the author's text")

    for locale in LOCALES:
        if NAME[locale] not in NOTICE[locale]:
            return fail(
                f"{locale}: the bolded phrase {NAME[locale]!r} is not verbatim inside the "
                f"sentence — the highlight would match nothing",
            )

    planned = {}

    # --- Kotlin -----------------------------------------------------------------------
    for rel, old, new in KOTLIN[:2] + [WRITER_ANCHOR] + REPO:
        path = ROOT / rel
        text = planned.get(path, path.read_text(encoding="utf-8"))
        found = text.count(old)
        if found != 1:
            return fail(f"{rel}: anchor matched {found} time(s): {old.strip()[:56]!r}")
        planned[path] = text.replace(old, new, 1)

    # --- strings ----------------------------------------------------------------------
    for locale in LOCALES:
        path = RES / locale / "strings.xml"
        text = planned.get(path, path.read_text(encoding="utf-8"))

        for key in ("settings_tab_notice", "settings_tab_notice_name"):
            if f'name="{key}"' in text:
                return fail(f"{locale}: {key} already exists — has this run before?")

        for value in (NOTICE[locale], NAME[locale]):
            if "'" in value and "\\'" not in value:
                return fail(f"{locale}: unescaped apostrophe in {value[:32]!r}")
            if "&" in value and "&amp;" not in value:
                return fail(f"{locale}: unescaped ampersand")
            if "\n" in value:
                return fail(f"{locale}: literal newline")

        block = (
            f'    <string name="settings_tab_notice">{NOTICE[locale]}</string>\n'
            f'    <string name="settings_tab_notice_name">{NAME[locale]}</string>\n'
        )

        marker = "</resources>"
        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        planned[path] = text.replace(marker, block + marker, 1)

    for path, text in planned.items():
        if path.suffix == ".xml":
            try:
                ET.fromstring(text)
            except ET.ParseError as error:
                return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(planned)} file(s)")
    print(f"  notice: {AUTHOR!r}")
    print(f"  bold  : {AUTHOR_NAME!r}  (asserted verbatim in all 11 sentences)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
