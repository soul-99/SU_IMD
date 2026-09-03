#!/usr/bin/env python3
"""v3-r4n items 1 and 2 — IMD+ requires 'Manage Shizuku', and refuses Shevery outright.

The author, on item 1: *"IMD+ must not work with Shevery — toggle does not turn on, make it a
condition"*, and the requirement row is to read
`'Shizuku configuration in IMD (Shevery not supported)'` with the suffix in red.

On item 2: *"why is imd+ on if manage shizuku is off, should not its shizuku config requirement
also cover it?"*

Both land on the same row, which is why they are one script.

---

## What was wrong

`SettingsScreen.kt` fed the row `shizukuConfigured = userData.isShizukuConfigured` — the fields
being filled in, and nothing else. So:

* with **'Manage Shizuku' off** the row read *met* and IMD+ switched on, while every other gate
  in the app reads `manageShizukuEffective` and would have refused the work;
* on **Shevery** the row read *met* too, and IMD+ switched on for a fork IMD cannot start.

## What this does

`shizukuConfigured` becomes **`shizukuManageable`** and is fed `manageShizukuEffective`, which is
`manageShizuku && isShizukuConfigured` — the same expression every other gate reads. The rename
is not cosmetic: a field called "configured" that also means "and managed" is exactly the drift
`canHide` was introduced to end.

A new **`forkSupported`** carries the fork question on its own, because the row has to tell the
two refusals apart: Manage-Shizuku-off is something to go and switch on, Shevery is not.

⚠ **`forkSupported` is a term of `satisfied` unconditionally — the author's decision, and it
overrides a rule already written into this file.** `shizukuNeeded` is false when
"Do not kill app on first launch" is ticked, and the KDoc argues that a device which asks
Shizuku for nothing may run IMD+ with no Shizuku at all. Put to him in those words; his answer
was **block always**. So the fork term sits outside `shizukuSatisfied`, beside the four
system requirements, rather than inside it.

⚠ **`forkSupported` defaults to `false`, like every other field here.** A default of `true`
would let a caller that forgot it read as "supported", which is the wrong direction for a
requirement. The three host-test fixtures are updated to say so explicitly.

## The string

The row's title is unchanged — `'Shizuku configuration in IMD'`. The author confirmed the spec's
rename to *'Shizuku (Thedjchi) configuration in IMD'* is dead: *"yes the old name because i told
so dont touch Shizuku config setting section title"*.

The suffix is a **second resource**, appended with a space at draw time, because only the suffix
is red — his answer when asked how much of the row goes red. Splitting a sentence across
resources for per-span styling is the pattern `shizuku_rikka_name_*` already uses. The script
asserts `title + " " + suffix` is exactly his verbatim sentence, so the split cannot drift from
what he wrote.

⚠ **No leading space in the resource.** aapt strips leading and trailing whitespace from an
unquoted string, so the space is added in code — the same trap `_v25_wording_6.py` records for
the contributor separators.

English only; the key joins `check_translations.py`'s `DEFERRED` set.

Every edit asserts its anchor matches exactly once, and the assertions below check position and
absence as well as presence. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/AutoHide.kt"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
PAGE = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHidePage.kt"
STRINGS = "feature/settings/src/main/res/values/strings.xml"
CHECK = "tools/check_translations.py"
TESTS = "tools/host-tests/DomainLogicTests.kt"

TITLE = "Shizuku configuration in IMD"
SUFFIX = "(Shevery not supported)"
VERBATIM = "Shizuku configuration in IMD (Shevery not supported)"

EDITS: list[tuple[str, str, str, str]] = []


def edit(rel: str, name: str, old: str, new: str) -> None:
    EDITS.append((rel, name, old, new))


# ---------------------------------------------------------------------------------------
# 1 — the model
# ---------------------------------------------------------------------------------------
edit(
    MODEL,
    "the shizukuConfigured field",
    """    /** Every field of the chosen fork is filled in under IMD's own Shizuku settings. */
    val shizukuConfigured: Boolean = false,""",
    """    /**
     * Shizuku is configured **and** 'Manage Shizuku' is on — `UserData.manageShizukuEffective`.
     *
     * ⚠ **Not `isShizukuConfigured`, which is what this used to be fed.** With the master
     * switch off, every other gate in the app refuses to touch Shizuku while this row read
     * "met" and let IMD+ switch on: *"why is imd+ on if manage shizuku is off, should not its
     * shizuku config requirement also cover it?"* Named for what it means so the two cannot
     * drift apart again.
     */
    val shizukuManageable: Boolean = false,
    /**
     * The chosen fork answers start-stop intents — that is, it is Thedjchi.
     *
     * ⚠ **Its own field rather than folded into [shizukuManageable]**, because the row has to
     * tell the two refusals apart: 'Manage Shizuku' off is something the user can go and
     * switch on, and Shevery is not. The page reads this to decide whether to say so in red.
     */
    val forkSupported: Boolean = false,""",
)

edit(
    MODEL,
    "shizukuSatisfied",
    """    /**
     * Whether Shizuku's side of the requirements is met.
     *
     * The configuration is always required when Shizuku is needed at all — without it IMD does
     * not know which fork to start. The permission is required only when it could actually be
     * read: see [shizukuUnreachable].
     */
    val shizukuSatisfied: Boolean
        get() = !shizukuNeeded ||
            (shizukuConfigured && (shizukuPermission || shizukuUnreachable))""",
    """    /**
     * Whether Shizuku's side of the requirements is met.
     *
     * The configuration is always required when Shizuku is needed at all — without it IMD does
     * not know which fork to start. The permission is required only when it could actually be
     * read: see [shizukuUnreachable].
     *
     * ⚠ **[forkSupported] is deliberately not part of this.** It is not conditional on the
     * kill checkbox — see [satisfied].
     */
    val shizukuSatisfied: Boolean
        get() = !shizukuNeeded ||
            (shizukuManageable && (shizukuPermission || shizukuUnreachable))""",
)

edit(
    MODEL,
    "satisfied",
    """    /** Whether IMD+ may be switched on right now. */
    val satisfied: Boolean
        get() = accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            shizukuSatisfied""",
    """    /**
     * Whether IMD+ may be switched on right now.
     *
     * ⚠ **[forkSupported] sits here, outside [shizukuSatisfied], and that is a decision rather
     * than an oversight.** Inside, it would only apply when a kill is wanted — and a Shevery
     * user who ticks "Do not kill app on first launch" asks Shizuku for nothing, so IMD+ would
     * run. The author was asked in those words and chose to block always: *"Also strip the
     * ability to use shevery for IMD+."* This overrides the argument in [shizukuNeeded]'s KDoc
     * that a device needing no Shizuku may run IMD+ with none.
     */
    val satisfied: Boolean
        get() = accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            forkSupported &&
            shizukuSatisfied""",
)

edit(
    MODEL,
    "onlyAccessibilityMissing",
    """    val onlyAccessibilityMissing: Boolean
        get() = !accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            shizukuSatisfied
}""",
    """    val onlyAccessibilityMissing: Boolean
        get() = !accessibilityEnabled &&
            batteryUnrestricted &&
            notificationsAllowed &&
            appsChosen &&
            // ⚠ The same term [satisfied] gained, and for the same reason: offering to switch
            // the detector on for a fork IMD+ will refuse anyway is offering nothing.
            forkSupported &&
            shizukuSatisfied
}""",
)

# ---------------------------------------------------------------------------------------
# 2 — where the requirements are assembled
# ---------------------------------------------------------------------------------------
edit(
    SCREEN,
    "the requirements construction",
    """        shizukuUnreachable = !autoHide.serviceState.shizukuRunning,
        shizukuConfigured = userData.isShizukuConfigured,""",
    """        shizukuUnreachable = !autoHide.serviceState.shizukuRunning,
        // ⚠ **manageShizukuEffective, not isShizukuConfigured.** The master switch is part of
        // the question now - r4n item 2 - and this is the expression every other gate reads.
        shizukuManageable = userData.manageShizukuEffective,
        // Thedjchi only: IMD+ has to be able to bring the service up on demand, and a fork
        // with no start intent cannot be.
        forkSupported = userData.shizukuForkMode.supportsIntents,""",
)

# ---------------------------------------------------------------------------------------
# 3 — the row itself
# ---------------------------------------------------------------------------------------
edit(
    PAGE,
    "the row's imports",
    """import androidx.compose.ui.text.style.TextDecoration""",
    """import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.style.TextDecoration
