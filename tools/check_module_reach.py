#!/usr/bin/env python3
"""
Reports imports a round **introduces** that reach a module the importing module cannot see.

    python3 tools/check_module_reach.py /path/to/baseline

**Why this exists.** In r2b3 `PriorHideDialog` was written into `feature/apps`, beside the other
launch dialogs, and imported from `feature/app-settings`. That import cannot resolve: **`feature/
apps` depends on `feature/app-settings`**, so the dependency can never run the other way without
a cycle. The author's Gradle build was the first thing to say so:

    AppSettingsScreen.kt:72:33 Unresolved reference 'apps'

Nothing in the suite could have caught it:

* `check4_deps` reads the dependency **declarations**, not whether a new reference obeys them.
* `check23_crossmodule_visibility` is about `internal` leaking across modules, not reachability.
* `check_new_types` asks whether a name is **imported**, and this one was — from a module that is
  not on the classpath.
* The domain compile covers five pure modules; this was two feature modules.

**A diff, for the same reason `check_new_types` is one.** Only imports this round *adds* are
judged, so the noise floor on an unchanged tree is zero and the check says nothing until a round
writes a new cross-module reference.

**Reachability is declared dependencies plus [IMPLICIT].** Every module's `build.gradle.kts` is
read for `projects.foo.bar` entries. On top of that, the convention plugins in `build-logic` add
a handful of modules to every Android feature without any module naming them — `design-system`
and `ui` among them — and a check that did not know about those would report every use of
`DialogContainer` in the project. That list is short, stated, and the only place this check can
be wrong in the quiet direction.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Modules the convention plugins in build-logic put on every feature module's classpath, which
# therefore appear in no module's own dependency block. Short and explicit: anything added here
# is a decision, not a hole that widens by itself.
IMPLICIT = {
    "design-system",
    "ui",
    "domain/model",
    "domain/common",
}

IMPORT = re.compile(r"^import\s+([\w.]+)(?:\s+as\s+\w+)?\s*$", re.MULTILINE)

PACKAGE = re.compile(r"^package\s+([\w.]+)\s*$", re.MULTILINE)

# `projects.feature.appSettings` -> feature/app-settings
PROJECT_DEP = re.compile(r"projects\.((?:[a-zA-Z]+)(?:\.[a-zA-Z]+)*)")


def camel_to_path(reference: str) -> str:
    """`feature.appSettings` -> `feature/app-settings`, the Gradle accessor spelling reversed."""
    parts = []

    for part in reference.split("."):
        parts.append(re.sub(r"(?<!^)(?=[A-Z])", "-", part).lower())

    return "/".join(parts)


def module_of(path: Path, modules: list[str]) -> str | None:
    """The longest module path this file sits under."""
    relative = path.as_posix()

    best: str | None = None

    for module in modules:
        if relative.startswith(module + "/") and (best is None or len(module) > len(best)):
            best = module

    return best


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} /path/to/baseline", file=sys.stderr)

        return 2

    baseline = Path(sys.argv[1]).resolve()

    root = Path(__file__).resolve().parents[1]

    if not baseline.is_dir():
        print(f"{baseline} is not a directory", file=sys.stderr)

        return 2

    # Every module, by the directory holding its build file.
    modules = sorted(
        build.parent.relative_to(root).as_posix()
        for build in root.rglob("build.gradle.kts")
        if build.parent != root and "build-logic" not in build.parent.parts
    )

    # What each module declares it can see, plus what the convention plugins add.
    reachable: dict[str, set[str]] = {}

    for module in modules:
        text = (root / module / "build.gradle.kts").read_text(encoding="utf-8")

        declared = {camel_to_path(match) for match in PROJECT_DEP.findall(text)}

        reachable[module] = {d for d in declared if d in modules} | IMPLICIT | {module}

    # Which module owns each package.
    owner: dict[str, str] = {}

    for path in root.rglob("*.kt"):
        if "build" in path.relative_to(root).parts:
            continue

        match = PACKAGE.search(path.read_text(encoding="utf-8", errors="replace"))

        module = module_of(path.relative_to(root), modules)

        if match and module:
            owner[match.group(1)] = module

    problems: list[str] = []

    checked = 0

    for path in sorted(root.rglob("*.kt")):
        relative = path.relative_to(root)

        if "build" in relative.parts:
            continue

        module = module_of(relative, modules)

        if module is None:
            continue

        text = path.read_text(encoding="utf-8", errors="replace")

        old = baseline / relative

        before = (
            set(IMPORT.findall(old.read_text(encoding="utf-8", errors="replace")))
            if old.is_file()
            else set()
        )

        added = set(IMPORT.findall(text)) - before

        if not added:
            continue

        checked += 1

        for imported in sorted(added):
            if not imported.startswith("com.android.geto."):
                continue

            # Strip the trailing member until a known package is found — an import can name a
            # class, a top-level function or an aliased R.
            parts = imported.split(".")

            target: str | None = None

            while len(parts) > 2 and target is None:
                parts = parts[:-1]

                target = owner.get(".".join(parts))

            if target is None or target in reachable[module]:
                continue

            problems.append(
                f"{relative}: imports {imported}\n"
                f"      {module} cannot see {target}",
            )

    if problems:
        print(f"checked {checked} changed file(s); {len(problems)} problem(s)")

        for problem in problems:
            print(f"  {problem}")

        return 1

    print(f"checked {checked} file(s) with new imports; 0 unreachable")

    return 0


if __name__ == "__main__":
    sys.exit(main())
