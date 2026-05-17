# SPEC — Bastion Mining Sovereignty Layer

Status: **Draft / Planning (M0-03)**  
Date: **2026-05-16**  
Classification: **Advisory intelligence specification (non-custodial, non-consensus authority)**

Implementation status note: **PLANNED / FOUNDATION SPEC** (not an implemented runtime feature set).

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



## 10) Deterministic Pool Sovereignty Score model (initial)

Status: **Initial deterministic advisory model (M0-05)**

### 10.1 Score range and intent
- `pool_sovereignty_score_100` is a deterministic score in **[0, 100]**.
- The score is **advisory only** and must not be treated as proof of decentralization, censorship absence, or protocol compliance.

### 10.2 Weighted factors (fixed initial weights)
The score uses the following factor weights (sum = 100):
1. Stratum V2 support: **20**
2. Job Declaration support: **25**
3. Miner-built block templates: **25**
4. Transaction policy transparency: **10**
5. Censorship/filtering history: **10**
6. Jurisdictional resilience: **5**
7. Open documentation / implementation transparency: **5**

### 10.3 Factor normalization
Each factor is normalized into `f_i` in **[0.0, 1.0]** using evidence-backed heuristics:
- `1.0` = strong positive evidence
- `0.5` = partial/mixed evidence
- `0.0` = strong negative evidence
- Unknown values must be handled via section 10.6 (no fabricated certainty)

### 10.4 Deterministic formula
Let weights `w_i` be the fixed integers above, and normalized factors `f_i`.

`raw_score_100 = sum(w_i * f_i)`

Because `sum(w_i)=100` and `f_i in [0,1]`, `raw_score_100` is naturally in `[0,100]`.

Rounded output:
- `pool_sovereignty_score_100 = round(raw_score_100, 2)`

### 10.5 Explainability requirements for score output
Every score output must include:
1. per-factor contribution list: `contribution_i = w_i * f_i`
2. factor-level evidence references
3. factor-level limitations/uncertainty notes
4. confidence impact summary for unknown/fallback/synthetic inputs
5. final score + confidence presented together

Minimum explainability payload fragment:
- `factors`: array of `{name, weight, normalized_value, contribution, source_type, evidence_refs, limitations}`
- `raw_score_100`
- `pool_sovereignty_score_100`
- `confidence_score`

### 10.6 Unknown/fallback/synthetic behavior (mandatory)
Unknown data must reduce confidence and must not fabricate certainty.

Rules:
1. If a factor has `unknown` evidence state:
   - set `f_i = 0.5` (neutral placeholder), and
   - apply confidence penalty for that factor.
2. If a factor uses `fallback` source:
   - compute `f_i` normally if possible,
   - reduce confidence using fallback penalty,
   - add explicit limitation note.
3. If a factor uses `synthetic` source:
   - compute `f_i` only for advisory simulation,
   - apply stronger confidence penalty,
   - never mark capability state as `verified` from this factor alone.
4. If critical factors (Job Declaration or Miner-built templates) are unknown, score remains calculable but confidence must be capped at moderate-or-lower band.

Recommended confidence cap logic:
- any `synthetic` critical factor -> `confidence_score <= 0.59`
- both critical factors unknown -> `confidence_score <= 0.59`
- three or more unknown factors total -> `confidence_score <= 0.59`

### 10.7 Confidence coupling (advisory)
The numerical score and confidence are separate outputs:
- Score answers: “where does this pool land on the current deterministic rubric?”
- Confidence answers: “how trustworthy is this score given source quality/freshness/evidence?”

Consumer rule:
- Low confidence must be displayed prominently and must suppress strong recommendation language.

### 10.8 Non-overclaim policy for this model
- This model is an initial deterministic rubric for advisory monitoring, not a definitive sovereignty truth function.
- High score with low confidence is not a production-grade trust signal.
- Verified claims require auditable evidence and must respect data-quality gating rules in `docs/MINING_DATA_QUALITY_LABELS.md`.


## 11) Deterministic v1 model — Mining Censorship Risk

