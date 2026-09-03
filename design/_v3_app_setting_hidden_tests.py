#!/usr/bin/env python3
"""
v3-r4m-c — host assertions for `appSettingHidden`, the one case that still leaves the screen.

The author's answer was *"keep them hidden until Shevery's engine lands"* for exactly one row,
and everything else greys. That is a one-line rule with a one-word difference from
`appSettingBlocked`, which is precisely the shape that gets quietly widened later - so it is
pinned here: **hidden is a strict subset of blocked, and it covers one key on one fork.**

⚠ The pairing assertion is the one that matters. A row that is hidden but not blocked would be
taken off the screen while the hide still acted on it, which is the exact defect r4m removed
from the two filters these replaced.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

OLD = """    // 6. And with 'Manage Shizuku' off, which is the author's own wording for this round -
    //    the marker is blocked on a fork that does speak intents.
    check(
        "manage shizuku off blocks the shizuku marker on thedjchi",
        appSettingBlocked(
            userData = thedjchi.copy(manageShizuku = false),
            key = AppSettingKeys.SHIZUKU_SERVICE,
        ),
    )
}"""

NEW = """    // 6. And with 'Manage Shizuku' off, which is the author's own wording for this round -
    //    the marker is blocked on a fork that does speak intents.
    check(
        "manage shizuku off blocks the shizuku marker on thedjchi",
        appSettingBlocked(
            userData = thedjchi.copy(manageShizuku = false),
            key = AppSettingKeys.SHIZUKU_SERVICE,
        ),
    )

    // 7. ⚠ **Hidden is not the same as blocked, and it is one key on one fork.** Everything
    //    else that cannot work is drawn and greyed; only the Shizuku marker on a fork with no
    //    intents leaves the screen, because there the control has no engine behind it yet.
    check(
        "shevery hides the shizuku marker",
        appSettingHidden(userData = shevery, key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    check(
        "and hides nothing else",
        !appSettingHidden(userData = shevery, key = AppSettingKeys.SYSTEM_ALERT_WINDOW) &&
            !appSettingHidden(userData = shevery, key = AppSettingKeys.ACCESSIBILITY_ENABLED) &&
            !appSettingHidden(userData = shevery, key = "screen_brightness"),
    )
    check(
        "thedjchi hides nothing at all, with the master switch either way",
        !appSettingHidden(userData = thedjchi, key = AppSettingKeys.SHIZUKU_SERVICE) &&
            !appSettingHidden(
                userData = thedjchi.copy(manageShizuku = false),
                key = AppSettingKeys.SHIZUKU_SERVICE,
            ),
    )

    // ⚠ **The pairing, and it is the assertion worth having.** A row hidden but not blocked
    // would leave the screen while the hide went on acting on it - the exact defect the two
    // filters r4m removed used to carry.
    for (fork in listOf(shevery, thedjchi, thedjchi.copy(manageShizuku = false))) {
        for (key in listOf(
            AppSettingKeys.SYSTEM_ALERT_WINDOW,
            AppSettingKeys.SHIZUKU_SERVICE,
            AppSettingKeys.ACCESSIBILITY_ENABLED,
            "screen_brightness",
        )) {
            if (appSettingHidden(userData = fork, key = key)) {
                check(
                    "anything hidden is also blocked: $key",
                    appSettingBlocked(userData = fork, key = key),
                )
            }
        }
    }
}"""

IMPORT = "import com.android.geto.domain.model.appSettingHidden"


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")

    if statement in lines:
        return text

    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    path = ROOT / TESTS

    original = path.read_text(encoding="utf-8")

    if "appSettingHidden" in original:
        print("REFUSED: appSettingHidden already asserted — has this run before?")
        return 1

    if original.count(OLD) != 1:
        print(f"REFUSED: the shevery block matched {original.count(OLD)} time(s), expected 1")
        return 1

    text = insert_import(original.replace(OLD, NEW, 1), IMPORT)

    # Assert POSITION: the new assertions sit inside the same function as the ones above them.
    at_shevery = text.index('val shevery = userData(ShizukuForkMode.Other')
    at_new = text.index('"shevery hides the shizuku marker"')
    at_next = text.index("\nprivate fun taskerIntegrationTests()")

    if not at_shevery < at_new < at_next:
        print(f"REFUSED: placement wrong — shevery@{at_shevery} new@{at_new} next@{at_next}")
        return 1

    was = {line for line in original.split("\n") if len(line) > 120}

    gained = [
        (n, len(line))
        for n, line in enumerate(text.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ") and line not in was
    ]

    if gained:
        print(f"REFUSED: {TESTS} would gain lines over 120 chars: {gained}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {TESTS}")
    print("  + hidden is one key on one fork, and is always also blocked")
    print("\nwrote 1 file, 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
