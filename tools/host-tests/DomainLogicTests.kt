/*
 *
 *   Copyright 2026 soul_99 (suIMD)
 *
 *   Licensed under the GNU General Public License v3.0 (the "License");
 *   you may not use this file except in compliance with the License.
 *   You may obtain a copy of the License at
 *
 *       https://www.gnu.org/licenses/gpl-3.0
 *
 */

/**
 * Host-side assertions for the pure logic in :domain:model.
 *
 * :domain:model is a plain JVM library with no dependencies, so it compiles and runs on
 * a desktop JVM with nothing but the Kotlin stdlib. That makes the accessibility-service
 * arithmetic and the favourites ordering testable without a device or an emulator, which
 * matters because those are the two places where a quiet off-by-one would silently
 * corrupt the user's system settings.
 *
 * Run with tools/host-tests/run.sh — it fails the build on the first bad assertion.
 */

import com.android.geto.domain.model.AccessibilityServiceData
import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppListOrder
import com.android.geto.domain.model.AppListOrdering
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.AppSettingTemplate
import com.android.geto.domain.model.AutoHideRequirements
import com.android.geto.domain.model.AutoUnhideRequirements
import com.android.geto.domain.model.IconStyle
import com.android.geto.domain.model.appSettingBlocked
import com.android.geto.domain.model.autoHideFailureBackoffMillis
import com.android.geto.domain.model.screenLockAfterTile
import com.android.geto.domain.model.tileAfterScreenLock
import com.android.geto.domain.model.autoHideSwitchOn
import com.android.geto.domain.model.FavouriteAppsOrdering
import com.android.geto.domain.model.HidingFramework
import com.android.geto.domain.model.canHide
import com.android.geto.domain.model.hideOwnsRevert
import com.android.geto.domain.model.hidingFrameworkFor
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.ManualRevertResult
import com.android.geto.domain.model.ManagerRows
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.manualTargetForKey
import com.android.geto.domain.model.memoryHeldComponents
import com.android.geto.domain.model.memoryHoldsSettings
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.strandsSettings
import com.android.geto.domain.model.deviceWideMemoryWanted
import com.android.geto.domain.model.deviceWideRecordAfterRevert
import com.android.geto.domain.model.deviceWideSnapshotId
import com.android.geto.domain.model.manualChangeRecord
import com.android.geto.domain.model.masterPillOnOrder
import com.android.geto.domain.model.masterPillOrder
import com.android.geto.domain.model.revertNamesApp
import com.android.geto.domain.model.settingsOutsideRevertDefaults
import com.android.geto.domain.model.SettingSnapshot.settingOf
import com.android.geto.domain.model.UnhidingFramework
import com.android.geto.domain.model.unhidingFrameworkFor
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.RevertDefaults
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.TaskerIntegration
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.accessibilityServicesForPicker
import com.android.geto.domain.model.effectiveRevertDefaults
import com.android.geto.domain.model.effectiveSettingsToHide
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.memoryHeldComponents
import com.android.geto.domain.model.overlayAlreadyWithdrawn
import com.android.geto.domain.model.memoryHoldsSettings
import com.android.geto.domain.model.settingsHidden
import com.android.geto.domain.model.OverlayBlockReason
import com.android.geto.domain.model.manageShizukuEffective
import com.android.geto.domain.model.overlayBlockReasons
import com.android.geto.domain.model.overlayManageableInManager
import com.android.geto.domain.model.withoutOverlayWhenUnmanaged
import com.android.geto.domain.model.withoutShizukuWhenNoIntents

private var passed = 0
private val failures = mutableListOf<String>()

private fun check(name: String, condition: Boolean) {
    if (condition) {
        passed++
    } else {
        failures += name
    }
}

private fun <T> checkEquals(name: String, expected: T, actual: T) {
    if (expected == actual) {
        passed++
    } else {
        failures += "$name\n      expected: $expected\n      actual:   $actual"
    }
}

private const val TALKBACK = "com.google.android.marvin.talkback/com.google.android.marvin.talkback.TalkBackService"
private const val SWIPE = "dev.utk.swipesearch/dev.utk.swipesearch.SwipeService"
private const val TASKER = "net.dinglisch.android.taskerm/net.dinglisch.android.taskerm.MyAccessibilityService"
private const val BIXBY = "com.samsung.bixby/com.samsung.bixby.BixbyService"

private fun app(
    componentName: String,
    label: String,
    system: Boolean = false,
) = LauncherAppsActivityInfo(
    componentName = componentName,
    packageName = componentName.substringBefore('/'),
    activityIcon = null,
    activityLabel = label,
    firstInstallTime = 0L,
    lastUpdateTime = 0L,
    isSystem = system,
)

private fun setting(
    key: String,
    enabled: Boolean = true,
    valueOnLaunch: String = "0",
    valueOnRevert: String = "1",
) = AppSetting(
    id = 0,
    enabled = enabled,
    settingType = SettingType.SECURE,
    componentName = "com.bank/com.bank.Main",
    label = key,
    key = key,
    valueOnLaunch = valueOnLaunch,
    valueOnRevert = valueOnRevert,
)

private fun accessibilityHoldTests() {
    // 1. A managed service that is on gets removed, and the untouched ones keep their order.
    val a = AccessibilityServicePlan.hold(
        managed = listOf(SWIPE),
        currentlyEnabled = listOf(TALKBACK, SWIPE, TASKER),
        heldByOthers = emptyList(),
    )
    checkEquals("hold removes only the managed service", listOf(TALKBACK, TASKER), a.enabledAfter)
    checkEquals("hold claims what it removed", listOf(SWIPE), a.held)
    check("hold reports the list changed", a.listChanged)

    // 2. Managing a service that is already off must not claim it, or the revert would
    //    switch on something the user had deliberately disabled.
    val b = AccessibilityServicePlan.hold(
        managed = listOf(SWIPE, BIXBY),
        currentlyEnabled = listOf(TALKBACK, SWIPE),
        heldByOthers = emptyList(),
    )
    checkEquals("hold ignores managed services that are already off", listOf(SWIPE), b.held)
    checkEquals("hold leaves unmanaged services alone", listOf(TALKBACK), b.enabledAfter)

    // 3. Nothing selected in settings means nothing happens at all.
    val c = AccessibilityServicePlan.hold(
        managed = emptyList(),
        currentlyEnabled = listOf(TALKBACK, SWIPE),
        heldByOthers = emptyList(),
    )
    check("hold with no managed services claims nothing", c.held.isEmpty())
    check("hold with no managed services leaves the list alone", !c.listChanged)
    checkEquals("hold with no managed services is identity", listOf(TALKBACK, SWIPE), c.enabledAfter)

    // 4. Managed services selected, but none of them running and none held elsewhere.
    val d = AccessibilityServicePlan.hold(
        managed = listOf(BIXBY),
        currentlyEnabled = listOf(TALKBACK),
        heldByOthers = emptyList(),
    )
    check("hold claims nothing when nothing managed is enabled", d.held.isEmpty())
    check("hold reports no list change", !d.listChanged)

    // 5. THE cross-app case. App A already holds SWIPE down, so it is not in the enabled
    //    list any more. App B must still claim it, otherwise A's revert switches SWIPE
    //    back on while B is in the foreground.
    val e = AccessibilityServicePlan.hold(
        managed = listOf(SWIPE),
        currentlyEnabled = listOf(TALKBACK),
        heldByOthers = listOf(SWIPE),
    )
    checkEquals("hold claims a service another app already holds", listOf(SWIPE), e.held)
    check("hold does not need to rewrite the list for an already-held service", !e.listChanged)

    // 6. Several managed at once, and duplicates in the managed list collapse.
    val f = AccessibilityServicePlan.hold(
        managed = listOf(SWIPE, TASKER, SWIPE),
        currentlyEnabled = listOf(TALKBACK, SWIPE, TASKER),
        heldByOthers = emptyList(),
    )
    checkEquals("hold handles several managed services", listOf(TALKBACK), f.enabledAfter)
    checkEquals("hold collapses duplicates in the managed list", listOf(SWIPE, TASKER), f.held)

    // 7. Empty device list.
    val g = AccessibilityServicePlan.hold(
        managed = listOf(SWIPE),
        currentlyEnabled = emptyList(),
        heldByOthers = emptyList(),
    )
    check("hold on an empty device list claims nothing", g.held.isEmpty())
    checkEquals("hold on an empty device list stays empty", emptyList<String>(), g.enabledAfter)
}

private fun accessibilityReleaseTests() {
    // 8. The straightforward case.
    val a = AccessibilityServicePlan.release(
        released = listOf(SWIPE),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = listOf(TALKBACK),
    )
    checkEquals("release puts the service back", listOf(TALKBACK, SWIPE), a.enabledAfter)
    checkEquals("release reports what it re-enabled", listOf(SWIPE), a.restored)

    // 9. THE lesson from the previous project: the user turned the service back on by
    //    hand while the target app was open. Releasing must not produce a duplicate.
    val b = AccessibilityServicePlan.release(
        released = listOf(SWIPE),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = listOf(TALKBACK, SWIPE),
    )
    checkEquals("release does not duplicate a manually re-enabled service", listOf(TALKBACK, SWIPE), b.enabledAfter)
    check("release reports no change when nothing was missing", !b.listChanged)

    // 10. The other half of that lesson: a service enabled elsewhere while the target app
    //     was open must survive. A blind save-and-restore would drop it.
    val c = AccessibilityServicePlan.release(
        released = listOf(SWIPE),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = listOf(TALKBACK, BIXBY),
    )
    check("release keeps a service enabled elsewhere", BIXBY in c.enabledAfter)
    check("release still brings back its own service", SWIPE in c.enabledAfter)
    checkEquals("release keeps everything", 3, c.enabledAfter.size)

    // 11. Another app is still holding it, so it must stay off.
    val d = AccessibilityServicePlan.release(
        released = listOf(SWIPE, TASKER),
        stillHeldByOthers = listOf(SWIPE),
        currentlyEnabled = listOf(TALKBACK),
    )
    checkEquals("release skips a service another app still holds", listOf(TASKER), d.restored)
    check("release does not re-enable a still-held service", SWIPE !in d.enabledAfter)

    // 12. Nothing was held, so nothing to do.
    val e = AccessibilityServicePlan.release(
        released = emptyList(),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = listOf(TALKBACK),
    )
    check("release with nothing held reports no change", !e.listChanged)
    checkEquals("release with nothing held is identity", listOf(TALKBACK), e.enabledAfter)

    // 13. Duplicated records must not double-add.
    val f = AccessibilityServicePlan.release(
        released = listOf(SWIPE, SWIPE),
        stillHeldByOthers = emptyList(),
        currentlyEnabled = emptyList(),
    )
    checkEquals("release collapses duplicate records", listOf(SWIPE), f.enabledAfter)
}

/**
 * releaseAll is what the manager's toggle and Revert to default use, and its whole reason to
 * exist is the bug where a service held device-wide *and* by a later launch could not be put
 * back. release() of one holder finds it "held by others" and restores nothing; releaseAll()
 * clears every holder at once.
 */
private fun accessibilityReleaseAllTests() {
    val deviceWide = AccessibilityServicePlan.DEVICE_WIDE_HOLD

    // 13a. The exact shape the bug produced: the manager switched SWIPE off (device-wide),
    // then a launch of app A claimed the same service. Two holders, one service, and it is
    // currently off. A scoped release of just the device-wide holder would see A still
    // holding it and leave it off; releaseAll brings it back.
    val shadowed = mapOf(deviceWide to listOf(SWIPE), "a/b" to listOf(SWIPE))

    val scoped = AccessibilityServicePlan.release(
        released = shadowed[deviceWide].orEmpty(),
        stillHeldByOthers = AccessibilityServicePlan.heldByOthers(shadowed, deviceWide),
        currentlyEnabled = listOf(TALKBACK),
    )
    check("a scoped release cannot restore a shadowed service - the bug", SWIPE !in scoped.enabledAfter)

    val all = AccessibilityServicePlan.releaseAll(
        held = shadowed,
        currentlyEnabled = listOf(TALKBACK),
    )
    check("releaseAll restores a service held by more than one holder", SWIPE in all.enabledAfter)

    // 13b. Cumulative: services held from the manager and across two launches all come back
    // together, deduplicated, and nothing the user turned on by hand is dropped.
    val many = mapOf(
        deviceWide to listOf(SWIPE),
        "a/b" to listOf(TASKER),
        "c/d" to listOf(SWIPE, TALKBACK),
    )
    val cumulative = AccessibilityServicePlan.releaseAll(
        held = many,
        currentlyEnabled = listOf(BIXBY),
    )
    check("releaseAll keeps a hand-enabled service", BIXBY in cumulative.enabledAfter)
    check("releaseAll brings back every held service (SWIPE)", SWIPE in cumulative.enabledAfter)
    check("releaseAll brings back every held service (TASKER)", TASKER in cumulative.enabledAfter)
    check("releaseAll brings back every held service (TALKBACK)", TALKBACK in cumulative.enabledAfter)
    checkEquals("releaseAll does not duplicate", cumulative.enabledAfter.size, cumulative.enabledAfter.distinct().size)

    // 13c. Empty record is a no-op, so the manager toggle on a device with nothing held does
    // not rewrite the setting.
    val none = AccessibilityServicePlan.releaseAll(held = emptyMap(), currentlyEnabled = listOf(TALKBACK))
    check("releaseAll of nothing is not a change", !none.listChanged)
}

private fun accessibilityRecordTests() {
    // 14. heldByOthers excludes the app being asked about.
    val held = mapOf(
        "com.a/com.a.Main" to listOf(SWIPE),
        "com.b/com.b.Main" to listOf(SWIPE, TASKER),
    )
    checkEquals(
        "heldByOthers excludes the named app and dedupes",
        listOf(SWIPE, TASKER),
        AccessibilityServicePlan.heldByOthers(held, "com.a/com.a.Main"),
    )
    checkEquals(
        "heldByOthers of an unknown app is everything",
        setOf(SWIPE, TASKER),
        AccessibilityServicePlan.heldByOthers(held, "com.z/com.z.Main").toSet(),
    )

    // 15. withHold adds, replaces and removes.
    checkEquals(
        "withHold records a claim",
        mapOf("com.a/com.a.Main" to listOf(SWIPE)),
        AccessibilityServicePlan.withHold(emptyMap(), "com.a/com.a.Main", listOf(SWIPE)),
    )
    checkEquals(
        "withHold drops the entry when the claim is empty",
        mapOf("com.b/com.b.Main" to listOf(TASKER)),
        AccessibilityServicePlan.withHold(
            mapOf("com.a/com.a.Main" to listOf(SWIPE), "com.b/com.b.Main" to listOf(TASKER)),
            "com.a/com.a.Main",
            emptyList(),
        ),
    )

    // 16. encode/decode round trip, including the empty case that must not become [""].
    checkEquals("encode/decode round trips", listOf(SWIPE, TASKER), AccessibilityServicePlan.decode(AccessibilityServicePlan.encode(listOf(SWIPE, TASKER))))
    checkEquals("decoding an empty record yields an empty list", emptyList<String>(), AccessibilityServicePlan.decode(""))
    checkEquals("encoding an empty list yields an empty string", "", AccessibilityServicePlan.encode(emptyList()))
}