Status: **Initial deterministic advisory model (M0-06)**

### 11.1 Intent and output
- `mining_censorship_risk_score_100` is a deterministic advisory score in **[0, 100]**.
- Output `mining_censorship_risk_level` must be one of:
  - `low`, `medium`, `high`, `critical`, `unknown`
- This model does **not** prove censorship; it estimates risk posture from available evidence.

### 11.2 Deterministic risk factors (v1)
Each factor is normalized as risk intensity `r_i` in `[0.0, 1.0]`:
- `0.0` = no observed risk signal
- `0.5` = partial/ambiguous risk signal
- `1.0` = strong risk signal

Required factors:
1. pool-dominant block construction
2. no Job Declaration
3. no miner template control
4. unclear transaction filtering policy
5. jurisdictional pressure exposure
6. hashrate concentration
7. opaque operational policy
8. history of filtering/censorship claims

### 11.3 Fixed weights (sum=100)
- pool-dominant block construction: **18**
- no Job Declaration: **14**
- no miner template control: **16**
- unclear transaction filtering policy: **12**
- jurisdictional pressure exposure: **10**
- hashrate concentration: **12**
- opaque operational policy: **8**
- history of filtering/censorship claims: **10**

### 11.4 Formula
Let each factor be `r_i in [0,1]` and weight `w_i` from section 11.3.

`raw_risk_score_100 = sum(w_i * r_i)`

Rounded output:
- `mining_censorship_risk_score_100 = round(raw_risk_score_100, 2)`

Because weights sum to 100, score remains bounded in `[0,100]`.

### 11.5 Risk level mapping
- `low`: `0.00 <= score < 25.00`
- `medium`: `25.00 <= score < 50.00`
- `high`: `50.00 <= score < 75.00`
- `critical`: `75.00 <= score <= 100.00`
- `unknown`: insufficient evidence coverage to classify reliably (see section 11.7)

### 11.6 Explainability fields (mandatory)
Each censorship-risk output must include:
- `mining_censorship_risk_score_100`
- `mining_censorship_risk_level`
- `confidence_score`
- `factor_breakdown`: list of
  - `factor_key`
  - `weight`
  - `normalized_risk_value`
  - `contribution`
  - `source_type`
  - `provider_name`
  - `is_fallback`
  - `is_synthetic`
  - `evidence_refs`
  - `limitations`
- `coverage_summary`:
  - `known_factors`
  - `unknown_factors`
  - `coverage_ratio`
- `disclaimer`: explicit advisory/non-proof statement

### 11.7 Unknown/fallback/synthetic rules
Unknown data must reduce confidence and must not fabricate certainty.

Rules:
1. Unknown factor handling:
   - set `r_i = 0.5` (neutral-risk placeholder)
   - apply confidence penalty per unknown factor
2. Fallback factor handling:
   - allow scoring with observed fallback value
   - apply fallback confidence penalty
   - append limitation on degraded data path
3. Synthetic factor handling:
   - scoring allowed only for advisory scenario support
   - apply stronger confidence penalty than fallback
   - synthetic-only evidence cannot promote risk claims to verified status
4. Unknown risk level trigger:
   - if `coverage_ratio < 0.50`, set `mining_censorship_risk_level = unknown`
   - still return numerical score for operator context, but emphasize low confidence

### 11.8 Source quality and confidence coupling
Confidence must be coupled to source quality/freshness/evidence quality, not score value.

Mandatory coupling rules:
- Any critical factor with `source_type in {fallback, synthetic, unknown}` caps confidence to moderate-or-lower.
- If 3+ factors are unknown, confidence must be low-or-very-low.
- If synthetic contributes >30% of weighted contribution, confidence must not exceed 0.59.

Recommended caps:
- any synthetic critical factor -> `confidence_score <= 0.59`
- `coverage_ratio < 0.70` -> `confidence_score <= 0.69`
- `coverage_ratio < 0.50` -> `confidence_score <= 0.49`

### 11.9 Non-overclaim policy
- High/critical risk with low confidence must be labeled as tentative advisory risk.
- Low risk with low confidence must not be presented as censorship safety proof.
- Verified language is prohibited unless verification policy and auditable evidence requirements are met.


