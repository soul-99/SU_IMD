#!/usr/bin/env python3
"""
v3-r4m-d — the build failure: a public property exposing an internal type.

    e: AppSettingsViewModel.kt:248:9
       'public' property exposes its 'internal' type argument 'BlockedAppSettings'.

`blockedAppSettings` is a public `val` on a public ViewModel, and its `StateFlow` type argument
was `internal`. Kotlin refuses that outright: a caller outside the module could see the property
and not the type it hands back.

⚠ **Public, not an internal property.** Every other flow on this ViewModel is public and this is
one more of them; narrowing the property instead would make `AppSettingsViewModel` half public
and half not, for a value whose whole job is to be read by the screen. It also keeps the type on
the safe side of the *other* half of the visibility trap - `internal` is module-scoped, so a
composable in `app` that ever needed to name this would fail in Android Studio and pass here.

`GATED_KEYS` stays `private`: it is a file-level value read only inside this file, and file-level
`private` is exactly file-scoped.

⚠ **The sandbox cannot compile `feature/*`, so nothing here saw this.** `tools/check_exposed_internal.py`
is added with the fix - see `_v3_check_exposed_internal.py`.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

VM = (
    "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings/"
    "AppSettingsViewModel.kt"
)

OLD = """internal data class BlockedAppSettings("""

NEW = """data class BlockedAppSettings("""

# The KDoc gains the reason, so the next reader does not narrow it again.
OLD_DOC = """ * manager.
 */
internal data class BlockedAppSettings("""

NEW_DOC = """ * manager.
 *
 * ⚠ **Public, and it has to be.** [AppSettingsViewModel.blockedAppSettings] is a public property
 * on a public class, and Kotlin refuses a public declaration whose type argument is `internal` -
 * a caller outside the module would see the property and not the type it returns. That is a
 * compile error in Android Studio and invisible here, because the sandbox cannot build
 * `feature/*`. `tools/check_exposed_internal.py` now asks the question instead.
 */
data class BlockedAppSettings("""


def main() -> int:
    path = ROOT / VM

    if not path.is_file():
        print(f"REFUSED: missing {VM}")
        return 1

    original = path.read_text(encoding="utf-8")

    if OLD not in original:
        print("REFUSED: BlockedAppSettings is not internal — has this run before?")
        return 1

    if original.count(OLD_DOC) != 1:
        print(f"REFUSED: the doc anchor matched {original.count(OLD_DOC)} time(s), expected 1")
        return 1

    text = original.replace(OLD_DOC, NEW_DOC, 1)

    # The declaration is public now, and nothing else in the file was widened by accident.
    if "internal data class BlockedAppSettings" in text:
        print("REFUSED: the declaration is still internal")
        return 1

    if text.count("data class BlockedAppSettings(") != 1:
        print("REFUSED: BlockedAppSettings declared more than once")
        return 1

    # ⚠ GATED_KEYS must stay private: file-level private is file-scoped, which is exactly what
    # it wants, and widening it would put an implementation list on the module's surface.
    if "private val GATED_KEYS = listOf(" not in text:
        print("REFUSED: GATED_KEYS lost its private modifier")
        return 1

    was = {line for line in original.split("\n") if len(line) > 120}

    gained = [
        (n, len(line))
        for n, line in enumerate(text.split("\n"), 1)
        if len(line) > 120 and not line.lstrip().startswith("import ") and line not in was
    ]

    if gained:
        print(f"REFUSED: {VM} would gain lines over 120 chars: {gained}")
        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  ok        {VM}")
    print("  ~ BlockedAppSettings is public; GATED_KEYS stays private")
    print("\nwrote 1 file, 1 edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
