# `:baselineprofile`

Generates the baseline profile that `:app` ships. Added in r29.

## What it is for

A baseline profile is a list of classes and methods, shipped inside the APK, that ART compiles
ahead of time at install rather than interpreting on first run. On a Compose app the measured
effect is on **cold start and the first scroll of a list** — the two moments this app is slowest,
because that is when the whole Compose runtime is being touched for the first time.

## Running it

Needs a connected device or emulator. It is not part of `assemble` and never runs in CI here.

```
gradlew :app:generateReleaseBaselineProfile
```

That installs the app and this module's own APK, drives the startup path several times, and writes

```
app/src/release/generated/baselineProfiles/baseline-prof.txt
```

**Commit that file.** It is the thing that ships; this module only produces it.

## If it produces nothing

* The device must be rooted or a `userdebug` build for Macrobenchmark to read the profile back. A
  Google APIs emulator image (not Play Store) is the easiest way to get one.
* `minSdk` here is 28 because Macrobenchmark cannot drive anything older. The profile it writes
  still installs back to the app's own `minSdk` of 24 through `profileinstaller`.

## When to regenerate

When the startup path changes — a new first screen, a different splash, a change to what
`MainActivity` reads before its first frame. Not every round.
