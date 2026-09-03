#!/usr/bin/env python3
"""v3-r4r — the two list dialogs can be setup steps.

    "just use those dialogs with Skip and Next buttons below"

`AccessibilityServicesDialog` and `OverlayPackagesDialog` each gain one parameter, `onSkip`. Null
- which is what Settings passes, by omitting it - and they are exactly what they were. Non-null
and they are a page in the setup flow: flat, and with **Skip** at the left and **Next** at the
right in place of **Cancel** and **Update**.

⚠ **Next is the Update button, renamed.** It runs the same code - `onUpdate...(selected.toList())`
then `onDismissRequest()` - so the draft each dialog already holds is what gets written, and
"Next" cannot come to mean something different from "Update" by drifting away from it.

⚠ **Skip is not Cancel.** Cancel means *close this*; Skip means *move on and write nothing*, which
is the same thing for these two dialogs but is a different callback, because during setup
`onDismissRequest` is what advances the flow after a save. Wiring Skip to `onDismissRequest`
would work by accident today and break the moment either meaning changes.

## ⚠ Both become public

The setup pages live in `:app`, which cannot see an `internal` of `:feature:settings`. Their
parameter types are all domain models, so nothing internal is exposed - `check_exposed_internal`
is the check that says so.

## The Skip and Next labels

New in `:common`, beside `update` and `cancel`, because both modules need them and `:app`'s own
`setup_next` is not visible from a feature module.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ACCESSIBILITY = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AccessibilityServicesDialog.kt"

OVERLAY = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/OverlayPackagesDialog.kt"

COMMON_STRINGS = "common/src/main/res/values/strings.xml"

TRANSLATIONS = "tools/check_translations.py"

SKIP_DOC = '''    /**
     * Non-null turns this into a step of the setup flow.
     *
     * ⚠ **Three things follow and nothing else does**: the container is drawn flat rather than
     * as a dialog, the actions become Skip and Next instead of Cancel and Update, and the row
     * holding them is arranged so Skip sits at the left. The body above is the same composable
     * either way, which is why this is a flag and not a second copy of the list.
     *
     * ⚠ **Not [onDismissRequest].** During setup that one is what advances the flow *after* a
     * save, so wiring Skip to it would work by accident and break the moment either meaning
     * changes.
     */
    onSkip: (() -> Unit)? = null,
'''


def actions_block(update_call: str) -> tuple[str, str]:
    """The old hand-built action row, and the same row with a setup arm."""
    old = f"""            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                horizontalArrangement = Arrangement.End,
            ) {{
                TextButton(onClick = onDismissRequest) {{
                    Text(text = stringResource(commonR.string.cancel))
                }}

                TextButton(
                    onClick = {{
                        {update_call}(selected.toList())

                        onDismissRequest()
                    }},
                ) {{
                    Text(text = stringResource(commonR.string.update))
                }}
            }}"""

    new = f"""            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                // SpaceBetween is what puts Skip at the left - see SettingsPage, which does the
                // same for the two dialogs built on it.
                horizontalArrangement = if (onSkip != null) {{
                    Arrangement.SpaceBetween
                }} else {{
                    Arrangement.End
                }},
            ) {{
                TextButton(onClick = onSkip ?: onDismissRequest) {{
                    Text(
                        text = stringResource(
                            if (onSkip != null) commonR.string.skip else commonR.string.cancel,
                        ),
                    )
                }}

                // ⚠ **The same button, renamed.** Next writes the draft this dialog is already
                // holding, exactly as Update does, so the two cannot drift into meaning
                // different things.
                TextButton(
                    onClick = {{
                        {update_call}(selected.toList())

                        onDismissRequest()
                    }},
                ) {{
                    Text(
                        text = stringResource(
                            if (onSkip != null) commonR.string.next else commonR.string.update,
                        ),
                    )
                }}
            }}"""

    return old, new


ACCESSIBILITY_OLD, ACCESSIBILITY_NEW = actions_block("onUpdateManagedAccessibilityServices")

OVERLAY_OLD, OVERLAY_NEW = actions_block("onUpdateManagedOverlayPackages")

EDITS: list[tuple[str, str, str]] = [
    # ---- the two labels ----
    (
        COMMON_STRINGS,
        """    <string name="update">Update</string>""",
        """    <!-- The setup flow's two footer buttons, here rather than in :app because the
         dialogs that draw them live in a feature module. -->
    <string name="skip">Skip</string>
    <string name="next">Next</string>
    <string name="update">Update</string>""",
    ),
    (
        TRANSLATIONS,
        """    # r4q: what the revert configuration is for, above what it does.""",
        """    # r4r: the setup flow's Skip and Next.
    "skip",
    "next",
    # r4q: what the revert configuration is for, above what it does.""",
    ),
    # ---- accessibility ----
    (
        ACCESSIBILITY,
        """internal fun AccessibilityServicesDialog(""",
        """fun AccessibilityServicesDialog(""",
    ),
    (
        ACCESSIBILITY,
        """    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
) {""",
        SKIP_DOC + """    onUpdateManagedAccessibilityServices: (List<String>) -> Unit,
) {""",
    ),
    (ACCESSIBILITY, ACCESSIBILITY_OLD, ACCESSIBILITY_NEW),
    (
        ACCESSIBILITY,
        """    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {""",
        """    DialogContainer(
        modifier = modifier,
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
    ) {""",
    ),
    # ---- overlay ----
    (
        OVERLAY,
        """internal fun OverlayPackagesDialog(""",
        """fun OverlayPackagesDialog(""",
    ),
    (
        OVERLAY,
        """    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
) {""",
        SKIP_DOC + """    onUpdateManagedOverlayPackages: (List<String>) -> Unit,
) {""",
    ),
    (OVERLAY, OVERLAY_OLD, OVERLAY_NEW),
]

