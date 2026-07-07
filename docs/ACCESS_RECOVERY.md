# Access Recovery

Bastion recovery restores Access rights, not Bitcoin funds. Bastion Recovery Seed is not your Bitcoin wallet seed. Never enter your Bitcoin wallet seed into Bastion. Bastion will never ask for your Bitcoin private key or wallet seed.

Recovery must never be easier than login. Support cannot unilaterally recover Pro, Business, or Enterprise access.

## Recovery profiles

| Plan | Recovery profile |
| --- | --- |
| Lite | 12-word Bastion Recovery Seed with cooldown. |
| Basic | 12-word Bastion Recovery Seed with audit event and cooldown. |
| Plus | 12-word Bastion Recovery Seed; optional 2-of-3 with Desktop Vault, Mobile Vault, and 12-word Recovery Seed. |
| Pro | Required 2-of-3 with Desktop Vault, Mobile Vault, and 24-word Bastion Recovery Seed. |
| Business | Required 2-of-3 with Owner Vault, Admin Vault, and Business Recovery Seed. |
| Enterprise | Required 3-of-5 with Owner Key, Admin Key, Hardware Key, 24-word Seed, and Offline Recovery Kit. |

## Cooldown and audit

Recovery attempts are rate-limited, cooldown-bound, and audited. Audit events record hashes/fingerprints, decision, policy status, and timestamps; they must not record raw recovery phrases, raw shares, raw session tokens, raw Access Passes, private keys, or Bitcoin seed material.

## Support boundaries

Support can explain the process, confirm public docs, and help interpret structured errors. Support cannot ask for a Bitcoin seed, cannot ask for a Bastion Recovery Seed in plaintext, cannot bypass quorum, cannot bypass cooldown, and cannot unilaterally restore high-tier access. Enterprise recovery follows customer policy and issuer checks.

## Phishing warnings

- Do not scan QR codes that ask for a Bitcoin seed.
- Do not paste xprv, WIF, wallet.dat, or hardware-wallet secrets.
- Do not trust browser-only critical approval for recovery changes.
- Rotate recovery material after suspected compromise.