private fun accessibilityRoundTripTests() {
    val original = listOf(TALKBACK, SWIPE, TASKER)
    val managed = listOf(SWIPE, TASKER)
    val appA = "com.a/com.a.Main"
    val appB = "com.b/com.b.Main"

    // 17. Hold then release with nothing else happening returns the same set.
    val h = AccessibilityServicePlan.hold(managed, original, emptyList())
    val r = AccessibilityServicePlan.release(h.held, emptyList(), h.enabledAfter)
    checkEquals("round trip preserves the set", original.toSet(), r.enabledAfter.toSet())

    // 18. Same, but the user enables an unrelated service midway.
    val h2 = AccessibilityServicePlan.hold(managed, original, emptyList())
    val meanwhile = h2.enabledAfter + BIXBY
    val r2 = AccessibilityServicePlan.release(h2.held, emptyList(), meanwhile)
    checkEquals(
        "round trip with an interleaved change keeps everything",
        (original + BIXBY).toSet(),
        r2.enabledAfter.toSet(),
    )

    // 19. THE interleaved two-app scenario that a single global record got wrong:
    //     A applies, B applies, A reverts, B reverts. SWIPE and TASKER must stay off for
    //     as long as B is open, and both must come back only at the very end.
    var record = emptyMap<String, List<String>>()
    var enabled = original

    // A applies.
    val ha = AccessibilityServicePlan.hold(
        managed = managed,
        currentlyEnabled = enabled,
        heldByOthers = AccessibilityServicePlan.heldByOthers(record, appA),
    )
    record = AccessibilityServicePlan.withHold(record, appA, ha.held)
    enabled = ha.enabledAfter
    checkEquals("A applied: only TalkBack left on", listOf(TALKBACK), enabled)

    // B applies, and must claim the same services even though they are already off.
    val hb = AccessibilityServicePlan.hold(
        managed = managed,
        currentlyEnabled = enabled,
        heldByOthers = AccessibilityServicePlan.heldByOthers(record, appB),
    )
    record = AccessibilityServicePlan.withHold(record, appB, hb.held)
    enabled = hb.enabledAfter
    checkEquals("B applied: B claims the already-held services", managed.toSet(), record[appB]?.toSet())
    checkEquals("B applied: list unchanged", listOf(TALKBACK), enabled)

    // A reverts while B is still open — nothing may come back on.
    val ra = AccessibilityServicePlan.release(
        released = record[appA].orEmpty(),
        stillHeldByOthers = AccessibilityServicePlan.heldByOthers(record, appA),
        currentlyEnabled = enabled,
    )
    record = AccessibilityServicePlan.withHold(record, appA, emptyList())
    enabled = ra.enabledAfter
    checkEquals("A reverted while B open: nothing re-enabled", listOf(TALKBACK), enabled)
    check("A reverted: A's record is gone", appA !in record)

    // B reverts — now everything comes back.
    val rb = AccessibilityServicePlan.release(
        released = record[appB].orEmpty(),
        stillHeldByOthers = AccessibilityServicePlan.heldByOthers(record, appB),
        currentlyEnabled = enabled,
    )
    record = AccessibilityServicePlan.withHold(record, appB, emptyList())
    enabled = rb.enabledAfter
    checkEquals("B reverted last: everything is back", original.toSet(), enabled.toSet())
    check("B reverted: the record is empty", record.isEmpty())

    // 20. The reverse order also settles correctly: B reverts first, then A.
    var record2 = emptyMap<String, List<String>>()
    var enabled2 = original
    val ha2 = AccessibilityServicePlan.hold(managed, enabled2, AccessibilityServicePlan.heldByOthers(record2, appA))
    record2 = AccessibilityServicePlan.withHold(record2, appA, ha2.held)
    enabled2 = ha2.enabledAfter
    val hb2 = AccessibilityServicePlan.hold(managed, enabled2, AccessibilityServicePlan.heldByOthers(record2, appB))
    record2 = AccessibilityServicePlan.withHold(record2, appB, hb2.held)
    enabled2 = hb2.enabledAfter

    val rb2 = AccessibilityServicePlan.release(
        record2[appB].orEmpty(),
        AccessibilityServicePlan.heldByOthers(record2, appB),
        enabled2,
    )
    record2 = AccessibilityServicePlan.withHold(record2, appB, emptyList())
    enabled2 = rb2.enabledAfter
    checkEquals("B reverted first: nothing re-enabled", listOf(TALKBACK), enabled2)

    val ra2 = AccessibilityServicePlan.release(
        record2[appA].orEmpty(),
        AccessibilityServicePlan.heldByOthers(record2, appA),
        enabled2,
    )
    record2 = AccessibilityServicePlan.withHold(record2, appA, emptyList())
    enabled2 = ra2.enabledAfter
    checkEquals("A reverted last: everything is back", original.toSet(), enabled2.toSet())
    check("reverse order also empties the record", record2.isEmpty())

    // 21. A device-wide hold claims every enabled service and anything already held by a
    // per-app profile. Releasing the profile first must restore nothing; releasing the
    // device-wide hold last restores the exact original set.
    val deviceWide = AccessibilityServicePlan.DEVICE_WIDE_HOLD
    var record3 = mapOf(appA to listOf(SWIPE))
    var enabled3 = listOf(TALKBACK, TASKER)
    val globalHold = AccessibilityServicePlan.hold(
        managed = enabled3 + AccessibilityServicePlan.heldByOthers(record3, deviceWide),
        currentlyEnabled = enabled3,
        heldByOthers = AccessibilityServicePlan.heldByOthers(record3, deviceWide),
    )
    record3 = AccessibilityServicePlan.withHold(record3, deviceWide, globalHold.held)
    enabled3 = globalHold.enabledAfter
    checkEquals("device-wide hold disables every enabled service", emptyList<String>(), enabled3)
    checkEquals(
        "device-wide hold also claims services already held per app",
        setOf(TALKBACK, TASKER, SWIPE),
        record3[deviceWide]?.toSet(),
    )

    val profileRelease = AccessibilityServicePlan.release(
        released = record3[appA].orEmpty(),
        stillHeldByOthers = AccessibilityServicePlan.heldByOthers(record3, appA),
        currentlyEnabled = enabled3,
    )
    record3 = AccessibilityServicePlan.withHold(record3, appA, emptyList())
    enabled3 = profileRelease.enabledAfter
    checkEquals("profile revert cannot pierce device-wide hold", emptyList<String>(), enabled3)

    val globalRelease = AccessibilityServicePlan.release(
        released = record3[deviceWide].orEmpty(),
        stillHeldByOthers = AccessibilityServicePlan.heldByOthers(record3, deviceWide),
        currentlyEnabled = enabled3,
    )
    enabled3 = globalRelease.enabledAfter
    checkEquals(
        "device-wide revert restores the exact original services",
        setOf(TALKBACK, TASKER, SWIPE),
        enabled3.toSet(),
    )

    // A later launch can find a newly enabled service, but must retain the debt from the
    // first launch even though those earlier services are no longer in the live list.
    val previousDebt = listOf(TALKBACK, TASKER)
    val laterHold = AccessibilityServicePlan.hold(
        managed = previousDebt + listOf(BIXBY),
        currentlyEnabled = listOf(BIXBY),
        heldByOthers = emptyList(),
    )
    checkEquals(
        "repeated device-wide holds merge old and new restoration debt",
        setOf(TALKBACK, TASKER, BIXBY),
        (previousDebt + laterHold.held).toSet(),
    )
}

private fun favouriteOrderingTests() {
    val installed = listOf(
        app("com.bank/com.bank.Main", "iMobile"),
        app("com.chat/com.chat.Main", "apple chat"),
        app("com.zoo/com.zoo.Main", "Zebra"),
    )

    // 16. Custom order is the saved order, not the installed order.
    checkEquals(
        "custom sort follows the saved order",
        listOf("Zebra", "iMobile"),
        FavouriteAppsOrdering.order(
            favouriteComponentNames = listOf("com.zoo/com.zoo.Main", "com.bank/com.bank.Main"),
            installed = installed,
            sortFavouriteApps = SortFavouriteApps.Custom,
        ).map { it.activityLabel },
    )

    // 17. Alphabetical must be case-insensitive, or "apple chat" sorts after "Zebra".
    checkEquals(
        "alphabetical sort ignores case",
        listOf("apple chat", "iMobile", "Zebra"),
        FavouriteAppsOrdering.order(
            favouriteComponentNames = installed.map { it.componentName },
            installed = installed,
            sortFavouriteApps = SortFavouriteApps.Alphabetical,
        ).map { it.activityLabel },
    )

    // 18. A favourite whose app was uninstalled must vanish rather than crash or blank.
    checkEquals(
        "uninstalled favourites are dropped",
        listOf("iMobile"),
        FavouriteAppsOrdering.order(
            favouriteComponentNames = listOf("com.gone/com.gone.Main", "com.bank/com.bank.Main"),
            installed = installed,
            sortFavouriteApps = SortFavouriteApps.Custom,
        ).map { it.activityLabel },
    )

    // 19. A duplicate in the saved list must not render twice; LazyColumn keys are the
    //     component name and duplicate keys crash Compose at runtime.
    checkEquals(
        "duplicate favourites collapse",
        1,
        FavouriteAppsOrdering.order(
            favouriteComponentNames = listOf("com.bank/com.bank.Main", "com.bank/com.bank.Main"),
            installed = installed,
            sortFavouriteApps = SortFavouriteApps.Custom,
        ).size,
    )

    // 20. Empty cases.
    checkEquals(
        "no favourites yields nothing",
        0,
        FavouriteAppsOrdering.order(emptyList(), installed, SortFavouriteApps.Custom).size,
    )
    checkEquals(
        "no installed apps yields nothing",
        0,
        FavouriteAppsOrdering.order(listOf("com.bank/com.bank.Main"), emptyList(), SortFavouriteApps.Alphabetical).size,
    )

    // 21. Search.
    checkEquals("null search returns everything", 3, FavouriteAppsOrdering.filter(installed, null).size)
    checkEquals("empty search returns everything", 3, FavouriteAppsOrdering.filter(installed, "").size)
    checkEquals(
        "search is case-insensitive",
        listOf("iMobile"),
        FavouriteAppsOrdering.filter(installed, "IMOB").map { it.activityLabel },
    )
    checkEquals("search matching nothing is empty", 0, FavouriteAppsOrdering.filter(installed, "zzz").size)
}

private fun favouriteToggleTests() {
    // 22. Adding appends, so the newest favourite lands at the end of the custom order.
    checkEquals(
        "toggle on appends",
        listOf("a", "b"),
        FavouriteAppsOrdering.toggle(listOf("a"), "b", favourite = true),
    )

    // 23. Re-adding must not reorder an existing favourite.
    checkEquals(
        "toggle on is idempotent and does not reorder",
        listOf("a", "b", "c"),
        FavouriteAppsOrdering.toggle(listOf("a", "b", "c"), "b", favourite = true),
    )

    // 24. Removing.
    checkEquals(
        "toggle off removes",
        listOf("a", "c"),
        FavouriteAppsOrdering.toggle(listOf("a", "b", "c"), "b", favourite = false),
    )

    // 25. Removing something that is not there.
    checkEquals(
        "toggle off of a non-favourite is a no-op",
        listOf("a"),
        FavouriteAppsOrdering.toggle(listOf("a"), "z", favourite = false),
    )
}

private fun appSettingKeyTests() {
    // 26. Only USB debugging arms the restart now, and only when this profile is what
    // switched it off. Shizuku's service runs over the USB transport; a profile restoring
    // wireless debugging never took it down, so restarting was firing at a service that had
    // not stopped.
    check(
        "usb debugging switched off then restored arms the restart",
        AppSettingKeys.triggersShizukuRestart(
            listOf(setting(AppSettingKeys.ADB_ENABLED, valueOnLaunch = "0", valueOnRevert = "1")),
        ),
    )
    check(
        "wireless debugging does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(listOf(setting(AppSettingKeys.ADB_WIFI_ENABLED))),
    )
    check(
        "developer options alone does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(listOf(setting(AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED))),
    )

    // 27. A profile that leaves USB debugging on, or turns it on, did not stop Shizuku.
    check(
        "usb debugging left on does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(
            listOf(setting(AppSettingKeys.ADB_ENABLED, valueOnLaunch = "1", valueOnRevert = "1")),
        ),
    )
    check(
        "usb debugging not restored does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(
            listOf(setting(AppSettingKeys.ADB_ENABLED, valueOnLaunch = "0", valueOnRevert = "0")),
        ),
    )

    // 28. An unticked setting is not written, so it must not arm the restart either.
    check(
        "a disabled setting does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(listOf(setting(AppSettingKeys.ADB_ENABLED, enabled = false))),
    )

    // 29. An unrelated key must not arm it, and one matching key among several is enough.
    check(
        "an unrelated key does not arm the restart",
        !AppSettingKeys.triggersShizukuRestart(listOf(setting("screen_brightness"))),
    )
    check("no settings does not arm the restart", !AppSettingKeys.triggersShizukuRestart(emptyList()))
    check(
        "one matching key among several arms the restart",
        AppSettingKeys.triggersShizukuRestart(
            listOf(setting("screen_brightness"), setting(AppSettingKeys.ADB_ENABLED)),
        ),
    )

    // 30. Hiding accessibility only counts when the launch value actually turns it off.
    check(
        "accessibility_enabled=0 on launch hides services",
        AppSettingKeys.hidesAccessibilityServices(
            listOf(setting(AppSettingKeys.ACCESSIBILITY_ENABLED, valueOnLaunch = "0")),
        ),
    )
    check(
        "accessibility_enabled=1 on launch does not hide services",
        !AppSettingKeys.hidesAccessibilityServices(
            listOf(setting(AppSettingKeys.ACCESSIBILITY_ENABLED, valueOnLaunch = "1")),
        ),
    )
    check(
        "a disabled accessibility setting does not hide services",
        !AppSettingKeys.hidesAccessibilityServices(
            listOf(setting(AppSettingKeys.ACCESSIBILITY_ENABLED, enabled = false)),
        ),
    )

    // 31. Reverting restores regardless of the launch value, so a service is never left
    //     stranded off by an odd configuration.
    check(
        "revert restores services whatever the launch value",
        AppSettingKeys.restoresAccessibilityServices(
            listOf(setting(AppSettingKeys.ACCESSIBILITY_ENABLED, valueOnLaunch = "1")),
        ),
    )
    check(
        "an unrelated key does not restore services",
        !AppSettingKeys.restoresAccessibilityServices(listOf(setting("screen_brightness"))),
    )

    // 31b. Stopping the Shizuku service is a marker row, like overlay access: only a launch
    //      value of "0" counts as a stop, and reverting starts it again whatever the value.
    check(
        "shizuku_service=0 on launch stops the service",
        AppSettingKeys.stopsShizukuService(
            listOf(setting(AppSettingKeys.SHIZUKU_SERVICE, valueOnLaunch = "0")),
        ),
    )
    check(
        "shizuku_service=1 on launch does not stop the service",
        !AppSettingKeys.stopsShizukuService(
            listOf(setting(AppSettingKeys.SHIZUKU_SERVICE, valueOnLaunch = "1")),
        ),
    )
    check(
        "a disabled shizuku_service row does not stop the service",
        !AppSettingKeys.stopsShizukuService(
            listOf(setting(AppSettingKeys.SHIZUKU_SERVICE, enabled = false)),
        ),
    )
    check(
        "an unrelated key does not stop the service",
        !AppSettingKeys.stopsShizukuService(listOf(setting("screen_brightness"))),
    )
    // 31c. The reserved id that records "this app stopped Shizuku" must be underivable from
    //      any real row - including the profile's own shizuku_service marker, which is what
    //      idOf() would otherwise turn into exactly this string.
    check(
        "the shizuku-stopped record id cannot be produced by any setting row",
        SettingType.entries.none { type ->
            SettingSnapshot.idOf(type, AppSettingKeys.SHIZUKU_SERVICE) ==
                SettingSnapshot.SHIZUKU_STOPPED_ID
        },
    )
    check(
        "the shizuku-stopped record id survives a snapshot round trip",
        SettingSnapshot.decode(
            SettingSnapshot.encode(mapOf(SettingSnapshot.SHIZUKU_STOPPED_ID to "1")),
        ).containsKey(SettingSnapshot.SHIZUKU_STOPPED_ID),
    )

    // 31d. The same three properties for the note that records "this app withdrew overlay
    //      access", which is what stops a second app's revert handing the permission back
    //      while the app that actually hid it is still open.
    check(
        "the overlay-hidden record id cannot be produced by any setting row",
        SettingType.entries.none { type ->
            SettingSnapshot.idOf(type, AppSettingKeys.SYSTEM_ALERT_WINDOW) ==
                SettingSnapshot.OVERLAY_HIDDEN_ID
        },
    )
    check(
        "the two reserved record ids are distinct",
        SettingSnapshot.OVERLAY_HIDDEN_ID != SettingSnapshot.SHIZUKU_STOPPED_ID,
    )
    check(
        "the overlay-hidden record id survives a snapshot round trip",
        SettingSnapshot.decode(
            SettingSnapshot.encode(
                mapOf(
                    SettingSnapshot.SHIZUKU_STOPPED_ID to "1",
                    SettingSnapshot.OVERLAY_HIDDEN_ID to "1",
                ),
            ),
        ).keys == setOf(SettingSnapshot.SHIZUKU_STOPPED_ID, SettingSnapshot.OVERLAY_HIDDEN_ID),
    )
}

private fun appListOrderingTests() {
    val apps = listOf(
        app("com.zoo/com.zoo.Main", "Zebra", system = false),
        app("com.chat/com.chat.Main", "apple chat", system = false),
        app("com.sys/com.sys.Main", "System Thing", system = true),
    )

    fun order(
        sort: SortLauncherAppsActivityInfo = SortLauncherAppsActivityInfo.Name,
        dir: SortOrderLauncherAppsActivityInfo = SortOrderLauncherAppsActivityInfo.Ascending,
        showSystem: Boolean = true,
    ) = AppListOrder(sort = sort, order = dir, showSystem = showSystem)

    // 32. Name sort is case-insensitive, or "apple chat" lands after "Zebra".
    checkEquals(
        "name sort ignores case",
        listOf("apple chat", "System Thing", "Zebra"),
        AppListOrdering.arrange(apps, order()).map { it.activityLabel },
    )

    // 33. Descending is the exact reverse.
    checkEquals(
        "descending reverses the order",
        listOf("Zebra", "System Thing", "apple chat"),
        AppListOrdering.arrange(apps, order(dir = SortOrderLauncherAppsActivityInfo.Descending))
            .map { it.activityLabel },
    )

    // 34. System apps are dropped unless asked for.
    checkEquals(
        "system apps are hidden by default",
        listOf("apple chat", "Zebra"),
        AppListOrdering.arrange(apps, order(showSystem = false)).map { it.activityLabel },
    )

    // 35. Ordering never invents or loses entries.
    checkEquals("ordering preserves the app count", 3, AppListOrdering.arrange(apps, order()).size)
    checkEquals("ordering an empty list is empty", 0, AppListOrdering.arrange(emptyList(), order()).size)

    // 36. The order key is what decides whether a re-sort is needed, so equal inputs must
    //     compare equal — otherwise distinctUntilChanged never filters anything.
    check("equal order keys compare equal", order() == order())
    check(
        "a different sort field is a different key",
        order() != order(sort = SortLauncherAppsActivityInfo.InstallTime),
    )
    check("a different direction is a different key", order() != order(dir = SortOrderLauncherAppsActivityInfo.Descending))
    check("a different showSystem is a different key", order() != order(showSystem = false))

    // 37. Search.
    checkEquals("null search returns everything", 3, AppListOrdering.search(apps, null).size)
    checkEquals("empty search returns everything", 3, AppListOrdering.search(apps, "").size)
    checkEquals(
        "search is case-insensitive",
        listOf("Zebra"),
        AppListOrdering.search(apps, "ZEB").map { it.activityLabel },
    )
    checkEquals("search matching nothing is empty", 0, AppListOrdering.search(apps, "qqq").size)
}

