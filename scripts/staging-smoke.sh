#!/usr/bin/env bash
set -euo pipefail
if command -v kustomize >/dev/null 2>&1; then
  kustomize build k8s/overlays/staging >/dev/null
  echo "staging kustomize build ok"
else
  echo "kustomize not installed; staging smoke baseline skipped"
fi
