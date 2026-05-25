# Frontend Deployment Guide

## Topology

- **Frontend**: Next.js on Vercel (recommended).
- **Backend**: FastAPI on VPS, Fly.io, Render, Railway, or Kubernetes.

## Frontend on Vercel

1. Create a Vercel project with root directory `frontend`.
2. Ensure build command is `npm run build`.
3. Ensure output is Next.js default.
4. Configure environment variables:
   - `NEXT_PUBLIC_API_BASE_URL`

## Backend deployment options

### VPS
- Run FastAPI behind Nginx/Caddy with TLS.

### Fly / Render / Railway
- Deploy containerized API and expose HTTPS endpoint.

### Kubernetes
- Expose via ingress with TLS and controlled CORS origins.

## CORS setup

Backend must set `CORS_ALLOW_ORIGINS` to explicit domains only.

Examples:

- Local frontend:
  - `CORS_ALLOW_ORIGINS=http://localhost:3000`
- Vercel preview + production:
  - `CORS_ALLOW_ORIGINS=https://bitcoinbastion.vercel.app,https://www.bitcoinbastion.org`
- Custom production domain:
  - `CORS_ALLOW_ORIGINS=https://bitcoinbastion.org,https://www.bitcoinbastion.org`

Do not use `*` in production.

## Environment variables

### Frontend
- `NEXT_PUBLIC_API_BASE_URL`

### Backend
- `CORS_ALLOW_ORIGINS`
- Existing backend runtime variables (database, redis, auth, etc.)

## Preview deployments

- Enable automatic preview deploys on pull requests.
- Point preview frontend to a staging backend or a controlled public API mock backend.
- Verify fallback behaviors still communicate degraded/unknown backend status clearly.

## Production checklist

- [ ] Frontend deploy succeeds on Vercel.
- [ ] Backend API reachable over HTTPS.
- [ ] `NEXT_PUBLIC_API_BASE_URL` points to production API origin.
- [ ] Backend `CORS_ALLOW_ORIGINS` contains production frontend domain(s).
- [ ] No wildcard CORS in production.
- [ ] Robots/sitemap URLs match production domain.
- [ ] Smoke tests pass (`/`, `/status`, `/evidence`, `/self-host`).
