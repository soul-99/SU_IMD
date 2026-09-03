# Icons the author is sending for the Settings tab

He sends one at a time and will say when he is **done**; only then are they drawn, and a template
for **both dark and light** goes to him before anything is built. His words: *"now i will attach
icons for every setting, afterwards when i say i am done draw all those in the settings tab and show
me template for both dark and light mode"*.

## A pattern worth naming

Four of the seven settled so far need **no new asset at all**: the author keeps pointing at icons the
app already draws somewhere else, and in every case `:design-system` already holds a byte-identical
copy of the `:app` tile drawable, put there in an earlier round for exactly this reason. Checking
before drawing has saved four redundant vectors. ⚠ Always compare `pathData` rather than trusting
the filenames — `ic_hide_glyph` and `ic_hidden_glyph` are named for the *outcome of pressing them*,
not for the state they depict, which is the opposite of what "the hidden icon" sounds like.

## Rules that apply to the whole set

- Tinted **`MaterialTheme.colorScheme.outline`** — the off-switch rim grey (`#8F9285` dark,
  `#75796C` light). His words: *"display all icons in grey the same grey which is the outline colour
  of off toggles"*.
- They go on the eleven `SettingsColumn` rows — the ones with **no toggle**. `SettingsColumn` needs a
  `leading` slot; rows without an icon stay unchanged.
- ⚠ Everything arriving is a **raster**, and several are multi-colour. A single grey tint replaces
  every non-transparent pixel, so a coloured source would come out as a flat silhouette with its
  internal detail gone. Each one is therefore **redrawn as a monochrome `VectorDrawable`** — which is
  also the only form that stays crisp at any density.
- The **Logics card** illustration is the exception and stays coloured: *"no logics icon stay
  coloured"*. Already built in r26 as `feature/settings/res/drawable/ic_logics.xml`.

## Received

