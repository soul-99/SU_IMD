#!/usr/bin/env python3
"""v3-r4n — 'Display over other apps to hide' opens only on Thedjchi.

The v3 spec: *"We will only be able to open 'DOOAs to manage' now if thedjchi fo[rk] is selected
under shizuku configuration."* Never built. Put to the author in this round with the code's own
counter-argument attached, and his answer:

    "yes dooa to manage gate it to thedjchi shizuku only should not open in shevery and also
     display the popup we use for dooa when clicked in dialogs when shevery is used to tell user"

So: greyed on any fork but Thedjchi, and a press raises the same `ConfigureFirstDialog` the DOOA
toggles already raise, carrying `dooa_thedjchi_only` and **no path** — there is nothing to go and
configure.

---

## ⚠ The comment this replaces argued against doing it, and the argument does not apply

The row carried:

    Hiding the way to configure something behind a switch that is itself gated on the
    configuration would be a circle.

That is a good objection to gating this picker on `overlayManageable`, because
`overlayManageable` includes *"the picker is not empty"* — gate the picker on that and the user
can never fill it. It is **not** an objection to gating on the fork alone, which is a fact about
the device and cannot be changed from this screen. The distinction was put to the author before
building. The comment is rewritten to say which gate is circular and which is not, so the next
round does not re-derive the objection and undo this.

## ⚠ Greyed, and still clickable

`SettingsColumn` gains `enabled`, which greys the two texts to 38 % — nothing more. The row's own
`clickable` stays live so the press can raise the pop-up. Disabling the whole row would swallow
the press inside its own bounds and leave the one thing a user is most likely to tap saying
nothing, which is the trap `SettingToHideRow`, `TargetRow` and `AppSettingItem` all already work
around.

No new strings: `dooa_thedjchi_only` and `understood` are already in this module, put there for
the toggles in r3.

Asserts every anchor matches exactly once, that the picker is no longer opened unconditionally,
and that the pop-up is raised with an empty path list. Writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

EDITS: list[tuple[str, str, str]] = []


def edit(name: str, old: str, new: str) -> None:
    EDITS.append((name, old, new))


edit(
    "the ConfigureFirstDialog import",
    """import com.android.geto.designsystem.component.DialogContainer""",
    """import com.android.geto.designsystem.component.ConfigureFirstDialog
