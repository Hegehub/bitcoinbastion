# Kubernetes Runtime Security and Cluster Hardening

## Controls added
- RBAC least-privilege service accounts and bindings.
- Pod Security Admission restricted labels.
- Egress-restricted and emergency-lockdown NetworkPolicies.
- Falco runtime detection rule examples.
- Secret leakage scan job example.
- kube-bench / kube-score / polaris validation notes.

## Emergency lockdown mode
Apply `deploy/kubernetes/security/emergency-lockdown-networkpolicy.yaml` during incident containment.
Revert after containment and verification.

## Validation evidence
Attach outputs for:
- Falco alerts test
- kube-bench report
- kube-score report
- polaris audit
- secret leakage scan report
