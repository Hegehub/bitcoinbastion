# Frontend API Client Contract

## 1. Purpose

This document defines the Reflex frontend API client contract for Bitcoin Bastion. The Reflex frontend treats the FastAPI backend as the source of truth and does not duplicate Trace scoring, Market Intelligence, Evidence, Policy, or backend domain logic.

## 2. Config variables

The Reflex API layer reads environment variables through `bastion_ui.config.Settings`:

| Variable | Default | Status | Notes |
| --- | --- | --- | --- |
| `BB_API_BASE_URL` | `http://localhost:8000` | implemented | Trailing slashes are stripped. |
| `BB_REQUEST_TIMEOUT_SECONDS` | `5` | implemented | Must be positive. |
| `BB_PUBLIC_SITE_MODE` | `true` | implemented | Frontend feature mode flag. |
| `BB_ENABLE_TRACE` | `true` | implemented | Enables Trace UI wiring in later prompts. |
| `BB_ENABLE_MARKET` | `true` | implemented | Enables Market client wiring in later prompts. |
| `BB_ENABLE_TIME_MACHINE` | `true` | implemented | Enables Time Machine UI wiring in later prompts. |
| `BB_ENABLE_CONSOLE` | `true` | implemented | Enables Console UI wiring in later prompts. |
| `BB_ENABLE_SOVEREIGN_GRID` | `true` | implemented | Enables Sovereign Grid UI wiring in later prompts. |
| `BB_DEFAULT_LANGUAGE` | `en` | implemented | Future i18n default. |
| `BB_LOG_LEVEL` | `INFO` | implemented | Safe logging only; no secrets are printed. |

## 3. ResponseEnvelope handling

The shared client unwraps backend envelope responses when a `data` key is present. Examples:

- `{ "data": {...}, "error": null, "meta": {...} }` returns `data`.
- `{ "status": "ok", "data": {...} }` returns `data`.
- JSON without `data` returns the full JSON object.
- Non-JSON responses raise a normalized API error.
- HTTP 204 returns `None`.
- Non-null `error` envelopes raise a normalized frontend API error.

## 4. Error handling

The Reflex API layer exposes safe frontend error classes:

| Status / condition | Error class | Public message status |
| --- | --- | --- |
| 400 / 422 | `BastionApiValidationError` | implemented |
| 404 | `BastionApiNotFoundError` | implemented |
| 429 | `BastionApiRateLimitError` | implemented |
| 5xx | `BastionApiUnavailableError` | implemented |
| timeout | `BastionApiTimeoutError` | implemented |
| connection failure | `BastionApiConnectionError` | implemented |
| unreadable JSON | `BastionApiError` | implemented |

Errors expose safe fields: `status_code`, `message`, `public_message`, `details`, and `request_id`. Internal stack traces and request bodies are not exposed to UI callers.

## 5. Public client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_landing` | `/api/v1/public/landing` | implemented |
| `get_status` | `/api/v1/public/status` | implemented |
| `get_roadmap` | `/api/v1/public/roadmap` | implemented |
| `get_stats` | `/api/v1/public/stats` | implemented |
| `get_features` | `/api/v1/public/features` | implemented |
| `get_public_trace_summary` | `/api/v1/public/trace/{report_id}/summary` | implemented |

## 6. Trace client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_trace_lite` | `/api/v1/trace/lite/{address}` | implemented |
| `get_trace_address` | `/api/v1/trace/address/{address}` | implemented |
| `get_trace_report` | `/api/v1/trace/report/{report_id}` | implemented |
| `get_trace_evidence` | `/api/v1/trace/report/{report_id}/evidence` | implemented |
| `get_origin_passport` | `/api/v1/trace/report/{report_id}/origin-passport` | implemented |
| `get_privacy_shield` | `/api/v1/trace/report/{report_id}/privacy-shield` | implemented |
| `get_source_summary` | `/api/v1/trace/report/{report_id}/source-summary` | implemented |
| `get_provider_disagreement` | `/api/v1/trace/report/{report_id}/provider-disagreement` | implemented |
| `get_utxo_hygiene` | `/api/v1/trace/report/{report_id}/utxo-hygiene` | implemented |
| `get_dust_radar` | `/api/v1/trace/report/{report_id}/dust-radar` | implemented |
| `get_counterparty_lens` | `/api/v1/trace/report/{report_id}/counterparty-lens` | implemented |
| `get_policy_facts` | `/api/v1/trace/report/{report_id}/policy-facts` | implemented |

## 7. Evidence client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_evidence_packet` | `/web/evidence/{packet_id}` | uncertain |
| `get_trace_report_evidence` | `/api/v1/trace/report/{report_id}/evidence` | implemented |

`/web/evidence/{packet_id}` is used by the current web surface and may be DTO-ready or may require backend clarification before Reflex page migration.

## 8. Status client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_public_status` | `/api/v1/public/status` | implemented |
| `get_provider_health` | stable endpoint TBD | missing |
| `get_health` | `/health` | uncertain |

Provider health remains a backend/frontend mismatch until a stable DTO endpoint is documented.

## 9. Market client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_market_dashboard` | `/web/market-time-machine` | uncertain |
| `get_market_time_machine` | `/web/market-time-machine` | uncertain |
| `get_timeline` | `/web/timeline` | uncertain |
| `get_candle` | `/web/candle/{candle_id}` | uncertain |
| `get_evidence` | `/web/evidence/{packet_id}` | uncertain |

These paths are current FastAPI/Jinja or web DTO-style dependencies. If any endpoint returns HTML, Reflex must not treat it as a JSON API. Market pages are not migrated in this prompt.

## 10. Console client endpoints

| Method | Endpoint | Status |
| --- | --- | --- |
| `get_console_overview` | `/api/v1/public/status` | implemented fallback |
| `get_provider_health_matrix` | stable endpoint TBD | missing |
| `get_audit_summary` | stable endpoint TBD | missing |
| `get_policy_summary` | stable endpoint TBD | missing |

Missing console endpoints raise explicit frontend errors rather than returning fake dashboard data.

## 11. Known backend/frontend mismatches

- Provider health matrix has no stable documented Reflex DTO endpoint yet.
- Audit summary has no stable documented Reflex DTO endpoint yet.
- Policy summary has no stable documented Reflex DTO endpoint yet.
- Market `/web/*` endpoints require confirmation that responses are JSON/DTO-ready rather than HTML-only.
- Evidence packet lookup through `/web/evidence/{packet_id}` requires backend response-shape confirmation.

## 12. No-custody logging rules

The API layer must not log request JSON bodies by default. Safe logging redacts sensitive wallet material, authorization headers, API keys, webhook secrets, session tokens, bearer tokens, extended private-key prefixes, and mnemonic-like 12-word or 24-word strings.

## 13. Timeout behavior

Requests use `BB_REQUEST_TIMEOUT_SECONDS`. Timeout failures map to `BastionApiTimeoutError` with a UI-safe message and no sensitive request body details.

## 14. Testing strategy

Tests use `httpx.MockTransport` and do not require a live backend. Coverage includes URL joining, envelope unwrapping, 204 handling, HTTP status mapping, timeout and connection handling, public/Trace path construction, and safe logging redaction.

## 15. Remaining blockers

- Reflex pages are not migrated yet.
- Trace route parity is not complete.
- Market dashboard ownership is unchanged.
- Console backend DTO endpoints need confirmation.
- Provider health, audit, and policy summaries require stable backend contracts before UI migration.