private fun manualRevertTests() {
    checkEquals(
        "default selection is every target",
        6,
        ManualRevertTarget.Default.size,
    )
    checkEquals(
        "the three debugging targets carry a Global key",
        listOf("development_settings_enabled", "adb_enabled", "adb_wifi_enabled"),
        ManualRevertTarget.entries.mapNotNull { it.globalSettingKey },
    )
    checkEquals(
        "special targets are not a single settings row",
        listOf(
            ManualRevertTarget.AccessibilityServices,
            ManualRevertTarget.Shizuku,
            ManualRevertTarget.DisplayOverOtherApps,
        ),
        ManualRevertTarget.entries.filter { it.globalSettingKey == null },
    )

    val some = setOf(ManualRevertTarget.UsbDebugging, ManualRevertTarget.Shizuku)
    checkEquals(
        "encode emits declaration order, not set order",
        listOf("UsbDebugging", "Shizuku"),
        ManualRevertTarget.encode(some),
    )
    checkEquals("encode then decode round-trips", some, ManualRevertTarget.decode(ManualRevertTarget.encode(some)))
    checkEquals(
        "an empty stored selection reads as the default",
        ManualRevertTarget.Default,
        ManualRevertTarget.decode(emptyList()),
    )
    checkEquals(
        "unknown names are dropped rather than crashing",
        setOf(ManualRevertTarget.Shizuku),
        ManualRevertTarget.decode(listOf("Shizuku", "SomethingRemovedLater")),
    )
    checkEquals(
        "a selection of only unknown names falls back to the default",
        ManualRevertTarget.Default,
        ManualRevertTarget.decode(listOf("NotATarget")),
    )

    checkEquals("nothing requested is neither success nor failure", true, ManualRevertResult().isEmpty)
    checkEquals("nothing requested is not a success", false, ManualRevertResult().isSuccess)
    checkEquals(
        "all reverted is a success",
        true,
        ManualRevertResult(reverted = some).isSuccess,
    )
    checkEquals(
        "a partial result is not a success",
        false,
        ManualRevertResult(
            reverted = setOf(ManualRevertTarget.UsbDebugging),
            failed = setOf(ManualRevertTarget.Shizuku),
        ).isSuccess,
    )
    checkEquals(
        "no permission is not a success even with something reverted",
        false,
        ManualRevertResult(reverted = some, noPermission = true).isSuccess,
    )
}

private fun accessibilityEnableTests() {
    checkEquals(
        "enable adds what is missing and keeps the existing order",
        listOf("a/b", "c/d", "e/f"),
        AccessibilityServicePlan.enable(
            wanted = listOf("e/f", "a/b"),
            currentlyEnabled = listOf("a/b", "c/d"),
        ),
    )
    checkEquals(
        "enable never duplicates an already-enabled service",
        listOf("a/b"),
        AccessibilityServicePlan.enable(wanted = listOf("a/b"), currentlyEnabled = listOf("a/b")),
    )
    checkEquals(
        "enable de-duplicates the wanted list itself",
        listOf("a/b"),
        AccessibilityServicePlan.enable(wanted = listOf("a/b", "a/b"), currentlyEnabled = emptyList()),
    )
    checkEquals(
        "enable on an empty device switches on exactly what was asked for",
        listOf("a/b", "c/d"),
        AccessibilityServicePlan.enable(wanted = listOf("a/b", "c/d"), currentlyEnabled = emptyList()),
    )
    checkEquals(
        "enable with nothing wanted leaves the list untouched",
        listOf("a/b"),
        AccessibilityServicePlan.enable(wanted = emptyList(), currentlyEnabled = listOf("a/b")),
    )
}

private fun settingSnapshotTests() {
    val snapshot = mapOf(
        SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "0",
        SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled") to "1",
        SettingSnapshot.idOf(SettingType.SECURE, "never_written") to null,
    )

    checkEquals(
        "a snapshot round-trips through the proto string",
        snapshot,
        SettingSnapshot.decode(SettingSnapshot.encode(snapshot)),
    )
    checkEquals("an empty snapshot encodes to nothing", "", SettingSnapshot.encode(emptyMap()))
    checkEquals("nothing decodes to an empty snapshot", emptyMap(), SettingSnapshot.decode(""))
    checkEquals(
        "the same key in two tables stays distinct",
        2,
        SettingSnapshot.decode(
            SettingSnapshot.encode(
                mapOf(
                    SettingSnapshot.idOf(SettingType.GLOBAL, "same") to "g",
                    SettingSnapshot.idOf(SettingType.SECURE, "same") to "s",
                ),
            ),
        ).size,
    )
    checkEquals(
        "a value that is empty is not the same as one that was never set",
        mapOf(SettingSnapshot.idOf(SettingType.SECURE, "k") to ""),
        SettingSnapshot.decode(
            SettingSnapshot.encode(mapOf(SettingSnapshot.idOf(SettingType.SECURE, "k") to "")),
        ),
    )

    // The bug this exists for: developer options were already off, the profile hides them,
    // and the configured revert value would switch them on.
    // The second-launch bug: the app is opened again from a shortcut without reverting
    // first, so the settings it reads back are the ones it wrote last time.
    val firstLaunch = mapOf(SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1")
    val secondLaunch = mapOf(SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "0")

    checkEquals(
        "a second apply does not overwrite the first reading",
        firstLaunch,
        SettingSnapshot.merge(existing = firstLaunch, measured = secondLaunch),
    )
    checkEquals(
        "the first apply records everything",
        secondLaunch,
        SettingSnapshot.merge(existing = emptyMap(), measured = secondLaunch),
    )
    checkEquals(
        "a setting added to the profile later still gets its own first reading",
        mapOf(
            SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1",
            SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled") to "1",
        ),
        SettingSnapshot.merge(
            existing = firstLaunch,
            measured = secondLaunch + (SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled") to "1"),
        ),
    )
    checkEquals(
        "a recorded null is a record, not a gap to be refilled",
        mapOf(SettingSnapshot.idOf(SettingType.SECURE, "k") to null),
        SettingSnapshot.merge(
            existing = mapOf(SettingSnapshot.idOf(SettingType.SECURE, "k") to null),
            measured = mapOf(SettingSnapshot.idOf(SettingType.SECURE, "k") to "9"),
        ),
    )

    checkEquals(
        "revert uses what the setting really was, not what was configured",
        "0",
        SettingSnapshot.revertValue(
            recorded = snapshot,
            settingType = SettingType.GLOBAL,
            key = "development_settings_enabled",
            configured = "1",
        ),
    )
    checkEquals(
        "revert still uses the configured value when nothing was recorded",
        "1",
        SettingSnapshot.revertValue(
            recorded = emptyMap(),
            settingType = SettingType.GLOBAL,
            key = "development_settings_enabled",
            configured = "1",
        ),
    )
    checkEquals(
        "a setting that was never set falls back rather than writing nothing",
        "7",
        SettingSnapshot.revertValue(
            recorded = snapshot,
            settingType = SettingType.SECURE,
            key = "never_written",
            configured = "7",
        ),
    )
    checkEquals(
        "a recorded value of 1 is honoured too, not just 0",
        "1",
        SettingSnapshot.revertValue(
            recorded = snapshot,
            settingType = SettingType.GLOBAL,
            key = "adb_enabled",
            configured = "0",
        ),
    )
}

// ---------------------------------------------------------------------------------
// Shizuku fork selection
// ---------------------------------------------------------------------------------

private fun forkApp(label: String, packageName: String) = InstalledAppData(
    packageName = packageName,
    label = label,
    icon = null,
)

private val SHIZUKU_APP = forkApp("Shizuku", "moe.shizuku.privileged.api")
private val SHEVERY_APP = forkApp("Shevery", "com.hamondev.shevery")
private val RENAMED_SHIZUKU = forkApp("Shizuku", "com.uzuku")
private val UNRELATED = forkApp("Bitwarden", "com.x8bit.bitwarden")

private fun userData(
    forkMode: ShizukuForkMode,
    packageName: String = "moe.shizuku.privileged.api",
    startAction: String = ShizukuForkDefaults.THEDJCHI_ACTION,
    authKey: String = "",
    manageOverlay: Boolean = false,
    heldOverlay: Map<String, List<String>> = emptyMap(),
    hideStates: Map<ManualRevertTarget, Boolean> = SettingsToHide.Default,
    revertStates: Map<ManualRevertTarget, Boolean> = RevertDefaults.Default,
    // Saved, so effectiveSettingsToHide reads hideStates rather than the pre-v2.1 fallback
    // it applies to an install that never configured one. Tests that want that fallback say
    // so explicitly.
    hideConfigured: Boolean = true,
    settingsToHideDefaultsV21: Boolean = true,
    settingsHiddenDeviceWide: Boolean = false,
    autoHideEnabled: Boolean = false,
    settingStateBefore: Map<String, Map<String, String?>> = emptyMap(),
    heldAccessibility: Map<String, List<String>> = emptyMap(),
    hidingFramework: HidingFramework = HidingFramework.Default,
    unhidingFramework: UnhidingFramework = UnhidingFramework.Default,
    setupNoticeVersion: Int = 0,
    restoreWirelessDebugging: Boolean = false,
    manageShizuku: Boolean = true,
    // ⚠ **Non-empty by default, since r4m.** `canHide` refuses AccessibilityServices with an
    // empty selection, so a blank fixture would force that target off in every hide-map
    // assertion in this file and quietly change what they test. The two that want an empty
    // selection say so.
    managedAccessibility: List<String> = listOf("com.example/.Service"),
) = UserData(
    theme = Theme.FOLLOW_SYSTEM,
    dynamicTheme = false,
    sortLauncherAppsActivityInfo = SortLauncherAppsActivityInfo.Name,
    sortOrderLauncherAppsActivityInfo = SortOrderLauncherAppsActivityInfo.Ascending,
    showSystem = false,
    favouriteComponentNames = emptyList(),
    sortFavouriteApps = SortFavouriteApps.Custom,
    favouriteAppsView = FavouriteAppsView.List,
    restartShizuku = false,
    shizukuForkMode = forkMode,
    shizukuAuthKey = authKey,
    shizukuPackageName = packageName,
    shizukuStartAction = startAction,
    managedAccessibilityServices = managedAccessibility,
    heldAccessibilityServices = heldAccessibility,
    // ⚠ Derived from the same flag since r3: `overlayManageable` replaced the stored
    // manageOverlay switch and asks for a non-empty selection, so a test that wants overlay
    // management on has to have something selected to manage.
    managedOverlayPackages = if (manageOverlay) listOf("com.example.overlay") else emptyList(),
    heldOverlayPackages = heldOverlay,
    heldOverlayIdentities = emptyMap(),
    manageOverlay = manageOverlay,
    taskerAuthKey = "",
    taskerIntegrationEnabled = false,
    overlayRestoreFailed = false,
    autoRevertOnReturn = false,
    manualRevertTargets = emptySet(),
    notificationFunction = NotificationFunction.Default,
    hidingFramework = hidingFramework,
    unhidingFramework = unhidingFramework,
    revertDefaults = revertStates,
    settingsToHide = hideStates,
    restoreWirelessDebugging = restoreWirelessDebugging,
    manageShizuku = manageShizuku,
    manageShizukuMigratedV3 = true,
    revertDefaultsConfigured = true,
    settingsToHideConfigured = hideConfigured,
    settingsToHideDefaultsV21 = settingsToHideDefaultsV21,
    settingsHiddenDeviceWide = settingsHiddenDeviceWide,
    autoHideEnabled = autoHideEnabled,
    autoHidePackages = emptyList(),
    autoHideNoKillOnLaunch = false,
    autoHideEnabledBeforeHide = false,
    autoHideRunning = false,
    autoUnhideEnabled = false,
    autoUnhideOnSwipe = false,
    autoUnhideOnScreenLock = false,
    iconStyle = IconStyle.SmartAdaptive,
    autoUnhideOnIdle = false,
    autoUnhideScreenLockMinutes = 5,
    autoUnhideIdleMinutes = 15,
    autoUnhideOnAppLaunch = true,
    autoUnhideOnTile = true,
    diagnosticsEnabled = false,
    notificationFunctionResetV16 = true,
    frameworksMigratedV3 = true,
    shizukuStartFailed = false,
    settingStateBefore = settingStateBefore,
    tipShown = false,
    obtainiumTipShown = false,
    setupNoticeVersion = setupNoticeVersion,
    revertDefaultsResetV166 = false,
    revertDefaultsNoticePending = false,
    settingsManagerInfoShown = false,
    autoHideEverEnabled = false,
    settingsNoticeRevision = 0,
    // r4n: the one-shot auto-unhide reset has already run for every fixture, so the
    // triggers and conditions a test sets are the ones it gets.
    autoUnhideResetV3 = true,
    // r4o: fixtures are upgrades, so anything gated on "existed before v3" is reachable.
    upgradedToV3 = true,
    // r9: every row shown, which is what the manager drew before this preference existed. A test
    // written against the old six-row card goes on seeing six rows.
    managerRows = ManagerRows.Default,
    progressiveBlur = true,
    oledBackground = false,
    blurRadiusDp = 14,
    blurTintPercent = 50,
    blurFadeDp = 72,
    drawerShortcutManager = true,
    drawerShortcutHideUnhide = false,
    // r9: already migrated, for the same reason autoUnhideResetV3 above is - a fixture is a
    // settled install rather than one mid-upgrade.
    autoHideDetectorManagedV3 = true,
)

private fun shizukuForkDefaultsTests() {
    val forkInstalled = listOf(UNRELATED, SHIZUKU_APP, SHEVERY_APP)

    checkEquals(
        "thedjchi mode picks the app labelled Shizuku",
        "moe.shizuku.privileged.api",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Thedjchi, forkInstalled),
    )

    checkEquals(
        "other mode prefers Shevery over Shizuku",
        "com.hamondev.shevery",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Other, forkInstalled),
    )

    checkEquals(
        "other mode falls back to Shizuku when Shevery is absent",
        "moe.shizuku.privileged.api",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Other, listOf(UNRELATED, SHIZUKU_APP)),
    )

    checkEquals(
        "a renamed package is still found by its label",
        "com.uzuku",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Thedjchi, listOf(RENAMED_SHIZUKU)),
    )

    checkEquals(
        "nothing plausible installed leaves the field blank",
        "",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Thedjchi, listOf(UNRELATED)),
    )

    // Unset answers like thedjchi now, because a fresh install starts on that family rather
    // than on nothing: the package field should arrive already filled where the app is there
    // to find, instead of empty until something is picked.
    checkEquals(
        "unset detects like thedjchi",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Thedjchi, forkInstalled),
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Unset, forkInstalled),
    )

    // The package name is the second guess, after the label. It is what rescues a build
    // installed under a name this app has never heard of.
    val renamed = forkApp("Something Else", ShizukuForkDefaults.SHIZUKU_PACKAGE)
    checkEquals(
        "the stock package is found even when the label does not match",
        ShizukuForkDefaults.SHIZUKU_PACKAGE,
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Thedjchi, listOf(UNRELATED, renamed)),
    )
    val shevery = forkApp("Something Else", ShizukuForkDefaults.SHEVERY_PACKAGE)
    checkEquals(
        "shevery's stock package is found by package name too",
        ShizukuForkDefaults.SHEVERY_PACKAGE,
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Other, listOf(UNRELATED, shevery)),
    )
    checkEquals(
        "still blank when neither the label nor the package is installed",
        "",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Other, listOf(UNRELATED)),
    )

    checkEquals(
        "thedjchi action does not depend on the package label",
        ShizukuForkDefaults.THEDJCHI_ACTION,
        ShizukuForkDefaults.actionFor(ShizukuForkMode.Thedjchi, "Shevery"),
    )

    checkEquals(
        "Shevery gets its own action",
        ShizukuForkDefaults.SHEVERY_ACTION,
        ShizukuForkDefaults.actionFor(ShizukuForkMode.Other, "Shevery"),
    )

    checkEquals(
        "a Shizuku-labelled app in other mode gets the Shizuku action",
        ShizukuForkDefaults.THEDJCHI_ACTION,
        ShizukuForkDefaults.actionFor(ShizukuForkMode.Other, "Shizuku"),
    )

    checkEquals(
        "an unrecognised fork in other mode defaults to Shevery's action",
        ShizukuForkDefaults.SHEVERY_ACTION,
        ShizukuForkDefaults.actionFor(ShizukuForkMode.Other, "Something Else"),
    )

    checkEquals(
        "a missing label in other mode still yields an action",
        ShizukuForkDefaults.SHEVERY_ACTION,
        ShizukuForkDefaults.actionFor(ShizukuForkMode.Other, null),
    )

    checkEquals(
        "label matching ignores case and surrounding space",
        "com.hamondev.shevery",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Other, listOf(forkApp("  shevery ", "com.hamondev.shevery"))),
    )

    check("only thedjchi authenticates", ShizukuForkMode.Thedjchi.requiresAuthKey)
    check("other forks do not authenticate", !ShizukuForkMode.Other.requiresAuthKey)
    check("unset does not authenticate", !ShizukuForkMode.Unset.requiresAuthKey)
}

