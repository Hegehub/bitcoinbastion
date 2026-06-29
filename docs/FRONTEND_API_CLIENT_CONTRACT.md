> Current note (2026-06-29): the old Next.js frontend has been removed; historical references below are retained only for migration context. Reflex is the only repository-native frontend.

# Frontend API Client Contract

## 1. Purpose

This document defines the Prompt 5/22 Reflex API client contract. The Reflex frontend calls the FastAPI backend as the source of truth. Reflex may normalize transport errors, unwrap response envelopes, validate obviously unsafe frontend inputs, and redact logs, but it must not duplicate backend domain logic or fabricate Trace, Evidence, Market, Console, or Policy data.

## 2. Config variables

| Variable | Default | Status | Notes |
|---|---:|---|---|
| `BB_API_BASE_URL` | `http://localhost:8000` | implemented | Trailing slash is stripped by `AppConfig`. |
| `BB_REQUEST_TIMEOUT_SECONDS` | `5` | implemented | Must be positive. |
| `BB_PUBLIC_SITE_MODE` | `true` | implemented | Enables public-site mode flags for later pages. |
| `BB_ENABLE_TRACE` | `true` | implemented | Feature flag only; no Trace pages migrated here. |
| `BB_ENABLE_MARKET` | `true` | implemented | Feature flag only; Market dashboard remains unchanged. |
| `BB_ENABLE_TIME_MACHINE` | `true` | implemented | Feature flag only. |
| `BB_ENABLE_CONSOLE` | `true` | implemented | Feature flag only. |
| `BB_ENABLE_SOVEREIGN_GRID` | `true` | implemented | Feature flag only. |
| `BB_DEFAULT_LANGUAGE` | `en` | implemented | Reserved for later i18n work. |
| `BB_LOG_LEVEL` | `INFO` | implemented | Must not be used to print secrets. |

## 3. ResponseEnvelope handling

The client accepts normal JSON and envelope-style JSON. If a JSON payload contains `data`, the client returns `data`. If a JSON payload contains non-null `error`, it raises a normalized `BastionApiError`. If JSON does not contain `data`, the full JSON payload is returned. HTTP 204 returns `None`. Non-JSON responses raise a safe unavailable error.

## 4. Error handling

| Condition | Error class | Public message |
|---|---|---|
| `400` / `422` | `BastionApiValidationError` | The request could not be processed. Check the input and try again. |
| `404` | `BastionApiNotFoundError` | The requested resource was not found. |
| `429` | `BastionApiRateLimitError` | Too many requests. Wait briefly and try again. |
| `5xx` / non-JSON | `BastionApiUnavailableError` | Bitcoin Bastion is temporarily unavailable. |
| Timeout | `BastionApiTimeoutError` | The request timed out. Try again shortly. |
| Connection / transport | `BastionApiConnectionError` | Unable to reach Bitcoin Bastion backend. |

Errors expose safe fields: `status_code`, `message`, `public_message`, `details`, and `request_id`. UI code should display `public_message`.

## 5. Public client endpoints

| Endpoint | Status | Client method |
|---|---|---|
| `/api/v1/public/landing` | implemented | `get_landing` |
| `/api/v1/public/status` | implemented | `get_status` |
| `/api/v1/public/roadmap` | implemented | `get_roadmap` |
| `/api/v1/public/stats` | implemented | `get_stats` |
| `/api/v1/public/features` | implemented | `get_features` |
| `/api/v1/public/trace/{report_id}/summary` | implemented | `get_public_trace_summary` |

## 6. Trace client endpoints

| Endpoint | Status | Client method |
|---|---|---|
| `/api/v1/trace/lite/{address}` | implemented | `get_trace_lite` |
| `/api/v1/trace/address/{address}` | implemented | `get_trace_address` |
| `/api/v1/trace/report/{report_id}` | implemented | `get_trace_report` |
| `/api/v1/trace/report/{report_id}/evidence` | implemented | `get_trace_evidence` |
| `/api/v1/trace/report/{report_id}/origin-passport` | implemented | `get_origin_passport` |
| `/api/v1/trace/report/{report_id}/privacy-shield` | implemented | `get_privacy_shield` |
| `/api/v1/trace/report/{report_id}/source-summary` | implemented | `get_source_summary` |
| `/api/v1/trace/report/{report_id}/provider-disagreement` | implemented | `get_provider_disagreement` |
| `/api/v1/trace/report/{report_id}/utxo-hygiene` | implemented | `get_utxo_hygiene` |
| `/api/v1/trace/report/{report_id}/dust-radar` | implemented | `get_dust_radar` |
| `/api/v1/trace/report/{report_id}/counterparty-lens` | implemented | `get_counterparty_lens` |
| `/api/v1/trace/report/{report_id}/policy-facts` | implemented | `get_policy_facts` |

