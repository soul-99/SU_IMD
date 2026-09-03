#!/usr/bin/env python3
"""r4e — `sheveryStartTracker.begin(...)` lands in the function that has a job to hand it.

The author's build of r4d:

    e: SettingsManagerViewModel.kt:501:19 Unresolved reference 'job'.

⚠ **A block appended to the wrong function, and the script that put it there could not tell.**
`_v3_shevery_wait_survives.py` anchored the `begin(...)` call on

    }
    }

    fun markInfoShown() {

meaning "the end of `setSheveryService`, which is the function immediately above
`markInfoShown`". That was true when the anchor was written and stopped being true in r4c, when
`hideSettings()` was inserted between them. The text still matched — once — so every assertion
passed, and the call was appended to the end of `hideSettings()`, where `job` and
`wirelessBefore` do not exist.

**The lesson, and it is a new one for the trap table: an anchor that names a function by what
follows it is not an anchor.** A shape like `}\\n    }\\n\\n    fun x() {` says "some function ends
here"; it does not say *which*. Where a script appends to the end of a named function it must
either match text unique to that function, or assert afterwards that the inserted text sits
between that function's own opening and the next declaration - which is what this script does,
and what the sibling `check_local_scope.py` change ships to catch generally.

Computes every edit in memory, asserts each match count, and writes nothing if any fails.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MANAGER_VM = ("feature/apps/src/main/kotlin/com/android/geto/feature/apps/manager/"
              "SettingsManagerViewModel.kt")

BEGIN = """
        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessBefore = wirelessBefore,
        )
"""

# Out of hideSettings, where it has no job to pass.
WRONG = """            settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
                settingsHiddenRunner.hide()
            }
        }
""" + BEGIN + """    }
"""

RIGHT = """            settingsWorkTracker.track(kind = SettingsWorkKind.Hiding) {
                settingsHiddenRunner.hide()
            }
        }
    }
"""

# ...and into setSheveryService, straight after the launch that produces it. The closing brace
# of that `appScope.launch` is identified by the two lines of its `finally`, which appear
# nowhere else in the file.
ANCHOR = """            } finally {
                sheveryStartTracker.clear()

                _targetStates.value = getManualTargetStatesUseCase()
            }
        }
    }
"""

PLACED = """            } finally {
                sheveryStartTracker.clear()

                _targetStates.value = getManualTargetStatesUseCase()
            }
        }

        // ⚠ **After the launch, because the job is what is being registered.** The countdown
        // starts at its first `delay`, so the tracker is published well before the first tick,
        // and a later dialog can cancel this start without ever having met the ViewModel that
        // began it.
        sheveryStartTracker.begin(
            job = job,
            seconds = SHEVERY_WAIT_SECONDS,
            wirelessBefore = wirelessBefore,
        )
    }
"""


def main() -> int:
    path = ROOT / MANAGER_VM

    if not path.exists():
        print("REFUSED, nothing written")
        print(f"  {MANAGER_VM}: missing")

        return 1

    text = path.read_text(encoding="utf-8")
    problems: list[str] = []

    for old, new, expected in ((WRONG, RIGHT, 1), (ANCHOR, PLACED, 1)):
        found = text.count(old)

        if found != expected:
            problems.append(
                f"expected {expected} of {old.strip().splitlines()[0][:58]!r}, found {found}",
            )

            continue

        text = text.replace(old, new, expected)

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    # ⚠ **Position, not presence.** The whole of this round's bug is that the r4d script
    # asserted the call existed and never asked where. The registration must sit inside
    # setSheveryService: after its `fun` line, and before the next top-level declaration.
    start = text.find("    private fun setSheveryService(enabled: Boolean) {")
    call = text.find("        sheveryStartTracker.begin(")
    after = text.find("\n    /**", start + 1)

    if start < 0 or call < 0 or after < 0:
        problems.append("cannot locate setSheveryService, the call, or the declaration after it")
    elif not start < call < after:
        problems.append(
            "the begin() call is not inside setSheveryService — "
            f"fun at {start}, call at {call}, next declaration at {after}",
        )

    if text.count("sheveryStartTracker.begin(") != 1:
        problems.append("the registration appears more than once")

    if text.count("            job = job,") != 1:
        problems.append("the job is passed more or less than once")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    before = set(path.read_text(encoding="utf-8").splitlines())

    for line in text.splitlines():
        if line not in before and len(line) > 120:
            problems.append(f"added line of {len(line)} chars: {line.strip()[:58]!r}")

    if problems:
        print("REFUSED, nothing written")

        for problem in problems:
            print(f"  {problem}")

        return 1

    path.write_text(text, encoding="utf-8")

    print(f"  wrote {MANAGER_VM}")
    print("ok - begin() sits in setSheveryService, where the job it registers is declared")

    return 0


if __name__ == "__main__":
    sys.exit(main())
