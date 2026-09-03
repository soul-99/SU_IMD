#!/usr/bin/env python3
"""r4b — the section name back, the description link to releases, and two more Shevery points.

Three corrections the author made after seeing r4a:

  1. *"there was no need to rename 'Shizuku configuration' section in the settings tab, please
     put it back to 'Shizuku configuration'."* — overruling his own v3 spec item, which asked
     for `'Shizuku (Thedjchi) configuration in IMD'`. The location tree that names that section
     goes back with it, in both modules that carry a copy.
  2. *"in the description line thedjchi link should be to it's github release page not repo, i
     only want repo link for toggles."* — so the two are now different URLs: the red
     recommendation line points at the releases page a reader is being sent to download from,
     while the fork **names** in the picker point at the repo.
  3. Two more points in the Shevery pop-up's `How this works`, above the last red one, both
     bold and in the error colour.

### ⚠ The two new points are the scope of Shevery, written down

    "Managing Shevery service & Display over other apps is only allowed in IMD settings
     manager."
    "Hiding-unhiding for app launches is not supported for both settings mentioned above."

That settles a question r4 stopped on. Shevery's toggles are **not** coming back to Settings to
hide/unhide or Revert to default; `withoutShizukuWhenNoIntents` and `overlayManageable` go on
dropping both targets from the hide and revert paths, exactly as they do today. What Shevery
gains is the **settings manager**, which is the next script.

⚠ **The author's leading `'4. '` and `'5. '` are not in the strings.** This list draws its own
numbers — it has since the pop-up was built, because its first point reuses a string that
already existed and could not be re-prefixed — so keeping his would print `4. 4.`. Drawing them
is also what renumbers his old fourth point to sixth without touching its text. **He has been
told**; baking all six in instead is one line if he prefers it.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS_STRINGS = "feature/settings/src/main/res/values/strings.xml"
APPS_STRINGS = "feature/apps/src/main/res/values/strings.xml"
SCREEN = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
SETUP_DIALOGS = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
                 "ShizukuSetupDialogs.kt")
SHEVERY = ("feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/"
           "SheveryNoticeDialog.kt")
TRANSLATIONS = "tools/check_translations.py"

DEFERRED_KEYS = ["shevery_how_manager_only", "shevery_how_no_launch"]

NEW_POINTS = """    <!-- Added after r4a, above the last red point. Both bold and in the error colour: they
      are the scope of Shevery support rather than advice about it. -->
    <string name="shevery_how_manager_only">Managing Shevery service &amp; Display over other apps is only allowed in IMD settings manager.</string>
    <string name="shevery_how_no_launch">Hiding-unhiding for app launches is not supported for both settings mentioned above.</string>
"""

EDITS: list[tuple[str, list[tuple[str, str, int]]]] = [
    (SETTINGS_STRINGS, [
        (
            """    <string name="shizuku">Shizuku (Thedjchi) configuration in IMD</string>
""",
            """    <string name="shizuku">Shizuku configuration</string>
""",
            1,
        ),
        (
            """    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku (Thedjchi) configuration in IMD \\u2192 Manage Shizuku</string>
""",
            """    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku configuration \\u2192 Manage Shizuku</string>
""",
            1,
        ),
        (
            """    <string name="shevery_how_warning">Shevery framework might be prone to failures</string>
""",
            NEW_POINTS
            + """    <string name="shevery_how_warning">Shevery framework might be prone to failures</string>
""",
            1,
        ),
    ]),
    (APPS_STRINGS, [
        (
            """    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku (Thedjchi) configuration in IMD \\u2192 Manage Shizuku</string>
""",
            """    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku configuration \\u2192 Manage Shizuku</string>
