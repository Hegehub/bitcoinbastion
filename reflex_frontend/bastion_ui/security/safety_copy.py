from __future__ import annotations

ADVISORY_ONLY = "Advisory-only."
NOT_LEGAL_VERIFICATION = "Not legal verification."
NOT_CONSENSUS_PROOF = "Not Bitcoin consensus proof."
NO_CUSTODY = "No custody."
PUBLIC_ADDRESSES_ONLY = "Public Bitcoin addresses only."
NEVER_ENTER_SENSITIVE_MATERIAL = (
    "Never enter seed phrases, private keys, wallet files or signing material."
)
DEGRADED_DATA = "Degraded data may be delayed, incomplete, or unavailable."
STALE_DATA = "Stale data is visible and must be reviewed before action."
PROVIDER_DISAGREEMENT = "Provider disagreement requires manual review."
LOW_CONFIDENCE = "Low confidence: use independent verification."
MANUAL_REVIEW_RECOMMENDED = "Manual review recommended."
TRACE_PUBLIC_SAFETY_COPY = (
    f"{ADVISORY_ONLY} {NOT_LEGAL_VERIFICATION} {NOT_CONSENSUS_PROOF} "
    f"{NO_CUSTODY} {PUBLIC_ADDRESSES_ONLY} {NEVER_ENTER_SENSITIVE_MATERIAL}"
)
SENSITIVE_INPUT_ERROR = (
    "This interface accepts public Bitcoin addresses only. "
    "Never enter seed phrases, private keys, wallet files or signing material."
)
MARKET_SAFETY_COPY = (
    "Market intelligence is informational only and is not financial advice. "
    "Signals may be stale, incomplete, degraded, or wrong."
)
POLICY_REVIEW_COPY = (
    "Policy simulation is advisory. Human operator review is required before action."
)
