#!/usr/bin/env python3
"""v3-r4o — check_local_scope stops reading function-type parameter names as declarations.

r4o's Shizuku setup page gave `SetupScreen` a callback whose type names its own arguments:

    onSaveShizuku: (
        forkMode: ShizukuForkMode,
        packageName: String,
        startAction: String,
        authKey: String,
    ) -> Unit,

and the checker immediately reported two violations that are not violations:

    SetupScreen.kt:728  packageName  used in openNotificationSettings, declared on SetupScreen
    SetupScreen.kt:731  packageName  used in openNotificationSettings, declared on SetupScreen

`openNotificationSettings` is `private fun Context.openNotificationSettings()`, and the
`packageName` it reads is **`Context.packageName`** — a receiver property that has nothing to do
with `SetupScreen`. What went wrong is in `parameters()`:

    names = re.findall(r"(?:^|,)\\s*...(\\w+)\\s*:", inside)

`inside` is the whole parameter list including nested parentheses, so every name inside a
**function type** was collected as a parameter of the enclosing function.

⚠ **Names in a function type declare nothing in Kotlin.** `(name: String) -> Unit` is
documentation: the name is not in scope anywhere, and a lambda passed for it may call its
argument something else entirely. So dropping them is not a relaxation — it is the extractor
becoming correct.

## ⚠ The fix is to the checker, not to the code that tripped it

Renaming the callback's arguments would have made the report go away and left the defect in
place, ready for the next Compose function with a named callback — and this project's rule for a
first-draft refusal is to fix the assertion, not weaken it. This is the fifth false-positive
class the checker has been taught, after named arguments, nested `fun`s, multi-name lambdas and
overrides.

## Measured three ways, as handover_6 §4.1 requires

The script runs the checker itself before writing anything:

* **0 on the pristine tree** — proves the change reports nothing new;
* **0 on the working tree** — the two false positives are gone;
* **exactly the expected line on a tree with a real violation reintroduced** — proves it can
  still see one. A checker that has only ever printed zero has not been tested.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKER = "tools/check_local_scope.py"

PRISTINE = Path("/root/work/r4m1-pristine")

OLD = '''    inside = text[open_paren + 1: i]
    names = re.findall(r"(?:^|,)\\s*(?:@\\w+(?:\\([^)]*\\))?\\s*)*(?:vararg\\s+)?(\\w+)\\s*:", inside)

    return names, i'''

NEW = '''    inside = text[open_paren + 1: i]

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
    match = re.match(r"\\s*(?:@\\w+(?:\\([^)]*\\))?\\s*)*(?:vararg\\s+)?(\\w+)\\s*:", piece)

    return [match.group(1)] if match else []'''

# A real violation, reintroduced to prove the checker still sees one. Modelled on the r4b bug
# the checker was written for: a value declared in one function and read in another.
CANARY_FILE = "tools/_scope_canary.kt"

CANARY = """package com.android.geto.canary

fun outer(isShevery: Boolean) {
    println(isShevery)
}

fun inner() {
    println(isShevery)
}
"""


def run(tree: Path) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, str(ROOT / CHECKER), str(tree)],
        capture_output=True,
        text=True,
    )

    return result.returncode, result.stdout + result.stderr


def main() -> int:
    path = ROOT / CHECKER

    if not path.is_file():
        print(f"REFUSED: missing {CHECKER}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {CHECKER}\n  the extractor matched {found} time(s), expected exactly 1")
        return 1

    staged = text.replace(OLD, NEW, 1)

    # Written to a scratch copy first, so all three measurements are taken before the tree is
    # touched at all.
    with tempfile.TemporaryDirectory() as tmp:
        scratch = Path(tmp) / "check_local_scope.py"

        scratch.write_text(staged, encoding="utf-8")

        original = path.read_text(encoding="utf-8")

        path.write_text(staged, encoding="utf-8")

        try:
            # 1. The working tree, which is what has the two false positives today.
            code, out = run(ROOT)

            if "0 identifier" not in out:
                path.write_text(original, encoding="utf-8")

                print(f"REFUSED: the fixed checker still reports on the working tree:\n{out}")
                return 1

            # 2. The pristine tree, so the change cannot have started reporting something new.
            if PRISTINE.is_dir():
                code, out = run(PRISTINE)

                if "0 identifier" not in out:
                    path.write_text(original, encoding="utf-8")

                    print(f"REFUSED: the fixed checker reports on the pristine tree:\n{out}")
                    return 1
            else:
                print(f"  note      {PRISTINE} is absent; the pristine measurement was skipped")

            # 3. ⚠ **And a tree with a real violation in it.** A checker that has only ever
            #    printed zero has not been tested — handover_6 §4.1.
            canary = ROOT / CANARY_FILE

            canary.write_text(CANARY, encoding="utf-8")

            try:
                code, out = run(ROOT)
            finally:
                canary.unlink()

            if "isShevery" not in out:
                path.write_text(original, encoding="utf-8")

                print(f"REFUSED: the fixed checker cannot see a real violation:\n{out}")
                return 1

            if "1 identifier" not in out:
                print(f"REFUSED: the canary produced an unexpected count:\n{out}")
                return 1

        except BaseException:
            path.write_text(original, encoding="utf-8")

            raise

    print(f"  ok        {CHECKER}  :: function-type parameter names are not declarations")
    print("  ok        0 on the working tree")
    print("  ok        0 on the pristine tree")
    print("  ok        exactly 1 on a tree with the bug reintroduced")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
