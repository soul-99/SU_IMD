#!/usr/bin/env python3
"""v3-r4p — two things that vanish into a light-theme background.

    "the legibility of settings tab sections and also app icons is poor in light mode can we fix
     it by say?? darkening light background a bit?"
    "we can give the background app's green colour or theme colour tint(if dynamic theme is on)"
    "also the fav tab unhide button looks bad in light theme"

Templates `design/out/light_sections.png` and `design/out/fav_unhide_fab.png`, both approved as
drawn.

## 1. Collapsed sections

A collapsed section is `surfaceContainerLow`. In the light scheme that is **#F3F4E9** against a
page of **#F9FAEF** - a difference of six in each channel, which is why the cards read as
nothing at all. It is measured, not inferred from the screenshots.

⚠ **This does not reverse the recorded decision.** `CollapsibleSection`'s comment says a
collapsed section is left untinted because *"tinting all six headings meant the colour said 'this
is a heading', which the type already said, and the one thing worth pointing at - which section
is open - was left to a difference of two steps in the same shade"*. That is about the **heading
strips**, and they are untouched: the open section still gets `primary @ 34%` across its heading
and `primary @ 16%` behind its rows, and that is still what says which one is open. What changes
is the collapsed **card body**, at `primary @ 12%` - below the open body, so the hierarchy is
unchanged, and far enough from the page to be a card.

⚠ **An alpha of `primary`, never a colour.** With Dynamic Theme on, `LightGreenColorScheme` is
not in use at all, so any hard-coded value would have been right on one setting and wrong on the
other. This follows whatever scheme is in force - the author's *"or theme colour tint (if dynamic
theme is on)"*.

## 2. The Favourites unhide button

Idle, the FAB is `onSurface @ 12%` over the page: **#DEDFD5** on **#F9FAEF**, plus a shadow. It
is a translucent grey over a near-white page, which is exactly the "looks bad" - it reads as a
smudge rather than a control. `surfaceContainerHighest` is an opaque tonal step of the same
scheme, and `onSurfaceVariant` is the content colour that goes with it.

⚠ **Still greyed, and deliberately.** The recorded reason stands: *"Greyed reads as 'this has
nothing to do' where green reads as 'press me', and on a tab that exists for a device needing to
be put back, the second is a lie most of the time."* It is still pressable, and still answers
with a toast. Only the container stops being translucent ink.

The red active state is untouched.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETTINGS = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"

FAVOURITES = "feature/apps/src/main/kotlin/com/android/geto/feature/apps/FavouriteAppsScreen.kt"

EDITS: list[tuple[str, str, str]] = [
    # 1. The comment that records the decision, extended rather than replaced.
    (
        SETTINGS,
        """    // The muted one is the body: every setting inside the expanded section sits on it, which is
    // what marks out where the open section starts and ends. The stronger one is the heading
    // strip above them. A collapsed section is left untinted altogether: tinting all six
    // headings meant the colour said "this is a heading", which the type already said, and the
    // one thing worth pointing at - which section is open - was left to a difference of two
    // steps in the same shade.""",
        """    // The muted one is the body: every setting inside the expanded section sits on it, which is
    // what marks out where the open section starts and ends. The stronger one is the heading
    // strip above them. A collapsed section's *heading* is still left untinted, for the reason
    // it always was: tinting all six headings meant the colour said "this is a heading", which
    // the type already said, and the one thing worth pointing at - which section is open - was
    // left to a difference of two steps in the same shade.
    //
    // ⚠ **Its body is not, since r4p, and that is a different question.** A collapsed card was
    // surfaceContainerLow, which in the light scheme is #F3F4E9 against a #F9FAEF page - six in
    // each channel, so the card was not visible as a card at all. A third, weaker step of the
    // same tint separates it from the page while staying below the open body, so the ordering
    // page < collapsed < open body < heading still says which section is open.
    //
    // An alpha of primary rather than a colour, because with Dynamic Theme on the scheme below
    // is not the one in use - the author's "theme colour tint (if dynamic theme is on)".""",
    ),
    # 2. The tint itself, declared beside the two it belongs with.
    (
        SETTINGS,
        """    val headingTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.34f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)""",
        """    val headingTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.34f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)

    val collapsedTint = MaterialTheme.colorScheme.primary
        .copy(alpha = 0.12f)
        .compositeOver(MaterialTheme.colorScheme.surfaceContainerLowest)""",
    ),
    # 3. And the card that uses it.
    (
        SETTINGS,
        """                targetValue = if (expanded) {
                    bodyTint
                } else {
                    MaterialTheme.colorScheme.surfaceContainerLow
                },""",
        """                targetValue = if (expanded) {
                    bodyTint
                } else {
                    collapsedTint
                },""",
    ),
    # 4. The idle FAB.
    (
        FAVOURITES,
        """                    containerColor = if (anythingHidden) {
                        GetoRed
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.12f)
                    },
                    contentColor = if (anythingHidden) {
                        Color.White
                    } else {
                        MaterialTheme.colorScheme.onSurface.copy(alpha = 0.38f)
                    },""",
        """                    // ⚠ **An opaque tonal step, not translucent ink** - r4p. The idle
                    // container was onSurface at 12%, which over a light page is #DEDFD5 on
                    // #F9FAEF: a smudge with a shadow under it rather than a control, which is
                    // the author's "looks bad in light theme". Greyed is still the intent, and
                    // the paragraph above is still why; only the way it is drawn changes.
                    containerColor = if (anythingHidden) {
                        GetoRed
                    } else {
                        MaterialTheme.colorScheme.surfaceContainerHighest
                    },
                    contentColor = if (anythingHidden) {
                        Color.White
                    } else {
                        MaterialTheme.colorScheme.onSurfaceVariant
                    },""",
    ),
]

AFTER = [
    (SETTINGS, "collapsedTint", 2),
    (SETTINGS, "alpha = 0.12f", 1),
    # The two that were already there are unchanged.
    (SETTINGS, "alpha = 0.16f", 1),
    (SETTINGS, "alpha = 0.34f", 1),
    # surfaceContainerLow is no longer the collapsed card's colour, and it is used nowhere else
    # in this file.
    #
    # ⚠ **Spelled the way only a statement can spell it.** The first draft asserted
    # "surfaceContainerLow," was absent and was refused by the new *comment* three edits up,
    # which names the colour it is replacing - the comment trap again, inflating a count instead
    # of hiding one. The receiver makes it code. The trailing comma keeps surfaceContainerLowest
    # out, since that one is always followed by a bracket.
    (SETTINGS, "colorScheme.surfaceContainerLow,", 0),
    (FAVOURITES, "surfaceContainerHighest", 1),
    (FAVOURITES, "onSurfaceVariant", 1),
    (FAVOURITES, "GetoRed", 2),
    # Nothing else in the file used the disabled pair; the two that were here are gone.
    (FAVOURITES, "onSurface.copy(alpha = 0.12f)", 0),
    (FAVOURITES, "onSurface.copy(alpha = 0.38f)", 0),
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

    print(f"  ok        {SETTINGS}  :: collapsed cards tinted at 12%, headings untouched")
    print(f"  ok        {FAVOURITES}  :: the idle FAB is an opaque tonal step")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
