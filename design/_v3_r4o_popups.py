#!/usr/bin/env python3
"""v3-r4o — two pop-ups out, one in, and the Shevery red line names IMD+.

Four of the author's reports, all about what a dialog says or whether it should exist at all:

    "remove the popup when i check shizuku service checkbox in default settings to hide"
    "remove the popup that shows after first app setup about 'no need to hide developer
     settings...' one"
    "when within auto hide dialog when autounhide toggle is clicked it does not tell user
     anything if it is uable to be toggled on due to permissions, please give it a popup to say
     'Please grant required permissions first'"
    "in shevery dialog add to the red line which tell whats not supported 'IMD+' like both
     setting above and IMD+"

---

## 1. The Shizuku service checkbox pop-up

`ShizukuServiceNoticeDialog` and everything that raised it. Its two strings stay declared —
translations are frozen — with a comment saying nothing shows them.

## 2. The developer-options tip after setup

`TipDialog` and its branch in `MainActivity`. The file goes; `tip_developer_options` and
`tip_got_it` stay declared for the same reason, and so do `UserData.tipShown` and
`MainActivityViewModel.markTipShown` — nothing reads them now, and the r2i principle is to leave
a declaration rather than churn the datastore for a field that costs a byte.

## 3. ⚠ The auto-unhide switch was not silent — it was saying the wrong thing

Worth stating precisely, because the report says *"does not tell user anything"*. The page's
switch **does** raise a pop-up: `SettingsScreen.kt:1360` routes it to `AutoUnhideBlockedDialog`.
What it says is `'Please setup Auto unhide settings first'` — read by somebody who is standing on
the Auto unhide settings page doing exactly that, while the real blocker is a permission granted
somewhere else entirely. So it tells them nothing *useful*, which is the same thing from where
they are sitting.

The fix is his: a second sentence for the permissions case. Which one is shown is decided by a
new `AutoUnhideRequirements.permissionsSatisfied` — the four terms that are not the user's own
ticks — so the two questions are asked in one place rather than at each call site.

⚠ **All three raise sites take it, not just the one he reported.** The settings-list switch and
the page's switch describe the same state; two different sentences for one condition is the
drift this project keeps finding.

## 4. The Shevery red line

Point 5 of *How this works*, bold and red. ⚠ **The insertion is mine and needs his eye** — the
sentence is his and I am adding three words to it:

    before: Hiding-unhiding for app launches is not supported for both settings mentioned above.
    after:  Hiding-unhiding for app launches is not supported for both settings mentioned above
            and IMD+.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HIDE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SettingsToHideDialog.kt"
TIP = "app/src/main/kotlin/com/android/geto/onboarding/TipDialog.kt"
ACTIVITY = "app/src/main/kotlin/com/android/geto/activity/main/MainActivity.kt"
MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/AutoUnhide.kt"
DIALOGS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoUnhideDialogs.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
APP_STRINGS = "app/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# 1 — the Shizuku service checkbox pop-up
# ---------------------------------------------------------------------------------------
edit(
    HIDE,
    "the notice state",
    """    // Raised when the Shizuku row is ticked - see the row itself for why the warning cannot
    // wait until the hide fails.
    var showShizukuServiceNotice by rememberSaveable { mutableStateOf(false) }

""",
    "",
)

edit(
    HIDE,
    "the notice render",
    """    if (showShizukuServiceNotice) {
        ShizukuServiceNoticeDialog(
            onDismissRequest = { showShizukuServiceNotice = false },
        )
    }

""",
    "",
)

edit(
    HIDE,
    "the row's raise",
    """            onCheckedChange = { wanted ->
                toggle(ManualRevertTarget.Shizuku, wanted)

                // Only on the way on, and only then. Both forks need something switched
                // in their own app before IMD can drive their service, and neither says
                // so anywhere the user would look - the failure is silent and arrives
                // later, at the moment a hide is supposed to work.
                if (wanted) showShizukuServiceNotice = true
            },""",
    """            // ⚠ **No pop-up on the way on any more, at the author's instruction.** It used
            // to raise a notice about each fork's own app settings every time this was
            // ticked. The same two sentences are still reachable from the fork setup dialogs
            // in Shizuku configuration, which is where a fork is chosen and where they
            // belong; here they interrupted a checkbox.
            onCheckedChange = { toggle(ManualRevertTarget.Shizuku, it) },""",
)

edit(
    HIDE,
    "the notice composable",
    """/**
 * What each Shizuku fork needs switched in its *own* app before IMD can drive its service.
 *
 * Raised the moment the Shizuku box is ticked rather than left as a note under it, because
 * neither fork tells the user any of this and both failures are silent: with thedjchi's
 * watchdog left on, the service is restarted from under IMD and USB debugging never goes away;
 * with Shevery's error reporting left off, IMD is never told the service stopped and cannot
 * bring it back on the unhide. Both surface as "hiding does not work", minutes later, with
 * nothing on screen connecting it to this checkbox.
 *
 * One popup covering both forks rather than one per fork: the fork is configured elsewhere and
 * can be changed afterwards, so a notice keyed to whichever is selected right now would be
 * wrong for the user who switches later.
 */
