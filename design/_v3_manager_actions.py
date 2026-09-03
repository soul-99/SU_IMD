#!/usr/bin/env python3
"""
v3-r2g — the Settings Manager dialog: the author's five changes to it.

1. **The title drops IMD.** `settings_manager_title` becomes `Settings Manager`, in all
   eleven locales.
2. **The centred logo button is gone**, and its job moves onto the app icon beside the title,
   which was already there and already says which app put this dialog in front of you. The two
   drawables generated for it in r2 go with it.
3. **The two scope descriptions** under Accessibility services and Display over other apps are
   dropped, at the author's instruction.
4. **A new `Unhide settings` button**, first, with `Revert to default` beside it. Both carry
   their own glyph enlarged as a centred watermark; both are equal width, which is what gives
   the two watermarks the same room.
5. **Close moves to its own row below**, right-aligned.

### ⚠ The title rename does not need a single translated sentence rewritten

`check_translations.py` asserts each locale's `settings_manager_title` appears **verbatim
inside** that locale's `settings_manager_info_live`, so that the bolding matches something.
Dropping `IMD` from a title that is embedded in a longer sentence would normally break all
eleven — except that in every locale the word sits at one end of the phrase, so the shortened
title is still a substring of the untouched sentence:

    IMD Settings Manager           -> Settings Manager            (prefix dropped)
    IMD 設定マネージャー              -> 設定マネージャー              (prefix dropped)
    Gestionnaire de paramètres IMD -> Gestionnaire de paramètres   (suffix dropped)

The script asserts that containment per locale rather than trusting it. **Only English's
`settings_manager_info_live` is rewritten**, and only because the author supplied new wording
for it; the other ten keep the sentence they have, which still contains their own new title.

⚠ The author's new English sentence keeps `IMD Settings Manager` inside it while the title is
now `Settings Manager`, so the bold will cover `Settings Manager` and leave `IMD` in plain
text. That is what the author wrote, and it is left exactly as written — rule 1.

### The greyed button is still a button

The author: *"only keep it clickable when settings are hidden and otherwise greyed out ... and
on being clicked show the toast"*. Drawn in the disabled palette but still taking the press,
which is the pattern the unusable switches in this same dialog already use — a control that
swallows taps in silence is the least legible thing this screen can do.

**And nothing branches on it.** `SettingsHiddenRunner.unhidePending` already asks the three
debt questions and already says `'IMD: No hidden settings to restore'` when the answer is
none, so the press runs the same call either way and the flag only decides the colour. Two
tests that could disagree would be one too many.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

APPS = "feature/apps/src/main/kotlin/com/android/geto/feature/apps"

DIALOG = f"{APPS}/dialog/AndroidSettingsManagerDialog.kt"

ROUTE = f"{APPS}/manager/SettingsManagerRoute.kt"

VIEW_MODEL = f"{APPS}/manager/SettingsManagerViewModel.kt"

RES = "feature/apps/src/main/res"

DESIGN_SYSTEM_DRAWABLES = "design-system/src/main/res/drawable"

# locale directory -> (old title, new title). The word IMD sits at one end in every one, so
# each new title is still a substring of that locale's untouched info sentence.
TITLES = {
    "values": ("IMD Settings Manager", "Settings Manager"),
    "values-ar": ("مدير إعدادات IMD", "مدير إعدادات"),
    "values-b+pt+BR": ("Gerenciador de configurações do IMD", "Gerenciador de configurações"),
    "values-b+zh+Hans": ("IMD 设置管理器", "设置管理器"),
    "values-de": ("IMD-Einstellungsmanager", "Einstellungsmanager"),
    "values-es": ("Gestor de ajustes de IMD", "Gestor de ajustes"),
    "values-fr": ("Gestionnaire de paramètres IMD", "Gestionnaire de paramètres"),
    "values-hi": ("IMD सेटिंग्स प्रबंधक", "सेटिंग्स प्रबंधक"),
    "values-ja": ("IMD 設定マネージャー", "設定マネージャー"),
    "values-ko": ("IMD 설정 관리자", "설정 관리자"),
    "values-ru": ("Диспетчер настроек IMD", "Диспетчер настроек"),
}

# The author's sentence, verbatim. English only — see the module docstring.
INFO_LIVE_OLD = (
    "<string name=\"settings_manager_info_live\">IMD Settings Manager displays the live "
    "status of settings and change them easily.</string>"
)

INFO_LIVE_NEW = (
    "<string name=\"settings_manager_info_live\">IMD Settings Manager displays the live "
    "status of settings and helps you turn them on/off easily.</string>"
)

DIALOG_EDITS: list[tuple[str, str]] = [
    (
        """import androidx.annotation.StringRes
