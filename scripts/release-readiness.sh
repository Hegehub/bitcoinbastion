#!/usr/bin/env bash
set -euo pipefail
make lint
python -m pytest -q
make docs-truthfulness
echo "release-readiness baseline checks complete"
