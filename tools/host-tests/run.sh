#!/usr/bin/env bash
# Compiles :domain:model (a plain JVM library with no dependencies) together with the
# host assertions and runs them. Needs kotlinc on PATH; nothing else.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT

kotlinc -nowarn -d "$OUT/tests.jar" \
  "$ROOT"/domain/model/src/main/kotlin/com/android/geto/domain/model/*.kt \
  "$ROOT"/tools/host-tests/DomainLogicTests.kt

kotlin -cp "$OUT/tests.jar" DomainLogicTestsKt
