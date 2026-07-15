# Trace API Contract

Bastion Trace is a backend baseline. It is advisory-only, no-custody, not legal verification, not Bitcoin consensus proof, and not production-calibrated unless separate environment evidence exists. All endpoints below are served under `/api/v1` and use `ResponseEnvelope[...]` unless noted.

| Method | Endpoint | Purpose | Response envelope | Frontend consumer | Status | Limitations |
| --- | --- | --- | --- | --- | --- | --- |
| GET | `/trace/lite/{address}` | Public Bitcoin address Lite check. | `ResponseEnvelope[dict[str, object]]` | `/check`, `/trace`, `apiClient.checkTraceLite` | implemented baseline | Rejects sensitive wallet material; advisory scoring only. |
| GET | `/public/trace/{report_id}/summary` | Public-safe Trace report summary. | `ResponseEnvelope[PublicTraceSummary]` | `/check`, `/trace/[reportId]`, `apiClient.getTraceSummary` | implemented baseline | Public summary only; not full investigative record. |
| GET | `/trace/address/{address}` | Analyze a public Bitcoin address and persist a report. | `ResponseEnvelope[TraceReport]` | backend/API users | implemented baseline | Public address only; advisory scoring. |
| GET | `/trace/report/{report_id}` | Full Trace report DTO. | `ResponseEnvelope[TraceReport]` | `apiClient.getTraceReport` | implemented baseline | Not production-calibrated. |
| GET | `/trace/report/{report_id}/evidence` | Evidence rows for a report. | `ResponseEnvelope[list[TraceEvidence]]` | `apiClient.getTraceEvidence` | implemented baseline | Source-limited baseline evidence. |
| GET | `/trace/report/{report_id}/proof-packet` | Public-safe application-level proof packet summary. | `ResponseEnvelope[dict[str, object]]` | `/trace/[reportId]/proof-packet`, `apiClient.getProofPacket` | implemented baseline | Unsigned unless signing is explicitly configured; not legal verification or Bitcoin consensus proof. |
| GET | `/trace/report/{report_id}/privacy-shield` | Privacy-shield facet. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTracePrivacyShield` | implemented baseline | Probabilistic/source-limited privacy assessment. |
| GET | `/trace/report/{report_id}/origin-passport` | Origin-passport facet. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTraceOriginPassport` | implemented baseline | Origin attribution may be unknown/source-limited. |
| GET | `/trace/report/{report_id}/source-summary` | Source summary for a report. | `ResponseEnvelope[list[dict[str, object]]]` | none currently | implemented baseline | Baseline source inventory. |
| GET | `/trace/report/{report_id}/provider-disagreement` | Provider disagreement facet. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTraceProviderDisagreement` | implemented baseline | Depends on available providers. |
| GET | `/trace/report/{report_id}/utxo-hygiene` | UTXO hygiene facet. | `ResponseEnvelope[dict[str, object]]` | none currently | implemented baseline | Not a wallet action or signing feature. |
| GET | `/trace/report/{report_id}/dust-radar` | Dust-radar facet. | `ResponseEnvelope[dict[str, object]]` | none currently | implemented baseline | Source-limited. |
| GET | `/trace/report/{report_id}/counterparty-lens` | Counterparty-lens facet. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTraceCounterpartyLens` | implemented baseline | Advisory manual-review context only. |
| GET | `/trace/report/{report_id}/policy-facts` | Policy facts bridge. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTracePolicyFacts` | implemented baseline | Not legal advice. |
| GET | `/trace/report/{report_id}/evidence-refs` | Public-safe evidence reference list. | `ResponseEnvelope[list[dict[str, object]]]` | none currently | implemented baseline | Reference metadata only. |
| GET | `/trace/status` | Trace operational baseline status. | `ResponseEnvelope[dict[str, object]]` | `apiClient.getTraceStatus` | implemented baseline | Reports not production calibration evidence. |
| GET | `/trace/events` | Trace runtime events. | `ResponseEnvelope[list[dict[str, object]]]` | `apiClient.getTraceEvents` | implemented baseline | Runtime-event records only; no WebSocket stream. |
| GET | `/trace/events/{event_id}` | Single Trace runtime event. | `ResponseEnvelope[dict[str, object]]` | none currently | implemented baseline | 404 when missing. |
| GET | `/trace/alerts` | Trace alert placeholders/list. | `ResponseEnvelope[list[dict[str, object]]]` | none currently | baseline | Delivery depends on environment configuration. |
| GET | `/trace/sources` | Trace source registry list. | `ResponseEnvelope[list[TraceSourceStatus]]` | none currently | implemented baseline | Baseline sources only. |
| GET | `/trace/sources/{source_name}` | Single Trace source status. | `ResponseEnvelope[TraceSourceStatus]` | none currently | implemented baseline | 404 when missing. |
| GET | `/trace/watchlist` | Watchlist entries. | `ResponseEnvelope[list[TraceWatchlistEntry]]` | none currently | implemented baseline | Operator-controlled metadata only. |
| POST | `/trace/watchlist` | Add watchlist entry. | `ResponseEnvelope[TraceWatchlistEntry]` | none currently | implemented baseline | Rejects sensitive wallet material. |
| POST | `/trace/payment-context` | Payment-context advisory review. | `ResponseEnvelope[dict[str, object]]` | none currently | baseline | Does not approve payments or sign/broadcast transactions. |
| POST | `/trace/payment-intent/preview` | Payment-intent advisory preview. | `ResponseEnvelope[dict[str, object]]` | none currently | baseline | Preview only; no transaction creation. |
| POST | `/trace/destination-review` | Destination review. | `ResponseEnvelope[dict[str, object]]` | none currently | baseline | Advisory only. |
| GET | `/trace/business/profile` | Business tier profile. | `ResponseEnvelope[dict[str, object]]` | business UI | baseline | Capability profile, not billing/enforcement. |
| POST | `/trace/business/batch` | Business batch screening. | `ResponseEnvelope[dict[str, object]]` | business UI | baseline | Advisory screening only. |
| GET | `/trace/business/policy-profiles` | Business policy profiles. | `ResponseEnvelope[list[dict[str, object]]]` | business UI | baseline | Baseline policy metadata. |
| GET | `/trace/business/events` | Business event records. | `ResponseEnvelope[list[dict[str, object]]]` | business UI | baseline | Business-tier records; not used by public runtime feed. |
| GET | `/trace/enterprise/profile` | Enterprise tier profile. | `ResponseEnvelope[dict[str, object]]` | enterprise UI | baseline | Placeholder until configured. |
| GET | `/trace/enterprise/rbac/roles` | Enterprise roles. | `ResponseEnvelope[list[str]]` | enterprise UI | placeholder | Not production IdP integration. |
| GET | `/trace/enterprise/rbac/permissions` | Enterprise permissions. | `ResponseEnvelope[list[str]]` | enterprise UI | placeholder | Not production IdP integration. |
| GET | `/trace/enterprise/rbac/default-policy` | Enterprise default policy. | `ResponseEnvelope[dict[str, object]]` | enterprise UI | placeholder | Baseline only. |
| GET | `/trace/enterprise/sso` | SSO placeholder status. | `ResponseEnvelope[dict[str, object]]` | enterprise UI | placeholder | No production SSO unless configured. |
| POST | `/trace/enterprise/evidence-access/evaluate` | Evidence access evaluation. | `ResponseEnvelope[dict[str, object]]` | enterprise UI | baseline | Not legal access determination. |
| POST | `/trace/enterprise/proof-packet` | Enterprise proof packet builder. | `ResponseEnvelope[dict[str, object]]` | enterprise UI/API users | baseline | Evidence bundle; not legal certificate. |
| GET | `/trace/report/{report_id}/citadel-contribution` | Citadel integration contribution. | `ResponseEnvelope[dict[str, object]]` | none currently | baseline | Advisory integration bridge. |
| POST | `/trace/treasury/destination-check` | Treasury bridge destination check. | `ResponseEnvelope[dict[str, object]]` | treasury UI/API users | baseline | No signing or broadcasting. |
| POST | `/trace/register/payment-advisory` | Register bridge payment advisory. | `ResponseEnvelope[dict[str, object]]` | register UI/API users | baseline | Does not auto-accept or auto-reject payments. |

## Frontend contract lock

The Reflex Trace frontend calls the implemented endpoints above through
`frontend/bastion_ui/services/api_client.py` and
`frontend/bastion_ui/services/trace_client.py`.
`ResponseEnvelope.data` unwrapping is preserved by the shared API client. Proof
packets are displayed as unsigned application-level evidence summaries unless
real signing is implemented, configured, and evidenced.
