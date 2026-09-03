#!/usr/bin/env python3
"""r4c — the manager's unhide button becomes a hide/unhide button, and stops looking disabled.

The author:

    "in the settings manager make the hide button a hide unhide button, which does what the
     hide settings toggle does and show the same colour as revert to default when settings are
     unhidden and says 'Unhide settings' also update the icon for that"

and, from the template questions: two labels and two colours, never greyed; the glyph is his own
Hide settings tile pair rather than new artwork.

### What the button becomes

    nothing hidden     `Hide settings`     secondaryContainer, the Revert to default colour
                                           ic_hidden_glyph, the struck-out eye
                                           press hides

    something hidden   `Unhide settings`   GetoRed, as today
                                           ic_hide_glyph, the open eye, as today
                                           press settles what is outstanding

⚠ **The greyed state goes, and with it the reason [dimmed] existed.** The author asked in r2 for
this button to be greyed with nothing outstanding and to answer with a toast when pressed, which
is why `ActionButton` takes a colour that only *looks* disabled. It is no longer greyed in any
state, so `dimmed` has no caller and comes out - a parameter kept "in case" is one a later
reader has to work out the meaning of.

⚠ **`hide()` and `unhidePending()`, not `toggle()`.** The tile's `toggle()` reads
`settingsHidden` for itself and decides the direction from that; this button's label is decided
by `anythingHidden`, which is `autoHideRunning || settingsHidden` and so can be true when
`settingsHidden` alone is false. Handing the direction to `toggle()` would let the two disagree,
and the way it would show is a button reading `Unhide settings` that hides. One value picks the
label and the call, which is the same argument the `anythingHidden` doc already makes about
never asking the question twice.

⚠ **The unhide direction keeps `unhidePending`.** That was an explicit instruction - this button
answers `'IMD: No hidden settings to restore'` rather than falling back to the configured
defaults the way the tile does. Being able to hide from here does not change what unhiding from
here means.

⚠ **Tracked as `Hiding` for the whole press.** `SettingsHiddenRunner.hide()` does not claim the
tracker - `toggle()` claims it around the call - so a press from here would otherwise leave the
manager's own busy state and the tile flickering between the use cases underneath. Same
treatment `revertToDefault()` gives itself.

⚠ **On the application scope**, for the reason `unhideSettings` and `revertToDefault` are:
opened from the tile or the shortcut, dismissing this dialog finishes the activity and takes the
ViewModel with it, and the work has to outlive that.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/dialog/"
           "AndroidSettingsManagerDialog.kt")
MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")
ROUTE = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
         "SettingsManagerRoute.kt")
STRINGS = "feature/apps/src/main/res/values/strings.xml"

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (STRINGS, [
        (
            """    <string name="unhide_settings">Unhide settings</string>
""",
            """    <string name="unhide_settings">Unhide settings</string>
    <string name="hide_settings">Hide settings</string>
""",
            1,
        ),
    ]),

    (MANAGER, [
        # The parameter doc says what the value now decides, which is both halves of a button
        # rather than the shade of one.
        (
            """    /**
     * Whether anything IMD did is still outstanding — a device-wide hide, per-app records, or
     * an IMD+ run. Decides only how `Unhide settings` is **drawn**; the press runs the same
     * call either way and answers for itself. See the note on [ActionButton].
     */
    anythingHidden: Boolean = false,
""",
            """    /**
     * Whether anything IMD did is still outstanding — a device-wide hide, per-app records, or
     * an IMD+ run.
     *
     * ⚠ **Decides the whole of the first action button: its label, its glyph, its colour and
     * which call the press makes.** One value for all four, deliberately. A button that took
     * its label from one test and its behaviour from another could say `Unhide settings` and
     * hide, which is the one way this control can lie to somebody.
     */
    anythingHidden: Boolean = false,
""",
            1,
        ),
        (
            """    onUnhideSettings: () -> Unit,
""",
            """    onUnhideSettings: () -> Unit,
    onHideSettings: () -> Unit,
""",
            1,
        ),
        # The button itself.
        (
            """                // Unhide first, at the author's instruction. It is the one people reach for,
                // and it is the safe one: it puts back what a hide took, where Revert to
                // default drives the configured list whatever was there before.
                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_hide_glyph,
                    label = stringResource(R.string.unhide_settings),
                    pending = anythingHidden,
                    dimmed = !anythingHidden,
                    onClick = onUnhideSettings,
                )
