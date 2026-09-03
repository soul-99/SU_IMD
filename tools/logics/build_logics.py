#!/usr/bin/env python3
"""Render the IMD logic flowcharts to PNGs for SUIMD.md.

One mermaid source per logic, rendered through mermaid-cli with the app's own dark
Material 3 palette so the diagrams read as part of the project rather than as
generic clip art. Ordered the way SUIMD.md lists them: the paths every user hits
first, then the ones behind a setting.

⚠ **Rewritten wholesale in r30, after a line-by-line audit against the code.** Every one of the
fourteen had drifted, several of them badly:

* **Shevery was in none of them.** The second Shizuku fork appears in 32 Kotlin files and changed
  four paths without a single picture following it - its start is not an intent at all, it is IMD
  raising the debugging transports and waiting for the fork's own watchdog.
* **Auto unhide settings had no diagram**, so a whole feature was undocumented. It is number 15.
* Diagram 5 described a confirmation poll that v3 deleted, and a fallback notification whose
  notifier is `@Deprecated` with no consumer anywhere in the app.
* Diagram 9 described a card that no longer exists: rows are user-configurable, ordered by fork,
  and the Shizuku row is hidden rather than greyed when the fork is unconfigured.
* Several named the "IMD services manager", which the app calls the **Settings manager**, and the
  "Memory notification function", which v3 split into a hiding and an unhiding framework.

The rule that produced all of that is worth writing down: **a diagram is only current if something
forces it to be.** Regenerate these whenever a logic changes, and re-read them against the code at
each release - `tools/logics/README.md` says how.
"""
import json
import pathlib
import subprocess

HERE = pathlib.Path(__file__).parent
OUT = HERE.parent.parent / "docs" / "logics"
OUT.mkdir(parents=True, exist_ok=True)

# app's Material 3 dark scheme (design-system/.../theme/Theme.kt)
SURFACE = "#12140E"
PRIMARY = "#B1D18A"
ON_SURF = "#E2E3D8"
OUTLINE = "#44483D"
CARD = "#1E2118"
STOP = "#FFB4AB"

CONFIG = {
    "theme": "base",
    "themeVariables": {
        "background": SURFACE,
        "primaryColor": CARD,
        "primaryTextColor": ON_SURF,
        "primaryBorderColor": OUTLINE,
        "lineColor": PRIMARY,
        "secondaryColor": CARD,
        "tertiaryColor": CARD,
        "fontFamily": "Roboto, Helvetica Neue, Arial, sans-serif",
        "fontSize": "16px",
    },
    "flowchart": {"curve": "basis", "nodeSpacing": 45, "rankSpacing": 50, "padding": 12},
}

# Two accents beyond the default card: the red terminal that has always meant "this run stops
# here", and a green one added in r30 for the branches that exist only on the Shevery fork - so
# the second fork can be picked out at a glance in the five diagrams where it changes the answer.
CLASSES = """
    classDef stop fill:#2A1B18,stroke:#FFB4AB,color:#FFB4AB
    classDef fork fill:#1B2415,stroke:#B1D18A,color:#CFE9A8
"""

DIAGRAMS: list[tuple[str, str, str]] = []


def add(slug: str, title: str, src: str) -> None:
    DIAGRAMS.append((slug, title, src.strip() + "\n" + CLASSES.rstrip()))


