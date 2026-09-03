#!/usr/bin/env python3
r"""
r29g2 — `check_translations.py` learns to read backslash escapes.

## Why this exists

r29-2 shipped a broken escape into French and aapt refused the entire resource table:

    values-fr.xml:218:4: Failed to flatten XML for resource 'help_path_accessibility'
    with error: Invalid unicode escape sequence in string
    …
    java.lang.IllegalStateException: Can not extract resource from ParsedResource@1b4d47f7

The value was `Services d\\'accessibilité` — a doubled backslash. It got there because
`ElementTree` resolves XML entities but knows **nothing about Android's backslash escapes**; they
are ordinary characters to it. A value read back out of an already-translated file therefore
arrives still carrying its `\'`, and r29's writer escaped it a second time.

⚠ **Not one existing check could see it.** The key sets matched, the format specifiers matched, the
emphasis substrings matched, and the XML parsed cleanly — because at the XML level nothing is
wrong. The fault lives one level down, in text that only Android interprets, and every checker in
this file had been reading through `strings()`, which is ET.

So this one reads the raw file.

## What it flags

* **A doubled backslash.** Legal in principle — it means one literal backslash — but no string in
  this app contains one, and every occurrence so far has been a value escaped twice.
* **An escape Android does not understand.** `\n`, `\t`, `\'`, `\"`, `\\`, `\@`, `\?` and
  `\uXXXX` are the whole set.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER = ROOT / "tools/check_translations.py"

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


BLOCK = '''# The whole set Android understands after a backslash. Anything else is a typo, and a doubled
# backslash - legal in principle, meaning one literal backslash - has so far only ever been a value
# that went through an escaping pass twice.
VALID_AFTER_BACKSLASH = frozenset(
    [
        "n",
        "t",
        "u",
        "@",
        "?",
        "'",
        '"',
        "\\\\",
    ],
)

RAW_STRING = re.compile(r'<string\\s+name="([^"]+)"[^>]*>(.*?)</string>', re.S)

HEX = frozenset("0123456789abcdefABCDEF")


def check_escapes(module: pathlib.Path, locale: str) -> list[str]:
    """Backslash escapes, read at the raw level where they actually live.

    \\u26a0 **Deliberately not built on `strings()`.** That parses with ElementTree, which resolves
    XML entities and leaves backslash escapes alone as ordinary text - so a doubled backslash is
    invisible to it, and to every other check in this file. r29 lost a whole resource table to one.
    """
    path = module / f"src/main/res/values-{locale}/strings.xml"

    if not path.exists():
        return []

    problems = []

    for name, raw in RAW_STRING.findall(path.read_text(encoding="utf-8")):
        position = 0

        while position < len(raw):
            if raw[position] != "\\\\":
                position += 1

                continue

            following = raw[position + 1:position + 2]

            if following == "\\\\":
                problems.append(
                    f"{module.name}/{locale}: '{name}' has a doubled backslash - "
                    "almost always a value that was escaped twice",
                )

                break

            if following not in VALID_AFTER_BACKSLASH:
                problems.append(
                    f"{module.name}/{locale}: '{name}' has an escape Android does not "
                    f"understand: {raw[position:position + 2]!r}",
                )

                break

            if following == "u" and not set(raw[position + 2:position + 6]) <= HEX:
                problems.append(
                    f"{module.name}/{locale}: '{name}' has a truncated unicode escape: "
                    f"{raw[position:position + 6]!r}",
                )

                break

            position += 2

    return problems


'''

checker = CHECKER.read_text(encoding="utf-8")

check(
    "check_escapes" not in checker,
    "checker: an escape check already exists",
)

check(
    "def check(module: pathlib.Path, locale: str) -> list[str]:" in checker,
    "checker: the main check function is not where it was",
)

checker = replace_once(
    checker,
    "def check(module: pathlib.Path, locale: str) -> list[str]:",
    BLOCK + "def check(module: pathlib.Path, locale: str) -> list[str]:",
    "checker: the escape check",
)

checker = replace_once(
    checker,
    "        for module in modules:\n"
    "            all_problems += check(module, locale)\n",
    "        for module in modules:\n"
    "            all_problems += check(module, locale)\n"
    "\n"
    "            all_problems += check_escapes(module, locale)\n",
    "checker: calling the escape check",
)

check(
    checker.count("def check_escapes(") == 1,
    "checker: check_escapes is not declared exactly once",
)

check(
    checker.count("check_escapes(module, locale)") == 1,
    "checker: check_escapes is not called exactly once",
)

# It is a syntax error in a tool the author runs every round, so it is compiled before it is written.
try:
    compile(checker, str(CHECKER), "exec")
except SyntaxError as error:
    failures.append(f"checker: the result does not parse — {error}")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

CHECKER.write_text(checker, encoding="utf-8")

print(f"wrote {CHECKER.relative_to(ROOT).as_posix()}")

print("ok")