private fun shizukuConfiguredTests() {
    check(
        "unset is never configured, however full the fields are",
        !userData(ShizukuForkMode.Unset, authKey = "token").isShizukuConfigured,
    )

    check(
        "thedjchi without an auth key is not configured",
        !userData(ShizukuForkMode.Thedjchi).isShizukuConfigured,
    )

    check(
        "thedjchi with an auth key is configured",
        userData(ShizukuForkMode.Thedjchi, authKey = "token").isShizukuConfigured,
    )

    check(
        "other forks need no auth key",
        userData(
            ShizukuForkMode.Other,
            packageName = "com.hamondev.shevery",
            startAction = ShizukuForkDefaults.SHEVERY_ACTION,
        ).isShizukuConfigured,
    )

    check(
        "a blank package is never configured",
        !userData(ShizukuForkMode.Other, packageName = "").isShizukuConfigured,
    )

    check(
        "a blank action is never configured",
        !userData(ShizukuForkMode.Other, startAction = "").isShizukuConfigured,
    )
}

// ---------------------------------------------------------------------------------
// v1.2 — the settings manager's live rows
// ---------------------------------------------------------------------------------

private fun stopActionTests() {
    checkEquals(
        "thedjchi's start action pairs with its stop action",
        "moe.shizuku.privileged.api.STOP",
        ShizukuForkDefaults.stopActionFor("moe.shizuku.privileged.api.START"),
    )

    checkEquals(
        "Shevery's START_SERVER pairs with STOP_SERVER",
        "moe.shizuku.manager.action.STOP_SERVER",
        ShizukuForkDefaults.stopActionFor("moe.shizuku.manager.action.START_SERVER"),
    )

    checkEquals(
        "an unknown fork's action is rewritten the same way",
        "com.example.fork.action.STOP_IT",
        ShizukuForkDefaults.stopActionFor("com.example.fork.action.START_IT"),
    )

    checkEquals(
        "only the last START is rewritten, so a package containing it survives",
        "com.START.thing.STOP",
        ShizukuForkDefaults.stopActionFor("com.START.thing.START"),
    )

    checkEquals(
        "an action with no START yields no stop action rather than a guess",
        "",
        ShizukuForkDefaults.stopActionFor("moe.shizuku.privileged.api.LAUNCH"),
    )

    checkEquals("a blank action stays blank", "", ShizukuForkDefaults.stopActionFor(""))
}

private fun launchPackageTests() {
    val installed = listOf(UNRELATED, SHIZUKU_APP, SHEVERY_APP)

    checkEquals(
        "the configured package wins when it is installed",
        "com.hamondev.shevery",
        ShizukuForkDefaults.launchPackageFor("com.hamondev.shevery", installed),
    )

    checkEquals(
        "a configured package that is not installed falls back to Shizuku",
        "moe.shizuku.privileged.api",
        ShizukuForkDefaults.launchPackageFor("com.gone", installed),
    )

    checkEquals(
        "with no Shizuku installed it falls back to Shevery",
        "com.hamondev.shevery",
        ShizukuForkDefaults.launchPackageFor("", listOf(UNRELATED, SHEVERY_APP)),
    )

    checkEquals(
        "nothing installed means nothing to open",
        "",
        ShizukuForkDefaults.launchPackageFor("", listOf(UNRELATED)),
    )

    checkEquals(
        "a renamed but configured package is still honoured",
        "com.uzuku",
        ShizukuForkDefaults.launchPackageFor("com.uzuku", listOf(RENAMED_SHIZUKU)),
    )
}

private fun accessibilityLiveStateTests() {
    val enabled = listOf(TALKBACK, SWIPE, BIXBY)

    check(
        "the row reads on only when every managed service is on",
        AccessibilityServicePlan.allEnabled(listOf(TALKBACK, SWIPE), enabled),
    )

    check(
        "one managed service missing reads as off",
        !AccessibilityServicePlan.allEnabled(listOf(TALKBACK, TASKER), enabled),
    )

    check(
        "managing nothing reads as on, since there is nothing to put back",
        AccessibilityServicePlan.allEnabled(emptyList(), emptyList()),
    )

    check(
        "duplicates in the managed list do not change the answer",
        AccessibilityServicePlan.allEnabled(listOf(TALKBACK, TALKBACK), enabled),
    )

    checkEquals(
        "switching off removes only the managed services",
        listOf(BIXBY),
        AccessibilityServicePlan.disable(listOf(TALKBACK, SWIPE), enabled),
    )

    checkEquals(
        "a service the user enabled themselves is never swept up",
        listOf(TALKBACK, SWIPE, BIXBY),
        AccessibilityServicePlan.disable(listOf(TASKER), enabled),
    )

    checkEquals(
        "switching off an empty managed set changes nothing",
        enabled,
        AccessibilityServicePlan.disable(emptyList(), enabled),
    )

    checkEquals(
        "order of the survivors is preserved",
        listOf(TALKBACK, BIXBY),
        AccessibilityServicePlan.disable(listOf(SWIPE), enabled),
    )
}

/**
 * The "Revert to default" configuration: what it stores, what it falls back to, and the one
 * rule it enforces between two of its rows.
 */
private fun revertDefaultsTests() {
    // 45. Never configured falls back to nothing restored. Restoring something the user
    // keeps off leaves the device more open than they keep it, on a schedule they did not
    // choose - so, as of v2.1, an install nobody has configured restores nothing at all.
    checkEquals(
        "an empty configuration falls back to the default",
        RevertDefaults.Default,
        RevertDefaults.decode(emptyList()),
    )
    checkEquals(
        "nothing is restored by default",
        0,
        RevertDefaults.Default.count { it.value },
    )
    for (target in ManualRevertTarget.entries) {
        checkEquals(
            "revert leaves ${'$'}target alone by default",
            false,
            RevertDefaults.Default[target],
        )
    }
    check(
        "the default covers every target, so decode can never be missing one",
        RevertDefaults.Default.keys == ManualRevertTarget.entries.toSet(),
    )

    // 45b. The v1.6.6 map is frozen apart from the default, because the migration that
    // preserves it for an existing install must not follow a later change to what a fresh
    // install starts with.
    checkEquals(
        "the v1.6.6 default restores accessibility services",
        true,
        RevertDefaults.NarrowedV166[ManualRevertTarget.AccessibilityServices],
    )
    checkEquals(
        "accessibility services is the only target the v1.6.6 default restores",
        1,
        RevertDefaults.NarrowedV166.count { it.value },
    )
    check(
        "the v1.6.6 default covers every target",
        RevertDefaults.NarrowedV166.keys == ManualRevertTarget.entries.toSet(),
    )

    // 46. Every target is written, on or off, so "off" and "not configured" stay distinct.
    val mixed = mapOf(
        ManualRevertTarget.DeveloperSettings to true,
        ManualRevertTarget.UsbDebugging to true,
        ManualRevertTarget.WirelessDebugging to false,
        ManualRevertTarget.AccessibilityServices to true,
        ManualRevertTarget.Shizuku to false,
        ManualRevertTarget.DisplayOverOtherApps to true,
    )
    checkEquals(
        "encode writes one entry per target",
        ManualRevertTarget.entries.size,
        RevertDefaults.encode(mixed).size,
    )
    checkEquals("a mixed configuration round-trips", mixed, RevertDefaults.decode(RevertDefaults.encode(mixed)))

    // 47. All off is a real answer and must survive the round trip, or someone who wants
    // nothing restored gets everything restored.
    val allOff = ManualRevertTarget.entries.associateWith { false }
    checkEquals("all off round-trips", allOff, RevertDefaults.decode(RevertDefaults.encode(allOff)))

    // 48. A downgrade, or a target added in a later version, must not poison the stored
    // configuration: unknown names are dropped and missing ones fall back to the default.
    checkEquals(
        "an unknown target name is ignored",
        RevertDefaults.Default,
        RevertDefaults.decode(listOf("SomethingElse=0")),
    )
    // Every default is off since v2.1, so a value of false proves nothing on its own -
    // an absent target and a target defaulting to off read the same. What can be asserted
    // is that the target is in the map at all, which is what "falls back" has to mean when
    // the fallback value is the same as the empty one.
    check(
        "a missing target is still present, on its default",
        RevertDefaults.decode(listOf("Shizuku=1"))
            .containsKey(ManualRevertTarget.AccessibilityServices),
    )
    checkEquals(
        "a missing target falls back to its default",
        RevertDefaults.Default[ManualRevertTarget.AccessibilityServices],
        RevertDefaults.decode(listOf("Shizuku=1"))[ManualRevertTarget.AccessibilityServices],
    )
    checkEquals(
        "a stored target still wins over the default",
        true,
        RevertDefaults.decode(listOf("Shizuku=1"))[ManualRevertTarget.Shizuku],
    )
    checkEquals(
        "a malformed entry is ignored",
        RevertDefaults.Default,
        RevertDefaults.decode(listOf("=1", "Shizuku", "")),
    )

    // 49. Every target is independent. An earlier version tied Shizuku to USB debugging;
    // which transport the service needs depends on how Shizuku was started, and Shizuku
    // re-enables the right one itself, so deciding it here overrode a deliberate choice.
    checkEquals(
        "the encoding has no cross-target rule left to enforce",
        listOf("DeveloperSettings=0", "UsbDebugging=1", "WirelessDebugging=0",
               "AccessibilityServices=1", "Shizuku=0", "DisplayOverOtherApps=1"),
        RevertDefaults.encode(
            mapOf(
                ManualRevertTarget.DeveloperSettings to false,
                ManualRevertTarget.UsbDebugging to true,
                ManualRevertTarget.WirelessDebugging to false,
                ManualRevertTarget.AccessibilityServices to true,
                ManualRevertTarget.Shizuku to false,
                ManualRevertTarget.DisplayOverOtherApps to true,
            ),
        ),
    )

    // 50. The combination the old rule forbade — Shizuku on with USB debugging off — has to
    // survive a round trip, because it is now a configuration the user is allowed to save.
    val shizukuWithoutUsb = mapOf(
        ManualRevertTarget.DeveloperSettings to false,
        ManualRevertTarget.UsbDebugging to false,
        ManualRevertTarget.WirelessDebugging to true,
        ManualRevertTarget.AccessibilityServices to false,
        ManualRevertTarget.Shizuku to true,
        ManualRevertTarget.DisplayOverOtherApps to true,
    )
    checkEquals(
        "Shizuku on with USB debugging off round-trips",
        shizukuWithoutUsb,
        RevertDefaults.decode(RevertDefaults.encode(shizukuWithoutUsb)),
    )

    // 53. Revert to default is what an install that has never opened the picker gets. The
    // memory function's notification is its only way back, and a notification can be swiped
    // away; this one has a tile and a shortcut that need no notification at all.
    checkEquals(
        "revert to default is the recommended default",
        NotificationFunction.RevertToDefault,
        NotificationFunction.Default,
    )
    check(
        "both functions are still reachable",
        NotificationFunction.entries.toSet() ==
            setOf(NotificationFunction.Memory, NotificationFunction.RevertToDefault),
    )
}

/**
 * "Settings to hide" — the device-wide configuration applied on the way into any app.
 *
 * Its rules differ from [RevertDefaults] in two ways that are easy to get wrong by copying
 * one from the other, so both are pinned here: Shizuku is excluded, and overlay access is
 * opt-in because it requires a live Shizuku shell.
 */
private fun settingsToHideTests() {
    // 51. Shizuku is a target now: stopped on the way in through its fork's stop intent. It
    // sits between accessibility services and overlay access — the two other targets that are
    // not plain settings rows.
    check(
        "Shizuku is one of the targets",
        ManualRevertTarget.Shizuku in SettingsToHide.Targets,
    )
    checkEquals("there are exactly six targets", 6, SettingsToHide.Targets.size)
    checkEquals(
        "Shizuku sits between accessibility services and overlay access",
        listOf(
            ManualRevertTarget.AccessibilityServices,
            ManualRevertTarget.Shizuku,
            ManualRevertTarget.DisplayOverOtherApps,
        ),
        SettingsToHide.Targets.takeLast(3),
    )

    // 52. Nothing is hidden by default, as of v2.1: an install nobody has configured must
    // not change a device on its own the first time an app is launched from it.
    checkEquals(
        "an empty configuration falls back to the default",
        SettingsToHide.Default,
        SettingsToHide.decode(emptyList()),
    )
    checkEquals(
        "nothing is hidden by default",
        0,
        SettingsToHide.Default.count { it.value },
    )
    checkEquals(
        "the default covers every target, so decode can never be missing one",
        SettingsToHide.Targets.toSet(),
        SettingsToHide.Default.keys,
    )

    // 52b. The pre-v2.1 map, frozen for the migration that writes it down for an install
    // that has been behaving as it all along.
    check(
        "the legacy default hides developer settings",
        SettingsToHide.LegacyDefault[ManualRevertTarget.DeveloperSettings] == true,
    )
    check(
        "the legacy default leaves display-over-other-apps alone",
        SettingsToHide.LegacyDefault[ManualRevertTarget.DisplayOverOtherApps] == false,
    )
    check(
        "the legacy default leaves the Shizuku service alone",
        SettingsToHide.LegacyDefault[ManualRevertTarget.Shizuku] == false,
    )
    checkEquals(
        "the legacy default hides exactly the four secure settings",
        4,
        SettingsToHide.LegacyDefault.count { it.value },
    )
    checkEquals(
        "the legacy default covers every target",
        SettingsToHide.Targets.toSet(),
        SettingsToHide.LegacyDefault.keys,
    )

    // 53. Off is switched in the reverse of the order things are switched on in: developer
    // options must go last, after the things that live underneath it.
    checkEquals(
        "the hide order is the reverse of the target order",
        SettingsToHide.Targets.reversed(),
        SettingsToHide.HideOrder,
    )
    checkEquals(
        "developer settings is hidden last",
        ManualRevertTarget.DeveloperSettings,
        SettingsToHide.HideOrder.last(),
    )

    // 54. Every target is written, on or off, so "not hidden" and "not configured" stay
    // distinct — the same reason the revert configuration stores a state per target.
    val mixed = mapOf(
        ManualRevertTarget.DeveloperSettings to true,
        ManualRevertTarget.UsbDebugging to false,
        ManualRevertTarget.WirelessDebugging to true,
        ManualRevertTarget.AccessibilityServices to false,
        ManualRevertTarget.Shizuku to true,
        ManualRevertTarget.DisplayOverOtherApps to true,
    )
    checkEquals(
        "encode writes one entry per target",
        SettingsToHide.Targets.size,
        SettingsToHide.encode(mixed).size,
    )
    checkEquals(
        "a mixed configuration round-trips",
        mixed,
        SettingsToHide.decode(SettingsToHide.encode(mixed)),
    )

    // 55. Nothing ticked is a real answer — it means "launch apps without hiding anything"
    // — and must survive the round trip rather than reading back as the default.
    val allOff = SettingsToHide.Targets.associateWith { false }
    checkEquals(
        "all off round-trips rather than falling back to the default",
        allOff,
        SettingsToHide.decode(SettingsToHide.encode(allOff)),
    )

    // 56. Shizuku is a real target now, so a stored entry for it is read back like any other.
    checkEquals(
        "a stored Shizuku entry is kept",
        true,
        SettingsToHide.decode(listOf("Shizuku=1"))[ManualRevertTarget.Shizuku],
    )

    // 57. A downgrade, or a target added later, must not poison the configuration.
    checkEquals(
        "an unknown target name is ignored",
        SettingsToHide.Default,
        SettingsToHide.decode(listOf("SomethingElse=0")),
    )
    // Every default is off since v2.1, so what "falls back" can assert is that the target
    // is in the map at all - an absent one and one defaulting to off read identically.
    check(
        "a missing target is still present, on its default",
        SettingsToHide.decode(listOf("UsbDebugging=1"))
            .containsKey(ManualRevertTarget.DeveloperSettings),
    )
    checkEquals(
        "a missing target falls back to its default",
        SettingsToHide.Default[ManualRevertTarget.DeveloperSettings],
        SettingsToHide.decode(listOf("UsbDebugging=1"))[ManualRevertTarget.DeveloperSettings],
    )
    checkEquals(
        "a stored target still wins over the default",
        false,
        SettingsToHide.decode(listOf("UsbDebugging=0"))[ManualRevertTarget.UsbDebugging],
    )
    checkEquals(
        "a malformed entry is ignored",
        SettingsToHide.Default,
        SettingsToHide.decode(listOf("=1", "UsbDebugging", "")),
    )

    // 58. The pre-v2.1 fallback. MigrateRevertDefaultsUseCase writes the old default down
    // for an install that predates the change and never saved a configuration, but it runs
    // on a coroutine at process start and a shortcut can fire a launch in the same instant.
    // effectiveSettingsToHide answers the same way in that window, so the launch path and
    // the migration cannot disagree about what this install has been hiding all along.
    checkEquals(
        "an upgrading install that never configured reads the legacy default",
        SettingsToHide.LegacyDefault,
        userData(
            ShizukuForkMode.Thedjchi,
            hideStates = SettingsToHide.Default,
            hideConfigured = false,
            settingsToHideDefaultsV21 = false,
            setupNoticeVersion = 14,
        ).effectiveSettingsToHide,
    )
    // A first run has nothing to preserve: setup has never been finished, so there is no
    // earlier behaviour to be faithful to, and the new default is the whole point.
    checkEquals(
        "a first run hides nothing",
        0,
        userData(
            ShizukuForkMode.Thedjchi,
            hideStates = SettingsToHide.Default,
            hideConfigured = false,
            settingsToHideDefaultsV21 = false,
            setupNoticeVersion = 0,
        ).effectiveSettingsToHide.count { it.value },
    )
    // Once the migration has run its answer is stored, so the fallback must stop applying -
    // otherwise an install that later cleared every tick would be silently given the old
    // default back on every launch.
    checkEquals(
        "the fallback stops once the migration has run",
        0,
        userData(
            ShizukuForkMode.Thedjchi,
            hideStates = SettingsToHide.Default,
            hideConfigured = false,
            settingsToHideDefaultsV21 = true,
            setupNoticeVersion = 14,
        ).effectiveSettingsToHide.count { it.value },
    )
    // And a saved configuration always wins, whatever the markers say.
    checkEquals(
        "a saved configuration wins over the fallback",
        0,
        userData(
            ShizukuForkMode.Thedjchi,
            hideStates = SettingsToHide.Default,
            hideConfigured = true,
            settingsToHideDefaultsV21 = false,
            setupNoticeVersion = 14,
        ).effectiveSettingsToHide.count { it.value },
    )
}

