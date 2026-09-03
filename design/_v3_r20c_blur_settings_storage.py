#!/usr/bin/env python3
"""
r20c — the three blur numbers become stored preferences.

⚠ **A companion `blurCustomised` bool rather than three sentinel zeroes.** proto3 decodes an
unwritten int32 to 0, and 0 is a value two of these three sliders can legitimately land on — a
tint of nothing is exactly what somebody who wants a bare blur will pick. The bool is how "never
opened the dialog" is told apart from "chose these", which is the same shape `favouriteAppsViewSet`
and `sortFavouriteAppsSet` already use in this proto for the same reason.

⚠ **The defaults live in `:design-system`, not here.** A preview, a test harness and an install
that has never opened the dialog must all draw the same thing, and the place that draws is the
place that should own the number.

Computes every edit in memory, asserts every match count, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PROTO = ROOT / "data/datastore-proto/src/main/proto/com/android/geto/data/datastore/proto/user_preferences.proto"

SOURCE = ROOT / "data/datastore/src/main/kotlin/com/android/geto/data/datastore/UserPreferencesDataSource.kt"

MODEL = ROOT / "domain/model/src/main/kotlin/com/android/geto/domain/model/UserData.kt"

REPO = ROOT / "domain/repository/src/main/kotlin/com/android/geto/domain/repository/UserDataRepository.kt"

IMPL = ROOT / "data/repository/src/main/kotlin/com/android/geto/data/repository/DefaultUserDataRepository.kt"

VIEWMODEL = ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsViewModel.kt"

TESTS = ROOT / "tools/host-tests/DomainLogicTests.kt"

failures: list[str] = []

pending: list[tuple[Path, str]] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def swap(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    found = text.count(old)

    if check(found == count, f"{label}: found {found}x, expected {count}"):
        return text.replace(old, new, count)

    return text


# ------------------------------------------------------------ 1. proto

proto = PROTO.read_text(encoding="utf-8")

proto = swap(
    proto,
    "  bool progressiveBlurOn = 79;\n",
    """  bool progressiveBlurOn = 79;

  // The three numbers behind the blur - the author's r20 sliders, which govern the page bands and
  // the settings manager's frosted window together.
  //
  // ⚠ A companion bool rather than three sentinel zeroes. proto3 decodes an unwritten int32 to 0,
  // and 0 is a value two of these sliders can legitimately land on: a tint of nothing is what
  // somebody who wants a bare blur will pick. This is how "never opened the dialog" is told apart
  // from "chose these", and it is the shape favouriteAppsViewSet on 69 already uses.
  //
  // The defaults the app falls back to are in :design-system beside the code that draws with
  // them, not here - a preview and a fresh install have to agree and only one of them has a
  // datastore.
  bool blurCustomised = 80;

  // Radius in dp, tint as a percentage, ramp length in dp. Stored in the units the sliders show,
  // so a value means the same thing in the store, on the slider and in the draw.
  int32 blurRadiusDp = 81;

  int32 blurTintPercent = 82;

  int32 blurFadeDp = 83;
""",
    "proto: blur fields",
)

pending.append((PROTO, proto))

# ------------------------------------------------------------ 2. data source

source = SOURCE.read_text(encoding="utf-8")

source = swap(
    source,
    "            progressiveBlur = it.progressiveBlurOn,\n",
    """            progressiveBlur = it.progressiveBlurOn,
            // ⚠ **All three or none of them.** The bool says whether the dialog has ever been
            // saved; reading each number against its own zero would let a half-written state
            // exist, and there is no way to write one from the dialog.
            blurRadiusDp = if (it.blurCustomised) it.blurRadiusDp else DEFAULT_RADIUS_DP,
            blurTintPercent = if (it.blurCustomised) it.blurTintPercent else DEFAULT_TINT_PERCENT,
            blurFadeDp = if (it.blurCustomised) it.blurFadeDp else DEFAULT_FADE_DP,
""",
    "source: read",
)

source = swap(
    source,
    """    suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { progressiveBlurOn = enabled }
        }
    }