""",
            """                // Hide and unhide in one button, at the author's instruction, and it is
                // first for the reason unhide alone was: it is the one people reach for, and
                // it is the reversible one — it puts back what a hide took, where Revert to
                // default drives the configured list whatever was there before.
                //
                // ⚠ **The glyph names the outcome, not the mechanism.** Press the struck-out
                // eye and the settings end up hidden; press the open one and they end up
                // visible. That reading is `_v3_fav_hide_glyph.py`'s, settled in r2e for the
                // open eye alone, and its sibling now follows it.
                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = if (anythingHidden) {
                        designR.drawable.ic_hide_glyph
                    } else {
                        designR.drawable.ic_hidden_glyph
                    },
                    label = if (anythingHidden) {
                        stringResource(R.string.unhide_settings)
                    } else {
                        stringResource(R.string.hide_settings)
                    },
                    pending = anythingHidden,
                    onClick = if (anythingHidden) onUnhideSettings else onHideSettings,
                )
""",
            1,
        ),
        # `dimmed` has no caller left. The doc that explained it goes with it.
        (
            """ * ### The three colour pairs
 *
 * [pending] and [dimmed] are complements on the one button that uses them — `Unhide settings`
 * is red when something is outstanding and greyed when nothing is, with no neutral state in
 * between, because the button has no neutral meaning. `Revert to default` passes neither and
 * stays tonal, because it always has something to do.
 *
 * ⚠ **[dimmed] does not disable anything.** The author asked for the unhide button to be greyed
 * out with nothing outstanding *and* to answer with a toast when pressed, which a disabled
 * control cannot do — it swallows the press in silence, which is this screen's least legible
 * failure and the reason the unusable switches above are wrapped rather than disabled. So this
 * takes the press whatever colour it is wearing, and the call underneath — `unhidePending` — is
 * the single thing that decides whether there was anything to do. Two tests that could disagree
 * would be one too many.
 *""",
            """ * ### The two colour pairs
 *
 * [pending] is red, for the hide/unhide button with something outstanding. Everything else is
 * tonal: that same button offering to hide, and `Revert to default`, which always has something
 * to do and so has never had a second shade.
 *
 * ⚠ **There is no greyed state any more, and its parameter is gone with it.** r2 asked for the
 * unhide button to be greyed with nothing outstanding *and* to answer with a toast when
 * pressed, which a disabled control cannot do, so this took a colour that only looked disabled.
 * r4c replaced that state with an offer to hide, in the same tonal shade as its neighbour, and
 * a `dimmed` kept for no caller would be a parameter the next reader has to work out.
 *""",
            1,
        ),
        (
            """    pending: Boolean = false,
    dimmed: Boolean = false,
""",
            """    pending: Boolean = false,
""",
            1,
        ),
        (
            """    // Subjectless `when`, deliberately: `check16_when` reads `when (x)` against an enum's
    // labels, and these are two independent booleans rather than one state with three names.
    //
    // The dimmed pair is Material's own disabled palette, restated rather than borrowed from
    // ButtonDefaults — they are the colours a genuinely disabled button would take, and the
    // whole point of this control is that it looks disabled without being it.
    val container = when {
        pending -> GetoRed
        dimmed -> MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
        else -> MaterialTheme.colorScheme.secondaryContainer
    }

    val content = when {
        pending -> Color.White
        dimmed -> MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
        else -> MaterialTheme.colorScheme.onSecondaryContainer
    }
""",
            """    val container = if (pending) {
        GetoRed
    } else {
        MaterialTheme.colorScheme.secondaryContainer
    }

    val content = if (pending) {
        Color.White
    } else {
        MaterialTheme.colorScheme.onSecondaryContainer
    }
""",
            1,
        ),
    ]),

    (MANAGER_VM, [
        (
            """    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }
