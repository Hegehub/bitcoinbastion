# LNURL Withdraw Operations

## Operator warnings

Never manually retry an ambiguous LNURL-withdraw payout without first checking the Lightning provider or node payment state. A blind retry can produce a duplicate payout.

A refund request is not final until the Lightning payout is confirmed. Settled Lightning payments are not reversible by Bastion.

## Incident handling

Emergency lockdown blocks new valuable withdraw requests, QR exposure, callback acceptance for revoked requests, payout queue insertion, and blind retries. In-flight payments are marked for reconciliation and existing audit evidence remains readable.

## Reconciliation

Reconciliation can report matched settled, matched failed, still pending, provider/local mismatch, duplicate payment detected, amount mismatch, or manual investigation required. Mismatches should page operators and keep refund reservations until the state is known.

## Metrics and alerts

Track withdraw request counts, requested and approved amounts, denials, step-up, manual review, velocity rejections, invoice rejections, provider failures, payment-in-flight counts, and reconciliation mismatches. Recommended alerts include payout amount spikes, replay attempts, provider timeout increases, unexpected mainnet payout activity, and manual-review backlog.
