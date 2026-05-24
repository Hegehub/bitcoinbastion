#!/usr/bin/env bash
set -euo pipefail
kustomize build k8s/overlays/dev >/dev/null
kustomize build k8s/overlays/staging >/dev/null
kustomize build k8s/overlays/production >/dev/null
echo "kustomize overlays validated"
