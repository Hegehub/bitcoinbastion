# SPEC — Bastion Mining Sovereignty Layer

Status: **Draft / Planning (M0-03)**  
Date: **2026-05-16**  
Classification: **Advisory intelligence specification (non-custodial, non-consensus authority)**

---

## 1) Purpose
Define the product-level specification for a new Mining Sovereignty Layer in Bitcoin Bastion.

This layer provides **advisory intelligence** about mining centralization, template control, and censorship pressure.  
It does **not** claim protocol authority, consensus finality guarantees, or direct miner/pool control.

All outputs in this specification are **advisory unless independently verified by operator-controlled data sources**.

---

## 2) Product scope

### In scope
- Monitoring of mining sovereignty risk indicators.
- Stratum V2 posture awareness and trend tracking.
- Job Declaration capability tracking (where observable).
- Template Provider and Translator Proxy awareness.
- Encrypted channel support posture (where observable/inferred).
- Miner template control posture inference.
- Censorship risk analytics.
- Pool sovereignty scoring.
- Template sovereignty monitoring.
- Mining sovereignty signal generation for API/Telegram.
- Explainability-first output contracts.

### Out of scope (for this spec block)
- Enforcement actions on miners or pools.
- Claims of real-time global completeness.
- Guaranteed censorship attribution.
- Consensus-level truth claims.
- Autonomous policy execution without operator confirmation.

---

## 3) Core principles
1. **Advisory-first:** Every score and alert is advisory unless verified.
2. **Provenance required:** Every high-impact claim must carry evidence provenance.
3. **Uncertainty explicit:** Confidence, freshness, and limitations are mandatory.
4. **No architecture rewrite:** Integrates with existing modular monolith boundaries.
5. **Safety in wording:** Avoid language that implies deterministic censorship proof.

---

## 4) Capability requirements

## 4.1 Stratum V2 adoption monitoring
The system must maintain pool/network-level indicators for:
- declared Stratum V2 support status
- observed/announced rollout phase
- confidence in adoption signal
- timestamped freshness and provenance

Output requirement:
- `sv2_adoption_status` in `{unknown, not_observed, partial, broad}`
- advisory note when sourced from indirect/public telemetry

## 4.2 Job Declaration capability
The system must track whether a pool/mining stack appears to support Job Declaration-related workflows (directly observed or strongly evidenced).

Output requirement:
- `job_declaration_capability` in `{unknown, not_observed, signaled, evidenced}`
- explicit evidence-type metadata (`self_reported`, `measurement`, `third_party_report`)

## 4.3 Template Provider awareness
The system must identify template production posture:
- vertically integrated pool template control
- external template provider dependence (where visible)
- mixed/unknown template sourcing

Output requirement:
- `template_provider_mode` in `{integrated, externalized, mixed, unknown}`

## 4.4 Translator Proxy awareness
The system must track Translator Proxy presence/risk posture where data allows.

Output requirement:
- `translator_proxy_mode` in `{not_observed, observed, likely, unknown}`
- limitations note when evidence is inferential

## 4.5 Encrypted channel support
The system must surface encrypted transport posture signals associated with mining stack communications.

Output requirement:
- `encrypted_channel_support` in `{unknown, absent_signal, partial_signal, strong_signal}`
- confidence score + freshness

## 4.6 Miner template control
The system must estimate miner-side template agency (versus pure pool-side template control) based on available indicators.

Output requirement:
- `miner_template_control_score` in `[0.0, 1.0]` (advisory)
- mandatory explanation list of contributing factors

## 4.7 Censorship risk
The system must compute an advisory censorship-risk model using multi-factor inputs:
- inclusion delay anomalies
- concentration and template concentration factors
- policy/event evidence context
- uncertainty penalties for sparse data

Output requirement:
- `censorship_risk_score` in `[0.0, 1.0]`
- `censorship_risk_band` in `{low, elevated, high, critical}`
- explicit “not proof” disclaimer

## 4.8 Pool sovereignty score
The system must provide per-pool and aggregate sovereignty scoring.

Minimum factors:
- concentration contribution
- template sovereignty posture
- declared protocol modernization posture (incl. SV2 signals)
- evidence quality and freshness

Output requirement:
- `pool_sovereignty_score` in `[0.0, 1.0]`
- comparable factor breakdown with weights

## 4.9 Template sovereignty monitor
The system must monitor template-control centralization trends.

Output requirement:
- trend state `{improving, stable, degrading, unknown}`
- `template_sovereignty_pressure_score` in `[0.0, 1.0]`
- rolling-window explainability packet

## 4.10 Mining sovereignty signals
The system must publish mining-domain signals consumable by:
- API surfaces
- Signal engine integration
- Citadel/policy integration (advisory inputs)
- Telegram notifications

Output requirement:
- signal includes `severity`, `confidence`, `freshness`, `provenance`, and `limitations`

---

## 5) Telegram command requirements (planned)

User-facing planned commands:
- `/mining_status` — summary of current advisory mining sovereignty posture.
- `/mining_pools` — pool sovereignty scoreboard snapshot.
- `/mining_censorship` — latest censorship-risk indicators and caveats.
- `/mining_templates` — template sovereignty monitor output.

Admin-facing planned commands:
- `/admin_mining_refresh` — trigger mining telemetry refresh workflow.
- `/admin_mining_signals` — preview publishable mining signals and confidence.

Command response rules:
- Must include advisory disclaimer in high-impact outputs.
- Must include confidence/freshness/provenance blocks.
- Must avoid deterministic claims unless operator-verified.

---

## 6) Explainability requirements (mandatory)
Every high-impact mining output (score, band, alert, recommendation) must include:
1. **Inputs used** (features and source classes).
2. **Transform summary** (how inputs influenced result).
3. **Weights/factors** (or rank-ordered influence when exact weights unavailable).
4. **Confidence calculation basis**.
5. **Freshness window + staleness penalties**.
6. **Limitations and uncertainty notes**.
7. **Provenance references** (traceable source refs).

Release gate requirement:
- If explainability packet is missing for a high-impact mining claim, that output must be downgraded or withheld.

---

## 7) Data quality and verification policy

### Output labeling policy
- **ADVISORY**: default label for all mining outputs.
- **VERIFIED**: allowed only when backed by operator-approved verification workflow and auditable evidence.

### Minimum metadata per output
- `confidence_score` `[0.0, 1.0]`
- `freshness` (observed_at, age_seconds)
- `source_quality_class` in `{real, fallback, synthetic, unknown}`
- `limitations` list
- `verification_status` in `{advisory, verified}`

### No fake production claims
This specification makes no claim that the described capabilities are currently fully implemented in production.
Any UI/API copy based on this spec must avoid “guaranteed”, “proven”, or “complete coverage” wording unless verified evidence exists.

---

## 8) Integration constraints
- Preserve modular monolith boundaries (`api -> services -> repositories/integrations`).
- Mining domain outputs are inputs to Signals/Policy/Citadel, not authority overrides.
- Persistence and migrations are independent rollout concerns and not assumed by this spec.

---

## 9) Acceptance criteria
This spec is considered complete when:
1. All required capability areas in this document are represented in contracts/backlog.
2. Telegram and explainability requirements are mapped to implementation tasks.
3. Output labeling policy (`advisory` vs `verified`) is enforced in response contracts.
4. Documentation and APIs avoid unverified production claims.