""",
        """import androidx.annotation.DrawableRes
import androidx.annotation.StringRes
""",
    ),
    (
        """import androidx.compose.ui.res.stringResource
""",
        """import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.style.TextAlign
""",
    ),
    # The two new parameters.
    (
        """    onDismissRequest: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
    onRevertToDefault: () -> Unit,
    onOpenRevertConfiguration: () -> Unit,
) {""",
        """    /**
     * Whether anything IMD did is still outstanding — a device-wide hide, per-app records, or
     * an IMD+ run. Decides only how `Unhide settings` is **drawn**; the press runs the same
     * call either way and answers for itself. See the note on [ActionButton].
     */
    anythingHidden: Boolean = false,
    onDismissRequest: () -> Unit,
    onSetEnabled: (ManualRevertTarget, Boolean) -> Unit,
    onOpen: (ManualRevertTarget) -> Unit,
    onUnhideSettings: () -> Unit,
    onRevertToDefault: () -> Unit,
    onOpenRevertConfiguration: () -> Unit,
) {""",
    ),
    # The header: a Box with a centred button becomes a plain Row again.
    (
        """            // A Box, so the new button can be centred on the dialog rather than placed
            // after the ⓘ. The author asked for it centred above the toggles, and the title
            // line is the line above the toggles.
            Box(modifier = Modifier.fillMaxWidth().padding(10.dp)) {
                Row(
                    modifier = Modifier.align(Alignment.CenterStart),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    Image(
                        modifier = Modifier.size(32.dp),
                        painter = painterResource(designR.drawable.ic_imd_app),
                        contentDescription = null,
                    )

                    Spacer(modifier = Modifier.width(12.dp))

                    Text(
                        text = stringResource(R.string.settings_manager_title),
                        style = MaterialTheme.typography.titleLarge,
                    )

                    Spacer(modifier = Modifier.width(4.dp))

                    IconButton(onClick = { showInfo = true }) {
                        Icon(
                            modifier = Modifier.size(18.dp),
                            imageVector = GetoIcons.Info,
                            contentDescription = stringResource(R.string.settings_manager_info),
                            tint = MaterialTheme.colorScheme.onSurfaceVariant,
                        )
                    }
                }

                ManagerLogoButton(
                    modifier = Modifier.align(Alignment.Center),
                    onClick = {
                        onDismissRequest()

                        context.relaunchToAdvancedSettings()
                    },
                )
            }
""",
        """            // A plain Row again. r2's centred logo button is gone and its job has moved
            // onto the app icon below, at the author's instruction — the icon was already
            // there, already says which app put this dialog in front of you, and one glyph
            // on this line is easier to aim at than two.
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // The icon is the button now. Clipped to a circle so the ripple matches the
                // shape a launcher draws it in, and left at 32dp rather than grown to a 48dp
                // target: this sits on the title line, and a taller press area would push the
                // title and the ⓘ out of line with it.
                Image(
                    modifier = Modifier
                        .size(32.dp)
                        .clip(CircleShape)
                        .clickable {
                            onDismissRequest()

                            context.relaunchToAdvancedSettings()
                        },
                    painter = painterResource(designR.drawable.ic_imd_app),
                    contentDescription = stringResource(
                        R.string.settings_manager_open_settings,
                    ),
                )

                Spacer(modifier = Modifier.width(12.dp))

                Text(
                    text = stringResource(R.string.settings_manager_title),
                    style = MaterialTheme.typography.titleLarge,
                )

                Spacer(modifier = Modifier.width(4.dp))

                IconButton(onClick = { showInfo = true }) {
                    Icon(
                        modifier = Modifier.size(18.dp),
                        imageVector = GetoIcons.Info,
                        contentDescription = stringResource(R.string.settings_manager_info),
                        tint = MaterialTheme.colorScheme.onSurfaceVariant,
                    )
                }
            }
