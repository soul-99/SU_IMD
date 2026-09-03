#!/usr/bin/env python3
"""
v3-r2d — the six remaining LENGTH_LONG toasts, which r2c missed.

The author's instruction was "Make all the toasts that IMD sends to short length, i mean all".
r2c did the hide/unhide set in `common/RevertToasts.kt` and stopped there, because that file is
where a grep for the shared helpers ends. These six call `Toast.makeText` directly from their
own modules and never touch a helper, so nothing pointed at them.

Seven toasts across six call sites — `SettingsManagerRoute` line 186 picks one of two strings:

| toast | where |
| --- | --- |
| This device has no screen for that setting | the ⧉ buttons in the dialogs |
| No Shizuku app found — set the package name in Settings | settings manager |
| Please enable developer options first / Could not open that screen on this device | settings manager |
| Please wait 10s, as some Shizuku forks are slow to start service via intents | settings manager |
| Your current launcher does not support shortcuts | pinning a shortcut |
| Could not open settings on this device | setup screen |

⚠ **The wait toast is the one worth a second thought and it goes short anyway.** It is the
longest sentence of the six and it asks the user to wait ten seconds, so a two-second toast is
arguably too short to read it. The author has now twice been asked whether an exception is
wanted and twice said all of them, and a rule with one survivor is not a rule. If the sentence
turns out to be unreadable on the device the fix is to shorten the sentence, not to lengthen
the toast.

`setup_copied` is untouched: it was already LENGTH_SHORT, and it is the only toast in the app
that already agreed with the instruction.

Asserts that nothing but these six changes, that no LENGTH_LONG survives in any Kotlin file,
and writes nothing if either fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# path -> the exact lines to flip. Each must appear exactly once.
EDITS: dict[str, list[str]] = {
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
    "SystemSettingsButton.kt": [
        "            android.widget.Toast.LENGTH_LONG,\n",
    ],
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
    "SettingsManagerRoute.kt": [
        "        Toast.makeText(this, R.string.settings_manager_no_shizuku, "
        "Toast.LENGTH_LONG).show()\n",
        "        Toast.makeText(this, message, Toast.LENGTH_LONG).show()\n",
        "    Toast.makeText(this, R.string.settings_manager_shizuku_wait, "
        "Toast.LENGTH_LONG).show()\n",
    ],
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/shortcut/"
    "ShortcutRoute.kt": [
        "                    Toast.LENGTH_LONG,\n",
    ],
    "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt": [
        "        Toast.makeText(this, R.string.setup_open_settings_failed, "
        "Toast.LENGTH_LONG).show()\n",
    ],
}

# The one place the words may still appear: RevertToasts.kt's KDoc, which explains why the
# failure trio stopped being long. A comment, not a call.
COMMENT_ONLY = "common/src/main/kotlin/com/android/geto/common/RevertToasts.kt"


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {}

    flipped = 0

    for name, lines in EDITS.items():
        path = ROOT / name

        if not path.exists():
            problems.append(f"{name} is missing")

            continue

        text = path.read_text(encoding="utf-8")

        for line in lines:
            found = text.count(line)

            if found != 1:
                problems.append(f"{path.name}: {found} of {line.strip()[:70]!r}")

                continue

            text = text.replace(line, line.replace("LENGTH_LONG", "LENGTH_SHORT"), 1)

            flipped += 1

        for line in text.splitlines():
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

        staged[path] = text

    if flipped != sum(len(lines) for lines in EDITS.values()):
        problems.append(f"flipped {flipped}, expected {sum(len(v) for v in EDITS.values())}")

    # Nothing anywhere may still ask for a long toast.
    for kotlin in sorted(ROOT.rglob("*.kt")):
        if "build" in kotlin.relative_to(ROOT).parts:
            continue

        body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

        if "LENGTH_LONG" not in body:
            continue

        if kotlin.relative_to(ROOT).as_posix() == COMMENT_ONLY:
            for number, line in enumerate(body.splitlines(), start=1):
                if "LENGTH_LONG" in line and not line.lstrip().startswith("*"):
                    problems.append(f"{COMMENT_ONLY}:{number} is code, not the KDoc")

            continue

        problems.append(f"{kotlin.relative_to(ROOT)}: LENGTH_LONG survives")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"ok — {flipped} toasts across {len(staged)} files; no LENGTH_LONG left in any call")

    return 0


if __name__ == "__main__":
    sys.exit(main())
