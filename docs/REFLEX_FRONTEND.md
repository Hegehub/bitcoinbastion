# Reflex Frontend

The Reflex frontend is an experimental, parallel Python-first UI layer under `reflex_frontend/`.

## Ownership boundaries

- Next.js is not removed and remains available until route/API parity and deployment evidence are complete.
- FastAPI remains the backend source of truth for domain logic, calculations, validation, and persistence.
- The `/market` FastAPI/Jinja Market Time Machine dashboard is not replaced by this Reflex work.
- Reflex is not production-primary until route/API parity, CI evidence, deployment evidence, and operator validation are complete.

## Prompt 26 scope

Prompt 26 adds Trace and Console routes: `/check`, `/trace`, Trace report/proof-packet pages, `/console`, `/console/trace`, `/console/evidence`, and `/console/provider-health`.

Trace is migration-critical, but it remains advisory-only. Safety warnings are required on Trace and Console surfaces. Proof Packet pages may be frontend-ready placeholders if backend public endpoints are not available yet; unavailable proof data must not be faked.

## Safety requirements

Reflex must never request seed phrases, private keys, wallet files, keystores, extended private keys, or signing material. Trace accepts public Bitcoin addresses only and must never present output as legal verification or Bitcoin consensus proof.
