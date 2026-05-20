# Runtime Security Checklist
- [ ] Dedicated service accounts assigned (no default SA).
- [ ] Pod Security Admission labels enforced at restricted level.
- [ ] Egress restrictions validated.
- [ ] Emergency lockdown policy tested in staging.
- [ ] Falco rules loaded and alerting path verified.
- [ ] Secret leakage scan executed and archived.
- [ ] kube-bench, kube-score, and polaris outputs attached.
