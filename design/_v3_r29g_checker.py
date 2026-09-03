#!/usr/bin/env python3
"""
r29g — `tools/check_translations.py` stops under-reporting, in both of the ways it did.

## What it was doing

Two independent narrowings, and the handover's *"under-reports by about six times"* was the sum of
them rather than a bug in either:

1. **`locales = sys.argv[1:] or ["hi"]`.** Run the way §4 of the handover runs it — no arguments —
   it checked Hindi and nothing else. The default is now all ten.
2. **A 129-entry `DEFERRED` allowlist**, which subtracted the keys the author had deliberately not
   translated yet. It was doing exactly its job: keeping a deferral visible as a deferral rather
   than letting an untranslated key be disguised as a translation identical to English.

r29 wrote all of them, so the allowlist has nothing left to hold. ⚠ **It is emptied rather than
deleted**, with the note kept, because the mechanism is the right one and the next batch of new
strings will want it again. Five of its entries — `auto_hide_flow_2`, `auto_hide_flow_3`,
`revert_defaults_entry_both`, `shizuku_rikka_warning`, `ui_fade` — had already stopped being
missing from anywhere and were quietly making the list look bigger than the debt.

The eight step lines and `support_view_github_button` are **not** listed here: they carry
`translatable="false"` since r29a, which is the honest way to say "this one stays English" — the
checker skips them at the source and no allowlist is involved.

## The emphasis list gains the pair that was missing from it

`SupportDialog` underlines `support_name_project` and `support_name_alive` as substrings of
`support_intro_3`. That coupling was never in `EMPHASIS`, so nothing would have caught a
translation of either phrase that did not appear inside the sentence — which is the exact failure
the list exists to catch, on the two strings most likely to be retranslated by hand later.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER = ROOT / "tools/check_translations.py"

LOCALES = ["hi", "ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "ja", "ko", "ru"]

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


checker = CHECKER.read_text(encoding="utf-8")

# ---------------------------------------------------------------- the allowlist

start = checker.index("DEFERRED = {")

end = checker.index("\n}\n", start) + len("\n}\n")

old_block = checker[start:end]

# ⚠ Counted before the replacement, on the block being replaced — not on the file, whose comments
# name several of these keys for other reasons.
entries = len(re.findall(r'^\s{4}"[a-z0-9_]+",$', old_block, re.M))

check(
    entries > 100,
    f"checker: found {entries} DEFERRED entries, expected the ~129-entry list",
)

new_block = (
    "DEFERRED: set[str] = set()\n"
)

checker = replace_once(checker, old_block, new_block, "checker: the DEFERRED block")

# The comment above it explained the old policy. It now explains why the set is empty.
checker = replace_once(
    checker,
    "# Keys the author has deliberately left untranslated for now.",
    "# Keys the author has deliberately left untranslated for now.\n"
    "#\n"
    "# ⚠ **Empty since r29, and kept rather than deleted.** r29 translated all 150 of the keys this\n"
    "# held, so there is no debt left for it to record — but the mechanism is the right one and the\n"
    "# next batch of new strings will want it. A key that is never going to be translated does not\n"
    "# belong here at all: give it translatable=\"false\", which this checker already skips, the way\n"
    "# the six Shizuku/Shevery step lines and support_view_github_button now do.",
    "checker: the DEFERRED comment",
)

check(
    "DEFERRED: set[str] = set()" in checker,
    "checker: the allowlist was not emptied",
)

check(
    "prior_hide_title" not in checker,
    "checker: an old DEFERRED entry survived",
)

# ---------------------------------------------------------------- the emphasis pair

checker = replace_once(
    checker,
    '    ("feature/settings", "notification_function_revert_detail", ["revert_defaults_entry"]),\n',
    '    ("feature/settings", "notification_function_revert_detail", ["revert_defaults_entry"]),\n'
    '    # r29: SupportDialog underlines these two inside support_intro_3. The coupling is as old as\n'
    '    # the dialog and was never listed, so a translation of either phrase that did not appear\n'
    '    # inside that locale\'s own sentence would simply have underlined nothing.\n'
    '    ("feature/settings", "support_intro_3",\n'
    '     ["support_name_project", "support_name_alive"]),\n',
    "checker: the emphasis pair",
)

check(
    checker.count('"support_intro_3",\n') == 1,
    "checker: the support emphasis entry did not land exactly once",
)

# ---------------------------------------------------------------- the default locale list

checker = replace_once(
    checker,
    '    locales = sys.argv[1:] or ["hi"]\n',
    "    # ⚠ **All ten by default since r29.** It used to be Hindi alone, which is how the handover\n"
    "    # invoked it — so the number it printed was one locale's, and read as the whole app's.\n"
    "    locales = sys.argv[1:] or [\n"
    '        "hi", "ar", "b+pt+BR", "b+zh+Hans", "de", "es", "fr", "ja", "ko", "ru",\n'
    "    ]\n",
    "checker: the default locale list",
)

for locale in LOCALES:
    check(
        f'"{locale}"' in checker,
        f"checker: {locale} is not in the default list",
    )

check(
    'or ["hi"]' not in checker,
    "checker: the Hindi-only default survived",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

CHECKER.write_text(checker, encoding="utf-8")

print(f"wrote {CHECKER.relative_to(ROOT).as_posix()} (emptied {entries} DEFERRED entries)")

print("ok")
