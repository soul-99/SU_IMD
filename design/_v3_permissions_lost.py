#!/usr/bin/env python3
"""
v3-r1i — "the WRITE_SECURE_SETTINGS grant has gone" said in one sentence, everywhere.

One key, 11 locales, in `common` — which is the only module carrying resources that `app`,
`broadcast-receiver`, `feature/apps` and `feature/settings` can all see. The dialog that shows
it lives in `feature/apps`; the Tasker notification that shows it lives in `broadcast-receiver`;
neither can see the other's strings, so the sentence has to sit below both.

The English is the author's, verbatim, and is asserted against their exact text before anything
is written — including the comma before a capitalised "Please", which they confirmed is
deliberate and must not be tidied into a full stop.

Writes nothing unless every locale is present, every value survives the escaping checks, and
every result still parses.
"""
from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "common/src/main/res"

LOCALES = [
    "values", "values-ar", "values-b+pt+BR", "values-b+zh+Hans", "values-de",
    "values-es", "values-fr", "values-hi", "values-ja", "values-ko", "values-ru",
]

KEY = "permissions_lost"

# The author's words. Do NOT tidy: the comma before "Please", the capital P after it, and the
# plural "permissions" are all theirs and were confirmed as typed.
AUTHOR_ENGLISH = (
    "Necessary permissions lost, Please open IMD and re-grant the permissions first."
)

VALUES = {
    "values": AUTHOR_ENGLISH,
    "values-ar": "‏تم فقدان الأذونات الضرورية. يرجى فتح IMD وإعادة منح الأذونات أولاً.",
    "values-b+pt+BR": "Permissões necessárias perdidas. Abra o IMD e conceda as permissões novamente.",
    "values-b+zh+Hans": "必要权限已丢失。请先打开 IMD 并重新授予权限。",
    "values-de": "Notwendige Berechtigungen verloren. Bitte öffne IMD und erteile die Berechtigungen erneut.",
    "values-es": "Se han perdido los permisos necesarios. Abre IMD y vuelve a concederlos primero.",
    "values-fr": "Autorisations nécessaires perdues. Veuillez ouvrir IMD et accorder à nouveau les autorisations.",
    "values-hi": "आवश्यक अनुमतियाँ खो गई हैं। कृपया पहले IMD खोलें और अनुमतियाँ फिर से दें।",
    "values-ja": "必要な権限が失われました。まず IMD を開いて権限を再度付与してください。",
    "values-ko": "필요한 권한이 사라졌습니다. 먼저 IMD를 열어 권한을 다시 부여해 주세요.",
    "values-ru": "Необходимые разрешения утрачены. Пожалуйста, откройте IMD и предоставьте разрешения заново.",
}

# Every locale must name the app, which is the one thing the sentence asks the reader to open.
MUST_CONTAIN = "IMD"


def fail(message: str) -> int:
    print(f"REFUSED, nothing written: {message}")
    return 1


def main() -> int:
    # --- the author's English, asserted before anything else ---------------------------
    if VALUES["values"] != AUTHOR_ENGLISH:
        return fail("the English value is not the author's text")

    if "lost, Please" not in AUTHOR_ENGLISH:
        return fail("the English lost the author's comma before a capitalised 'Please'")

    if not AUTHOR_ENGLISH.endswith("first."):
        return fail("the English lost its ending")

    # --- coverage -----------------------------------------------------------------------
    missing = [loc for loc in LOCALES if loc not in VALUES]

    if missing:
        return fail(f"{KEY} is missing locales: {missing}")

    extra = [loc for loc in VALUES if loc not in LOCALES]

    if extra:
        return fail(f"{KEY} has unknown locales: {extra}")

    for locale, value in VALUES.items():
        if MUST_CONTAIN not in value:
            return fail(f"{KEY}/{locale}: does not name {MUST_CONTAIN}")

    # --- escaping, collisions, and the write --------------------------------------------
    planned: dict[Path, str] = {}

    for locale in LOCALES:
        path = RES / locale / "strings.xml"

        if not path.is_file():
            return fail(f"missing {path.relative_to(ROOT)}")

        text = path.read_text(encoding="utf-8")

        if f'name="{KEY}"' in text:
            return fail(f"{KEY} already exists in {locale} — has this run before?")

        value = VALUES[locale]

        if "'" in value and "\\'" not in value:
            return fail(f"{KEY}/{locale}: unescaped apostrophe")

        if "&" in value and "&amp;" not in value:
            return fail(f"{KEY}/{locale}: unescaped ampersand")

        if "\n" in value:
            return fail(f"{KEY}/{locale}: a literal newline collapses to a space; use \\n")

        marker = "</resources>"

        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        block = f'    <string name="{KEY}">{value}</string>\n'

        planned[path] = text.replace(marker, block + marker)

    # --- the result must still parse, with exactly one new key ---------------------------
    for path, text in planned.items():
        try:
            root = ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

        found = [child for child in root if child.get("name") == KEY]

        if len(found) != 1:
            return fail(f"{path.relative_to(ROOT)}: {len(found)} copies of {KEY}, wanted 1")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {KEY} x {len(LOCALES)} locale(s) = {len(LOCALES)} strings")
    print(f"  English: {AUTHOR_ENGLISH!r}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