""",
    ),
    # The action rows.
    (
        """            // A clear gap before the action row, so Revert to default does not sit hard against
            // the last toggle above it.
            Spacer(modifier = Modifier.height(16.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // Filled, unlike Close, because it does something to the device while the
                // other one only shuts the dialog. The rows above are switches; without the
                // weight difference this would read as a third way to close.
                // Deliberately does not dismiss. The rows below are polled live, so staying
                // open is what shows the revert happening — closing would hide the one piece
                // of feedback the action has.
                // A Surface rather than a Button, only because Button has no long press and
                // this one needs one: holding it opens the configuration that decides what
                // the short press will do. Everything else here is Button's own shape,
                // colours and content padding, so it still reads as the filled button it
                // was.
                Surface(
                    modifier = Modifier.combinedClickable(
                        onClick = onRevertToDefault,
                        onLongClick = onOpenRevertConfiguration,
                        onLongClickLabel = stringResource(
                            R.string.settings_manager_configure_revert,
                        ),
                    ),
                    shape = ButtonDefaults.shape,
                    color = MaterialTheme.colorScheme.secondaryContainer,
                    contentColor = MaterialTheme.colorScheme.onSecondaryContainer,
                ) {
                    Row(
                        modifier = Modifier.padding(ButtonDefaults.ContentPadding),
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Icon(
                            modifier = Modifier.size(18.dp),
                            painter = painterResource(designR.drawable.ic_revert_glyph),
                            contentDescription = null,
                        )

                        Spacer(modifier = Modifier.width(8.dp))

                        Text(text = stringResource(R.string.revert_to_default))
                    }
                }

                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
""",
        """            // A clear gap before the action rows, so they do not sit hard against the last
            // toggle above them.
            Spacer(modifier = Modifier.height(16.dp))

            // Both filled, unlike Close, because both do something to the device while Close
            // only shuts the dialog. Neither dismisses: the rows above are polled live, so
            // staying open is what shows the work happening, and closing would hide the one
            // piece of feedback either action has.
            //
            // Equal width rather than each at its natural size. Two watermarked buttons of
            // different widths read as one button and one afterthought, and "Revert to
            // default" is long enough that the difference would be obvious.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(10.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                // Unhide first, at the author's instruction. It is the one people reach for,
                // and it is the safe one: it puts back what a hide took, where Revert to
                // default drives the configured list whatever was there before.
                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_hide_glyph,
                    label = stringResource(R.string.unhide_settings),
                    dimmed = !anythingHidden,
                    onClick = onUnhideSettings,
                )

                ActionButton(
                    modifier = Modifier.weight(1f),
                    glyph = designR.drawable.ic_revert_glyph,
                    label = stringResource(R.string.revert_to_default),
                    onClick = onRevertToDefault,
                    onLongClick = onOpenRevertConfiguration,
                    onLongClickLabel = stringResource(
                        R.string.settings_manager_configure_revert,
                    ),
                )
            }

            Spacer(modifier = Modifier.height(4.dp))

            // Its own row, right-aligned, at the author's instruction. Below the two rather
            // than beside them: with both of those filled and equal width, a third control on
            // the same line would have to be squeezed in, and the one that only closes the
            // dialog is the one that should give way.
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.End,
            ) {
                TextButton(onClick = onDismissRequest) {
                    Text(text = stringResource(R.string.close))
                }
            }
""",
    ),
    # The two scope descriptions come out of the row.
    (
        """            // These two rows are scoped to a chosen subset rather than the whole system
            // feature, and that difference is worth saying out loud - otherwise an "off"
            // here reads as "no accessibility service is running" or "no app can draw over
            // others", which is not what either of them means.
            val scopeNote = when (target) {
                ManualRevertTarget.AccessibilityServices ->
                    R.string.settings_manager_accessibility_note

                ManualRevertTarget.DisplayOverOtherApps ->
                    R.string.settings_manager_overlay_note

                else -> null
            }

            if (scopeNote != null) {
                Text(
                    text = stringResource(scopeNote),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant,
                )
            }
        }
""",
        """            // The two scope descriptions that used to sit here — "only services selected in
            // the IMD app settings are managed" and its overlay twin — are gone at the
            // author's instruction. Their strings are kept: the ⓘ dialog covers the same
            // ground, and a removed line is cheaper to put back than to re-translate.
        }