AFTER = [
    (COMMON_STRINGS, 'name="skip"', 1),
    (COMMON_STRINGS, 'name="next"', 1),
    # Six each: the parameter, the arrangement test, the Skip button's own fallback, the two
    # label tests, and the container's flat argument. Counted, not guessed.
    (ACCESSIBILITY, "onSkip", 6),
    (ACCESSIBILITY, "internal fun AccessibilityServicesDialog(", 0),
    (ACCESSIBILITY, "flat = onSkip != null,", 1),
    (OVERLAY, "onSkip", 6),
    (OVERLAY, "internal fun OverlayPackagesDialog(", 0),
    (TRANSLATIONS, '"skip",', 1),
]


def main() -> int:
    staged: dict[str, str] = {}

    for relative, old, new in EDITS:
        path = ROOT / relative

        if not path.is_file():
            print(f"REFUSED: missing {relative}")
            return 1

        text = staged.get(relative, path.read_text(encoding="utf-8"))

        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            print(f"REFUSED: {relative}\n  {head!r} matched {found} time(s), expected 1")
            return 1

        staged[relative] = text.replace(old, new, 1)

    # ⚠ The overlay dialog's own container call is found rather than assumed: it has two
    # DialogContainer call sites in this file, its own and the loading one below it.
    marker = """    DialogContainer(
        modifier = modifier,
        onDismissRequest = onDismissRequest,
    ) {"""

    if staged[OVERLAY].count(marker) != 1:
        print(
            f"REFUSED: {OVERLAY}\n  its own container call matched "
            f"{staged[OVERLAY].count(marker)} time(s), expected 1",
        )
        return 1

    staged[OVERLAY] = staged[OVERLAY].replace(
        marker,
        """    DialogContainer(
        modifier = modifier,
        flat = onSkip != null,
        onDismissRequest = onDismissRequest,
    ) {""",
        1,
    )

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {COMMON_STRINGS}  :: skip, next")
    print(f"  ok        {ACCESSIBILITY}  :: public, with a setup arm")
    print(f"  ok        {OVERLAY}  :: public, with a setup arm")
    print(f"  ok        {TRANSLATIONS}  :: both deferred")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS) + 1} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
