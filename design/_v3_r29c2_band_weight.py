#!/usr/bin/env python3
"""
r29c2 — the destructured stop weight inside `BandCache.brush` stops being called `strength`.

`check_local_scope` flagged it, and it is right to. `bandStops` returns `Pair<position, strength>`,
and while the gradient was built inside `progressiveEdgeBlur` the destructured `strength` simply
shadowed that function's `strength` parameter — same function, so the checker never saw it. r29c
moved the gradient into `BandCache.brush`, and now the same name is a *different* function's local
that happens to match a parameter of the one it came from, which is exactly the shape the checker
exists to catch.

Renamed rather than suppressed: `weight` is what the second half of a stop actually is — how much
of the treatment survives at that position — and the two meanings of "strength" in one file were
always going to be read wrong by somebody.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def code(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


blur = BLUR.read_text(encoding="utf-8")

# ⚠ Both lines together, and the read as well as the declaration. Renaming a value means finding
# every *read* of it — handover §8, which says this shipped a compile error twice.
blur = replace_once(
    blur,
    "                val (position, strength) = stops[index]\n"
    "\n"
    "                position to fade.copy(alpha = fade.alpha * strength * amount)\n",
    "                val (position, weight) = stops[index]\n"
    "\n"
    "                position to fade.copy(alpha = fade.alpha * weight * amount)\n",
    "blur: the destructured stop inside BandCache.brush",
)

body = code(blur)

check(
    body.count("val (position, weight) = stops[index]") == 1,
    "blur: the rename did not land",
)

check(
    body.count("fade.alpha * weight * amount") == 1,
    "blur: the read was not renamed with the declaration",
)

# ⚠ **Word boundaries, not `count`.** `strengthAt` — the quadratic ramp, a different identifier
# entirely — contains the needle three times over, which is handover §8's substring trap in one
# line. `strength` survives only as `progressiveEdgeBlur`'s own parameter and its two lambda calls.
occurrences = len(re.findall(r"\bstrength\b", body))

check(
    occurrences == 3,
    f"blur: 'strength' appears {occurrences}x in code, expected 3 (the parameter and two calls)",
)

check(
    len(re.findall(r"\bstrengthAt\b", body)) == 3,
    "blur: strengthAt was disturbed",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

BLUR.write_text(blur, encoding="utf-8")

print(f"wrote {BLUR.relative_to(ROOT).as_posix()}")

print("ok")
