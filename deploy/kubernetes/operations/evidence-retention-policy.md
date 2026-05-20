# Evidence retention policy
Retain: release, migration, schema parity, backup/restore, incident, drill, vulnerability scan, SBOM/provenance evidence.
- Suggested retention: 12 months (minimum), with critical incident evidence longer per policy.
- Storage options: object storage, WORM archive, internal artifact registry.
- Recommend checksums/signatures for integrity.
- Restrict access by role; redact secrets/tokens/PII.
