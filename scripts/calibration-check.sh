#!/usr/bin/env bash
set -euo pipefail
required=(docs/CALIBRATION_FRAMEWORK.md docs/RC_STATUS_MATRIX.md docs/RELEASE_CANDIDATE_GATES.md)
for f in "${required[@]}"; do
  test -f "$f"
done
echo "calibration governance docs present"
