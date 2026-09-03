#!/usr/bin/env python3
"""
Reports type names a round **introduces** into a Kotlin file without importing them.

    python3 tools/check_new_types.py /path/to/baseline

**Why this exists.** In r2h `Color.White` was written into `FavouriteAppsScreen.kt`, which had
no `androidx.compose.ui.graphics.Color` import. **All 23 audits passed it**, and so did the
domain compile, the host tests, the translations and the lost-declaration check. The author's
Gradle build would have been the first thing to notice.

Nothing in the suite could have caught it:

* `check12_unusedimports` finds imports nothing uses — the exact opposite question.
* `check18_missing_imports` covers **internal top-level functions** declared elsewhere in the
  project, not framework types.
* `check20_resrefs` covers `R.string.*`, not Kotlin types.
* `check21_syntax` only parses, and `Color.White` parses perfectly.
* `check23_crossmodule_visibility` is about `internal` across modules, not existence.

**Why it is a diff rather than a full resolver.** `check_lost_declarations` records that a
reference-resolving check was tried and abandoned: with no classpath, every Android and Compose
type in the project looks unresolvable and the output is noise. That reasoning is right for a
whole-tree check and wrong for a **round-level** one. What a round can be held to is much
narrower and completely checkable:

> every capitalised name that this round **adds** to a file must be importable from that file.

A name already in the baseline is somebody else's problem and is presumed to compile, because
the author has been building this project all along. Only the delta is judged, so the noise
floor is zero on an unchanged tree — this check reports nothing at all until a round writes a
new type name somewhere.

**What counts as importable**, in order:

1. it appears in the file's own import list;
2. it is declared in the file;
3. it is declared in another file of the same package anywhere in the tree (Kotlin resolves
   package-mates with no import — this is what stops every `GetoIcons` and `DialogContainer`
   from being reported), or it is a **generic parameter** of a declaration in the file, which
   `fun <T> track(block: suspend () -> T): T` needs and no import can ever supply;
4. it is in the Kotlin builtins list below, which is short on purpose: everything else has to
   be spelled out.

Star imports are honoured by giving up on the file, which is the honest answer — there are
almost none in this project and pretending to resolve one would be worse than saying so.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Kotlin's default imports, plus the handful of built-in names a file can use with no import.
# Deliberately minimal: a name missing from here is reported, and adding it is a decision
# somebody makes on purpose rather than a hole that widens by itself.
BUILTINS = {
    "Any", "Array", "Boolean", "BooleanArray", "Byte", "ByteArray", "Char", "CharArray",
    "CharSequence", "Comparable", "Deprecated", "Double", "DoubleArray", "Enum", "Error",
    "Exception", "Float", "FloatArray", "Function", "IllegalArgumentException",
    "IllegalStateException", "IndexOutOfBoundsException", "Int", "IntArray", "Iterable",
    "Iterator", "JvmField", "JvmName", "JvmOverloads", "JvmStatic", "Lazy", "List", "Long",
    "LongArray", "Map", "MutableList", "MutableMap", "MutableSet", "Nothing",
    "NoSuchElementException", "Number", "Pair", "Regex", "Result", "RuntimeException", "Set",
    "Short", "ShortArray", "String", "StringBuilder", "Suppress", "Throwable", "Triple",
    "UInt", "ULong", "Unit", "UnsupportedOperationException", "OptIn", "Volatile",
    "Synchronized", "Transient", "Strictfp", "Throws", "System", "Math", "Thread",
}

IMPORT = re.compile(r"^import\s+([\w.]+)(?:\s+as\s+(\w+))?\s*$", re.MULTILINE)

STAR_IMPORT = re.compile(r"^import\s+[\w.]+\.\*\s*$", re.MULTILINE)

PACKAGE = re.compile(r"^package\s+([\w.]+)\s*$", re.MULTILINE)

# Declarations a file provides to itself and to its package-mates.
#
# ⚠ **Values and functions as well as types**, and the first run of this check refused six of
# its own: `TAG`, `SHORT_NAMES`, `ActionButton`, `GetoRed` and two alpha constants are all
# capitalised names a round had just declared *in the file that uses them*. A pattern that read
# only `class|object|interface|typealias` called every one of them unimported.
DECLARED = re.compile(
    r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*"
    r"(?:public\s+|internal\s+|private\s+|protected\s+|abstract\s+|open\s+|sealed\s+|data\s+"
    r"|value\s+|inline\s+|annotation\s+|enum\s+|const\s+|suspend\s+|operator\s+"
    r"|override\s+|lateinit\s+|expect\s+|actual\s+)*"
    r"(?:class|object|interface|typealias|fun|val|var)\s+"
    r"(?:<[^>]*>\s*)?"          # a generic parameter list on a function
    r"(?:[\w.]+\.)?"            # an extension receiver
    r"(\w+)",
    re.MULTILINE,
)

# A capitalised name used as a type or a receiver. Excludes anything preceded by a dot, which
# is a member rather than a name being resolved, and anything followed by one of the string
# delimiters, which is inside a comment or a literal often enough to matter.
USED = re.compile(r"(?<![\w.@])([A-Z][A-Za-z0-9_]*)")

COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.DOTALL)

STRING = re.compile(r'"""".*?"""|""".*?"""|"(?:\\.|[^"\\\n])*"', re.DOTALL)


