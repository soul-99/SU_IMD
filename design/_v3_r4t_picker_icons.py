#!/usr/bin/env python3
"""v3-r4t — the accessibility and Display over other apps pickers show app icons.

    "can we display app icons in accessibility service & DOOA to manage dialogs and initialisation
     page"

The setup steps are the same composables as the dialogs, so both places get this from one change.

## ⚠ Icons for the listed packages only, never the whole device

`GetOverlayPackagesUseCase` carries a comment about exactly the mistake to avoid here: it used to
enumerate every installed application and rasterise an icon for each — *"a second or more of work,
all of it thrown away except the labels"*. So the new `getAppIcons` takes the same `Set<String>`
`getAppLabels` takes, and both pickers list a dozen rows or so. It rasterises at
`PICKER_ICON_SIZE`, the same 96px the app picker already uses for rows this size, not the 192px
default.

## ⚠ Both models get `icon` with an `equals` that ignores it

`ByteArray` has identity equality, so a data class holding one compares unequal to a
freshly-decoded copy of itself — and these lists are re-read on a poll. Left alone, every refresh
would look like a whole-list change and re-render the picker under the user's finger.
`InstalledAppData` already solves this and its solution is copied: `equals` compares the fields
that identify and describe the row, and skips the bytes.

⚠ **`enabled` and `allowed` stay *inside* `equals`.** They are what the row's supporting line
reports, so a service being switched off has to read as a change. Only the icon is excluded, and
only because it cannot compare.

⚠ **`icon` is defaulted to null**, so every existing construction — the orphan branch in the
accessibility wrapper, the host tests, the previews — keeps compiling and simply shows no icon
where there is none to show.

## Where the icon is drawn

`leadingContent` of the `ListItem`, in a `Row` after the checkbox: the checkbox stays at the
leading edge where it is in every other picker in the app, and the icon sits between it and the
label, which is the arrangement the Shizuku package picker already uses.

Every edit asserts its anchor matches exactly once. Nothing is written if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

IFACE = "domain/framework/src/main/kotlin/com/android/geto/domain/framework/PackageManagerWrapper.kt"

IMPL = "framework/package-manager/src/main/kotlin/com/android/geto/framework/packagemanager/DefaultPackageManagerWrapper.kt"

ACC_MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/AccessibilityServiceData.kt"

OVL_MODEL = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayPackageData.kt"

ACC_USE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetAccessibilityServicesUseCase.kt"

OVL_USE = "domain/use-case/src/main/kotlin/com/android/geto/domain/usecase/GetOverlayPackagesUseCase.kt"

ACC_DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/AccessibilityServicesDialog.kt"

OVL_DIALOG = "feature/settings/src/main/kotlin/com/android/geto/feature/settings/dialog/OverlayPackagesDialog.kt"

EDITS: list[tuple[str, str, str]] = [
    # ---------------- 1. The wrapper can be asked for a handful of icons ----------------
    (
        IFACE,
        """    /** Installation identities for the requested packages; missing packages are omitted. */""",
        """    /**
     * Small icons for the named packages only; missing or undecodable packages are omitted.
     *
     * ⚠ **The counterpart of [getAppLabels], and it exists for the same reason.**
     * [getInstalledApps] would answer this too, by enumerating every package on the device and
     * rasterising an icon for each — seconds of work and megabytes of bitmaps to put pictures on
     * a dozen rows. The pickers that need this know exactly which packages they are asking about.
     */
    suspend fun getAppIcons(packageNames: Set<String>): Map<String, ByteArray>

    /** Installation identities for the requested packages; missing packages are omitted. */""",
    ),
    (
        IMPL,
        """    override suspend fun getPackageIdentities(packageNames: Set<String>): Map<String, String> =""",
        """    override suspend fun getAppIcons(packageNames: Set<String>): Map<String, ByteArray> =
        withContext(ioDispatcher) {
            packageNames.mapNotNull { packageName ->
                val icon = runCatching {
                    androidDrawableWrapper.toByteArray(
                        drawable = packageManager.getApplicationIcon(packageName),
                        // The same 96px the app picker uses. These rows are the same size, and
                        // the 192px default is four times the pixels for no visible gain.
                        size = PICKER_ICON_SIZE,
                    )
                }.getOrNull() ?: return@mapNotNull null

                packageName to icon
            }.toMap()
        }

    override suspend fun getPackageIdentities(packageNames: Set<String>): Map<String, String> =""",
    ),
    # ---------------- 2. Both models carry one ----------------
    (
        ACC_MODEL,
        """data class AccessibilityServiceData(
    val id: String,
    val packageName: String,
    val label: String,
    val enabled: Boolean,
)""",
        """data class AccessibilityServiceData(
    val id: String,
    val packageName: String,
    val label: String,
    val enabled: Boolean,
    /**
     * The owning app's icon, or null when it has none, could not be decoded, or was not asked
     * for — an orphan row whose app is gone has no icon and is still worth showing.
     */
    val icon: ByteArray? = null,
) {
    // ⚠ **ByteArray compares by identity**, so a data-class equals holding one would report a
    // change on every re-read of this list and re-render the picker under the user's finger.
    // The same fix InstalledAppData already carries.
    //
    // `enabled` stays in: it is what the row's supporting line reports, so a service being
    // switched off has to read as a change. Only the bytes are left out, and only because they
    // cannot compare.
    override fun equals(other: Any?): Boolean = this === other ||
        (
            other is AccessibilityServiceData &&
                id == other.id &&
                packageName == other.packageName &&
                label == other.label &&
                enabled == other.enabled
            )

    override fun hashCode(): Int {
        var result = id.hashCode()

        result = 31 * result + packageName.hashCode()

        result = 31 * result + label.hashCode()

        result = 31 * result + enabled.hashCode()

        return result
    }
}""",
    ),
    (
        OVL_MODEL,
        """data class OverlayPackageData(
    val packageName: String,
    val label: String,
    val allowed: Boolean,
)""",
        """data class OverlayPackageData(
    val packageName: String,
    val label: String,
    val allowed: Boolean,
    /** The app's icon, or null when it has none, could not be decoded, or the app is gone. */
    val icon: ByteArray? = null,
) {
    // ByteArray compares by identity — see AccessibilityServiceData for the whole of why this
    // is written out. `allowed` stays in; only the bytes are left out.
    override fun equals(other: Any?): Boolean = this === other ||
        (
            other is OverlayPackageData &&
                packageName == other.packageName &&
                label == other.label &&
                allowed == other.allowed
            )

    override fun hashCode(): Int {
        var result = packageName.hashCode()

        result = 31 * result + label.hashCode()

        result = 31 * result + allowed.hashCode()

        return result
    }
}""",
    ),
    # ---------------- 3. The use cases fill them in ----------------
    (
        OVL_USE,
        """        val labels = runCatching {
            packageManagerWrapper.getAppLabels(names)
        }.getOrDefault(emptyMap())

        names
            .map { packageName ->
                OverlayPackageData(
                    packageName = packageName,
                    // A package with no entry in the installed list is one that has gone
                    // since; showing its name is more useful than dropping the row, because
                    // it may still be sitting in the selection waiting to be unticked.
                    label = labels[packageName] ?: packageName,
                    allowed = packageName in allowed,
                )
            }""",
        """        val labels = runCatching {
            packageManagerWrapper.getAppLabels(names)
        }.getOrDefault(emptyMap())

        // ⚠ **These packages only** — the same rule as the labels above, and for the reason the
        // paragraph there records. A dozen icons is nothing; every icon on the device is seconds.
        val icons = runCatching {
            packageManagerWrapper.getAppIcons(names)
        }.getOrDefault(emptyMap())

        names
            .map { packageName ->
                OverlayPackageData(
                    packageName = packageName,
                    // A package with no entry in the installed list is one that has gone
                    // since; showing its name is more useful than dropping the row, because
                    // it may still be sitting in the selection waiting to be unticked.
                    label = labels[packageName] ?: packageName,
                    allowed = packageName in allowed,
                    icon = icons[packageName],
                )
            }""",
    ),
    (
        ACC_USE,
        """class GetAccessibilityServicesUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val userDataRepository: UserDataRepository,
) {""",
        """class GetAccessibilityServicesUseCase @Inject constructor(
    private val accessibilityServicesWrapper: AccessibilityServicesWrapper,
    private val packageManagerWrapper: PackageManagerWrapper,
    private val userDataRepository: UserDataRepository,
) {""",
    ),
    (
        ACC_USE,
        """        return accessibilityServicesForPicker(
            services = accessibilityServicesWrapper.getAccessibilityServices(),
            heldAccessibilityServices = userData.heldAccessibilityServices,
            managedAccessibilityServices = userData.managedAccessibilityServices,
        ).sortedWith(
            compareByDescending<AccessibilityServiceData> { it.enabled }
                .thenBy(String.CASE_INSENSITIVE_ORDER) { it.label },
        )""",
        """        val services = accessibilityServicesForPicker(
            services = accessibilityServicesWrapper.getAccessibilityServices(),
            heldAccessibilityServices = userData.heldAccessibilityServices,
            managedAccessibilityServices = userData.managedAccessibilityServices,
        ).sortedWith(
            compareByDescending<AccessibilityServiceData> { it.enabled }
                .thenBy(String.CASE_INSENSITIVE_ORDER) { it.label },
        )

        // ⚠ **Read after the filter, not before it.** The picker shows a fraction of the
        // installed services, and asking for an icon per row of a list nobody will see is the
        // waste `GetOverlayPackagesUseCase` records having made once already.
        //
        // Several services can share one app, so the set is smaller again than the list.
        val icons = runCatching {
            packageManagerWrapper.getAppIcons(services.map { it.packageName }.toSet())
        }.getOrDefault(emptyMap())

        return services.map { service -> service.copy(icon = icons[service.packageName]) }""",
    ),
    (
        ACC_USE,
        "import com.android.geto.domain.framework.AccessibilityServicesWrapper\n",
        "import com.android.geto.domain.framework.AccessibilityServicesWrapper\n"
        "import com.android.geto.domain.framework.PackageManagerWrapper\n",
    ),
    # ---------------- 4. The rows draw them ----------------
    (
        ACC_DIALOG,
        """                            leadingContent = {
                                Checkbox(
                                    checked = checked,
                                    enabled = !own,
                                    onCheckedChange = { toggle() },
                                )
                            },""",
        """                            leadingContent = {
                                // Checkbox at the leading edge as in every other picker here,
                                // with the icon between it and the label — the arrangement the
                                // Shizuku package picker already uses.
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Checkbox(
                                        checked = checked,
                                        enabled = !own,
                                        onCheckedChange = { toggle() },
                                    )

                                    AsyncImage(
                                        modifier = Modifier
                                            .padding(start = 4.dp)
                                            .size(PICKER_ICON),
                                        model = service.icon,
                                        contentDescription = null,
                                    )
                                }
                            },""",
    ),
    (
        OVL_DIALOG,
        """                            leadingContent = {
                                Checkbox(
                                    checked = id in selected,
                                    onCheckedChange = { toggle() },
                                )
                            },""",
        """                            leadingContent = {
                                // The same arrangement as the accessibility picker beside it.
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Checkbox(
                                        checked = id in selected,
                                        onCheckedChange = { toggle() },
                                    )

                                    AsyncImage(
                                        modifier = Modifier
                                            .padding(start = 4.dp)
                                            .size(PICKER_ICON),
                                        model = app.icon,
                                        contentDescription = null,
                                    )
                                }
                            },""",
    ),
]

ICON_CONSTANT = """
/** The picker rows' app icon. Matches the 40dp slot the Shizuku package picker draws. */
private val PICKER_ICON = 36.dp
"""

IMPORTS = [
    (ACC_DIALOG, "import androidx.compose.foundation.layout.Row"),
    (ACC_DIALOG, "import androidx.compose.foundation.layout.size"),
    (ACC_DIALOG, "import androidx.compose.ui.Alignment"),
    (OVL_DIALOG, "import androidx.compose.foundation.layout.Row"),
    (OVL_DIALOG, "import androidx.compose.foundation.layout.size"),
    (OVL_DIALOG, "import androidx.compose.ui.Alignment"),
]

COIL = [
    (ACC_DIALOG, "import coil.compose.AsyncImage"),
    (OVL_DIALOG, "import coil.compose.AsyncImage"),
]

AFTER = [
    (IFACE, "suspend fun getAppIcons(", 1),
    (IMPL, "override suspend fun getAppIcons(", 1),
    (ACC_MODEL, "val icon: ByteArray? = null,", 1),
    (OVL_MODEL, "val icon: ByteArray? = null,", 1),
    (ACC_USE, "getAppIcons(", 1),
    (OVL_USE, "getAppIcons(", 1),
    (ACC_DIALOG, "AsyncImage(", 1),
    (OVL_DIALOG, "AsyncImage(", 1),
    (ACC_DIALOG, "private val PICKER_ICON = 36.dp", 1),
    (OVL_DIALOG, "private val PICKER_ICON = 36.dp", 1),
]


def add_import(text: str, statement: str, tail: bool = False) -> str:
    if statement in text:
        return text

    lines = text.splitlines(keepends=True)

    prefix = "import " if tail else "import androidx."

    indices = [i for i, line in enumerate(lines) if line.startswith(prefix)]

    if not indices:
        raise SystemExit(f"REFUSED: nowhere to put {statement!r}")

    if tail:
        lines.insert(indices[-1] + 1, statement + "\n")

        return "".join(lines)

    target = next((i for i in indices if lines[i] > statement + "\n"), indices[-1] + 1)

    lines.insert(target, statement + "\n")

    return "".join(lines)


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
            print(f"REFUSED: {relative}\n  {old.strip().splitlines()[0][:60]!r} matched {found} time(s)")
            return 1

        staged[relative] = text.replace(old, new, 1)

    for relative, statement in IMPORTS:
        staged[relative] = add_import(staged[relative], statement)

    for relative, statement in COIL:
        staged[relative] = add_import(staged[relative], statement, tail=True)

    # The size constant goes after the imports of each dialog.
    for relative in (ACC_DIALOG, OVL_DIALOG):
        lines = staged[relative].splitlines(keepends=True)

        last = max(i for i, line in enumerate(lines) if line.startswith("import "))

        lines.insert(last + 1, ICON_CONSTANT)

        staged[relative] = "".join(lines)

    for relative, token, expected in AFTER:
        found = staged[relative].count(token)

        if found != expected:
            print(f"REFUSED: {relative}\n  {token!r} occurs {found} time(s), expected {expected}")
            return 1

    # ⚠ Coil has to be on this module's compile classpath or the import is a build error rather
    # than a missing picture — and `feature/settings/build.gradle.kts` does not mention it, which
    # is what a first draft of this check tripped over. It arrives through `:design-system`, which
    # declares it as **api** rather than implementation; that keyword is the whole reason the
    # module already compiles `coil.compose.AsyncImage` in SettingsScreen.kt. Both facts are
    # checked, since either one alone would be a coincidence.
    build = (ROOT / "design-system/build.gradle.kts").read_text(encoding="utf-8")

    if "api(libs.coil.kt.compose)" not in build:
        print("REFUSED: design-system/build.gradle.kts\n  coil is no longer exported as api")
        return 1

    settings_screen = (
        ROOT / "feature/settings/src/main/kotlin/com/android/geto/feature/settings/SettingsScreen.kt"
    ).read_text(encoding="utf-8")

    if "import coil.compose.AsyncImage" not in settings_screen:
        print("REFUSED: feature/settings\n  nothing in this module imports coil today")
        return 1

    for relative, text in staged.items():
        (ROOT / relative).write_text(text, encoding="utf-8")

    print(f"  ok        {IFACE}  :: getAppIcons, for named packages only")
    print(f"  ok        both models carry an icon that equals() ignores")
    print(f"  ok        both pickers draw one, dialogs and setup steps alike")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
