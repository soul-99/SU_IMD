# Location - screenshots

Three pictures of the Location row, taken on a Xiaomi 24129PN74C (Android 17, 1200×2670, dark
scheme) from the running app rather than mocked up.

| File | What it shows |
| --- | --- |
| `01-favourites.png` | The Favourites tab - where a launch starts, and the screen the row exists for. Tapping **Meezan Bank** here is what switches location on. |
| `02-manager-location-toggle.png` | The settings manager card with **Location** as its last row, switched on, with the arrow out to Android's own location screen. |
| `03-settings-to-hide-location.png` | **Settings → Settings to hide / unhide**, scrolled to the Location row: ticked, with the note that says what it does - *"Location is switched on while an app is open, and put back to how it was when you revert"*. |

The row is the only one in that list which is ticked to switch something **on**. Everything else
there is a setting IMD hides on the way into an app; location is what those apps ask for.

## What the device log showed, for the record

```
write   SECURE.location_mode = 3 -> ok                 # launch, through IMD
unhide  session ended apps=1 mode=deviceWide reasons=Swiped
write   SECURE.location_mode = 0 -> ok                 # closing the app
revert  device-wide -> RevertToDefaultResult(changed=[AccessibilityServices, Location], failed=[], …)
```
