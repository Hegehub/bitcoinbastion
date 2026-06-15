# Frontend Parity Status

Status vocabulary: **implemented**, **partially implemented**, **planned**, **blocked**, **not applicable**.

## Existing Next.js Frontend

Status: **implemented / retained**.

The existing `frontend/` application remains in the repository. Prompt 29 does not delete, archive, or replace it.

## FastAPI/Jinja Market Dashboard

Status: **implemented / retained**.

The `/market` dashboard remains owned by existing FastAPI/Jinja web routes. Reflex console Time Machine and Market Intelligence pages are previews only and do not replace `/market`.

## Reflex Frontend

Status: **partially implemented**.

Implemented Reflex route groups:

- Public pages: `/`, `/platform`, `/developers`, `/operations`, `/manifesto`, `/evidence`, `/status`, `/roadmap`, `/security`, `/docs`.
- Trace pages: `/check`, `/trace`, `/trace/[report_id]`, `/trace/[report_id]/proof-packet`.
- Console pages: `/console`, `/console/trace`, `/console/evidence`, `/console/provider-health`, `/console/market-intelligence`, `/console/time-machine`, `/console/sovereign-grid`, `/console/policy`, `/console/audit`, `/console/deployment`, `/console/api-explorer`, `/console/command-center`.

## Wow Layer

Status: **partially implemented**.

Wow-layer components exist as preview/operator-visibility surfaces: Bastion Command Center, Trace Radar, Evidence Chain Viewer, Proof Packet Explorer, Time Machine Timeline, Sovereignty Score Panel, Node Pulse, Provider Trust Matrix, No-Custody Safety Layer, Human Confirmation Firewall, Trace Story Mode, Policy Engine Simulator, Risk Heatmap, Operator Audit Replay, Market Intelligence Wall, Historical Similarity Lens, Sovereign Grid Map, API Contract Explorer, Privacy Exposure Lens, Citadel Mode, and Animated Core.

These components remain frontend foundations. They must consume backend DTOs where available and explicitly display preview/unavailable/degraded states where backend data is missing.

## Safety Boundary

Status: **implemented**.

Frontend surfaces must preserve: Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material.
