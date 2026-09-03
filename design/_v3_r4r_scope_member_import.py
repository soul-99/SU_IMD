#!/usr/bin/env python3
"""v3-r4r — the import that broke the build, and a check so it cannot happen again.

    SetupCompletePage.kt:35:43
      Cannot access 'val RowColumnParentData?.weight: Float': it is internal in file.

`Modifier.weight` is a member of `ColumnScope` and `RowScope`. Inside a `Column { }` it is in
scope already and needs no import - and the name *is* importable from the same package, where it
resolves to an internal `RowColumnParentData.weight` property that nothing outside the library
may touch. So the import did not fail to resolve; it resolved to the wrong thing.

⚠ **This is the first defect of this round the audits did not catch**, and it is worth writing
down why. `check12_unusedimports` saw a name that *was* used. `check_symbol_imports` looks for
references with no import, which is the mirror image. `check3_imports` checks that imports exist.
None of them asks whether an import should exist at all.

## The fix, and the check

The import is removed - `weight` was always in scope.

`check24_scope_imports` is new: it lists the layout-scope members that must never be imported and
reports any file that imports one. Short and explicit, like `check_module_reach`'s IMPLICIT list;
anything added to it is a decision rather than a hole that widens by itself.

⚠ **Measured on a tree with the bug present**, because a check that has only ever printed zero has
not been tested: it is run before the import is removed, must report exactly this file, and is run
again afterwards and must report nothing.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

CHECK = "/root/work/toolkit/audit/check24_scope_imports.py"

BAD = "import androidx.compose.foundation.layout.weight\n"

CHECK_TEXT = '''#!/usr/bin/env python3
"""Reports imports of names that are members of a Compose layout scope.

`Modifier.weight`, `Modifier.align` and their neighbours are members of `ColumnScope`, `RowScope`
and `BoxScope`. Inside the corresponding layout they are already in scope and need no import - and
the same names *are* importable from `androidx.compose.foundation.layout`, where they resolve to
internal properties of `RowColumnParentData` that nothing outside the library may access.

So the import does not fail to resolve. It resolves to the wrong thing, and the compiler says:

    Cannot access 'val RowColumnParentData?.weight: Float': it is internal in file.

⚠ **No other check in this suite asks this question.** check12_unusedimports sees a name that is
used; check_symbol_imports looks for references with *no* import, which is the mirror image;
check3_imports asks that imports exist. None of them asks whether an import should exist at all -
which is how one of these reached a build.

The list is short and explicit. Anything added to it is a decision, not a hole that widens by
itself.
"""
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(os.environ.get("GETO_ROOT", ".")).resolve()

# Members of ColumnScope, RowScope and BoxScope. Every one of them is in scope inside its own
# layout and must never be imported from the layout package.
SCOPE_MEMBERS = {
    "weight",
    "align",
    "alignBy",
    "alignByBaseline",
    "matchParentSize",
}

IMPORT = re.compile(r"^import\\s+androidx\\.compose\\.foundation\\.layout\\.(\\w+)\\s*$")


def main() -> int:
    problems = []

    for path in sorted(ROOT.rglob("*.kt")):
        if "/build/" in path.as_posix():
            continue

        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = IMPORT.match(line.strip())

            if match and match.group(1) in SCOPE_MEMBERS:
                problems.append(
                    f"  {path.relative_to(ROOT)}:{number}  imports {match.group(1)}, "
                    f"which is a layout-scope member",
                )

    for problem in problems:
        print(problem)

    print(f"{len(problems)} layout-scope member import(s)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
'''


def run() -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, CHECK],
        capture_output=True,
        text=True,
        env={**os.environ, "GETO_ROOT": str(ROOT)},
    )

    return result.returncode, result.stdout + result.stderr


import os  # noqa: E402  - used by run() above, kept beside it for readability


def main() -> int:
    page = ROOT / PAGE

    if not page.is_file():
        print(f"REFUSED: missing {PAGE}")
        return 1

    text = page.read_text(encoding="utf-8")

    if text.count(BAD) != 1:
        print(f"REFUSED: {PAGE}\\n  the bad import matched {text.count(BAD)} time(s), expected 1")
        return 1

    if "Modifier\\n                .weight(1f)" not in text and ".weight(1f)" not in text:
        print(f"REFUSED: {PAGE}\\n  nothing here uses weight; the import may not be the problem")
        return 1

    pathlib_check = Path(CHECK)

    pathlib_check.write_text(CHECK_TEXT, encoding="utf-8")

    # ⚠ With the bug still present: the check must see it.
    code, out = run()

    if "SetupCompletePage.kt" not in out or code == 0:
        pathlib_check.unlink()

        print(f"REFUSED: the new check does not see the import that broke the build:\\n{out}")
        return 1

    page.write_text(text.replace(BAD, "", 1), encoding="utf-8")

    # And with it gone: nothing at all.
    code, out = run()

    if code != 0:
        print(f"REFUSED: the tree still has a scope-member import:\\n{out}")
        return 1

    print(f"  ok        {PAGE}  :: the import removed; weight was always in scope")
    print(f"  ok        {CHECK}  :: new — seen with the bug present, silent with it gone")
    print("\\nwrote 2 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