## 12) Template-Control Sovereignty Monitor model (v1)

Status: **Initial deterministic advisory model (M0-07)**

### 12.1 Path under observation
Monitored logical path:

`Bitcoin node → Template Provider → Job Declarator → Pool → ASIC`

This model evaluates who effectively controls block template construction/selection along that path and what risks are introduced at each hop.

### 12.2 Non-custodial and non-assumption constraints
- This model introduces **no custody assumptions** and does not infer asset custody state.
- It evaluates communication/control topology only.
- All outputs remain advisory unless verification requirements are satisfied.

### 12.3 Required evaluation dimensions
For each monitored mining profile/pool context, the model must evaluate:
1. miner uses own Bitcoin node
2. block template constructed locally
3. pool can replace template
4. channel encrypted
5. MITM risk
6. censorship risk
7. template-control owner

### 12.4 Template-control states (required)
`template_control_state` must be one of:
- `miner_controlled_verified`
- `miner_controlled_claimed_unverified`
- `shared_control_partial`
- `pool_controlled`
- `external_provider_controlled`
- `unknown`

State semantics:
- `miner_controlled_verified`: miner template authority is evidenced and independently verified.
- `miner_controlled_claimed_unverified`: miner control is claimed/signaled but not independently verified.
- `shared_control_partial`: template authority appears split by context/path or policy branch.
- `pool_controlled`: pool-side systems can deterministically override miner template intent.
- `external_provider_controlled`: control appears delegated upstream of pool to template-provider stack.
- `unknown`: evidence coverage is insufficient/conflicting.

### 12.5 Deterministic scoring surfaces
Two coupled outputs are required:
1. `template_sovereignty_score_100` in `[0,100]` (higher = stronger miner-side template sovereignty)
2. `template_interference_risk_score_100` in `[0,100]` (higher = stronger replacement/interference risk)

Model guidance:
- Miner-owned node + local template construction + encrypted channel + low MITM + no replacement capability should raise sovereignty score and reduce interference risk.
- Pool replacement capability, unclear control boundaries, or opaque policy should reduce sovereignty score and raise interference risk.

### 12.6 Deterministic risk semantics
Risk labels for template-control monitoring:
- `low`: topology indicates strong miner-side template agency with low replacement/interference signals.
- `medium`: mixed control signals or moderate uncertainty.
- `high`: strong pool/provider override or multiple unresolved control weaknesses.
- `critical`: persistent override dominance with additional MITM/censorship risk indicators.
- `unknown`: insufficient data coverage or conflicting evidence.

### 12.7 MITM and channel semantics
Required channel/transport fields:
- `channel_encryption_state` in `{verified_encrypted, claimed_encrypted_unverified, unencrypted_or_unknown}`
- `mitm_risk_level` in `{low, medium, high, unknown}`

Rules:
- `claimed_encrypted_unverified` must not be treated as equivalent to `verified_encrypted`.
- If encryption state is unknown or unverified and path includes third-party relay/translator behavior, MITM risk cannot be lower than medium without strong counter-evidence.

### 12.8 Template-control owner semantics
`template_control_owner` must be one of:
- `miner`
- `pool`
- `template_provider`
- `shared`
- `unknown`

Owner classification must include explainability evidence and limitations describing why ownership was inferred.

### 12.9 Explainability requirements (mandatory)
Each template-control output must include:
- `path_observation`: status for each hop (`node`, `template_provider`, `job_declarator`, `pool`, `asic`)
- `template_control_state`
- `template_control_owner`
- `template_sovereignty_score_100`
- `template_interference_risk_score_100`
- `mitm_risk_level`
- `censorship_risk_linkage` (how template-control posture influences censorship-risk model)
- `source_quality_labels` (per M0-04 standard)
- `evidence_refs`
- `limitations`