""",
    ),
    # The logo button and its size go with it, and ActionButton takes their place.
    (
        """/**
 * The monochrome IMD glyph, next to the ⓘ and sized against it.
 *
 * ⚠ **31dp, and the number is not arbitrary.** The author's rule is that the gear matches the
 * ⓘ by radius, not by box. The gear spans 26.13 of the icon's 108 viewport units as a radius,
 * and the ⓘ's circle spans 10 of its 24 — so a box of 18 × (10/24) ÷ (26.13/108) ≈ 31dp puts
 * the two circles at the same size. Drawn at a different size, the two stop matching.
 *
 * **Dual-tone**, which is why it is two drawables stacked rather than one tinted: a vector's
 * fillColor is baked in, so one file can only be tinted as a whole. The gear takes the outline
 * colour and the glyph inside it takes the ⓘ's own tint, so the pair reads as one icon in the
 * same family rather than as a shrunken app icon.
 */
@Composable
private fun ManagerLogoButton(
    modifier: Modifier = Modifier,
    onClick: () -> Unit,
) {
    Box(
        modifier = modifier
            .size(LOGO_BUTTON_SIZE)
            .clip(CircleShape)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center,
    ) {
        Icon(
            modifier = Modifier.size(LOGO_BUTTON_SIZE),
            painter = painterResource(designR.drawable.ic_imd_glyph_gear),
            contentDescription = stringResource(R.string.settings_manager_open_settings),
            tint = MaterialTheme.colorScheme.outline,
        )

        Icon(
            modifier = Modifier.size(LOGO_BUTTON_SIZE),
            painter = painterResource(designR.drawable.ic_imd_glyph_inner),
            contentDescription = null,
            tint = MaterialTheme.colorScheme.onSurfaceVariant,
        )
    }
}

private val LOGO_BUTTON_SIZE = 31.dp
""",
        """/**
 * One of the dialog's two filled actions, with its own glyph drawn large behind the label.
 *
 * **The watermark is the icon, not a decoration.** A leading glyph beside the text costs the
 * label horizontal room in a button that is already sharing the row, and pushes it off centre;
 * drawn behind at [WATERMARK_SIZE] and [WATERMARK_ALPHA] it says the same thing, is readable at
 * a glance, and leaves the label centred in its own button.
 *
 * ⚠ **[dimmed] does not disable anything.** The author asked for `Unhide settings` to be greyed
 * out with nothing outstanding *and* to answer with a toast when pressed, which a disabled
 * control cannot do — it swallows the press in silence, which is this screen's least legible
 * failure and the reason the unusable switches above are wrapped rather than disabled. So this
 * takes the press whatever it looks like, and the call underneath — `unhidePending` — is the
 * single thing that decides whether there was anything to do. Two tests that could disagree
 * would be one too many.
 *
 * A Surface rather than a Button, because Button has no long press and Revert to default needs
 * one: holding it opens the configuration that decides what the short press will do.
 */
@OptIn(ExperimentalFoundationApi::class)
@Composable
private fun ActionButton(
    modifier: Modifier = Modifier,
    @DrawableRes glyph: Int,
    label: String,
    dimmed: Boolean = false,
    onClick: () -> Unit,
    onLongClick: (() -> Unit)? = null,
    onLongClickLabel: String? = null,
) {
    // Material's own disabled pair, restated rather than borrowed from ButtonDefaults: these
    // are the colours a genuinely disabled button would take, and the point of this control is
    // that it looks disabled without being it.
    val container = if (dimmed) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTAINER_ALPHA)
    } else {
        MaterialTheme.colorScheme.secondaryContainer
    }

    val content = if (dimmed) {
        MaterialTheme.colorScheme.onSurface.copy(alpha = DIMMED_CONTENT_ALPHA)
    } else {
        MaterialTheme.colorScheme.onSecondaryContainer
    }

    Surface(
        modifier = modifier
            .height(ACTION_BUTTON_HEIGHT)
            .clip(ButtonDefaults.shape)
            .combinedClickable(
                onClick = onClick,
                onLongClick = onLongClick,
                onLongClickLabel = onLongClickLabel,
            ),
        shape = ButtonDefaults.shape,
        color = container,
        contentColor = content,
    ) {
        Box(contentAlignment = Alignment.Center) {
            Icon(
                modifier = Modifier.size(WATERMARK_SIZE),
                painter = painterResource(glyph),
                // Null, and deliberately: the label beside it already says what this button
                // is, and a screen reader announcing the glyph as well would say it twice.
                contentDescription = null,
                tint = content.copy(alpha = WATERMARK_ALPHA),
            )

            Text(
                modifier = Modifier.padding(horizontal = 8.dp),
                text = label,
                style = MaterialTheme.typography.labelLarge,
                textAlign = TextAlign.Center,
            )
        }
    }
}