# ── 1. the main path ────────────────────────────────────────────────────────
add("01-launch-hide", "Launching an app (Settings to hide)", """
flowchart TD
    A["User taps an app in IMD, its homescreen<br/>shortcut, the <b>Hide settings</b> tile,<br/>or an IMD intent"] --> B{"<b>Hiding framework</b>"}
    B -- "Default IMD settings<br/>(the default)" --> C["Read the device-wide<br/><b>Settings to hide</b>"]
    B -- "Per app configuration" --> M["That app's own profile<br/>(logic 3)"]

    C --> N{"Anything left to do?"}
    N -- "Nothing ticked" --> Y1["<b>Stop.</b> Say what to configure.<br/>The app is not opened"]
    N -- "IMD+ already holds<br/>the device" --> Y2["Open the app.<br/>Nothing to do"]
    N -- "A previous hide was<br/>never undone" --> Y3["<b>Stop.</b> Offer to restore<br/>that first"]
    N -- "WRITE_SECURE_SETTINGS<br/>has gone" --> Y4["<b>Stop.</b> Say the grant<br/>was lost"]
    N -- Yes --> V{"<b>Unhiding framework</b><br/>is Memory?"}

    V -- Yes --> W["Measure what every ticked target holds<br/><b>now</b> and record it, before<br/>anything moves"]
    V -- No --> D
    W --> D{"Hide <b>Display over<br/>other apps</b>?"}

    D -- "Not ticked, already withdrawn,<br/>or the fork is <b>Shevery</b>" --> H
    D -- Yes --> E{"Shizuku running?"}
    E -- No --> F["Start Shizuku (logic 8)"]
    E -- Yes --> G["Withdraw overlay access<br/>from the selected apps"]
    F --> G
    F -- "Would not start" --> X1["<b>Stop.</b> Nothing was touched"]
    G -- "The write was refused" --> X2["<b>Stop.</b> The Shizuku start is<br/><b>not</b> rolled back"]

    G --> H["Write the remaining targets in<br/><b>HideOrder</b> - the reverse of the<br/>order a revert puts them back"]
    H --> I["Stop Shizuku last (logic 5), told<br/>which transports to leave up"]
    I --> J{"A write refused, and<br/>the grant gone?"}
    J -- Yes --> K["<b>Undo everything this run did</b>, in<br/>reverse, then report the loss"]
    J -- No --> L["Mark the device hidden - even if<br/>only some of it moved"]
    L --> P["Open the app, and post the one ongoing<br/>notification: <i>Settings hidden,<br/>click to unhide settings</i>"]

    class Y1 stop
    class Y3 stop
    class Y4 stop
    class X1 stop
    class X2 stop
    class K stop
""")

# ── 2. the way back ─────────────────────────────────────────────────────────
add("02-revert-default", "Revert to default", """
flowchart TD
    A["<b>Revert to default</b>, the named function:<br/>its Quick Settings tile · a homescreen shortcut ·<br/>the Settings manager's button · an IMD intent"] --> B["Clear any IMD+ hold, sweep every per-app<br/>memory record, and drop the auto-unhide<br/>and auto-revert watches"]
    B --> C["<b>Restore the extras first</b> - settings a<br/>profile changed that the six targets<br/>cannot reach"]
    C --> D["Read <b>Settings to unhide on Revert</b>"]

    D --> E{"Does overlay access<br/>need a write?"}
    E -- "No, or the fork<br/>is <b>Shevery</b>" --> H
    E -- "Yes, to give it back" --> F["Start Shizuku if needed (logic 8),<br/>then write the AppOp"]
    E -- "Yes, to withdraw it -<br/>the configuration says off" --> F
    F --> G{"Did the write land?"}
    G -- No --> G1["Record the debt and post<br/><b>Unhide settings failure</b>,<br/>with a <i>Try again</i> button"]
    G -- Yes --> H

    H["Write the ordinary targets in order"] --> I{"Shizuku available -<br/>configured <b>and</b> installed?"}
    I -- "No, or this fork<br/>has no intents" --> L
    I -- Yes --> J["Start or stop it to match what<br/>the configuration asks. A start<br/>that fails is not retried here"]
    J --> K["If it was started, re-settle wireless<br/>debugging - a fork takes it<br/>down on its way up"]
    K --> L["Clear the hidden mark"]
    L --> M["Release the held accessibility services,<br/>and bring <b>IMD's own IMD+ detector</b><br/>back last"]

    class G1 stop
""")

