#!/usr/bin/env python3
"""
Dialogs stop closing on rotation, and on a foldable being folded or unfolded.

## What was wrong

Nothing in the manifest declares `configChanges`, so a rotation - or a fold, which is a
configuration change of the same kind - destroys and recreates the activity. Every dialog in
this app is driven by a `var show… by remember { mutableStateOf(false) }` in the composable
that owns it, and `remember` does not survive that. The dialog was not closing; the flag that
kept it open was being thrown away and rebuilt as `false`.

## Why this and not `android:configChanges`

Declaring `configChanges` on the activities would fix all of it in four lines and was the first
thing considered. It was rejected: `AppLocale.wrap` is applied in `attachBaseContext`, which is
*not* called again when an activity handles a configuration change itself. Below Android 13 -
which is `minSdk 24` up to 32, so most of the supported range - the framework would hand the
activity a fresh Configuration carrying the system locale, and rotating the phone would drop
the app back into the system language. That is a worse bug than the one being fixed, in ten
locales that would not be noticed here.

`rememberSaveable` changes no lifecycle. It writes the flag into the saved-state bundle, which
is exactly what a recreation restores, and it costs a boolean per dialog.

## What is deliberately left alone

- **`expanded`, the settings accordion** - documented as plain `remember` so the screen always
  opens on Default IMD settings rather than wherever it was left last week.
- **`refreshing` / `refreshTick`** - true only while a package-manager sweep is in flight. The
  coroutine does not survive recreation, so a saved `true` would strand a spinner that nothing
  is left to switch off.
- **`languageTag`** - documented as deliberately re-read from the platform rather than held,
  because Android's own per-app language screen can change it behind the app's back. It re-reads
  to the same value across a rotation, so the language dialog loses nothing by it.
- **`asking` / `grant` in the setup screen** - `asking` is an in-flight Shizuku call, and
  MainActivity already documents why setup state is not saved.
- **dropdown `expanded` flags and `revealed`** - a menu restored open with nothing focused under
  it, and a secret re-revealed by a rotation, are both worse than the reset.

## One decision reversed

`showSheveryNotice` and `pendingFork` carried a comment saying the drop on rotation was the safe
direction. It is - nothing is committed either way - but the author has now asked for dialogs to
survive rotation, and "safe" was never the same as "wanted". The comment is rewritten rather
than left contradicting the code.

Asserts every match count and writes nothing on any mismatch.
"""

import os
import re
import sys

ROOT = os.environ.get(
    "GETO_ROOT",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
)

IMPORT = "import androidx.compose.runtime.saveable.rememberSaveable"

# file -> {variable name: how many declarations of it that file has}
TARGETS = {
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt": {
        "showThemeDialog": 1,
        "showLanguageDialog": 1,
        "showAccessibilityServicesDialog": 1,
        "showOverlayPackagesDialog": 1,
        "showNotificationFunctionDialog": 1,
        "showRevertDefaultsDialog": 1,
        "showSettingsToHideDialog": 1,
        "showAutoHidePage": 1,
        "showAutoHideApps": 1,
        "showAutoHideHowItWorks": 1,
        "showMemoryHideNotice": 1,
        "showSettingsLog": 1,
        "showAutoHideBlockedNotice": 1,
        "showAutoRevertNotice": 1,
        "showManageOverlayNotice": 1,
        "showTaskerIntegration": 1,
        # The theme dialog's pending radio selection.
        "selectedTheme": 1,
        "showSheveryNotice": 1,
        "pendingFork": 1,
    },
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHideDialogs.kt": {
        # The search box inside the app picker: a rotation used to empty it mid-search.
        "query": 1,
    },
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt": {
        "showShizukuServiceNotice": 1,
    },
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHidePage.kt": {
        # Whether the notification permission was refused - the answer to a question the user
        # has already been asked, which should not be forgotten by turning the phone.
        "denied": 1,
    },
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/AndroidSettingsManagerDialog.kt": {
        "showShizukuHelp": 1,
        "showShizukuUnmanageable": 1,
        "showSheveryToggle": 1,
        "showAccessibilityUnmanaged": 1,
        "showOverlayUnmanaged": 1,
        "showInfo": 1,
        "showFailureHelp": 1,
    },
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/SortLauncherAppsActivityInfoDialog.kt": {
        "selectedSortLauncherAppsActivityInfoIndex": 1,
        "selectedSortOrderLauncherAppsActivityInfoIndex": 1,
        "selectedShowSystem": 1,
    },
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/AppsScreen.kt": {
        "showSortLauncherAppsActivityInfoDialog": 1,
    },
    "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt": {
        "showOptionsDialog": 1,
        "showReorderDialog": 1,
    },
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/dialog/ShortcutDialog.kt": {
        # Two composables in this file - create and update - each with the same four.
        "shortLabel": 2,
        "longLabel": 2,
        "showShortLabelError": 2,
        "showLongLabelError": 2,
    },
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/dialog/AppSettingDialog.kt": {
        "selectedRadioOptionIndex": 1,
        "label": 1,
        "key": 1,
        "valueOnLaunch": 1,
        "valueOnRevert": 1,
        "showLabelError": 1,
        "showKeyError": 1,
        "showKeyNotFoundError": 1,
        "showValueOnLaunchError": 1,
        "showValueOnRevertError": 1,
    },
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/AppSettingsScreen.kt": {
        "showAppSettingDialog": 1,
        "showTemplateDialog": 1,
        "showWriteSecureSettingsDialog": 1,
    },
    "app/src/main/kotlin/com/android/geto/onboarding/LanguageSetupScreen.kt": {
        # The language picked but not yet confirmed.
        "draft": 1,
    },
}

