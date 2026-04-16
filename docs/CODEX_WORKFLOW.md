# CODEX WORKFLOW

This document defines the practical implementation workflow for Bitcoin Bastion when executing scoped coding tasks.

## 1. Task framing
Each task should include:
- Task ID
- Goal
- Allowed files
- Constraints (security, architecture, backward compatibility)
- Definition of Done

## 2. Execution sequence
1. Read relevant architecture and domain docs.
2. Confirm layer ownership (API vs service vs repository vs integration).
3. Implement smallest production-safe slice.
4. Add/adjust tests.
5. Run lint/type/test checks for touched scope.
6. Update docs if behavior/contracts changed.

## 3. Layer ownership rules
- API routes and bot handlers: transport only, no core business logic.
- Services: orchestration, scoring, policy, explainability, decision logic.
- Repositories: persistence and query concerns only.
- Integrations: external I/O with retries/timeouts.
- Tasks: scheduled/event-driven orchestration with idempotency in mind.

## 4. Quality gates per change
- Type hints for all new public functions/classes.
- Structured error envelopes for API changes.
- Explainability payload for any new score/recommendation.
- Audit logging for sensitive policy/treasury/admin actions.
- Tests for bugfixes and new business behavior.

## 5. PR expectations
PRs should be small and atomic where possible and include:
- concise architectural intent
- changed files summary
- backward-compatibility notes
- test commands + outcomes
- follow-up tasks for deferred scope

## 6. Anti-patterns to avoid
- Fat route handlers
- Hidden global state
- Hardcoded secrets
- Non-deterministic scoring without explanation
- Cross-layer leakage (repository calling integrations directly, etc.)
