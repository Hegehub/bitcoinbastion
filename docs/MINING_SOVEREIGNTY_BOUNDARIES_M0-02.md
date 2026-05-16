# Mining Sovereignty Domain Boundaries (M0-02)

Date: **2026-05-16**  
Status: **Planning complete (responsibilities only)**

## Goal
Define module boundaries for the new Mining Sovereignty domain while preserving the modular monolith architecture and avoiding full implementation.

## Module responsibility map

### `app/domain/mining/`
Owns domain language and invariants for:
- hashrate/difficulty semantics
- pool concentration semantics
- production integrity semantics
- inclusion neutrality semantics

### `app/services/mining/`
Owns orchestration responsibilities:
- normalize provider payloads
- compute mining scorecard
- assemble explainability payloads
- publish signal-compatible inputs
- provide API-ready read models

### `app/integrations/mining/`
Owns provider adapter boundaries:
- telemetry collection contracts
- provenance/source quality metadata normalization
- provider-specific mapping isolation

### `app/api/v1/mining.py`
Owns mining API transport surface:
- thin route definitions only
- envelope-compatible response shape for future runtime endpoints
- no direct persistence/business logic

### `app/schemas/mining.py`
Owns request/response and internal mining contracts:
- snapshot payloads
- scorecard payloads
- explainability payload fragments

### `app/db/models/mining.py`
Planned ownership (deferred to M2):
- mining snapshots and scorecard persistence entities
- retention/indexing strategy attachment points

### `app/db/repositories/mining_repository.py`
Planned ownership (deferred to M2):
- persistence access patterns
- time-window querying
- latest-scorecard lookup

### `app/tasks/mining_tasks.py`
Planned ownership:
- scheduled telemetry refresh orchestration
- scorecard recomputation orchestration
- signal-input publication orchestration

## API surface proposal (planning)
- `GET /api/v1/mining/scorecard`
- `GET /api/v1/mining/hashrate`
- `GET /api/v1/mining/pools`
- `GET /api/v1/mining/production`
- `GET /api/v1/mining/inclusion`
- `GET /api/v1/mining/capabilities` (planning helper)

## Architecture constraints (explicit)
- No architecture rewrite.
- No full mining logic implementation in this task.
- No DB migration/table implementation in this task.
- Keep route -> service -> repository layering intact.
