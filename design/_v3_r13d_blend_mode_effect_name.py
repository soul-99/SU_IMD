#!/usr/bin/env python3
"""
r13d — one wrong method name in the effect chain.

`android.graphics.RenderEffect`'s compositor is **`createBlendModeEffect(dst, src, blendMode)`**.
I wrote `createBlendModeRenderEffect`, which is the spelling of nothing: the family is
`createBitmapEffect`, `createBlendModeEffect`, `createBlurEffect`, `createChainEffect`,
`createColorFilterEffect`, `createOffsetEffect`, `createShaderEffect` — every one of them ends in
`…Effect`, and I typed the class name into the middle of one. The other three calls in the same
function used the right names and compiled, which is why only these two lines failed.

The argument order is unchanged and was already right: `dst` first, then `src`, then the mode —
`(blurred, mask, DST_IN)` keeps the blurred copy where the mask is opaque, and
`(identity, band, SRC_OVER)` lays that band over the untouched page.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BLUR = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/component/ProgressiveBlur.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


text = BLUR.read_text(encoding="utf-8")

WRONG = "AndroidRenderEffect.createBlendModeRenderEffect("

RIGHT = "AndroidRenderEffect.createBlendModeEffect("

found = text.count(WRONG)

if check(found == 2, f"createBlendModeRenderEffect found {found}x, expected 2"):
    text = text.replace(WRONG, RIGHT, 2)

check(text.count(RIGHT) == 2, "the corrected call does not appear twice")

# ⚠ Every other RenderEffect factory this file names, checked against the real API surface rather
# than against memory — the mistake above was a name, not a signature.
KNOWN = (
    "AndroidRenderEffect.createOffsetEffect(",
    "AndroidRenderEffect.createBlurEffect(",
    "AndroidRenderEffect.createShaderEffect(",
    "AndroidRenderEffect.createBlendModeEffect(",
)

for line in text.splitlines():
    stripped = line.strip()

    if not stripped.startswith("AndroidRenderEffect."):
        continue

    check(
        any(stripped.startswith(known) for known in KNOWN),
        f"unrecognised RenderEffect factory: {stripped}",
    )

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

BLUR.write_text(text, encoding="utf-8")

print(f"wrote {BLUR.relative_to(ROOT).as_posix()}")

print("ok")
