#!/usr/bin/env python3
"""
r25a — one token, to remove a smart-cast the compiler does not have to grant.

r25's self-arming handler reads:

    onCheckedChange = if (enabled && onCheckedChange != null) {
        { want -> …; onCheckedChange(want) }
    } else { null }

which relies on Kotlin smart-casting a nullable function-typed **parameter** to non-null across a
lambda boundary and then invoking it. Parameters are stable vals and this does compile — but it is
the kind of thing that is true until a language version or an inference detail says otherwise, and
the author builds this once per round on a machine I cannot see. `?.invoke` asks for nothing and
costs nothing.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TOGGLES = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/GetoToggles.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


toggles = TOGGLES.read_text(encoding="utf-8")

OLD = """        onCheckedChange = if (enabled && onCheckedChange != null) {
            { want ->
                if (want) awaiting = true

                onCheckedChange(want)
            }
        } else {
            null
        },"""

NEW = """        onCheckedChange = if (enabled && onCheckedChange != null) {
            { want ->
                if (want) awaiting = true

                // `?.invoke` rather than a smart cast: the null check above is a few lines and a
                // lambda boundary away, and this asks the compiler for nothing.
                onCheckedChange?.invoke(want)
            }
        } else {
            null
        },"""

found = toggles.count(OLD)

if check(found == 1, f"toggles: the handler was found {found}x, expected 1"):
    toggles = toggles.replace(OLD, NEW, 1)

check(
    toggles.count("onCheckedChange?.invoke(want)") == 1,
    "toggles: expected exactly one invocation through the handler",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

TOGGLES.write_text(toggles, encoding="utf-8")

print(f"wrote {TOGGLES.relative_to(ROOT).as_posix()}")

print("ok")