# ── 3. the per-app profile ──────────────────────────────────────────────────
add("03-memory-apply", "Per app configuration - applying a profile", """
flowchart TD
    A["An app is launched while the<br/><b>Hiding framework</b> is<br/><b>Per app configuration</b>"] --> B{"Is there a profile,<br/>and is anything on?"}
    B -- "No profile at all" --> Z1["<b>Stop.</b> Say so. The app<br/>is <b>not</b> opened"]
    B -- "A profile, every row off" --> Z2["Open the app.<br/>Nothing is changed"]
    B -- "IMD+ is running" --> Z3["Open it, or refuse -<br/>depending on whose hold it is"]
    B -- "A previous hide stands,<br/>or the grant has gone" --> Z4["<b>Stop.</b> Offer to restore,<br/>or report the loss"]
    B -- Yes --> C{"Does this profile hide<br/><b>Display over other apps</b>,<br/>and may it?"}

    C -- "No; or not <b>Thedjchi</b>;<br/>or Manage Shizuku<br/>is incomplete" --> E
    C -- Yes --> D["Start Shizuku if needed, withdraw<br/>overlay access, and note <b>this app</b><br/>as the one that did it"]
    D --> E["<b>Record what each setting holds now</b> -<br/>but only where this app is the first to<br/>move it away from that value"]

    E --> F["Write the profile's settings"]
    F --> G{"Does it hide<br/>accessibility services?"}
    G -- Yes --> H["Switch off the services IMD manages,<br/>and claim them against this app"]
    G -- No --> I
    H --> I{"Does it stop Shizuku?"}
    I -- Yes --> J["Stop it (logic 5), and note that<br/>this app took it down"]
    I -- No --> K
    J --> K["Switch off <b>IMD's own IMD+ detector</b>"]
    K --> L["Open the app, and post the one<br/>shared ongoing notification"]

    class Z1 stop
    class Z4 stop
""")

# ── 4. the per-app way back ─────────────────────────────────────────────────
add("04-memory-revert", "Per app configuration - reverting a profile", """
flowchart TD
    A["Auto revert on returning · the auto-unhide<br/>watcher · IMD+'s own revert · the button on<br/>the app's configuration screen"] --> B{"Is there anything<br/>to work from?"}
    B -- "No profile, or<br/>every row off" --> Z["Nothing to do"]
    B -- Yes --> C{"Did <b>this app</b> withdraw<br/>overlay access?"}

    C -- "No - another app holds it,<br/>or it was already withdrawn" --> E
    C -- Yes --> D["Give overlay access back"]
    D --> E["Write each setting back to what was recorded -<br/>or, where nothing was recorded, to the value<br/>the profile names for a revert.<br/><i>Wireless debugging is left down if switching it<br/>on is what this would do and</i> Restore wireless<br/>debugging <i>is off</i>"]

    E --> F{"Did every write land?"}

    F -- No --> Y["<b>Stop.</b> Keep the record<br/>so a retry can use it"]
    F -- Yes --> G["<b>Drop the record</b> - before anything<br/>else, so a second revert cannot<br/>apply it twice"]
    G --> H{"Does the profile restore<br/>accessibility services?"}
    H -- Yes --> I["Release only the services<br/>this app is holding"]
    H -- No --> J
    I --> J["Restart Shizuku if this app stopped it -<br/>unconditionally since v3, after a<br/>1.5s wait for the daemon"]
    J --> K{"Is anything still hidden -<br/>device-wide <b>or</b> by<br/>another profile?"}
    K -- Yes --> L["Leave IMD's own detector off"]
    K -- No --> M["Bring the detector back"]

    class Z stop
    class Y stop
""")

# ── 5. stopping Shizuku ─────────────────────────────────────────────────────
add("05-stop-shizuku", "Stopping the Shizuku service", """
flowchart TD
    A["A hide asks for the Shizuku<br/>service to stop"] --> B{"Which fork?"}
    B -- "<b>Shevery</b> - it has<br/>no intents" --> S["<b>Nothing is sent.</b> Reported as<br/><i>not configured</i>, never<br/>as a failure"]
    B -- "Not configured" --> Z["Nothing to send. Skipped,<br/>never a failure"]
    B -- "<b>Thedjchi</b>" --> C{"Service running?"}

    C -- No --> Y["Already stopped"]
    C -- Yes --> D["Broadcast the fork's own<br/><b>stop intent</b>"]
    D --> E["Switch <b>USB debugging</b> off, then<br/><b>wireless debugging</b> off - always,<br/>not as a fallback: the service cannot<br/>outlive the transport it rides on"]
    E --> F["Wait 300ms for the<br/>transports to settle"]
    F --> G["Put back only the transports the<br/><b>caller</b> asked to leave up. It knows<br/>what was on before, and what<br/>this run is hiding"]
    G --> H["<b>Stopped.</b> There is no confirmation<br/>poll - v3 removed it"]

    class S fork
""")

