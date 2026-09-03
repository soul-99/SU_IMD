#!/usr/bin/env python3
"""
r27c — the six things the author asked for alongside the icons.

1. **Support page, point 2** loses its link and gains a button under it, styled like the Share
   button beside point 1, carrying the GitHub glyph from the soul_99 popup and the words
   `view Project on GitHub`. ⚠ Lowercase *view*, capital *Project* — confirmed deliberate, so it
   goes in as written.
2. **The soul_99 dialog's title** becomes two lines, the second `(Dr. Utkarsh Rajput)`. No new
   string: `support_signature_real_name` already carries exactly that text, untranslatable, for the
   signature at the foot of the support dialog. The same name in two places should be one resource.
3. **The FOSS footer** becomes `Long live FOSS !` over `(Free and Open Source Software)`. His
   spacing before the `!` is kept as he wrote it.
4. **The shell panel goes back to dark in dark mode**, brighter than the `#212121` it used to be.
   ⚠ The prompt green has to come back with it: r25 collapsed the light/dark pair into one when the
   panel stopped varying, and a light-green prompt is what a dark panel needs. Undoing half of r25
   and leaving the other half would put `#4C662B` on `#2E2E2E`.
5. **Progressive UI blur on by default.**
6. **`(Recommended)` under IMD defaults** in the hiding-framework dialog.

## The blur default is not a one-line flip

proto3 has no custom defaults, which is why field 79 is named `progressiveBlurOn` — an unwritten
bool decodes to false, so a field named for the ON state is off until something writes it, which is
what r17 wanted. Turning it on by default means that name now says the wrong thing.

Renaming it to `progressiveBlurOff` on a fresh number would work but throws away every stored
choice. A companion bool keeps them: `progressiveBlurSet` says whether anybody has touched the
switch, and the resolution reads the stored value only when they have. That is the shape field 69
(`favouriteAppsViewSet`) and field 80 (`blurCustomised`) already use in this proto.

⚠ **One honest consequence, and it is unavoidable rather than a shortcut.** Under the old default,
"never touched it" and "deliberately turned it off" are the *same stored bytes* — an absent field.
No scheme can tell them apart after the fact, so anyone who had turned the blur off will find it on
once after updating, and off again for good the moment they touch it. Flipping a proto3 default
costs exactly that, whichever way it is implemented.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SUPPORT = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/SupportDialog.kt"

SETTINGS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

FRAMEWORKS = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/FrameworkDialogs.kt"

STRINGS = ROOT / "feature/settings/src/main/res/values/strings.xml"

PROTO = ROOT / "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"

SOURCE = ROOT / "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

ICONS = ROOT / "design-system/src/main/kotlin/com/android/geto/designsystem/icon/GetoIcons.kt"

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
# 1. Support point 2: a button instead of a link.
# ─────────────────────────────────────────────────────────────────────────────────────────────

support = SUPPORT.read_text(encoding="utf-8")

support = replace_once(
    support,
    """            LinkedPoint(
                number = 2,
                sentence = stringResource(R.string.support_point_star),
                linkPhrase = stringResource(R.string.support_point_star_link),
                url = ProjectLinks.REPOSITORY,
                // The gold star as a glyph, so it flows and wraps with the words instead of
                // floating beside them.
                prefix = "⭐ ",
            )
""",
    """            // ⚠ **No longer a link — r27, at the author's request.** Point 1 is an ask with a
            // button under it; point 2 was an ask with a phrase inside it that happened to be
            // tappable, which is a different affordance in the same list. It is now the same
            // shape as point 1: the sentence, then the thing it asks for as a button.
            //
            // The gold star stays a glyph in the text so it flows and wraps with the words
            // instead of floating beside them.
            SupportPoint(
                number = 2,
                text = "⭐ " + stringResource(R.string.support_point_star),
            )

            // Deliberately the same control as the Share button above, down to the tonal fill and
            // the 18 dp glyph: two points that can be finished in a tap should look alike, and a
            // reader who has just used one knows what the other is.
            FilledTonalButton(
                modifier = Modifier.padding(start = POINT_INSET, top = 4.dp, bottom = 8.dp),
                onClick = { context.openProjectUri(ProjectLinks.REPOSITORY) },
            ) {
                Icon(
                    modifier = Modifier.size(18.dp),
                    // The glyph from the soul_99 popup, at the author's word — the app has one
                    // GitHub mark and this is it.
                    painter = painterResource(designR.drawable.ic_github),
                    contentDescription = null,
                )

                Spacer(modifier = Modifier.width(8.dp))

                Text(text = stringResource(R.string.support_view_github_button))
            }
