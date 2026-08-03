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
  docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md
  docs/LNURL_AUTH_DOMAIN_POLICY.md
)
for f in "${required[@]}"; do test -f "$f"; done
make docs-truthfulness
bash scripts/wallet-lnurl-auth-release-gate.sh --candidate
echo "final readiness baseline checks complete"
