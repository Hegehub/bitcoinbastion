# Frontend Architecture

Frontend foundation is baseline.

- Next.js App Router + TypeScript + Tailwind.
- Presentation-safe API consumption layer (`frontend/services/api.ts`).
- Layout/navigation shells for public and dashboard-like sections.
- Placeholder modules are intentionally marked as baseline/coming soon.

Frontend hardening baseline completed.
Production accessibility audit still pending unless fully executed.
Frontend E2E coverage is baseline unless full E2E suite exists.
Frontend does not custody funds or handle private keys.
Frontend does not sign or broadcast transactions.

## Market Time Machine UI

The backend-rendered Market Time Machine interface lives in `app/web/routes_market.py`, `app/web/view_models/market.py`, `app/web/templates/market/`, `app/web/templates/components/`, `app/web/static/js/market.js`, and `app/web/static/css/market.css`.

It follows the existing FastAPI/Jinja site model rather than introducing a separate standalone application. Static assets are mounted under `/static`.

Accessibility baseline:

- Keyboard-focusable chart, candles, markers, panels, and section navigation.
- Screen-reader labels for chart and marker controls.
- Responsive mobile collapse at narrow widths.
- High-contrast mode styling through `prefers-contrast`.

Safety baseline:

- Every page renders no-causation and evidence/degraded-provider disclosures.
- Missing evidence and operator review status remain visible.