/** Tall enough to hold a two-line label and a watermark without either crowding the other. */
private val ACTION_BUTTON_HEIGHT = 52.dp

private val WATERMARK_SIZE = 44.dp

/** Visible as a shape, never as competition for the label sitting on top of it. */
private const val WATERMARK_ALPHA = 0.16f

private const val DIMMED_CONTAINER_ALPHA = 0.12f

private const val DIMMED_CONTENT_ALPHA = 0.38f
""",
    ),
]

ROUTE_EDITS: list[tuple[str, str]] = [
    (
        """    val permissionsLost by viewModel.permissionsLost.collectAsStateWithLifecycle()
""",
        """    val permissionsLost by viewModel.permissionsLost.collectAsStateWithLifecycle()

    val anythingHidden by viewModel.anythingHidden.collectAsStateWithLifecycle()
""",
    ),
    (
        """        infoShown = infoShown,
        onInfoShown = viewModel::markInfoShown,
        onDismissRequest = onDismissRequest,
""",
        """        infoShown = infoShown,
        anythingHidden = anythingHidden,
        onInfoShown = viewModel::markInfoShown,
        onDismissRequest = onDismissRequest,
""",
    ),
    (
        """        onRevertToDefault = viewModel::revertToDefault,
""",
        """        // Not a revert to default: this settles what is actually outstanding and says so
        // when nothing is. See the ViewModel.
        onUnhideSettings = viewModel::unhideSettings,
        onRevertToDefault = viewModel::revertToDefault,
""",
    ),
]

VIEW_MODEL_EDITS: list[tuple[str, str]] = [
    (
        """import com.android.geto.broadcastreceiver.RevertToDefaultRunner
""",
        """import com.android.geto.broadcastreceiver.RevertToDefaultRunner
import com.android.geto.broadcastreceiver.SettingsHiddenRunner
""",
    ),
    (
        """import com.android.geto.domain.model.ShizukuForkDefaults
""",
        """import com.android.geto.domain.model.ShizukuForkDefaults
import com.android.geto.domain.model.settingsHidden
""",
    ),
    (
        """    private val revertToDefaultRunner: RevertToDefaultRunner,
""",
        """    private val revertToDefaultRunner: RevertToDefaultRunner,
    private val settingsHiddenRunner: SettingsHiddenRunner,
