# Mining Data Quality Labels Standard (M0-04)

Date: **2026-05-16**  
Status: **Draft standard (documentation-only)**

## Purpose
Define a mandatory, uniform labeling standard for Mining Sovereignty outputs so downstream consumers can interpret quality, trust boundaries, and uncertainty consistently.

All mining outputs are **advisory by default** unless explicitly marked verified through approved evidence workflows.

---

## 1) Required labels (mandatory on every mining output)

Each mining output must include the following fields:

1. `source_type`
   - Allowed values: `real`, `fallback`, `synthetic`, `unknown`
   - Meaning:
     - `real`: derived from direct telemetry/data collection path
     - `fallback`: derived from degraded/backup logic
     - `synthetic`: simulated or heuristic-generated
     - `unknown`: source quality cannot be confidently classified

2. `provider_name`
   - String identifier for upstream provider/adapter source.
   - If multiple providers are used, include the dominant provider and list others in `limitations`.

3. `is_verified`
   - Boolean.
   - `true` only when verification workflow and auditable evidence refs are present.

4. `is_fallback`
   - Boolean.
   - `true` when data path used fallback/degraded logic.

5. `is_synthetic`
   - Boolean.
   - `true` when value is simulated/heuristic or generated without direct telemetry.

6. `freshness`
   - Object containing at minimum:
     - `observed_at` (timestamp)
     - `age_seconds` (integer)
     - `freshness_band` (`fresh`, `stale`, `expired`, `unknown`)

7. `confidence`
   - Float in `[0.0, 1.0]`.
   - Must be accompanied by confidence-model rationale (see section 3).

8. `limitations`
   - Non-empty list of caveats and known blind spots.

9. `evidence_refs`
   - List of traceable references (IDs/URIs/hashes) used to derive the output.
   - May be empty only when `source_type` is `synthetic` or `unknown`; this must be explained in `limitations`.

---

## 2) Mining capability states

Every capability status field in mining outputs must use one of the following states:

- `supported`
- `unsupported`
- `partial`
- `unknown`
- `claimed_unverified`
- `verified`

### State semantics
- `supported`: evidence indicates capability is present, but verification may still be incomplete.
- `unsupported`: evidence indicates capability is absent.
- `partial`: capability appears present in limited or non-uniform scope.
- `unknown`: insufficient or conflicting evidence.
- `claimed_unverified`: capability is claimed (e.g., self-reported) but not independently verified.
- `verified`: capability is independently validated and traceably evidenced.

### State transition guardrail
- `claimed_unverified` must **not** be auto-promoted to `verified` without explicit verification artifacts in `evidence_refs`.

---

## 3) Confidence model (required)

Confidence must be computed as an advisory quality metric and documented per output type.

## 3.1 Base formula (reference)
`confidence = clamp01(source_quality_weight * freshness_weight * evidence_weight * consistency_weight)`

Recommended factor ranges:
- `source_quality_weight`
  - `real`: 0.75–1.00
  - `fallback`: 0.35–0.70
  - `synthetic`: 0.10–0.45
  - `unknown`: 0.05–0.40
- `freshness_weight`
  - `fresh`: 0.85–1.00
  - `stale`: 0.45–0.84
  - `expired`: 0.10–0.44
  - `unknown`: 0.20–0.50
- `evidence_weight`: 0.10–1.00 (quantity + quality of evidence refs)
- `consistency_weight`: 0.20–1.00 (cross-source agreement and variance checks)

## 3.2 Confidence interpretation bands
- `0.85–1.00`: high advisory confidence
- `0.60–0.84`: moderate advisory confidence
- `0.35–0.59`: low advisory confidence
- `0.00–0.34`: very low advisory confidence

Important: even “high” is advisory unless `is_verified=true`.

---

## 4) Production-grade gating rules

Fallback or synthetic outputs cannot appear as production-grade.

Mandatory gating:
1. If `is_fallback=true` OR `is_synthetic=true`, output must be labeled **ADVISORY**.
2. If `source_type in {fallback, synthetic, unknown}`, output cannot carry `verified` capability state.
3. If `is_verified=true`, then all must be true:
   - `source_type == real`
   - `is_fallback == false`
   - `is_synthetic == false`
   - `evidence_refs` non-empty and auditable
4. If gating fails, force downgrade:
   - `is_verified=false`
   - capability state downgraded to `claimed_unverified` or `unknown`
   - append limitation note describing downgrade reason

---

## 5) Canonical output envelope fragment (example)

```json
{
  "source_type": "real",
  "provider_name": "example_provider",
  "is_verified": false,
  "is_fallback": false,
  "is_synthetic": false,
  "freshness": {
    "observed_at": "2026-05-16T00:00:00Z",
    "age_seconds": 120,
    "freshness_band": "fresh"
  },
  "confidence": 0.78,
  "limitations": [
    "Advisory signal based on partial telemetry coverage"
  ],
  "evidence_refs": [
    "provider:example_provider:dataset:abc123"
  ],
  "capability_state": "claimed_unverified"
}
```

---

## 6) Non-claim policy
- This label standard defines how outputs must be described.
- It does **not** claim these capabilities are fully implemented in production today.
- Any consumer UI/API must preserve advisory wording unless verification requirements are met.