/**
 * The master switch for overlay management, and the one asymmetry in it: hiding is gated on
 * it, restoring is not. Both halves are checked here because getting the second one wrong is
 * silent - it does not fail a build or a launch, it just leaves an app without a permission
 * IMD took from it and hides every screen that could give it back.
 */
private fun overlayManagementTests() {
    val target = ManualRevertTarget.DisplayOverOtherApps

    val hideOn = SettingsToHide.Default + (target to true)

    val revertOn = RevertDefaults.Default + (target to true)

    // 55. Managed: both configurations read exactly what was stored.
    checkEquals(
        "managed hiding reads the stored tick",
        true,
        userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true, hideStates = hideOn)
            .effectiveSettingsToHide[target],
    )
    checkEquals(
        "managed reverting reads the stored tick",
        true,
        userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true, revertStates = revertOn)
            .effectiveRevertDefaults[target],
    )

    // 56. Unmanaged: hiding is off however it was left, so no launch can withdraw access.
    checkEquals(
        "unmanaged hiding reads off despite a stored tick",
        false,
        userData(ShizukuForkMode.Thedjchi, manageOverlay = false, hideStates = hideOn)
            .effectiveSettingsToHide[target],
    )

    // 57. Unmanaged with nothing owed: the target is absent, so a revert neither hides nor
    // restores it and does not report on it at all.
    checkEquals(
        "unmanaged reverting drops the target when nothing is owed",
        false,
        userData(ShizukuForkMode.Thedjchi, manageOverlay = false, revertStates = revertOn)
            .effectiveRevertDefaults
            .containsKey(target),
    )

    // 58. Unmanaged with a debt outstanding: restoring still happens. This is the case that
    // matters - the user switched the feature off while apps were still held.
    checkEquals(
        "unmanaged reverting still restores an outstanding debt",
        true,
        userData(
            ShizukuForkMode.Thedjchi,
            manageOverlay = false,
            heldOverlay = mapOf(AccessibilityServicePlan.DEVICE_WIDE_HOLD to listOf("a.b")),
            revertStates = RevertDefaults.Default + (target to false),
        ).effectiveRevertDefaults[target],
    )

    // 59. A debt is repaid even when the stored answer says "leave it hidden": restoring can
    // only put back what IMD itself withdrew, so it can never grant anything new.
    checkEquals(
        "an outstanding debt outranks a stored hide once unmanaged",
        true,
        userData(
            ShizukuForkMode.Thedjchi,
            manageOverlay = false,
            heldOverlay = mapOf("com.x/Y" to listOf("a.b")),
            revertStates = RevertDefaults.Default + (target to false),
        ).effectiveRevertDefaults[target],
    )

    // 60. What the dialogs draw and their summaries count. The entry is removed rather than
    // forced false, because size is the denominator of the "x of y" line.
    checkEquals(
        "an unmanaged configuration loses the overlay row entirely",
        SettingsToHide.Targets.size - 1,
        hideOn.withoutOverlayWhenUnmanaged(manageOverlay = false).size,
    )
    checkEquals(
        "a managed configuration keeps every row",
        SettingsToHide.Targets.size,
        hideOn.withoutOverlayWhenUnmanaged(manageOverlay = true).size,
    )

    // 61. The stored map is never mutated by any of this - switching the feature off and on
    // again has to return the configuration as it was left rather than blank.
    val stored = userData(ShizukuForkMode.Thedjchi, manageOverlay = false, hideStates = hideOn)

    checkEquals(
        "switching the feature off leaves the stored tick alone",
        true,
        stored.settingsToHide[target],
    )
}

private fun appSetting(key: String) = AppSetting(
    enabled = true,
    settingType = SettingType.GLOBAL,
    componentName = "com.example/Activity",
    label = key,
    key = key,
    valueOnLaunch = "0",
    valueOnRevert = "1",
)

private fun appSettingTemplate(key: String) = AppSettingTemplate(
    settingType = SettingType.GLOBAL,
    label = key,
    key = key,
    valueOnLaunch = "0",
    valueOnRevert = "1",
)

/**
 * The per-app config screen's view of the overlay marker.
 *
 * ⚠ **r4m turned this from removing to greying.** The two filters that used to drop the marker
 * out of the templates and the added rows are gone; the screen now draws every row and asks
 * [appSettingBlocked] whether each one can work. What is pinned here is that the question
 * answers for exactly the three keys that mean something beyond "write this", and that it
 * answers the same way the hide itself does.
 */
