#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
MODE="${1:---candidate}"

case "$MODE" in --candidate|--production) ;; *) echo "usage: $0 [--candidate|--production]" >&2; exit 2;; esac

run() { printf '\n==> %q ' "$1"; shift; printf '%q ' "$@"; printf '\n'; "$@"; }

# Fail-fast security invariants: legacy/bearer, proof-not-authorization, PoP/replay,
# policy, settlement, recovery, revocation, audit, SSRF, and sensitive logging.
run security python -m pytest -q tests/security
run unit python -m pytest -q tests/unit
run contracts python -m pytest -q \
  tests/contract/test_wallet_auth_api_contract.py \
  tests/contract/test_wallet_lnurl_policy_contract.py \
  tests/contract/test_wallet_lnurl_metrics_contract.py \
  tests/contract/test_lnurlp_openapi_contract.py \
  tests/contract/test_lnurl_entitlement_contract.py \
  tests/contract/test_lnurl_comment_contract.py \
  tests/contract/test_principal_access_certificate_openapi.py
run integration python -m pytest -q \
  tests/integration/test_wallet_pop_protected_request.py \
  tests/integration/test_wallet_session_lifecycle.py \
  tests/integration/test_wallet_entitlement_policy_flow.py \
  tests/integration/test_lnurl_k1_atomic_consume.py \
  tests/integration/test_lnurl_payment_entitlement_flow.py \
  tests/integration/test_lnurl_verify_settlement.py \
  tests/integration/test_lnurl_withdraw_callback_api.py \
  tests/integration/test_wallet_lnurl_step_up_flow.py \
  tests/integration/test_wallet_lnurl_revocation_flow.py \
  tests/integration/test_wallet_lnurl_audit_integration.py \
  tests/integration/test_recovery_capsule_flow.py \
  tests/integration/test_principal_access_certificate_flow.py \
  tests/integration/test_offline_pack_issue_verify_reconcile.py \
  tests/integration/test_payregister_lnurl_shift_flow.py
run python-sdk python -m pytest -q sdk/python/tests
run cli python -m pytest -q tests/cli
run typescript-sdk bash -c 'cd sdk/typescript && npm test && npm run typecheck && npm run build'
run reflex bash -c 'cd frontend && uv run pytest && uv run ruff check bastion_ui && uv run mypy bastion_ui && uv run reflex export --frontend-only --no-zip'
run release-governance python -m pytest -q tests/test_release_gates.py
run docs-truthfulness python scripts/check_docs_truthfulness.py
run migrations bash scripts/check_alembic_reproducibility.sh

if [[ "$MODE" == "--production" ]]; then
  echo "Production gate BLOCKED: final validation classifies this repository NOT PRODUCTION-READY." >&2
  echo "See docs/WALLET_LNURL_AUTH_FINAL_VALIDATION.md for mandatory blockers." >&2
  exit 1
fi

echo "Wallet/LNURL release-candidate gate PASS; production promotion remains blocked by documented gaps."
