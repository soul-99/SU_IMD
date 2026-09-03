#!/usr/bin/env python3
"""v3-r4r — the four configuration steps join the setup flow.

    "add a few more pages to initialisation screen after shizuku"
    "all these new initialisation pages including manage shizuku one should only be displayed to
     people with fresh install not updaters"

The flow becomes: Permissions, Shizuku, Accessibility, Display over other apps, Settings to hide,
Auto unhide, Reminders.

## ⚠ Fresh installs only, and there is exactly one honest way to ask

`upgradedToV3` - proto field 69 - is written once by `MigrateFrameworksUseCase`, at the only
moment the app can still tell a fresh install from an upgrade: after that, both look identical.
So the five configuration pages are gated on it, **Shizuku included**, at the author's
instruction.

⚠ **Not `remindersOnly`.** That flag means *"the permissions are already satisfied and only the
reminders are due"*, which is a different question - an upgrade that is missing a permission still
has to be walked through Permissions, and must still not be walked through the configuration.
Reusing it here would have been right most of the time, which is the worst kind of wrong.

## ⚠ Where a page goes when the one after it is absent

Every step's "move on" is [nextAfter], one function that walks forward past whichever steps do not
apply. Written once because there are five hops through four optional pages, and a chain of
`if (a) X else if (b) Y else Z` at each of them is where an unreachable page comes from.

## The DOOA step has two ways to be absent

* **Before it is reached**: Shizuku is not fully configured on a fork that can drive overlay
  access. `overlayStepApplies` answers that from stored values, so the flow simply steps over it.
* **Once it is reached**: the device will not list its overlay packages. Only the step itself can
  know that, so it calls `onUnavailable` and the flow moves on - the author's *"if IMD fails to
  get DOOA list to load skip it"*.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETUP = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

EDITS: list[tuple[str, str]] = [
    # 1. The page constants.
    (
        """/** The reminders, which is where `remindersOnly` opens. */
private const val REMINDERS = 2""",
        """/** The accessibility services IMD may manage — r4r. */
private const val ACCESSIBILITY = 2

/** The apps whose Display over other apps IMD may manage — r4r. */
private const val OVERLAY = 3

/** Which settings a launch hides — r4r. */
private const val SETTINGS_TO_HIDE = 4

/** Auto unhide, whole — r4r. */
private const val AUTO_UNHIDE = 5

/** The reminders, which is where `remindersOnly` opens. */
private const val REMINDERS = 6

/**
 * The next page after [from], stepping over the ones this install has no use for.
 *
 * ⚠ **One function rather than a decision at each hop.** There are five hops through four
 * optional pages, and a chain of `if (a) ... else if (b) ...` written out at each of them is how
 * a page ends up unreachable — or worse, reachable from one direction only.
 *
 * ⚠ **[configuring] gates all five configuration pages, Shizuku included**, on the author's
 * instruction. It is `!upgradedToV3`: an install that existed before v3 has answered these
 * questions already, and asking again would read as the app having forgotten.
 */
