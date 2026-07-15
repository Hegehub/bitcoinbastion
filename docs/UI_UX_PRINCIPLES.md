# UI/UX Principles

Status: **ACTIVE**. This document owns cross-surface UI safety language; route
and API ownership remain in the relevant frontend and API documents.

- Bitcoin-first, no-custody, advisory-only messaging.
- Accessible focusable navigation and semantic landmarks.
- Calm motion only; reduced animation baseline.
- Never use clean/dirty/safe/approved wording in risk presentation.

- Public pages are informational and product-orientation baseline.
- Frontend does not handle seed phrases/private keys.
- Frontend does not sign or broadcast transactions.


Public address check UX is baseline-only, advisory, and must never use clean/dirty/safe/approved wording.

Detailed report UI must avoid certainty claims and remain advisory/probabilistic.

Business/Enterprise frontend wording must remain operational/advisory and non-legal.

Platform dashboard/Citadel/Operations UI are informational baselines, not control planes.

## Surface boundaries

| Surface | Required posture |
| --- | --- |
| Public and Lite | Public-address-only, advisory, no certainty or address-morality wording. |
| Trace report | Probabilistic evidence with visible confidence, reasons, limitations, replay context, and operator guidance. |
| Business | Operational recommendations only; actions do not execute payments and proof packets are not legal certificates. |
| Enterprise | Governance metadata only until production RBAC, SSO, SIEM, and policy enforcement are configured and evidenced. |
| Review Desk | Review, notes, approve/reject/hold semantics only; no payment execution. |
| Citadel | Advisory resilience analysis; never a Bitcoin consensus or legal-verification surface. |
| Platform and Operations | Read-only operational context, not a direct infrastructure control plane. |
| Runtime events | Degraded and placeholder states must be explicit; secrets and internal topology must not be exposed. |

Detailed implementation guidance lives in [REFLEX_FRONTEND.md](REFLEX_FRONTEND.md),
[TRACE_REPORT_UI.md](TRACE_REPORT_UI.md), and
`frontend/docs/SAFETY_COPY.md`.
