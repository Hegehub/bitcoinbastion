# Prompt-0 Risk Register

| ID | Risk | Likelihood/impact | Gate, owner and rollback |
|---|---|---|---|
| R01 | Duplicate/unstable operation IDs break generation | high/high | G1, backend API owner; fail generation, no handwritten override |
| R02 | OpenAPI security extensions underdescribe dependency policy | high/critical | G6, Access/security; bind dependency tests before UI |
| R03 | Route/source-string tests overclaim parity | certain/high | G3/G13, frontend QA; matrix validator and browser request+DOM evidence |
| R04 | Existing clients never trigger or render | high/high | G4/G5; inverse mapping, delete/merge unused code only after evidence |
| R05 | Stale URL calls wrong service | high/high | generated URL allowlist; disable client method |
| R06 | Secrets leak through URL/storage/log/copy/share/fixture | medium/critical | G11, security; default deny, clear/revoke, negative tests |
| R07 | Bearer/password shortcut weakens PoA | medium/critical | G6; hard stop and revert slice |
| R08 | PayRegister leaks into core product/navigation | medium/high | G16; separate flag/route/owner, flag off |
| R09 | Callback/protocol endpoints become unsafe buttons | medium/critical | G2/G6; backend-owned dispositions |
| R10 | Stale/partial/synthetic data appears live | high/high | G7/G12; provenance union, unavailable fallback |
| R11 | WebSocket reconnect storms or hides staleness | medium/high | G12; bounded backoff/visibility pause/HTTP fallback |
| R12 | Glass/geometry harms contrast/performance | high/medium | G10/G13; solid/reduced/low-power fallback |
| R13 | Visualization dependency violates CSP/supply chain | medium/high | G14; no dependency until approved, vanilla/text fallback |
| R14 | Wow placeholders copied as production | high/high | G9; view-model-first extraction and retained compatibility route |
| R15 | Feature pack labels differ from undiscovered approved pack | high/medium | product owner reconcile labels without ID/count changes before Prompt 9 |
| R16 | Browser harness cannot force all status states | high/high | Prompt 7/13; no verified claim until deterministic interception exists |
| R17 | Future Temporal work displaces current runtime truth | low/high | G15; Celery stays canonical, optional backend adapter only |
| R18 | Documentation claims production readiness | medium/high | Prompt 52 revision-specific evidence or explicit limitation |
