#!/usr/bin/env python3
"""v3-r4p — the Favourites tab opens in grid view on a fresh install.

    "set grid view as the default in the Favourites tab"

## ⚠ Why this cannot be done in the mapper alone

`FavouriteViewList = 0` is the proto3 default, so an install that has never chosen decodes to
**List** — and is indistinguishable, on the wire, from one that chose List deliberately.
Answering the zero value with Grid would therefore also flip every upgrader who picked List, and
they would have to set it back.

The house pattern for exactly this is already here, on `restartShizuku`:

    restartShizuku = if (it.restartShizukuSet) it.restartShizuku else true,

⚠ *"A proto3 bool cannot tell 'the user switched this off' from 'the user has never seen it'"* —
the comment on field 10. Same question, same answer: a companion marker.

## The four moving parts

1. **proto field 70, `favouriteAppsViewSet`.** False until something writes the view.
2. **The read** answers `Grid` while the marker is false, and the stored value once it is true.
3. **`updateFavouriteAppsView` sets the marker**, so *any* explicit choice sticks — including
   choosing List, which is the case this exists to protect.
4. **`MigrateFrameworksUseCase` sets it to `upgraded`.** An install that existed before v3 keeps
   whatever it had; a fresh one does not, and gets Grid. This is the same one-shot that already
   answers "fresh or upgrade", so no new marker and no new launch ordering is introduced.

⚠ **The migration is where this belongs and not, say, `GetoApplication`.** It already reads
`setupNoticeVersion` at the only moment the two can still be told apart, and it already runs
exactly once per install.

⚠ **Re-run protoc after this** or `check11_proto` reads a stale `/tmp/protogen`.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"

SOURCE = "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

DOMAIN_REPO = "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"

DATA_REPO = "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

MIGRATION = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/MigrateFrameworksUseCase.kt"

EDITS: list[tuple[str, str, str]] = [
    # 1. The proto field, immediately before the reserved block that closes the message.
    (
        PROTO,
        """  bool upgradedToV3 = 69;

  // 9 was favouriteAppsTapAction.""",
        """  bool upgradedToV3 = 69;

  /*
   * Whether anything has ever chosen the Favourites tab's view.
   *
   * ⚠ Field 8 cannot answer this by itself. FavouriteViewList is 0, so "never chosen" and
   * "chose List" decode identically - and the default is now Grid, so telling them apart is
   * the difference between a new install opening on a grid and an upgrader losing the list
   * they picked. Same shape as restartShizukuSet on field 10, for the same reason.
   *
   * Set by any write of field 8, and by MigrateFrameworksUseCase for an install that existed
   * before v3.
   */
  bool favouriteAppsViewSet = 70;

  // 9 was favouriteAppsTapAction.""",
    ),
    # 2. The read.
    (
        SOURCE,
        """            favouriteAppsView = it.favouriteAppsView.asFavouriteAppsView(),""",
        """            // Grid until something chooses, at the author's instruction. The marker is
            // what separates "never chosen" from "chose List": both store 0 in field 8.
            favouriteAppsView = if (it.favouriteAppsViewSet) {
                it.favouriteAppsView.asFavouriteAppsView()
            } else {
                FavouriteAppsView.Grid
            },""",
    ),
    # 3. Any explicit choice sets the marker, in the same write as the value.
    (
        SOURCE,
        """    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        userPreferences.updateData {
            it.copy {
                this.favouriteAppsView = favouriteAppsView.asFavouriteAppsViewProto()
            }
        }
    }""",
        """    suspend fun updateFavouriteAppsView(favouriteAppsView: FavouriteAppsView) {
        userPreferences.updateData {
            it.copy {
                this.favouriteAppsView = favouriteAppsView.asFavouriteAppsViewProto()

                // ⚠ In the same write as the value, never a second one. Choosing List is the
                // case this protects, and a marker that landed separately could be lost
                // between the two - leaving a deliberate List reading as "never chosen" and
                // being answered with Grid on the next launch.
                this.favouriteAppsViewSet = true
            }
        }
    }""",
    ),
    # 4. The marker's own setter, for the migration.
    (
        SOURCE,
        """    suspend fun updateUpgradedToV3(upgraded: Boolean) {""",
        """    suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferences.updateData {
            it.copy {
                favouriteAppsViewSet = set
            }
        }
    }

    suspend fun updateUpgradedToV3(upgraded: Boolean) {""",
    ),
    # 5. The domain interface.
    (
        DOMAIN_REPO,
        """    suspend fun updateUpgradedToV3(upgraded: Boolean)""",
        """    suspend fun updateUpgradedToV3(upgraded: Boolean)

    /**
     * Records that the Favourites tab's view is somebody's answer rather than the default.
     *
     * The stored view is Grid until this is true, so an upgrade has to set it to keep the list
     * it was already showing.
     */
    suspend fun updateFavouriteAppsViewSet(set: Boolean)""",
    ),
    # 6. The implementation.
    (
        DATA_REPO,
        """    override suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferencesDataSource.updateUpgradedToV3(upgraded = upgraded)
    }""",
        """    override suspend fun updateUpgradedToV3(upgraded: Boolean) {
        userPreferencesDataSource.updateUpgradedToV3(upgraded = upgraded)
    }

    override suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferencesDataSource.updateFavouriteAppsViewSet(set = set)
    }""",
    ),
    # 7. The migration, beside the marker it already writes for the same question.
    (
        MIGRATION,
        """        userDataRepository.updateUpgradedToV3(upgraded = upgraded)

        if (!upgraded) return@withContext""",
        """        userDataRepository.updateUpgradedToV3(upgraded = upgraded)

        // ⚠ **Before the return below, because a fresh install needs the `false` too.** The
        // Favourites tab now opens on Grid until something has chosen, and an install that
        // existed before v3 has chosen - by using the tab at all - even though field 8 cannot
        // say so. Setting it to `upgraded` keeps an upgrader's list and leaves a new install
        // on the grid.
        userDataRepository.updateFavouriteAppsViewSet(set = upgraded)

        if (!upgraded) return@withContext""",
    ),
]

