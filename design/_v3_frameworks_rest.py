#!/usr/bin/env python3
"""
v3-r2 — the remaining read sites.

Two groups:

* **hide-side** — IMD+'s two "which list does this run read" decisions, the apps list's long
  press, and the favourites per-app flag. All become HidingFramework.
* **unhide-side** — the per-app screen, whose only use of the old preference is choosing which
  notification a successful apply posts. Becomes UnhidingFramework.

⚠ AutoHideRunner's local is renamed `memory` -> `perApp`, deliberately. After the split
"memory" is an *unhiding* word and this local is a *hiding* question; leaving it named memory
is how the next round reads it as the wrong half. Only the two declarations and their four
readers move — the prose in the KDoc is left for the wording pass.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

AUTO_HIDE = "broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoHideRunner.kt"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (AUTO_HIDE, [
        ("                val memory = userData.notificationFunction == NotificationFunction.Memory\n",
         "                val perApp = userData.hidingFramework == HidingFramework.PerApp\n", 1),
        ("                    !memory ->\n", "                    !perApp ->\n", 1),
        ("            val memory = userData.notificationFunction == NotificationFunction.Memory\n",
         "            val perApp = userData.hidingFramework == HidingFramework.PerApp\n", 1),
        ("            val componentName = if (memory) configuredComponentFor(packageName) else null\n",
         "            val componentName = if (perApp) configuredComponentFor(packageName) else null\n", 1),
        ("                memory && componentName == null -> AutoHideOutcome.NoProfile\n",
         "                perApp && componentName == null -> AutoHideOutcome.NoProfile\n", 1),
        ("                !memory && userData.effectiveSettingsToHide.none { it.value } ->\n",
         "                !perApp && userData.effectiveSettingsToHide.none { it.value } ->\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n", 1),
    ]),
    ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt", [
        ("    val notificationFunction by viewModel.notificationFunction.collectAsStateWithLifecycle()\n",
         "    val hidingFramework by viewModel.hidingFramework.collectAsStateWithLifecycle()\n", 1),
        ("            if (notificationFunction == NotificationFunction.Memory) {\n",
         "            if (hidingFramework == HidingFramework.PerApp) {\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n", 1),
    ]),
    ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt", [
        ("    val perApp = userData.notificationFunction == NotificationFunction.Memory\n",
         "    val perApp = userData.hidingFramework == HidingFramework.PerApp\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n", 1),
    ]),
    ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsViewModel.kt", [
        ("    val notificationFunction = userDataRepository.userData\n        .map { it.notificationFunction }\n",
         "    val unhidingFramework = userDataRepository.userData\n        .map { it.unhidingFramework }\n", 1),
        ("            initialValue = NotificationFunction.Default,\n",
         "            initialValue = UnhidingFramework.Default,\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsScreen.kt", [
        ("    val notificationFunction by viewModel.notificationFunction.collectAsStateWithLifecycle()\n",
         "    val unhidingFramework by viewModel.unhidingFramework.collectAsStateWithLifecycle()\n", 1),
        ("\n        notificationFunction = notificationFunction,\n",
         "\n        unhidingFramework = unhidingFramework,\n", 2),
        ("\n    notificationFunction: NotificationFunction,\n",
         "\n    unhidingFramework: UnhidingFramework,\n", 2),
        ("\n                    notificationFunction = notificationFunction,\n",
         "\n                    unhidingFramework = unhidingFramework,\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
]


def main() -> int:
    staged: dict[Path, str] = {}
    problems: list[str] = []

    for rel, subs in EDITS:
        path = ROOT / rel

        if not path.exists():
            problems.append(f"{rel}: missing")
            continue

        text = path.read_text(encoding="utf-8")

        for old, new, expected in subs:
            found = text.count(old)

            if found != expected:
                problems.append(
                    f"{rel}: expected {expected} of "
                    f"{old.strip().splitlines()[0][:58]!r}, found {found}",
                )
                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    # No code line may still name the old preference. KDoc prose is left alone on purpose —
    # the wording pass rewrites it — so only lines that are not comments are checked.
    for path, text in staged.items():
        leftover = [
            line.strip()
            for line in text.splitlines()
            if "otificationFunction" in line and not line.lstrip().startswith(("*", "//", "/*"))
        ]

        if leftover:
            problems.append(
                f"{path.relative_to(ROOT)}: code still names the old preference: {leftover}",
            )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print(f"ok — {len(staged)} files re-pointed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
