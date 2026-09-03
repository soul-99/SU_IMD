#!/usr/bin/env python3
"""Top-level symbols used across a package boundary without an import.

⚠ **Born from r4, which shipped a zip that would not compile — three times over.** The round
added four top-level declarations to `:domain:model` (`overlayManageable`,
`accessibilityManageable`, `manageShizukuEffective`, `overlayBlockReasons`) and referenced them
from six other modules. Two missing imports were caught by the domain compile. The third was in
`broadcast-receiver`, which the sandbox **cannot** compile — only the five pure-JVM domain
modules really compile here — so 23 audits, the host tests and the zip round-trip all passed a
tree that failed in Android Studio on `DiagnosticStateReporter.kt:213`.

**Why nothing else catches it.** `check3_imports` asks whether the imports that *are* written
resolve; `check12` finds imports with no use; `check18` covers `internal` top-level *functions*;
and `check_new_types.py` collects **capitalised** names, so a lowercase extension property or
function sails straight past it. This is the missing half of `check_new_types`.

### What it does

1. Collects every **top-level** `val`/`var`/`fun` declaration in the repo, with its package —
   including extension receivers, which is the case that bit: `val UserData.overlayManageable`
   declares the name `overlayManageable`.
2. For every Kotlin file, finds references to those names — `.name` for properties, `name(` for
   functions, and a bare `name` on its own.
3. Reports a reference whose declaring package differs from the file's own package and which the
   file does not import, either by name or by a `package.*` star import.

Not a diff check: it reads the tree as it stands and has a zero noise floor, so it can be run on
any build without a baseline.

⚠ **Same-name declarations in two packages are skipped**, not guessed at — the point of this is
to catch the omission, not to resolve overloads.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SKIP_PARTS = {"build", "out", ".git", "design"}

PACKAGE = re.compile(r"^package\s+([\w.]+)", re.MULTILINE)
IMPORT = re.compile(r"^import\s+([\w.]+)(?:\s+as\s+\w+)?", re.MULTILINE)

# A top-level declaration starts at column 0. The optional receiver before the name is what
# makes an extension property findable by the name people actually write at the call site.
DECL = re.compile(
    r"^(?:@\w+(?:\([^)]*\))?\s*)*"
    r"(?:public\s+|internal\s+|private\s+)?"
    r"(?:inline\s+|suspend\s+|operator\s+)*"
    r"(?:val|var|fun)\s+"
    r"(?:<[^>]+>\s+)?"
    r"(?:[\w.]+(?:<[^>]*>)?\.)?"
    r"(\w+)",
    re.MULTILINE,
)

# Strings and comments are stripped before looking for references, so a name quoted in prose
# does not read as a use - the trap two scripts in this project have already tripped over.
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"//[^\n]*")
STRING = re.compile(r'"""(?:.|\n)*?"""|"(?:\\.|[^"\\\n])*"')


def sources() -> list[Path]:
    return [
        path
        for path in sorted(ROOT.rglob("*.kt"))
        if not SKIP_PARTS & set(path.relative_to(ROOT).parts)
    ]


def keep_interpolations(match: re.Match[str]) -> str:
    """Replace a string literal with only the `${...}` expressions inside it.

    ⚠ **The whole reason this check exists lived inside a template.** `DiagnosticStateReporter`
    writes `"manage=${yesNo(userData.overlayManageable)}"`, and a checker that strips strings
    wholesale reads that file as never mentioning the name at all - which is precisely how the
    missing import reached a zip. `check12_unusedimports` has the mirror-image bug and lists it
    as a known false positive; this one must not inherit it.
    """
    return " ".join(re.findall(r"\$\{(.*?)\}", match.group(0), re.DOTALL)) or '""'


def strip(text: str) -> str:
    text = BLOCK_COMMENT.sub(" ", text)
    text = LINE_COMMENT.sub(" ", text)

    return STRING.sub(keep_interpolations, text)


def main() -> int:
    files = sources()
    packages: dict[Path, str] = {}
    declared: dict[str, set[str]] = {}

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = PACKAGE.search(text)

        if not match:
            continue

        package = match.group(1)
        packages[path] = package

        for name in DECL.findall(strip(text)):
            declared.setdefault(name, set()).add(package)

    # Only names with exactly one home can be judged; anything ambiguous is left alone.
    homes = {name: next(iter(pkgs)) for name, pkgs in declared.items() if len(pkgs) == 1}

    problems: list[str] = []

    for path in files:
        package = packages.get(path)

        if package is None:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")
        body = strip(text)
        imports = set(IMPORT.findall(text))
        stars = {imp[:-2] for imp in imports if imp.endswith(".*")}

        for name, home in homes.items():
            if home == package or home in stars:
                continue

            if f"{home}.{name}" in imports:
                continue

            # A qualified use carries its own package and needs no import.
            if re.search(rf"\b{re.escape(name)}\b", body) is None:
                continue

            used = (
                re.search(rf"\.{re.escape(name)}\b", body)
                or re.search(rf"(?<![\w.]){re.escape(name)}\s*\(", body)
                or re.search(rf"(?<![\w.]){re.escape(name)}\s*=", body)
            )

            if used is None:
                continue

            line = body[: used.start()].count("\n") + 1

            problems.append(
                f"  {path.relative_to(ROOT)}:{line}  {name}  "
                f"(declared in {home})",
            )

    print(f"checked {len(files)} Kotlin file(s) against {len(homes)} top-level name(s)")

    for problem in problems:
        print(problem)

    print(f"{len(problems)} cross-package reference(s) with no import")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
