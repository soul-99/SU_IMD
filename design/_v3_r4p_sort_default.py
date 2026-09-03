#!/usr/bin/env python3
"""v3-r4p — the Favourites tab sorts A-Z on a fresh install.

    "also in fav tab make A-z sorting default"

The same shape as `_v3_r4p_grid_default.py`, one field along, and for the same reason:
`FavouriteSortCustom = 0` is the proto3 default, so "never chosen" and "chose Custom" decode
identically. A marker separates them - field **71**, `sortFavouriteAppsSet`.

## ⚠ Why Custom cannot simply be answered with Alphabetical

Reordering is not a preference somebody sets in a dialog; it is a drag. `FavouriteAppsScreen`
already switches to `SortFavouriteApps.Custom` the moment an order is saved:

    // Reordering only makes sense against the custom order, so switch to it
    // rather than saving an order the user cannot see.
    onUpdateSortFavouriteApps(SortFavouriteApps.Custom)

So a user who drags their favourites into an order is moved to Custom by that act, and the write
sets the marker with it - their order is safe. Nobody is left on Alphabetical with an invisible
custom order, and nobody who dragged is dragged back.

The upgrade half is the same one-shot as the grid default: `MigrateFrameworksUseCase` sets the
marker to `upgraded`, so an install that existed before v3 keeps the order it was showing.

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
    # 1. Field 71, beside the view marker it mirrors.
    (
        PROTO,
        """  bool favouriteAppsViewSet = 70;

  // 9 was favouriteAppsTapAction.""",
        """  bool favouriteAppsViewSet = 70;

  /*
   * Whether anything has ever chosen the Favourites tab's sort order.
   *
   * ⚠ Field 7 cannot answer this by itself, exactly as field 8 cannot: FavouriteSortCustom is
   * 0, so "never chosen" and "chose Custom" decode identically - and the default is now
   * Alphabetical.
   *
   * Set by any write of field 7, which includes the write the reorder dialog makes when an
   * order is saved, and by MigrateFrameworksUseCase for an install that existed before v3.
   */
  bool sortFavouriteAppsSet = 71;

  // 9 was favouriteAppsTapAction.""",
    ),
    # 2. The read.
    (
        SOURCE,
        """            sortFavouriteApps = it.sortFavouriteApps.asSortFavouriteApps(),""",
        """            // A-Z until something chooses, at the author's instruction. Saving a custom
            // order is itself a choice - the reorder dialog writes Custom - so nobody ends up
            // sorted alphabetically over an order they dragged.
            sortFavouriteApps = if (it.sortFavouriteAppsSet) {
                it.sortFavouriteApps.asSortFavouriteApps()
            } else {
                SortFavouriteApps.Alphabetical
            },""",
    ),
    # 3. Any explicit choice sets the marker, in the same write as the value.
    (
        SOURCE,
        """                this.sortFavouriteApps = sortFavouriteApps.asSortFavouriteAppsProto()""",
        """                this.sortFavouriteApps = sortFavouriteApps.asSortFavouriteAppsProto()

                // In the same write as the value, for the reason on favouriteAppsViewSet.
                this.sortFavouriteAppsSet = true""",
    ),
    # 4. The marker's own setter.
    (
        SOURCE,
        """    suspend fun updateFavouriteAppsViewSet(set: Boolean) {""",
        """    suspend fun updateSortFavouriteAppsSet(set: Boolean) {
        userPreferences.updateData {
            it.copy {
                sortFavouriteAppsSet = set
            }
        }
    }

    suspend fun updateFavouriteAppsViewSet(set: Boolean) {""",
    ),
    # 5. The domain interface.
    (
        DOMAIN_REPO,
        """    suspend fun updateFavouriteAppsViewSet(set: Boolean)""",
        """    suspend fun updateFavouriteAppsViewSet(set: Boolean)

    /**
     * Records that the Favourites tab's sort order is somebody's answer rather than the default.
     *
     * The stored order is Alphabetical until this is true, so an upgrade has to set it to keep
     * the order it was already showing.
     */
    suspend fun updateSortFavouriteAppsSet(set: Boolean)""",
    ),
    # 6. The implementation.
    (
        DATA_REPO,
        """    override suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferencesDataSource.updateFavouriteAppsViewSet(set = set)
    }""",
        """    override suspend fun updateFavouriteAppsViewSet(set: Boolean) {
        userPreferencesDataSource.updateFavouriteAppsViewSet(set = set)
    }

    override suspend fun updateSortFavouriteAppsSet(set: Boolean) {
        userPreferencesDataSource.updateSortFavouriteAppsSet(set = set)
    }""",
    ),
    # 7. The migration, beside the marker it already writes for the same question.
    (
        MIGRATION,
        """        userDataRepository.updateFavouriteAppsViewSet(set = upgraded)""",
        """        userDataRepository.updateFavouriteAppsViewSet(set = upgraded)

        // The Favourites tab's other default, and the same argument: an install that existed
        // before v3 has an order it was already showing, and field 7 cannot say whether it
        // was chosen.
        userDataRepository.updateSortFavouriteAppsSet(set = upgraded)""",
    ),
]

AFTER = [
    (PROTO, "bool sortFavouriteAppsSet = 71;", 1),
    (SOURCE, "sortFavouriteAppsSet", 3),
    (SOURCE, "SortFavouriteApps.Alphabetical", 1),
    (DOMAIN_REPO, "updateSortFavouriteAppsSet", 1),
    (DATA_REPO, "updateSortFavouriteAppsSet", 2),
    (MIGRATION, "updateSortFavouriteAppsSet", 1),
    # The view marker's own wiring is untouched by this run: its read, its write inside
    # updateFavouriteAppsView, and the assignment in its setter's body - three, plus the one
    # this script's own comment adds when it points at it. The first draft expected three and
    # was refused by its own assertion, which was right and the expectation was not.
    (SOURCE, "favouriteAppsViewSet", 4),
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

    if "import com.android.geto.domain.model.SortFavouriteApps" not in staged[SOURCE]:
        print(f"REFUSED: {SOURCE}\n  SortFavouriteApps is used in the mapper but not imported")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {PROTO}  :: sortFavouriteAppsSet = 71")
    print(f"  ok        {SOURCE}  :: reads A-Z until chosen; any write sets the marker")
    print(f"  ok        {DOMAIN_REPO}  :: updateSortFavouriteAppsSet")
    print(f"  ok        {DATA_REPO}  :: updateSortFavouriteAppsSet")
    print(f"  ok        {MIGRATION}  :: set = upgraded, beside the view marker")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")
    print("\n⚠ re-run protoc, or check11_proto reads a stale /tmp/protogen")

    return 0


if __name__ == "__main__":
    sys.exit(main())
