# Bitcoin Bastion Frontend

Production-oriented Next.js App Router frontend for Bitcoin Bastion.

## Local development

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Environment variables

Create `.env.local` in `frontend/`.

Required:

- `NEXT_PUBLIC_API_BASE_URL` — Base URL for the backend API (for example `http://localhost:8000` locally).

Reference:

- `frontend/.env.example`

## API base URL setup

Local backend:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

Staging/preview backend:

```env
NEXT_PUBLIC_API_BASE_URL=https://staging-api.example.com
```

Production backend:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.bitcoinbastion.org
```

The frontend is designed to build even when the backend is offline by using safe fallbacks for supported public views.

## Scripts

- `npm run dev` — start local dev server
- `npm run build` — production build
- `npm run start` — run production build locally
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript strict checking
- `npm run test` — Vitest test suite
- `npm run test:watch` — Vitest in watch mode
- `npm run test:e2e` — Playwright e2e tests
- `npm run test:e2e:ui` — Playwright UI mode
- `npm run format` — Prettier check

## Vercel deployment

1. Import the `frontend/` directory as the project root in Vercel.
2. Set `NEXT_PUBLIC_API_BASE_URL` in Vercel Environment Variables for Preview and Production.
3. Deploy on every push/PR.
4. Validate `status`, `evidence`, and `self-host` pages in preview.

## Backend deployment assumptions

- Backend exposes FastAPI routes under `/api/v1/*`.
- CORS is configured with explicit allowlist via `CORS_ALLOW_ORIGINS` (no wildcard).
- Public endpoints are reachable from the internet for production frontend usage.
- Backend health and public status endpoints are available:
  - `/api/v1/health`
  - `/api/v1/health/live`
  - `/api/v1/health/ready`
  - `/api/v1/public/status`
  - `/api/v1/public/stats`