### 12.10 Unknown/fallback/synthetic handling
- Unknown path segments must reduce confidence and can force `template_control_state=unknown` when coverage is inadequate.
- Fallback/synthetic observations may support advisory outputs but must not be presented as verified topology control evidence.
- Any high-confidence claim about miner-controlled templates requires non-fallback, non-synthetic evidence on control-critical hops.


## 13) Mining sovereignty signal taxonomy (M0-08)

Status: **Planned taxonomy and rules (advisory)**

### 13.1 Signal types (required)
The Mining Sovereignty layer must emit the following signal types:
1. `MINING_SOVEREIGNTY`
2. `POOL_CENSORSHIP_RISK`
3. `STRATUM_V2_ADOPTION`
4. `HASHRATE_CENTRALIZATION`
5. `TEMPLATE_CONTROL_RISK`
6. `MINING_PROVIDER_DEGRADATION`

### 13.2 Common signal contract
Each signal must include:
- `signal_type`
- `severity` in `{low, medium, high, critical, unknown}`
- `confidence_score` in `[0.0, 1.0]`
- `source_quality` block (`source_type`, `provider_name`, `is_fallback`, `is_synthetic`, `is_verified`)
- `freshness` block
- `limitations`
- `evidence_refs`
- `explainability`

All signals are advisory unless verification requirements are met.

### 13.3 Severity rules by signal type

#### A) `MINING_SOVEREIGNTY`
Primary input: `pool_sovereignty_score_100`.
- `low` risk signal if score `>= 75`
- `medium` if `>= 50 and < 75`
- `high` if `>= 25 and < 50`
- `critical` if `< 25`
- `unknown` if coverage inadequate (`coverage_ratio < 0.50`)

#### B) `POOL_CENSORSHIP_RISK`
Primary input: `mining_censorship_risk_score_100`.
- `low` if `< 25`
- `medium` if `>= 25 and < 50`
- `high` if `>= 50 and < 75`
- `critical` if `>= 75`
- `unknown` if evidence coverage insufficient/conflicting

#### C) `STRATUM_V2_ADOPTION`
Primary input: SV2 capability state and adoption coverage.
- `low` concern when adoption state is `verified` or broad supported coverage
- `medium` concern when state is `partial`/`claimed_unverified`
- `high` concern when state is mostly `unsupported`
- `critical` concern when unsupported + concentration indicators are elevated
- `unknown` when data is mostly unobserved

#### D) `HASHRATE_CENTRALIZATION`
Primary input: concentration metrics (e.g., top-N dominance).
- `low` if concentration pressure score `< 25`
- `medium` if `>= 25 and < 50`
- `high` if `>= 50 and < 75`
- `critical` if `>= 75`
- `unknown` on inadequate coverage

#### E) `TEMPLATE_CONTROL_RISK`
Primary input: template interference risk + control owner state.
- `low` when `template_interference_risk_score_100 < 25` and miner-controlled verified evidence exists
- `medium` when mixed/shared control
- `high` when pool/provider override indicators are strong
- `critical` when override dominance combines with MITM/censorship flags
- `unknown` when control path evidence is insufficient

#### F) `MINING_PROVIDER_DEGRADATION`
Primary input: provider health/degradation telemetry.
- `low` when provider freshness, reliability, and consistency are healthy
- `medium` when transient degradation exists
- `high` when sustained failures/fallback rates impact major factors
- `critical` when persistent degradation materially invalidates monitoring reliability
- `unknown` when provider diagnostics are unavailable

### 13.4 Confidence rules
Confidence must be source-quality-driven and not inferred from severity.

Mandatory rules:
1. Unknown factors reduce confidence.
2. Fallback/synthetic evidence applies penalties and caps confidence.
3. `severity=critical` with low confidence must be marked tentative.
4. `severity=low` with low confidence must not be shown as safety proof.
5. If `coverage_ratio < 0.50`, confidence should not exceed `0.49`.

Recommended caps:
- any control-critical synthetic input -> `confidence_score <= 0.59`
- 3+ unknown factors -> `confidence_score <= 0.59`
- provider degradation high/critical -> cap downstream mining signal confidence to moderate-or-lower

