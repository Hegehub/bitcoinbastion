# Reflex Safety Copy Rules

## Required safety copy

- Advisory-only.
- Not legal verification.
- Not Bitcoin consensus proof.
- No custody.
- Public Bitcoin addresses only.
- Never enter seed phrases, private keys, wallet files or signing material.

## Forbidden wording

The Reflex frontend must not use stigmatizing or certainty-implying address/payment labels. Forbidden phrase fixtures are kept only inside explicit tests.

## Allowed alternatives

Use advisory-only, manual review recommended, limited evidence, provider disagreement, insufficient evidence, elevated risk band, low confidence, not legal verification, not Bitcoin consensus proof, no custody, degraded data, stale data, and fallback mode.

## Trace wording rules

Trace accepts public Bitcoin addresses only and must never ask for wallet secrets. Trace outputs are advisory and not legal verification or Bitcoin consensus proof.

## Market wording rules

Market intelligence is informational only and not financial advice. Historical similarity is contextual, not predictive certainty.

## Treasury wording rules

Treasury-related UI must remain draft/review/approval-based and must not sign, broadcast, or execute transactions.

## Degraded-state wording rules

Provider unavailable, stale data, fallback mode, and partial results must remain visible.

## Sensitive input rejection rules

Reject seed phrase-like input, mnemonic-like input, private-key-like input, xprv/yprv/zprv, wallet.dat, keystore, and signing material.
