#!/usr/bin/env python3
"""
v3-r4m-e — `/*` inside a KDoc, which opens a comment rather than sitting inside one.

`check21_syntax` reported:

    AppSettingsViewModel.kt:382:1: error: syntax error: Unclosed comment.

⚠ **Kotlin block comments NEST.** `_v3_blocked_settings_public.py` wrote the phrase
`` `feature/*` `` into a KDoc; the `/*` in it opened a nested comment, the block's own closing
`*/` closed that one, and the outer KDoc ran to the end of the file. Every declaration after it
disappeared into a comment.

This is the first time this project has written a glob inside a Kotlin comment - a grep across
the whole tree finds no other `feature/*` in a `.kt` file - which is why nothing had hit it
before. The phrase is reworded rather than escaped: prose does not need the glob.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)

OLD = """ * compile error in Android Studio and invisible here, because the sandbox cannot build
 * `feature/*`. `tools/check_exposed_internal.py` now asks the question instead."""

NEW = """ * compile error in Android Studio and invisible here, because the sandbox only really
 * compiles the five pure-JVM domain modules. `tools/check_exposed_internal.py` now asks the
 * question instead."""


def main() -> int:
    path = ROOT / VM

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: the anchor matched {original.count(OLD)} time(s), expected 1")
        return 1

    text = original.replace(OLD, NEW, 1)

    # ⚠ **The rule this exists for, asserted for the whole file.** Kotlin block comments nest,
    # so a `/*` anywhere inside a comment opens one. Checked across every comment in the file
    # rather than only the edited one, because the same phrase could be written again.
    comments = re.findall(r"/\*.*?\*/", text, re.DOTALL)

    for comment in comments:
        if "/*" in comment[2:]:
            snippet = comment[2:][comment[2:].index("/*") - 30:][:70].strip()

            print(f"REFUSED: a comment still opens a nested block comment near: {snippet!r}")
            return 1

    # Balanced overall: as many opens as closes, and the file does not end inside one.
    if text.count("/*") != text.count("*/"):
        print(
            f"REFUSED: {text.count('/*')} comment opens against "
            f"{text.count('*/')} closes"
        )
        return 1

    # The declarations that vanished into the runaway comment must be back at top level.
    for declaration in (
        "\ndata class BlockedAppSettings(",
        "\nprivate val GATED_KEYS = listOf(",
    ):
        if text.count(declaration) != 1:
            print(f"REFUSED: {declaration.strip()!r} is not declared exactly once")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {VM}")
    print("  ~ the glob is out of the KDoc; no comment opens a nested one")
    print("\nwrote 1 file, 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
