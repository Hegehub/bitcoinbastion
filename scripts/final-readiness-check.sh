#!/usr/bin/env bash
set -euo pipefail
required=(
  docs/FINAL_READINESS_MATRIX.md
  docs/RC_FREEZE.md
  docs/PRODUCTION_TRANSITION_PACK.md
  docs/KNOWN_LIMITATIONS.md
  docs/SUPPORT_BOUNDARIES.md
  CHANGELOG.md
  RELEASE_NOTES.md
)
for f in "${required[@]}"; do test -f "$f"; done
make docs-truthfulness
echo "final readiness baseline checks complete"