import com.android.geto.designsystem.component.DialogContainer""",
)

edit(
    "the dialog state",
    """    var showOverlayPackagesDialog by rememberSaveable { mutableStateOf(false) }""",
    """    var showOverlayPackagesDialog by rememberSaveable { mutableStateOf(false) }

    // r4n: raised instead of the picker on a fork that cannot write overlay AppOps.
    var showOverlayForkBlocked by rememberSaveable { mutableStateOf(false) }""",
)

edit(
    "the picker row and the comment above it",
    """            // ⚠ **Shown to everybody since v3**, where it used to appear only once overlay
            // management had been switched on in Advanced. That switch is gone: the DOOA
            // toggles are offered to everyone now and gated on whether they can work, and
            // this picker is one of the three things that decides whether they can. Hiding
            // the way to configure something behind a switch that is itself gated on the
            // configuration would be a circle.
            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.overlay_packages_row),
                subtitle = overlayPackagesSubtitle(
                    overlayPackages = overlayPackages,
                    managed = userData.managedOverlayPackages,
                ),
                onClick = {
                    onRefreshOverlayPackages()

                    showOverlayPackagesDialog = true
                },
            )""",
    """            // ⚠ **Shown to everybody since v3**, where it used to appear only once overlay
            // management had been switched on in Advanced. That switch is gone: the DOOA
            // toggles are offered to everyone now and gated on whether they can work, and
            // this picker is one of the three things that decides whether they can.
            //
            // ⚠ **Gated on the fork, and deliberately not on `overlayManageable` — the two
            // are not the same gate.** `overlayManageable` includes "this picker is not
            // empty", so gating the picker on it would hide the only way to fill it: that is
            // the circle this comment used to warn about, and it still stands. The fork is a
            // fact about the device that cannot be changed from this screen, so gating on it
            // traps nobody. The author's instruction, v3 spec: the picker opens on Thedjchi
            // only.
            SettingsRowDivider()

            SettingsColumn(
                title = stringResource(R.string.overlay_packages_row),
                subtitle = overlayPackagesSubtitle(
                    overlayPackages = overlayPackages,
                    managed = userData.managedOverlayPackages,
                ),
                // Greyed, not disabled. The row keeps its own clickable so the press below
                // can explain itself; a disabled row would swallow it in silence.
                enabled = userData.shizukuForkMode.supportsIntents,
                onClick = {
                    if (userData.shizukuForkMode.supportsIntents) {
                        onRefreshOverlayPackages()

                        showOverlayPackagesDialog = true
                    } else {
                        showOverlayForkBlocked = true
                    }
                },
            )""",
)

edit(
    "the SettingsColumn signature",
    """private fun SettingsColumn(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    onClick: () -> Unit,""",
    """private fun SettingsColumn(
    modifier: Modifier = Modifier,
    title: String,
    subtitle: String,
    /**
     * Whether the row leads anywhere.
     *
     * ⚠ **Appearance only — the row stays clickable.** A greyed row that refuses has to be
     * able to say why, and a `clickable(enabled = false)` would eat the press. Callers that
     * pass false are expected to branch in [onClick] and raise an explanation.
     */
    enabled: Boolean = true,
    onClick: () -> Unit,""",
)

edit(
    "the SettingsColumn body",
    """        Column(modifier = Modifier.weight(1f)) {
            Text(text = title, style = MaterialTheme.typography.bodyLarge)

            Spacer(modifier = Modifier.height(6.dp))

            Text(text = subtitle, style = MaterialTheme.typography.bodySmall)
        }""",
    """        val contentColour = if (enabled) {
            MaterialTheme.colorScheme.onSurface
        } else {
            MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
        }

        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = title,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(6.dp))

            Text(
                text = subtitle,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }""",
)

edit(
    "the blocked dialog",
    """    if (showOverlayPackagesDialog) {""",
    """    // ⚠ **No path line, exactly like the DOOA toggles on this fork.** `ConfigureFirstDialog`
    // takes an empty list here because there is nothing to go and set: Shevery has no
    // start-stop intent, so IMD cannot bring a shell up to write an overlay AppOp at all.
    if (showOverlayForkBlocked) {
        ConfigureFirstDialog(
            message = stringResource(R.string.dooa_thedjchi_only),
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { showOverlayForkBlocked = false },
        )
    }

    if (showOverlayPackagesDialog) {""",
)


def main() -> int:
    path = ROOT / SCREEN

    if not path.is_file():
        print(f"REFUSED: missing {SCREEN}")
        return 1

    text = path.read_text(encoding="utf-8")

    for name, old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {SCREEN}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        if new in text:
            print(f"REFUSED: {SCREEN} already carries {name} — has this run before?")
            return 1

        text = text.replace(old, new, 1)

    # ⚠ **The picker must no longer be opened without asking the fork.** Spelled as the
    # statement it can only be, not as a bare identifier, because the new comment above talks
    # about the picker in prose — the comment trap.
    unconditional = """                onClick = {
                    onRefreshOverlayPackages()

                    showOverlayPackagesDialog = true
                },"""

    if unconditional in text:
        print("REFUSED: the picker is still opened unconditionally")
        return 1

    # ⚠ **Position, not presence** (the anchor trap). The gate has to be read *before* the
    # picker is opened, and the blocked dialog has to be declared before it is rendered.
    row = text.index("enabled = userData.shizukuForkMode.supportsIntents,")
    branch = text.index("showOverlayForkBlocked = true")
    declared = text.index("var showOverlayForkBlocked by rememberSaveable")
    rendered = text.index("if (showOverlayForkBlocked) {")

    if not declared < row < branch < rendered:
        print("REFUSED: the gate, its branch and its dialog are not in order")
        return 1

    # The pop-up must carry no path. `paths` defaults to an empty list, so the assertion is
    # that nothing passes one here — a path pointing at a screen that cannot help would be
    # worse than no path at all.
    block = text[rendered : text.index("if (showOverlayPackagesDialog) {", rendered)]

    if "paths" in block:
        print("REFUSED: the fork pop-up passes a path — there is nothing to configure")
        return 1

    for needed in ("R.string.dooa_thedjchi_only", "R.string.understood"):
        if needed not in block:
            print(f"REFUSED: the fork pop-up does not read {needed}")
            return 1

    # Both strings must exist in this module — neither is new, but a missing one is a build
    # failure the sandbox cannot see.
    strings = (ROOT / "feature/settings/src/main/res/values/strings.xml").read_text(
        encoding="utf-8",
    )

    for key in ("dooa_thedjchi_only", "understood"):
        if f'<string name="{key}">' not in strings:
            print(f"REFUSED: feature/settings has no string named {key}")
            return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}")
    print("  ok        picker gated on Thedjchi; greyed row keeps its press")
    print(f"\nwrote 1 file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
