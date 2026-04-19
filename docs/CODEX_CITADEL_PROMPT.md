# Codex Prompt — Citadel Implementation Mode

Implement Bitcoin Citadel as a focused domain extension within Bitcoin Bastion.

## Non-negotiables
- Keep FastAPI routes thin
- Keep logic in `services/citadel`
- Keep types strict in schemas
- Keep scoring/simulation deterministic and explainable
- Keep security sovereignty-first (no secret custody in system)

## Suggested first tasks
- CIT-01: `CitadelAssessment` model + `schemas/citadel.py`
- CIT-02: `CitadelScoreService` with deterministic breakdown
- CIT-03: `SovereigntyDependency` model + graph service baseline

## Completion output format
1. Architecture summary
2. Files changed
3. Code implementation notes
4. Tests
5. Verification commands
6. Next best task