""",
    ),
    (
        """    fun markInfoShown() {
""",
        """    /**
     * Whether anything IMD did is still outstanding, by any of the three routes it can owe on.
     *
     * ⚠ **The same three questions `unhidePending` asks**, and derived from the same stored
     * values rather than from a flag of its own — `UserData.settingsHidden` is
     * `settingsHiddenDeviceWide || memoryHoldsSettings`, which is exactly what
     * `GetSettingsHiddenUseCase` returns. A separate test here could disagree with the one
     * doing the work, and the way it would show is a live button that says there is nothing
     * to restore, or a greyed one that would have restored something.
     */
    val anythingHidden: StateFlow<Boolean> = userDataRepository.userData
        .map { it.autoHideRunning || it.settingsHidden }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = false,
        )

    /**
     * Settle every debt that actually exists, or say there is none.
     *
     * ⚠ **`unhidePending`, not `unhide` and not a revert.** `unhide` is the Hide settings
     * tile's behaviour and falls back to the configured defaults on a device with nothing
     * hidden, because a tile that did nothing reads as broken; the author asked this button
     * for the opposite — `'IMD: No hidden settings to restore'`, and no setting touched.
     *
     * On the application scope for the reason [revertToDefault] is: opened from the tile or
     * the shortcut, this dialog's dismissal finishes the activity and takes this ViewModel
     * with it, and the work must outlive that.
     */
    fun unhideSettings() {
        appScope.launch { settingsHiddenRunner.unhidePending() }
    }

    fun markInfoShown() {
""",
    ),
]


def apply(path: Path, edits: list[tuple[str, str]], problems: list[str]) -> str | None:
    if not path.exists():
        problems.append(f"{path} is missing")

        return None

    text = path.read_text(encoding="utf-8")

    for old, new in edits:
        found = text.count(old)

        if found != 1:
            head = old.strip().splitlines()[0][:70] if old.strip() else old[:70]

            problems.append(f"{path.name}: {found} of {head!r}")

            continue

        text = text.replace(old, new, 1)

    return text


def main() -> int:
    problems: list[str] = []

    staged: dict[Path, str] = {}

    # --- the strings, and the containment the translation check depends on ---------------
    for values, (old_title, new_title) in TITLES.items():
        path = ROOT / RES / values / "strings.xml"

        if not path.exists():
            problems.append(f"{values}/strings.xml is missing")

            continue

        text = path.read_text(encoding="utf-8")

        marker = f"<string name=\"settings_manager_title\">{old_title}</string>"

        if text.count(marker) != 1:
            problems.append(f"{values}: {text.count(marker)} of the old title")

            continue

        text = text.replace(
            marker,
            f"<string name=\"settings_manager_title\">{new_title}</string>",
            1,
        )

        if values == "values":
            if text.count(INFO_LIVE_OLD) != 1:
                problems.append(f"{values}: {text.count(INFO_LIVE_OLD)} of the info sentence")

                continue

            text = text.replace(INFO_LIVE_OLD, INFO_LIVE_NEW, 1)

        # ⚠ The whole reason the ten translated sentences can be left alone. Asserted per
        # locale rather than assumed: check_translations.py requires the title to appear
        # verbatim inside the info sentence, and a locale that put IMD in the middle rather
        # than at an end would silently stop bolding.
        start = text.index("<string name=\"settings_manager_info_live\">")

        sentence = text[start:text.index("</string>", start)]

        if new_title not in sentence:
            problems.append(f"{values}: {new_title!r} is not inside settings_manager_info_live")

        staged[path] = text

    # --- the Kotlin -----------------------------------------------------------------------
    for name, edits in ((DIALOG, DIALOG_EDITS), (ROUTE, ROUTE_EDITS), (VIEW_MODEL, VIEW_MODEL_EDITS)):
        path = ROOT / name

        before = set(path.read_text(encoding="utf-8").splitlines()) if path.exists() else set()

        text = apply(path=path, edits=edits, problems=problems)

        if text is None:
            continue

        staged[path] = text

        # ⚠ Only lines this edit adds — handover_3 §4.
        for line in set(text.splitlines()) - before:
            if len(line) > 120:
                problems.append(f"{path.name}: {len(line)} chars — {line.strip()[:60]}")

    dialog = staged.get(ROOT / DIALOG, "")

    # Nothing may still name what has been removed, in this file or anywhere else.
    for gone in (
        "ManagerLogoButton",
        "LOGO_BUTTON_SIZE",
        "ic_imd_glyph_gear",
        "ic_imd_glyph_inner",
        "settings_manager_accessibility_note",
        "settings_manager_overlay_note",
    ):
        for kotlin in sorted(ROOT.rglob("*.kt")):
            if "build" in kotlin.relative_to(ROOT).parts:
                continue

            body = staged.get(kotlin) or kotlin.read_text(encoding="utf-8")

            if gone in body:
                problems.append(f"{kotlin.relative_to(ROOT)}: still names {gone}")

    # And the new pieces must all be present exactly once.
    for needle, expected in (
        ("private fun ActionButton(", 1),
        ("dimmed = !anythingHidden", 1),
        ("glyph = designR.drawable.ic_hide_glyph", 1),
        ("glyph = designR.drawable.ic_revert_glyph", 1),
        # Six already, one per dialog in this file that ends in an OK or Understood row,
        # plus the new Close row. Enumerated against the pristine tree, never estimated.
        ("Arrangement.End", 7),
        ("R.string.settings_manager_open_settings", 1),
    ):
        if dialog.count(needle) != expected:
            problems.append(f"dialog: {dialog.count(needle)} of {needle}, expected {expected}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    for path, text in staged.items():
        path.write_text(text, encoding="utf-8")

    for drawable in ("ic_imd_glyph_gear.xml", "ic_imd_glyph_inner.xml"):
        (ROOT / DESIGN_SYSTEM_DRAWABLES / drawable).unlink()

    print(f"ok — {len(staged)} files rewritten, 2 drawables deleted; title, logo click, "
          f"Unhide settings, watermarks, Close below")

    return 0


if __name__ == "__main__":
    sys.exit(main())
