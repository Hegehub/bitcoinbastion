# Security policy layer

- `external-secret.example.yaml` is vendor-neutral: configure your `ClusterSecretStore` for Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, 1Password, or Doppler.
- Kyverno policies are examples and can run in `Audit` mode first, then move to `Enforce` after validation.
- No real credentials are committed.

- Add `kyverno-require-image-digests.yaml` to enforce digest-pinned images in production.
- Add `kyverno-require-signed-images.example.yaml` for keyless image-signature verification via Cosign/Sigstore.
- `cosign-policy.example.yaml` documents signing verification and rotation policy.

## Runtime security and hardening
- `rbac-least-privilege.yaml`: split service accounts and least-privilege bindings.
- `pod-security-namespace-labels.yaml`: PSA restricted labels.
- `networkpolicy-egress-restricted.yaml`: default egress restriction profile.
- `emergency-lockdown-networkpolicy.yaml`: incident-mode lockdown template.
- `falco-rules-bitcoin-bastion.example.yaml`: runtime detection examples.
- `kube-bench-job.example.yaml`, `kube-score-notes.md`, `polaris-notes.md`: cluster hardening validation references.
- `secret-leakage-scan-job.example.yaml`: leakage scan example job.
