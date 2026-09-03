#!/usr/bin/env python3
"""
v3-r2b3b part 1 — the force-close popup can only be closed by its two buttons.

**The reported bug, and it is a bad one.** `PriorHideDialog` passed `onDismissRequest = onIgnore`,
and in `DialogContainer` that name is wired to two separate things: the platform's back press,
and the full-screen `Box`'s `detectTapGestures` — which exists only because turning
`usePlatformDefaultWidth` off leaves no real "outside" for the platform's own
`dismissOnClickOutside` to fire on. So a stray tap beside the card ran **Ignore**, which is the
permanent one: `DiscardPendingRevertsUseCase` wipes `settingStateBefore`,
`heldAccessibilityServices`, `heldOverlayPackages` and their identities. The author lost a real
device's holds that way.

⚠ **A parameter on the container rather than a hand-rolled `Dialog` in `PriorHideDialog`.**
Every width, centring and animation decision in this file was arrived at against real
regressions — the tablet width cap, the `compact` branch that must *not* animate, the empty tap
handler that stops an inside tap reaching the box behind. A second dialog built beside all that
would inherit none of it and would drift from the first change made here.

⚠ **Both halves, and both are needed.** `DialogProperties` alone still leaves the box's own tap
handler firing, and dropping the tap handler alone still leaves the back press. They are turned
off together or not at all, which is why one flag drives both.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DIALOG = "design-system/src/main/kotlin/com/android/geto/designsystem/component/Dialog.kt"

PRIOR = "design-system/src/main/kotlin/com/android/geto/designsystem/component/PriorHideDialog.kt"

DIALOG_EDITS: list[tuple[str, str]] = [
    # 1. The flag, beside the other two shape-of-the-window parameters.
    (
        """    compact: Boolean = false,
""",
        """    compact: Boolean = false,
    /**
     * Whether a back press or a tap beside the card closes this dialog.
     *
     * ⚠ **False is for a dialog whose dismissal would *do* something**, and there is exactly one:
     * the force-close popup, whose two answers are "restore everything" and "forget everything".
     * It had `onDismissRequest` wired to the second, so a stray tap beside the card silently
     * discarded a device's worth of pending reverts. A dialog with no harmless way out has no
     * business having an accidental one.
     *
     * Turns off **both** routes, because they are two different mechanisms: the platform's, via
     * [DialogProperties], and this file's own tap handler below — which exists because
     * `usePlatformDefaultWidth = false` leaves the platform nothing to call "outside".
     */
    dismissible: Boolean = true,
""",
    ),
    # 2. The compact branch: the platform is the only route there, so properties are enough.
    (
        """    if (compact) {
        Dialog(onDismissRequest = onDismissRequest) {
""",
        """    if (compact) {
        Dialog(
            onDismissRequest = onDismissRequest,
            properties = DialogProperties(
                dismissOnBackPress = dismissible,
                dismissOnClickOutside = dismissible,
            ),
        ) {
""",
    ),
    # 3. The wide branch: the platform's half.
    (
        """    Dialog(
        onDismissRequest = onDismissRequest,
        properties = DialogProperties(usePlatformDefaultWidth = false),
    ) {
""",
        """    Dialog(
        onDismissRequest = onDismissRequest,
        properties = DialogProperties(
            usePlatformDefaultWidth = false,
            // dismissOnClickOutside is left honest even though this window has no outside:
            // it costs nothing, and a future change that restores the platform width should
            // not have to remember to come back here.
            dismissOnBackPress = dismissible,
            dismissOnClickOutside = dismissible,
        ),
    ) {
""",
    ),
    # 4. And this file's own half — the tap handler that is the real "outside" here.
    (
        """            modifier = if (fullScreen) {
                // The page supplies its own insets - it is meant to reach the edges of what
                // is left after them.
                Modifier.fillMaxSize()
            } else {
                Modifier
                    .fillMaxSize()
                    .pointerInput(onDismissRequest) {
                        detectTapGestures { onDismissRequest() }
                    }
                    .padding(horizontal = 16.dp, vertical = 24.dp)
            },
""",
        """            modifier = if (fullScreen) {
                // The page supplies its own insets - it is meant to reach the edges of what
                // is left after them.
                Modifier.fillMaxSize()
            } else if (!dismissible) {
                // Same box, same padding, no tap handler: the card still centres and still
                // caps its width, and the space around it simply does nothing.
                Modifier
                    .fillMaxSize()
                    .padding(horizontal = 16.dp, vertical = 24.dp)
            } else {
                Modifier
                    .fillMaxSize()
                    .pointerInput(onDismissRequest) {
                        detectTapGestures { onDismissRequest() }
                    }
                    .padding(horizontal = 16.dp, vertical = 24.dp)
            },
""",
    ),
]

PRIOR_EDITS: list[tuple[str, str]] = [
    (
        """ * Two answers, and both of them end in the launch going ahead — which is why neither button
 * dismisses without doing something and there is no third way out.
""",
        """ * Two answers, and both of them end in the launch going ahead — which is why neither button
 * dismisses without doing something and there is no third way out.
 *
 * ⚠ **`dismissible = false`, and that is not a detail.** This dialog shipped once with
 * `onDismissRequest = onIgnore`, which handed the *permanent* answer to a back press and to a
 * tap beside the card. The author lost a device's pending reverts to a stray tap. There is no
 * harmless dismissal to offer here — every way out of this dialog changes the device — so it
 * has none, and `onDismissRequest` is left empty rather than pointed at either button.
""",
    ),
    (
        """    DialogContainer(modifier = modifier, onDismissRequest = onIgnore) {
""",
        """    DialogContainer(
        modifier = modifier,
        dismissible = false,
        // Unreachable while dismissible is false, and deliberately empty rather than either
        // answer: if it ever does become reachable, doing nothing is the safe outcome.
        onDismissRequest = {},
    ) {
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path.name} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    before = set(text.splitlines())

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    for line in set(text.splitlines()) - before:
        if len(line) > 120:
            problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    return text


def main() -> int:
    problems: list[str] = []

    dialog = ROOT / DIALOG
    prior = ROOT / PRIOR

    dialog_text = apply(dialog, DIALOG_EDITS, problems)
    prior_text = apply(prior, PRIOR_EDITS, problems)

    # The one thing that would make all of this pointless. Matched on the call rather than on
    # the phrase, because the doc comment above now quotes the phrase to explain the bug.
    if prior_text is not None and "DialogContainer(modifier = modifier, onDismissRequest" in prior_text:
        problems.append("the destructive answer is still wired to dismissal")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    dialog.write_text(dialog_text, encoding="utf-8")
    prior.write_text(prior_text, encoding="utf-8")

    print("ok — the force-close popup closes on its two buttons and nothing else")

    return 0


if __name__ == "__main__":
    sys.exit(main())
