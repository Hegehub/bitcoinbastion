# Frontend Trace Flow

/check (and /trace alias) performs client-side validation first, then calls backend Lite API and public summary API.
It never sends rejected sensitive material.
It renders limitations and safety warnings by default.