import androidx.compose.ui.text.withStyle""",
)

edit(
    PAGE,
    "the AutoHideRequirementRow signature",
    """internal fun AutoHideRequirementRow(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    met: Boolean,
    optional: Boolean = false,""",
    """internal fun AutoHideRequirementRow(
    modifier: Modifier = Modifier,
    title: String,
    /**
     * Appended to [title] after a space, in the error colour.
     *
     * ⚠ **Two resources for one sentence, on purpose.** The author asked for the suffix alone
     * to be red, and a single string cannot carry two colours. `title + " " + suffix` is
     * asserted in `design/_v3_r4n_imd_plus_gate.py` to be his sentence exactly, so the split
     * cannot drift from what he wrote. The space is added here because aapt strips leading
     * whitespace from an unquoted string resource.
     */
    titleSuffix: String? = null,
    subtitle: String,
    met: Boolean,
    optional: Boolean = false,""",
)

# ⚠ **Anchored from the busy branch, not from the Column.** The first draft anchored on
# `Column(modifier = Modifier.weight(1f)) {` plus the two Texts under it and matched TWICE:
# `AutoHideInfoRow` above has the identical shape. The `if (busy)` / `StatusDot(met, optional)`
# pair belongs to this row alone.
edit(
    PAGE,
    "the row's title Text",
    """        if (busy) {
            CircularProgressIndicator(modifier = Modifier.size(12.dp), strokeWidth = 2.dp)
        } else {
            StatusDot(met = met, optional = optional)
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }""",
    """        if (busy) {
            CircularProgressIndicator(modifier = Modifier.size(12.dp), strokeWidth = 2.dp)
        } else {
            StatusDot(met = met, optional = optional)
        }

        Spacer(modifier = Modifier.width(12.dp))

        Column(modifier = Modifier.weight(1f)) {
            Text(
                // One paragraph rather than two Texts, so the suffix wraps with the title
                // instead of being pushed onto a line of its own on a narrow screen.
                text = buildAnnotatedString {
                    append(title)

                    if (titleSuffix != null) {
                        append(" ")

                        withStyle(SpanStyle(color = MaterialTheme.colorScheme.error)) {
                            append(titleSuffix)
                        }
                    }
                },
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(4.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }""",
)

edit(
    PAGE,
    "the Shizuku configuration row",
    """        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_shizuku_configured),
            subtitle = stringResource(R.string.auto_hide_req_shizuku_configured_note),
            met = requirements.shizukuConfigured,
            optional = !requirements.shizukuNeeded,
            onClick = onOpenShizukuSettings,
        )""",
    """        AutoHideRequirementRow(
            title = stringResource(R.string.auto_hide_req_shizuku_configured),
            // Only on a fork IMD cannot drive. Nothing to go and configure, so it says so
            // rather than sending the reader to a screen that cannot help them.
            titleSuffix = if (requirements.forkSupported) {
                null
            } else {
                stringResource(R.string.auto_hide_req_shizuku_shevery)
            },
            subtitle = stringResource(R.string.auto_hide_req_shizuku_configured_note),
            met = requirements.shizukuManageable && requirements.forkSupported,
            // ⚠ **Greyed as optional only while the fork is one IMD can drive.** On Shevery
            // this requirement is not optional at any setting of the kill checkbox - see
            // AutoHideRequirements.satisfied - so greying it there would say the opposite of
            // why the switch will not move. The permission row above keeps the plain rule,
            // because a permission really is unnecessary once nothing is killed.
            optional = !requirements.shizukuNeeded && requirements.forkSupported,
            onClick = onOpenShizukuSettings,
        )""",
)

# ---------------------------------------------------------------------------------------
# 4 — the string, and its deferral
# ---------------------------------------------------------------------------------------
edit(
    STRINGS,
    "the suffix string",
    f'    <string name="auto_hide_req_shizuku_configured">{TITLE}</string>',
    f'    <string name="auto_hide_req_shizuku_configured">{TITLE}</string>\n'
    f'    <!-- Appended to the row above after a space, in the error colour. The two together\n'
    f'      are the author\'s sentence: "{VERBATIM}" -->\n'
    f'    <string name="auto_hide_req_shizuku_shevery">{SUFFIX}</string>',
)

edit(
    CHECK,
    "the DEFERRED set",
    """    # r4n: the revert row's two-line label, and the two IMD+ flow steps.""",
    """    # r4n: the IMD+ requirement row's Shevery suffix.
    "auto_hide_req_shizuku_shevery",
    # r4n: the revert row's two-line label, and the two IMD+ flow steps.""",
)

# ---------------------------------------------------------------------------------------
# 5 — the host tests
# ---------------------------------------------------------------------------------------
edit(
    TESTS,
    "the asleep fixture",
    """    val asleep = AutoHideRequirements(
        shizukuPermission = false,
        shizukuUnreachable = true,
        shizukuConfigured = true,
        accessibilityEnabled = true,""",
    """    val asleep = AutoHideRequirements(
        shizukuPermission = false,
        shizukuUnreachable = true,
        shizukuManageable = true,
        // ⚠ Stated rather than defaulted. r4n made the fork a requirement in its own right and
        // the field defaults to false, so a fixture that omitted it would fail for the wrong
        // reason and hide whatever it was actually testing.
        forkSupported = true,
        accessibilityEnabled = true,""",
)

edit(
    TESTS,
    "the unconfigured-Shizuku assertion",
    """    check(
        "an unreachable Shizuku with no configuration does not",
        !asleep.copy(shizukuConfigured = false).satisfied,
    )""",
    """    check(
        "an unreachable Shizuku with no configuration does not",
        !asleep.copy(shizukuManageable = false).satisfied,
    )

    // r4n item 1. Unconditional, and asserted at both settings of the kill checkbox — the
    // author's decision, and the one thing about this gate that is easy to get wrong.
    check(
        "Shevery is never satisfied, kill wanted",
        !asleep.copy(forkSupported = false).satisfied,
    )

    check(
        "Shevery is never satisfied, kill not wanted either",
        !asleep.copy(forkSupported = false, noKillOnLaunch = true).satisfied,
    )

    // r4n item 2. 'Manage Shizuku' off is a refusal on a fork that would otherwise work.
    check(
        "Manage Shizuku off is not satisfied on Thedjchi",
        !asleep.copy(shizukuManageable = false).satisfied,
    )""",
)

edit(
    TESTS,
    "the withoutShizuku fixture",
    """    val withoutShizuku = AutoHideRequirements(
        accessibilityEnabled = true,
        batteryUnrestricted = true,
        notificationsAllowed = true,
        appsChosen = true,
        noKillOnLaunch = true,
    )""",
    """    val withoutShizuku = AutoHideRequirements(
        accessibilityEnabled = true,
        batteryUnrestricted = true,
        notificationsAllowed = true,
        appsChosen = true,
        forkSupported = true,
        noKillOnLaunch = true,
    )""",
)

edit(
    TESTS,
    "the fork term in the no-kill group",
    """    check("no apps chosen is never satisfied", !withoutShizuku.copy(appsChosen = false).satisfied)""",
    """    check("no apps chosen is never satisfied", !withoutShizuku.copy(appsChosen = false).satisfied)

    // r4n: the fifth member of that group, and the reason it is in it. "No Shizuku at all" is
    // still not "any fork at all".
    check(
        "an unsupported fork is never satisfied, even with no kill wanted",
        !withoutShizuku.copy(forkSupported = false).satisfied,
    )""",
)

edit(
    TESTS,
    "the onlyAccessibilityMissing fixture",
    """        notificationsAllowed = true,
        appsChosen = true,
        noKillOnLaunch = true,
    )

    check("only the detector missing is recognised", ready.onlyAccessibilityMissing)""",
    """        notificationsAllowed = true,
        appsChosen = true,
        forkSupported = true,
        noKillOnLaunch = true,
    )

    check("only the detector missing is recognised", ready.onlyAccessibilityMissing)

    // r4n: offering to switch the detector on for a fork IMD+ will refuse anyway is offering
    // nothing, so the fork is a term of this too.
    check(
        "an unsupported fork stops it",
        !ready.copy(forkSupported = false).onlyAccessibilityMissing,
    )""",
)

edit(
    TESTS,
    "the ready-Shizuku assertion",
    """        needsShizuku.copy(
            shizukuConfigured = true,
            shizukuPermission = true,
        ).onlyAccessibilityMissing,""",
    """        needsShizuku.copy(
            shizukuManageable = true,
            shizukuPermission = true,
        ).onlyAccessibilityMissing,""",
)

edit(
    TESTS,
    "the unreachable-Shizuku assertion",
    """        needsShizuku.copy(
            shizukuConfigured = true,
            shizukuUnreachable = true,
        ).onlyAccessibilityMissing,""",
    """        needsShizuku.copy(
            shizukuManageable = true,
            shizukuUnreachable = true,
        ).onlyAccessibilityMissing,""",
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

    # ⚠ **The split sentence must reassemble into his exact words.** The whole reason the
    # suffix is a separate resource is the red span; if the two halves ever stop adding up to
    # what he wrote, the row is showing a sentence he did not write.
    strings = staged[ROOT / STRINGS]

    def value(key: str) -> str:
        return strings.split(f'<string name="{key}">', 1)[1].split("</string>", 1)[0]

    rebuilt = value("auto_hide_req_shizuku_configured") + " " + value(
        "auto_hide_req_shizuku_shevery",
    )

    if rebuilt != VERBATIM:
        print(f"REFUSED: the two halves rebuild to {rebuilt!r}, not {VERBATIM!r}")
        return 1

    if value("auto_hide_req_shizuku_shevery").strip() != SUFFIX:
        print("REFUSED: the suffix resource carries whitespace aapt would strip")
        return 1

    # ⚠ **`shizukuConfigured` must be gone from the three files that used *this* one.** Spelled
    # the way it can only appear as a named argument or a property read, never as a bare word,
    # because the replacement comments above discuss it by name — the comment trap.
    for rel in (MODEL, PAGE, TESTS):
        text = staged[ROOT / rel]

        for spelling in ("shizukuConfigured =", "requirements.shizukuConfigured"):
            if spelling in text:
                print(f"REFUSED: {rel} still carries {spelling!r}")
                return 1

    # ⚠ **SettingsScreen is scoped to the construction, and the first draft was not.**
    # `shizukuConfigured` is ALSO a parameter of SettingsToHideDialog and RevertDefaultsDialog —
    # a different question ("is the fork configured", which picks the DOOA note) that the author
    # has not asked to change. A file-wide absence check refuses on those two forever, and
    # renaming them to make it pass would be changing two dialogs nobody asked about.
    screen = staged[ROOT / SCREEN]

    start = screen.index("val autoHideRequirements = AutoHideRequirements(")
    end = screen.index("\n    )", start)

    block = screen[start:end]

    if "shizukuConfigured" in block:
        print("REFUSED: the AutoHideRequirements construction still names shizukuConfigured")
        return 1

    for needed in ("shizukuManageable = userData.manageShizukuEffective",
                   "forkSupported = userData.shizukuForkMode.supportsIntents"):
        if needed not in block:
            print(f"REFUSED: the construction does not carry {needed!r}")
            return 1

    # And the two dialog parameters must be exactly as they were — untouched, not renamed.
    if screen.count("shizukuConfigured = userData.isShizukuConfigured") != 2:
        print("REFUSED: the two dialog call sites are no longer intact")
        return 1

    # ⚠ **Position, not presence** (the anchor trap). In the model, the two new fields must sit
    # inside the constructor — before the closing `) {` — and `forkSupported` must appear in
    # `satisfied` *after* `appsChosen`, which is the group it was added to.
    model = staged[ROOT / MODEL]

    ctor_end = model.index("\n) {")

    for field in ("val shizukuManageable:", "val forkSupported:"):
        if not model.index(field) < ctor_end:
            print(f"REFUSED: {field} is outside the constructor")
            return 1

    satisfied = model.index("val satisfied: Boolean")
    only = model.index("val onlyAccessibilityMissing: Boolean")

    for start, end, label in ((satisfied, only, "satisfied"), (only, len(model), "onlyAcc")):
        block = model[start:end]

        if "forkSupported &&" not in block:
            print(f"REFUSED: {label} does not carry the forkSupported term")
            return 1

    # And the page must read the new names, in the row the author asked about.
    page = staged[ROOT / PAGE]

    row = page.index("R.string.auto_hide_req_shizuku_configured")
    suffix_read = page.index("R.string.auto_hide_req_shizuku_shevery")
    note = page.index("R.string.auto_hide_req_shizuku_configured_note")

    if not row < suffix_read < note:
        print("REFUSED: the suffix is not drawn between the title and the note")
        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    print(f"  ok        {MODEL}  :: shizukuManageable, forkSupported")
    print(f"  ok        {SCREEN}  :: manageShizukuEffective + supportsIntents")
    print(f"  ok        {PAGE}  :: red suffix, met and optional re-read")
    print(f"  ok        {STRINGS}  :: auto_hide_req_shizuku_shevery")
    print(f"  ok        {CHECK}  :: key deferred")
    print(f"  ok        {TESTS}  :: 3 fixtures updated, 5 assertions added")
    print(f"\n  row on Shevery: {rebuilt}")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