### 13.5 Explainability requirements
Each signal must include explainability with:
- `drivers`: top factor contributions
- `factor_breakdown`: per-factor weight/value/contribution
- `source_quality_impact`: how fallback/synthetic/unknown affected confidence
- `temporal_context`: window and trend direction
- `limitations`
- `evidence_refs`

If explainability is missing for high-impact signals (`high`/`critical`), signal must be downgraded or withheld.

### 13.6 Source quality requirements
Source quality must follow `docs/MINING_DATA_QUALITY_LABELS.md`:
- `source_type` required
- `provider_name` required
- `is_verified`, `is_fallback`, `is_synthetic` required
- `freshness`, `confidence`, `limitations`, `evidence_refs` required

Gating reminder:
- fallback/synthetic/unknown cannot produce verified-grade claims.
- claimed capability states remain `claimed_unverified` absent auditable evidence.

### 13.7 Integration with existing Signal Engine (planned)
Mining signals must integrate through existing Signal Engine patterns:
1. Mining services produce typed mining signal candidates.
2. Signal Engine ingests candidates via explicit source links.
3. Dedup uses (`signal_type`, canonical_source_key, window_start, window_end).
4. Explainability graph nodes/edges are attached at publish time.
5. Delivery pipeline (API/Telegram) uses standard envelope and severity/confidence display policy.

Boundary rule:
- Mining domain defines factor semantics; global cross-domain prioritization remains owned by Signal Engine/recommendation layers.

### 13.8 Example signals (advisory examples)

Example 1 — `POOL_CENSORSHIP_RISK`:
- `severity`: `high`
- `confidence_score`: `0.63`
- reason: elevated censorship-risk score with moderate source quality and partial unknowns

Example 2 — `TEMPLATE_CONTROL_RISK`:
- `severity`: `critical`
- `confidence_score`: `0.46`
- reason: pool override indicators + unverified channel encryption + fallback telemetry
- presentation requirement: marked tentative due to low confidence

Example 3 — `STRATUM_V2_ADOPTION`:
- `severity`: `medium`
- `confidence_score`: `0.58`
- reason: claimed adoption signals without independent verification artifacts


## 14) API contract draft for mining module (M0-09)

Status: **PLANNED** (these endpoints are contract drafts and are not declared implemented in this document).

### 14.1 Planned endpoints
- `GET /api/v1/mining/pools`
- `GET /api/v1/mining/pools/{pool_id}`
- `GET /api/v1/mining/stratum-v2/adoption`
- `GET /api/v1/mining/sovereignty-score`
- `GET /api/v1/mining/censorship-risk`
- `GET /api/v1/mining/template-control`
- `GET /api/v1/mining/signals`

### 14.2 Response envelope rule
All mining endpoints must return standard envelope contracts:
- success: `ResponseEnvelope[T]`
- error: standard error envelope with `code`, `message`, `request_id`

### 14.3 Explainability is mandatory
Each mining API response must include an `explainability` object with at minimum:
- `drivers`
- `factor_breakdown`
- `source_quality_impact`
- `limitations`
- `evidence_refs`

If explainability is unavailable for high-impact output, endpoint must return downgraded advisory output or an explicit unavailable state.

### 14.4 Planned endpoint-level contract highlights
1. `/mining/pools`:
   - paginated pool summaries with sovereignty and confidence metadata.
2. `/mining/pools/{pool_id}`:
   - single-pool detail including capability states, censorship risk, and template-control owner.
3. `/mining/stratum-v2/adoption`:
   - network + per-pool adoption posture with verification state visibility.
4. `/mining/sovereignty-score`:
   - deterministic score output with weighted factor breakdown.
5. `/mining/censorship-risk`:
   - deterministic risk score + risk level + factor contributions.
6. `/mining/template-control`:
   - topology/path observation, control state, owner classification, interference risk, MITM semantics.
7. `/mining/signals`:
   - paginated mining signal feed following M0-08 taxonomy.

### 14.5 Planned vs implemented clarity rule
- These routes are **planned contracts only** in M0.
- Runtime implementation status must be tracked in `docs/API_CONTRACTS.md` inventory before any route is considered implemented.


