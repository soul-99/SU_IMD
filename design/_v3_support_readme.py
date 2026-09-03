#!/usr/bin/env python3
"""
v3-r1 — the README's Support section, brought in line with the dialog.

The author asked for the dialog changes "as repo readme" too, so the same four moves:
  * the two intro lines swap
  * point 1 is rewritten, with the aside on its own line
  * 'Report' links to the issue tracker
  * 'Join' links to the subreddit

Asserts each anchor matches exactly once; writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"

ISSUES = "https://github.com/soul-99/SU_IMD/issues/"
REDDIT = "https://www.reddit.com/r/SU_IMD/"

FREE = "**<u>You can do these for free, if you want to support this project and keep it alive.</u>**"
SUCCESSION = (
    "I want it to be taken over by a more capable developer in future, as my profession does "
    "not allow me to maintain it all year round."
)

EDITS = [
    # the swap, done as one block so the order cannot come out half-applied
    (f"{FREE}\n\n{SUCCESSION}", f"{SUCCESSION}\n\n{FREE}"),
    # point 1
    (
        "1. Spread the word if you can - it helps the community, and I don't need any credit "
        "or mention. [Share the repo »](https://github.com/soul-99/SU_IMD)",
        "1. **Share this project/app to community. This is most helpful and will help to keep "
        "the project alive.**\n   (I don't need any credit or mentions) "
        "[Share the repo »](https://github.com/soul-99/SU_IMD)",
    ),
    # 'Report' is the link, not 'Report bugs'
    (
        "3. [Report bugs](https://github.com/soul-99/SU_IMD/issues) in the main repo.",
        f"3. [Report]({ISSUES}) bugs in the main repo.",
    ),
    # 'Join' gains one
    (
        "4. Join discussions.",
        f"4. [Join]({REDDIT}) discussions.",
    ),
]


def main() -> int:
    text = README.read_text(encoding="utf-8")

    for old, new in EDITS:
        found = text.count(old)

        if found != 1:
            print(f"REFUSED, nothing written: anchor matched {found} time(s), expected 1")
            print(f"  {old[:88]!r}")
            return 1

        text = text.replace(old, new, 1)

    # The swap must actually have swapped.
    if text.index(SUCCESSION) > text.index(FREE):
        print("REFUSED, nothing written: the two intro lines are still in the old order")
        return 1

    README.write_text(text, encoding="utf-8")

    print(f"README.md: {len(EDITS)} edit(s) applied")
    print("  intro lines swapped, point 1 rewritten, 'Report' and 'Join' linked")

    return 0


if __name__ == "__main__":
    sys.exit(main())