""",
    "support: point 2",
)

for needed, anchor in (
    ("import androidx.compose.ui.res.painterResource\n", "import androidx.compose.ui.res.stringResource\n"),
    ("import com.android.geto.designsystem.R as designR\n", None),
):
    if needed not in support and anchor is not None:
        support = replace_once(support, anchor, needed + anchor, f"support: {needed.strip()}")

if "import com.android.geto.designsystem.R as designR\n" not in support:
    support = replace_once(
        support,
        "import com.android.geto.feature.settings.R\n",
        "import com.android.geto.designsystem.R as designR\nimport com.android.geto.feature.settings.R\n",
        "support: designR alias",
    )

check("openProjectUri" in support, "support: openProjectUri is not reachable here")

# Two calls (points 3 and 4) plus the declaration — the count that caught this was written as if
# the declaration were not in the same file.
check(code(support).count("LinkedPoint(") == 3, "support: points 3 and 4 should still be links")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 2 + 3. The soul_99 dialog's second line, and the FOSS footer.
# ─────────────────────────────────────────────────────────────────────────────────────────────

settings = SETTINGS.read_text(encoding="utf-8")

settings = replace_once(
    settings,
    """            Text(
                modifier = Modifier.padding(bottom = 8.dp),
                text = stringResource(R.string.about_author_name),
                style = MaterialTheme.typography.titleLarge,
            )
""",
    """            // ⚠ **Two lines, and the second is not a new string.** `support_signature_real_name`
            // already carries exactly "(Dr. Utkarsh Rajput)" for the signature at the foot of the
            // support dialog, and it is untranslatable there for the same reason it is here: it is
            // a name. One resource, two places, nothing to keep in step.
            Text(
                text = stringResource(R.string.about_author_name),
                style = MaterialTheme.typography.titleLarge,
            )

            Text(
                modifier = Modifier.padding(bottom = 8.dp),
                text = stringResource(R.string.support_signature_real_name),
                style = MaterialTheme.typography.titleLarge,
            )
""",
    "settings: author dialog title",
)

settings = replace_once(
    settings,
    """        Text(
            text = stringResource(R.string.long_live_foss),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )""",
    """        Text(
            text = stringResource(R.string.long_live_foss),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )

        // The expansion on its own line rather than inside the sentence, at the author's word.
        // Two Texts, not one string with a \\n: only this half is the parenthetical, and a
        // translation is free to break it differently.
        Text(
            text = stringResource(R.string.long_live_foss_expansion),
            style = MaterialTheme.typography.bodyMedium,
            textAlign = TextAlign.Center,
        )""",
    "settings: FOSS footer",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 4. The shell panel: dark again in dark mode, and brighter than it was.
# ─────────────────────────────────────────────────────────────────────────────────────────────

settings = replace_once(
    settings,
    """    // ⚠ **One prompt green now, because there is one panel — r25.** The dark prompt existed to
    // sit on the dark panel; with the panel fixed to the cream one it would be barely there. A
    // fixed panel and a themed prompt is the one combination that is worse than either.
    val shellPrompt = SHELL_PROMPT""",
    """    val shellDark = MaterialTheme.colorScheme.surface.luminance() < DARK_SURFACE_LUMINANCE

    // ⚠ **Both back — r27, and they move together or not at all.** r25 pinned the panel to the
    // author's sepia in both themes and collapsed this pair into one, which was right while there
    // was one panel. He has since asked for the dark panel back, brighter; leaving the prompt
    // pinned would have put the dark green `#4C662B` on `#2E2E2E`, which is the one combination
    // worse than either of the two this file has shipped.
    val shellPrompt = if (shellDark) SHELL_PROMPT_DARK else SHELL_PROMPT_LIGHT""",
    "settings: shell prompt",
)

settings = replace_once(
    settings,
    """    // ⚠ **The same panel in both themes — r25, at the author's word:** *"even for the dark mode
    // i want to show the quirky shell output window in the sepia colour one i use for light
    // mode"*. It used to be picked by a luminance test on the live scheme, which was the right
    // way to ask a question this block no longer asks. The block is an easter egg drawn as a
    // terminal, and a terminal is whatever colour its author made it — the same argument
    // [SHELL_OUTPUT_COLOUR] has carried since it was pinned.
    val shellPanel = SHELL_PANEL""",
    """    // Which panel goes behind it, read from the scheme that is actually in force rather than
    // from isSystemInDarkTheme(). The app has a user-selectable theme - FOLLOW_SYSTEM, LIGHT,
    // DARK - so asking the *system* would give a user on LIGHT with a dark system a grey panel
    // inside a light app, and the reverse. This is also the only form that stays right under
    // dynamic colour, where the scheme is neither of the two the app declares.
    val shellPanel = if (shellDark) SHELL_PANEL_DARK else SHELL_PANEL_LIGHT""",
    "settings: shell panel",
)

settings = replace_once(
    settings,
    """private val SHELL_PROMPT = Color(0xFF4C662B)