## 15) Persistence baseline status (M1)

Status label: **MODELS/PERSISTENCE BASELINE IMPLEMENTED**.

### What is implemented
- SQLAlchemy mining model set exists and is migration-backed.
- Repository persistence abstraction exists for pool/capability/score/risk/template/signal records.
- Schema parity checks include mining tables and surface mining drift context.

### What is not implied by this status
- This does not claim fully implemented mining provider ingestion.
- This does not claim production-grade live mining intelligence runtime.
- Planned mining API endpoints remain planned unless explicitly marked implemented in `docs/API_CONTRACTS.md`.

## 15.1 M2 Stratum V2 registry/service baseline (implemented)

Status label: **SERVICE BASELINE IMPLEMENTED**.

Implemented baseline behavior:
- Pool capability metadata upsert flow exists (resolve/create pool, endpoint attach where provided, capability persistence with practical idempotency).
- Stratum V2 capability evaluation and adoption summary service methods exist with explainability and confidence semantics.
- Celery refresh task baseline exists for manual/fixture capability refresh (`tasks.mining.refresh_stratum_v2_capabilities`).

Capability-state semantics:
- Allowed states: `supported`, `unsupported`, `partial`, `unknown`, `claimed_unverified`, `verified`.
- `claimed_unverified` and `verified` must never be collapsed into one bucket.
- `unknown` must not be counted as supported in adoption calculations.

Adoption-summary semantics:
- Required summary fields: `total_pools`, `sv2_supported_count`, `job_declaration_supported_count`,
  `template_control_supported_count`, `unknown_count`, `claimed_unverified_count`, `adoption_rate`,
  `confidence`, `limitations`, `explainability`.
- `adoption_rate` is advisory and must include confidence caveats/limitations.

Source-quality and evidence semantics:
- Source labeling is mandatory (`source_type`, verified/fallback/synthetic flags, confidence, freshness, limitations, evidence refs).
- Manual/fixture records must remain source-labeled and non-production-grade by policy.
- No active network probing is implemented in current baseline; verification-sensitive claims remain advisory unless evidence-backed.

### Source-quality and unknown/unverified semantics
- Persistence includes `source_type`, `is_verified`, `is_fallback`, `is_synthetic`, `confidence(_score)`, freshness/observed fields, limitations, and evidence refs.
- Unknown/unverified states are accepted and expected defaults for baseline records.

### Synthetic fixture warning
- Test fixtures under `tests/fixtures/mining.py` are synthetic and must never be represented as real-world pool intelligence.


## 16) Block M1 verification summary

### M1 completion statement
- Mining persistence foundation exists and is migration-backed.
- Repository abstraction and baseline schema contracts are in place.
- This is **not** full mining runtime completion.

### Verification outcomes
- Mining model tests: passed.
- Mining repository tests: passed.
- Migration smoke replay: passed.
- Runtime schema parity check: passed.
- Lint gate note: `make lint` currently reports pre-existing mypy failures outside mining scope; this does not alter mining-specific pass/fail of persistence verification.

### Next block reference
- **M2** is the next execution block for provider-connected read/runtime behavior and implementation of planned mining endpoint flows.

## 17) M2 completion verification snapshot (M2-10)

M2 block verification confirms:
- Stratum V2 capability registry service exists.
- adoption summary service exists.
- mining task baseline exists and is worker-discoverable.
- limitations and advisory semantics are explicitly documented.

Verification command outcomes (M2-10 run):
- `make lint`: Ruff passed; mypy failed due to pre-existing non-mining typing debt.
- `python -m pytest -q tests/unit/test_mining_pool_registry_service.py`: passed.
- `python -m pytest -q tests/unit/test_stratum_v2_capability_service.py`: passed.
- `python -m pytest -q tests/unit/test_mining_capability_upsert.py`: passed.
- `python -m pytest -q tests/unit/test_stratum_v2_adoption_summary.py`: passed.
- `python -m pytest -q tests/unit/test_mining_tasks.py`: passed.
