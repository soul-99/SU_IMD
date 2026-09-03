# Logic flowcharts

The pictures in **SUIMD.md → IMD app logics** are rendered from the `.mmd` files here, so a
change to a logic is a change to text rather than to a drawing.

Each diagram is a mermaid `flowchart`; `build_logics.py` renders all fifteen to
`docs/logics/*.png` in the app's own dark Material 3 palette.

```
npm i -g @mermaid-js/mermaid-cli   # provides mmdc
python3 tools/logics/build_logics.py
```

⚠ **`build_logics.py` is the source of truth, not the `.mmd` files.** It writes them on every run,
so an edit made directly to a `.mmd` is overwritten the next time anybody renders. Edit the
`add(...)` call instead.

## Colours

| | |
|---|---|
| plain card | a step, or a decision |
| **red** | this run stops here |
| **green** | a branch that exists only on the **Shevery** fork |

## Keeping them true

Update these whenever a logic changes, as part of preparing a release — and **re-read them against
the code at each release**, not only when you remember having changed something.

⚠ **The second half is the one that matters, and r30 is why.** All fourteen diagrams had drifted,
several into saying the opposite of what the code does: a confirmation poll that v3 had deleted, a
warning notification whose notifier is `@Deprecated` with no consumer anywhere, a manager card
whose rows had since become user-configurable — and, worst, **the Shevery fork, which reached
thirty-two source files without appearing in a single drawing**. Auto unhide settings, a whole
feature, had no diagram at all.

None of that came from somebody changing a logic and forgetting the picture. It accumulated because
nothing ever forced the two to be compared. **A diagram is only current if something makes it so.**
