#!/usr/bin/env python3
"""
v3-r9 — draw the app icons in IMD+'s "apps to watch" picker.

The author: *"in IMD+ apps to watch dialog box show app icons"*.

⚠ **Nothing has to be loaded for this.** [InstalledAppData] has carried `icon: ByteArray?` all
along and `DefaultPackageManagerWrapper.getInstalledApps` fills it in, so the bytes were already
crossing into this dialog and being thrown away at the last step. The two sibling pickers -
`AccessibilityServicesDialog` and `OverlayPackagesDialog` - have drawn theirs since v3; this one
simply never did, which is the whole of the bug.

So the change is the row's leading slot and nothing else: the same `Row` holding the checkbox and
an `AsyncImage` at the same `PICKER_ICON` size those two use, in the same order. This dialog's own
KDoc already says it is *"the same shape as the overlay and accessibility pickers, deliberately -
three lists of the same kind of thing should not look like three different features"*, and the
missing icon was the one place that was not true.

⚠ **`PICKER_ICON` is declared here rather than shared.** Both siblings declare their own private
copy of the same 36 dp; a fourth file to hold one number would be worse than the duplication, and
hoisting it is a change to two files that are not otherwise in this build.

Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AutoHideDialogs.kt"

ROW_OLD = '''                            leadingContent = {
                                Checkbox(
                                    checked = id in selected,
                                    onCheckedChange = { toggle() },
                                )
                            },
'''

ROW_NEW = '''                            leadingContent = {
                                // Checkbox first, then the icon, then the label - the
                                // arrangement the accessibility and overlay pickers already
                                // use. The icon rides in on InstalledAppData and was simply
                                // never drawn; see this file's own note about the three
                                // pickers being one shape.
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Checkbox(
                                        checked = id in selected,
                                        onCheckedChange = { toggle() },
                                    )

                                    AsyncImage(
                                        modifier = Modifier
                                            .padding(start = 4.dp)
                                            .size(PICKER_ICON),
                                        model = app.icon,
                                        contentDescription = null,
                                    )
                                }
                            },
'''

CONST_OLD = '''@Composable
internal fun AutoHideAppsDialog(
'''

CONST_NEW = '''/**
 * The app icon beside each row.
 *
 * The same 36 dp the accessibility and overlay pickers draw theirs at, and declared here for the
 * same reason they each declare their own: one number is cheaper duplicated than shared through a
 * file that exists only to hold it.
 */
private val PICKER_ICON = 36.dp

@Composable
internal fun AutoHideAppsDialog(
'''

IMPORT_OLD = "import androidx.compose.foundation.layout.padding\n"

IMPORT_NEW = (
    "import androidx.compose.foundation.layout.padding\n"
    "import androidx.compose.foundation.layout.size\n"
)

COIL_OLD = "import com.android.geto.designsystem.component.DialogContainer\n"

COIL_NEW = (
    "import coil.compose.AsyncImage\n"
    "import com.android.geto.designsystem.component.DialogContainer\n"
)

EDITS = [(IMPORT_OLD, IMPORT_NEW), (COIL_OLD, COIL_NEW), (CONST_OLD, CONST_NEW), (ROW_OLD, ROW_NEW)]

CHECKS = [
    ("AsyncImage(", 1, "one icon is drawn"),
    ("model = app.icon,", 1, "and it is the app's own"),
    ("PICKER_ICON", 2, "declared once, used once"),
    ("import coil.compose.AsyncImage", 1, "coil is imported once"),
    ("import androidx.compose.foundation.layout.size", 1, "and size once"),
    # Already imported by this file for the flow-diagram rows below; not gained here.
    ("import androidx.compose.ui.Alignment", 1, "Alignment was already imported"),
    ("import androidx.compose.foundation.layout.Row", 1, "and so was Row"),
]


def main() -> int:
    path = ROOT / DIALOG

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in EDITS:
        if text.count(old) != 1:
            print(f"REFUSED: anchor {old.strip()[:60]!r} matched {text.count(old)} time(s)")
            return 1

        if new in original:
            print("REFUSED: already applied")
            return 1

        text = text.replace(old, new, 1)

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:46]!r}")

    over = lambda s: {ln for ln in s.split("\n")
                      if len(ln) > 120 and not ln.lstrip().startswith("import ")}

    if over(text) - over(original):
        print("REFUSED: would gain lines over 120 chars")
        return 1

    path.write_text(text, encoding="utf-8")

    print("\n  ok  the apps-to-watch picker draws its icons")

    return 0


if __name__ == "__main__":
    sys.exit(main())