def strip(text: str) -> str:
    """Comments and string literals removed, so prose cannot look like a type reference."""
    return COMMENT.sub(" ", STRING.sub('""', text))


def names_used(text: str) -> set[str]:
    body = strip(text)

    # Everything above the first declaration is the package line and the imports; a name there
    # is being declared as importable rather than used.
    without_imports = IMPORT.sub(" ", PACKAGE.sub(" ", body))

    return set(USED.findall(without_imports)) - NEVER_IMPORTED


# ⚠ **`R` is generated into the module's own package**, so every file in that package sees it
# with no import - SettingsScreen.kt uses `R.string.…` throughout and imports no R at all. A file
# in a *different* package cannot use the bare name: it has to alias it, as this repo does with
# `R as commonR` and `R as settingsR`, and an alias is a different token this checker already
# understands.
#
# So a bare R is never a name an import could have supplied. Excluding it is the extractor
# becoming correct, not the check being relaxed.
NEVER_IMPORTED = {"R"}


def imported(text: str) -> set[str]:
    found: set[str] = set()

    for path, alias in IMPORT.findall(text):
        found.add(alias or path.rsplit(".", 1)[-1])

    return found


# An enum entry declares a name with no keyword in front of it, which no declaration pattern
# built around `class|object|fun|val` can see. Its first real run reported three of them —
# `PriorHide`, and `HiddenFromPreviousUse` twice — as unimported uses of themselves.
ENUM_ENTRY = re.compile(r"^\s{4}([A-Z][A-Za-z0-9_]*)\s*(?:,|;|\(|$)", re.MULTILINE)


# A generic parameter list declares names that resolve nowhere else: `fun <T> track(...): T` uses
# `T` three times and imports it never. Reported on its first encounter — `PriorHideRestore.track`
# — as an unimported type, which it is not.
#
# Deliberately crude. It matches the *contents* of any `<...>` that follows `fun` or a type
# keyword, so a bound (`<T : Any>`) and a variance marker (`<out T>`) both give up their names
# along with the bound's own type, which is already resolvable or already reported elsewhere in
# the same file. Over-collecting inside a declaration site is the safe direction: the alternative
# is a parser.
TYPE_PARAMS = re.compile(
    r"(?:fun|class|interface|object|typealias)\s*<([^>]*)>",
    re.MULTILINE,
)

TYPE_PARAM_NAME = re.compile(r"(?<![\w.])([A-Z][A-Za-z0-9_]*)")


def declared(text: str) -> set[str]:
    body = strip(text)

    generics: set[str] = set()

    for params in TYPE_PARAMS.findall(body):
        generics.update(TYPE_PARAM_NAME.findall(params))

    return set(DECLARED.findall(body)) | set(ENUM_ENTRY.findall(body)) | generics


def package_of(text: str) -> str:
    match = PACKAGE.search(text)

    return match.group(1) if match else ""


def kotlin_files(root: Path) -> list[Path]:
    return [
        path
        for path in sorted(root.rglob("*.kt"))
        if "build" not in path.relative_to(root).parts
    ]


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} /path/to/baseline", file=sys.stderr)

        return 2

    baseline = Path(sys.argv[1]).resolve()

    root = Path(__file__).resolve().parents[1]

    if not baseline.is_dir():
        print(f"{baseline} is not a directory", file=sys.stderr)

        return 2

    # Everything every package provides, across the whole tree. A package-mate needs no import,
    # which is why this is gathered once rather than guessed at per file.
    by_package: dict[str, set[str]] = {}

    texts: dict[Path, str] = {}

    for path in kotlin_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")

        texts[path] = text

        by_package.setdefault(package_of(text), set()).update(declared(text))

    problems: list[str] = []

    checked = 0

    skipped = 0

    for path, text in texts.items():
        relative = path.relative_to(root)

        old = baseline / relative

        # A new file is judged in full: nothing in it is somebody else's problem.
        before = (
            names_used(old.read_text(encoding="utf-8", errors="replace"))
            if old.is_file()
            else set()
        )

        added = names_used(text) - before

        if not added:
            continue

        checked += 1

        if STAR_IMPORT.search(text):
            skipped += 1

            continue

        resolvable = (
            imported(text)
            | declared(text)
            | by_package.get(package_of(text), set())
            | BUILTINS
        )

        for name in sorted(added - resolvable):
            problems.append(f"{relative}: {name} is new here and not imported")

    if problems:
        print(f"checked {checked} changed file(s); {len(problems)} problem(s)")

        for problem in problems:
            print(f"  {problem}")

        return 1

    print(
        f"checked {checked} file(s) with new type names"
        + (f", {skipped} skipped for a star import" if skipped else "")
        + "; 0 unimported",
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