# Names that must keep plain `remember`, asserted afterwards so a future sweep cannot quietly
# take them with it. file -> names.
KEEP = {
    "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt": [
        "expanded", "refreshing", "refreshTick", "languageTag", "revealed",
    ],
    "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt": ["asking", "grant"],
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/dialog/AppSettingDialog.kt": [
        "secureSettingsExpanded",
    ],
}

# The comment above showSheveryNotice argues for the behaviour being replaced.
COMMENT_FROM = """    // Opened from the caution beside the Shevery option, and again every time that option is
    // picked. Plain remember rather than rememberSaveable, and deliberately: a rotation with
    // this open drops the pending choice, which is the safe direction - nothing is committed.
"""

COMMENT_TO = """    // Opened from the caution beside the Shevery option, and again every time that option is
    // picked. Saved rather than remembered: it used to be dropped on rotation on the grounds
    // that losing an uncommitted choice is the safe direction, which is true and is not the
    // point - a dialog that vanishes when the phone turns reads as the app having crashed,
    // whether or not it took anything with it. pendingFork below is saved for the same reason
    // and has to be, or the dialog would come back asking about a choice that no longer exists.
"""


def declaration(name):
    """
    `var <name> by remember` — with or without keys, one line or several.

    The lookahead is what keeps this from matching `rememberSaveable`, `rememberCoroutineScope`
    and the rest: what follows has to be the opening of a lambda or an argument list. The `\\s*`
    is not decoration - `remember { … }` carries a space and `remember(key) { … }` does not.
    """
    return re.compile(r"(\bvar %s by )remember(?=\s*[({])" % re.escape(name))


def main():
    print("ROOT = %s" % ROOT)

    errors = []
    pending = {}

    for rel, names in TARGETS.items():
        path = os.path.join(ROOT, rel)

        if not os.path.exists(path):
            errors.append("%s: missing" % rel)

            continue

        text = open(path, encoding="utf-8").read()

        for name, expected in sorted(names.items()):
            pattern = declaration(name)

            found = len(pattern.findall(text))

            if found != expected:
                errors.append(
                    "%s: `var %s by remember` matched %d times, expected %d"
                    % (rel, name, found, expected)
                )

                continue

            text = pattern.sub(r"\1rememberSaveable", text)

        # The import, once, in alphabetical position among the runtime imports.
        if IMPORT not in text:
            anchor = "import androidx.compose.runtime.setValue"

            if text.count(anchor) != 1:
                errors.append("%s: no single `%s` to place the import after" % (rel, anchor))

                continue

            text = text.replace(anchor, IMPORT + "\n" + anchor, 1)

        pending[path] = text

    if errors:
        print("\nREFUSED, nothing written:\n  " + "\n  ".join(errors))

        return 1

    # --- the one comment that now says the opposite of the code -------
    settings = os.path.join(
        ROOT, "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
    )

    if pending[settings].count(COMMENT_FROM) != 1:
        print("\nREFUSED, nothing written:\n  the Shevery comment did not match exactly once")

        return 1

    pending[settings] = pending[settings].replace(COMMENT_FROM, COMMENT_TO, 1)

    # --- validation ---------------------------------------------------
    problems = []

    for rel, names in TARGETS.items():
        text = pending[os.path.join(ROOT, rel)]

        for name, expected in names.items():
            left = len(declaration(name).findall(text))

            if left:
                problems.append("%s: %s still plain remember (%d)" % (rel, name, left))

            saved = len(
                re.findall(r"\bvar %s by rememberSaveable(?=\s*[({])" % re.escape(name), text)
            )

            if saved != expected:
                problems.append(
                    "%s: %s is saveable %d times, expected %d" % (rel, name, saved, expected)
                )

        if text.count(IMPORT) != 1:
            problems.append("%s: %d rememberSaveable imports, expected 1" % (rel, text.count(IMPORT)))

    # Nothing on the keep list may have been swept up.
    for rel, names in KEEP.items():
        path = os.path.join(ROOT, rel)

        text = pending.get(path) or open(path, encoding="utf-8").read()

        for name in names:
            if re.search(r"\bvar %s by rememberSaveable" % re.escape(name), text):
                problems.append("%s: %s was converted and should not have been" % (rel, name))

            if not declaration(name).search(text):
                problems.append("%s: %s is not a plain remember any more" % (rel, name))

    if problems:
        print("\nVALIDATION FAILED, nothing written:\n  " + "\n  ".join(problems))

        return 1

    for path, text in sorted(pending.items()):
        open(path, "w", encoding="utf-8").write(text)

    total = sum(sum(names.values()) for names in TARGETS.values())

    print("\n%d declarations made saveable across %d files" % (total, len(TARGETS)))
    print("%d left as plain remember, on purpose" % sum(len(v) for v in KEEP.values()))

    for rel, names in sorted(TARGETS.items()):
        print("   %-46s %s" % (os.path.basename(rel), ", ".join(sorted(names))))

    return 0


if __name__ == "__main__":
    sys.exit(main())