# ── 6. display over other apps ──────────────────────────────────────────────
add("06-overlay", "Display over other apps", """
flowchart TD
    A["A hide or a revert reaches<br/>the overlay step"] --> B{"May IMD manage it?"}
    B -- "The fork is not<br/><b>Thedjchi</b>" --> Z1["Skipped. <b>Shevery cannot do<br/>this on a launch</b>"]
    B -- "Manage Shizuku incomplete,<br/>or no apps selected" --> Z2["Skipped"]
    B -- Yes --> C{"Already withdrawn from<br/>every selected app?"}

    C -- Yes --> Z3["Skipped - and the Shizuku<br/>start is skipped with it"]
    C -- No --> D{"Shizuku running?"}
    D -- No --> E["Start it (logic 8)"]
    D -- Yes --> F
    E -- "Would not start" --> X1["<b>Stop.</b> Nothing touched"]
    E --> F["Ask Shizuku which apps currently<br/>hold the permission"]
    F -- "No answer" --> X2["<b>Stop</b>"]

    F --> G["<b>Record the debt first</b>, extending what<br/>is already owed rather than replacing it -<br/>a write that dies halfway must<br/>still be repayable"]
    G --> H["Withdraw the AppOp"]
    H -- Refused --> X3["<b>Stop.</b> The Shizuku start is<br/><b>not</b> rolled back"]
    H --> I["On the way back, give it to the apps<br/>recorded - minus any another holder<br/>still owns, and any whose install<br/>identity has changed"]
    I -- "Restore refused" --> J["Post <b>Unhide settings failure</b> with<br/><i>Try again</i>. The debt survives a<br/>reboot and is retried"]

    N["In the <b>Settings manager</b> only, <b>Shevery</b><br/>may drive this too - while its service<br/>is actually running"] -.-> B

    class Z1 stop
    class X1 stop
    class X2 stop
    class X3 stop
    class J stop
    class N fork
""")

# ── 7. accessibility services ───────────────────────────────────────────────
add("07-accessibility", "Accessibility services", """
flowchart TD
    A["A hide reaches the<br/>accessibility step"] --> B["Only the services selected in<br/><b>Accessibility services managed by IMD</b><br/>are ever touched"]
    B --> C["Claim every selected service that is on<br/><b>or</b> already held by another profile - so<br/>that profile's revert cannot bring<br/>one back mid-hide"]
    C --> G["Record the claim <b>before</b> switching anything off,<br/>and roll it back if the write fails.<br/>A device-wide hide records under one fixed key;<br/>a per-app one records against that app"]
    G --> H["Switch the claimed services off"]

    H --> I{"On the way back -<br/>which revert?"}
    I -- "Revert to default, or the<br/>Settings manager's switch" --> J["<b>Release everything.</b> Every holder is<br/>flattened, deliberately: scoping this<br/>is what caused the reported bug"]
    I -- "A per-app revert" --> K["Release only this app's claim, and<br/>leave a service another app<br/>still holds switched off"]

    J --> L{"Switched from the<br/><b>Settings manager</b>?"}
    L -- "Turned off" --> M["Also switch <b>IMD's own IMD+<br/>detector</b> off - always"]
    L -- "Turned on" --> N["Also bring the detector back,<br/>unless something is still hidden"]
    K --> O["The detector is left alone<br/>on this path"]

    class M stop
""")

