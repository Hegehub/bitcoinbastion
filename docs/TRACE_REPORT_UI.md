# Trace Report UI

Detailed Trace reports are advisory-only.
Frontend report UI is baseline and not production-calibrated.
The report page includes overview, timeline, privacy, origin, confidence, reasons, limitations, replay summary, and operator guidance.

Lite accepts public Bitcoin addresses only, rejects sensitive key material, and
must never use `clean`, `dirty`, `safe`, or `approved` as address judgments.
Privacy findings are probabilistic and source-limited; they do not imply
criminality or a legal conclusion. Timeline entries use neutral language such
as “signal observed”, “provider disagreement”, and “manual review recommended”.

## Public navigation baseline

Trace is exposed in the public site navigation and command palette so operators can reach `/trace` and `/check` without relying on hidden routes.
The command palette replaces stale `/products` and `/self-host` actions with the canonical `/platform` and `/operations` routes, and it exposes Market Intelligence / Time Machine routes for discovery.

## Proof packet UI

`/trace/[reportId]/proof-packet` calls the backend `GET /api/v1/trace/report/{report_id}/proof-packet` endpoint.
The UI must describe the packet as an unsigned application-level evidence summary when `signed` is `false`.
Proof packets are not legal verification, not Bitcoin consensus proof, and not production calibration evidence.
