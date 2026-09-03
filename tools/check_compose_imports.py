#!/usr/bin/env python3
"""
Compose symbols used without their import.

⚠ **Why this exists.** Nothing in this toolkit compiles the Android modules - `check3_imports`
resolves only the app's *own* top-level names, and `check12_unusedimports` reports the opposite
problem. A Compose extension modifier such as `Modifier.padding` is an ordinary imported function,
so leaving its import out is not a typo the eye catches in a diff; it is a compile error found by
Android Studio one file at a time. r11 shipped exactly that: `AppsScreen` lost its `Column` and
gained a `Modifier.padding` in the same edit, and nothing here noticed.

⚠ **Deliberately shallow.** It knows a fixed table of symbols and the one import each needs. It
does not parse Kotlin, does not resolve scopes, and does not know about star imports. That makes it
capable of a false positive - a local function named `padding`, say - and each finding is meant to
be read rather than obeyed. What it cannot do is miss the case it exists for.

⚠ **Scope-member modifiers are absent from the table on purpose.** `Modifier.weight`, `align`,
`matchParentSize` and `alignByBaseline` are members of `RowScope`, `ColumnScope` or `BoxScope`;
they need no import, and listing them would report every well-formed file in the repository.

Exit status is the number of files with findings.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAYOUT = "androidx.compose.foundation.layout"

FOUNDATION = "androidx.compose.foundation"

UI = "androidx.compose.ui"

# token (as it appears in source) -> the import it needs
MODIFIERS = {
    ".padding(": f"{LAYOUT}.padding",
    ".fillMaxSize(": f"{LAYOUT}.fillMaxSize",
    ".fillMaxWidth(": f"{LAYOUT}.fillMaxWidth",
    ".fillMaxHeight(": f"{LAYOUT}.fillMaxHeight",
    ".heightIn(": f"{LAYOUT}.heightIn",
    ".widthIn(": f"{LAYOUT}.widthIn",
    ".sizeIn(": f"{LAYOUT}.sizeIn",
    ".offset(": f"{LAYOUT}.offset",
    ".navigationBarsPadding(": f"{LAYOUT}.navigationBarsPadding",
    ".systemBarsPadding(": f"{LAYOUT}.systemBarsPadding",
    ".statusBarsPadding(": f"{LAYOUT}.statusBarsPadding",
    ".imePadding(": f"{LAYOUT}.imePadding",
    ".consumeWindowInsets(": f"{LAYOUT}.consumeWindowInsets",
    ".windowInsetsPadding(": f"{LAYOUT}.windowInsetsPadding",
    ".background(": f"{FOUNDATION}.background",
    ".border(": f"{FOUNDATION}.border",
    ".clickable(": f"{FOUNDATION}.clickable",
    ".combinedClickable(": f"{FOUNDATION}.combinedClickable",
    ".verticalScroll(": f"{FOUNDATION}.verticalScroll",
    ".horizontalScroll(": f"{FOUNDATION}.horizontalScroll",
    ".selectable(": f"{FOUNDATION}.selection.selectable",
    ".toggleable(": f"{FOUNDATION}.selection.toggleable",
    ".clip(": f"{UI}.draw.clip",
    ".shadow(": f"{UI}.draw.shadow",
    ".alpha(": f"{UI}.draw.alpha",
    ".rotate(": f"{UI}.draw.rotate",
    ".scale(": f"{UI}.draw.scale",
    ".drawBehind(": f"{UI}.draw.drawBehind",
    ".drawWithContent(": f"{UI}.draw.drawWithContent",
    ".drawWithCache(": f"{UI}.draw.drawWithCache",
    ".blur(": f"{UI}.draw.blur",
    ".graphicsLayer(": f"{UI}.graphics.graphicsLayer",
    ".zIndex(": f"{UI}.zIndex",
    ".pointerInput(": f"{UI}.input.pointer.pointerInput",
    ".nestedScroll(": f"{UI}.input.nestedscroll.nestedScroll",
    ".aspectRatio(": f"{LAYOUT}.aspectRatio",
}

# Types and composables that are equally easy to lose. `.size(` is deliberately not in
# MODIFIERS - `list.size` and `IntSize.size` would drown the output - so `Modifier.size(` is
# spelled out here instead, which only a Modifier chain can produce.
TOKENS = {
    "Modifier.size(": f"{LAYOUT}.size",
    "Modifier.width(": f"{LAYOUT}.width",
    "Modifier.height(": f"{LAYOUT}.height",
    "PaddingValues(": f"{LAYOUT}.PaddingValues",
    "WindowInsets(": f"{LAYOUT}.WindowInsets",
    "Arrangement.": f"{LAYOUT}.Arrangement",
    "Spacer(": f"{LAYOUT}.Spacer",
    "CircleShape": f"{FOUNDATION}.shape.CircleShape",
    "RoundedCornerShape(": f"{FOUNDATION}.shape.RoundedCornerShape",
    "Alignment.": f"{UI}.Alignment",
}

# ⚠ **Imports that cannot exist.** These are members of `BoxScope`, `RowScope` or `ColumnScope`,
# so there is no top-level function of the name to import - writing the import is an unresolved
# reference, which is the mistake r12 made three times in one round while converting a modifier
# into a wrapper. Reported as an error rather than as unused.
SCOPE_MEMBERS = {
    f"{LAYOUT}.matchParentSize",
    f"{LAYOUT}.weight",
    f"{LAYOUT}.align",
    f"{LAYOUT}.alignByBaseline",
    f"{LAYOUT}.alignBy",
}

# A file that declares the name itself needs no import for it.
DECLARES = re.compile(r"^\s*(?:private |internal |public )?(?:fun|val|var|object|class|enum class)\b")


def imports_of(text: str) -> set[str]:
    return {
        line.split("import ", 1)[1].split(" as ")[0].strip()
        for line in text.splitlines()
        if line.startswith("import ")
    }


def code_of(text: str) -> str:
    """The file with comment lines dropped, so prose about a modifier is not a use of it."""
    return "\n".join(
        line
        for line in text.splitlines()
        if not line.lstrip().startswith(("*", "//", "/*"))
    )


def declared_names(text: str) -> set[str]:
    out = set()

    for line in text.splitlines():
        if not DECLARES.match(line):
            continue

        match = re.search(r"\b(?:fun|val|var|object|class)\s+(?:\w+\.)?(\w+)", line)

        if match:
            out.add(match.group(1))

    return out


def main() -> int:
    files = sorted(ROOT.glob("**/src/**/*.kt"))

    bad = 0

    for path in files:
        if "/build/" in path.as_posix():
            continue

        text = path.read_text(encoding="utf-8")

        code = code_of(text)

        have = imports_of(text)

        local = declared_names(text)

        # A star import of the package covers everything in it.
        stars = {i[:-2] for i in have if i.endswith(".*")}

        findings = []

        for table in (MODIFIERS, TOKENS):
            for token, needed in table.items():
                # ⚠ **A word boundary in front, always.** `asPaddingValues(` ends in
                # `PaddingValues(` and `Modifier.someOffset(` ends in `Offset(`; without this the
                # checker reports every correct file that calls one of them.
                if not re.search(r"(?<![A-Za-z0-9_])" + re.escape(token), code):
                    continue

                if needed in have:
                    continue

                package, name = needed.rsplit(".", 1)

                if package in stars or name in local:
                    continue

                findings.append((token, needed))

        for wrong in sorted(have & SCOPE_MEMBERS):
            findings.append(("(scope member)", f"NOTHING — {wrong} does not exist"))

        if findings:
            bad += 1

            print(f"\n{path.relative_to(ROOT).as_posix()}")

            for token, needed in findings:
                print(f"    {token:34s} needs  import {needed}")

    if bad:
        print(f"\n{bad} file(s) with a Compose symbol and no import for it")
    else:
        print(f"checked {len(files)} Kotlin file(s); every listed Compose symbol is imported")

    return bad


if __name__ == "__main__":
    sys.exit(main())