# ── 8. starting Shizuku ─────────────────────────────────────────────────────
add("08-shizuku-start", "Starting the Shizuku service", """
flowchart TD
    A["Something needs Shizuku running"] --> B{"Configured, and the<br/>app installed?"}
    B -- No --> Z["Fail immediately.<br/>Do not burn the wait"]
    B -- Yes --> C{"Which fork?"}

    C -- "<b>Thedjchi</b>" --> D["Broadcast the fork's <b>start intent</b><br/>- with the auth key, if it needs one"]
    D --> E["Poll every 0.5s, resend the broadcast<br/>every 2s, for up to <b>8 seconds</b>"]
    E --> F{"Running?"}
    F -- Yes --> G["Started. The fork brings the<br/>debugging transport up with it"]
    F -- "8s elapsed" --> H["Give up, and <b>record the failure</b> so<br/>the Settings manager can<br/>show it later"]

    C -- "<b>Shevery</b>" --> P["<b>No intent, and no auth key.</b> Switch<br/><b>USB</b> and <b>wireless debugging</b> on -<br/>but only the ones that were off"]
    P --> Q["Wait for <b>ErrorProtect</b>, Shevery's own<br/>watchdog, to notice and start the<br/>service. It scans every 10s"]
    Q --> R["Poll every 0.5s for up to<br/><b>40 seconds</b>"]
    R --> S{"Running?"}
    S -- Yes --> T["Started. <b>IMD</b> brought the transport up,<br/>and the fork followed"]
    S -- "40s elapsed" --> U["Put back <b>exactly</b> the transports this<br/>attempt switched on, then record<br/>the failure"]
    U --> V["From the Settings manager, also post<br/><b>Failed to start Shevery</b>. The countdown<br/>outlives the dialog that started it"]

    class H stop
    class U stop
    class V stop
    class P fork
    class Q fork
    class R fork
    class S fork
    class T fork
""")

# ── 9. the settings manager ─────────────────────────────────────────────────
add("09-services-manager", "The Settings manager", """
flowchart TD
    A["Its own launcher icon · a Quick Settings tile ·<br/>a homescreen shortcut · the Favourites tab ·<br/>an IMD intent - <b>all without IMD open</b>"] --> B["Read every row's <b>live</b> state, and<br/>re-read it twice a second"]
    B --> C["Draw only the rows ticked in <b>Setting manager<br/>toggles</b>, in an order that<br/>depends on the fork"]

    C --> D{"Row pressed"}
    D -- "Developer settings ·<br/>USB · Wireless debugging" --> E["Write it directly. Locked while a<br/>fork start or an overlay write<br/>is in flight"]
    D -- "Accessibility services" --> F["Act only on the selection -<br/><i>only selected ones</i>"]
    D -- "Display over other apps" --> G["Start Shizuku if needed, write the<br/>AppOp, then put back the rows<br/>the start disturbed"]

    D -- "Shizuku, on <b>Thedjchi</b>" --> H["Start or stop it. The spinner turns in<br/>the switch thumb, with an <b>8s</b><br/>countdown under the row"]
    D -- "Shizuku, on <b>Shevery</b>" --> I["Renamed <b>Shevery service</b>. Turning it on<br/>raises the debugging transports and<br/>waits <b>40s</b> for ErrorProtect"]
    I --> J["During the wait the row looks locked but<br/>stays pressable - <b>a press cancels</b>. USB<br/>and the row itself are held;<br/>wireless stays free"]
    I -- "Turned off" --> K["Stops the service <b>and</b> both<br/>debugging transports"]

    C -- "Shizuku not configured" --> L["The Shizuku row and the overlay row are<br/><b>removed from the card</b>, not greyed"]

    E --> M["<b>All off</b> / <b>All on</b> pill, above the first<br/>switch. It moves only the rows it judged<br/>operable, in dependency order, and skips<br/>wireless unless the user restores it"]
    F --> M
    G --> M
    H --> M
    J --> M
    M --> N["Rows that were off when a bulk button<br/>was pressed <b>tick</b> as they come on"]
    N --> O["Footer: <b>Hide settings</b> or <b>Unhide settings</b>,<br/>whichever the device is - and <b>Revert to<br/>default</b>, which long-presses into<br/>its own configuration"]

    class I fork
    class J fork
    class K fork
""")