private fun nextAfter(from: Int, configuring: Boolean, overlayApplies: Boolean): Int {
    var page = from + 1

    while (page < REMINDERS) {
        val skip = when (page) {
            ACCESSIBILITY, SETTINGS_TO_HIDE, AUTO_UNHIDE -> !configuring

            OVERLAY -> !configuring || !overlayApplies

            // SHIZUKU, and anything added between the two without a rule of its own.
            else -> !configuring
        }

        if (!skip) return page

        page += 1
    }

    return REMINDERS
}""",
    ),
    # 2. The Shizuku page hands on to whatever comes next rather than straight to the reminders.
    (
        """    var page by rememberSaveable { mutableIntStateOf(if (remindersOnly) REMINDERS else PERMISSIONS) }

    when (page) {
        PERMISSIONS -> PermissionsPage(
            modifier = modifier,
            setupState = setupState,
            grantViaShizuku = grantViaShizuku,
            onNext = { page = SHIZUKU },
        )

        SHIZUKU -> ShizukuSetupPage(
            modifier = modifier,
            userData = userData,
            installedApps = installedApps,
            installedAppsRevision = installedAppsRevision,
            onRefreshInstalledApps = onRefreshInstalledApps,
            // ⚠ **Both answers move on.** Skipping is a real answer, and a page that came
            // back after it would be the app refusing to accept one.
            onSave = { forkMode, packageName, startAction, authKey ->
                onSaveShizuku(forkMode, packageName, startAction, authKey)

                page = REMINDERS
            },
            onSkip = { page = REMINDERS },
        )
""",
        """    var page by rememberSaveable { mutableIntStateOf(if (remindersOnly) REMINDERS else PERMISSIONS) }

    // ⚠ **The one question that decides whether any of the configuration is shown**, and the
    // only field that can answer it: see nextAfter. Not `remindersOnly`, which means something
    // else — an upgrade missing a permission still walks through Permissions and still must not
    // walk through the configuration.
    val configuring = !userData.upgradedToV3

    // Read once per composition rather than at each hop, so a Shizuku configuration saved on the
    // page before cannot change the flow's shape underneath a press.
    val overlayApplies = overlayStepApplies(userData = userData)

    val advance = { from: Int ->
        page = nextAfter(from = from, configuring = configuring, overlayApplies = overlayApplies)
    }

    when (page) {
        PERMISSIONS -> PermissionsPage(
            modifier = modifier,
            setupState = setupState,
            grantViaShizuku = grantViaShizuku,
            onNext = { advance(PERMISSIONS) },
        )

        SHIZUKU -> ShizukuSetupPage(
            modifier = modifier,
            userData = userData,
            installedApps = installedApps,
            installedAppsRevision = installedAppsRevision,
            onRefreshInstalledApps = onRefreshInstalledApps,
            // ⚠ **Both answers move on.** Skipping is a real answer, and a page that came
            // back after it would be the app refusing to accept one.
            onSave = { forkMode, packageName, startAction, authKey ->
                onSaveShizuku(forkMode, packageName, startAction, authKey)

                advance(SHIZUKU)
            },
            onSkip = { advance(SHIZUKU) },
        )

        ACCESSIBILITY -> AccessibilityStep(
            modifier = modifier,
            stepTitle = stringResource(R.string.setup_step_accessibility),
            onSkip = { advance(ACCESSIBILITY) },
            onNext = { advance(ACCESSIBILITY) },
        )

        OVERLAY -> OverlayStep(
            modifier = modifier,
            stepTitle = stringResource(R.string.setup_step_overlay),
            onSkip = { advance(OVERLAY) },
            onNext = { advance(OVERLAY) },
            // The device would not list its overlay packages. Nothing to configure, so nothing
            // to show — the author's "if IMD fails to get DOOA list to load skip it".
            onUnavailable = { advance(OVERLAY) },
        )

        SETTINGS_TO_HIDE -> SettingsToHideStep(
            modifier = modifier,
            stepTitle = stringResource(R.string.setup_step_settings_to_hide),
            onSkip = { advance(SETTINGS_TO_HIDE) },
            onNext = { advance(SETTINGS_TO_HIDE) },
        )

        AUTO_UNHIDE -> AutoUnhideStep(
            modifier = modifier,
            stepTitle = stringResource(R.string.setup_step_auto_unhide),
            onSkip = { advance(AUTO_UNHIDE) },
            onNext = { advance(AUTO_UNHIDE) },
        )
""",
    ),
]

IMPORTS = [
    "import com.android.geto.feature.settings.AccessibilityStep",
    "import com.android.geto.feature.settings.AutoUnhideStep",
    "import com.android.geto.feature.settings.OverlayStep",
    "import com.android.geto.feature.settings.SettingsToHideStep",
    "import com.android.geto.feature.settings.overlayStepApplies",
]

AFTER = [
    ("private const val REMINDERS = 6", 1),
    ("private fun nextAfter(", 1),
    ("advance(", 12),
    ("AccessibilityStep(", 1),
    ("OverlayStep(", 1),
    ("SettingsToHideStep(", 1),
    ("AutoUnhideStep(", 1),
    ("overlayStepApplies(", 1),
    ("upgradedToV3", 2),
    # The reminders page is still reached, and is still what remindersOnly opens at.
    ("if (remindersOnly) REMINDERS else PERMISSIONS", 1),
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import com.android.geto.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


def main() -> int:
    path = ROOT / SETUP

    if not path.is_file():
        print(f"REFUSED: missing {SETUP}")
        return 1

    text = path.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {SETUP}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        text = text.replace(old, new, 1)

    for statement in IMPORTS:
        text = add_import(text, statement)

    for token, expected in AFTER:
        found = text.count(token)

        if found != expected:
            print(
                f"REFUSED: {SETUP}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # ⚠ Every page constant must be distinct and in order, or nextAfter walks past a page.
    order = ["PERMISSIONS = 0", "SHIZUKU = 1", "ACCESSIBILITY = 2", "OVERLAY = 3",
             "SETTINGS_TO_HIDE = 4", "AUTO_UNHIDE = 5", "REMINDERS = 6"]

    positions = []

    for name in order:
        if text.count(name) != 1:
            print(f"REFUSED: {SETUP}\n  {name!r} is not declared exactly once")
            return 1

        positions.append(text.index(name))

    if positions != sorted(positions):
        print(f"REFUSED: {SETUP}\n  the page constants are not declared in flow order")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SETUP}  :: seven pages, five of them fresh-install only")
    print("  ok        nextAfter steps over what does not apply")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