@Composable
private fun ShizukuServiceNoticeDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.shizuku_service_notice_watchdog),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(10.dp))

            Text(
                text = stringResource(R.string.shizuku_service_notice_shevery),
                style = MaterialTheme.typography.bodyMedium,
            )

            Spacer(modifier = Modifier.height(12.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.understood))
                }
            }
        }
    }
}
""",
    "",
)

edit(
    STRINGS,
    "the orphaned notice strings",
    """    <string name="shizuku_service_notice_watchdog">""",
    """    <!-- ⚠ Unshown since r4o, when the author removed the pop-up the Shizuku service
      checkbox raised. Left declared because eleven locale copies exist and translations are
      frozen; the same two facts are still told by the fork setup dialogs. -->
    <string name="shizuku_service_notice_watchdog">""",
)

# ---------------------------------------------------------------------------------------
# 2 — the developer-options tip
# ---------------------------------------------------------------------------------------
edit(
    ACTIVITY,
    "the tip branch",
    """                                    } else if (!uiState.userData.tipShown) {
                                        TipDialog(onDismissRequest = viewModel::markTipShown)
                                    } else if (!uiState.userData.obtainiumTipShown) {""",
    """                                    } else if (!uiState.userData.obtainiumTipShown) {""",
)

edit(
    ACTIVITY,
    "the tip import",
    """import com.android.geto.onboarding.TipDialog
""",
    "",
)

edit(
    APP_STRINGS,
    "the orphaned tip strings",
    """    <string name="tip_got_it">Got it</string>""",
    """    <!-- ⚠ Unshown since r4o, when the author removed the tip after setup. Left declared
      because their locale copies are frozen along with every other translation. -->
    <string name="tip_got_it">Got it</string>""",
)

# ---------------------------------------------------------------------------------------
# 3 — the auto-unhide switch says which kind of blocked it is
# ---------------------------------------------------------------------------------------
edit(
    MODEL,
    "permissionsSatisfied",
    """    /** Whether auto unhide may be switched on right now. */""",
    """    /**
     * Whether everything auto unhide needs from *outside* the app is in place.
     *
     * ⚠ **The four terms that are not the user's own ticks**, held apart from [satisfied] so a
     * blocked switch can say which kind of blocked it is. Telling somebody standing on the Auto
     * unhide settings page to "set up Auto unhide settings" is no answer when what is actually
     * missing is a permission granted somewhere else.
     */
    val permissionsSatisfied: Boolean
        get() = dumpSatisfied && usageSatisfied && batteryUnrestricted && notificationsAllowed

    /** Whether auto unhide may be switched on right now. */""",
)

edit(
    STRINGS,
    "the permissions sentence",
    """    <string name="auto_unhide_blocked">""",
    """    <string name="auto_unhide_permissions_blocked">Please grant required permissions first</string>
    <string name="auto_unhide_blocked">""",
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4n: the developer's note, its bullets and its notification.""",
    """    # r4o: the auto-unhide switch's second refusal.
    "auto_unhide_permissions_blocked",
    # r4n: the developer's note, its bullets and its notification.""",
)

edit(
    DIALOGS,
    "the blocked dialog's message",
    """internal fun AutoUnhideBlockedDialog(
    modifier: Modifier = Modifier,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = stringResource(R.string.auto_unhide_blocked),
                style = MaterialTheme.typography.bodyMedium,
            )""",
    """internal fun AutoUnhideBlockedDialog(
    modifier: Modifier = Modifier,
    /**
     * Which refusal this is.
     *
     * ⚠ **Passed in rather than decided here**, because the caller is the only one holding the
     * requirements — and because the two sentences are answers to two different questions: a
     * permission granted outside the app, or a trigger the user has not ticked yet.
     */
    permissionsMissing: Boolean = false,
    onDismissRequest: () -> Unit,
) {
    DialogContainer(modifier = modifier, onDismissRequest = onDismissRequest) {
        Column(modifier = Modifier.padding(20.dp)) {
            Text(
                text = if (permissionsMissing) {
                    stringResource(R.string.auto_unhide_permissions_blocked)
                } else {
                    stringResource(R.string.auto_unhide_blocked)
                },
                style = MaterialTheme.typography.bodyMedium,
            )""",
)

edit(
    SCREEN,
    "the blocked dialog's render",
    """    if (showAutoUnhideBlocked) {
        AutoUnhideBlockedDialog(onDismissRequest = { showAutoUnhideBlocked = false })
    }""",
    """    if (showAutoUnhideBlocked) {
        AutoUnhideBlockedDialog(
            // ⚠ **Read at the moment it is drawn, not at the moment it was raised.** The page
            // behind this polls the requirements every second, so a permission granted while
            // the pop-up is up would otherwise leave it still naming the permission.
            permissionsMissing = !autoUnhideRequirements.permissionsSatisfied,
            onDismissRequest = { showAutoUnhideBlocked = false },
        )
    }""",
)