# ── 10. auto revert ─────────────────────────────────────────────────────────
add("10-auto-revert", "Auto revert on returning", """
flowchart TD
    A["An app is launched <b>from inside IMD</b>,<br/>and something is actually applied"] --> B["Arm the watch"]
    B --> C["IMD goes away - marked when it stops, so<br/>a dialog or the notification shade<br/>does not count"]
    C --> D["IMD comes back to the foreground"]
    D --> E{"Is <b>Auto revert on<br/>returning</b> on?"}
    E -- No --> F["<b>Clear the armed marker</b> and stop. The<br/>launch is discarded, not<br/>merely skipped"]
    E -- Yes --> G{"<b>Unhiding framework</b>?"}
    G -- Memory --> H["Revert only the launched app's profile<br/>(logic 4), cancel its notification, and<br/>clear the revert offer if<br/>nothing is left"]
    G -- "Default IMD settings" --> I["Revert to default (logic 2)"]
    H -- "Overlay could not<br/>be restored" --> J["Report that instead<br/>of the toast"]

    class F stop
    class J stop
""")

# ── 11. IMD intents ─────────────────────────────────────────────────────────
add("11-tasker", "IMD intents (Tasker / MacroDroid)", """
flowchart TD
    A["An automation app wants<br/>to drive IMD"] --> B{"Which kind?"}

    B -- "<b>Open the Settings manager</b>" --> C["Not a broadcast, and <b>no auth key</b>. It<br/>launches an exported activity - a screen<br/>you then toggle by hand, so the<br/>integration switch cannot refuse it"]

    B -- "A broadcast" --> D{"Is <b>IMD intents</b><br/>switched on?"}
    D -- No --> Z["Refused, <b>silently</b>"]
    D -- Yes --> E{"Auth key correct?"}
    E -- No --> Z
    E -- Yes --> F{"Which action?"}

    F -- "Hide settings" --> G["Hide the configured settings (logic 1),<br/>suppressing the previous-hide prompt.<br/>Reports by toast and notification only"]
    F -- "Unhide settings" --> H["Flush the outstanding reverts -<br/>and only those"]
    F -- "Toggle settings" --> I["Exactly what the <b>Hide settings</b><br/>tile press does (logic 13)"]
    F -- "Revert to default" --> J["Run the named function (logic 2)"]
    F -- "Revert using memory" --> K["Still honoured for macros written before<br/>v3, but <b>no longer offered</b><br/>in the picker"]

    class Z stop
""")

# ── 12. the settings observer ───────────────────────────────────────────────
add("12-observer", "The settings observer", """
flowchart TD
    A["<b>Settings Observer Service</b> switched<br/>on under Advanced"] --> B["Watch <b>System</b>, <b>Secure</b> and <b>Global</b> for<br/>as long as the service runs - no app<br/>has to be open"]
    B --> C{"Who changed it?"}
    C -- "<b>IMD itself</b>" --> D["Ignored. The log is for what<br/><i>something else</i> moved"]
    C -- "Anything else" --> E["Record the table, the key, and the<br/>value before and after"]
    E --> F["Rewrite the ongoing notification<br/>with the table and key"]
    F --> G["Advanced → <b>View log</b>, or <b>Clear log</b>"]
    G --> H["Kept <b>in memory only</b>, capped at 300<br/>entries, and gone when the service<br/>stops. It is a live window,<br/>not a history"]
    H --> I["The four fields it records are exactly the<br/>four the <i>Add setting</i> form asks for,<br/>so a row can be copied across"]

    class D stop
""")

