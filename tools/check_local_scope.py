#!/usr/bin/env python3
"""A parameter threaded halfway: used in one function, declared on another in the same file.

⚠ **Born from r4b, the second zip in a row that reached the author without compiling.**
`isShevery` was added to `AndroidSettingsManagerDialog` and then read inside `TargetRow`, a
separate private composable in the same file. Nothing in the suite could see it: `feature/apps`
is not one of the five modules the sandbox really compiles, `check_symbol_imports` asks about
**cross-package** names rather than local scope, and `check9_arity` counts arguments at a call
site rather than identifiers in a body.

⚠ **Widened in r4e after a second one got through**, of the same family but not the same shape:
`sheveryStartTracker.begin(job = job, …)` was appended to the end of the wrong function, and the
`val job` it names is declared two functions away. So the question is now asked of locals as well
as parameters:

    is this identifier a parameter or a local of some *other* function in this file,
    and nothing at all in the scope where it is used?

Anything with a plausible local origin is left alone: a parameter or local of the enclosing
function, a lambda parameter, a nested function's parameters, **the locals of any function this
one is written inside** (a nested helper closes over its host), a top-level or class-level
declaration, a primary-constructor property, or an import. What survives all of that is nearly
always the bug.

### Reading it

Zero on a healthy tree. Each report names the file, the line, the identifier, the function it is
used in and the function that actually declares it:

    AndroidSettingsManagerDialog.kt:672  isShevery  used in TargetRow, declared on
    AndroidSettingsManagerDialog

⚠ **Not a diff check.** It needs no baseline and can be run on any build.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

SKIP_PARTS = {"build", "out", ".git", "design"}

BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT = re.compile(r"//[^\n]*")
STRING = re.compile(r'"""(?:.|\n)*?"""|"(?:\\.|[^"\\\n])*"')

FUN = re.compile(r"^(\s*)(?:@\w+(?:\([^)]*\))?\s*)*"
                 r"(?:public\s+|internal\s+|private\s+|protected\s+)?"
                 r"((?:inline\s+|suspend\s+|operator\s+|override\s+|tailrec\s+)*)"
                 r"fun\s+(?:<[^>]+>\s+)?(?:[\w.]+(?:<[^>]*>)?\.)?(\w+)\s*\(",
                 re.MULTILINE)

# Anything that introduces a name in a body: locals, destructuring, for loops, and catch
# clauses. Lambda parameter lists are handled by LAMBDA, which keeps all of them rather than
# only the first.
LOCAL = re.compile(r"\b(?:val|var)\s+(\w+)|\bfor\s*\(\s*(\w+)|\bcatch\s*\(\s*(\w+)")

# `{ hidden, busy, work -> …}` and `{ (key, value) -> …}`.
#
# ⚠ **Anchored to the opening brace.** A bare `…->` matches every arm of every `when` in the
# file, and a `when` arm swallows whatever identifier happens to sit in front of it - which is
# how an earlier draft of this check quietly stopped seeing the very bug it was written for.
# Only a parameter list at the head of a lambda binds names.
LAMBDA_NAME = r"[a-z_]\w*(?:\s*:\s*[\w.<>?\[\]]+)?"
LAMBDA = re.compile(r"\{\s*\(?\s*(" + LAMBDA_NAME + r"(?:\s*,\s*" + LAMBDA_NAME + r")*)\s*\)?\s*->")
LAMBDA_BINDS = re.compile(r"(?:^|,)\s*([a-z_]\w*)")

DECL_ANY = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*"
                      r"(?:public\s+|internal\s+|private\s+|protected\s+)?"
                      r"(?:const\s+|lateinit\s+|open\s+|override\s+|abstract\s+)*"
                      r"(?:val|var|fun|class|object|interface|enum|typealias)\s+"
                      r"(?:<[^>]+>\s+)?(?:[\w.]+(?:<[^>]*>)?\.)?(\w+)",
                      re.MULTILINE)

IMPORT = re.compile(r"^import\s+[\w.]*?(\w+)(?:\s+as\s+(\w+))?\s*$", re.MULTILINE)

# `class Checks(private val context: Context)` — a primary-constructor `val` is a property of
# the class, in scope in every member, and `DECL_ANY` cannot see it because it is mid-line.
CLASS = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*"
                   r"(?:public\s+|internal\s+|private\s+|protected\s+)?"
                   r"(?:data\s+|value\s+|sealed\s+|abstract\s+|open\s+|inner\s+|enum\s+)*"
                   r"(?:class|object|interface)\s+(\w+)",
                   re.MULTILINE)

CONSTRUCTOR_PROPERTY = re.compile(r"\b(?:val|var)\s+(\w+)")

USE = re.compile(r"(?<![\w.@$])([a-z]\w*)\b")

# `foo(bar = …)` and `foo(x, bar = …)`: the name on the left of a named argument is the callee's
# parameter, not a reference to anything in this scope. Kotlin's `==`, `>=`, `!=` and friends are
# excluded by the lookahead so a real comparison still counts as a use.
NAMED_ARG = re.compile(r"[(,]\s*$")
ASSIGN_AHEAD = re.compile(r"\s*=(?!=)")


def strip(text: str) -> str:
    """Comments and string literals out, `${…}` expressions kept."""
    text = BLOCK_COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    text = LINE_COMMENT.sub("", text)

    return STRING.sub(
        lambda m: " ".join(re.findall(r"\$\{(.*?)\}", m.group(0), re.DOTALL))
        + "\n" * m.group(0).count("\n"),
        text,
    )


def parameters(text: str, open_paren: int) -> tuple[list[str], int]:
    """Names in the parameter list starting at open_paren, and the index just past it."""
    depth, i = 0, open_paren

    # ⚠ **Parentheses and brackets only.** Counting `<` and `>` as a pair looks right until a
    # parameter is a lambda: the `>` of `() -> Unit` closes a bracket that was never opened, the
    # scan stops in the middle of the list, and every function with a callback parameter comes
    # back with an empty body. Generic commas cannot be mistaken for parameters anyway - the
    # name pattern below wants `name:`, and `Pair<Int, Int?>` offers nothing of the sort.
    while i < len(text):
        if text[i] in "([":
            depth += 1
        elif text[i] in ")]":
            depth -= 1

            if depth == 0:
                break

        i += 1

    inside = text[open_paren + 1: i]

    # ⚠ **Top level only.** A parameter whose type is a function type names its own arguments -
    # `onSave: (forkMode: ShizukuForkMode, packageName: String) -> Unit` - and those names
    # declare nothing: they are documentation, and a lambda passed for it may call them anything.
    # Reading them as parameters of the enclosing function made `packageName` look like a local
    # of a Compose function, and every unrelated `Context.packageName` below it a violation.
    #
    # Split on commas at depth zero, then take the leading `name:` of each piece.
    # ⚠ **Parentheses and brackets only — the same rule as the scan above, for the same
    # reason.** The first draft of this counted `<` and `>` too, and the `>` of `() -> Unit`
    # closed a bracket that was never opened: depth went negative, every following comma
    # stopped being top level, and forty-two functions lost their parameter lists. The warning
    # was three lines further up.
    names, depth, piece = [], 0, []

    for ch in inside:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1

        if ch == "," and depth == 0:
            names.extend(_parameter_name("".join(piece)))

            piece = []
        else:
            piece.append(ch)

    names.extend(_parameter_name("".join(piece)))

    return names, i


def _parameter_name(piece: str) -> list[str]:
    """The declared name of one parameter, or nothing when the piece declares none."""
    match = re.match(r"\s*(?:@\w+(?:\([^)]*\))?\s*)*(?:vararg\s+)?(\w+)\s*:", piece)

    return [match.group(1)] if match else []


def body(text: str, after_params: int) -> tuple[str, int]:
    """The braced body following a signature, and where in `text` it begins.

    Empty for expression bodies. The offset is what turns a position inside the body into a real
    line number: counting from the start of the *signature* instead loses the parameter list,
    which on a Compose function is a dozen lines and puts every report in the wrong place.
    """
    i = after_params

    while i < len(text) and text[i] not in "{\n":
        if text[i] == "=":
            return "", i

        i += 1

    if i >= len(text) or text[i] != "{":
        return "", i

    depth, start = 0, i

    while i < len(text):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1

            if depth == 0:
                return text[start + 1: i], start + 1

        i += 1

    return text[start + 1:], start + 1


def main() -> int:
    files = [
        path
        for path in sorted(ROOT.rglob("*.kt"))
        if not SKIP_PARTS & set(path.relative_to(ROOT).parts)
    ]

    problems: list[str] = []

    for path in files:
        raw = path.read_text(encoding="utf-8", errors="replace")
        text = strip(raw)

        functions: list[tuple[str, list[str], str, int, bool]] = []

        for match in FUN.finditer(text):
            params, close = parameters(text, match.end() - 1)
            fun_body, at = body(text, close + 1)
            functions.append((
                match.group(3), params, fun_body, at,
                "override" in match.group(2),
            ))

        # ⚠ **A declaration inside a function body is not a file-level name.** `DECL_ANY` begins
        # `^\s*`, so it matched every local `val` in the file as well as the class's own
        # properties — which meant every local was in scope everywhere, and the whole
        # locals-as-owners rule below had no effect at all. Ranges rather than an indentation
        # test, so a local inside a *top-level* function is excluded too.
        spans = [(at, at + len(fun_body)) for _, _, fun_body, at, _ in functions if fun_body]

        file_names = {
            match.group(1)
            for match in DECL_ANY.finditer(text)
            if not any(start <= match.start() < end for start, end in spans)
        }

        for match in IMPORT.finditer(raw):
            file_names.add(match.group(2) or match.group(1))

        # Primary-constructor properties. In scope in every member of their class, and mid-line,
        # so neither DECL_ANY nor the enclosure rule above can reach them.
        for match in CLASS.finditer(text):
            head = text.find("(", match.end())
            line_end = text.find("\n", match.end())

            if head < 0 or (0 <= line_end < head):
                continue

            _, close = parameters(text, head)

            file_names.update(CONSTRUCTOR_PROPERTY.findall(text[head:close]))

        owners: dict[str, str] = {}

        for name, params, _, _, overridden in functions:
            # ⚠ **An override's parameter names are the platform's, not the author's.** A class
            # that overrides `onNewIntent(intent)` and elsewhere reads the inherited `intent`
            # property is not threading anything halfway; it is two things the framework named
            # the same. Only names someone here chose can be threaded, so only those can be
            # dropped on the way down.
            if overridden:
                continue

            for param in params:
                owners.setdefault(param, name)

        # ⚠ **Locals count as owners too, not just parameters.** r4d shipped a block appended to
        # the wrong function — `sheveryStartTracker.begin(job = job, …)` landed at the end of
        # `hideSettings()`, where the `val job` it names is declared two functions away. A check
        # that only knew about parameters could not see it.
        #
        # Registered second, so a parameter wins the name: a parameter is the stronger claim,
        # and it is the one the report should name when a file has both.
        for name, _, fun_body, _, overridden in functions:
            if overridden or not fun_body:
                continue

            for group in LOCAL.findall(fun_body):
                for part in group:
                    if part:
                        owners.setdefault(part, name)

        binds: list[set[str]] = []

        for _, params, fun_body, _, _ in functions:
            names = set(params)

            for group in LOCAL.findall(fun_body):
                names.update(part for part in group if part)

            for head in LAMBDA.findall(fun_body):
                names.update(LAMBDA_BINDS.findall(head))

            # A local `fun` declared inside this body brings its own parameters, and its body is
            # read as part of this one. Without this every local helper's parameters look like
            # names borrowed from a sibling function.
            for nested in FUN.finditer(fun_body):
                nested_params, _ = parameters(fun_body, nested.end() - 1)
                names.update(nested_params)

            binds.append(names)

        for index, (name, _, fun_body, at, overridden) in enumerate(functions):
            # ⚠ **An override sees what it inherits, and this check cannot.** `onCreate` reads
            # `intent` off the Activity it extends; nothing in the file declares it. Reading a
            # supertype it has never opened is out of reach here, so an override's body is not
            # somewhere this check can speak with any confidence.
            if not fun_body or overridden:
                continue

            local = {"it", "this"} | file_names | binds[index]

            # ⚠ **A nested function closes over the one it is written inside.** `refresh()`
            # declared in the middle of a composable reads that composable's `val context`
            # perfectly legally, and treating the two as peers reported sixteen of those on an
            # untouched tree. Enclosure is decided by span containment rather than by
            # indentation, so it holds for a helper nested three deep.
            for other, (_, _, other_body, other_at, _) in enumerate(functions):
                if other == index or not other_body:
                    continue

                if other_at <= at and at + len(fun_body) <= other_at + len(other_body):
                    local |= binds[other]

            for use in USE.finditer(fun_body):
                used = use.group(1)

                if used in local or used not in owners or owners[used] == name:
                    continue

                # A named argument names the *callee's* parameter. `userData(forkMode = …)` says
                # nothing about what is in scope here, and the host tests are full of them.
                if (NAMED_ARG.search(fun_body[: use.start()])
                        and ASSIGN_AHEAD.match(fun_body[use.end():])):
                    continue

                line = text[: at + use.start()].count("\n") + 1

                problems.append(
                    f"  {path.relative_to(ROOT)}:{line}  {used}  "
                    f"used in {name}, declared on {owners[used]}",
                )

    print(f"checked {len(files)} Kotlin file(s)")

    for problem in problems:
        print(problem)

    print(f"{len(problems)} identifier(s) used outside the function that declares them")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
