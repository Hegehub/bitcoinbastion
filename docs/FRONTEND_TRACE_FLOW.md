# Frontend Trace Flow

`/check` and `/trace` perform client-side validation first, then call `/api/v1/trace/lite/{address}` and `/api/v1/public/trace/{report_id}/summary` through the frontend API client. They reject sensitive wallet material before submission and never request custody, signing, seed phrases, private keys, wallet files, or signing material.

`/trace/[reportId]` calls `/api/v1/public/trace/{report_id}/summary` and renders public-safe limitations, timeline context, advisory guidance, and unavailable/not-found states.

`/trace/[reportId]/proof-packet` calls `/api/v1/trace/report/{report_id}/proof-packet`. The page displays proof packets as unsigned application-level evidence summaries unless backend signing is explicitly implemented and configured. The page must always show: advisory-only, no custody, not legal verification, and not Bitcoin consensus proof.

Trace frontend routes are a baseline/production-foundation UI. They are not proof of production calibration, legal verification, or Bitcoin consensus validation.
