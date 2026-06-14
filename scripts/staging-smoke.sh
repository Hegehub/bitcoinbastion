#!/usr/bin/env bash
set -euo pipefail
if command -v kustomize >/dev/null 2>&1; then
  kustomize build deploy/kubernetes/overlays/staging >/dev/null
  echo "staging kustomize build ok"
else
  echo "kustomize not installed; staging smoke baseline skipped"
fi