""",
            """    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }

    /**
     * Hide, from the same button that unhides.
     *
     * ⚠ **`hide()` rather than the tile's `toggle()`.** `toggle()` reads `settingsHidden` and
     * picks a direction from it; the button's label is picked from [anythingHidden], which is
     * `autoHideRunning || settingsHidden` and can be true where that is false. Two tests would
     * eventually disagree, and the way it would show is a button reading `Unhide settings`
     * that hides. The screen decides the direction once and calls the matching half.
     *
     * ⚠ **Claimed as [SettingsWorkKind.Hiding] for the whole press**, because
     * [SettingsHiddenRunner.hide] does not claim the tracker for itself — `toggle()` wraps it.
     * Without this the manager's own busy state and the tile would flicker between the use
     * cases underneath, which is exactly what `revertToDefault` claims to avoid.
     *
     * The runner posts the revert notification and says `'Settings hidden'` itself, on the one
     * test that means the device may actually have changed. Nothing to add here.
     *
     * On the application scope for the reason [unhideSettings] is: opened from the tile or the
     * shortcut, this dialog's dismissal finishes the activity and takes this ViewModel with
     * it, and the work must outlive that.
     */
    fun hideSettings() {
        appScope.launch {
            settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
                settingsHiddenRunner.hide()
            }
        }
    }
""",
            1,
        ),
    ]),

    (ROUTE, [
        (
            """        onUnhideSettings = viewModel::unhideSettings,
""",
            """        onUnhideSettings = viewModel::unhideSettings,
        // The other half of the same button. Which one a press reaches is decided by
        // `anythingHidden`, one floor up, from the value that also picks the label.
        onHideSettings = viewModel::hideSettings,
""",
            1,
        ),
    ]),
]

# `SettingsWorkKind` may or may not be imported already; added only if it is not.
VM_IMPORT = ("import com.android.geto.domain.usecase.SettingsWorkKind\n",
             "import com.android.geto.domain.usecase.SettingsWorkTracker\n")


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

    view_model = staged.get(ROOT / MANAGER_VM, "")

    if VM_IMPORT[0] not in view_model:
        anchor = VM_IMPORT[1]

        if view_model.count(anchor) != 1:
            problems.append(f"{MANAGER_VM}: cannot place the SettingsWorkKind import")
        else:
            # Alphabetical: SettingsWorkKind sorts before SettingsWorkTracker.
            staged[ROOT / MANAGER_VM] = view_model.replace(anchor, VM_IMPORT[0] + anchor, 1)
            view_model = staged[ROOT / MANAGER_VM]

    manager = staged.get(ROOT / MANAGER, "")

    # ⚠ **Asserted against code, not against prose.** A first draft of this script tested for
    # the bare word `dimmed` and for `SettingsWorkKind.Hiding`, and tripped on its own new
    # comments explaining why each was going away. Every token below is spelled the way it can
    # only appear in a statement.
    for token, expected in (
        ("dimmed = ", 0),
        ("    dimmed: Boolean", 0),
        ("dimmed ->", 0),
        # Both alphas stay: MasterPill's disabled state still uses them, so each keeps one use
        # and one declaration. Only the button's use goes.
        ("DIMMED_CONTAINER_ALPHA", 2),
        ("DIMMED_CONTENT_ALPHA", 2),
        ("ic_hidden_glyph", 1),
        ("R.string.hide_settings", 1),
        ("onHideSettings", 2),
    ):
        if manager.count(token) != expected:
            problems.append(f"{MANAGER}: expected {expected} of {token!r}, "
                            f"found {manager.count(token)}")

    # The two alphas still belong to MasterPill, so neither declaration may have been orphaned.
    if "private const val DIMMED_CONTAINER_ALPHA" not in manager:
        problems.append(f"{MANAGER}: the pill's disabled palette went with the button's")

    # The new glyph has to exist, or the button is a build failure rather than a plain one.
    if not (ROOT / "design-system/src/main/res/drawable/ic_hidden_glyph.xml").exists():
        problems.append("design-system: ic_hidden_glyph is missing — run _v3_hidden_glyph.py")

    if view_model.count("kind = SettingsWorkKind.Hiding") != 1:
        problems.append(f"{MANAGER_VM}: the hide is not claimed as Hiding exactly once")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

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

    print("ok - one button, two labels, two colours, two glyphs, and no greyed state")

    return 0


if __name__ == "__main__":
    sys.exit(main())