Trace clients only call backend endpoints. They do not compute or reinterpret risk, evidence, source disagreement, or policy facts.

## 7. Evidence client endpoints

| Endpoint | Status | Client method | Notes |
|---|---|---|---|
| `/web/evidence/{packet_id}` | uncertain | `get_evidence_packet` | Current web DTO route is used as a foundation; verify JSON/DTO behavior before page migration. |
| `/api/v1/trace/report/{report_id}/evidence` | implemented | `get_trace_report_evidence` | Trace evidence endpoint. |
| Stable `/api/v1/evidence/{packet_id}` JSON endpoint | missing | `get_json_evidence_packet` | Method raises a safe not-found error until backend contract exists. |

## 8. Status client endpoints

| Endpoint | Status | Client method |
|---|---|---|
| `/api/v1/public/status` | implemented | `get_public_status` |
| `/api/v1/health/providers` | implemented | `get_provider_health` |
| `/api/v1/health` | implemented | `get_health` |

Degraded/stale state must be displayed by future pages when exposed by backend payloads.

## 9. Market client endpoints

| Endpoint | Status | Client method | Notes |
|---|---|---|---|
| `/api/v1/market/health` | JSON/DTO-ready | `get_market_dashboard` | Foundation only; not a migrated dashboard. |
| `/web/market-time-machine` | uncertain | `get_market_time_machine` | Existing web DTO-style endpoint; verify response shape before page migration. |
| `/web/timeline` | uncertain | `get_timeline` | Existing web DTO-style endpoint. |
| `/web/candle/{candle_id}` | uncertain | `get_candle` | Existing web DTO-style endpoint. |
| `/web/evidence/{packet_id}` | uncertain | `get_evidence` | Existing web DTO-style endpoint. |

If an endpoint returns HTML, future Reflex pages must not treat it as JSON. The FastAPI/Jinja Market dashboard remains active during parity work.

## 10. Console client endpoints

| Endpoint | Status | Client method | Notes |
|---|---|---|---|
| `/api/v1/operations/status` | implemented | `get_console_overview` | Safe operational summary foundation. |
| `/api/v1/health/providers` | implemented | `get_provider_health_matrix` | Provider health foundation. |
| Stable audit summary endpoint | missing | `get_audit_summary` | Raises safe unavailable error. |
| Stable policy summary endpoint | missing | `get_policy_summary` | Raises safe unavailable error. |

## 11. Known backend/frontend mismatches

- Stable JSON Evidence packet endpoint remains missing or undocumented; current `/web/evidence/{packet_id}` ownership must be verified before Reflex Evidence pages use it.
- Market `/web/*` endpoints are DTO-style web endpoints; future work must verify JSON response behavior and avoid treating HTML views as API data.
- Console audit and policy summaries do not have stable Reflex client endpoints yet, so placeholder methods raise explicit safe errors rather than fake data.
- Trace API methods are implemented for documented backend paths, but page migration and UI parity remain future work.

## 12. No-custody logging rules

Do not log request JSON bodies by default. Do not log authorization headers, bearer/session tokens, API keys, webhook secrets, seed/mnemonic/private-key-like text, wallet files, keystores, extended private keys, or signing material. Use `redact_payload`, `redact_sensitive_text`, and `safe_error_message` for diagnostic messages.

## 13. Timeout behavior

`BB_REQUEST_TIMEOUT_SECONDS` controls the `httpx.AsyncClient` timeout. Timeouts raise `BastionApiTimeoutError` with a safe public message.

## 14. Testing strategy

Tests use `httpx.MockTransport` and recording clients. They do not require a live backend. The suite verifies URL joining, ResponseEnvelope unwrapping, raw JSON passthrough, 204 handling, HTTP error mapping, timeout/connection normalization, path construction, and redaction rules.

## 15. Remaining blockers

- No pages are migrated in Prompt 5.
- Next.js remains intact and active as the legacy-supported rollback surface.
- FastAPI/Jinja Market dashboard remains unchanged.
- Evidence and Market DTO response shapes need verification before route migration.
- Console audit/policy backend contracts remain missing or unstable.
