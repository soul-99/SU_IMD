#!/usr/bin/env python3
"""v3-r4s — the closing page has a body again.

    "the new last initialisation page i am unable to see its contents, just made with emoji by
     soul99 and button"

## ⚠ The diagnosis, exactly

`SetupCompletePage` is built the way a full-screen page with a pinned footer has to be:

    Column(fillMaxSize) {
        Column(Modifier.weight(1f).verticalScroll(...)) { ...the whole body... }
        Row { signature ... "Let's go" }
    }

`weight(1f)` means *"take what is left of my parent's height"*. r4r then wrapped that page inside
`ConfigurePage`, which is itself a `verticalScroll` Column - and a scrolling parent measures its
children with an **unbounded** height constraint, because that is what scrolling means. There is
no "what is left" of infinity to take, so the weighted child is given zero height and the body
disappears. The footer, which has no weight, is the one thing that still measures - which is
precisely what the author sees: the signature and the button, and nothing above them.

⚠ **Not a padding or an inset problem, and not fixable with either.** A `weight` inside a
`verticalScroll` is always this bug; the only repair is to stop nesting them.

So `ConfigurePage` goes - it existed only to wrap this one page - and the flow draws
`SetupCompletePage` directly, where it gets the bounded height it was written for.

## ⚠ Back moves into the scrolling body, and the approved footer is untouched

`ConfigurePage` carried the Back button, so it has to land somewhere. It goes at the end of the
body, after the last item, rather than into the footer: the footer's two contents - the signature
at the left and "Let's go" at the right - are the layout the author approved from a template, and
squeezing a third control in beside them would be redrawing something already agreed without
asking. At the end of a page whose job is "you are done", Back is a way out for someone who wants
one, not something the page should lead with.

It keeps its `null` meaning: `remindersOnly` opens straight here, and Back there would drop the
user into a page asking them to grant what they already granted.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SCREEN = "app/src/main/kotlin/com/android/geto/onboarding/SetupScreen.kt"

PAGE = "app/src/main/kotlin/com/android/geto/onboarding/SetupCompletePage.kt"

EDITS: list[tuple[str, str, str]] = [
    # 1. The flow draws the page itself.
    (
        SCREEN,
        """            ConfigurePage(
                modifier = modifier,
                onBack = onBack,
                onContinue = onContinue,
            )""",
        """            // ⚠ **Drawn directly, not wrapped.** It was inside a `verticalScroll` Column
            // until r4s, and its body — a `weight(1f)` child — was therefore measured against an
            // unbounded height and given none of it. The page needs a bounded parent, which is
            // what this branch is.
            SetupCompletePage(
                modifier = modifier,
                onBack = onBack,
                onContinue = onContinue,
            )""",
    ),
    # 2. And the wrapper goes, since drawing this page was all it did.
    (
        SCREEN,
        """/**
 * Page two. Nothing here is enforced — both items are optional in the sense that the app
 * runs without them — but both are silent when unconfigured, which is exactly the kind of
 * thing that gets diagnosed as "the app is broken" months later.
 */
@Composable
private fun ConfigurePage(
    modifier: Modifier = Modifier,
    onBack: (() -> Unit)?,
    onContinue: () -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxSize()
            .windowInsetsPadding(WindowInsets.safeDrawing)
            .verticalScroll(rememberScrollState())
            .padding(24.dp),
    ) {
        Spacer(modifier = Modifier.height(8.dp))

        // ⚠ **The help content is gone from here, at the author's instruction** - "remove the
        // help/readme page after initialisation as its not needed now". `SetupHelpContent` is
        // untouched and still backs the Help button in Settings; only this use of it went.
        //
        // What is here instead closes the flow rather than explaining the app: what to do next,
        // and a button into it.
        SetupCompletePage(onContinue = onContinue)

        if (onBack != null) {
            TextButton(
                modifier = Modifier.fillMaxWidth(),
                onClick = onBack,
            ) {
                Text(text = stringResource(R.string.setup_back))
            }
        }
    }
}

""",
        "",
    ),
    # 3. The page takes the Back button the wrapper used to carry.
    (
        PAGE,
        """internal fun SetupCompletePage(
    modifier: Modifier = Modifier,
    onContinue: () -> Unit,
) {""",
        """internal fun SetupCompletePage(
    modifier: Modifier = Modifier,
    /**
     * Null when there is nowhere to go back to.
     *
     * `remindersOnly` opens straight at this page, and a Back there would drop the user into a
     * page asking them to grant what they have already granted.
     */
    onBack: (() -> Unit)? = null,
    onContinue: () -> Unit,
) {""",
    ),
    (
        PAGE,
        """            SubPoint(text = stringResource(R.string.setup_done_4_3))

            Spacer(modifier = Modifier.height(16.dp))
        }""",
        """            SubPoint(text = stringResource(R.string.setup_done_4_3))

            // ⚠ **At the end of the body, not in the footer.** The footer is the signature at
            // the left and "Let's go" at the right, which is the layout approved from a
            // template; a third control wedged in beside them would be redrawing that without
            // asking. Back belongs to whoever goes looking for it.
            if (onBack != null) {
                TextButton(
                    modifier = Modifier.padding(top = 12.dp),
                    onClick = onBack,
                ) {
                    Text(text = stringResource(R.string.setup_back))
                }
            }

            Spacer(modifier = Modifier.height(16.dp))
        }""",
    ),
]

IMPORTS = [
    (PAGE, "import androidx.compose.material3.TextButton"),
]

AFTER = [
    # The wrapper is gone, root and branch.
    (SCREEN, "ConfigurePage", 0),
    (SCREEN, "SetupCompletePage(", 1),
    # ⚠ Counted from the file: the string moved out of SetupScreen.kt entirely.
    (SCREEN, "R.string.setup_back", 0),
    (PAGE, "R.string.setup_back", 1),
    # Declaration, the guard, and the onClick.
    (PAGE, "onBack", 3),
    # Still exactly one weighted, scrolling body and one footer.
    (PAGE, ".weight(1f)", 1),
    (PAGE, "verticalScroll(rememberScrollState())", 1),
    (PAGE, "Arrangement.SpaceBetween", 1),
]

# ⚠ Removing a function can orphan an import, and an orphan is a warning that becomes an error
# under `allWarningsAsErrors`. Each of these was counted in the file before the edit and is still
# used by another page in it; the assertion below is what proves that, rather than the counting.
STILL_USED = [
    "fillMaxSize()",
    "windowInsetsPadding(WindowInsets.safeDrawing)",
    "verticalScroll(rememberScrollState())",
    "TextButton(",
    "Spacer(",
    "Column(",
]


def add_import(text: str, statement: str) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    indices = [i for i, line in enumerate(lines) if line.startswith("import androidx.")]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


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

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    for token in STILL_USED:
        # The import line itself is not a use, so a single occurrence means only the import is
        # left — which is the orphan this is looking for.
        if staged[SCREEN].count(token) < 1:
            print(f"REFUSED: {SCREEN}\n  {token!r} has no remaining use; its import is orphaned")
            return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {SCREEN}  :: the closing page is drawn directly, wrapper gone")
    print(f"  ok        {PAGE}  :: bounded height, so the body measures; Back at its end")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
