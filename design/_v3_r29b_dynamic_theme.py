#!/usr/bin/env python3
"""
r29b — dynamic theme is ON until somebody says otherwise.

The author: *"also make dynamic theme on by default"*.

## Why this is not a one-line change

`dynamicTheme` is proto tag 2, a plain bool, and **proto3 has no custom defaults** — handover §7.
An unwritten bool decodes to false, so "on by default" cannot be expressed by the field itself.
There are two shapes already in this schema for the problem:

* rename the field for the *non*-default state, the way `drawerShortcutManagerOff` does — which
  needs a fresh tag, and throws away every choice already stored against tag 2; or
* a companion `…Set` bool, the way `progressiveBlurSet` (84), `favouriteAppsViewSet` (69) and
  `blurCustomised` (80) do — unset, the resolution answers the new default; set, it answers what
  the real field holds.

This takes the second, because it keeps tag 2 and everything written to it. It is the same change
r27 made for the blur, on the next free tag, 85.

⚠ **It cannot recover a choice made before it existed**, and that is worth saying out loud because
somebody will notice it on the device. Under the old default, an install that never touched the
switch and an install that deliberately turned dynamic theme *off* are the same absent field —
there is no byte anywhere that tells them apart. So on this update, anyone in the second group gets
dynamic theme back **once**, turns it off again, and is then recorded properly for ever after.
r27 paid exactly this for the blur; it is what flipping a proto3 default costs, whichever way it is
done.

⚠ **Both fields on every write.** `updateDynamicColor` must set 85 as well as 2, or the value it
writes is invisible to the read above — which is the bug the same pattern would have had in r27.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = ROOT / "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"
SOURCE = ROOT / "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

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
    """The file with its comment lines removed — see handover §8, the comment trap."""
    return "\n".join(
        line for line in text.splitlines()
        if not line.strip().startswith(("//", "*", "/*", "/**", "#"))
    )


# ---------------------------------------------------------------- the proto

proto = PROTO.read_text(encoding="utf-8")

# ⚠ Asserted on the code, not the file: the comment above 84 discusses "custom defaults" and
# several tags by number, so a bare search for "85" finds prose.
body = code(proto)

check(
    "= 85;" not in body,
    "proto: tag 85 is already taken — pick the next free one",
)

check(
    body.count("bool dynamicTheme = 2;") == 1,
    "proto: dynamicTheme is not on tag 2",
)

proto = replace_once(
    proto,
    "  bool progressiveBlurSet = 84;\n",
    "  bool progressiveBlurSet = 84;\n"
    "\n"
    "  // Whether anybody has touched the dynamic colour switch.\n"
    "  //\n"
    "  // ⚠ **Added in r29, when the author asked for dynamic theme to be ON by default.** Tag 2 is\n"
    "  // named for the ON state and proto3 decodes it to false, so the name stopped describing what\n"
    "  // an unwritten field gives the moment the default moved. This says whether 2 means anything\n"
    "  // yet: unset, the resolution answers true; set, it answers what 2 holds. Keeping 2 rather\n"
    "  // than renaming onto a fresh number is what preserves every choice already stored there.\n"
    "  //\n"
    "  // ⚠ It cannot recover a choice made before it existed. Under the old default an install that\n"
    "  // never touched the switch and one that deliberately turned it off are the same absent field,\n"
    "  // so anyone in the second group gets dynamic colour back once and keeps their answer from\n"
    "  // then on. progressiveBlurSet on 84 paid the same price in r27.\n"
    "  bool dynamicThemeSet = 85;\n",
    "proto: the field after progressiveBlurSet",
)

check(
    code(proto).count("bool dynamicThemeSet = 85;") == 1,
    "proto: dynamicThemeSet did not land exactly once",
)

# ---------------------------------------------------------------- the read

source = SOURCE.read_text(encoding="utf-8")

source = replace_once(
    source,
    "            dynamicTheme = it.dynamicTheme,\n",
    "            // ⚠ **On until told otherwise — r29.** See dynamicThemeSet in the proto: the\n"
    "            // companion bool is what lets the default change without discarding the choices\n"
    "            // already stored against dynamicTheme. Same shape as progressiveBlur, below.\n"
    "            dynamicTheme = if (it.dynamicThemeSet) it.dynamicTheme else true,\n",
    "datasource: the dynamicTheme read",
)

# ---------------------------------------------------------------- the write

source = replace_once(
    source,
    "    suspend fun updateDynamicColor(dynamicTheme: Boolean) {\n"
    "        userPreferences.updateData {\n"
    "            it.copy { this.dynamicTheme = dynamicTheme }\n"
    "        }\n"
    "    }\n",
    "    suspend fun updateDynamicColor(dynamicTheme: Boolean) {\n"
    "        userPreferences.updateData {\n"
    "            it.copy {\n"
    "                this.dynamicTheme = dynamicTheme\n"
    "\n"
    "                // Both, always: the value is meaningless to the read above until this is true.\n"
    "                dynamicThemeSet = true\n"
    "            }\n"
    "        }\n"
    "    }\n",
    "datasource: updateDynamicColor",
)

# ⚠ Counted on the code so the two new comment blocks above do not count themselves — the very
# trap handover §8 opens with.
body = code(source)

check(
    body.count("dynamicThemeSet") == 2,
    f"datasource: dynamicThemeSet referenced {body.count('dynamicThemeSet')}x in code, expected 2 "
    "(one read, one write)",
)

check(
    "if (it.dynamicThemeSet) it.dynamicTheme else true" in body,
    "datasource: the read is not resolving against the companion bool",
)

check(
    body.count("it.copy { this.dynamicTheme = dynamicTheme }") == 0,
    "datasource: the old single-field write survived",
)

# The switch's own call path is untouched by design — this is a check that it still exists, so a
# rename upstream cannot leave the default stranded with nothing writing the flag.
check(
    "updateDynamicColor" in body,
    "datasource: updateDynamicColor has gone",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

PROTO.write_text(proto, encoding="utf-8")

print(f"wrote {PROTO.relative_to(ROOT).as_posix()}")

SOURCE.write_text(source, encoding="utf-8")

print(f"wrote {SOURCE.relative_to(ROOT).as_posix()}")

print("ok")
