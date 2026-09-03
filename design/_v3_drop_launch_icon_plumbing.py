#!/usr/bin/env python3
"""
r3 — the launch icon and the launch-time unhiding framework, removed now that nothing reads them.

`_v3_generic_revert_notification.py` reduced `postAppliedSettingsNotification` to
`(context, notificationManager)`. Three things existed **only** to fill the arguments it no
longer takes, and each was a real binder call or a real Flow on every launch:

  FavouriteAppLaunch.icon                 the launched app's rasterised icon
  FavouriteAppLaunch.unhidingFramework    read at apply time so the notification could branch
  ShortcutActivityUiState.applicationIcon the same icon, on the shortcut route
  ShortcutActivityUiState.unhidingFramework
  AppSettingsViewModel.unhidingFramework  a whole StateFlow, threaded through three composables

⚠ **Kept, and deliberately: the `unhidingFramework` *locals* in all three view models.** They
still feed `revertNamesApp(...)` in `AutoUnhideWatch.armIfApplied`, which is a different
question — *which app's record does a revert need* — and one that has nothing to do with
notifications. Only the copies carried onward to the UI go.

⚠ **Kept: `AppSettingsScreen`'s `activityIcon`.** It also draws the pin-shortcut dialogs, so
unlike the other two it was never the notification's alone.

⚠ **`ShortcutActivityUiState.Success` loses its hand-written `equals`/`hashCode`.** They exist
because `applicationIcon` is a `ByteArray`, whose generated equality is identity-based; with
the array gone the remaining fields are an enum pair, a nullable enum and a `String?`, for
which the generated implementations of a `data class` are exactly what the overrides spelled
out. Removing them is equivalent, not a behaviour change.

`FavouriteAppLaunch` stays a plain class rather than becoming a data class: its own comment
says why it is not one, and the reason has to be rewritten rather than the class converted —
converting it would give a launch record structural equality that `_appLaunch.update` has
never wanted.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LAUNCH = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppLaunch.kt"
APPS_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsViewModel.kt"
FAV_VM = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsViewModel.kt"
SHORTCUT_STATE = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityUiState.kt"
SHORTCUT_VM = "app/src/main/kotlin/com/android/geto/activity/shortcut/ShortcutActivityViewModel.kt"
SETTINGS_SCREEN = ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
                   "AppSettingsScreen.kt")
SETTINGS_VM = ("feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
               "AppSettingsViewModel.kt")

# The construction and the two fields, identical in both view models.
CONSTRUCTION_OLD = """                FavouriteAppLaunch(
                    componentName = componentName,
                    result = result,
                    icon = icon,
                    unhidingFramework = unhidingFramework,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
"""

CONSTRUCTION_NEW = """                FavouriteAppLaunch(
                    componentName = componentName,
                    result = result,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
"""

APP_NAME_OLD = """            // Fetched beside the icon, on the same binder trip out, and before the update
            // below: update re-runs its block on a compare-and-set failure and these are real
            // binder calls.
            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)
"""

APP_NAME_NEW = """            // Fetched before the update: update re-runs its block on a compare-and-set
            // failure, and getActivityLabel is a real binder call.
            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)
