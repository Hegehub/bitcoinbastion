# FRONTEND BACKLOG

## Purpose
This backlog assumes the backend is the current source of truth.
Frontend must follow real APIs and avoid inventing unavailable data.

## Phase F1 — Core app shell
### FE-01
Build authenticated app shell and navigation for:
- Intelligence
- Citadel
- Admin / Ops

### FE-02
Build health and observability surfaces.

## Phase F2 — Bastion intelligence
### FE-03
Signal feed screen using `/api/v1/signals/top`

### FE-04
Signal explanation drawer using `/api/v1/signals/{signal_id}/explanation`

### FE-05
Recommendation view using `/api/v1/signals/{signal_id}/recommendations`

### FE-06
On-chain events screen using `/api/v1/onchain/events`

### FE-07
Entity list and provenance surface using `/api/v1/entities`

## Phase F3 — Sovereign operations
### FE-08
Wallet health screen

### FE-09
Fee recommendation screen

### FE-10
Privacy assessment screen

### FE-11
Treasury request list and review screen

### FE-12
Policy simulation / catalog screen

## Phase F4 — Citadel
### FE-13
Citadel overview screen

### FE-14
Citadel assessment breakdown screen

### FE-15
Dependency graph screen

### FE-16
Recovery readiness screen

### FE-17
Disaster simulation screen

### FE-18
Inheritance readiness screen

### FE-19
Repair plan screen

### FE-20
Policy maturity / gaps screen

## UX constraints
- show severity, confidence, freshness, and explainability
- no fabricated metrics
- surface synthetic/baseline outputs honestly when backend marks them as such
- operator actions must remain clear and auditable