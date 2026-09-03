#!/usr/bin/env python3
"""
v3-r10 — storage for the two new User interface switches.

## `progressiveBlurOff` (75)

The author's *"Progressive UI blur"*, and he asked for it **enabled by default**. proto3 has no
custom defaults: an unwritten bool decodes to false, so a field named for the on state would
arrive off on every fresh install and on every install that upgrades into this build.

⚠ **Stored as the negation for that reason, and unwrapped once at the boundary.** The field is
"off", so unwritten means on; [UserData.progressiveBlur] is the positive reading and is the only
thing the rest of the app ever sees. The alternative the file already uses beside
`autoUnhideOnAppLaunch` - a second "was this ever configured" flag - costs a field and exists there
only because that setting had to distinguish a deliberate off from an untouched install. This one
does not: off is off however it got there.

## `oledBackground` (76)

The author's *"OLED background mode"*, *"pure black UI background"*. Default off, which proto3
gives for nothing, so it is stored the way it reads.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = (
    "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/"
    "user_preferences.proto"
)

SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

USERDATA = "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"

REPO = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"

REPO_IMPL = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

# --- proto ------------------------------------------------------------------------------

PROTO_OLD = '''  bool autoHideDetectorManagedV3 = 74;
'''

PROTO_NEW = '''  bool autoHideDetectorManagedV3 = 74;

  // Whether the bottom-edge blur is switched OFF - the author's "Progressive UI blur", which he
  // asked for enabled by default.
  //
  // Named for the off state on purpose. proto3 decodes an unwritten bool to false, so a field
  // named for the on state would arrive off on every fresh install and on every upgrade into
  // this build, which is the opposite of what was asked for. UserData.progressiveBlur is the
  // positive reading and is what the app uses; this spelling exists only here.
  bool progressiveBlurOff = 75;

  // The author's "OLED background mode": pure black backgrounds instead of the dark scheme's
  // near-black. Off by default, which is what an unwritten bool already means.
  bool oledBackground = 76;
'''

# --- datastore: read ----------------------------------------------------------------------

READ_OLD = '''            managerRows = ManagerRows.decode(it.managerRowsList),
'''

READ_NEW = '''            managerRows = ManagerRows.decode(it.managerRowsList),
            // ⚠ The one inversion in this file, and the proto comment on field 75 is why:
            // the stored field is "off" so that an install which has never touched the switch
            // gets the blur. Everything above this line reads the positive.
            progressiveBlur = !it.progressiveBlurOff,
            oledBackground = it.oledBackground,
'''

# --- datastore: write ---------------------------------------------------------------------

WRITE_OLD = '''    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
'''

WRITE_NEW = '''    suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferences.updateData {
            // Inverted here to match, and nowhere else. See the proto comment on field 75.
            it.copy { progressiveBlurOff = !enabled }
        }
    }

    suspend fun updateOledBackground(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { oledBackground = enabled }
        }
    }

    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
'''

# --- UserData -----------------------------------------------------------------------------

UD_OLD = '''    val managerRows: Map<ManualRevertTarget, Boolean>,
'''

UD_NEW = '''    val managerRows: Map<ManualRevertTarget, Boolean>,
    /**
     * Whether the bottom-edge blur is drawn — the author's "Progressive UI blur".
     *
     * ⚠ **The positive reading of a field stored as its negation**, so that an install which
     * has never seen the switch gets the blur. The inversion happens once, in the data source;
     * nothing above it needs to know.
     *
     * ⚠ **Not the same question as whether a real blur is possible.** A blur of what is behind
     * needs API 31, and below that the band is the gradient alone — see `ProgressiveBottomBlur`
     * in :design-system, which is where that split lives. This flag only says whether the band
     * is drawn at all.
     */
    val progressiveBlur: Boolean,
    /**
     * Pure black backgrounds instead of the dark scheme's near-black — "OLED background mode".
     *
     * ⚠ **Dark only.** It changes nothing in a light scheme, and the row that sets it is not
     * drawn while the app is light, at the author's instruction.
     */
    val oledBackground: Boolean,
'''

# --- repository ---------------------------------------------------------------------------

REPO_OLD = '''    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>)
'''

REPO_NEW = '''    /** Which rows the settings manager draws - see `UserData.managerRows`. */
    suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>)

    /** The bottom-edge blur - see `UserData.progressiveBlur`. Takes the positive. */
    suspend fun updateProgressiveBlur(enabled: Boolean)

    /** Pure black backgrounds in the dark scheme - see `UserData.oledBackground`. */
    suspend fun updateOledBackground(enabled: Boolean)
'''

IMPL_OLD = '''    override suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateManagerRows(states = states)
    }
'''

IMPL_NEW = '''    override suspend fun updateManagerRows(states: Map<ManualRevertTarget, Boolean>) {
        userPreferencesDataSource.updateManagerRows(states = states)
    }

    override suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferencesDataSource.updateProgressiveBlur(enabled = enabled)
    }

    override suspend fun updateOledBackground(enabled: Boolean) {
        userPreferencesDataSource.updateOledBackground(enabled = enabled)
    }
'''

EDITS = [
    (PROTO, PROTO_OLD, PROTO_NEW),
    (SOURCE, READ_OLD, READ_NEW),
    (SOURCE, WRITE_OLD, WRITE_NEW),
    (USERDATA, UD_OLD, UD_NEW),
    (REPO, REPO_OLD, REPO_NEW),
    (REPO_IMPL, IMPL_OLD, IMPL_NEW),
]

CHECKS = [
    (PROTO, "bool progressiveBlurOff = 75;", 1, "the blur field is numbered 75"),
    (PROTO, "bool oledBackground = 76;", 1, "and OLED 76"),
    (PROTO, "= 75;", 1, "75 is used once"),
    (PROTO, "= 76;", 1, "and 76 once"),
    # ⚠ The inversion must exist exactly once in the whole app. Two of them cancel out silently.
    (SOURCE, "!it.progressiveBlurOff", 1, "read as the negation, once"),
    (SOURCE, "progressiveBlurOff = !enabled", 1, "written as the negation, once"),
    (USERDATA, "val progressiveBlur: Boolean", 1, "UserData carries the positive"),
    (USERDATA, "val oledBackground: Boolean", 1, "and the OLED flag"),
    (REPO, "suspend fun updateProgressiveBlur", 1, "the repository declares it"),
    (REPO, "suspend fun updateOledBackground", 1, "both of them"),
    (REPO_IMPL, "override suspend fun updateProgressiveBlur", 1, "and implements it"),
    (REPO_IMPL, "override suspend fun updateOledBackground", 1, "both of them"),
]


def main() -> int:
    planned: dict[Path, str] = {}

    originals: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED: missing {rel}")
            return 1

        originals.setdefault(path, path.read_text(encoding="utf-8"))

        text = planned.get(path, originals[path])

        found = text.count(old)

        if found != 1:
            print(
                f"REFUSED: {Path(rel).name}\n  anchor {old.strip()[:66]!r}\n"
                f"  matched {found} time(s), expected exactly 1",
            )
            return 1

        if new in originals[path]:
            print(f"REFUSED: {Path(rel).name} already carries the replacement")
            return 1

        planned[path] = text.replace(old, new, 1)

        print(f"  ok        {Path(rel).name:36s} {old.strip().splitlines()[0][:38]}")

    for rel, token, want, why in CHECKS:
        got = planned[ROOT / rel].count(token)

        if got != want:
            print(f"REFUSED: {Path(rel).name}: {why} — {token!r} x{got}, expected {want}")
            return 1

        print(f"  checked   {Path(rel).name:36s} x{got}  {token[:36]!r}")

    def over(source: str) -> set[str]:
        return {
            line
            for line in source.split("\n")
            if len(line) > 120 and not line.lstrip().startswith("import ")
        }

    for path, text in planned.items():
        if over(text) - over(originals[path]):
            print(f"REFUSED: {path.name} would gain lines over 120 chars")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"\n  ok  wrote {len(planned)} file(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