"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (LAUNCH, [
        (
            """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.UnhidingFramework
""",
            """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
""",
            1,
        ),
        (
            """/**
 * The outcome of applying a favourite's settings, on its way to the UI so it can post the
 * revert notification and open the app.
 *
 * Not a data class: [icon] is a ByteArray, whose equality is identity-based, and the state
 * is cleared to null after handling anyway — so structural equality would buy nothing and
 * mislead anyone who assumed it worked.
 */
class FavouriteAppLaunch(
    val componentName: String,
    val result: AppSettingsResult,
    val icon: ByteArray?,
    /**
     * Read when the settings were applied rather than when the notification is posted, so a
     * launch cannot be applied under one framework and announced under the other if the
     * preference changes in the moment between.
     *
     * The **unhiding** half: this decides which notification follows the hide, and a
     * notification is an offer to undo. What was hidden is [HidingFramework]'s answer and was
     * already settled by the time this record was made.
     */
    val unhidingFramework: UnhidingFramework,
    /**
""",
            """/**
 * The outcome of applying a favourite's settings, on its way to the UI so it can post the
 * revert notification and open the app.
 *
 * ⚠ **It carried the launched app's icon and the unhiding framework until r3**, both solely
 * to fill arguments on `postAppliedSettingsNotification`. That function now takes neither:
 * every launch posts the one generic revert notification, so there is no icon to draw and no
 * branch to choose. The icon was a rasterised bitmap fetched over binder on every launch.
 *
 * Not a data class, still: the state is cleared to null after handling, so nothing compares
 * two of these, and structural equality would only mislead the next reader into thinking
 * something does.
 */
class FavouriteAppLaunch(
    val componentName: String,
    val result: AppSettingsResult,
    /**
""",
            1,
        ),
    ]),
    (APPS_VM, [
        (
            """            val icon = packageManagerWrapper.getActivityIcon(componentName = componentName)

""" + APP_NAME_OLD,
            APP_NAME_NEW,
            1,
        ),
        (CONSTRUCTION_OLD, CONSTRUCTION_NEW, 1),
    ]),
    (FAV_VM, [
        (
            """            // Fetched before the update: update re-runs its block on a compare-and-set
            // failure, and getActivityIcon is a real binder call.
            val icon = packageManagerWrapper.getActivityIcon(componentName = componentName)

""" + APP_NAME_OLD,
            APP_NAME_NEW,
            1,
        ),
        (CONSTRUCTION_OLD, CONSTRUCTION_NEW, 1),
    ]),
    (SHORTCUT_STATE, [
        (
            """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.UnhidingFramework
""",
            """import com.android.geto.domain.model.AppSettingsResult
import com.android.geto.domain.model.HidingFramework
""",
            1,
        ),
        (
            """    data class Success(
        val appSettingsResult: AppSettingsResult?,
        val applicationIcon: ByteArray?,
        val unhidingFramework: UnhidingFramework = UnhidingFramework.Default,
        val hidingFramework: HidingFramework = HidingFramework.Default,
        val appName: String? = null,
    ) : ShortcutActivityUiState {
        override fun equals(other: Any?): Boolean {
            if (this === other) return true
            if (javaClass != other?.javaClass) return false

            other as Success

            if (appSettingsResult != other.appSettingsResult) return false
            if (unhidingFramework != other.unhidingFramework) return false
            if (hidingFramework != other.hidingFramework) return false
            if (appName != other.appName) return false
            if (!applicationIcon.contentEquals(other.applicationIcon)) return false

            return true
        }

        override fun hashCode(): Int {
            var result = appSettingsResult?.hashCode() ?: 0
            result = 31 * result + unhidingFramework.hashCode()
            result = 31 * result + hidingFramework.hashCode()
            result = 31 * result + appName.hashCode()
            result = 31 * result + (applicationIcon?.contentHashCode() ?: 0)
            return result
        }
    }
""",
            """    /**
     * ⚠ **It carried `applicationIcon` and `unhidingFramework` until r3**, both only so the
     * shortcut route could post a per-app revert notification with the launched app's icon.
     * Every launch posts the one generic notification now, so neither is read any more — and
     * the icon was a bitmap fetched over binder on every shortcut press.
     *
     * ⚠ **The hand-written `equals`/`hashCode` went with the icon**, which is the only reason
     * they existed: a `ByteArray` property gives a data class identity-based equality, so both
     * had to be spelled out. What is left is an enum, a nullable enum and a `String?`, for
     * which the generated implementations are exactly what those overrides wrote by hand.
     */
    data class Success(
        val appSettingsResult: AppSettingsResult?,
        val hidingFramework: HidingFramework = HidingFramework.Default,
        val appName: String? = null,
    ) : ShortcutActivityUiState
""",
            1,
        ),
    ]),
    (SHORTCUT_VM, [
        (
            """            val applicationIcon = packageManagerWrapper.getActivityIcon(componentName = componentName)

            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)

            _shortcutActivityUiState.update {
                ShortcutActivityUiState.Success(
                    appSettingsResult = appSettingsResult,
                    applicationIcon = applicationIcon,
                    unhidingFramework = unhidingFramework,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
            }
""",
            """            val appName = packageManagerWrapper.getActivityLabel(componentName = componentName)

            _shortcutActivityUiState.update {
                ShortcutActivityUiState.Success(
                    appSettingsResult = appSettingsResult,
                    hidingFramework = hidingFramework,
                    appName = appName,
                )
            }
""",
            1,
        ),
    ]),
    (SETTINGS_VM, [
        (
            """    /**
     * Which notification this screen's launch button should post.
     *
     * Read here rather than in the composable because the repository is a suspending flow
     * and this screen already owns every other read of it.
     */
    val unhidingFramework = userDataRepository.userData
        .map { it.unhidingFramework }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = UnhidingFramework.Default,
        )

""",
            "",
            1,
        ),
        (
            """import com.android.geto.domain.model.UnhidingFramework
""",
            "",
            1,
        ),
    ]),
    (SETTINGS_SCREEN, [
        (
            """import com.android.geto.domain.model.UnhidingFramework
""",
            "",
            1,
        ),
        (
            """    val unhidingFramework by viewModel.unhidingFramework.collectAsStateWithLifecycle()

""",
            "",
            1,
        ),
        (
            """        revertAppSettingsResult = revertAppSettingsResult,
        unhidingFramework = unhidingFramework,
        requestPinShortcutResult = requestPinShortcutResult,
        appSettingTemplates = appSettingTemplates,
""",
            """        revertAppSettingsResult = revertAppSettingsResult,
        requestPinShortcutResult = requestPinShortcutResult,
        appSettingTemplates = appSettingTemplates,
""",
            1,
        ),
        (
            """    revertAppSettingsResult: AppSettingsResult?,
    unhidingFramework: UnhidingFramework,
    requestPinShortcutResult: RequestPinShortcutResult?,
    appSettingTemplates: List<AppSettingTemplate>,
""",
            """    revertAppSettingsResult: AppSettingsResult?,
    requestPinShortcutResult: RequestPinShortcutResult?,
    appSettingTemplates: List<AppSettingTemplate>,
""",
            1,
        ),
        (
            """        revertAppSettingsResult = revertAppSettingsResult,
        unhidingFramework = unhidingFramework,
        requestPinShortcutResult = requestPinShortcutResult,
        getPinShortcutResult = getPinShortcutResult,
""",
            """        revertAppSettingsResult = revertAppSettingsResult,
        requestPinShortcutResult = requestPinShortcutResult,
        getPinShortcutResult = getPinShortcutResult,
""",
            1,
        ),
        (
            """    revertAppSettingsResult: AppSettingsResult?,
    unhidingFramework: UnhidingFramework,
    requestPinShortcutResult: RequestPinShortcutResult?,
    getPinShortcutResult: GetPinShortcutResult?,
""",
            """    revertAppSettingsResult: AppSettingsResult?,
    requestPinShortcutResult: RequestPinShortcutResult?,
    getPinShortcutResult: GetPinShortcutResult?,
""",
            1,
        ),
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

    # ⚠ The locals must survive: they still answer `revertNamesApp`, which is a different
    # question from which notification to post and is not what this script is removing.
    for rel in (APPS_VM, FAV_VM, SHORTCUT_VM):
        text = staged.get(ROOT / rel, "")

        if text.count("val unhidingFramework = userData.unhidingFramework") != 1:
            problems.append(f"{rel}: the local the auto-unhide arm reads is gone")

        if text.count("unhidingFramework = unhidingFramework,") != 1:
            problems.append(f"{rel}: expected the arm to be the only remaining reader")

    # Nothing anywhere may still name what this removes.
    for name, where in (
        ("applicationIcon", SHORTCUT_VM),
        ("val icon =", APPS_VM),
        ("val icon =", FAV_VM),
        ("unhidingFramework", SETTINGS_SCREEN),
        ("unhidingFramework", SETTINGS_VM),
    ):
        if name in staged.get(ROOT / where, ""):
            problems.append(f"{where}: still names {name!r}")

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120:
                problems.append(
                    f"{path.relative_to(ROOT)}: added line of {len(line)} chars: "
                    f"{line.strip()[:58]!r}",
                )

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")
        print(f"  wrote {path.relative_to(ROOT)}")

    print("ok - the launch icon and the launch-time unhiding framework are gone")

    return 0


if __name__ == "__main__":
    sys.exit(main())
