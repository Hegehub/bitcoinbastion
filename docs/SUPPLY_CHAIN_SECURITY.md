# Supply Chain Security (K8S-3)

## Scope
This layer adds SBOM, vulnerability scanning, image signing, provenance, immutable digest deployment, and admission-policy examples.

## CI artifacts
- `artifacts/sbom.spdx.json`
- `artifacts/vulnerability_report.json`
- `artifacts/pip_audit_report.json`
- `artifacts/provenance.json`

## Signing
- Keyless signing is supported via GitHub OIDC in `.github/workflows/container-security.yml`.
- Optional key-based verification policy is represented in `deploy/kubernetes/security/cosign-policy.example.yaml`.
- Do not commit private signing keys.

## Verification
```bash
cosign verify --certificate-oidc-issuer https://token.actions.githubusercontent.com --certificate-identity-regexp '.*' ghcr.io/your-org/bitcoin-bastion@sha256:<digest>
```

## Vulnerability policy
- CI fails on CRITICAL findings from Trivy output.
- HIGH findings are surfaced for security review and tracked explicitly.
- No silent suppression; allowlisting requires explicit reason in repository policy/process.
