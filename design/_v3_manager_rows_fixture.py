#!/usr/bin/env python3
"""
v3-r9 — teach the host-test UserData fixture the two new fields.

`_v3_manager_rows_storage.py` added `managerRows` and `autoHideDetectorManagedV3` to [UserData],
and the fixture every domain test builds from is a full constructor call, so it stops compiling
until it names them. Split from that script rather than folded into it: this file is the test
harness, not the app, and a change to one should be readable without the other.

Both take the value a fresh install has, and both say so:

  * `ManagerRows.Default` is every row shown, which is what the manager has always drawn. A test
    written before this preference existed must go on seeing all six.
  * `autoHideDetectorManagedV3 = true` marks the one-shot migration as already run, which is the
    same choice `autoUnhideResetV3` and `upgradedToV3` beside it already make — a fixture is a
    settled install, not one mid-upgrade, so a migration firing inside a test would be answering a
    question the test did not ask.

Nothing is written if the anchor does not match exactly once.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TESTS = "tools/host-tests/DomainLogicTests.kt"

OLD = '''    // r4o: fixtures are upgrades, so anything gated on "existed before v3" is reachable.
    upgradedToV3 = true,
)
'''

NEW = '''    // r4o: fixtures are upgrades, so anything gated on "existed before v3" is reachable.
    upgradedToV3 = true,
    // r9: every row shown, which is what the manager drew before this preference existed. A test
    // written against the old six-row card goes on seeing six rows.
    managerRows = ManagerRows.Default,
    // r9: already migrated, for the same reason autoUnhideResetV3 above is - a fixture is a
    // settled install rather than one mid-upgrade.
    autoHideDetectorManagedV3 = true,
)
'''

IMPORT_OLD = "import com.android.geto.domain.model.ManualRevertTarget\n"

IMPORT_NEW = (
    "import com.android.geto.domain.model.ManagerRows\n"
    "import com.android.geto.domain.model.ManualRevertTarget\n"
)


def main() -> int:
    path = ROOT / TESTS

    original = path.read_text(encoding="utf-8")

    text = original

    for old, new in ((OLD, NEW), (IMPORT_OLD, IMPORT_NEW)):
        if text.count(old) != 1:
            print(f"REFUSED: anchor {old.strip()[:60]!r} matched {text.count(old)} time(s)")
            return 1

        if new in original:
            print("REFUSED: already applied")
            return 1

        text = text.replace(old, new, 1)

    for token, want in (("managerRows = ManagerRows.Default,", 1),
                        ("autoHideDetectorManagedV3 = true,", 1),
                        ("import com.android.geto.domain.model.ManagerRows", 1)):
        if text.count(token) != want:
            print(f"REFUSED: {token!r} appears {text.count(token)} time(s), expected {want}")
            return 1

    path.write_text(text, encoding="utf-8")

    print("  ok  the fixture names both new fields")

    return 0


if __name__ == "__main__":
    sys.exit(main())
