#!/usr/bin/env python3
"""
r29f — the translation batch. 150 keys × 10 locales = 1,500 strings.

The author lifted the standing *"do not run or touch translations"* rule for this round, all at
once rather than by module or by locale.

## What the repo's own checker was and was not saying

`tools/check_translations.py` printed *"26 PROBLEMS, locales: hi"*. Both halves of that are
narrowings, and they multiply out exactly:

* `locales = sys.argv[1:] or ["hi"]` — run with no arguments it checks **Hindi only**, which is how
  §4 of the handover invokes it.
* a 129-entry `DEFERRED` allowlist subtracted the keys the author had deliberately not translated
  yet — 132 of the 158 module/key pairs that were actually absent.

158 − 132 = 26, and across all ten locales 26 × 10 + 2 = 262. Neither number was wrong; they were
answers to different questions. r29a then marked nine keys `translatable="false"` and added
`setup_done_4_4`, which is how 158 became the 150 written here.

## Three groups, written three different ways

**1. Typed.** 131 distinct key names, in `design/translations_r29/<locale>.py` as plain text —
real apostrophes, real newlines. This script does the Android escaping, so a `'` cannot be
half-escaped by hand in one file out of ten.

**2. Derived — the `help_path_*` keys.** These are navigation trails: *"IMD Settings → Default IMD
settings → Accessibility services managed by IMD"*. ⚠ **Translating them as sentences would point
the user at rows that do not exist under those names.** Each segment is therefore composed from the
key that actually labels that row *in that locale*, so a path always names what is on the screen.
That includes inheriting a locale's drift: German's `section_imd_plus` says "IMD+ (EXPERIMENTELL)"
where English now says "IMD+ (needs background service)", and the German path says EXPERIMENTELL —
because that is what the German settings screen says.

**3. Extracted — `support_name_project` and `support_name_alive`.** `SupportDialog` underlines
these as *substrings* of `support_intro_3`, which is already translated in all ten. A fresh
translation of "support this project" would not be found inside the existing sentence and nothing
would be underlined, silently. They are taken from each locale's own sentence and asserted to
appear inside it.

## Numerals

Every literal digit is Western, at the author's instruction — *"display keep western numerals
everywhere even arabic and hindi"*.

⚠ **That governs this file and not the runtime.** The digit substituted for `%1$d` is formatted by
`Resources.getString(int, Object...)` against the configuration locale, and `ar` carries the
`arab` numbering system, so those come out Arabic-Indic (٠١٢) whatever is written here. Forcing
Latin digits there is a Kotlin change at each call site, it would also change strings shipped in
earlier rounds, and it is **not** in this round — flagged to the author rather than done quietly.
`hi` is unaffected: Hindi's default numbering system is already `latn`.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import importlib.util
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "design/translations_r29"

MODULES = [
    "app",
    "common",
    "feature/app-settings",
    "feature/apps",
    "feature/settings",
    "framework/notification-manager",
    "service",
]

# The BCP47 folder suffix, and the module file that holds it.
LOCALES = {
    "hi": "hi",
    "ar": "ar",
    "b+pt+BR": "pt_BR",
    "b+zh+Hans": "zh_Hans",
    "de": "de",
    "es": "es",
    "fr": "fr",
    "ja": "ja",
    "ko": "ko",
    "ru": "ru",
}

SPEC = re.compile(r"%\d*\$?[sdf]|%[sdf]")

# ⚠ **`help_path_accessibility` is copied, not composed.** :feature:settings already had it in all
# ten locales; :feature:apps and :feature:app-settings did not. Composing a second wording for the
# same key name would leave one key with two texts, which is precisely the drift the derivation is
# supposed to prevent — so the module that already has one is the source, and nothing already
# shipped is rewritten.
#
# It is also where each locale's ROOT, ARROW and LINE_JOIN came from, so every trail composed below
# reads like the trails that were already there.
COPY_FROM_SETTINGS = ["help_path_accessibility"]

# section key, then the row or rows the trail ends at. Composed as
# "IMD {settings} → {section} → {rows joined by ' + '}".
PATHS = {
    "help_path_dooa": ("section_app_functions", ["overlay_packages_row"]),
    "help_path_manage_shizuku": ("shizuku_setup_page_title", ["manage_shizuku"]),
    "help_path_auto_hide": ("section_imd_plus", ["auto_hide"]),
    "help_path_auto_unhide": ("section_app_functions", ["auto_unhide"]),
    "help_path_hide_defaults": ("section_app_functions", ["settings_to_hide_defaults_label"]),
    "help_path_intents": ("section_advanced", ["tasker_integration"]),
    "help_path_unhide_both": ("section_app_functions", ["revert_defaults_entry", "revert_defaults"]),
}

SUPPORT_NAMES = ("support_name_project", "support_name_alive")

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def android_escape(value: str) -> str:
    """Plain text to what may sit between <string> and </string>.

    ⚠ The ampersand first, or every entity written after it gets its own `&` escaped again.
    Format specifiers are left completely alone: `%` is not an XML matter and `%%` in the source
    is already the literal-percent form aapt wants.
    """
    out = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    out = out.replace("'", "\\'").replace('"', '\\"')

    return out.replace("\n", "\\n")


UNESCAPE = re.compile(r"\\(u[0-9a-fA-F]{4}|.)", re.S)


def backslash_unescape(value: str) -> str:
    """Undo Android's *backslash* escapes only — the half `ElementTree` does not do.

    ⚠ **This exists because r29-2 shipped `d\\\\'accessibilité` into French and aapt refused the
    whole resource table.** `ElementTree` resolves XML entities but knows nothing about Android's
    *backslash* escapes — they are ordinary characters to it — so a value read back out of a
    translated file arrives still carrying its `\\'`. Escaping that a second time on the way out
    turns one escaped apostrophe into an escaped backslash followed by a bare one, which is not a
    string aapt will compile:

        values-fr.xml: Failed to flatten XML for resource 'help_path_accessibility'
        with error: Invalid unicode escape sequence in string

    Only the copied and derived groups read from existing files, so only they were exposed — two
    strings in the event — but the asymmetry was the bug: everything written went through
    [android_escape] and nothing read came back through its inverse.
    """
    def one(match: re.Match[str]) -> str:
        body = match.group(1)

        if body.startswith("u"):
            return chr(int(body[1:], 16))

        return {"n": "\n", "t": "\t"}.get(body, body)

    return UNESCAPE.sub(one, value)


def android_unescape(value: str) -> str:
    """The exact inverse of [android_escape], for the round-trip assertion.

    ⚠ **Both halves, in the opposite order.** `android_escape` writes the XML entities first and
    the backslashes second, so undoing it means backslashes first and entities second. Reading a
    file needs only [backslash_unescape], because `ElementTree` has already resolved the entities
    by the time the text reaches us — which is precisely the asymmetry that produced the bug this
    function now guards.
    """
    out = backslash_unescape(value)

    return out.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")


def load(locale_file: str):
    path = DATA / f"{locale_file}.py"

    spec = importlib.util.spec_from_file_location(f"tr_{locale_file}", path)

    module = importlib.util.module_from_spec(spec)

    spec.loader.exec_module(module)

    return module


def strings_of(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    # ⚠ Unescaped on the way in. Every consumer of this wants plain text — the derivations
    # compose it, the support assertion searches it — and plain text is what android_escape
    # expects on the way back out.
    return {
        e.get("name"): backslash_unescape("".join(e.itertext()))
        for e in ET.parse(path).getroot().findall("string")
    }


def english_of(module: str) -> dict[str, str]:
    path = ROOT / module / "src/main/res/values/strings.xml"

    return {
        e.get("name"): backslash_unescape("".join(e.itertext()))
        for e in ET.parse(path).getroot().findall("string")
        if e.get("translatable") != "false"
    }


english = {module: english_of(module) for module in MODULES}

# What each module is missing, per locale. Identical across the ten today, but computed rather
# than assumed — the whole point of the audit was that a number everyone repeats can be wrong.
missing: dict[str, dict[str, list[str]]] = {}

for locale in LOCALES:
    missing[locale] = {}

    for module in MODULES:
        have = set(strings_of(ROOT / module / f"src/main/res/values-{locale}/strings.xml"))

        missing[locale][module] = sorted(k for k in english[module] if k not in have)

pairs = sum(len(v) for m in missing.values() for v in m.values())

check(pairs == 1500, f"expected 1,500 module/key pairs across ten locales, found {pairs}")

for locale, by_module in missing.items():
    count = sum(len(v) for v in by_module.values())

    check(count == 150, f"{locale}: {count} keys missing, expected 150")

writes: dict[Path, str] = {}

written_total = 0

for locale, locale_file in LOCALES.items():
    data = load(locale_file)

    # Everything this locale already says, plus everything it is about to say. The derived paths
    # below need both — `accessibility_services_row` is itself new this round.
    lookup: dict[str, str] = {}

    for module in MODULES:
        for name, value in strings_of(
            ROOT / module / f"src/main/res/values-{locale}/strings.xml",
        ).items():
            lookup.setdefault(name, value)

    lookup.update(data.T)

    lookup.update(data.SUPPORT)

    # ---------------------------------------------------------------- the underlined phrases

    intro = lookup.get("support_intro_3", "")

    if check(bool(intro), f"{locale}: support_intro_3 is missing, so nothing can be underlined"):
        for name in SUPPORT_NAMES:
            phrase = data.SUPPORT.get(name, "")

            check(
                bool(phrase) and phrase in intro,
                f"{locale}: {name} ({phrase!r}) does not appear inside support_intro_3, "
                "so SupportDialog would underline nothing",
            )

    # ---------------------------------------------------------------- the derived trails

    derived: dict[str, str] = {}

    settings_translated = strings_of(
        ROOT / "feature/settings" / f"src/main/res/values-{locale}/strings.xml",
    )

    for name in COPY_FROM_SETTINGS:
        existing = settings_translated.get(name)

        if check(
            existing is not None,
            f"{locale}: {name} was expected to already exist in :feature:settings",
        ):
            derived[name] = existing

    if check(bool(getattr(data, "ROOT", "")), f"{locale}: no ROOT label to build a path on"):
        for name, (section_key, row_keys) in PATHS.items():
            section = lookup.get(section_key)

            rows = [lookup.get(k) for k in row_keys]

            if not check(
                section is not None and all(rows),
                f"{locale}: {name} needs {section_key} and {row_keys}, and one of them is absent",
            ):
                continue

            # ⚠ The row labels carry a newline — "Accessibility services\nmanaged by IMD" is two
            # lines in the settings list. A trail is one line, so it is flattened rather than
            # re-translated, which is what keeps the two spellings the same words.
            tail = " + ".join(row.replace("\n", data.LINE_JOIN) for row in rows)

            derived[name] = f"{data.ROOT}{data.ARROW}{section}{data.ARROW}{tail}"

    # ---------------------------------------------------------------- assemble per module

    for module in MODULES:
        names = missing[locale][module]

        if not names:
            continue

        path = ROOT / module / f"src/main/res/values-{locale}/strings.xml"

        text = path.read_text(encoding="utf-8")

        lines = []

        for name in names:
            if name in derived:
                value = derived[name]
            elif name in data.SUPPORT:
                value = data.SUPPORT[name]
            elif name in data.T:
                value = data.T[name]
            else:
                failures.append(f"{locale}/{module}: no translation supplied for {name!r}")

                continue

            # ⚠ Specifiers compared as sorted sets against the English, exactly as the repo's
            # checker does — a translation may reorder %1$d and %2$d, which several of these do,
            # but it may not lose one. A lost specifier is a crash, not a typo.
            want = sorted(SPEC.findall(english[module][name]))

            got = sorted(SPEC.findall(value))

            check(
                want == got,
                f"{locale}/{module}: {name} specifiers {want} -> {got}",
            )

            escaped = android_escape(value)

            # ⚠ **The round trip is the assertion, not a search for one bad character.** If
            # escaping and unescaping are not inverses for this value then something upstream
            # handed us text that was already escaped, which is exactly how r29-2 shipped a
            # double backslash into French and lost the whole resource table.
            check(
                android_unescape(escaped) == value,
                f"{locale}/{module}: {name} does not survive escape/unescape — "
                f"{value!r} -> {escaped!r} -> {android_unescape(escaped)!r}",
            )

            lines.append(f'    <string name="{name}">{escaped}</string>')

        if not check(
            len(lines) == len(names),
            f"{locale}/{module}: built {len(lines)} of {len(names)} strings",
        ):
            continue

        block = (
            "    <!-- r29: the batch that closed the gap - see design/_v3_r29f_translations.py. -->\n"
            + "\n".join(lines)
            + "\n"
        )

        closing = "</resources>"

        if not check(
            text.count(closing) == 1,
            f"{locale}/{module}: {text.count(closing)} </resources>, expected 1",
        ):
            continue

        writes[path] = text.replace(closing, block + closing, 1)

        written_total += len(lines)

check(
    written_total == 1500,
    f"built {written_total} strings, expected 1,500",
)

# ---------------------------------------------------------------- re-parse before writing

for path, text in list(writes.items()):
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        failures.append(f"{path.parent.name}/{path.parts[-5]}: does not parse — {error}")

        continue

    names = [e.get("name") for e in root.findall("string")]

    check(
        len(names) == len(set(names)),
        f"{path.parent.name}: a duplicate <string name> was introduced",
    )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures[:40]:
        print(f"  - {failure}")

    if len(failures) > 40:
        print(f"  … and {len(failures) - 40} more")

    sys.exit(1)

for path, text in writes.items():
    path.write_text(text, encoding="utf-8")

print(f"wrote {len(writes)} files, {written_total} strings")

print("ok")