# Asserted present after the run, so a later reader can see the pair is wired end to end.
AFTER = [
    (PROTO, "bool favouriteAppsViewSet = 70;", 1),
    (SOURCE, "favouriteAppsViewSet", 3),
    (SOURCE, "FavouriteAppsView.Grid", 1),
    (DOMAIN_REPO, "updateFavouriteAppsViewSet", 1),
    (DATA_REPO, "updateFavouriteAppsViewSet", 2),
    (MIGRATION, "updateFavouriteAppsViewSet", 1),
]


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

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(
                f"REFUSED: {relative}\n  {token!r} occurs {found} time(s) after the edits, "
                f"expected {expected}",
            )
            return 1

    # FavouriteAppsView is now named in the mapper block; it was already imported for the
    # update below, but a missing import here is a compile failure in a module the sandbox
    # cannot build, so it is asserted rather than assumed.
    if "import com.android.geto.domain.model.FavouriteAppsView" not in staged[SOURCE]:
        print(f"REFUSED: {SOURCE}\n  FavouriteAppsView is used in the mapper but not imported")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {PROTO}  :: favouriteAppsViewSet = 70")
    print(f"  ok        {SOURCE}  :: reads Grid until chosen; any write sets the marker")
    print(f"  ok        {DOMAIN_REPO}  :: updateFavouriteAppsViewSet")
    print(f"  ok        {DATA_REPO}  :: updateFavouriteAppsViewSet")
    print(f"  ok        {MIGRATION}  :: set = upgraded, before the fresh-install return")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")
    print("\n⚠ re-run protoc, or check11_proto reads a stale /tmp/protogen")

    return 0


if __name__ == "__main__":
    sys.exit(main())
