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

import com.android.geto.domain.model.AccessibilityServicePlan
import com.android.geto.domain.model.AppListOrder
import com.android.geto.domain.model.AppListOrdering
import com.android.geto.domain.model.ManualRevertResult
import com.android.geto.domain.model.ManualRevertTarget
import com.android.geto.domain.model.NotificationFunction
import com.android.geto.domain.model.RevertDefaults
import com.android.geto.domain.model.SettingSnapshot
import com.android.geto.domain.model.SettingsToHide
import com.android.geto.domain.model.AppSetting
import com.android.geto.domain.model.AppSettingKeys
import com.android.geto.domain.model.FavouriteAppsOrdering
import com.android.geto.domain.model.LauncherAppsActivityInfo
import com.android.geto.domain.model.InstalledAppData
import com.android.geto.domain.model.SettingType
import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.ShizukuForkMode
import com.android.geto.domain.model.Theme
import com.android.geto.domain.model.UserData
import com.android.geto.domain.model.FavouriteAppsView
import com.android.geto.domain.model.isShizukuConfigured
import com.android.geto.domain.model.SortFavouriteApps
import com.android.geto.domain.model.SortLauncherAppsActivityInfo
import com.android.geto.domain.model.SortOrderLauncherAppsActivityInfo

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
        5,
        ManualRevertTarget.Default.size,
    )
    checkEquals(
        "the three debugging targets carry a Global key",
        listOf("development_settings_enabled", "adb_enabled", "adb_wifi_enabled"),
        ManualRevertTarget.entries.mapNotNull { it.globalSettingKey },
    )
    checkEquals(
        "accessibility and shizuku are not a single settings row",
        listOf(ManualRevertTarget.AccessibilityServices, ManualRevertTarget.Shizuku),
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
    managedAccessibilityServices = emptyList(),
    heldAccessibilityServices = emptyMap(),
    manualRevertTargets = emptySet(),
    notificationFunction = NotificationFunction.Default,
    revertDefaults = RevertDefaults.Default,
    settingsToHide = SettingsToHide.Default,
    notificationFunctionResetV16 = true,
    shizukuStartFailed = false,
    settingStateBefore = emptyMap(),
    tipShown = false,
    obtainiumTipShown = false,
    setupNoticeVersion = 0,
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

    checkEquals(
        "unset picks nothing",
        "",
        ShizukuForkDefaults.packageFor(ShizukuForkMode.Unset, forkInstalled),
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
    // 45. Never configured falls back to the three a locked-down app actually breaks, and
    // leaves developer settings and wireless debugging alone — turning either on for someone
    // who keeps them off is a change they never asked for.
    checkEquals(
        "an empty configuration falls back to the default",
        RevertDefaults.Default,
        RevertDefaults.decode(emptyList()),
    )
    checkEquals(
        "USB debugging is on by default",
        true,
        RevertDefaults.Default[ManualRevertTarget.UsbDebugging],
    )
    checkEquals(
        "accessibility services is on by default",
        true,
        RevertDefaults.Default[ManualRevertTarget.AccessibilityServices],
    )
    checkEquals(
        "Shizuku is on by default",
        true,
        RevertDefaults.Default[ManualRevertTarget.Shizuku],
    )
    checkEquals(
        "developer settings is off by default",
        false,
        RevertDefaults.Default[ManualRevertTarget.DeveloperSettings],
    )
    checkEquals(
        "wireless debugging is off by default",
        false,
        RevertDefaults.Default[ManualRevertTarget.WirelessDebugging],
    )
    check(
        "the default covers every target, so decode can never be missing one",
        RevertDefaults.Default.keys == ManualRevertTarget.entries.toSet(),
    )

    // 46. Every target is written, on or off, so "off" and "not configured" stay distinct.
    val mixed = mapOf(
        ManualRevertTarget.DeveloperSettings to true,
        ManualRevertTarget.UsbDebugging to true,
        ManualRevertTarget.WirelessDebugging to false,
        ManualRevertTarget.AccessibilityServices to true,
        ManualRevertTarget.Shizuku to false,
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
    checkEquals(
        "a missing target falls back to its default",
        true,
        RevertDefaults.decode(listOf("Shizuku=0"))[ManualRevertTarget.UsbDebugging],
    )
    checkEquals(
        "a stored target still wins over the default",
        false,
        RevertDefaults.decode(listOf("Shizuku=0"))[ManualRevertTarget.Shizuku],
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
               "AccessibilityServices=1", "Shizuku=0"),
        RevertDefaults.encode(
            mapOf(
                ManualRevertTarget.DeveloperSettings to false,
                ManualRevertTarget.UsbDebugging to true,
                ManualRevertTarget.WirelessDebugging to false,
                ManualRevertTarget.AccessibilityServices to true,
                ManualRevertTarget.Shizuku to false,
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
 * one from the other, so both are pinned here: it covers four targets rather than five, and
 * it defaults to all of them on rather than to a conservative subset.
 */
private fun settingsToHideTests() {
    // 51. Shizuku is not a target. It is not a setting an app reads, and hiding it belongs
    // to Shizuku's own "Hide Shizuku from other apps" switch — offering a toggle here would
    // promise something this app cannot do.
    check(
        "Shizuku is not one of the targets",
        ManualRevertTarget.Shizuku !in SettingsToHide.Targets,
    )
    checkEquals("there are exactly four targets", 4, SettingsToHide.Targets.size)

    // 52. All four on by default, unlike the revert configuration. Hiding only some of them
    // is the case that fails without any way to diagnose it: the app still sees developer
    // mode and still refuses to run, having changed the device for nothing.
    checkEquals(
        "an empty configuration falls back to the default",
        SettingsToHide.Default,
        SettingsToHide.decode(emptyList()),
    )
    check(
        "every target is hidden by default",
        SettingsToHide.Default.values.all { it },
    )
    checkEquals(
        "the default covers every target, so decode can never be missing one",
        SettingsToHide.Targets.toSet(),
        SettingsToHide.Default.keys,
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

    // 56. Shizuku cannot get in even through stored data written by another version.
    check(
        "a stored Shizuku entry is dropped",
        ManualRevertTarget.Shizuku !in SettingsToHide.decode(listOf("Shizuku=1")).keys,
    )

    // 57. A downgrade, or a target added later, must not poison the configuration.
    checkEquals(
        "an unknown target name is ignored",
        SettingsToHide.Default,
        SettingsToHide.decode(listOf("SomethingElse=0")),
    )
    checkEquals(
        "a missing target falls back to its default",
        true,
        SettingsToHide.decode(listOf("UsbDebugging=0"))[ManualRevertTarget.DeveloperSettings],
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
}

fun main() {
    accessibilityHoldTests()
    accessibilityReleaseTests()
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
    launchPackageTests()
    accessibilityLiveStateTests()
    revertDefaultsTests()
    settingsToHideTests()

    println("passed: $passed")

    if (failures.isEmpty()) {
        println("ALL HOST ASSERTIONS PASSED")
    } else {
        println("FAILED: ${failures.size}")
        failures.forEach { println("  - $it") }
        kotlin.system.exitProcess(1)
    }
}
