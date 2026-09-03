#!/usr/bin/env python3
"""
r27b — the eleven icons onto their rows, and the app grid onto the All Apps tab.

The author: *"I want all the icon we generated to show in the same place switches are shown"* — so
they go on the **trailing** edge, not the leading one, and the settings list gets a single column of
marks down its right side whether a row carries a switch or an icon.

## Two things worth reading

**`SettingsColumn` takes a `Painter`, not a drawable id.** Ten of the eleven are `VectorDrawable`s
and would be happier with `@DrawableRes Int`; the app grid cannot be, because its second home is the
All Apps tab and `TopLevelDestination.icon` is typed `ImageVector` through the `HomeDestination`
interface in `:feature:home`. Changing that type to reach one icon is a refactor across three
modules. A `Painter` is the one thing both forms convert to — `painterResource` for the drawables,
`rememberVectorPainter` for the grid — so the grid has exactly one definition and the tab and the
row draw the same value.

**The grid is *not* tinted grey on the tab.** The author's grey rule is about the settings rows;
the tab bar tints its own icons by selected state, and forcing `outline` there would make the
selected tab illegible against its own fill. Same drawing, two tints, decided by each call site —
which is the other reason this is a shared `ImageVector` rather than a resource with a baked colour.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

ICONS = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/icon/GetoIcons.kt"

DESTINATION = ROOT / "app/src/main/kotlin/com/android/geto/navigation/TopLevelDestination.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


def code(text: str) -> str:
    return "\n".join(
        line for line in text.splitlines() if not line.strip().startswith(("//", "*", "/*", "/**"))
    )


# ─────────────────────────────────────────────────────────────────────────────────────────────
# 1. The app grid, as an ImageVector so the tab bar and the settings row share one definition.
# ─────────────────────────────────────────────────────────────────────────────────────────────

CELLS = ""

for row in range(3):
    for column in range(3):
        x = 3.2 + column * 6.3

        y = 3.2 + row * 6.3

        CELLS += f"""
        cell(x = {x:.1f}f, y = {y:.1f}f)"""

GRID = f'''
/**
 * The author's nine-square app grid — the All Apps tab, and the App drawer shortcuts row.
 *
 * ⚠ **Built here rather than as a drawable, because it has two homes with different tints.** The
 * settings row wants `colorScheme.outline` like the rest of that set; the tab bar tints by selected
 * state and would be illegible in grey. `TopLevelDestination.icon` is typed `ImageVector`, so this
 * is the one form both can take — `rememberVectorPainter` carries it to the row. One definition,
 * two tints.
 *
 * ⚠ **Nine rounded rectangles, drawn as paths.** `ImageVector` has no rounded-rect primitive, so
 * each cell is four lines and four quarter-arcs. The numbers are the template's: a 4.9 cell on a
 * 6.3 pitch from 3.2, which fills a 24 box with even gutters.
 */
val AppGrid: ImageVector = ImageVector.Builder(
    name = "AppGrid",
    defaultWidth = 24.dp,
    defaultHeight = 24.dp,
    viewportWidth = 24f,
    viewportHeight = 24f,
).apply {{
    fun cell(x: Float, y: Float) {{
        path(fill = SolidColor(Color.White)) {{
            val side = 4.9f

            val radius = 1.35f

            moveTo(x + radius, y)

            lineTo(x + side - radius, y)

            quadTo(x + side, y, x + side, y + radius)

            lineTo(x + side, y + side - radius)

            quadTo(x + side, y + side, x + side - radius, y + side)

            lineTo(x + radius, y + side)

            quadTo(x, y + side, x, y + side - radius)

            lineTo(x, y + radius)

            quadTo(x, y, x + radius, y)

            close()
        }}
    }}
{CELLS}
}}.build()
'''

icons = ICONS.read_text(encoding="utf-8")

check("AppGrid" not in icons, "icons: AppGrid already exists")

icons = replace_once(
    icons,
    "    val Apps = Icons.Rounded.Apps\n",
    "    val Apps = Icons.Rounded.Apps\n    val AppGrid = GetoAppGrid\n",
    "icons: AppGrid entry",
)

# The builder goes at the end of the file, beside whatever other hand-built vectors live there.
check("GetoStarFilled" in icons, "icons: expected the hand-built star to sit at the end of this file")

icons = icons.rstrip("\n") + "\n" + GRID.replace("val AppGrid: ImageVector", "private val GetoAppGrid: ImageVector")

for needed in (
    "import androidx.compose.ui.graphics.Color\n",
    "import androidx.compose.ui.graphics.SolidColor\n",
    "import androidx.compose.ui.graphics.vector.ImageVector\n",
    "import androidx.compose.ui.graphics.vector.path\n",
    "import androidx.compose.ui.unit.dp\n",
):
    if needed not in icons:
        icons = replace_once(
            icons,
            "import androidx.compose.material.icons.Icons\n",
            "import androidx.compose.material.icons.Icons\n" + needed,
            f"icons: {needed.rsplit('.', 1)[1].strip()} import",
        )

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 2. The All Apps tab.
# ─────────────────────────────────────────────────────────────────────────────────────────────

destination = DESTINATION.read_text(encoding="utf-8")

destination = replace_once(
    destination,
    """    ALL_APPS(
        label = R.string.all_apps,
        icon = GetoIcons.Apps,""",
    """    ALL_APPS(
        label = R.string.all_apps,
        // r27: the author's own nine-square grid, replacing Material's dotted one. The same
        // drawing carries the App drawer shortcuts row — see GetoIcons.AppGrid for why it is an
        // ImageVector rather than a drawable.
        icon = GetoIcons.AppGrid,""",
    "destination: All Apps icon",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 3. SettingsColumn gains the slot, and every toggle-less row fills it.
# ─────────────────────────────────────────────────────────────────────────────────────────────

settings = SETTINGS.read_text(encoding="utf-8")

settings = replace_once(
    settings,
    """    enabled: Boolean = true,
    onClick: () -> Unit,
    /**
     * A control at the far end of the row, with its own tap target - so it can say
     * something about the row without a press on it opening the row's dialog.
     */
    trailing: (@Composable () -> Unit)? = null,
) {""",
    """    enabled: Boolean = true,
    /**
     * The row's mark, drawn where a switch would be.
     *
     * ⚠ **At the far end, not the near one — r27, and it is the author's whole point:** *"I want
     * all the icon we generated to show in the same place switches are shown"*. The settings list
     * mixes rows that toggle with rows that open something, and putting these on the leading edge
     * would have given it two ragged columns instead of one tidy one.
     *
     * A `Painter` rather than a drawable id because one of the eleven is an `ImageVector` — see
     * `GetoIcons.AppGrid`.
     */
    icon: Painter? = null,
    onClick: () -> Unit,
    /**
     * A control at the far end of the row, with its own tap target - so it can say
     * something about the row without a press on it opening the row's dialog.
     */
    trailing: (@Composable () -> Unit)? = null,
) {""",
    "settings: SettingsColumn parameter",
)

settings = replace_once(
    settings,
    """        trailing?.let {
            Spacer(modifier = Modifier.width(12.dp))

            it()
        }
    }
}""",
    """        trailing?.let {
            Spacer(modifier = Modifier.width(12.dp))

            it()
        }

        // ⚠ **After `trailing`, so the icon is always the last thing on the row.** One row — the
        // hide list under the memory function — carries both, and a mark that sometimes sat
        // outside the notice and sometimes inside it would break the very column this exists to
        // make.
        icon?.let {
            Spacer(modifier = Modifier.width(12.dp))

            Icon(
                modifier = Modifier.size(SETTINGS_ICON_SIZE),
                painter = it,
                contentDescription = null,
                // The off-switch rim, at the author's word. Dimmed with the row, because a row
                // that greys its words and keeps a full-strength mark reads as half disabled.
                tint = if (enabled) {
                    MaterialTheme.colorScheme.outline
                } else {
                    MaterialTheme.colorScheme.outline.copy(alpha = 0.38f)
                },
            )
        }
    }
}""",
    "settings: SettingsColumn icon slot",
)

settings = replace_once(
    settings,
    """/** The Logics card's illustration. Big enough to read its parts, short enough for two lines. */""",
    """/**
 * Every settings-row mark, at one size.
 *
 * 24 dp: the same box the drawables are drawn in, and near enough a switch's height that the two
 * kinds of row do not look like different lists.
 */