private fun overlayMarkerVisibilityTests() {
    val overlayKey = AppSettingKeys.SYSTEM_ALERT_WINDOW

    val unmanaged = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = false)

    val managed = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true)

    // 62. Off: the overlay marker is blocked, and an ordinary key beside it is not.
    check(
        "the overlay marker is blocked while unmanaged",
        appSettingBlocked(userData = unmanaged, key = overlayKey),
    )
    check(
        "an ordinary key is never blocked",
        !appSettingBlocked(
            userData = unmanaged,
            key = AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED,
        ),
    )

    // 63. On: nothing is blocked, and in particular the marker comes back - the block is on
    // the drawing, never on what is stored.
    check(
        "the overlay marker is clear while managed",
        !appSettingBlocked(userData = managed, key = overlayKey),
    )

    // 64. The accessibility flag follows its own picker, not the overlay switch. This is the
    // gap r4m closed: with nothing selected a per-app profile used to write the raw
    // accessibility_enabled flag, which switches off every service including IMD+'s detector.
    check(
        "the accessibility flag is blocked with an empty selection",
        appSettingBlocked(
            userData = managed.copy(managedAccessibilityServices = emptyList()),
            key = AppSettingKeys.ACCESSIBILITY_ENABLED,
        ),
    )
    check(
        "and clear once something is selected",
        !appSettingBlocked(userData = managed, key = AppSettingKeys.ACCESSIBILITY_ENABLED),
    )

    // 65. Only three keys mean anything beyond "write this".
    checkEquals(
        "the overlay marker names its target",
        ManualRevertTarget.DisplayOverOtherApps,
        manualTargetForKey(key = overlayKey),
    )
    checkEquals(
        "the shizuku marker names its target",
        ManualRevertTarget.Shizuku,
        manualTargetForKey(key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    checkEquals(
        "the accessibility flag names its target",
        ManualRevertTarget.AccessibilityServices,
        manualTargetForKey(key = AppSettingKeys.ACCESSIBILITY_ENABLED),
    )
    check(
        "an ordinary key names none",
        manualTargetForKey(key = "screen_brightness") == null,
    )
}

/**
 * The auth gate on the exported Tasker receiver, and the "which apps has memory got a hold on"
 * sweep the memory trigger reverts. Both are the security-load-bearing halves of the feature,
 * so both are pinned here where they can be reasoned about without a device.
 */
/**
 * The two fork families are driven in completely different ways, and everything here is an
 * invariant that keeps IMD from promising Shevery something it cannot do. Shevery has no start
 * or stop intent: its service follows the debugging transport, and its own ErrorProtect
 * watchdog is what brings it back. So every place that offers to toggle the service has to
 * disappear for it, and the waits differ because the two are waiting on different things.
 */
private fun shizukuForkStrategyTests() {
    // 1. Only thedjchi speaks intents; Shevery is the indirect one.
    check("thedjchi supports intents", ShizukuForkMode.Thedjchi.supportsIntents)
    check("shevery does not support intents", !ShizukuForkMode.Other.supportsIntents)
    check("unset supports nothing", !ShizukuForkMode.Unset.supportsIntents)
    check("Other is the shevery family", ShizukuForkMode.Other.isShevery)
    check("thedjchi is not shevery", !ShizukuForkMode.Thedjchi.isShevery)

    // 2. The waits are waiting on different things: a broadcast being answered versus a
    //    ten-second watchdog cycle coming round, so Shevery's must clear a full revolution.
    checkEquals("thedjchi waits eight seconds", 8_000L, ShizukuForkMode.Thedjchi.serviceWaitMillis)
    checkEquals("shevery waits forty seconds", 40_000L, ShizukuForkMode.Other.serviceWaitMillis)
    check(
        "shevery's wait clears a full ErrorProtect cycle",
        ShizukuForkMode.Other.serviceWaitMillis > 10_000L,
    )
    checkEquals("unset never waits", 0L, ShizukuForkMode.Unset.serviceWaitMillis)

    // 2b. 'Manage Shizuku' — the stored answer AND a configuration complete enough to act
    //     on. The second half is what makes the switch drop when a field is emptied; the
    //     stored answer is what makes it come back when the field is filled again.
    val managedThedjchi = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageShizuku = true)

    check("manage shizuku on with everything filled", managedThedjchi.manageShizukuEffective)

    check(
        "manage shizuku off when the answer is off",
        !managedThedjchi.copy(manageShizuku = false).manageShizukuEffective,
    )

    // Emptied, then filled again, with the stored answer untouched throughout.
    val blanked = managedThedjchi.copy(shizukuPackageName = "")

    check("manage shizuku drops when a field is blank", !blanked.manageShizukuEffective)

    check("the stored answer survives the blank", blanked.manageShizuku)

    check(
        "manage shizuku comes back when the field is filled again",
        blanked.copy(shizukuPackageName = "moe.shizuku.privileged.api").manageShizukuEffective,
    )

    // 2c. Why a Display over other apps control will not move. Reasons rather than
    //     sentences, because two modules ask and neither can see the other's strings.
    val dooaReady = userData(
        ShizukuForkMode.Thedjchi,
        authKey = "k",
        manageOverlay = true,
        manageShizuku = true,
    )

    check("a ready overlay setup blocks on nothing", overlayBlockReasons(dooaReady).isEmpty())

    checkEquals(
        "shevery is unsupported rather than unconfigured",
        listOf(OverlayBlockReason.ForkUnsupported),
        overlayBlockReasons(dooaReady.copy(shizukuForkMode = ShizukuForkMode.Other)),
    )

    checkEquals(
        "manage shizuku off is its own reason",
        listOf(OverlayBlockReason.ManageShizukuOff),
        overlayBlockReasons(dooaReady.copy(manageShizuku = false)),
    )

    checkEquals(
        "an empty picker is its own reason",
        listOf(OverlayBlockReason.NothingSelected),
        overlayBlockReasons(dooaReady.copy(managedOverlayPackages = emptyList())),
    )

    checkEquals(
        "both can be missing at once, master switch first",
        listOf(OverlayBlockReason.ManageShizukuOff, OverlayBlockReason.NothingSelected),
        overlayBlockReasons(
            dooaReady.copy(manageShizuku = false, managedOverlayPackages = emptyList()),
        ),
    )

    // ⚠ Shevery short-circuits: it does not also report the empty picker behind it.
    checkEquals(
        "shevery reports one reason even with nothing selected",
        listOf(OverlayBlockReason.ForkUnsupported),
        overlayBlockReasons(
            dooaReady.copy(
                shizukuForkMode = ShizukuForkMode.Other,
                managedOverlayPackages = emptyList(),
            ),
        ),
    )

    // 2d. The manager's own Display over other apps rule, which is not the hiding one.
    check(
        "thedjchi may manage overlay without the service running",
        overlayManageableInManager(userData = dooaReady, shizukuRunning = false),
    )

    val sheveryReady = dooaReady.copy(shizukuForkMode = ShizukuForkMode.Other)

    check(
        "shevery may not manage overlay with the service down",
        !overlayManageableInManager(userData = sheveryReady, shizukuRunning = false),
    )

    check(
        "shevery may manage overlay once the service is up",
        overlayManageableInManager(userData = sheveryReady, shizukuRunning = true),
    )

    check(
        "a running service does not excuse an empty picker",
        !overlayManageableInManager(
            userData = sheveryReady.copy(managedOverlayPackages = emptyList()),
            shizukuRunning = true,
        ),
    )

    check(
        "a running service does not excuse manage shizuku being off",
        !overlayManageableInManager(
            userData = sheveryReady.copy(manageShizuku = false),
            shizukuRunning = true,
        ),
    )

    // The auth key is only required where the fork reads it, so Shevery stays on without one.
    check(
        "shevery needs no auth key to be manageable",
        userData(ShizukuForkMode.Other, authKey = "", manageShizuku = true)
            .manageShizukuEffective,
    )

    check(
        "thedjchi without an auth key is not manageable",
        !userData(ShizukuForkMode.Thedjchi, authKey = "", manageShizuku = true)
            .manageShizukuEffective,
    )

    // 3. The Shizuku entry is *removed*, not forced false: the hide loop reads
    //    `wanted[t] == true` and the revert reads `wanted[t]?.let`, and only an absent key
    //    makes the revert skip the target entirely rather than trying to stop it.
    val both = SettingsToHide.Default + (ManualRevertTarget.Shizuku to true)
    check(
        "shevery drops the shizuku entry",
        ManualRevertTarget.Shizuku !in both.withoutShizukuWhenNoIntents(ShizukuForkMode.Other),
    )
    check(
        "thedjchi keeps the shizuku entry",
        both.withoutShizukuWhenNoIntents(ShizukuForkMode.Thedjchi)[ManualRevertTarget.Shizuku] == true,
    )

    // 4. And it reaches the two maps the launch and revert paths actually read.
    // ⚠ **Forced false, not dropped — r4n changed this deliberately.** The entry has to stay
    // in the map because the hide dialog counts it and now draws its row on every fork; every
    // reader asks `== true`, so false and absent mean the same thing to the engine. The revert
    // map below still drops it, and that asymmetry is the point: its reader is `?.let`.
    checkEquals(
        "the hide config forces shizuku off on shevery, keeping the entry",
        false,
        userData(ShizukuForkMode.Other, hideStates = both)
            .effectiveSettingsToHide[ManualRevertTarget.Shizuku],
    )
    check(
        "the hide config keeps shizuku on thedjchi",
        // authKey, because since r4m the gate also asks whether Shizuku is configured at all -
        // a blank key is not a configured Thedjchi, and this assertion is about the fork.
        userData(ShizukuForkMode.Thedjchi, authKey = "k", hideStates = both)
            .effectiveSettingsToHide[ManualRevertTarget.Shizuku] == true,
    )
    check(
        "the revert config drops shizuku on shevery",
        ManualRevertTarget.Shizuku !in
            userData(ShizukuForkMode.Other, revertStates = both).effectiveRevertDefaults,
    )

    // 5. The per-app markers on shevery. Since r4m they are greyed on the screen rather than
    //    removed from it, so what is asserted is the block rather than the absence - and the
    //    author's answer to which rows grey: both of them, and the ordinary key never.
    val shevery = userData(ShizukuForkMode.Other, authKey = "k", manageOverlay = true)

    val thedjchi = userData(ShizukuForkMode.Thedjchi, authKey = "k", manageOverlay = true)

    check(
        "shevery blocks the shizuku marker",
        appSettingBlocked(userData = shevery, key = AppSettingKeys.SHIZUKU_SERVICE),
    )
    check(
        "shevery blocks the overlay marker too",
        appSettingBlocked(userData = shevery, key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
    )
    check(
        "and never an ordinary key",
        !appSettingBlocked(userData = shevery, key = "screen_brightness"),
    )
    check(
        "thedjchi blocks neither marker",
        !appSettingBlocked(userData = thedjchi, key = AppSettingKeys.SHIZUKU_SERVICE) &&
            !appSettingBlocked(userData = thedjchi, key = AppSettingKeys.SYSTEM_ALERT_WINDOW),
    )

    // 6. And with 'Manage Shizuku' off, which is the author's own wording for this round -
    //    the marker is blocked on a fork that does speak intents.
    check(
        "manage shizuku off blocks the shizuku marker on thedjchi",
        appSettingBlocked(
            userData = thedjchi.copy(manageShizuku = false),
            key = AppSettingKeys.SHIZUKU_SERVICE,
        ),
    )

    // 7. ⚠ **Nothing leaves the screen any more — r4n.** `appSettingHidden` is gone, and with
    //    it the one exception to "grey, don't remove": the Shizuku marker on a fork with no
    //    intents. The author reversed his earlier *"keep them hidden until Shevery's engine
    //    lands"*. What replaces those assertions is the rule the removal has to satisfy —
    //    **every gated key is blocked on every fork that cannot run it**, so a row that is
    //    drawn is either live or greyed, and never drawn-and-acted-on.
    for (fork in listOf(shevery, thedjchi.copy(manageShizuku = false))) {
        for (key in listOf(AppSettingKeys.SYSTEM_ALERT_WINDOW, AppSettingKeys.SHIZUKU_SERVICE)) {
            check(
                "a marker that cannot run is blocked, not removed: $key",
                appSettingBlocked(userData = fork, key = key),
            )
        }
    }

    // And the engine's own gate is the same expression, which is what stops a greyed row and
    // a running hide drifting apart.
    check(
        "the hide map refuses exactly what the screen greys",
        shevery.effectiveSettingsToHide[ManualRevertTarget.Shizuku] == false &&
            shevery.effectiveSettingsToHide[ManualRevertTarget.DisplayOverOtherApps] == false,
    )
}

/**
 * r4n — the auto-unhide coupling, and the term the v3 reset made necessary.
 *
 * The invariant is the author's: the Hide settings tile condition can only be honoured by the
 * screen-lock trigger, because a session the tile starts names no app for the watcher to see
 * leaving the foreground.
 */
private fun autoUnhideCouplingTests() {
    // Ticking the tile ticks screen lock; ticking screen lock says nothing about the tile.
    check("the tile brings the screen lock trigger with it", screenLockAfterTile(
        onScreenLock = false,
        onTile = true,
    ))
    check("and leaves it alone when it is already on", screenLockAfterTile(
        onScreenLock = true,
        onTile = true,
    ))
    check("unticking the tile does not take the trigger with it", screenLockAfterTile(
        onScreenLock = true,
        onTile = false,
    ))
    check("and does not switch it on either", !screenLockAfterTile(
        onScreenLock = false,
        onTile = false,
    ))

    // Unticking screen lock unticks the tile; ticking it says nothing about the tile.
    check("losing the trigger loses the tile", !tileAfterScreenLock(
        onTile = true,
        onScreenLock = false,
    ))
    check("the tile survives a trigger that is still on", tileAfterScreenLock(
        onTile = true,
        onScreenLock = true,
    ))
    check("and a trigger coming on does not tick the tile", !tileAfterScreenLock(
        onTile = false,
        onScreenLock = true,
    ))

    // ⚠ **The pairing, which is the assertion worth having.** Whichever side moved, the state
    // the two functions leave behind must satisfy the invariant: no tile without screen lock.
    for (tile in listOf(false, true)) {
        for (lock in listOf(false, true)) {
            check(
                "after a screen-lock edit the invariant holds: tile=$tile lock=$lock",
                !tileAfterScreenLock(onTile = tile, onScreenLock = lock) || lock,
            )
            check(
                "after a tile edit the invariant holds: tile=$tile lock=$lock",
                !tile || screenLockAfterTile(onScreenLock = lock, onTile = tile),
            )
        }
    }

    // r4n: satisfied needs one of each. The reset unticks both conditions, so this is the
    // difference between the switch reading off and reading on while nothing can act.
    val ready = AutoUnhideRequirements(
        batteryUnrestricted = true,
        notificationsAllowed = true,
        onAppLaunch = true,
        onScreenLock = true,
    )

    check("a trigger and a condition satisfy it", ready.satisfied)
    check("no condition does not", !ready.copy(onAppLaunch = false).satisfied)
    check("no trigger does not either", !ready.copy(onScreenLock = false).satisfied)
    check(
        "the tile alone is a condition too",
        ready.copy(onAppLaunch = false, onTile = true).satisfied,
    )

    // r4s: screen lock is *the* trigger, not one of three — the author's failsafe. Each of
    // these fails if that is reverted, and the anyTrigger line beside each one is what proves
    // it: under the old rule these cases were satisfied precisely because anyTrigger was true.
    val idleOnly = ready.copy(onScreenLock = false, onIdle = true, usageAccess = true)

    check("the idle trigger alone would once have satisfied it", idleOnly.anyTrigger)

    check("but screen lock is mandatory, so it does not", !idleOnly.satisfied)

    val swipeOnly = ready.copy(
        onScreenLock = false,
        onSwipe = true,
        exitReasonsSupported = true,
        dumpPermission = true,
    )

    check("the swipe trigger alone would once have satisfied it", swipeOnly.anyTrigger)

    check("and it does not either, with DUMP granted", !swipeOnly.satisfied)

    check("screen lock on its own is enough", ready.satisfied)
}

private fun taskerIntegrationTests() {
    // 64. A blank stored key is "never set up", and nothing gets through it - not even a
    // broadcast that helpfully sends a blank key of its own.
    check(
        "no stored key authorises nothing",
        !TaskerIntegration.authorises(enabled = true, storedKey = "", providedKey = "anything"),
    )
    check(
        "a blank provided key cannot match a blank stored key",
        !TaskerIntegration.authorises(enabled = true, storedKey = "", providedKey = ""),
    )

    // 65. Once a key exists and the switch is on, only an exact match passes.
    check(
        "the matching key authorises when enabled",
        TaskerIntegration.authorises(enabled = true, storedKey = "abc123", providedKey = "abc123"),
    )
    check(
        "a wrong key is refused",
        !TaskerIntegration.authorises(enabled = true, storedKey = "abc123", providedKey = "abc124"),
    )
    check(
        "a missing key is refused",
        !TaskerIntegration.authorises(enabled = true, storedKey = "abc123", providedKey = null),
    )

    // 65a. The master switch overrides even a correct key: off means off.
    check(
        "a correct key is refused while the integration is off",
        !TaskerIntegration.authorises(enabled = false, storedKey = "abc123", providedKey = "abc123"),
    )

    // 66. "Revert using memory" sweeps every app memory is holding something for - a snapshot
    // or a per-app accessibility hold - and never the device-wide holder, which belongs to
    // Revert to default.
    val components = memoryHeldComponents(
        settingStateBefore = mapOf(
            "a/b" to mapOf("k" to "0"),
            "c/d" to emptyMap(),
        ),
        heldAccessibilityServices = mapOf(
            AccessibilityServicePlan.DEVICE_WIDE_HOLD to listOf(TALKBACK),
            "e/f" to listOf(SWIPE),
            "a/b" to listOf(TASKER),
        ),
    )
    checkEquals(
        "memory sweep unions snapshots and per-app holds, minus the device-wide one",
        setOf("a/b", "c/d", "e/f"),
        components,
    )
    check("memory sweep excludes the device-wide holder", AccessibilityServicePlan.DEVICE_WIDE_HOLD !in components)

    // 67. Nothing held means nothing to revert - the trigger is a no-op, not an error.
    checkEquals(
        "an empty memory record sweeps nothing",
        emptySet<String>(),
        memoryHeldComponents(settingStateBefore = emptyMap(), heldAccessibilityServices = emptyMap()),
    )
}

private fun hiddenStateTests() {
    // 68. Nothing hidden by either mechanism: the tile is off.
    check("a device with no debt reads as visible", !userData(ShizukuForkMode.Thedjchi).settingsHidden)

    // 69. The device-wide half is the stored one, because a "Settings to hide" run that
    // named only the secure settings leaves nothing else behind to read.
    check(
        "the stored flag alone makes the tile read hidden",
        userData(ShizukuForkMode.Thedjchi, settingsHiddenDeviceWide = true).settingsHidden,
    )

    // 70. The memory half is derived from the records a launch leaves, so it needs no flag
    // of its own and cannot disagree with what is actually outstanding.
    val memoryOnly = userData(
        ShizukuForkMode.Thedjchi,
        settingStateBefore = mapOf("a/b" to mapOf("k" to "0")),
    )
    check("an outstanding memory snapshot reads as hidden", memoryOnly.settingsHidden)
    check("and is attributed to the memory half", memoryOnly.memoryHoldsSettings)
    check("with the device-wide half untouched", !memoryOnly.settingsHiddenDeviceWide)

    // 70a. A per-app accessibility hold counts too: a profile that only managed services has
    // no snapshot but is still holding something down.
    check(
        "a per-app accessibility hold alone reads as hidden",
        userData(ShizukuForkMode.Thedjchi, heldAccessibility = mapOf("e/f" to listOf(SWIPE))).settingsHidden,
    )

    // 71. The device-wide holder is not a memory debt. A "Settings to hide" run records its
    // accessibility hold under that marker, and the memory sweep must not claim it - or
    // pressing the tile off would run the wrong revert and leave the real debt standing.
    val deviceWideHold = userData(
        ShizukuForkMode.Thedjchi,
        heldAccessibility = mapOf(AccessibilityServicePlan.DEVICE_WIDE_HOLD to listOf(TALKBACK)),
        settingsHiddenDeviceWide = true,
    )
    check("the device-wide holder is not a memory debt", !deviceWideHold.memoryHoldsSettings)
    check("but the device is still hidden", deviceWideHold.settingsHidden)

    // 72. Both at once is a real state, not an impossible one: the tile hides device-wide
    // whichever mechanism is chosen, so a memory user who presses it and then launches an
    // app from IMD owes one debt of each kind, and both halves have to say so separately.
    val both = userData(
        ShizukuForkMode.Thedjchi,
        settingsHiddenDeviceWide = true,
        settingStateBefore = mapOf("a/b" to mapOf("k" to "0")),
    )
    check("both debts are visible at once", both.settingsHidden)
    check("the memory half is reported", both.memoryHoldsSettings)
    check("the device-wide half is reported", both.settingsHiddenDeviceWide)
}

private fun repeatLaunchFailSafeTests() {
    val holder = AccessibilityServicePlan.DEVICE_WIDE_HOLD

    // 73. Nothing selected is settled by definition: there is nobody to take anything away
    // from, and starting Shizuku to find that out was pure waste on every single launch.
    check(
        "an empty selection needs no overlay work",
        overlayAlreadyWithdrawn(
            managedOverlayPackages = emptyList(),
            heldOverlayPackages = emptyMap(),
        ),
    )

    // 74. The ordinary first launch: selected, nothing held yet, so the full step runs.
    check(
        "a selection with nothing held still needs the overlay step",
        !overlayAlreadyWithdrawn(
            managedOverlayPackages = listOf("com.a", "com.b"),
            heldOverlayPackages = emptyMap(),
        ),
    )

    // 75. The repeat launch this exists for: everything selected is already held, so there is
    // nothing left to withdraw and the ten-second Shizuku start is skipped.
    check(
        "a fully held selection needs no second withdrawal",
        overlayAlreadyWithdrawn(
            managedOverlayPackages = listOf("com.a", "com.b"),
            heldOverlayPackages = mapOf(holder to listOf("com.a", "com.b")),
        ),
    )

    // 76. Half held is not held. A package added to the selection since the hide has to be
    // dealt with, so the step runs - the safe direction to be wrong in.
    check(
        "a package added since the hide forces the step",
        !overlayAlreadyWithdrawn(
            managedOverlayPackages = listOf("com.a", "com.b"),
            heldOverlayPackages = mapOf(holder to listOf("com.a")),
        ),
    )

    // 77. Only the device-wide holder counts. A per-app profile's own hold is released by
    // that app's revert, so treating it as evidence would skip a withdrawal the device-wide
    // hide still owes.
    check(
        "another holder's record is not evidence",
        !overlayAlreadyWithdrawn(
            managedOverlayPackages = listOf("com.a"),
            heldOverlayPackages = mapOf("some/app" to listOf("com.a")),
        ),
    )

    // 78. A hold left over for a package no longer selected does not make the rest settled.
    check(
        "a stale hold does not cover a different selection",
        !overlayAlreadyWithdrawn(
            managedOverlayPackages = listOf("com.c"),
            heldOverlayPackages = mapOf(holder to listOf("com.a", "com.b")),
        ),
    )
}


/**
 * Auto-hide settings (IMD+): the three rules that decide what a hide touches, when the switch
 * may be on, and which holders are apps.
 *
 * All three are the sort of thing that fails silently. A detector missing from the hide set is
 * an accessibility service left listening through a hide; an internal holder counted as an app
 * is a device that reads "hidden" forever; a Shizuku requirement keyed on the wrong checkbox is
 * a switch that refuses to move for a reason the page does not show.
 */
private fun autoHideTests() {
    val detector = "com.soul_99.suIMD/com.android.geto.service.AutoHideAccessibilityService"

    val chosen = listOf("com.other/.Service")

    // 79. A Shizuku that is asleep must not read as a refused permission - see
    // AutoHideRequirements.shizukuUnreachable. This is the difference between IMD+ staying on
    // and switching itself off on every device whose fork is not currently running.
    val asleep = AutoHideRequirements(
        shizukuPermission = false,
        shizukuUnreachable = true,
        shizukuManageable = true,
        // ⚠ Stated rather than defaulted. r4n made the fork a requirement in its own right and
        // the field defaults to false, so a fixture that omitted it would fail for the wrong
        // reason and hide whatever it was actually testing.
        forkSupported = true,
        accessibilityEnabled = true,
        batteryUnrestricted = true,
        notificationsAllowed = true,
        appsChosen = true,
    )

    check("an unreachable Shizuku still satisfies the requirements", asleep.satisfied)

    check(
        "a reachable Shizuku that refused does not",
        !asleep.copy(shizukuUnreachable = false).satisfied,
    )

    check(
        "an unreachable Shizuku with no configuration does not",
        !asleep.copy(shizukuManageable = false).satisfied,
    )

    // r4n item 1. Unconditional, and asserted at both settings of the kill checkbox — the
    // author's decision, and the one thing about this gate that is easy to get wrong.
    check(
        "Shevery is never satisfied, kill wanted",
        !asleep.copy(forkSupported = false).satisfied,
    )

    check(
        "Shevery is never satisfied, kill not wanted either",
        !asleep.copy(forkSupported = false, noKillOnLaunch = true).satisfied,
    )

    // r4n item 2. 'Manage Shizuku' off is a refusal on a fork that would otherwise work.
    check(
        "Manage Shizuku off is not satisfied on Thedjchi",
        !asleep.copy(shizukuManageable = false).satisfied,
    )

    // 80. The one checkbox decides the whole Shizuku question: force-stopping the launched app
    // is the only thing IMD+ asks Shizuku for on its own account.
    check(
        "Shizuku is needed while the app is closed on launch",
        AutoHideRequirements(noKillOnLaunch = false).shizukuNeeded,
    )

    check(
        "Shizuku is not needed once the app is left alone",
        !AutoHideRequirements(noKillOnLaunch = true).shizukuNeeded,
    )

    val withoutShizuku = AutoHideRequirements(
        accessibilityEnabled = true,
        batteryUnrestricted = true,
        notificationsAllowed = true,
        appsChosen = true,
        forkSupported = true,
        noKillOnLaunch = true,
    )

    check("no-kill satisfies the requirements with no Shizuku at all", withoutShizuku.satisfied)

    check(
        "the same requirements are unsatisfied once the kill comes back",
        !withoutShizuku.copy(noKillOnLaunch = false).satisfied,
    )

    // 80b. Every one of the other four is required, whatever the checkbox says.
    check(
        "a missing detector is never satisfied",
        !withoutShizuku.copy(accessibilityEnabled = false).satisfied,
    )

    check(
        "a restricted battery is never satisfied",
        !withoutShizuku.copy(batteryUnrestricted = false).satisfied,
    )

    check(
        "blocked notifications are never satisfied",
        !withoutShizuku.copy(notificationsAllowed = false).satisfied,
    )

    check("no apps chosen is never satisfied", !withoutShizuku.copy(appsChosen = false).satisfied)

    // r4n: the fifth member of that group, and the reason it is in it. "No Shizuku at all" is
    // still not "any fork at all".
    check(
        "an unsupported fork is never satisfied, even with no kill wanted",
        !withoutShizuku.copy(forkSupported = false).satisfied,
    )

    // 81. The switch reads the live answer. The stored choice is kept either way, which is what
    // lets a requirement coming back bring IMD+ back with it.
    check(
        "the switch is on when the answer and the requirements agree",
        autoHideSwitchOn(
            userData = userData(ShizukuForkMode.Thedjchi, autoHideEnabled = true),
            requirements = withoutShizuku,
        ),
    )

    check(
        "the switch is off while a hide is outstanding",
        !autoHideSwitchOn(
            userData = userData(
                ShizukuForkMode.Thedjchi,
                autoHideEnabled = true,
                settingsHiddenDeviceWide = true,
            ),
            requirements = withoutShizuku,
        ),
    )

    check(
        "the switch is off while a requirement is missing",
        !autoHideSwitchOn(
            userData = userData(ShizukuForkMode.Thedjchi, autoHideEnabled = true),
            requirements = withoutShizuku.copy(appsChosen = false),
        ),
    )

    // 82. The detector's holder is IMD's own bookkeeping, not an app's memory. Counting it
    // would make the tile, the IMD+ switch and the memory sweep all read a device with nothing
    // of the user's hidden as still hidden - and send the sweep looking for an app by that name.
    val detectorOnly = userData(
        ShizukuForkMode.Thedjchi,
        heldAccessibility = mapOf(AccessibilityServicePlan.AUTO_HIDE_HOLD to listOf(detector)),
    )

    check("the detector's own hold is not an app's memory", !detectorOnly.memoryHoldsSettings)

    check("a device holding only the detector reads as visible", !detectorOnly.settingsHidden)

    check(
        "both internal holders are excluded from the memory sweep",
        memoryHeldComponents(
            settingStateBefore = emptyMap(),
            heldAccessibilityServices = mapOf(
                AccessibilityServicePlan.DEVICE_WIDE_HOLD to listOf("a/.A"),
                AccessibilityServicePlan.AUTO_HIDE_HOLD to listOf(detector),
                "com.app/.Main" to listOf("b/.B"),
            ),
        ) == setOf("com.app/.Main"),
    )

    // 83. Revert to default releases every holder at once, so the detector comes back with the
    // rest and needs no path of its own.
    val release = AccessibilityServicePlan.releaseAll(
        held = mapOf(
            AccessibilityServicePlan.DEVICE_WIDE_HOLD to listOf("a/.A"),
            AccessibilityServicePlan.AUTO_HIDE_HOLD to listOf(detector),
        ),
        currentlyEnabled = listOf("kept/.Service"),
    )

    check(
        "releaseAll brings the detector back with everything else",
        release.enabledAfter.toSet() == setOf("kept/.Service", "a/.A", detector),
    )
}

// ---------------------------------------------------------------------------------
// v3 — "only the detector is missing", the gate on switching it back on
// ---------------------------------------------------------------------------------

private fun onlyAccessibilityMissingTests() {
    // Everything in place except the detector, with Shizuku taken out of the question by the
    // checkbox — the ordinary shape of a device whose detector was switched off by something
    // that was not the user.
    val ready = AutoHideRequirements(
        accessibilityEnabled = false,
        batteryUnrestricted = true,
        notificationsAllowed = true,
        appsChosen = true,
        forkSupported = true,
        noKillOnLaunch = true,
    )

    check("only the detector missing is recognised", ready.onlyAccessibilityMissing)

    // r4n: offering to switch the detector on for a fork IMD+ will refuse anyway is offering
    // nothing, so the fork is a term of this too.
    check(
        "an unsupported fork stops it",
        !ready.copy(forkSupported = false).onlyAccessibilityMissing,
    )

    check("and that state is not 'satisfied'", !ready.satisfied)

    check(
        "with the detector back, it is satisfied and no longer 'only missing'",
        ready.copy(accessibilityEnabled = true).let {
            it.satisfied && !it.onlyAccessibilityMissing
        },
    )

    // The distinction the KDoc is about: this must not fire when other things are missing too,
    // or IMD would switch the detector on and leave the feature just as off.
    check(
        "a missing battery exemption stops it",
        !ready.copy(batteryUnrestricted = false).onlyAccessibilityMissing,
    )

    check(
        "missing notifications stop it",
        !ready.copy(notificationsAllowed = false).onlyAccessibilityMissing,
    )

    check(
        "no apps chosen stops it",
        !ready.copy(appsChosen = false).onlyAccessibilityMissing,
    )

    // Shizuku only counts when the checkbox says a kill is wanted.
    val needsShizuku = ready.copy(noKillOnLaunch = false)

    check(
        "with a kill wanted and Shizuku unconfigured, it does not fire",
        !needsShizuku.onlyAccessibilityMissing,
    )

    check(
        "with a kill wanted and Shizuku ready, it does",
        needsShizuku.copy(
            shizukuManageable = true,
            shizukuPermission = true,
        ).onlyAccessibilityMissing,
    )

    // A sleeping Shizuku is not a refusal — the same rule `satisfied` already follows.
    check(
        "a configured but unreachable Shizuku still counts as ready",
        needsShizuku.copy(
            shizukuManageable = true,
            shizukuUnreachable = true,
        ).onlyAccessibilityMissing,
    )
}

// ---------------------------------------------------------------------------------
// v3 — which services the accessibility picker lists
// ---------------------------------------------------------------------------------

private fun accessibilityPickerTests() {
    val detector = "com.soul_99.suIMD/com.android.geto.service.AutoHideAccessibilityService"

    fun service(id: String, enabled: Boolean) = AccessibilityServiceData(
        id = id,
        packageName = id.substringBefore('/'),
        label = id.substringBefore('/'),
        enabled = enabled,
    )

    val all = listOf(
        service("a/.A", enabled = true),
        service("b/.B", enabled = false),
        service("c/.C", enabled = false),
        service(detector, enabled = false),
    )

    val none = accessibilityServicesForPicker(
        services = all,
        heldAccessibilityServices = emptyMap(),
    )

    checkEquals(
        "with nothing held, only the enabled ones are listed",
        listOf("a/.A"),
        none.map { it.id },
    )

    // The whole reason this is not a plain `filter { it.enabled }`. A service IMD has switched
    // off is not enabled, and dropping it would empty the picker during the very hide it
    // exists to configure.
    val held = accessibilityServicesForPicker(
        services = all,
        heldAccessibilityServices = mapOf("__device_wide_settings_to_hide__" to listOf("b/.B")),
    )

    checkEquals(
        "a service IMD is holding down stays listed even though it is off",
        listOf("a/.A", "b/.B"),
        held.map { it.id },
    )

    check(
        "a service that is merely off, and not held, stays out",
        "c/.C" !in held.map { it.id },
    )

    val detectorHeld = accessibilityServicesForPicker(
        services = all,
        heldAccessibilityServices = mapOf("__auto_hide_own_detector__" to listOf(detector)),
    )

    check(
        "the detector held under its own holder is listed too",
        detector in detectorHeld.map { it.id },
    )

    checkEquals(
        "order is preserved, so the caller's sort survives",
        listOf("a/.A", "b/.B", "c/.C"),
        accessibilityServicesForPicker(
            services = all,
            heldAccessibilityServices = mapOf(
                "h" to listOf("c/.C", "b/.B"),
            ),
        ).map { it.id }.filter { it != detector },
    )

    checkEquals(
        "an empty list in, an empty list out",
        emptyList<String>(),
        accessibilityServicesForPicker(
            services = emptyList(),
            heldAccessibilityServices = mapOf("h" to listOf("a/.A")),
        ).map { it.id },
    )

    // r2b3b. The author reported the overlay picker dropping a package he had selected; this
    // list had the same hole. "Held" only covers a service IMD switched off *and still has a
    // record of* — so a service the user switched off themselves, or one whose record was
    // discarded by 'Ignore all previous reverts', was selected, off, unheld and invisible.
    val selected = accessibilityServicesForPicker(
        services = all,
        heldAccessibilityServices = emptyMap(),
        managedAccessibilityServices = listOf("c/.C"),
    )

    checkEquals(
        "a selected service is listed even when it is neither enabled nor held",
        listOf("a/.A", "c/.C"),
        selected.map { it.id },
    )

    check(
        "and the rule it was hiding behind still holds: unselected, unheld and off stays out",
        "b/.B" !in selected.map { it.id },
    )

    checkEquals(
        "a selected service that is also held is listed once, not twice",
        listOf("a/.A", "b/.B"),
        accessibilityServicesForPicker(
            services = all,
            heldAccessibilityServices = mapOf(
                "__device_wide_settings_to_hide__" to listOf("b/.B"),
            ),
            managedAccessibilityServices = listOf("b/.B"),
        ).map { it.id },
    )

    checkEquals(
        "an empty selection changes nothing",
        listOf("a/.A"),
        accessibilityServicesForPicker(
            services = all,
            heldAccessibilityServices = emptyMap(),
            managedAccessibilityServices = emptyList(),
        ).map { it.id },
    )
}

// ---------------------------------------------------------------------------------
// v3 — the IMD+ failure back-off
// ---------------------------------------------------------------------------------

private fun autoHideBackoffTests() {
    val minute = 60L * 1000L

    checkEquals(
        "the first failure waits a minute",
        minute,
        autoHideFailureBackoffMillis(failures = 1),
    )

    checkEquals(
        "the second waits five",
        5L * minute,
        autoHideFailureBackoffMillis(failures = 2),
    )

    checkEquals(
        "the third waits thirty",
        30L * minute,
        autoHideFailureBackoffMillis(failures = 3),
    )

    // The whole point of the cap: a permanently revoked permission costs one attempt every
    // half hour rather than one attempt per relaunch, for ever.
    checkEquals(
        "the fourth is capped at thirty, not reaching past the end of the table",
        30L * minute,
        autoHideFailureBackoffMillis(failures = 4),
    )

    checkEquals(
        "and so is the fortieth",
        30L * minute,
        autoHideFailureBackoffMillis(failures = 40),
    )

    // A count of zero should never arrive - an entry is only written when a failure is
    // recorded - but reaching back past the start of the table would throw rather than
    // misbehave, and inside a detector callback that would take IMD+ down with it.
    checkEquals(
        "a zero count is treated as the first failure rather than throwing",
        minute,
        autoHideFailureBackoffMillis(failures = 0),
    )

    checkEquals(
        "a negative count is clamped the same way",
        minute,
        autoHideFailureBackoffMillis(failures = -7),
    )

    // Written as a plain loop on purpose. `zipWithNext().all { (a, b) -> ... }` was the first
    // shape here and it failed twice over: destructuring a Pair in a lambda hits the
    // component1/component2 ambiguity this project has now met four times, and zipWithNext
    // does not resolve against the host runner's classpath at all.
    val waits = (1..6).map { failures -> autoHideFailureBackoffMillis(failures = failures) }

    var neverShortens = true

    for (index in 1 until waits.size) {
        if (waits[index] < waits[index - 1]) neverShortens = false
    }

    check(
        "the waits only ever increase, so a later failure is never retried sooner",
        neverShortens,
    )
}

/**
 * The first-owner rule, and the cascade it exists for.
 *
 * The walk below is r2b §5.1's table, run rather than argued: two apps into one hidden window,
 * both revert orders, and the assertion is that the setting they share ends up **on** either
 * way. Before the rule, one of the two orders stranded it off.
 */
private fun firstOwnerTests() {
    check("a hide that changes a setting owns putting it back", hideOwnsRevert("1", "0"))

    check("a hide that changes nothing owns nothing", !hideOwnsRevert("0", "0"))

    // Never set is not equal to anything a hide writes, so it is recorded. The revert's own
    // rule then declines to write a null back, which is where that case is actually handled.
    check("an unset setting is recorded", hideOwnsRevert(null, "0"))

    // A profile that drives a setting to something other than off is the same question.
    check("a non-zero target still compares by value", hideOwnsRevert("0", "2"))

    check("and owns nothing when it is already there", !hideOwnsRevert("2", "2"))

    // --- the cascade, both orders -------------------------------------------------------
    //
    // Two apps, one shared key. `live` is what the device reads; `records` is what each app
    // owes. A hide writes "0" and records the old value only if it owns the revert.
    val live = mutableMapOf("dev" to "1", "usb" to "1", "wifi" to "1")

    val records = mutableMapOf<String, MutableMap<String, String>>()

    fun hide(app: String, keys: List<String>) {
        val owed = mutableMapOf<String, String>()

        for (key in keys) {
            val current = live.getValue(key)

            if (hideOwnsRevert(currentValue = current, valueOnLaunch = "0")) {
                owed[key] = current
            }

            live[key] = "0"
        }

        records[app] = owed
    }

    fun revert(app: String) {
        val owed = records.remove(app) ?: return

        for (key in owed.keys) {
            live[key] = owed.getValue(key)
        }
    }

    hide(app = "calculator", keys = listOf("dev", "usb"))
    hide(app = "gallery", keys = listOf("usb", "wifi"))

    check(
        "the second app records nothing for a key the first already holds",
        records.getValue("gallery").keys == setOf("wifi"),
    )

    check(
        "and the first app still owns both of its own",
        records.getValue("calculator").keys == setOf("dev", "usb"),
    )

    revert(app = "calculator")
    revert(app = "gallery")

    check(
        "first-then-second leaves the shared setting on",
        live == mapOf("dev" to "1", "usb" to "1", "wifi" to "1"),
    )

    // The other order, from the same start. This is the one that used to strand it.
    live.putAll(mapOf("dev" to "1", "usb" to "1", "wifi" to "1"))

    records.clear()

    hide(app = "calculator", keys = listOf("dev", "usb"))
    hide(app = "gallery", keys = listOf("usb", "wifi"))

    revert(app = "gallery")
    revert(app = "calculator")

    check(
        "second-then-first leaves the shared setting on too",
        live == mapOf("dev" to "1", "usb" to "1", "wifi" to "1"),
    )

    // And the user's own choice is never overridden: a setting they had off before any hide
    // is owned by nobody, so no revert switches it on.
    live.putAll(mapOf("dev" to "1", "usb" to "0", "wifi" to "1"))

    records.clear()

    hide(app = "calculator", keys = listOf("dev", "usb"))

    check(
        "a setting the user had off is owned by nobody",
        records.getValue("calculator").keys == setOf("dev"),
    )

    revert(app = "calculator")

    check(
        "so a revert leaves it off",
        live == mapOf("dev" to "1", "usb" to "0", "wifi" to "1"),
    )
}

private fun frameworkSplitTests() {
    // The pair-off. Every pre-v3 install stored one of exactly two values, and each maps to
    // the combination that behaves the way that install already behaved.
    check(
        "Revert to default migrates to IMD defaults + Revert to default",
        hidingFrameworkFor(NotificationFunction.RevertToDefault) == HidingFramework.ImdDefaults &&
            unhidingFrameworkFor(NotificationFunction.RevertToDefault) ==
            UnhidingFramework.RevertToDefault,
    )

    check(
        "the memory function migrates to Per app + Memory",
        hidingFrameworkFor(NotificationFunction.Memory) == HidingFramework.PerApp &&
            unhidingFrameworkFor(NotificationFunction.Memory) == UnhidingFramework.Memory,
    )

    // The whole point of the migration: no upgrading install may arrive in one of the two
    // combinations no released version has ever run.
    check(
        "migration never produces a crossed pair",
        NotificationFunction.entries.none { stored ->
            val hiding = hidingFrameworkFor(stored)
            val unhiding = unhidingFrameworkFor(stored)

            (hiding == HidingFramework.ImdDefaults && unhiding == UnhidingFramework.Memory) ||
                (hiding == HidingFramework.PerApp &&
                    unhiding == UnhidingFramework.RevertToDefault)
        },
    )

    // A fresh install is NOT the migration's pairing, and that is deliberate: it gets
    // IMD defaults with the memory function, which is one of the two new combinations.
    check(
        "a new install defaults to IMD defaults + Memory",
        HidingFramework.Default == HidingFramework.ImdDefaults &&
            UnhidingFramework.Default == UnhidingFramework.Memory,
    )

    // Only one of the four can leave something hidden with nothing to put it back.
    check(
        "Per app + Revert to default is the stranding pair",
        strandsSettings(HidingFramework.PerApp, UnhidingFramework.RevertToDefault),
    )

    check(
        "the other three do not strand",
        !strandsSettings(HidingFramework.ImdDefaults, UnhidingFramework.RevertToDefault) &&
            !strandsSettings(HidingFramework.ImdDefaults, UnhidingFramework.Memory) &&
            !strandsSettings(HidingFramework.PerApp, UnhidingFramework.Memory),
    )

    // Only the app's revert has to name it.
    check(
        "Per app + Memory is the pair whose revert names the app",
        revertNamesApp(HidingFramework.PerApp, UnhidingFramework.Memory) &&
            !revertNamesApp(HidingFramework.ImdDefaults, UnhidingFramework.Memory) &&
            !revertNamesApp(HidingFramework.PerApp, UnhidingFramework.RevertToDefault) &&
            !revertNamesApp(HidingFramework.ImdDefaults, UnhidingFramework.RevertToDefault),
    )

    // The three keys a Revert to default drives are exactly the ones it must not be handed
    // back from memory afterwards — that is the double write, and adb_enabled is one of them.
    check(
        "the three driven keys are excluded from the extras",
        settingsOutsideRevertDefaults(
            mapOf(
                AppSettingKeys.DEVELOPMENT_SETTINGS_ENABLED to "1",
                AppSettingKeys.ADB_ENABLED to "1",
                AppSettingKeys.ADB_WIFI_ENABLED to "1",
            ),
        ).isEmpty(),
    )

    check(
        "a setting the defaults cannot reach is kept",
        settingsOutsideRevertDefaults(
            mapOf(
                AppSettingKeys.ADB_ENABLED to "1",
                "some_other_secure_setting" to "0",
            ),
        ) == mapOf<String, String?>("some_other_secure_setting" to "0"),
    )

    // A target configured off is still driven off, so its key stays out of the extras
    // whatever the configuration says — the filter is on the key, not on the toggle.
    check(
        "the filter does not depend on how the defaults are configured",
        settingsOutsideRevertDefaults(mapOf(AppSettingKeys.ADB_WIFI_ENABLED to null))
            .isEmpty(),
    )

    check(
        "nothing recorded means nothing extra",
        settingsOutsideRevertDefaults(emptyMap()).isEmpty(),
    )

    // settingOf is the inverse of idOf, and must refuse the two reserved markers — a caller
    // that took those for settings would try to write a row called shizuku_stopped.
    check(
        "an id round-trips back to its type and key",
        settingOf(SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled")) ==
            (SettingType.GLOBAL to "adb_enabled"),
    )

    check(
        "the reserved markers are not settings",
        settingOf(SettingSnapshot.SHIZUKU_STOPPED_ID) == null &&
            settingOf(SettingSnapshot.OVERLAY_HIDDEN_ID) == null,
    )

    check(
        "a key containing the separator still round-trips",
        settingOf(SettingSnapshot.idOf(SettingType.SECURE, "a\u001Fb")) ==
            (SettingType.SECURE to "a\u001Fb"),
    )

    check(
        "rubbish is refused rather than guessed at",
        settingOf("") == null && settingOf("no_separator") == null,
    )

    // The device-wide memory record: what a hide measured decides where the revert drives.
    val devId = { t: ManualRevertTarget -> deviceWideSnapshotId(t)!! }

    check(
        "a target recorded as on is driven back on",
        deviceWideMemoryWanted(
            mapOf(devId(ManualRevertTarget.UsbDebugging) to "1"),
        ) == mapOf(ManualRevertTarget.UsbDebugging to true),
    )

    check(
        "a target recorded as off or unset is left off",
        deviceWideMemoryWanted(
            mapOf(
                devId(ManualRevertTarget.UsbDebugging) to "0",
                devId(ManualRevertTarget.WirelessDebugging) to null,
            ),
        ) == mapOf(
            ManualRevertTarget.UsbDebugging to false,
            ManualRevertTarget.WirelessDebugging to false,
        ),
    )

    // The whole point of the memory framework: a setting the user never had on before the
    // hide must not be switched on by the revert.
    check(
        "an unrecorded target is not driven at all",
        ManualRevertTarget.DeveloperSettings !in
            deviceWideMemoryWanted(mapOf(devId(ManualRevertTarget.UsbDebugging) to "1")),
    )

    check(
        "the three hold-backed targets are never in the wanted map",
        deviceWideSnapshotId(ManualRevertTarget.AccessibilityServices) == null &&
            deviceWideSnapshotId(ManualRevertTarget.Shizuku) == null &&
            deviceWideSnapshotId(ManualRevertTarget.DisplayOverOtherApps) == null,
    )

    check(
        "an empty record drives nothing",
        deviceWideMemoryWanted(emptyMap()).isEmpty(),
    )

    // The debt rule: moving a settings manager switch by hand joins the outstanding revert
    // only when there is one. With nothing pending the user is managing their own device and
    // no later revert should undo it.
    val deviceWideHold = AccessibilityServicePlan.DEVICE_WIDE_HOLD

    val usbId = devId(ManualRevertTarget.UsbDebugging)

    val wifiId = devId(ManualRevertTarget.WirelessDebugging)

    check(
        "a manual change with no revert pending records nothing",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = false,
        ) == null,
    )

    check(
        "a manual change with a revert pending records the value it had",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1"),
    )

    check(
        "switching something on records that it was off",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = false,
            revertPending = true,
        ) == mapOf(usbId to "0"),
    )

    // First owner. A second press must not overwrite the first reading with the value IMD
    // itself just wrote - the same guard recordDeviceWideValues applies on the hide side.
    check(
        "a key already recorded is not re-recorded",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = false,
            revertPending = true,
        ) == null,
    )

    check(
        "a new key is merged rather than replacing the record",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.WirelessDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1", wifiId to "1"),
    )

    check(
        "another holder's record does not count as already recorded",
        manualChangeRecord(
            settingStateBefore = mapOf("com.example/.Main" to mapOf(usbId to "1")),
            target = ManualRevertTarget.UsbDebugging,
            currentlyEnabled = true,
            revertPending = true,
        ) == mapOf(usbId to "1"),
    )

    // The three hold-backed targets keep their own records - an accessibility or overlay
    // hold is written before the shell command for crash safety, and Shizuku has no stored
    // "before" value at all - so none of them is ever written here.
    check(
        "accessibility services are not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.AccessibilityServices,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    check(
        "Shizuku is not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.Shizuku,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    check(
        "Display over other apps is not recorded by a manual change",
        manualChangeRecord(
            settingStateBefore = emptyMap(),
            target = ManualRevertTarget.DisplayOverOtherApps,
            currentlyEnabled = true,
            revertPending = true,
        ) == null,
    )

    // Belt and braces on the rule itself: a hold-backed target with nothing pending is still
    // null, so neither half of the guard is doing all the work on its own.
    // The master pill's order. Guarded here rather than left to a reviewer, because a
    // seventh ManualRevertTarget added later would otherwise be skipped by the pill in
    // silence - nothing in the audit suite reads a list of enum members against its enum.
    // Clearing the device-wide record after a memory revert. Until v3 nothing cleared it at
    // all, so a second hide reverted to the state measured at the first one - for ever.
    val recordBefore = mapOf(
        deviceWideHold to mapOf(
            devId(ManualRevertTarget.UsbDebugging) to "1",
            devId(ManualRevertTarget.WirelessDebugging) to "1",
        ),
    )

    check(
        "a revert that drove everything leaves no device-wide record",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = emptySet(),
        ).isEmpty(),
    )

    check(
        "a failed target stays recorded so a retry can still put it back",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = setOf(ManualRevertTarget.WirelessDebugging),
        ) == mapOf(
            deviceWideHold to mapOf(devId(ManualRevertTarget.WirelessDebugging) to "1"),
        ),
    )

    check(
        "a target the revert never drove is left recorded",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = setOf(ManualRevertTarget.UsbDebugging),
            failed = emptySet(),
        ) == mapOf(
            deviceWideHold to mapOf(devId(ManualRevertTarget.WirelessDebugging) to "1"),
        ),
    )

    check(
        "another holder's record is untouched",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore +
                mapOf("com.example/.Main" to mapOf(devId(ManualRevertTarget.UsbDebugging) to "1")),
            driven = setOf(
                ManualRevertTarget.UsbDebugging,
                ManualRevertTarget.WirelessDebugging,
            ),
            failed = emptySet(),
        ) == mapOf(
            "com.example/.Main" to mapOf(devId(ManualRevertTarget.UsbDebugging) to "1"),
        ),
    )

    check(
        "a revert that drove nothing changes nothing",
        deviceWideRecordAfterRevert(
            settingStateBefore = recordBefore,
            driven = emptySet(),
            failed = emptySet(),
        ) == recordBefore,
    )

    check(
        "no device-wide record at all is left alone",
        deviceWideRecordAfterRevert(
            settingStateBefore = emptyMap(),
            driven = setOf(ManualRevertTarget.UsbDebugging),
            failed = emptySet(),
        ).isEmpty(),
    )

    check(
        "the pill order covers every target exactly once",
        masterPillOnOrder.toSet() == ManualRevertTarget.entries.toSet() &&
            masterPillOnOrder.size == ManualRevertTarget.entries.size,
    )

    val pillOn = masterPillOrder(enabled = true, usable = ManualRevertTarget.entries.toList())

    val pillOff = masterPillOrder(enabled = false, usable = ManualRevertTarget.entries.toList())

    check(
        "on: developer options before USB debugging",
        pillOn.indexOf(ManualRevertTarget.DeveloperSettings) <
            pillOn.indexOf(ManualRevertTarget.UsbDebugging),
    )

    check(
        "on: Shizuku before the overlay AppOps that need it running",
        pillOn.indexOf(ManualRevertTarget.Shizuku) <
            pillOn.indexOf(ManualRevertTarget.DisplayOverOtherApps),
    )

    check(
        "on: wireless debugging last, after the Shizuku start that moves it",
        pillOn.last() == ManualRevertTarget.WirelessDebugging,
    )

    check("off is exactly the reverse of on", pillOff == pillOn.reversed())

    check(
        "off: developer options last of all",
        pillOff.last() == ManualRevertTarget.DeveloperSettings,
    )

    // The pill never touches a row the dialog called unusable.
    val pillSome = listOf(ManualRevertTarget.WirelessDebugging, ManualRevertTarget.UsbDebugging)

    check(
        "an unusable row is never moved",
        masterPillOrder(enabled = true, usable = pillSome).none { it !in pillSome },
    )

    check(
        "a partial list keeps the canonical order",
        masterPillOrder(enabled = true, usable = pillSome) ==
            listOf(ManualRevertTarget.UsbDebugging, ManualRevertTarget.WirelessDebugging),
    )

    check(
        "nothing usable orders nothing",
        masterPillOrder(enabled = true, usable = emptyList()).isEmpty(),
    )

    check(
        "no revert pending beats everything else",
        manualChangeRecord(
            settingStateBefore = mapOf(deviceWideHold to mapOf(usbId to "1")),
            target = ManualRevertTarget.WirelessDebugging,
            currentlyEnabled = true,
            revertPending = false,
        ) == null,
    )

    // The MemoryHolds fix. Until v3 the internal-holder filter was applied to the
    // accessibility map only; the device-wide memory record now writes the same marker into
    // settingStateBefore, and an unfiltered sweep would revert it as if it were an app.
    check(
        "the device-wide memory record is not swept as an app",
        memoryHeldComponents(
            settingStateBefore = mapOf(
                AccessibilityServicePlan.DEVICE_WIDE_HOLD to mapOf("adb_enabled" to "1"),
            ),
            heldAccessibilityServices = emptyMap(),
        ).isEmpty(),
    )

    check(
        "IMD+'s own holder is not swept as an app either",
        memoryHeldComponents(
            settingStateBefore = mapOf(
                AccessibilityServicePlan.AUTO_HIDE_HOLD to mapOf("adb_enabled" to "1"),
            ),
            heldAccessibilityServices = emptyMap(),
        ).isEmpty(),
    )

    check(
        "a real app alongside the device-wide record still is",
        memoryHeldComponents(
            settingStateBefore = mapOf(
                AccessibilityServicePlan.DEVICE_WIDE_HOLD to mapOf("adb_enabled" to "1"),
                "com.example/.Main" to mapOf("adb_enabled" to "1"),
            ),
            heldAccessibilityServices = emptyMap(),
        ) == setOf("com.example/.Main"),
    )

    // settingsHidden must still read true for a device-wide hide - it just gets there through
    // settingsHiddenDeviceWide rather than through the memory record.
    check(
        "a device-wide hide still reads as hidden",
        userData(forkMode = ShizukuForkMode.Thedjchi, settingsHiddenDeviceWide = true)
            .settingsHidden,
    )

    check(
        "and the device-wide memory record alone does not make memoryHoldsSettings true",
        !userData(
            forkMode = ShizukuForkMode.Thedjchi,
            settingStateBefore = mapOf(
                AccessibilityServicePlan.DEVICE_WIDE_HOLD to mapOf("adb_enabled" to "1"),
            ),
        ).memoryHoldsSettings,
    )
}

