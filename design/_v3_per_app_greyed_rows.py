#!/usr/bin/env python3
"""
v3-r4m-c — open item 2: the per-app templates and rows are GREYED, not removed.

    "i want greyed out toggles and templates and toggles etc not them removed"
    spec item 8: "grey out their templates in per app config page (if already added) and per
    app config page setting templates. on clicking any of the greyed out toggles or templates
    display a popup 'Please configure the settings first' [+ a location tree]"

Three keys can grey: the Display over other apps marker, the Shizuku service marker and the
accessibility flag. Each greys for its own reason and each points somewhere different, which is
why the pop-up takes its sentences as parameters.

⚠ **One case still leaves the screen rather than greying, and it is the author's answer.** The
Shizuku marker on a fork with no start-stop intent stays removed - *"keep them hidden until
Shevery's engine lands"*. Bringing that control back needs the stop-intent redesign, and a
greyed row would be explaining a control whose engine does not exist yet. `appSettingHidden`
is that one case, held apart from `appSettingBlocked` so the difference is stated rather than
buried in a condition.

⚠ **Greyed rows draw UNTICKED** - the author's rule for every greyed control in the app - **and
the stored tick is never touched.** `onCheckedChange` is not reachable while blocked, so the
Room row keeps its value and comes straight back when the thing it needs is configured again,
in this app and every other it was added to. His words: *"shown unchecked and unclickable with
the checkbox position remembered"*.

⚠ **The control is WRAPPED, not merely disabled.** A disabled `Checkbox` or `IconButton`
swallows the press inside its own bounds, so the row's own `clickable` never sees it and a tap
does nothing at all - which reads as a broken app. Same treatment `SettingToHideRow` and
`TargetRow` already give their controls, and for the same reason.

⚠ **Five strings are duplicated into `feature/app-settings`.** That module cannot see
`feature/settings`' or `feature/apps`' resources; `check5_dupes` treats identical strings across
modules as intentional, and `string/understood` is already shared exactly this way between two
other modules.

Every edit asserts its anchor matches exactly once. Nothing is written if any file fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OVERLAY = "domain/model/src/main/kotlin/com/android/geto/domain/model/OverlayManagement.kt"

FEATURE = "feature/app-settings/src/main/kotlin/com/android/geto/feature/appsettings"

VM = f"{FEATURE}/AppSettingsViewModel.kt"
SCREEN = f"{FEATURE}/AppSettingsScreen.kt"
TEMPLATES = f"{FEATURE}/dialog/TemplateDialog.kt"

STRINGS = "feature/app-settings/src/main/res/values/strings.xml"

# =========================================================================================
# 1 — :domain:model, the one case that still leaves the screen
# =========================================================================================

DOMAIN_ANCHOR = """fun appSettingBlocked(userData: UserData, key: String): Boolean ="""

DOMAIN_NEW = '''/**
 * Whether a per-app template or row should leave the screen altogether rather than grey.
 *
 * ⚠ **Exactly one case, and it is the author's own answer** - the Shizuku marker on a fork with
 * no start-stop intent. Everything else that cannot work is drawn and greyed, because greying
 * says *what to go and configure*; here there is nothing to configure. Shevery's service
 * follows the debugging transport rather than anything IMD sends, so the control has no engine
 * behind it until the stop-intent redesign lands, and a greyed row would be explaining a
 * control that does not exist yet.
 *
 * Held apart from [appSettingBlocked] rather than folded into it so that the difference between
 * "cannot work yet" and "will never work on this fork" stays stated.
 */
fun appSettingHidden(userData: UserData, key: String): Boolean =
    key == AppSettingKeys.SHIZUKU_SERVICE && !userData.shizukuForkMode.supportsIntents

fun appSettingBlocked(userData: UserData, key: String): Boolean ='''

# =========================================================================================
# 2 — the ViewModel: hide the one, publish the rest as blocked
# =========================================================================================

VM_ROWS_OLD = """    // ⚠ **Still removed rather than greyed.** The author asked for these to be shown and
    // greyed with a pop-up; that is the half of open item 2 waiting on his approval of the
    // rendered template. What changed here is only which question decides it.
    val appSettingsUiState =
        combine(
            appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName),
            userDataRepository.userData,
        ) { appSettings, userData ->
            // ⚠ **One question, and the hide asks the same one.** This used to be two private
            // predicates in :domain:model that answered for the overlay marker and the Shizuku
            // marker separately - and disagreed with the engine, which went on acting on the
            // Shizuku marker after the screen had hidden it. `appSettingBlocked` reads
            // `canHide`, so a row that leaves the screen is a row the hide will not act on.
            appSettings.filterNot { appSettingBlocked(userData = userData, key = it.key) }
        }.map(AppSettingsUiState::Success).stateIn("""

VM_ROWS_NEW = """    // ⚠ **Shown and greyed, not removed.** The author's instruction for open item 2. Only
    // [appSettingHidden] takes a row off the screen, and it answers for exactly one case -
    // the Shizuku marker on a fork with no intents, which has no engine behind it yet.
    val appSettingsUiState =
        combine(
            appSettingsRepository.getAppSettingsFlowByComponentName(componentName = componentName),
            userDataRepository.userData,
        ) { appSettings, userData ->
            appSettings.filterNot { appSettingHidden(userData = userData, key = it.key) }
        }.map(AppSettingsUiState::Success).stateIn("""

VM_TEMPLATES_OLD = """    // The same question as the rows above, for the same reason: a template that cannot be
    // added to do anything is worse than a template that is not offered. Greying these is the
    // other half of open item 2.
    val appSettingTemplates = combine(
        _appSettingTemplates,
        userDataRepository.userData,
    ) { templates, userData ->
        templates.filterNot { appSettingBlocked(userData = userData, key = it.key) }
    }.onStart {"""

VM_TEMPLATES_NEW = """    // The same rule as the rows above: offered and greyed, so a press can say what to go and
    // configure. Only the no-intents Shizuku marker leaves the list.
    val appSettingTemplates = combine(
        _appSettingTemplates,
        userDataRepository.userData,
    ) { templates, userData ->
        templates.filterNot { appSettingHidden(userData = userData, key = it.key) }
    }.onStart {"""

VM_BLOCKED = '''
    /**
     * Which of the drawn keys IMD cannot act on right now, and why the overlay one cannot.
     *
     * ⚠ **The reasons rather than the sentences**, for the reason `:domain:model` returns them
     * at all: paths are resources and cannot live in the domain, and Display over other apps
     * has three ways to be unusable that are fixed in three different places. The screen maps
     * them to this module's own copy of the wording.
     *
     * ⚠ **Asked of the three keys that mean something beyond "write this".** Everything else
     * in a profile is a Settings row IMD writes directly and can always write.
     */
    val blockedAppSettings = userDataRepository.userData.map { userData ->
        BlockedAppSettings(
            keys = GATED_KEYS.filter { appSettingBlocked(userData = userData, key = it) }.toSet(),
            overlayReasons = overlayBlockReasons(userData = userData),
        )
    }.distinctUntilChanged().stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = BlockedAppSettings(),
    )
'''

VM_TAIL_ANCHOR = """    fun requestPinShortcut("""

VM_TYPES = '''
/**
 * The per-app keys that can be greyed, and why.
 *
 * A value rather than three flags so the screen asks one question per row. `overlayReasons` is
 * empty when Display over other apps is usable **and** on Shevery, where it is unsupported
 * rather than unconfigured - the empty list is what picks the author's fork sentence over his
 * configure-first one, exactly as it does in the two configuration dialogs and the settings
 * manager.
 */
internal data class BlockedAppSettings(
    val keys: Set<String> = emptySet(),
    val overlayReasons: List<OverlayBlockReason> = emptyList(),
)

/** The three keys that mean more to IMD than "write this value". */
private val GATED_KEYS = listOf(
    AppSettingKeys.SYSTEM_ALERT_WINDOW,
    AppSettingKeys.SHIZUKU_SERVICE,
    AppSettingKeys.ACCESSIBILITY_ENABLED,
)
'''

VM_IMPORTS = (
    "import com.android.geto.domain.model.AppSettingKeys",
    "import com.android.geto.domain.model.OverlayBlockReason",
    "import com.android.geto.domain.model.appSettingHidden",
    "import com.android.geto.domain.model.overlayBlockReasons",
    "import kotlinx.coroutines.flow.distinctUntilChanged",
)

# =========================================================================================
# 3 — TemplateDialog
# =========================================================================================

TD_SIG_OLD = """internal fun TemplateDialog(
    modifier: Modifier = Modifier,
    appSettingTemplates: List<AppSettingTemplate>,
    componentName: String,
    onAddAppSetting: (AppSetting) -> Unit,
    onDismissRequest: () -> Unit,
) {"""

TD_SIG_NEW = """internal fun TemplateDialog(
    modifier: Modifier = Modifier,
    appSettingTemplates: List<AppSettingTemplate>,
    componentName: String,
    /**
     * The keys IMD cannot act on right now, drawn greyed rather than left out.
     *
     * ⚠ **Offered and refused, not withheld.** A template that quietly vanished left the user
     * with no way to find out that the feature exists or what it needs; greyed, a press says
     * both. The author's instruction for open item 2.
     */
    blockedKeys: Set<String>,
    onBlockedClick: (String) -> Unit,
    onAddAppSetting: (AppSetting) -> Unit,
    onDismissRequest: () -> Unit,
) {"""

TD_CALL_OLD = """                    AppSettingTemplateItem(
                        appSettingTemplate = appSettingTemplate,
                        componentName = componentName,
                        onAddAppSetting = onAddAppSetting,
                    )"""

TD_CALL_NEW = """                    AppSettingTemplateItem(
                        appSettingTemplate = appSettingTemplate,
                        componentName = componentName,
                        enabled = appSettingTemplate.key !in blockedKeys,
                        onBlockedClick = { onBlockedClick(appSettingTemplate.key) },
                        onAddAppSetting = onAddAppSetting,
                    )"""

TD_ITEM_OLD = """@Composable
private fun AppSettingTemplateItem(
    modifier: Modifier = Modifier,
    appSettingTemplate: AppSettingTemplate,
    componentName: String,
    onAddAppSetting: (AppSetting) -> Unit,
) {
    Row(
        modifier = modifier.padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = appSettingTemplate.label,
                style = MaterialTheme.typography.bodyLarge,
            )"""

TD_ITEM_NEW = """@Composable
private fun AppSettingTemplateItem(
    modifier: Modifier = Modifier,
    appSettingTemplate: AppSettingTemplate,
    componentName: String,
    enabled: Boolean,
    onBlockedClick: () -> Unit,
    onAddAppSetting: (AppSetting) -> Unit,
) {
    // Material's disabled pair, restated rather than inherited: this row draws its own text
    // colours, so `LocalContentColor` alone would leave the label at full strength.
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    val supportColour = if (enabled) {
        MaterialTheme.colorScheme.onSurfaceVariant
    } else {
        MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    Row(
        modifier = modifier
            .fillMaxWidth()
            // ⚠ **The whole row answers, and only while it is refusing.** A greyed template
            // that did nothing at all when tapped reads as a broken list; an enabled one keeps
            // its single affordance, the + button, so a stray tap on the text cannot add a row
            // nobody asked for.
            .then(if (enabled) Modifier else Modifier.clickable(onClick = onBlockedClick))
            .padding(10.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(
                text = appSettingTemplate.label,
                style = MaterialTheme.typography.bodyLarge,
                color = contentColour,
            )"""

TD_DESC_OLD = """                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )"""

TD_DESC_NEW = """                Text(
                    text = description,
                    style = MaterialTheme.typography.bodySmall,
                    color = supportColour,
                )"""

TD_TYPE_OLD = """            Text(
                text = appSettingTemplate.settingType.getSettingTypeTitle(),
                style = MaterialTheme.typography.bodySmall,
            )

            Spacer(modifier = Modifier.height(5.dp))

            Text(
                text = appSettingTemplate.key,
                style = MaterialTheme.typography.bodySmall,
            )
        }

        IconButton(
            onClick = {
                onAddAppSetting(
                    AppSetting(
                        enabled = true,
                        settingType = appSettingTemplate.settingType,
                        componentName = componentName,
                        label = appSettingTemplate.label,
                        key = appSettingTemplate.key,
                        valueOnLaunch = appSettingTemplate.valueOnLaunch,
                        valueOnRevert = appSettingTemplate.valueOnRevert,
                    ),
                )
            },
        ) {
            Icon(
                imageVector = GetoIcons.Add,
                contentDescription = null,
            )
        }
    }
}"""

TD_TYPE_NEW = """            Text(
                text = appSettingTemplate.settingType.getSettingTypeTitle(),
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )

            Spacer(modifier = Modifier.height(5.dp))

            Text(
                text = appSettingTemplate.key,
                style = MaterialTheme.typography.bodySmall,
                color = contentColour,
            )
        }

        // ⚠ **Enabled and branching, rather than disabled.** A disabled IconButton swallows
        // the press inside its own bounds, so the row's `clickable` above never sees it and
        // the one place a user is most likely to tap would be the one place that says nothing.
        IconButton(
            onClick = {
                if (!enabled) {
                    onBlockedClick()

                    return@IconButton
                }

                onAddAppSetting(
                    AppSetting(
                        enabled = true,
                        settingType = appSettingTemplate.settingType,
                        componentName = componentName,
                        label = appSettingTemplate.label,
                        key = appSettingTemplate.key,
                        valueOnLaunch = appSettingTemplate.valueOnLaunch,
                        valueOnRevert = appSettingTemplate.valueOnRevert,
                    ),
                )
            },
        ) {
            Icon(
                imageVector = GetoIcons.Add,
                contentDescription = null,
                tint = contentColour,
            )
        }
    }
}

/** Material's disabled content alpha, restated where a row draws its own colours. */
private const val DISABLED_CONTENT_ALPHA = 0.38f"""

TD_IMPORTS = (
    "import androidx.compose.foundation.clickable",
)

# =========================================================================================
# 4 — the screen
# =========================================================================================

SCREEN_COLLECT_OLD = """    val appSettingTemplates by viewModel.appSettingTemplates.collectAsStateWithLifecycle()"""

SCREEN_COLLECT_NEW = """    val appSettingTemplates by viewModel.appSettingTemplates.collectAsStateWithLifecycle()

    val blockedAppSettings by viewModel.blockedAppSettings.collectAsStateWithLifecycle()"""

# ⚠ Anchored to its neighbour: the bare argument line also occurs in the TemplateDialog call
# below, and a substring count would have matched both.
SCREEN_PASS_OLD = """        requestPinShortcutResult = requestPinShortcutResult,
        appSettingTemplates = appSettingTemplates,"""

SCREEN_PASS_NEW = """        requestPinShortcutResult = requestPinShortcutResult,
        appSettingTemplates = appSettingTemplates,
        blockedAppSettings = blockedAppSettings,"""

SCREEN_SIG_OLD = """    appSettingTemplates: List<AppSettingTemplate>,"""

SCREEN_SIG_NEW = """    appSettingTemplates: List<AppSettingTemplate>,
    /** Which drawn keys are greyed, and why the Display over other apps one is. */
    blockedAppSettings: BlockedAppSettings,"""

SCREEN_STATE_OLD = """    var showTemplateDialog by rememberSaveable { mutableStateOf(false) }"""

SCREEN_STATE_NEW = """    var showTemplateDialog by rememberSaveable { mutableStateOf(false) }

    // Null while nothing is refusing; a list of location trees otherwise, empty for the one
    // case with nothing to point at - Shevery, where Display over other apps is unsupported
    // rather than unconfigured. The empty list is what picks the fork sentence over the
    // configure-first one. Same convention as the two configuration dialogs.
    var blockedPaths by remember { mutableStateOf<List<String>?>(null) }

    val accessibilityPath = stringResource(R.string.help_path_accessibility)

    val dooaPath = stringResource(R.string.help_path_dooa)

    val manageShizukuPath = stringResource(R.string.help_path_manage_shizuku)

    // ⚠ **The decision is not repeated here, only the wording.** `overlayBlockReasons` in
    // `:domain:model` is the single answer to why the overlay row will not move; this module
    // cannot see the other two modules' resources, so what is duplicated is five strings
    // rather than a rule.
    val pathsFor = { key: String ->
        when (key) {
            AppSettingKeys.SYSTEM_ALERT_WINDOW -> blockedAppSettings.overlayReasons.mapNotNull {
                when (it) {
                    OverlayBlockReason.ForkUnsupported -> null

                    OverlayBlockReason.ManageShizukuOff -> manageShizukuPath

                    OverlayBlockReason.NothingSelected -> dooaPath
                }
            }

            AppSettingKeys.SHIZUKU_SERVICE -> listOf(manageShizukuPath)

            else -> listOf(accessibilityPath)
        }
    }"""

SCREEN_TEMPLATE_CALL_OLD = """        TemplateDialog(
            appSettingTemplates = appSettingTemplates,
            componentName = appSettingsRouteData.componentName,
            onAddAppSetting = onAddAppSetting,
            onDismissRequest = {
                showTemplateDialog = false
            },
        )"""

SCREEN_TEMPLATE_CALL_NEW = """        TemplateDialog(
            appSettingTemplates = appSettingTemplates,
            componentName = appSettingsRouteData.componentName,
            blockedKeys = blockedAppSettings.keys,
            onBlockedClick = { blockedPaths = pathsFor(it) },
            onAddAppSetting = onAddAppSetting,
            onDismissRequest = {
                showTemplateDialog = false
            },
        )"""

SCREEN_SUCCESS_CALL_OLD = """                        Success(
                            appSettingsUiState = appSettingsUiState,
                            onCheckAppSetting = onCheckAppSetting,
                            onDeleteAppSettingsItem = onDeleteAppSetting,
                        )"""

SCREEN_SUCCESS_CALL_NEW = """                        Success(
                            appSettingsUiState = appSettingsUiState,
                            blockedKeys = blockedAppSettings.keys,
                            onBlockedClick = { blockedPaths = pathsFor(it) },
                            onCheckAppSetting = onCheckAppSetting,
                            onDeleteAppSettingsItem = onDeleteAppSetting,
                        )"""

SCREEN_DIALOG_OLD = """    if (showTemplateDialog) {"""

SCREEN_DIALOG_NEW = """    blockedPaths?.let { paths ->
        ConfigureFirstDialog(
            message = if (paths.isEmpty()) {
                stringResource(R.string.dooa_thedjchi_only)
            } else {
                stringResource(R.string.configure_first)
            },
            paths = paths,
            dismissLabel = stringResource(R.string.understood),
            onDismissRequest = { blockedPaths = null },
        )
    }

    if (showTemplateDialog) {"""

SCREEN_SUCCESS_OLD = """@Composable
private fun Success(
    modifier: Modifier = Modifier,
    appSettingsUiState: AppSettingsUiState.Success,
    onCheckAppSetting: (AppSetting) -> Unit,
    onDeleteAppSettingsItem: (AppSetting) -> Unit,
) {
    LazyColumn(modifier = modifier) {
        items(items = appSettingsUiState.appSettings, key = { it.id }) { appSettings ->
            AppSettingItem(
                appSetting = appSettings,
                onCheckedChange = { check ->
                    onCheckAppSetting(
                        appSettings.copy(enabled = check),
                    )
                },
                onDeleteClick = {
                    onDeleteAppSettingsItem(appSettings)
                },
            )
        }
    }
}"""

SCREEN_SUCCESS_NEW = """@Composable
private fun Success(
    modifier: Modifier = Modifier,
    appSettingsUiState: AppSettingsUiState.Success,
    blockedKeys: Set<String>,
    onBlockedClick: (String) -> Unit,
    onCheckAppSetting: (AppSetting) -> Unit,
    onDeleteAppSettingsItem: (AppSetting) -> Unit,
) {
    LazyColumn(modifier = modifier) {
        items(items = appSettingsUiState.appSettings, key = { it.id }) { appSettings ->
            AppSettingItem(
                appSetting = appSettings,
                enabled = appSettings.key !in blockedKeys,
                onBlockedClick = { onBlockedClick(appSettings.key) },
                onCheckedChange = { check ->
                    onCheckAppSetting(
                        appSettings.copy(enabled = check),
                    )
                },
                onDeleteClick = {
                    onDeleteAppSettingsItem(appSettings)
                },
            )
        }
    }
}"""

SCREEN_ITEM_OLD = """@Composable
private fun LazyItemScope.AppSettingItem(
    modifier: Modifier = Modifier,
    appSetting: AppSetting,
    onCheckedChange: (Boolean) -> Unit,
    onDeleteClick: () -> Unit,
) {
    ListItem(
        modifier = modifier.animateItem(),
        headlineContent = {
            Text(
                text = appSetting.label,
            )
        },
        overlineContent = {
            Text(
                text = appSetting.key,
            )
        },
        supportingContent = {
            Text(
                text = appSetting.settingType.getSettingTypeTitle(),
            )
        },
        leadingContent = {
            Checkbox(
                checked = appSetting.enabled,
                onCheckedChange = onCheckedChange,
            )
        },"""

SCREEN_ITEM_NEW = """@Composable
private fun LazyItemScope.AppSettingItem(
    modifier: Modifier = Modifier,
    appSetting: AppSetting,
    enabled: Boolean,
    onBlockedClick: () -> Unit,
    onCheckedChange: (Boolean) -> Unit,
    onDeleteClick: () -> Unit,
) {
    val contentColour = if (enabled) {
        MaterialTheme.colorScheme.onSurface
    } else {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DISABLED_CONTENT_ALPHA)
    }

    ListItem(
        modifier = modifier
            .animateItem()
            .then(if (enabled) Modifier else Modifier.clickable(onClick = onBlockedClick)),
        headlineContent = {
            Text(
                text = appSetting.label,
                color = contentColour,
            )
        },
        overlineContent = {
            Text(
                text = appSetting.key,
                color = contentColour,
            )
        },
        supportingContent = {
            Text(
                text = appSetting.settingType.getSettingTypeTitle(),
                color = contentColour,
            )
        },
        leadingContent = {
            // ⚠ **Unticked while blocked, and only in the drawing.** The stored row is not
            // touched - `onCheckedChange` cannot be reached from here - so the tick comes
            // straight back when the thing this row needs is configured again. The author:
            // "shown unchecked and unclickable with the checkbox position remembered".
            //
            // ⚠ **Wrapped in a Box, not merely disabled.** A disabled Checkbox swallows the
            // press inside its own bounds, so the ListItem's clickable above would never see
            // a tap on the one control the user is aiming at.
            Box(
                modifier = if (enabled) {
                    Modifier
                } else {
                    Modifier.clickable(onClick = onBlockedClick)
                },
            ) {
                Checkbox(
                    checked = enabled && appSetting.enabled,
                    enabled = enabled,
                    onCheckedChange = onCheckedChange,
                )
            }
        },"""

SCREEN_TAIL_OLD = """@Composable
internal fun SettingType.getSettingTypeTitle() = when (this) {"""

SCREEN_TAIL_NEW = """/** Material's disabled content alpha, restated where a row draws its own colours. */
private const val DISABLED_CONTENT_ALPHA = 0.38f

@Composable
internal fun SettingType.getSettingTypeTitle() = when (this) {"""

SCREEN_IMPORTS = (
    "import androidx.compose.foundation.clickable",
    "import androidx.compose.foundation.layout.Box",
    "import com.android.geto.designsystem.component.ConfigureFirstDialog",
    "import com.android.geto.domain.model.AppSettingKeys",
    "import com.android.geto.domain.model.OverlayBlockReason",
)

# =========================================================================================
# 5 — the five strings this module cannot see
# =========================================================================================

STRINGS_ANCHOR = "</resources>"

STRINGS_NEW = """
    <!-- ⚠ Duplicated from feature/settings and feature/apps, which this module cannot see.
      check5_dupes treats identical strings across modules as intentional; string/understood is
      already shared exactly this way. The wording is the author's and must stay identical in
      all three, or the same refusal would be worded three ways. -->
    <string name="understood">Understood</string>
    <string name="configure_first">Please configure the settings first</string>
    <string name="dooa_thedjchi_only">managing Display over other apps is only supported for Thedjchi fork of Shizuku</string>
    <string name="help_path_accessibility">IMD Settings \\u2192 Default IMD settings \\u2192 Accessibility services to hide</string>
    <string name="help_path_dooa">IMD Settings \\u2192 Default IMD settings \\u2192 Display over other apps to hide</string>
    <string name="help_path_manage_shizuku">IMD Settings \\u2192 Shizuku configuration \\u2192 Manage Shizuku</string>
</resources>"""

EDITS = [
    (OVERLAY, "appSettingHidden", DOMAIN_ANCHOR, DOMAIN_NEW),
    (VM, "the rows flow", VM_ROWS_OLD, VM_ROWS_NEW),
    (VM, "the templates flow", VM_TEMPLATES_OLD, VM_TEMPLATES_NEW),
    (VM, "blockedAppSettings", VM_TAIL_ANCHOR, VM_BLOCKED.lstrip("\n") + "\n" + VM_TAIL_ANCHOR),
    (TEMPLATES, "TemplateDialog's signature", TD_SIG_OLD, TD_SIG_NEW),
    (TEMPLATES, "the item call", TD_CALL_OLD, TD_CALL_NEW),
    (TEMPLATES, "AppSettingTemplateItem's head", TD_ITEM_OLD, TD_ITEM_NEW),
    (TEMPLATES, "the description colour", TD_DESC_OLD, TD_DESC_NEW),
    (TEMPLATES, "the type, key and add button", TD_TYPE_OLD, TD_TYPE_NEW),
    (SCREEN, "the collect", SCREEN_COLLECT_OLD, SCREEN_COLLECT_NEW),
    (SCREEN, "the pass-down", SCREEN_PASS_OLD, SCREEN_PASS_NEW),
    (SCREEN, "the screen's signature", SCREEN_SIG_OLD, SCREEN_SIG_NEW),
    (SCREEN, "the blocked state", SCREEN_STATE_OLD, SCREEN_STATE_NEW),
    (SCREEN, "the Success call", SCREEN_SUCCESS_CALL_OLD, SCREEN_SUCCESS_CALL_NEW),
    (SCREEN, "the ConfigureFirstDialog", SCREEN_DIALOG_OLD, SCREEN_DIALOG_NEW),
    (SCREEN, "the TemplateDialog call", SCREEN_TEMPLATE_CALL_OLD, SCREEN_TEMPLATE_CALL_NEW),
    (SCREEN, "Success", SCREEN_SUCCESS_OLD, SCREEN_SUCCESS_NEW),
    (SCREEN, "AppSettingItem", SCREEN_ITEM_OLD, SCREEN_ITEM_NEW),
    (SCREEN, "the alpha constant", SCREEN_TAIL_OLD, SCREEN_TAIL_NEW),
    (STRINGS, "the five strings", STRINGS_ANCHOR, STRINGS_NEW.lstrip("\n")),
]

IMPORTS = (
    [(VM, s) for s in VM_IMPORTS]
    + [(TEMPLATES, s) for s in TD_IMPORTS]
    + [(SCREEN, s) for s in SCREEN_IMPORTS]
)


def insert_import(text: str, statement: str) -> str:
    lines = text.split("\n")

    if statement in lines:
        return text

    idx = [i for i, line in enumerate(lines) if line.startswith("import ")]

    sortable = [
        i for i in idx
        if not lines[i].startswith(("import javax.", "import java."))
        and " as " not in lines[i]
    ]

    at = next((i for i in sortable if lines[i] > statement), sortable[-1] + 1)
    lines.insert(at, statement)

    return "\n".join(lines)


def main() -> int:
    staged: dict[Path, str] = {}
    originals: dict[Path, str] = {}

    def read(rel: str) -> str:
        path = ROOT / rel

        if path not in staged:
            if not path.is_file():
                raise SystemExit(f"REFUSED: missing {rel}")

            originals[path] = path.read_text(encoding="utf-8")
            staged[path] = originals[path]

        return staged[path]

    for rel, name, old, new in EDITS:
        text = read(rel)

        found = text.count(old)

        if found != 1:
            print(f"REFUSED: {rel}\n  {name} matched {found} time(s), expected exactly 1")
            return 1

        staged[ROOT / rel] = text.replace(old, new, 1)

    # The two top-level declarations go at the end of the ViewModel file, after everything
    # that references them. Appended rather than anchored: there is no landmark at the tail
    # of that file, and an anchor that names a declaration by its neighbour is the r4e trap.
    vm_text = read(VM)

    if not vm_text.endswith("}\n"):
        print(f"REFUSED: {VM} does not end with a closing brace, cannot append")
        return 1

    staged[ROOT / VM] = vm_text + VM_TYPES

    for rel, statement in IMPORTS:
        staged[ROOT / rel] = insert_import(read(rel), statement)

    # --- what the edits must have produced -------------------------------------------
    vm = staged[ROOT / VM]

    # ⚠ Neither flow may still remove a blocked row: greying is the whole instruction.
    if "appSettingBlocked(userData = userData, key = it.key)" in vm:
        print("REFUSED: a flow still filters on appSettingBlocked — rows would still vanish")
        return 1

    if vm.count("appSettingHidden(userData = userData, key = it.key)") != 2:
        print("REFUSED: appSettingHidden should filter both flows, found "
              f"{vm.count('appSettingHidden(userData = userData, key = it.key)')}")
        return 1

    # Assert POSITION: the data class and the key list are top level, below the ViewModel.
    at_class = vm.index("internal data class BlockedAppSettings(")
    at_keys = vm.index("private val GATED_KEYS = listOf(")
    at_flow = vm.index("    val blockedAppSettings = userDataRepository.userData.map")

    if not at_flow < at_class < at_keys:
        print(f"REFUSED: placement wrong — flow@{at_flow} class@{at_class} keys@{at_keys}")
        return 1

    screen = staged[ROOT / SCREEN]

    # Every greyed control is wrapped rather than left to swallow its own press.
    if screen.count("Modifier.clickable(onClick = onBlockedClick)") != 2:
        print("REFUSED: the row and its checkbox must each take the blocked press, found "
              f"{screen.count('Modifier.clickable(onClick = onBlockedClick)')}")
        return 1

    # The checkbox draws unticked while blocked and never writes.
    if "checked = enabled && appSetting.enabled," not in screen:
        print("REFUSED: the checkbox lost its unticked guard")
        return 1

    templates = staged[ROOT / TEMPLATES]

    if "onBlockedClick()" not in templates:
        print("REFUSED: the add button does not answer a blocked press")
        return 1

    for path, text in staged.items():
        was = {line for line in originals[path].split("\n") if len(line) > 120}

        gained = [
            (n, len(line))
            for n, line in enumerate(text.split("\n"), 1)
            if len(line) > 120
            and not line.lstrip().startswith(("import ", "<string name="))
            and line not in was
        ]

        if gained:
            print(f"REFUSED: {path.relative_to(ROOT)} would gain lines over 120: {gained}")
            return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    for rel in (OVERLAY, VM, TEMPLATES, SCREEN, STRINGS):
        print(f"  ok        {rel}")

    print("\n  ~ templates and rows are greyed, not removed")
    print("  ~ greyed draws unticked; the stored tick is untouched")
    print("  ~ only the no-intents Shizuku marker still leaves the screen")
    print(f"\nwrote {len(staged)} file(s), {len(EDITS)} edit(s)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
