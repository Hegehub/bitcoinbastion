# Bastion Trace Integrations

## Positioning
Bastion Trace is integrated as a module inside Bitcoin Bastion; it is not a standalone platform replacement.

## Citadel
- Integrated as a separate advisory contribution object.
- Deterministic impact mapping is baseline only.
- No legal verdict, no consensus proof.

## Policy Engine
- Trace facts and recommendation-style outputs are exposed.
- Policy integration is advisory unless a configured policy engine enforces it.
- No payment execution performed by bridge outputs.

## Treasury
- Treasury destination advisory is implemented as a hook endpoint.
- Treasury bridge does not sign or broadcast transactions.
- No custody/wallet secret handling.

## Register
- Merchant/payment advisory placeholder integration exists.
- Register bridge does not auto-reject or auto-accept payments by itself.

## Evidence layer
- Cross-domain trace evidence reference output is implemented.
- Designed for auditability without requiring full payload duplication.

## Operations/Observability
- Trace status and runtime events/alerts endpoints exist.
- `trace_production_calibrated` remains false.

## Telegram
- Telegram-related baseline docs/placeholders exist.
- Telegram usage is advisory and must never request seed phrases/private keys.