# ── 13. the hide settings tile ──────────────────────────────────────────────
add("13-hide-tile", "The Hide settings tile", """
flowchart TD
    A["The <b>Hide settings</b> Quick Settings<br/>tile is pressed"] --> B{"Already working?"}
    B -- Yes --> Z["Ignored. The tile reads <i>Hiding<br/>settings…</i> and cannot be pressed"]
    B -- No --> C["Run on the app's own scope - <b>the shade<br/>stays open</b>. Re-read which<br/>direction to go"]

    C --> D{"Is anything<br/>hidden now?"}

    D -- "No, so hide" --> E{"Outcome"}
    E -- Hidden --> F["Toast, and the one ongoing <b>Settings<br/>hidden</b> notification. The shade<br/>collapses a second later"]
    E -- "Nothing ticked" --> G["Collapse the shade, and say<br/>what to configure"]
    E -- "The overlay write failed" --> H["<b>Leave the shade open</b> and post a<br/>high-priority notification into it.<br/>Tapping opens the <b>Settings manager</b>"]
    E -- "The grant has gone" --> I["Collapse, and say so"]
    E -- "IMD+ holds it, or a<br/>prior hide stands" --> J["Nothing, silently"]

    D -- "Yes, so unhide" --> K{"Who is holding it?"}
    K -- "<b>IMD+</b>" --> L["Hand the whole press to IMD+'s own<br/>revert - this is checked first"]
    K -- "Per-app profiles" --> M["Cancel the notifications, then<br/>sweep every record (logic 4)"]
    K -- "Device-wide" --> N["Revert, following the <b>unhiding<br/>framework</b> - so under Memory it restores<br/>what the hide measured"]
    K -- "Nothing recorded" --> O["Fall back to <b>Revert to default</b> anyway,<br/>so a press is never a no-op"]

    P["On <b>Shevery</b> the Shizuku row is dropped from<br/>Settings to hide - so a list whose only<br/>tick is Shizuku hides nothing"] -.-> E

    class Z stop
    class G stop
    class H stop
    class I stop
    class P fork
""")

# ── 14. auto-hide settings (IMD+) ───────────────────────────────────────────
add("14-auto-hide", "Auto hide settings (IMD+)", """
flowchart TD
    A["A watched app comes<br/>to the foreground"] --> B{"Refuse before any<br/>window is opened?"}
    B -- "Not a watched app" --> Z1["Nothing"]
    B -- "Nothing configured for it, and<br/>the 30-minute reminder<br/>is not due" --> Z2["Nothing"]
    B -- "A recent run failed - backing<br/>off 60s, then 5min,<br/>then 30min" --> Z3["Nothing"]
    B -- "Already running, or<br/>something is hidden" --> Z4["Nothing"]
    B -- No --> C["Open IMD's own transparent window - a<br/>background start could not launch<br/>an app again afterwards"]

    C --> D{"Was a previous hide<br/>never undone?"}
    D -- Yes --> E["Ask: <b>Restore</b> it first, or <b>Ignore</b><br/>and throw the record away"]
    D -- No --> F
    E --> F["Re-read the settings. If anything<br/>changed in the meantime, stop"]

    F --> G{"Is there anything to<br/>hide for this app?"}
    G -- "No profile, or nothing ticked" --> Y["Say so, and stamp the<br/>30-minute timer"]
    G -- Yes --> H["Toast: <b>IMD+: Hiding settings…</b>"]

    H --> I{"Close the app first?"}
    I -- "Yes, the default" --> J["Start Shizuku if needed,<br/>then force-stop the app"]
    I -- "No - <i>Do not kill app<br/>on first launch</i>" --> L
    J -- "Shizuku would not start,<br/>or permission was refused" --> X["<b>Abandon the run.</b> The app was never<br/>stopped. Record the failure<br/>and post a notification"]
    J --> L["<b>Arm the auto-unhide watch first</b>,<br/>then hide"]

    L --> M{"Hiding framework?"}
    M -- "Default IMD settings" --> N["Hide the device-wide list (logic 1),<br/>and mark IMD+ running"]
    M -- "Per app configuration" --> O["Apply <b>that app's</b> profile (logic 3).<br/>The per-app hold is the record -<br/>nothing global is marked"]
    N -- "Hid nothing" --> P["Give the watch back, record a<br/>failure, reopen the app"]
    O -- "Hid nothing" --> P

    N --> Q["Switch <b>IMD's own detector</b> off - before<br/>anything is launched, so IMD+ cannot<br/>detect its own relaunch"]
    O --> Q
    Q --> R["Reopen the app, toast, and post the<br/><b>IMD+</b> notification. Swiping<br/>it away reposts it"]
    R --> S["Ended by: tapping it · the <b>Hide settings</b><br/>tile · or the auto-unhide watcher.<br/><b>No app is closed</b> on the way back"]

    class Z1 stop
    class Z2 stop
    class Z3 stop
    class Z4 stop
    class Y stop
    class X stop
    class P stop
""")

