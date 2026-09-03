#!/usr/bin/env python3
"""check25 — the protobuf schema actually compiles.

## Why this exists

r4v added a field:

    IconStyleProto iconStyle = 72;

and did not add the `import` that brings `IconStyleProto` into scope. `protoc` refuses the file,
the datastore module generates nothing, and everything above it fails to build — which is what the
author saw, several modules away from the line that caused it.

**`check11_proto` passed.** It reads field names and numbers, which is the right job for it and
tells it nothing about whether a type resolves across files. Every other check in this toolkit is
a static approximation of a compiler; this one is the compiler, because `protoc` is one of the two
real ones the sandbox has.

## What it does

Runs `protoc` over every `.proto` in the repo, into a scratch directory, and reports its errors
verbatim. Nothing is written into the tree.

Skips with a clear message rather than passing if `protoc` is absent - a check that quietly does
nothing is worse than one that says it could not run.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import ROOT  # noqa: E402

GETO_ROOT = Path(ROOT)


def main() -> int:
    protoc = shutil.which("protoc")

    if protoc is None:
        print("SKIPPED: protoc is not installed; run toolkit/bootstrap.sh")
        return 0

    proto_roots = sorted(
        {p for p in GETO_ROOT.rglob("src/main/proto") if p.is_dir()},
    )

    if not proto_roots:
        print("no proto source roots found")
        return 0

    problems: list[str] = []

    checked = 0

    for root in proto_roots:
        files = sorted(root.rglob("*.proto"))

        if not files:
            continue

        checked += len(files)

        with tempfile.TemporaryDirectory() as out:
            result = subprocess.run(
                [
                    protoc,
                    f"--proto_path={root}",
                    f"--java_out={out}",
                    *[str(f) for f in files],
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                problems.extend(
                    line for line in (result.stderr + result.stdout).splitlines() if line.strip()
                )

    for line in problems:
        print(f"  {line}")

    print(f"checked {checked} .proto file(s) in {len(proto_roots)} source root(s); "
          f"{len(problems)} protoc error line(s)")

    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
