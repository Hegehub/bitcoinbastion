#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASTION_API_BASE_URL:-http://localhost:8000}"
curl -fsS "${BASE_URL%/}/api/v1/storage/timescale/status"