| # | file | row | what he sent | his changes |
|---|---|---|---|---|
| 01 | `01-theme.png` | **Theme** | sun disc with a crescent bite out of it, eight flare lines | ⚠ **thicker flare lines** than the source |
| 02 | `02-language.png` | **Language** | two overlapping speech bubbles, one with `A`, one with `文`, outlined | — |
| 03 | `03-icon-style.png` | **Icon style** | the Android Studio mark: green droid head on a dark eight-point star, on a blue circle | ⚠ **line diagram**, ⚠ **solid droid head with hollow eyes**, ⚠ **smaller circle radius so it sits closer to the star** |
| 05 | `05-app-drawer-and-all-apps.png` | **App drawer shortcuts** *and* the **All Apps tab** | a 3x3 grid of rounded squares | ⚠ **Two homes, and only one of them is grey.** The settings row takes the `outline` tint like the rest of the set; the tab-switcher icon (`TopLevelDestination.kt:44`, currently `GetoIcons.Apps` = Material's dotted grid) keeps the tab bar's own selected/unselected colours — greying it would make the selected tab unreadable. So this becomes one shared `GetoIcons` entry drawn once and tinted by each call site. |
| 06 | *(none needed)* | **Settings to hide** | *"use the settings hidden icon from hide settings qs toggle"* — the struck-out eye the tile shows **while settings are hidden** | ✅ `HideTileService` uses `ic_hidden_tile` for that state, and `design-system/res/drawable/ic_hidden_glyph.xml` is a byte-identical copy already reachable. Use `designR.drawable.ic_hidden_glyph`. |
| 07 | *(none needed)* | **Revert to default** | *"use the icon we use for rev to def qs toggle"* | ✅ `app/res/drawable/ic_revert_tile.xml` is byte-identical to `design-system/res/drawable/ic_revert_glyph.xml`. Use `designR.drawable.ic_revert_glyph`. |
| 08 | `08-accessibility.png` | **Accessibility services** | the standard accessibility mark: a spread-armed figure inside a heavy ring | Solid figure, hollow ring — already a clean two-tone silhouette, so it redraws as a monochrome vector with nothing to decide. |
| 09 | `09-dooa.png` | **Display over other apps** | a large rounded-square outline with a smaller square at its top-right and a diagonal arrow rising into it — the standard overlay / picture-in-picture mark | ⚠ **The file he sent is a watermarked Adobe Stock preview** (`AdobeStock_245435050`, checkerboard and all). It is not going in the repo, and does not need to: like every icon in this set it is being **redrawn** as an original monochrome vector, and this particular arrangement — two nested squares and an arrow — is a generic UI convention rather than anything protectable. The reference stays in `design/` as a note of what he asked for; nothing derived from the file itself ships. |
| 10 | *(none needed)* | **Hiding framework** | *"similar icons as settings hidden ... of hide settings qs toggle"* — the struck-out eye | ⚠ **Collides with row 06.** `Settings to hide` already takes `ic_hidden_glyph`. See the note below. |
| 11 | *(none needed)* | **Unhiding framework** | *"... and settings visible"* — the open eye | `HideTileService` shows `ic_hide_tile` in the visible state; `design-system/res/drawable/ic_hide_glyph.xml` is byte-identical. |
| 04 | *(none needed)* | **Setting manager toggles** | *"show monochrome settings manager QS icon"* — the app's own Quick Settings tile glyph | ✅ **already in the repo and reachable.** `app/res/drawable/ic_services_tile.xml` is the tile, but its path data is byte-identical to `design-system/res/drawable/ic_services_glyph.xml`, which `:feature:settings` can already see. Nothing to add — just `designR.drawable.ic_services_glyph`. Copying the `:app` one would have been a duplicate *and* an upward module dependency. |

## All eleven rows are now spoken for

## ⚠ One collision to settle before drawing

He said *"similar icons"* rather than *the same*, and it matters, because taking the two glyphs
literally gives **two rows the identical icon**:

| row | section | would take |
|---|---|---|
| Settings to hide | App functions | `ic_hidden_glyph` — struck-out eye |
| **Hiding framework** | Advanced | `ic_hidden_glyph` — *the same* |

Two readings, both defensible:

- **A · Share them.** The rows sit in different sections and both genuinely are about hiding. Zero
  new assets, and the repetition arguably reinforces that the two settings are related.
- **B · Draw variants.** Same eye motif, plus a mark that says *mechanism* rather than *state* — the
  framework pair is a choice of **how**, not a switch for **what**. Keeps all eleven rows distinct.

Both go in the template for him to pick. Nothing is drawn until he says he is done.


## Also queued for the r27 build (not icons)

1. **Support page** — remove the link from point 2; put a button below that line, styled like the
   share button, with the GitHub icon already used in the soul_99 popup and the text
   `view Project on GitHub`. ⚠ Lowercase *view*, capital *Project* — **confirmed deliberate**, so it
   goes in verbatim.
2. **soul_99 dialog** — title becomes two lines, the second `(Dr. Utkarsh Rajput)`.
3. **FOSS footer** — `Long live FOSS !` then, on the next line, `(Free and Open Source Software)`.
   Note his spacing before the `!` is kept as written.
4. **Shell panel** — back to the dark colour in dark mode (r25 pinned it to sepia in both), but
   brighter than the old `#212121`. ⚠ The prompt green has to come back with it: r25 collapsed
   `SHELL_PROMPT_LIGHT`/`_DARK` into one when the panel stopped varying, and a dark panel needs the
   light prompt again.
5. **Progressive UI blur on by default** — flips `progressiveBlurOn`'s resolved default. proto3 has
   no custom defaults, which is why that field is named for the non-default state; turning it on by
   default means the *field name* is now backwards and the resolution has to be re-read rather than
   just flipped.
6. **Hiding framework dialog** — a `(RECOMMENDED)` tag under the **IMD defaults** option, exactly as
   the memory function already has one.