/** The sepia the author asked for in both themes — r25. Not the app's green, and not the page's. */
private val SHELL_PANEL = Color(0xFFF2F1E9)""",
    """private val SHELL_PROMPT_LIGHT = Color(0xFF4C662B)

private val SHELL_PROMPT_DARK = Color(0xFFB1D18A)

/**
 * The panel under the output in a dark scheme.
 *
 * ⚠ **`#2E2E2E`, up from the `#212121` this used to be — r27, the author's *"brighten it a bit"*.**
 * Grey rather than black and not the app's green, as it always was; the lift is thirteen points,
 * which is enough to read as a panel on the near-black page rather than as a hole in it.
 */
private val SHELL_PANEL_DARK = Color(0xFF2E2E2E)

/** And in a light one: the author's sepia. */
private val SHELL_PANEL_LIGHT = Color(0xFFF2F1E9)""",
    "settings: shell constants",
)

settings = replace_once(
    settings,
    """ * The same argument [SHELL_OUTPUT_COLOUR] already carries: the colour of terminal output is not
 * something a theme has an opinion about. ⚠ **And since r25 there is only one of them**, because
 * the panel behind it is the author's sepia in both themes — a dark prompt green was only ever
 * there to sit on a dark panel that no longer exists.
 */""",
    """ * The same argument [SHELL_OUTPUT_COLOUR] already carries: the colour of terminal output is not
 * something a theme has an opinion about. Which of the two applies is decided by the same
 * luminance test the panel behind it uses, not by isSystemInDarkTheme() — the app has its own
 * light/dark/follow-system setting, and asking the system would give a light-themed app on a
 * dark-themed phone the wrong one.
 */""",
    "settings: prompt KDoc",
)

body = code(settings)

check(body.count("SHELL_PANEL_DARK") == 2, "settings: expected the declaration and one use")

check(body.count("SHELL_PROMPT_DARK") == 2, "settings: expected the declaration and one use")

check("SHELL_PANEL " not in body and "SHELL_PROMPT " not in body, "settings: the r25 names should be gone")

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 5. (Recommended) under IMD defaults.
# ─────────────────────────────────────────────────────────────────────────────────────────────

frameworks = FRAMEWORKS.read_text(encoding="utf-8")

frameworks = replace_once(
    frameworks,
    """                summary = stringResource(R.string.hiding_framework_defaults_summary),""",
    """                // ⚠ **The same resource the memory function uses**, at the author's *"just like
                // we do for memory function"* — so the two dialogs cannot drift into two spellings
                // of one word. Its name still says `unhiding_` because that is where it was first
                // needed; renaming it would mean touching eight translation files, which is not
                // something this project does.
                recommended = stringResource(R.string.unhiding_framework_recommended),
                summary = stringResource(R.string.hiding_framework_defaults_summary),""",
    "frameworks: recommended tag",
)

check(
    code(frameworks).count("recommended = stringResource") == 2,
    "frameworks: expected the tag on both dialogs",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 6. Progressive UI blur, on by default.
# ─────────────────────────────────────────────────────────────────────────────────────────────

proto = PROTO.read_text(encoding="utf-8")

proto = replace_once(
    proto,
    "  bool progressiveBlurOn = 79;\n",
    """  bool progressiveBlurOn = 79;

  // Whether anybody has touched the Progressive UI blur switch.
  //
  // ⚠ **Added in r27, when the author asked for the blur to be ON by default.** proto3 has no
  // custom defaults, which is the whole reason 79 is named for the ON state; flipping the default
  // means that name no longer describes what an unwritten field gives. Renaming it again on a
  // fresh number would work and would throw away every stored choice, so this says whether 79
  // means anything yet: unset, the resolution answers true; set, it answers what 79 holds. The
  // shape favouriteAppsViewSet on 69 and blurCustomised on 80 already use.
  //
  // ⚠ It cannot recover a choice made before it existed. Under the old default an install that
  // never touched the switch and one that deliberately turned it off are the same absent field,
  // so anyone in the second group gets the blur back once and keeps their answer from then on.
  // That is what flipping a proto3 default costs, whichever way it is done.
  bool progressiveBlurSet = 84;
