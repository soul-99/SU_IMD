#!/usr/bin/env python3
"""
v3-r6 — stop the settings manager's *window* animating, so only the card does.

Two of the author's three reports are one window, and the screen recording settles both.

## What the recording shows

Opening the manager from its launcher icon (frames 30-32 at 15 fps):

    home screen  ->  a black rounded square with the app icon expanding out of the icon's
                     position and filling the screen  ->  the dialog fades in on top of it

That black square is **Android 12's splash screen**, and it is the author's *"an animation of app
launch of icon expanding then loads on top of it ... makes user feel like a full screen app is
loading which does not look seamless"*.

Pressing the IMD icon inside the manager (frames 52-60):

    dialog  ->  the whole dialog slides down and to the right and shrinks off the corner
            ->  about half a second of bare home screen
            ->  the black icon-expand square again, this time IMD's own
            ->  IMD

The shrink-to-the-corner is this activity's own **window close animation**, and it is the
author's *"very broken animation"* on the fold — a translucent window a third of the screen tall
being flung at a corner as if it were a full-screen app.

## The fix is the theme, and it is already written down in this file

`Theme.Geto.Tile` carries exactly these two items, with a comment explaining exactly this class of
problem: *"No dim, no window animation, and no starting preview: all three are ways for a window
that never draws to be seen anyway."* `Theme.Geto.Services` was given the dim on purpose — it is a
dialog and wants the background pushed back — but it was never given the other two, and it has the
same claim on them: **its window never draws anything.** Everything visible is the card inside it,
and the card has `DialogEntrance` of its own.

  * `windowDisablePreview` -> no splash. The starting window is suppressed, so the manager arrives
    as a card over whatever was on screen, which is what it is.
  * `windowAnimationStyle = @null` -> no window enter or exit. The card's own entrance is the only
    animation, and on the way out there is nothing left to fling at a corner.

Together with r5's start-before-finish ordering in `ServicesActivity`, pressing the IMD icon should
now be one transition: IMD's own, with the manager simply gone.

⚠ **Closing is instant too, and that is the trade.** The card currently fades with the window; with
no window animation it disappears the moment Close is pressed. `Theme.Geto.Tile` has behaved this
way since it was written and has drawn dialogs on it the whole time. Flagged to the author.

⚠ **`Theme.Geto.Shortcut` is deliberately left alone.** The long-press per-app shortcut has the
same missing `windowDisablePreview` and so the same splash, but the author has not reported it and
it is a different window on a different journey. Raised rather than changed in silence.

Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

THEMES = "app/src/main/res/values/themes.xml"

OLD = '''    <style name="Theme.Geto.Services" parent="Theme.Geto">
        <item name="android:windowIsTranslucent">true</item>
        <item name="android:windowBackground">@android:color/transparent</item>
        <item name="android:windowNoTitle">true</item>
        <item name="android:windowContentOverlay">@null</item>
        <item name="android:backgroundDimEnabled">true</item>
        <item name="android:colorBackgroundCacheHint">@null</item>
    </style>
'''

NEW = '''    <style name="Theme.Geto.Services" parent="Theme.Geto">
        <item name="android:windowIsTranslucent">true</item>
        <item name="android:windowBackground">@android:color/transparent</item>
        <item name="android:windowNoTitle">true</item>
        <item name="android:windowContentOverlay">@null</item>
        <item name="android:backgroundDimEnabled">true</item>
        <item name="android:colorBackgroundCacheHint">@null</item>
        <!--
          The two items Theme.Geto.Tile has carried all along, and this window has the same
          claim on them: it never draws anything. Everything visible is the card inside it,
          and the card animates itself in.

          Without windowDisablePreview, opening this from its launcher icon plays Android
          12's splash screen first - a black square with the app icon expanding out to fill
          the display - and only then fades the card in on top. The author, on the recording:
          "makes user feel like a full screen app is loading which does not look seamless".
          Translucency alone does not suppress it; this does.

          Without windowAnimationStyle, pressing the IMD icon flung the whole translucent
          window down at a corner and shrank it, as if a full-screen app were closing. That
          is the "very broken animation" on his fold. With no window animation there is
          nothing to fling, and IMD's own opening is the only thing on screen.

          Closing is instant as a result, where the card used to fade out with the window.
          That is the trade, and it is the behaviour Theme.Geto.Tile has always had.
        -->
        <item name="android:windowAnimationStyle">@null</item>
        <item name="android:windowDisablePreview">true</item>
    </style>
'''

CHECKS = [
    ('<item name="android:windowDisablePreview">true</item>', 2, "Tile had one; Services now too"),
    ('<item name="android:windowAnimationStyle">@null</item>', 2, "same for the animation style"),
    # Untouched by design: the dim is what makes this one a dialog rather than an invisible
    # worker, and removing it would be a different bug.
    ('<item name="android:backgroundDimEnabled">true</item>', 1, "Services keeps its dim"),
    ('<item name="android:backgroundDimEnabled">false</item>', 1, "and Tile keeps its lack of one"),
    ('<style name="Theme.Geto.Shortcut"', 1, "the shortcut theme is untouched"),
]


def main() -> int:
    path = ROOT / THEMES

    if not path.is_file():
        print(f"REFUSED: missing {THEMES}")
        return 1

    original = path.read_text(encoding="utf-8")

    if original.count(OLD) != 1:
        print(f"REFUSED: anchor matched {original.count(OLD)} time(s), expected 1")
        return 1

    if NEW in original:
        print("REFUSED: already applied — has this run before?")
        return 1

    text = original.replace(OLD, NEW, 1)

    for token, want, why in CHECKS:
        got = text.count(token)

        if got != want:
            print(f"REFUSED: {why} — {token!r} appears {got} time(s), expected {want}")
            return 1

        print(f"  checked  x{got:<3} {token[:56]!r}")

    path.write_text(text, encoding="utf-8")

    print("\n  ok  the manager's window no longer previews or animates")

    return 0


if __name__ == "__main__":
    sys.exit(main())
