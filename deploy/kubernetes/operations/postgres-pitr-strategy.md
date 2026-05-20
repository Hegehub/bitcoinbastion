# PostgreSQL PITR strategy (documented)
- WAL archiving with defined retention window.
- Restore to target timestamp.
- Options: managed DB PITR, self-hosted WAL archive, Kubernetes Postgres operator.
- Risks: archive gaps, clock skew, retention misconfiguration, long recovery windows.
- Required evidence: WAL retention proof, restore rehearsal logs, target-time restore validation.

Note: this repository documents PITR strategy; implementation is environment-dependent.