# ---------------------------------------------------------------------------------------
# 4 — the Shevery red line
# ---------------------------------------------------------------------------------------
edit(
    STRINGS,
    "the Shevery red line",
    """    <string name="shevery_how_no_launch">Hiding-unhiding for app launches is not supported for both settings mentioned above.</string>""",
    """    <string name="shevery_how_no_launch">Hiding-unhiding for app launches is not supported for both settings mentioned above and IMD+.</string>""",
)

edit(
    CHECK,
    "the Shevery line's deferral",
    """    # r4o: the auto-unhide switch's second refusal.""",
    """    # r4o: the Shevery red line now names IMD+, and the auto-unhide switch's second refusal.
    "shevery_how_no_launch",
    # r4o: the auto-unhide switch's second refusal.""",
)


def main() -> int:
    staged: dict[Path, str] = {}

    for rel, name, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        text = staged.get(path, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[path] = text.replace(old, new, 1)

    tip = ROOT / TIP

    if not tip.is_file():
        print(f"REFUSED: {TIP} is already gone")
        return 1

    # ⚠ **Nothing may still name either removed dialog.** Spelled as the call and the import
    # they can only be, because the replacement comments discuss both in prose.
    for rel, spellings in (
        (HIDE, ("ShizukuServiceNoticeDialog(", "showShizukuServiceNotice")),
        (ACTIVITY, ("TipDialog(", "onboarding.TipDialog")),
    ):
        text = staged[ROOT / rel]

        for spelling in spellings:
            if spelling in text:
                print(f"REFUSED: {rel} still carries {spelling!r}")
                return 1

    # And nothing anywhere else may reference TipDialog either.
    for path in ROOT.rglob("*.kt"):
        if path == tip:
            continue

        body = staged.get(path) or path.read_text(encoding="utf-8")

        if "TipDialog(" in body and "ObtainiumDialog" not in path.name:
            print(f"REFUSED: {path} still calls TipDialog")
            return 1

    # ⚠ **The strings both removed dialogs used must survive them** — translations are frozen.
    for rel, keys in (
        (STRINGS, ("shizuku_service_notice_watchdog", "shizuku_service_notice_shevery")),
        (APP_STRINGS, ("tip_developer_options", "tip_got_it")),
    ):
        text = staged[ROOT / rel]

        for key in keys:
            if f'<string name="{key}">' not in text:
                print(f"REFUSED: {key} was deleted; its translations are frozen")
                return 1

    # The author's new sentence, character for character.
    strings = staged[ROOT / STRINGS]

    value = strings.split('<string name="auto_unhide_permissions_blocked">', 1)[1]
    value = value.split("</string>", 1)[0]

    if value != "Please grant required permissions first":
        print(f"REFUSED: the permissions sentence reads {value!r}")
        return 1

    shevery = strings.split('<string name="shevery_how_no_launch">', 1)[1].split("</string>", 1)[0]

    if not shevery.endswith("mentioned above and IMD+."):
        print(f"REFUSED: the Shevery line reads {shevery!r}")
        return 1

    # ⚠ **The two sentences must be reachable from one place.** A call site that still passes
    # no argument would silently keep the old wording, which is the defect being fixed.
    screen = staged[ROOT / SCREEN]

    if "AutoUnhideBlockedDialog(onDismissRequest" in screen:
        print(f"REFUSED: {SCREEN} still raises the dialog without saying which refusal it is")
        return 1

    if screen.count("permissionsMissing = !autoUnhideRequirements.permissionsSatisfied") != 1:
        print(f"REFUSED: {SCREEN} does not pass the refusal exactly once")
        return 1

    # `permissionsSatisfied` must be a strict subset of `satisfied`'s terms, or the two answers
    # could both be false and the dialog would name the wrong one.
    model = staged[ROOT / MODEL]

    block = model.split("val permissionsSatisfied: Boolean", 1)[1].split("\n\n", 1)[0]

    for term in ("dumpSatisfied", "usageSatisfied", "batteryUnrestricted", "notificationsAllowed"):
        if term not in block:
            print(f"REFUSED: permissionsSatisfied is missing {term}")
            return 1

    for wrong in ("anyTrigger", "anyUsedFor"):
        if wrong in block:
            print(f"REFUSED: permissionsSatisfied includes {wrong}, which is the user's own tick")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    tip.unlink()

    print(f"  ok        {HIDE}  :: the Shizuku checkbox pop-up removed")
    print(f"  ok        {ACTIVITY} / {TIP}  :: the setup tip removed")
    print(f"  ok        {MODEL} / {DIALOGS} / {SCREEN}  :: the permissions refusal")
    print(f"  ok        {STRINGS}  :: Shevery's red line names IMD+")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s), 1 deleted")

    return 0


if __name__ == "__main__":
    sys.exit(main())
