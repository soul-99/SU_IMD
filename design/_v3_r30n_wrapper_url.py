#!/usr/bin/env python3
"""
r30n — the wrapper's distributionUrl, which is why F-Droid's build never started.

The CI job died at the first Gradle step:

    > /usr/local/bin/gradlew-fdroid assembleRelease
    Update checksum from gradle-transparency-log
    No suitable gradle version found

⚠ **It is not a Gradle version problem, it is a URL problem.** `gradlew-fdroid` does not read the
version out of the file name. It matches `distributionUrl` **as a string** against F-Droid's Gradle
Transparency Log, and that log is keyed by `https://services.gradle.org/distributions/...` URLs and
nothing else. The wrapper pointed at `github.com/gradle/gradle-distributions`, which is a perfectly
real mirror and matches no key, so the lookup returned nothing and the build stopped before it
compiled a line.

The log was read in full to settle the one open question — 9.3.1 is present (the 9.x bin range runs
9.0.0 through 9.7.1), and its recorded sha256 is the checksum this file already carries:

    b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06

So the two zips really are byte-identical, F-Droid's own log says so, and **the checksum does not
change** — only the host does. No Gradle downgrade, no new checksum to trust.

⚠ **The comment above the line had to go with it.** It existed to explain why the GitHub mirror was
deliberate, and it is now the opposite of true. The replacement records the F-Droid constraint, and
keeps the timeout warning that made the mirror attractive in the first place — services.gradle.org
still times out from some networks, and changing this URL changes the hash Gradle names its wrapper
cache folder with, so the next local build re-downloads rather than reusing what is on disk.

The old ⚠ paragraph about the version appearing twice in the URL is deleted rather than reworded:
the new URL carries the version once, so the trap it warned about no longer exists.

Computes the edit in memory, asserts, writes nothing if any assertion fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

WRAPPER = ROOT / "gradle/wrapper/gradle-wrapper.properties"

# Verified against https://fdroid.gitlab.io/gradle-transparency-log/checksums.json — the key below
# is present in the log and carries exactly this sha256.
LOG_URL = "https://services.gradle.org/distributions/gradle-9.3.1-bin.zip"

LOG_SHA256 = "b266d5ff6b90eada6dc3b20cb090e3731302e553a27c5d3e4df1f0d76beaff06"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)

    return condition


def replace_once(text: str, old: str, new: str, label: str) -> str:
    found = text.count(old)

    if not check(found == 1, f"{label}: found {found}x, expected 1"):
        return text

    return text.replace(old, new, 1)


OLD_BLOCK = """# Pulled from Gradle's own GitHub mirror rather than services.gradle.org, which times out
# from some networks. gradle/gradle-distributions is the official distributions repo and
# this file is byte-identical to the services.gradle.org one — the checksum below is the
# published one from https://gradle.org/release-checksums/, and Gradle verifies it before
# unpacking, so a bad or truncated download fails loudly instead of half-installing.
#
# ⚠ The version appears TWICE in this URL — once as the release tag, once as the file
# name — and Android Studio's Gradle upgrade only rewrites the file name. Accepting its
# offer produces .../download/v9.3.1/gradle-9.5.0-bin.zip, which 404s. If you do want a
# newer Gradle, change the tag and the file name together and replace the checksum with
# that version's from https://gradle.org/release-checksums/. Otherwise decline the offer.
distributionUrl=https\\://github.com/gradle/gradle-distributions/releases/download/v9.3.1/gradle-9.3.1-bin.zip"""

NEW_BLOCK = """# Must be a services.gradle.org URL, not the gradle/gradle-distributions GitHub mirror.
# F-Droid's gradlew-fdroid matches this line against the Gradle Transparency Log
# (https://fdroid.gitlab.io/gradle-transparency-log/checksums.json), which is keyed by
# services.gradle.org URLs only; a GitHub URL fails the build with "No suitable gradle
# version found". The two zips are byte-identical — the checksum below is unchanged from
# when this pointed at GitHub, and matches the transparency log's entry for 9.3.1.
#
# services.gradle.org can time out from some networks. If the wrapper download stalls,
# fetch the zip from the GitHub mirror by hand and drop it into the wrapper dists folder;
# Gradle verifies the checksum below before unpacking either way.
#
# If you do want a newer Gradle, change the version here and replace the checksum with
# that version's from https://gradle.org/release-checksums/.
distributionUrl=https\\://services.gradle.org/distributions/gradle-9.3.1-bin.zip"""

source = WRAPPER.read_text(encoding="utf-8")

# The checksum is the thing that must NOT move. Asserted before and after.
check(
    f"distributionSha256Sum={LOG_SHA256}\n" in source,
    "the wrapper's checksum is not the one the transparency log records for 9.3.1",
)

source = replace_once(source, OLD_BLOCK, NEW_BLOCK, "the distributionUrl and its comment")

check(
    "distributionUrl=https\\://services.gradle.org/distributions/gradle-9.3.1-bin.zip\n" in source,
    "the services.gradle.org URL did not land",
)

check("github.com/gradle/gradle-distributions" not in source, "the GitHub mirror URL survived")

check(
    f"distributionSha256Sum={LOG_SHA256}\n" in source,
    "the checksum changed, and it must not — the distributions are byte-identical",
)

# ⚠ The escape is load-bearing. .properties treats a bare ':' after a key as a separator, so the
# URL's own colon is written '\\:' in the file. Dropping it silently truncates the URL.
check(source.count("https\\://") == 1, "the ':' escape in distributionUrl is missing or doubled")

check(
    source.count("distributionUrl=") == 1 and source.count("distributionSha256Sum=") == 1,
    "distributionUrl / distributionSha256Sum are no longer exactly one line each",
)

if failures:
    print("NOTHING WRITTEN — assertions failed:")

    for failure in failures:
        print(f"  - {failure}")

    sys.exit(1)

with WRAPPER.open("w", encoding="utf-8", newline="\n") as handle:
    handle.write(source)

print("distributionUrl        github.com/gradle/gradle-distributions  ->  services.gradle.org")

print(f"distributionSha256Sum  {LOG_SHA256}  (unchanged)")

print("ok")
