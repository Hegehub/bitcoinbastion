# Reflex Frontend

The Reflex frontend is the primary Python-first UI layer under `reflex_frontend/` and is the sole repository-native frontend. It replaces the legacy Next.js UI surface that was previously used during migration.

## Ownership and boundaries

- FastAPI remains the backend source of truth for domain logic, calculations, validation and persistence.
- Some web pages remain served by FastAPI/Jinja templated routes. In particular, the Market dashboard and certain drill-down pages (`/market`, `/intelligence/timeline`, `/evidence/{packet_id}`, `/candles/{candle_id}`) continue to be rendered by the backend until frontend parity is fully achieved.
- Although Reflex is now the default frontend, full production readiness still requires route/API parity, CI evidence, deployment evidence and operator validation. Until these gates are met, the UI should be treated as migration-primary but not production-complete.

## Features

Reflex currently includes public pages (landing, platform, developers, operations, manifesto, evidence, status, roadmap, security, docs), Trace check/report and proof packet pages, and a set of operator console views (console dashboard, trace, evidence, market intelligence, time machine, sovereign grid, policy, audit, API explorer and command palette). Additional modules continue to be developed.

## Safety requirements

Reflex must never request seed phrases, private keys, wallet files, keystores, extended private keys or signing material. Trace accepts public Bitcoin addresses only and must never present output as legal verification or Bitcoin consensus proof.
