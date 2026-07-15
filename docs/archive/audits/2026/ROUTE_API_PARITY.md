# Route/API Parity Report

This report records the Prompt 29 static parity contract. It does not claim production readiness.

## Backend Router Registration

Status: **implemented**.

`app/main.py` registers core routers for health, auth, news, market intelligence, market data, market, intelligence timeline, intelligence, signals, operator signals, on-chain, entities, wallet, fees, treasury, admin, users, policy, privacy, education, evidence, observability, citadel, trace, public, webhooks, and WebSocket streams.

## Trace Contract

Status: **implemented** for required routes.

Required Trace routes are present for lite/address analysis, reports, evidence, privacy shield, origin passport, source summary, provider disagreement, UTXO hygiene, dust radar, counterparty lens, policy facts, status, events, and public summary.

`/api/v1/trace/report/{report_id}/proof-packet` is also present. The Reflex proof packet UI must still treat unavailable backend data as degraded rather than certified evidence.

## Public Frontend Route Contract

Status: **partially implemented**.

- Reflex public, Trace, Console, and Command Center routes are registered.
- The legacy Next.js interface has been removed; parity now focuses solely on Reflex.
- FastAPI/Jinja `/market` remains the current Market Time Machine owner.

## Known Constraints

- Route registration does not prove deployment readiness.
- Route presence does not prove every data path has production evidence.
- Reflex remains experimental until route/API parity, deployment evidence, and operator validation are complete.
