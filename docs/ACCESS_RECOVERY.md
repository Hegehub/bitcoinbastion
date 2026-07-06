# Access Recovery

Bastion Access Recovery allows you to regain control of your subscription entitlement if all devices are lost or compromised.  Recovery is **user‑controlled** and requires multiple factors.  Bastion support cannot unilaterally recover your pass, especially for Pro, Business or Enterprise tiers.

## Bastion Recovery Seed

When you first issue a certificate you may create a **Bastion Recovery Seed**, a list of human‑readable words (12 or 24).  This seed is *not* your Bitcoin wallet seed and cannot be used to derive Bitcoin private keys.  It is used solely to reconstruct your Bastion access entitlement during recovery.

- Lite, Basic and Plus plans use a 12‑word Bastion Recovery Seed.
- Pro, Business and Enterprise plans use a 24‑word Bastion Recovery Seed and may require additional hardware factors.

Store your recovery seed offline and never enter it into any software except the Bastion recovery flow.  Bastion will never ask for your Bitcoin wallet seed.

## Recovery quorum profiles

Recovery uses a threshold scheme.  You must supply `threshold` out of `total` factors.  The factors vary by plan:

- **Plus (optional 2‑of‑3):** Desktop Vault, Mobile Vault, 12‑word Bastion Recovery Seed.
- **Pro (2‑of‑3):** Desktop Vault, Mobile Vault, 24‑word Bastion Recovery Seed.
- **Business (2‑of‑3):** Owner Vault, Admin Vault, Business Recovery Seed.
- **Enterprise (3‑of‑5):** Owner Key, Admin Key, Hardware Key, 24‑word Seed, Offline Recovery Kit.

You may configure the vaults and hardware keys at issuance time.  The threshold cannot be reduced later.

## Cooldown and audit

- After a recovery attempt starts, a **cooldown period** (configured by `ACCESS_RECOVERY_COOLDOWN_SECONDS`, default 86400 seconds) prevents rapid successive attempts.  Each submitted factor logs an audit event.
- All recovery events are recorded on the audit chain.  Operators can review each factor submission and decision.

## Recovery process

1. **Setup** – After obtaining a certificate, call `POST /api/v1/access/recovery/setup` to generate a recovery phrase.  Write it down and confirm.
2. **Start** – When devices are lost, call `POST /api/v1/access/recovery/start` with your pass lookup hash and declared plan code.  The server returns the required factors and threshold and sets a cooldown.
3. **Submit factors** – Call `POST /api/v1/access/recovery/factors` repeatedly with each factor.  Factor types include `recovery_seed`, `vault_signature`, `hardware_key`, etc.
4. **Status** – Use `GET /api/v1/access/recovery/status/{recovery_attempt_id}` to track progress.  The server indicates how many factors have been verified and whether quorum is met.
5. **Complete** – Once the threshold is satisfied, call `POST /api/v1/access/recovery/complete` with a new device public key to rotate your certificate.  Optionally revoke old sessions.
6. **Rotate** – Use `POST /api/v1/access/recovery/rotate` to rotate the recovery seed after recovery is completed.

If you decide to abort, you may call `POST /api/v1/access/recovery/cancel`.

## Support boundaries

- **Bastion Recovery Seed is not your Bitcoin wallet seed.**  Never enter your Bitcoin seed into Bastion.
- Support will **never ask** for your Bastion Recovery Seed, device private keys or wallet seeds.
- Recovery must never be easier than login.  High‑tier plans (Pro/Business/Enterprise) always require multiple factors.
- Support cannot unilaterally recover Pro, Business or Enterprise passes; only the designated quorum can do so.
- If you lose your Bastion Recovery Seed and all devices, recovery may be impossible for high‑tier passes.  Keep the seed safe.
- Beware of phishing.  Bastion will only ask you to enter the recovery seed into the Bastion recovery UI, never through chat or email.
