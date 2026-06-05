# Sovereignty Certification

Certification date: 2026-06-05  
Classification: **Sovereignty-Grade Production Candidate**

## Certification statement

Bitcoin Bastion is certified in this repository as a Bitcoin-first, evidence-driven, self-hosted production candidate. The certification is conservative: it does not claim perfection, complete security, guaranteed accuracy, or bug-free operation.

Mandatory public-output safety language:

- Correlation is not proof of causation.
- Evidence-based informational analysis.
- Not financial advice.

## Sovereignty principles

| Principle | Status | Evidence |
| --- | --- | --- |
| Bitcoin-first | PASS | Market data, intelligence, signal, and policy layers are scoped around Bitcoin context. |
| No custody | PASS | The platform does not hold user funds or private keys. |
| No trading executor | PASS | Signal publication and operator review do not execute trades. |
| Evidence over claims | PASS | Evidence packets, source provenance, confidence inputs, limitations, and replay logs are first-class outputs. |
| Replay over trust | PASS | Evidence replay and restore validation require deterministic replay checks. |
| Operator control | PASS | Review, hold, approval, rejection, delivery, and degraded-state visibility are operator-facing. |
| Self-hosted compatible | PASS | Docker/Kubernetes/GitOps artifacts and environment-variable documentation support self-hosted operation. |
| No mandatory paid APIs | PASS | Provider abstractions and degraded mode avoid a mandatory paid-provider dependency. |
| No mandatory OpenAI dependency | PASS | Core production runtime is deterministic/rule-oriented and does not require OpenAI to operate. |
| Correlation is not causation | PASS | Market Time Machine, scoring, attribution, replay, and public/web outputs expose limitations. |

## Certification boundaries

This certification covers repository behavior and release-candidate readiness. It does not replace:

- independent security audit;
- legal review;
- production incident drill evidence;
- production data-provider SLA validation;
- accessibility certification;
- infrastructure hardening evidence.

## Operational sovereignty guarantees

Bitcoin Bastion must continue to expose:

- degraded provider state;
- provider confidence;
- last success and last failure timestamps;
- evidence limitations;
- replay limitations;
- operator review status;
- publication status;
- backup/restore/integrity validation outcomes.

If these become unavailable, the correct state is degraded or critical, never fake-healthy.
