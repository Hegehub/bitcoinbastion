# Security Hardening

Bitcoin Bastion applies a security‑hardened baseline but operators must take additional steps for production deployments.

- **HTTP headers and CSP** – Middleware sets strict content security policies and security headers. Operators may need to adjust CSP for custom domains.
- **Rate limiting** – Baseline rate limiting is enforced but should be complemented by infrastructure‑level throttling and WAF rules.
- **Proof‑of‑Access enforcement** – Premium endpoints enforce Proof‑of‑Access sessions and per‑request signatures. Frontend and SDKs must include the required headers.
- **No custody** – The platform does not custody funds or Bitcoin seeds. Never store wallet private keys or raw Access Pass values in logs or metrics.
- **Penetration testing** – Production deployments require penetration testing, code review and ongoing security audits. The security baseline does not replace a full audit.
