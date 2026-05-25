# Environment Variables

This repository uses environment-driven configuration; never commit real secrets.

## Core backend
- `APP_ENV` (dev/staging/production)
- `DEBUG` (`true`/`false`)
- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET_KEY`
- `CORS_ALLOW_ORIGINS` (comma-separated origins, never `*`)

## Frontend
- `NEXT_PUBLIC_API_BASE_URL` (public-safe base URL only)

## Notes
- Production should inject secrets from external secure tooling.
- `.env.example` must contain placeholders only.

## CORS production examples
- Local frontend: `CORS_ALLOW_ORIGINS=http://localhost:3000`
- Vercel frontend: `CORS_ALLOW_ORIGINS=https://bitcoin-bastion.vercel.app`
- Production domain: `CORS_ALLOW_ORIGINS=https://bitcoinbastion.org`
- Multiple environments: `CORS_ALLOW_ORIGINS=http://localhost:3000,https://bitcoin-bastion.vercel.app,https://bitcoinbastion.org`
