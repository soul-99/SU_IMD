#!/usr/bin/env python3
"""
v3-r2 — re-point the three launch sites at the two frameworks.

The apps list, favourites and the pinned shortcut read identically today: one preference
decides both which hide runs and which notification follows. After the split the hide asks
HidingFramework and the notification asks UnhidingFramework, and the auto-unhide session kind
asks both together through revertNamesApp.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPS_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsViewModel.kt"
FAV_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsViewModel.kt"
SHORTCUT_VM = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"

# The launch body, identical in all three but for the local names around it.
WHEN_OLD = """            val result = when (notificationFunction) {
                NotificationFunction.RevertToDefault -> applySettingsToHideUseCase()

                NotificationFunction.Memory -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }
"""

WHEN_NEW = """            val result = when (hidingFramework) {
                HidingFramework.ImdDefaults -> applySettingsToHideUseCase()

                HidingFramework.PerApp -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }
"""

SHORTCUT_WHEN_OLD = """            val appSettingsResult = when (notificationFunction) {
                NotificationFunction.RevertToDefault -> applySettingsToHideUseCase()

                NotificationFunction.Memory -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }
"""

SHORTCUT_WHEN_NEW = """            val appSettingsResult = when (hidingFramework) {
                HidingFramework.ImdDefaults -> applySettingsToHideUseCase()

                HidingFramework.PerApp -> {
                    applyAppSettingsUseCase(componentName = componentName)
                }
            }
"""

READ_OLD = """            val notificationFunction = userDataRepository.userData.first().notificationFunction
"""

READ_NEW = """            val userData = userDataRepository.userData.first()

            val hidingFramework = userData.hidingFramework

            val unhidingFramework = userData.unhidingFramework
"""

ARM_OLD = """                memory = notificationFunction == NotificationFunction.Memory,
"""

ARM_NEW = """                memory = revertNamesApp(
                    hidingFramework = hidingFramework,
                    unhidingFramework = unhidingFramework,
                ),
"""

LAUNCH_FIELD_OLD = """                    notificationFunction = notificationFunction,
"""

LAUNCH_FIELD_NEW = """                    unhidingFramework = unhidingFramework,
"""

# (path, [(old, new, expected count)])
EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (APPS_VM, [
        (READ_OLD, READ_NEW, 1),
        (WHEN_OLD, WHEN_NEW, 1),
        (ARM_OLD, ARM_NEW, 1),
        (LAUNCH_FIELD_OLD, LAUNCH_FIELD_NEW, 1),
        # The gesture flow the list reads: a long press edits a profile only where profiles
        # are what a launch uses, which is the hiding half.
        ("    val notificationFunction = userDataRepository.userData\n"
         "        .map { it.notificationFunction }\n"
         "        .stateIn(\n"
         "            viewModelScope,\n"
         "            SharingStarted.WhileSubscribed(5000),\n"
         "            NotificationFunction.Default,\n"
         "        )\n",
         "    val hidingFramework = userDataRepository.userData\n"
         "        .map { it.hidingFramework }\n"
         "        .stateIn(\n"
         "            viewModelScope,\n"
         "            SharingStarted.WhileSubscribed(5000),\n"
         "            HidingFramework.Default,\n"
         "        )\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n"
         "import com.android.geto.domain.model.revertNamesApp\n", 1),
    ]),
    (FAV_VM, [
        (READ_OLD, READ_NEW, 1),
        (WHEN_OLD, WHEN_NEW, 1),
        (ARM_OLD, ARM_NEW, 1),
        (LAUNCH_FIELD_OLD, LAUNCH_FIELD_NEW, 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n"
         "import com.android.geto.domain.model.revertNamesApp\n", 1),
    ]),
    (SHORTCUT_VM, [
        (READ_OLD, READ_NEW, 1),
        (SHORTCUT_WHEN_OLD, SHORTCUT_WHEN_NEW, 1),
        (ARM_OLD, ARM_NEW, 1),
        ("                    notificationFunction = notificationFunction,\n",
         "                    unhidingFramework = unhidingFramework,\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.HidingFramework\n"
         "import com.android.geto.domain.model.revertNamesApp\n", 1),
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
                    f"{rel}: expected {expected} of {old.strip().splitlines()[0][:58]!r}, "
                    f"found {found}",
                )
                continue

            text = text.replace(old, new, expected)

        staged[path] = text

    # Nothing may name the old preference in these files afterwards.
    for path, text in staged.items():
        if "notificationFunction" in text or "NotificationFunction" in text:
            leftover = [
                line.strip()
                for line in text.splitlines()
                if "otificationFunction" in line
            ]
            problems.append(
                f"{path.relative_to(ROOT)}: still names the old preference: {leftover}",
            )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print(f"ok — {len(staged)} launch sites re-pointed")

    return 0


if __name__ == "__main__":
    sys.exit(main())
