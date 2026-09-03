#!/usr/bin/env python3
"""v3-r4x — `:domain:common` gets the coroutines dependency `IconStyleState` needs.

The second build error, and the one the sandbox's domain compile could not see: it passes the
coroutines jar on the classpath by hand, so a module whose *Gradle* file never asked for it still
compiles there and fails on the author's machine.

Before r4w, **not one file in `:domain:common` imported `kotlinx.coroutines`** — the dispatcher
file declares a qualifier annotation and an enum, and `Diagnostics` and `PriorHide` import nothing
at all. So the module's build file has only `kotlin("stdlib")` from the convention plugin and
`javax.inject`. `IconStyleState`'s `MutableStateFlow` is `Unresolved reference: kotlinx`.

⚠ **`api`, not `implementation`, and the difference matters here.** `IconStyleState.revision` is a
`StateFlow` in this module's *public* signature, and two other modules collect it. Under
`implementation` the type would not be on their compile classpath and every one of them would fail
instead. `:domain:framework` and `:domain:repository` use `implementation` because their coroutine
types are internal to what they expose through their own interfaces; this one is not.

⚠ **`check4_deps` passed and could not have caught it**, and no check is added for it, which is
a deliberate limit rather than an oversight. It reads what modules *declare*; whether a
`kotlinx.coroutines` import resolves depends on what an external artifact propagates through its
own POM — every Android module here gets coroutines that way, through Hilt and the lifecycle
libraries, and none of them declares it. A checker that flagged those seventeen modules would
report sixteen false alarms to catch this one. The rule that would have caught it is smaller and
belongs in a reviewer's head: **a JVM module in `domain/` declares every library it imports**, and
the three beside this one already do.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUILD = "domain/common/build.gradle.kts"

STATE = "domain/common/src/main/kotlin/com/android/geto/domain/common/IconStyleState.kt"

OLD = """dependencies {
    api(libs.javax.inject)
}"""

NEW = """dependencies {
    api(libs.javax.inject)

    // ⚠ **api, not implementation.** `IconStyleState.revision` is a StateFlow in this module's
    // public signature and two other modules collect it; under `implementation` the type would
    // not be on their compile classpath and each of them would fail instead. The sibling domain
    // modules use `implementation` because their coroutine types stay behind their own
    // interfaces — this one does not.
    api(libs.kotlinx.coroutines.core)
}"""


def main() -> int:
    path = ROOT / BUILD

    if not path.is_file():
        print(f"REFUSED: missing {BUILD}")
        return 1

    text = path.read_text(encoding="utf-8")

    found = text.count(OLD)

    if found != 1:
        print(f"REFUSED: {BUILD}\n  the dependencies block matched {found} time(s), expected 1")
        return 1

    # ⚠ The alias has to exist in the catalog, or this is a different build error in the same
    # place. Read out of the file rather than assumed from the three modules that use it.
    catalog = (ROOT / "gradle/libs.versions.toml").read_text(encoding="utf-8")

    if "kotlinx-coroutines-core = {" not in catalog:
        print("REFUSED: gradle/libs.versions.toml\n  no kotlinx-coroutines-core alias")
        return 1

    # And the module really does need it now.
    state = (ROOT / STATE).read_text(encoding="utf-8")

    if "import kotlinx.coroutines.flow." not in state:
        print(f"REFUSED: {STATE}\n  nothing here imports coroutines; this dependency is unearned")
        return 1

    text = text.replace(OLD, NEW, 1)

    if text.count("api(libs.kotlinx.coroutines.core)") != 1:
        print(f"REFUSED: {BUILD}\n  the dependency was not added exactly once")
        return 1

    path.write_text(text, encoding="utf-8")

    # Printed as a sweep, and **informational only**: every Android module here imports
    # coroutines and declares none, because Hilt and the lifecycle libraries propagate it through
    # their own POMs. The signal to look for in this list is a *JVM* module — one under domain/ —
    # which has no such supplier and must declare what it imports.
    pattern = re.compile(r"^import kotlinx\.coroutines", re.MULTILINE)

    for build in sorted(ROOT.rglob("build.gradle.kts")):
        module = build.parent

        if module == ROOT or "build-logic" in str(module):
            continue

        sources = list((module / "src/main").rglob("*.kt")) if (module / "src/main").is_dir() else []

        uses = any(pattern.search(f.read_text(encoding="utf-8")) for f in sources)

        declared = "kotlinx.coroutines" in build.read_text(encoding="utf-8")

        if uses and not declared:
            print(f"  note      {module.relative_to(ROOT)} imports coroutines and declares none")

    print(f"  ok        {BUILD}  :: api(kotlinx-coroutines-core)")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
