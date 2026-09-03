#!/usr/bin/env python3
"""
v3-r1 — the Support dialog.

  * point 1 is rewritten: a bold sentence, then a bracketed aside on its own line
  * points 3 and 4 gain a clickable phrase each, to the issue tracker and the subreddit

The author's English for point 1, verbatim:
    Share this project/app to community. This is most helpful and will help to keep the
    project alive.
    (I don't need any credit or mentions)

⚠ **A link phrase must occur verbatim in its own locale's sentence** or the link silently
matches nothing and the point renders as plain text. That is not hypothetical: Russian
help_launch_tile_name was nominative while its sentence needed the accusative, and the
emphasis matched nothing for a whole release. Every phrase below is asserted against the
sentence it belongs to before anything is written.
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

AUTHOR_SHARE = (
    "Share this project/app to community. This is most helpful and will help to keep the "
    "project alive."
)
AUTHOR_SHARE_NOTE = "(I don\\'t need any credit or mentions)"

REPLACE = {
    "support_point_share": {
        "values": AUTHOR_SHARE,
        "values-ar": "شارك هذا المشروع/التطبيق مع المجتمع. هذا هو الأكثر فائدة وسيساعد على إبقاء المشروع حيًا.",
        "values-b+pt+BR": "Compartilhe este projeto/app com a comunidade. Isso ajuda muito e mantém o projeto vivo.",
        "values-b+zh+Hans": "把这个项目/应用分享给社区。这是最有帮助的方式，也能让项目继续下去。",
        "values-de": "Teilen Sie dieses Projekt bzw. diese App mit der Community. Das hilft am meisten und hält das Projekt am Leben.",
        "values-es": "Comparte este proyecto/aplicación con la comunidad. Es lo más útil y ayudará a mantener vivo el proyecto.",
        "values-fr": "Partagez ce projet ou cette appli avec la communauté. C\\'est le plus utile et cela aide à garder le projet en vie.",
        "values-hi": "इस प्रोजेक्ट/ऐप को समुदाय के साथ साझा करें. यह सबसे अधिक मददगार है और प्रोजेक्ट को जीवित रखने में मदद करेगा.",
        "values-ja": "このプロジェクト／アプリをコミュニティに共有してください。もっとも助けになり、プロジェクトの継続につながります。",
        "values-ko": "이 프로젝트/앱을 커뮤니티에 공유해 주세요. 가장 큰 도움이 되며 프로젝트를 계속 이어가는 데 힘이 됩니다.",
        "values-ru": "Поделитесь этим проектом или приложением с сообществом. Это помогает больше всего и поддерживает проект живым.",
    },
}

ADD = {
    "support_point_share_note": {
        "values": AUTHOR_SHARE_NOTE,
        "values-ar": "(لا أحتاج إلى أي فضل أو ذكر)",
        "values-b+pt+BR": "(Não preciso de créditos nem menções)",
        "values-b+zh+Hans": "（我不需要任何署名或提及）",
        "values-de": "(Ich brauche keine Nennung und keine Erwähnung)",
        "values-es": "(No necesito ningún crédito ni mención)",
        "values-fr": "(Je n\\'ai besoin d\\'aucun crédit ni mention)",
        "values-hi": "(मुझे किसी श्रेय या उल्लेख की ज़रूरत नहीं है)",
        "values-ja": "（クレジットや言及は必要ありません）",
        "values-ko": "(크레딧이나 언급은 필요하지 않습니다)",
        "values-ru": "(Мне не нужны упоминания или благодарности)",
    },
    # Must be a verbatim substring of support_point_bugs in the same locale.
    "support_point_bugs_link": {
        "values": "Report",
        "values-ar": "أبلغ",
        "values-b+pt+BR": "Relate",
        "values-b+zh+Hans": "报告",
        "values-de": "Melden Sie",
        "values-es": "Reporta",
        "values-fr": "Signalez",
        "values-hi": "रिपोर्ट करें",
        "values-ja": "報告",
        "values-ko": "신고",
        "values-ru": "Сообщайте",
    },
    # Must be a verbatim substring of support_point_discuss in the same locale.
    "support_point_discuss_link": {
        "values": "Join",
        "values-ar": "شارك",
        "values-b+pt+BR": "Participe",
        "values-b+zh+Hans": "加入",
        "values-de": "Nehmen Sie",
        "values-es": "Únete",
        "values-fr": "Rejoignez",
        "values-hi": "शामिल हों",
        "values-ja": "参加",
        "values-ko": "참여",
        "values-ru": "Присоединяйтесь",
    },
}

# link key -> the sentence key it must appear inside
COUPLED = {
    "support_point_bugs_link": "support_point_bugs",
    "support_point_discuss_link": "support_point_discuss",
}


def fail(message):
    print(f"REFUSED, nothing written: {message}")
    return 1


def value_of(text, key):
    marker = f'<string name="{key}">'
    start = text.find(marker)
    if start == -1:
        return None
    start += len(marker)
    end = text.find("</string>", start)
    return text[start:end] if end != -1 else None


def main():
    if REPLACE["support_point_share"]["values"] != AUTHOR_SHARE:
        return fail("the English share point is not the author's text")

    for table in list(REPLACE.values()) + list(ADD.values()):
        missing = [loc for loc in LOCALES if loc not in table]
        if missing:
            return fail(f"missing locales: {missing}")

    planned = {}
    checked = 0

    for locale in LOCALES:
        path = RES / locale / "strings.xml"
        text = path.read_text(encoding="utf-8")

        # the coupling that the Russian-case bug exists to enforce
        for link_key, sentence_key in COUPLED.items():
            sentence = value_of(text, sentence_key)
            if sentence is None:
                return fail(f"{locale}: {sentence_key} not found")

            phrase = ADD[link_key][locale]
            if phrase not in sentence:
                return fail(
                    f"{locale}: {link_key} {phrase!r} is not a verbatim substring of "
                    f"{sentence_key} {sentence!r} — the link would match nothing",
                )
            checked += 1

        for key, table in REPLACE.items():
            current = value_of(text, key)
            if current is None:
                return fail(f"{locale}: {key} not found")
            text = text.replace(
                f'<string name="{key}">{current}</string>',
                f'<string name="{key}">{table[locale]}</string>',
                1,
            )

        block = ""
        for key, table in ADD.items():
            if f'name="{key}"' in text:
                return fail(f"{locale}: {key} already exists — has this run before?")
            value = table[locale]
            if "'" in value and "\\'" not in value:
                return fail(f"{locale}/{key}: unescaped apostrophe")
            if "&" in value and "&amp;" not in value:
                return fail(f"{locale}/{key}: unescaped ampersand")
            if "\n" in value:
                return fail(f"{locale}/{key}: literal newline")
            block += f'    <string name="{key}">{value}</string>\n'

        marker = "</resources>"
        if text.count(marker) != 1:
            return fail(f"{locale}: expected exactly one {marker}")

        planned[path] = text.replace(marker, block + marker, 1)

    for path, text in planned.items():
        try:
            ET.fromstring(text)
        except ET.ParseError as error:
            return fail(f"{path.relative_to(ROOT)} would not parse: {error}")

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(planned)} locale(s)")
    print(f"  {checked} link-phrase/sentence pairs asserted verbatim")
    print(f"  point 1: {AUTHOR_SHARE!r}")
    print(f"           {AUTHOR_SHARE_NOTE!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
