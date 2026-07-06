# Known Limitations

Bitcoin Bastion is a production‑candidate platform but still has known limitations:

- **Proof‑of‑Access crypto agility** – Post‑quantum signature schemes (`ML‑DSA`, `ML‑KEM`, `SLH‑DSA`) are reserved variables and not yet implemented. PQ variables must remain disabled until audited implementations are available.
- **Payment provider integration** – The BTCPay payment provider is optional and disabled by default. Only verified settled webhooks mark payment intents as paid. Other providers are not yet supported.
- **Manual grants** – Manual grants must remain disabled in production. Enabling `ACCESS_ALLOW_MANUAL_GRANTS` for non‑test environments undermines Proof‑of‑Access.
- **Offline validity packs** – Offline validity packs and delegated passes are planned but not implemented. Access always requires an online origin‑bound session.
- **Recovery UX** – Recovery flows are new and may require further refinement. Recovery seeds must be stored offline and cannot be recovered if lost. Recovery cannot bypass plan restrictions or cooldown periods.
- **Browser‑only approval** – Browser UI is an interface, not a root of trust. High‑impact actions require human‑intent signatures from approved devices and cannot be approved via a single click or browser‑only prompt.
- **No transaction signing** – The platform does not sign or broadcast Bitcoin transactions. Custody and transaction responsibilities remain with the user’s wallet software.
- **No legal or financial advice** – Market intelligence, risk scores and advisory outputs are informational and not a substitute for professional advice.