""",
    "proto: progressiveBlurSet",
)

check(proto.count("= 84;") == 1, "proto: 84 is not free")

source = SOURCE.read_text(encoding="utf-8")

source = replace_once(
    source,
    "            progressiveBlur = it.progressiveBlurOn,",
    """            // ⚠ **On until told otherwise — r27.** See progressiveBlurSet in the proto: the
            // companion bool is what lets the default change without discarding the choices
            // already stored against progressiveBlurOn.
            progressiveBlur = if (it.progressiveBlurSet) it.progressiveBlurOn else true,""",
    "source: blur resolution",
)

source = replace_once(
    source,
    "            it.copy { progressiveBlurOn = enabled }",
    """            it.copy {
                progressiveBlurOn = enabled

                // Both, always: the value is meaningless to the read above until this is true.
                progressiveBlurSet = true
            }""",
    "source: blur write",
)

# ─────────────────────────────────────────────────────────────────────────────────────────────
# 7. Strings, and the comment that described the link that has gone.
# ─────────────────────────────────────────────────────────────────────────────────────────────

strings = STRINGS.read_text(encoding="utf-8")

strings = replace_once(
    strings,
    """    <!-- The Support button above the author line, and its popup. The author's own message,
      kept in the first person, as four separate paragraphs. In point 2 a yellow star is drawn
      before the sentence and the phrase in support_point_star_link is turned into the repo
      link, so that phrase must appear inside support_point_star verbatim. -->""",
    """    <!-- The Support button above the author line, and its popup. The author's own message,
      kept in the first person, as four separate paragraphs. In point 2 a yellow star is drawn
      before the sentence.
      support_point_star_link is no longer used: r27 replaced the inline link with a button under
      the point, matching the Share button under point 1. It is kept rather than deleted because
      removing it would orphan the phrase in eight translation files. -->""",
    "strings: support comment",
)

strings = replace_once(
    strings,
    """    <string name="support_share_button">Share</string>""",
    """    <string name="support_share_button">Share</string>
    <!-- The author's own capitalisation, confirmed deliberate: lowercase view, capital Project. -->
    <string name="support_view_github_button">view Project on GitHub</string>""",
    "strings: github button",
)

strings = replace_once(
    strings,
    """    <string name="long_live_foss">Long live free and open source software!</string>""",
    """    <!-- Two lines, the second expanding the first. The space before the "!" is the author's. -->
    <string name="long_live_foss">Long live FOSS !</string>
    <string name="long_live_foss_expansion">(Free and Open Source Software)</string>""",
    "strings: FOSS lines",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in (
    (SUPPORT, support),
    (SETTINGS, settings),
    (FRAMEWORKS, frameworks),
    (PROTO, proto),
    (SOURCE, source),
    (STRINGS, strings),
):
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
