#!/usr/bin/env python3
"""r4a — the three missing imports that made r4 fail in Android Studio, and the check for them.

The author's build:

    e: DiagnosticStateReporter.kt:213:42 Unresolved reference 'overlayManageable'.

⚠ **Third instance of the same class of bug in one round, and the first to reach a zip.** r4
added four top-level declarations to `:domain:model` and referenced them from six other modules.
Two missing imports were caught by the domain compile; this one was not, because the sandbox
compiles only the five pure-JVM domain modules and `broadcast-receiver` is not one of them.
23 audits, 409 host assertions and a byte-identical round-trip all passed a tree that does not
build.

**Why the existing checks all missed it.** `check3_imports` asks whether the imports that *are*
written resolve. `check12` finds imports with no use — the mirror image. `check18` covers
`internal` top-level *functions*. And `check_new_types.py`, written for exactly this shape of
failure in r2b, collects **capitalised** names only, so a lowercase extension property goes
straight past it.

`tools/check_symbol_imports.py` is the missing half, added with this fix: it collects every
top-level `val`/`var`/`fun` in the repo with its package — extension receivers included, since
`val UserData.overlayManageable` is written `userData.overlayManageable` at the call site — and
reports any cross-package reference with no import. Zero noise floor on the r3 tree.

⚠ **It must not strip string templates**, and that is not a detail: the reference the author's
build tripped over lives inside `"manage=${yesNo(userData.overlayManageable)}"`. A checker that
strips strings wholesale reads that file as never mentioning the name. `check12` has precisely
that blind spot and lists it as a known false positive.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REPORTER = ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/"
            "DiagnosticStateReporter.kt")
APP_SETTINGS_VM = ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
                   "AppSettingsViewModel.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (REPORTER, [
        (
            """import com.android.geto.domain.model.isShizukuConfigured
""",
            """import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.overlayManageable
""",
            1,
        ),
    ]),
    (APP_SETTINGS_VM, [
        (
            """import com.android.geto.domain.model.AppSettingsResult
""",
            """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.overlayManageable
""",
            1,
        ),
    ]),
    (MANAGER_VM, [
        (
            """import com.android.geto.domain.model.ManualRevertTarget
""",
            """import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.manageShizukuEffective
""",
            1,
        ),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")

            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )

                continue

            if new.strip().splitlines()[-1] in text:
                problems.append(f"{rel}: the import is already there")

                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    checker = ROOT / "tools/check_symbol_imports.py"

    if not checker.exists():
        problems.append(f"{checker.relative_to(ROOT)}: the check this fix comes with is missing")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    # The fix is only finished when the check that found it reports nothing.
    result = subprocess.run(
        [sys.executable, str(checker), str(ROOT)],
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout.strip())

    if result.returncode != 0:
        print("⚠ the check still reports problems — the fix is incomplete")

        return 1

    print("ok - three imports in, and check_symbol_imports reports a clean tree")

    return 0


if __name__ == "__main__":
    sys.exit(main())