private val SETTINGS_ICON_SIZE = 24.dp

/** The Logics card's illustration. Big enough to read its parts, short enough for two lines. */""",
    "settings: SETTINGS_ICON_SIZE",
)

# ── the eleven call sites, matched by the string each one shows ──────────────────────────────
BY_STRING = {
    "R.string.theme": "painterResource(designR.drawable.ic_theme)",
    "R.string.language": "painterResource(designR.drawable.ic_language)",
    "R.string.icon_style": "painterResource(designR.drawable.ic_icon_style)",
    "R.string.manager_rows_entry": "painterResource(designR.drawable.ic_services_glyph)",
    "R.string.drawer_shortcuts_entry": "rememberVectorPainter(GetoIcons.AppGrid)",
    "R.string.settings_to_hide_both_label": "painterResource(designR.drawable.ic_settings_hidden)",
    "R.string.revert_defaults": "painterResource(designR.drawable.ic_revert_glyph)",
    "R.string.accessibility_services_row": "painterResource(designR.drawable.ic_accessibility)",
    "R.string.overlay_packages_row": "painterResource(designR.drawable.ic_overlay)",
    "R.string.hiding_framework": "painterResource(designR.drawable.ic_hiding_framework)",
    "R.string.unhiding_framework": "painterResource(designR.drawable.ic_unhiding_framework)",
}

# ⚠ Two of the rows change their own title with the unhiding framework, so the *first* string each
# call site mentions is what identifies it — not the only one it can show.
pieces = []

cursor = 0

matched = []

for match in re.finditer(r"( *)SettingsColumn\(\n", settings):
    indent = match.group(1)

    window = settings[match.end() : match.end() + 1400]

    found = None

    for needle in BY_STRING:
        position = window.find(needle)

        if position != -1 and (found is None or position < found[1]):
            found = (needle, position)

    if found is None:
        continue

    pieces.append(settings[cursor : match.end()])

    pieces.append(f"{indent}    icon = {BY_STRING[found[0]]},\n")

    cursor = match.end()

    matched.append(found[0])

pieces.append(settings[cursor:])

settings = "".join(pieces)

check(
    len(matched) == 11,
    f"settings: matched {len(matched)} rows, expected 11 — {sorted(set(BY_STRING) - set(matched))}",
)

check(len(set(matched)) == 11, f"settings: a row was matched twice — {matched}")

for needed in (
    "import androidx.compose.ui.graphics.painter.Painter\n",
    "import androidx.compose.ui.graphics.vector.rememberVectorPainter\n",
):
    if needed not in settings:
        settings = replace_once(
            settings,
            "import androidx.compose.ui.res.painterResource\n",
            needed + "import androidx.compose.ui.res.painterResource\n",
            f"settings: {needed.rsplit('.', 1)[1].strip()} import",
        )

check("import com.android.geto.designsystem.icon.GetoIcons\n" in settings, "settings: GetoIcons import")

check(re.search(r"import .* as designR\n", settings) is not None, "settings: designR alias")

body = code(settings)

check(body.count("icon = painterResource") == 10, "settings: expected ten drawable rows")

check(body.count("icon = rememberVectorPainter") == 1, "settings: expected one vector row")

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in ((ICONS, icons), (DESTINATION, destination), (SETTINGS, settings)):
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
