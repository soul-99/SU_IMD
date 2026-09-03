#!/usr/bin/env python3
"""
v3-r1 — autoHideEverEnabled through UserData, the datastore and the repository.

Proto field 60 (added by hand alongside its comment). This threads it through the four Kotlin
layers, following exactly how diagnosticsEnabled is wired.

Every anchor must match exactly once. Nothing is written if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EDITS = [
    # 1. the domain model
    (
        "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt",
        "    val diagnosticsEnabled: Boolean,\n",
        "    val diagnosticsEnabled: Boolean,\n"
        "    /**\n"
        "     * Whether the user has ever switched IMD+ on themselves.\n"
        "     *\n"
        "     * Consent, recorded once, as opposed to [autoHideEnabled] which is the current\n"
        "     * state. It is what lets the switch offer to put IMD's own detector back when the\n"
        "     * detector is the only thing missing, instead of only refusing to move.\n"
        "     */\n"
        "    val autoHideEverEnabled: Boolean,\n",
    ),
    # 2. the datastore reader
    (
        "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt",
        "            diagnosticsEnabled = it.diagnosticsEnabled,\n",
        "            diagnosticsEnabled = it.diagnosticsEnabled,\n"
        "            autoHideEverEnabled = it.autoHideEverEnabled,\n",
    ),
    # 3. the datastore writer
    (
        "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt",
        "    suspend fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean) {",
        "    /**\n"
        "     * Records that the user has switched IMD+ on at least once.\n"
        "     *\n"
        "     * One-way on purpose. Switching IMD+ off is not a withdrawal of consent to use it\n"
        "     * - it already retires the detector, which is the whole of what off means - so\n"
        "     * clearing this would only make the next setup ask again for no reason.\n"
        "     */\n"
        "    suspend fun markAutoHideEverEnabled() {\n"
        "        userPreferences.updateData {\n"
        "            it.copy { this.autoHideEverEnabled = true }\n"
        "        }\n"
        "    }\n"
        "\n"
        "    suspend fun updateAutoUnhideUsedFor(onAppLaunch: Boolean, onTile: Boolean) {",
    ),
    # 4. the repository interface
    (
        "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt",
        "    suspend fun updateDiagnosticsEnabled(enabled: Boolean)\n",
        "    suspend fun updateDiagnosticsEnabled(enabled: Boolean)\n"
        "\n"
        "    /** Records that IMD+ has been switched on by the user at least once. */\n"
        "    suspend fun markAutoHideEverEnabled()\n",
    ),
    # 5. the repository implementation
    (
        "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt",
        "    override suspend fun updateDiagnosticsEnabled(enabled: Boolean) {\n"
        "        userPreferencesDataSource.updateDiagnosticsEnabled(enabled = enabled)",
        "    override suspend fun markAutoHideEverEnabled() {\n"
        "        userPreferencesDataSource.markAutoHideEverEnabled()\n"
        "    }\n"
        "\n"
        "    override suspend fun updateDiagnosticsEnabled(enabled: Boolean) {\n"
        "        userPreferencesDataSource.updateDiagnosticsEnabled(enabled = enabled)",
    ),
]


def main() -> int:
    planned: dict[Path, str] = {}

    for rel, old, new in EDITS:
        path = ROOT / rel

        if not path.is_file():
            print(f"REFUSED, nothing written: missing {rel}")
            return 1

        text = planned.get(path, path.read_text(encoding="utf-8"))
        found = text.count(old)

        if found != 1:
            print(f"REFUSED, nothing written: {rel}")
            print(f"  anchor matched {found} time(s), expected 1: {old.strip()[:64]!r}")
            return 1

        planned[path] = text.replace(old, new, 1)

    for path, text in planned.items():
        over = [
            n for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ")
        ]
        was = [
            n for n, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1)
            if len(line) > 120 and not line.lstrip().startswith("import ")
        ]
        if len(over) > len(was):
            print(f"REFUSED, nothing written: {path.relative_to(ROOT)} gains long lines")
            return 1

    for path, text in planned.items():
        path.write_text(text, encoding="utf-8")

    print(f"wrote {len(planned)} file(s), {len(EDITS)} edit(s)")
    for rel, _, _ in EDITS:
        print(f"  ok  {rel.split('/')[-1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
