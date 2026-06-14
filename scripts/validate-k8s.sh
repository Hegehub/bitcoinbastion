#!/usr/bin/env bash
set -euo pipefail
kustomize build deploy/kubernetes/overlays/dev >/dev/null
kustomize build deploy/kubernetes/overlays/staging >/dev/null
kustomize build deploy/kubernetes/overlays/production >/dev/null
echo "kustomize overlays validated"
