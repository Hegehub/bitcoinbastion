# ML/analytics layer

Owns analytical models, scoring logic, evidence-aware intelligence, model evaluation, explainability and governance for analytical outputs.

Current canonical paths:

- `app/services/analytics/`
- `app/services/intelligence/`
- market/evidence analytics documentation under `docs/`

Migration rule: analytical signals must expose confidence, limitations, data provenance and degraded/fallback states.
