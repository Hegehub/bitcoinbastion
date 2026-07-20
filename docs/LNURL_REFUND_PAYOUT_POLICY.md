# LNURL Refund and Payout Policy

LNURL-withdraw is a payout transport. A valid withdraw `k1`, callback, or wallet invoice is not authorization to move funds. Bastion evaluates policy before request creation, before withdraw exposure, after invoice callback verification, and immediately before payment execution.

Supported purpose classes include subscription refunds, PayRegister refunds, merchant refunds, cashback/customer rewards, partner and affiliate payouts, operator rewards, bug bounty payouts, business expense reimbursements, and explicitly separated testnet/signet faucets. Faucet policy must never be reused for mainnet payouts.

Actors are scoped operational principals: wallet or Lightning principals, business owners/admins/operators, cashiers, PayRegister devices, partner principals, bug bounty reviewers, and system jobs. Cashiers may initiate scoped PayRegister refund flows but cannot approve high-value refunds; PayRegister devices cannot approve owner-level payouts; system jobs may execute only previously approved payouts.

The policy service uses the central `AccessPolicyEngine` plus LNURL-specific checks for original-payment linkage, refund remainders, step-up freshness, quorum, revocation, lockdown, amount/velocity limits, idempotent execution IDs, duplicate payment-hash commitments, and no-custody executor boundaries.

Refunds must reference an original settled payment proof or equivalent hashed payment evidence. Cumulative partial refunds cannot exceed the original settled amount, duplicate full refunds are rejected, unrelated workspace/store/principal contexts fail closed, and `commentAllowed` or `payerData` cannot establish refund ownership.

Production payment execution is behind an `LNURLPayoutExecutor` interface. The disabled implementation returns `executor_unavailable`; the fake executor is only for controlled tests. Bastion does not store merchant seeds, node private keys, macaroon/admin credentials in payout policy records, or sign Bitcoin transactions in this layer.