""",
    """    suspend fun updateProgressiveBlur(enabled: Boolean) {
        userPreferences.updateData {
            it.copy { progressiveBlurOn = enabled }
        }
    }

    /**
     * The three slider values, written together with the bool that says they were chosen.
     *
     * Clamped here as well as on the sliders: this is the last place before the store, and a
     * radius of four hundred is a frame budget rather than a preference.
     */
    suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        userPreferences.updateData {
            it.copy {
                blurCustomised = true

                this.blurRadiusDp = radiusDp.coerceIn(BLUR_RADIUS_RANGE)

                this.blurTintPercent = tintPercent.coerceIn(BLUR_TINT_RANGE)

                this.blurFadeDp = fadeDp.coerceIn(BLUR_FADE_RANGE)
            }
        }
    }
""",
    "source: write",
)

source = swap(
    source,
    "import com.android.geto.domain.model.UserData\n",
    "import com.android.geto.designsystem.theme.BLUR_FADE_RANGE\n"
    "import com.android.geto.designsystem.theme.BLUR_RADIUS_RANGE\n"
    "import com.android.geto.designsystem.theme.BLUR_TINT_RANGE\n"
    "import com.android.geto.designsystem.theme.DEFAULT_FADE_DP\n"
    "import com.android.geto.designsystem.theme.DEFAULT_RADIUS_DP\n"
    "import com.android.geto.designsystem.theme.DEFAULT_TINT_PERCENT\n"
    "import com.android.geto.domain.model.UserData\n",
    "source: imports",
)

pending.append((SOURCE, source))

# ------------------------------------------------------------ 3. the model

model = MODEL.read_text(encoding="utf-8")

model = swap(
    model,
    "    val oledBackground: Boolean,\n",
    """    val oledBackground: Boolean,
    /** The author's r20 blur sliders: radius in dp, tint as a percentage, ramp length in dp. */
    val blurRadiusDp: Int,
    val blurTintPercent: Int,
    val blurFadeDp: Int,
""",
    "model: fields",
)

pending.append((MODEL, model))

# ------------------------------------------------------------ 4. the repository

repo = REPO.read_text(encoding="utf-8")

repo = swap(
    repo,
    "    suspend fun updateOledBackground(enabled: Boolean)\n",
    "    suspend fun updateOledBackground(enabled: Boolean)\n\n"
    "    /** The three blur sliders, written together — see `UserData.blurRadiusDp`. */\n"
    "    suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int)\n",
    "repo: interface",
)

pending.append((REPO, repo))

impl = IMPL.read_text(encoding="utf-8")

impl = swap(
    impl,
    """    override suspend fun updateOledBackground(enabled: Boolean) {
        userPreferencesDataSource.updateOledBackground(enabled = enabled)
""",
    """    override suspend fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        userPreferencesDataSource.updateBlurSettings(
            radiusDp = radiusDp,
            tintPercent = tintPercent,
            fadeDp = fadeDp,
        )
    }

    override suspend fun updateOledBackground(enabled: Boolean) {
        userPreferencesDataSource.updateOledBackground(enabled = enabled)
""",
    "impl: method",
)

pending.append((IMPL, impl))

# ------------------------------------------------------------ 5. the view model

viewmodel = VIEWMODEL.read_text(encoding="utf-8")

viewmodel = swap(
    viewmodel,
    """    fun updateOledBackground(enabled: Boolean) {""",
    """    fun updateBlurSettings(radiusDp: Int, tintPercent: Int, fadeDp: Int) {
        viewModelScope.launch {
            userDataRepository.updateBlurSettings(
                radiusDp = radiusDp,
                tintPercent = tintPercent,
                fadeDp = fadeDp,
            )
        }
    }

    fun updateOledBackground(enabled: Boolean) {""",
    "viewmodel: method",
)

pending.append((VIEWMODEL, viewmodel))

# ------------------------------------------------------------ 6. the host tests' sample UserData

tests = TESTS.read_text(encoding="utf-8")

tests = swap(
    tests,
    "    oledBackground = false,\n",
    "    oledBackground = false,\n"
    "    blurRadiusDp = 14,\n"
    "    blurTintPercent = 50,\n"
    "    blurFadeDp = 72,\n",
    "tests: sample UserData",
)

pending.append((TESTS, tests))

# ------------------------------------------------------------ commit

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

for path, text in pending:
    path.write_text(text, encoding="utf-8")

    print(f"wrote {path.relative_to(ROOT).as_posix()}")

print("ok")
