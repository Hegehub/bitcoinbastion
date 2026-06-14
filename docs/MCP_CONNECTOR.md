# Bastion MCP Connector

The Bastion MCP Connector is a developer-preview safe AI-agent interface for Bitcoin Bastion. It exposes read-only, recommendation-only, and draft-only tools over the existing Bitcoin Bastion API adapter.

Bitcoin Bastion MCP is not a wallet, not a custodian, not a trading executor, not a legal-verdict engine, not a Bitcoin consensus oracle, and not a signing interface.

## Safety model

Bitcoin Bastion is no-custody. Never enter seed phrases, private keys, wallet files, xprv/yprv/zprv, recovery phrases, keystore material, or signing material. Trace outputs are advisory-only, not legal verification, and not Bitcoin consensus proof. Market context is informational only; historical similarity does not guarantee future market behavior and correlation is not proof of causation.

The connector scans tool inputs for sensitive wallet material and scans outputs for misleading claims. Tool responses include `limitations`, `safety_flags`, `source`, and optional `degraded` state.

## Tools

- `get_latest_signals`: latest operator-safe signals with limitations.
- `explain_signal`: signal explanation with supporting evidence and correlation-not-causation language.
- `analyze_address`: advisory-only public Bitcoin address analysis through Trace.
- `get_trace_report`: existing Trace report retrieval.
- `get_public_trace_summary`: public-safe Trace summary retrieval.
- `get_wallet_health`: wallet-health context or explicit unavailable status.
- `evaluate_policy`: policy evaluation only; it does not execute actions.
- `create_treasury_draft`: local draft-only treasury review object requiring human approval.
- `get_provider_health`: provider health, stale, degraded, and fallback visibility.
- `get_market_dashboard`: BTC market context without financial advice or price prediction.
- `get_evidence_packet`: evidence packet/context retrieval.

## API adapter mapping

The adapter maps tools to the current Bitcoin Bastion API where available:

- Signals: `/api/v1/signals/latest`, `/api/v1/signals/{signal_id}`, `/api/v1/signals/{signal_id}/evidence`.
- Trace: `/api/v1/trace/lite/{address}`, `/api/v1/trace/report/{report_id}`, `/api/v1/public/trace/{report_id}/summary`.
- Wallet health: `/api/v1/wallet/profiles/{wallet_id}/health/reports?limit=1` when a wallet profile reference is supplied; otherwise unavailable is explicit.
- Policy: `/api/v1/policy/check` where policy-check payloads are available.
- Provider health: `/api/v1/health/providers`.
- Market context: `/api/v1/market/btc/context` for the current MCP dashboard baseline.
- Evidence: `/api/v1/evidence/packets/{packet_id}`.

Treasury draft creation is intentionally local/draft-only in this baseline. It does not call approve, reject, signing, broadcast, or execution endpoints.

## Configuration

```env
BB_API_BASE_URL=http://localhost:8000
BB_API_TOKEN=
BB_MCP_REQUEST_TIMEOUT_SECONDS=5
BB_MCP_DEFAULT_LIMIT=10
BB_MCP_ENABLE_TREASURY_DRAFTS=true
BB_MCP_ENABLE_MARKET_TOOLS=true
BB_MCP_ENABLE_TRACE_TOOLS=true
BB_MCP_ENABLE_WALLET_TOOLS=true
```

Empty tokens are allowed for local or public-safe endpoints. Protected deployments should provide `BB_API_TOKEN` and validate MCP host auth separately.

## Local usage

```bash
cd mcp
python -m pip install -e '.[dev]'
python -m bastion_mcp.server
```

The baseline entrypoint exposes the tool registry and accepts JSON-lines local tool calls. Live MCP-host compatibility testing, rate-limit evidence, production auth validation, and operator approval UX integration remain pending.

## Treasury draft-only model

`create_treasury_draft` may validate destination metadata, evaluate policy context, produce a draft summary, and return approval-required state. It must never sign, broadcast, approve, move funds, derive keys, request seed material, or bypass operator approval.

## Limitations and future work

- Production auth model validation is pending.
- Live MCP client compatibility testing is pending.
- Operator approval UX integration is pending.
- Rate-limit and abuse-prevention evidence is pending.
- Security review is pending.
