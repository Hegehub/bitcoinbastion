#!/usr/bin/env bash
set -euo pipefail
echo "Deployment smoke baseline (no real cluster actions)."
./scripts/validate-k8s.sh
