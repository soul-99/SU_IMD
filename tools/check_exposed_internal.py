#!/usr/bin/env python3
"""A public declaration whose type names an `internal` type from the same module.

⚠ **Born from r4m, which shipped a zip that would not compile.** The round added

    internal data class BlockedAppSettings(...)

to `feature/app-settings` and then handed it out of a **public** property on a public ViewModel:

    val blockedAppSettings = userDataRepository.userData.map { ... }.stateIn(...)

Kotlin refuses that outright — *"'public' property exposes its 'internal' type argument
'BlockedAppSettings'"* — because a caller outside the module could reach the property and not the
type it returns. Android Studio said so in one line; the sandbox could not, because only the five
pure-JVM domain modules really compile here and this lives in `feature/*`.

**Why nothing else catches it.** `check23_crossmodule_visibility` asks the opposite question —
whether one module *references* another's `internal` name. `check_symbol_imports` and
`check_new_types` are about imports. `check21_syntax` parses and does not resolve. Nothing in the
suite looked at a declaration's own visibility against the visibility of the types in it.

### What it does

For each module (the directory holding `src/main`):

1. Collects the names of top-level types declared `internal` — `class`, `interface`, `object`,
   `enum class`, `data class`, `value class`, `sealed class`.
2. Walks every Kotlin file in that module and finds declarations that are **public** — a
   `val`, `var` or `fun` with no `private`, `internal` or `protected` modifier, that is not
   inside a type which is itself `internal` or `private`.
3. Reports one whose **declared or inferred-from-constructor type** names an internal type.

⚠ **Both halves are checked, because both fail.** An explicit `: StateFlow<Foo>` is the easy
case; the one that actually shipped had no type at all and inferred it from `BlockedAppSettings(`
inside the initialiser. So the initialiser of a public `val` with no declared type is read for a
constructor call to an internal type, which is precisely how `stateIn` acquired the argument.

⚠ **Local declarations are skipped.** Only column-0 and single-indent (class member)
declarations count; a `val` inside a function body cannot expose anything.

Not a diff check: it reads the tree as it stands and has a zero noise floor, so it can be run on
any build without a baseline.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SKIP_PARTS = {"build", "out", ".git", "design"}

# `internal` top-level types. The optional `data`/`value`/`sealed`/`abstract`/`open` words are
# what make this find the real declarations rather than only the plain ones.
INTERNAL_TYPE = re.compile(
    r"^internal\s+"
    r"(?:abstract\s+|open\s+|sealed\s+|data\s+|value\s+|annotation\s+)*"
    r"(?:class|interface|object|enum\s+class)\s+"
    r"(\w+)",
    re.MULTILINE,
)

# A type declared `internal` at *any* nesting is still internal, but a nested one cannot be named
# from outside its parent anyway - so only top level is collected, which is where the risk is.

# A declaration that is public: column 0 or one indent (a class member), no visibility modifier.
# ⚠ `override` is deliberately allowed through: an override of a public member is public.
PUBLIC_DECL = re.compile(
    r"^(?P<indent> {0,4})"
    r"(?!.*\b(?:private|internal|protected)\b)"
    r"(?:@\w+(?:\([^)]*\))?\s+)*"
    r"(?:override\s+|open\s+|abstract\s+|final\s+|inline\s+|suspend\s+|operator\s+)*"
    r"(?P<kind>val|var|fun)\s+"
    r"(?:<[^>]+>\s+)?"
    r"(?:[\w.]+(?:<[^>]*>)?\.)?"
    r"(?P<name>\w+)"
    r"(?P<rest>.*)$",
    re.MULTILINE,
)

# A type or a private type at top level, whose whole body is out of reach of the question.
CLOSED_TYPE = re.compile(
    r"^(?:internal|private)\s+"
    r"(?:abstract\s+|open\s+|sealed\s+|data\s+|value\s+|annotation\s+)*"
    r"(?:class|interface|object|enum\s+class)\s+\w+",
    re.MULTILINE,
)

# ⚠ **A top-level function's body is also at one indent.** Without this, every local `val` in
# every top-level `fun` - including every composable in the project - reads as a public class
# member. This is the same lesson check_local_scope learned about DECL_ANY: indentation does not
# distinguish a member from a local, spans do.
TOP_LEVEL_FUN = re.compile(
    r"^(?:@\w+(?:\([^)]*\))?\s*)*"
    r"(?:public\s+|internal\s+|private\s+)?"
    r"(?:inline\s+|suspend\s+|operator\s+)*"
    r"fun\s",
    re.MULTILINE,
)

LINE_COMMENT = re.compile(r"//.*?$", re.MULTILINE)
BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
STRING = re.compile(r'"(?:\\.|[^"\\])*"', re.DOTALL)


def strip_noise(text: str) -> str:
    """Comments and string literals removed, newlines preserved so line numbers survive."""
    def blank(match: re.Match[str]) -> str:
        return re.sub(r"[^\n]", " ", match.group(0))

    text = BLOCK_COMMENT.sub(blank, text)
    text = LINE_COMMENT.sub(blank, text)

    return STRING.sub(blank, text)


def module_of(path: Path) -> Path | None:
    """The directory holding `src/main`, which is what `internal` is scoped to."""
    for parent in path.parents:
        if (parent / "src" / "main").is_dir():
            return parent

    return None


def body_spans(text: str, pattern: re.Pattern[str]) -> list[tuple[int, int]]:
    """Character ranges of each match's braced body, or of the match itself when it has none."""
    spans: list[tuple[int, int]] = []

    for match in pattern.finditer(text):
        start = match.start()

        # Bounded to the declaration's own line, so a `fun x() = y` with a lambda further
        # down the file cannot claim everything after it.
        line_end = text.find("\n", match.end())

        brace = text.find("{", match.end())

        if brace == -1 or (line_end != -1 and brace > line_end and "=" in
                           text[match.end():line_end]):
            spans.append((start, line_end if line_end != -1 else len(text)))

            continue

        depth = 0

        for i in range(brace, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1

                if depth == 0:
                    spans.append((start, i))

                    break
        else:
            spans.append((start, len(text)))

    return spans


def main() -> int:
    files = [
        path for path in ROOT.rglob("*.kt")
        if not SKIP_PARTS & set(path.relative_to(ROOT).parts)
    ]

    # module -> the internal type names it declares
    internal_types: dict[Path, set[str]] = {}

    stripped: dict[Path, str] = {}

    for path in files:
        text = strip_noise(path.read_text(encoding="utf-8"))

        stripped[path] = text

        module = module_of(path)

        if module is None:
            continue

        names = set(INTERNAL_TYPE.findall(text))

        if names:
            internal_types.setdefault(module, set()).update(names)

    problems: list[str] = []

    for path in files:
        module = module_of(path)

        if module is None or not internal_types.get(module):
            continue

        names = internal_types[module]

        text = stripped[path]

        # Out of reach: the members of an internal or private type, and every local inside a
        # top-level function.
        closed = body_spans(text, CLOSED_TYPE) + body_spans(text, TOP_LEVEL_FUN)

        for match in PUBLIC_DECL.finditer(text):
            at = match.start()

            if any(lo <= at <= hi for lo, hi in closed):
                continue

            rest = match.group("rest")

            # The declared type, when there is one: everything after the first `:` that is not
            # inside the parameter list, up to an `=` or the end of the line.
            after_params = re.sub(r"^\([^)]*\)", "", rest.strip())

            declared = ""

            if after_params.startswith(":"):
                declared = after_params[1:].split("=", 1)[0]

            # ⚠ **And the inferred case, which is the one that shipped.** A public `val` with no
            # declared type infers it from the initialiser, so a constructor call to an internal
            # type in the tail of the declaration exposes it just the same.
            initialiser = ""

            if not declared and "=" in rest:
                end = text.find("\n\n", at)

                initialiser = text[at:end if end != -1 else len(text)]

            hit = next(
                (
                    name for name in sorted(names)
                    if re.search(rf"\b{name}\b", declared)
                    or re.search(rf"\b{name}\s*\(", initialiser)
                ),
                None,
            )

            if hit is None:
                continue

            line = text.count("\n", 0, at) + 1

            problems.append(
                f"  {path.relative_to(ROOT)}:{line}  public {match.group('kind')} "
                f"'{match.group('name')}' exposes internal '{hit}'"
            )

    print(f"checked {len(files)} Kotlin file(s) in "
          f"{len(internal_types)} module(s) declaring internal types")

    for problem in problems:
        print(problem)

    print(f"{len(problems)} public declaration(s) exposing an internal type")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