fun main() {
    accessibilityHoldTests()
    accessibilityReleaseTests()
    accessibilityReleaseAllTests()
    accessibilityRecordTests()
    accessibilityRoundTripTests()
    favouriteOrderingTests()
    favouriteToggleTests()
    appSettingKeyTests()
    appListOrderingTests()
    manualRevertTests()
    accessibilityEnableTests()
    settingSnapshotTests()
    shizukuForkDefaultsTests()
    shizukuConfiguredTests()
    stopActionTests()
    autoUnhideCouplingTests()
    launchPackageTests()
    accessibilityLiveStateTests()
    revertDefaultsTests()
    settingsToHideTests()
    overlayManagementTests()
    overlayMarkerVisibilityTests()
    shizukuForkStrategyTests()
    taskerIntegrationTests()
    hiddenStateTests()
    repeatLaunchFailSafeTests()
    autoHideTests()
    autoHideBackoffTests()
    accessibilityPickerTests()
    onlyAccessibilityMissingTests()
    frameworkSplitTests()
    memoryRevertCoverageTests()
    firstOwnerTests()
    hideGateTests()

    println("passed: $passed")

    if (failures.isEmpty()) {
        println("ALL HOST ASSERTIONS PASSED")
    } else {
        println("FAILED: ${failures.size}")
        failures.forEach { println("  - $it") }
        kotlin.system.exitProcess(1)
    }
}