# ── 15. auto unhide settings ────────────────────────────────────────────────
add("15-auto-unhide", "Auto unhide settings", """
flowchart TD
    A["A hide leaves the device hidden"] --> B["The watcher service runs for as long as<br/><b>Auto unhide</b> is on and something is<br/>hidden - read from stored state, so it<br/>survives the process being killed"]
    A --> C{"Did the hide<br/>name an app?"}
    C -- "A launch from IMD, a<br/>shortcut, or IMD+" --> D["Add a watch entry: the package, and the<br/>component <b>only</b> under the<br/>memory framework"]
    C -- "The <b>Hide settings</b> tile" --> E["<b>No entry.</b> A tile hide names nothing, so<br/>only the screen-lock trigger<br/>can ever end it"]

    B --> F["Tick every 5s with the screen on,<br/>every 30s with it off"]
    F --> G{"Still armed, and still<br/>something hidden?"}
    G -- No --> S1["Clear the watch, and<br/><b>stop the service</b>"]
    G -- Yes --> H{"Are there entries?"}

    H -- Yes --> I["An <b>app-launch</b> session -<br/>gate on that checkbox"]
    H -- No --> J["A <b>tile</b> session -<br/>gate on that checkbox"]
    I --> K{"Is that checkbox ticked?"}
    J --> K
    K -- No --> S2["Stop watching, but <b>keep the<br/>entries</b>. They are still true"]
    K -- Yes --> L{"Is a hide or revert<br/>running right now?"}
    L -- Yes --> W

    L -- No --> M{"<b>Screen lock</b> - screen off<br/>longer than the timer?"}
    M -- Yes --> R2["<b>Revert everything.</b> The failsafe<br/>that can end any session"]
    M -- No --> N{"For each watched app"}

    N -- "<b>Swiped</b> away from recents -<br/>needs Android 11 and DUMP" --> O["That session has ended"]
    N -- "<b>Idle</b> longer than the timer,<br/>measured from last use - or from<br/>the hide, if usage access<br/>is missing" --> O
    N -- Neither --> W

    O --> P{"Does the entry name<br/>a component?"}
    P -- Yes --> R1["Revert that one profile (logic 4)<br/>and forget the entry"]
    P -- "No, it is device-wide" --> Q{"Have <b>all</b> the device-wide<br/>entries ended?"}
    Q -- No --> W
    Q -- Yes --> R2

    R1 --> W
    R2 --> T["Withdraw the notification the moment<br/>unhiding <b>starts</b>, then flush the<br/>reverts and clear every watch"]
    T --> S1

    W["<b>Keep watching.</b> Nothing has ended yet -<br/>wait for the next tick"]

    class S1 stop
    class S2 stop
    class E stop
""")


def main() -> None:
    (HERE / "config.json").write_text(json.dumps(CONFIG, indent=1))
    (HERE / "puppeteer.json").write_text(json.dumps({
        "executablePath": "/opt/pw-browsers/chromium",
        "args": ["--no-sandbox", "--disable-dev-shm-usage"],
    }))

    for slug, title, src in DIAGRAMS:
        mmd = HERE / f"{slug}.mmd"
        mmd.write_text(src + "\n")
        png = OUT / f"{slug}.png"
        subprocess.run([
            "mmdc", "-i", str(mmd), "-o", str(png),
            "-c", str(HERE / "config.json"),
            "-p", str(HERE / "puppeteer.json"),
            "-b", SURFACE, "-s", "2", "-q",
        ], check=True)
        print(f"{png.name:28s} {title}")


if __name__ == "__main__":
    main()
