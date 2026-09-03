#!/usr/bin/env python3
"""
v3-r2 — re-point the notification side at the Unhiding framework.

Which notification a hide posts is an unhiding question: the per-app one offers a memory
revert for one app, the single one offers a Revert to default for the device. Before the split
both read the same preference as the hide did, which is why the two could never disagree.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppLaunch.kt", [
        ("""    /**
     * Read when the settings were applied rather than when the notification is posted, so a
     * launch cannot be applied under one function and announced under the other if the
     * preference changes in the moment between.
     */
    val notificationFunction: NotificationFunction,
""",
         """    /**
     * Read when the settings were applied rather than when the notification is posted, so a
     * launch cannot be applied under one framework and announced under the other if the
     * preference changes in the moment between.
     *
     * The **unhiding** half: this decides which notification follows the hide, and a
     * notification is an offer to undo. What was hidden is [HidingFramework]'s answer and was
     * already settled by the time this record was made.
     */
    val unhidingFramework: UnhidingFramework,
""", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityUiState.kt", [
        ("        val notificationFunction: NotificationFunction = NotificationFunction.Default,\n",
         "        val unhidingFramework: UnhidingFramework = UnhidingFramework.Default,\n", 1),
        ("            if (notificationFunction != other.notificationFunction) return false\n",
         "            if (unhidingFramework != other.unhidingFramework) return false\n", 1),
        ("result = 31 * result + notificationFunction.hashCode()",
         "result = 31 * result + unhidingFramework.hashCode()", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppLaunchEffect.kt", [
        ("                        notificationFunction = launch.notificationFunction,\n",
         "                        unhidingFramework = launch.unhidingFramework,\n", 1),
    ]),
    ("app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivity.kt", [
        ("                            notificationFunction = shortcutActivityUiState.notificationFunction,\n",
         "                            unhidingFramework = shortcutActivityUiState.unhidingFramework,\n", 1),
    ]),
    ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/PostAppliedSettingsNotification.kt", [
        ("    notificationFunction: NotificationFunction,\n",
         "    unhidingFramework: UnhidingFramework,\n", 1),
        ("    when (notificationFunction) {\n        NotificationFunction.Memory -> {\n",
         "    when (unhidingFramework) {\n        UnhidingFramework.Memory -> {\n", 1),
        ("        NotificationFunction.RevertToDefault -> {\n",
         "        UnhidingFramework.RevertToDefault -> {\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("broadcast-receiver/src/main/kotlin/com/android/geto/broadcastreceiver/AutoRevertRunner.kt", [
        ("        when (settings.notificationFunction) {\n"
         "            NotificationFunction.RevertToDefault -> revertToDefaultRunner(auto = true)\n"
         "\n"
         "            NotificationFunction.Memory -> {\n",
         "        when (settings.unhidingFramework) {\n"
         "            UnhidingFramework.RevertToDefault -> revertToDefaultRunner(auto = true)\n"
         "\n"
         "            UnhidingFramework.Memory -> {\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetAutoRevertSettingsUseCase.kt", [
        ("        val notificationFunction: NotificationFunction,\n",
         "        val unhidingFramework: UnhidingFramework,\n", 1),
        ("            notificationFunction = userData.notificationFunction,\n",
         "            unhidingFramework = userData.unhidingFramework,\n", 1),
        ("import com.android.geto.domain.model.NotificationFunction\n",
         "import com.android.geto.domain.model.UnhidingFramework\n", 1),
    ]),
    ("domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetAutoUnhideSettingsUseCase.kt", [
        ("        val notificationFunction: NotificationFunction,\n",
         "        val unhidingFramework: UnhidingFramework,\n", 1),
        ("            notificationFunction = userData.notificationFunction,\n",
         "            unhidingFramework = userData.unhidingFramework,\n", 1),
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

    for path, text in staged.items():
        leftover = [
            line.strip()
            for line in text.splitlines()
            if "otificationFunction" in line
        ]

        if leftover:
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

    print(f"ok — {len(staged)} files re-pointed at the Unhiding framework")

    return 0


if __name__ == "__main__":
    sys.exit(main())