""",
            1,
        ),
    ]),
    (SCREEN, [
        (
            '''private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku"''',
            '''private const val SHIZUKU_THEDJCHI_URL = "https://github.com/thedjchi/Shizuku"

/**
 * ⚠ **The releases page, and only for the red recommendation line.**
 *
 * The author's rule after r4a: *"in the description line thedjchi link should be to it's github
 * release page not repo, i only want repo link for toggles."* The two links answer different
 * questions — the description is telling somebody to go and **download** the fork, while the
 * fork name beside a radio button is answering "which app is that?", and the repo is where that
 * is explained.
 */
private const val SHIZUKU_THEDJCHI_RELEASES_URL =
    "https://github.com/thedjchi/Shizuku/releases"''',
            1,
        ),
        (
            """            append(prefix)
            append(" ")
            withLink(LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_URL, styles = linkStyles)) {
""",
            """            append(prefix)
            append(" ")
            withLink(
                LinkAnnotation.Url(url = SHIZUKU_THEDJCHI_RELEASES_URL, styles = linkStyles),
            ) {
""",
            1,
        ),
    ]),
    (SETUP_DIALOGS, [
        (
            """internal fun HowThisWorksPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    color: Color = Color.Unspecified,
    content: (@Composable () -> Unit)? = null,
) {
    Row(modifier = modifier.padding(bottom = 8.dp)) {
        Text(
            text = "$number.",
            style = MaterialTheme.typography.bodyMedium,
            color = color,
        )

        Spacer(modifier = Modifier.width(8.dp))

        if (content == null) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = color,
            )
""",
            """internal fun HowThisWorksPoint(
    modifier: Modifier = Modifier,
    number: Int,
    text: String,
    color: Color = Color.Unspecified,
    /**
     * ⚠ **Two of these points are entirely bold**, which is how the author wrote them: they
     * state the scope of Shevery support rather than advising about it, and the pop-up is the
     * only place that scope is written down.
     */
    bold: Boolean = false,
    content: (@Composable () -> Unit)? = null,
) {
    Row(modifier = modifier.padding(bottom = 8.dp)) {
        Text(
            text = "$number.",
            style = MaterialTheme.typography.bodyMedium,
            color = color,
            fontWeight = if (bold) FontWeight.Bold else null,
        )

        Spacer(modifier = Modifier.width(8.dp))

        if (content == null) {
            Text(
                text = text,
                style = MaterialTheme.typography.bodyMedium,
                color = color,
                fontWeight = if (bold) FontWeight.Bold else null,
            )
""",
            1,
        ),
    ]),
    (SHEVERY, [
        (
            """            HowThisWorksPoint(number = 3, text = stringResource(R.string.shevery_how_delay))

            HowThisWorksPoint(
                number = 4,
                text = stringResource(R.string.shevery_how_warning),
                color = MaterialTheme.colorScheme.error,
            )
""",
            """            HowThisWorksPoint(number = 3, text = stringResource(R.string.shevery_how_delay))

            // ⚠ **Four and five are the scope of Shevery support, not advice about it** - the
            // author added them after r4a, and they are what settles where Shevery's two
            // targets can be operated at all. Bold and red for that reason.
            HowThisWorksPoint(
                number = 4,
                text = stringResource(R.string.shevery_how_manager_only),
                color = MaterialTheme.colorScheme.error,
                bold = true,
            )

            HowThisWorksPoint(
                number = 5,
                text = stringResource(R.string.shevery_how_no_launch),
                color = MaterialTheme.colorScheme.error,
                bold = true,
            )

            HowThisWorksPoint(
                number = 6,
                text = stringResource(R.string.shevery_how_warning),
                color = MaterialTheme.colorScheme.error,
            )
""",
            1,
        ),
    ]),
    (TRANSLATIONS, [
        (
            """    "shevery_how_warning",
""",
            """    "shevery_how_warning",
"""
            + "".join(f'    "{key}",\n' for key in DEFERRED_KEYS),
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

    # Nothing anywhere may still carry the withdrawn section name.
    for rel in (SETTINGS_STRINGS, APPS_STRINGS):
        if "Shizuku (Thedjchi) configuration" in staged.get(ROOT / rel, ""):
            problems.append(f"{rel}: still carries the withdrawn section name")

    # The two links must now be different, and each used exactly once.
    screen = staged.get(ROOT / SCREEN, "")

    if screen.count("url = SHIZUKU_THEDJCHI_RELEASES_URL") != 1:
        problems.append(f"{SCREEN}: the releases link is not used exactly once")

    if screen.count("url = SHIZUKU_THEDJCHI_URL") != 1:
        problems.append(f"{SCREEN}: the repo link is not used exactly once (the fork name)")

    # Six points, numbered once each.
    shevery = staged.get(ROOT / SHEVERY, "")

    for number in range(1, 7):
        if len(re.findall(rf"number = {number}\b", shevery)) != 1:
            problems.append(f"{SHEVERY}: point {number} is not drawn exactly once")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        before = set(path.read_text(encoding="utf-8").splitlines())

        for line in text.splitlines():
            if line not in before and len(line) > 120 and not path.name.endswith(".xml"):
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

    print("ok - section name back, releases link on the description, two more Shevery points")

    return 0


if __name__ == "__main__":
    sys.exit(main())
