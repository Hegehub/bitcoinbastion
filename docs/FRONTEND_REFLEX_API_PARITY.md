# Reflex Frontend API Parity

| Frontend feature | Frontend client method | Backend endpoint | Exists | Response envelope handled | Error handling | Tests | Blockers |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Public status | `PublicApiClient.get_status` | `/api/v1/public/status` | yes | yes | backend unavailable fallback | `test_public_api_fallbacks.py`, `test_api_client.py` | none |
| Public roadmap | `PublicApiClient.get_roadmap` | `/api/v1/public/roadmap` | yes | yes | safe degraded fallback | `test_api_client.py` | none |
| Public Trace summary | `TraceApiClient.get_public_trace_summary` | `/api/v1/public/trace/{report_id}/summary` | yes | yes | 404/transport safe | `test_api_client.py`, `test_trace_report_api_client.py` | none |
| Trace lite | `TraceApiClient.get_trace_lite` | `/api/v1/trace/lite/{address}` | yes | yes | 400/timeout safe; sensitive material rejected before call | `test_api_client.py`, `test_trace_api_client.py`, `test_no_sensitive_input.py` | none |
| Trace address | `TraceApiClient.get_trace_address` | `/api/v1/trace/address/{address}` | yes | yes | safe `ApiResult` degraded state | `test_trace_api_client.py` | none |
| Trace report | `TraceApiClient.get_trace_report` | `/api/v1/trace/report/{report_id}` | yes | yes | 404 safe | `test_trace_report_api_client.py` | none |
| Trace evidence | `TraceApiClient.get_trace_evidence` | `/api/v1/trace/report/{report_id}/evidence` | yes | yes | safe empty/degraded | `test_trace_report_api_client.py` | none |
| Trace proof packet | `TraceApiClient.get_proof_packet` | `/api/v1/trace/report/{report_id}/proof-packet` | yes | yes | 404 safe | `test_proof_packet_page.py`, `test_proof_packet_route.py` | none |
| Trace status | console/status clients | `/api/v1/trace/status` | yes | yes | safe degraded state | `test_console_safety.py`, root contract tests | none |
| Trace events | console/audit clients | `/api/v1/trace/events` | yes | yes | safe degraded state | `test_console_safety.py`, root contract tests | none |
| Provider health | `ProviderHealthClient` | provider/health API adapters | partial | yes where envelope exists | safe degraded state | `test_console_api_clients.py` | endpoint shape may evolve |
| Evidence packets | `EvidenceClient` | `/api/v1/evidence/*` | yes/partial | yes | safe empty/degraded | `test_evidence_routes.py`, `test_console_api_clients.py` | packet detail parity remains iterative |
| Market dashboard | `MarketApiClient` | market/intelligence/time-machine APIs | partial | yes | safe degraded/fallback copy | `test_market_client.py`, `test_market_api_client.py` | FastAPI/Jinja remains delegated for market-detail routes |
| Policy console | `PolicyClient` | `/api/v1/policy/*` | yes | yes | review/draft safe errors | `test_console_api_clients.py`, `test_console_safety.py` | no execution/custody actions allowed |
| Audit console | `AuditClient` | audit/admin adapters | partial | yes | safe degraded state | `test_console_api_clients.py` | auth/admin shape may evolve |

## API client contract status

The Reflex `BastionApiClient` uses `BB_API_BASE_URL`, configurable request timeout, `ResponseEnvelope.data` unwrapping, raw JSON fallback, normalized HTTP errors for 400/404/422/429, timeout/network error normalization, and redaction-safe public messages. Tests cover the API client contract and service adapters.

## Decision

API parity is sufficient for **SWITCH_PARTIAL_WITH_DELEGATED_ROUTES**. Market-detail ownership remains delegated and must be re-audited in Prompt 22/22 before any archive decision.