// ---------------------------------------------------------------------------------
// r4g - a device-wide memory revert covers the targets it cannot measure
// ---------------------------------------------------------------------------------

private fun memoryRevertCoverageTests() {
    // What RevertToDefaultUseCase computes as its destination, in the two shapes it takes.
    fun destination(
        defaults: Map<ManualRevertTarget, Boolean>,
        override: Map<ManualRevertTarget, Boolean>?,
    ): Map<ManualRevertTarget, Boolean> = if (override != null) {
        defaults.filterKeys { deviceWideSnapshotId(target = it) == null } + override
    } else {
        defaults
    }

    val defaults = ManualRevertTarget.entries.associateWith { true }

    // The author's log: a device-wide hide with all six hidden, then a memory revert.
    val recorded = mapOf(
        SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1",
        SettingSnapshot.idOf(SettingType.GLOBAL, "adb_enabled") to "1",
        SettingSnapshot.idOf(SettingType.GLOBAL, "adb_wifi_enabled") to "1",
    )

    val override = deviceWideMemoryWanted(recorded = recorded)

    check(
        "the memory record can only ever carry the three keyed targets",
        override.keys == setOf(
            ManualRevertTarget.DeveloperSettings,
            ManualRevertTarget.UsbDebugging,
            ManualRevertTarget.WirelessDebugging,
        ),
    )

    val wanted = destination(defaults = defaults, override = override)

    // The bug: these three were absent, so the revert never considered them at all.
    for (target in listOf(
        ManualRevertTarget.AccessibilityServices,
        ManualRevertTarget.Shizuku,
        ManualRevertTarget.DisplayOverOtherApps,
    )) {
        check("a memory revert still drives $target", wanted[target] == true)
    }

    check(
        "and the keyed three still come from the record",
        wanted[ManualRevertTarget.UsbDebugging] == true,
    )

    // A keyed target the hide never touched stays absent: the memory framework's whole point.
    val partial = deviceWideMemoryWanted(
        recorded = mapOf(
            SettingSnapshot.idOf(SettingType.GLOBAL, "development_settings_enabled") to "1",
        ),
    )

    val fromPartial = destination(defaults = defaults, override = partial)

    check(
        "an unrecorded keyed target is not driven from the defaults",
        ManualRevertTarget.UsbDebugging !in fromPartial,
    )

    check(
        "and an unkeyed one still is",
        fromPartial[ManualRevertTarget.AccessibilityServices] == true,
    )

    // A record saying a setting was off before keeps it off, over a default that wants it on.
    val wasOff = deviceWideMemoryWanted(
        recorded = mapOf(
            SettingSnapshot.idOf(SettingType.GLOBAL, "adb_wifi_enabled") to "0",
        ),
    )

    check(
        "the record beats the default where it has an opinion",
        destination(defaults = defaults, override = wasOff)[
            ManualRevertTarget.WirelessDebugging,
        ] == false,
    )

    // An explicit revert passes no override and is untouched by any of this.
    check(
        "an explicit revert still drives the configured defaults",
        destination(defaults = defaults, override = null) == defaults,
    )
}

// ---------------------------------------------------------------------------------
// r4m - a disabled toggle does not run, for IMD+ and for every other launch route
// ---------------------------------------------------------------------------------

/**
 * The gate that made the greyed rows true of the engine as well as of the dialog.
 *
 * Every one of these was a real gap: with 'Manage Shizuku' off a device-wide hide still
 * stopped the Shizuku service, and with the accessibility picker empty it still drove
 * accessibility_enabled. Both paths are what IMD+ runs, which is why the author asked.
 *
 * ⚠ **The last group is the one that must not be "fixed".** Reverts are deliberately not
 * gated: restoring something IMD already switched off has to keep working after the toggle
 * that hid it has greyed, or a user is left with settings down and no screen to raise them
 * from. A build that gates both directions passes the first three groups and fails this one.
 */
private fun hideGateTests() {
    val all = ManualRevertTarget.entries.associateWith { true }

    val ready = userData(
        ShizukuForkMode.Thedjchi,
        authKey = "k",
        manageOverlay = true,
        hideStates = all,
        revertStates = all,
    )

    // 1. Everything configured: the stored ticks come through untouched.
    checkEquals(
        "a fully configured install hides every target it was told to",
        ManualRevertTarget.entries.size,
        ready.effectiveSettingsToHide.count { it.value },
    )

    // 2. Manage Shizuku off. The Shizuku row leaves the manager and greys elsewhere, and the
    //    hide has to agree - this is the gap the author's "for IMD+ also" names.
    val noShizuku = ready.copy(manageShizuku = false)

    check("manage shizuku off refuses the shizuku target", !noShizuku.canHide(ManualRevertTarget.Shizuku))
    checkEquals(
        "and the hide config reads it off however it was stored",
        false,
        noShizuku.effectiveSettingsToHide[ManualRevertTarget.Shizuku],
    )
    // Overlay access goes with it, because it is written through Shizuku and nothing else.
    checkEquals(
        "overlay access goes off with the master switch",
        false,
        noShizuku.effectiveSettingsToHide[ManualRevertTarget.DisplayOverOtherApps],
    )
    // And the three settings IMD writes directly are untouched by any of it.
    check(
        "the three direct settings are never gated",
        noShizuku.canHide(ManualRevertTarget.DeveloperSettings) &&
            noShizuku.canHide(ManualRevertTarget.UsbDebugging) &&
            noShizuku.canHide(ManualRevertTarget.WirelessDebugging),
    )

    // 3. An empty accessibility picker. The row greys in both dialogs; before r4m the hide
    //    went ahead and wrote the flag anyway.
    val noAccessibility = ready.copy(managedAccessibilityServices = emptyList())

    check(
        "an empty selection refuses the accessibility target",
        !noAccessibility.canHide(ManualRevertTarget.AccessibilityServices),
    )
    checkEquals(
        "and the hide config reads it off however it was stored",
        false,
        noAccessibility.effectiveSettingsToHide[ManualRevertTarget.AccessibilityServices],
    )

    // 4. ⚠ Reverts are not gated. Both of these would fail on a build that collapsed the two
    //    directions into one rule.
    checkEquals(
        "a revert still restores shizuku with the master switch off",
        true,
        noShizuku.effectiveRevertDefaults[ManualRevertTarget.Shizuku],
    )
    checkEquals(
        "a revert still restores accessibility services with an empty selection",
        true,
        noAccessibility.effectiveRevertDefaults[ManualRevertTarget.AccessibilityServices],
    )
}
