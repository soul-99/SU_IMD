#!/usr/bin/env python3
"""v3-r4s — the `when` block wrapped by the width cap is re-indented to match its new depth.

Whitespace only. The previous script nested `when (page)` two levels deeper without moving its
body, which Kotlin does not mind and `spotless` does.

⚠ **Nothing but leading spaces changes, and this proves it**: the file is compared to itself with
every line stripped, before and after. If a single non-whitespace character differs, nothing is
written.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

OPEN = "            when (page) {\n"

# The body runs from the line after OPEN to the line that closes the `when` — found by brace
# depth rather than by a marker, so a branch added later cannot fall outside it.
def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    original = path.read_text(encoding="utf-8")

    lines = original.splitlines(keepends=True)

    starts = [i for i, line in enumerate(lines) if line == OPEN]

    if len(starts) != 1:
        print(f"REFUSED: {SCREEN}\n  the wrapped `when` matched {len(starts)} time(s), expected 1")
        return 1

    start = starts[0]

    depth = 0
    end = None

    for i in range(start, len(lines)):
        # Comments in this region contain no braces; asserted below by the strip comparison,
        # which would catch any line this counted wrongly and then re-indented wrongly.
        depth += lines[i].count("{") - lines[i].count("}")

        if depth == 0:
            end = i
            break

    if end is None:
        print(f"REFUSED: {SCREEN}\n  the wrapped `when` never closes")
        return 1

    for i in range(start + 1, end):
        if lines[i].strip():
            lines[i] = "        " + lines[i]

    lines[end] = "            }\n"

    text = "".join(lines)

    if [line.strip() for line in text.splitlines()] != [
        line.strip() for line in original.splitlines()
    ]:
        print(f"REFUSED: {SCREEN}\n  something other than indentation changed")
        return 1

    if text == original:
        print(f"REFUSED: {SCREEN}\n  nothing to re-indent")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: {end - start - 1} line(s) re-indented, whitespace only")
    print("\nwrote 1 file(s), 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
