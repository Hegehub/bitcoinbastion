#!/usr/bin/env bash
set -euo pipefail
make lint
make access-release-gate
python -m pytest -q
make docs-truthfulness
echo "release-readiness baseline checks complete"
