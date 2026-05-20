# Emergency override policy
Manual production kubectl changes are break-glass only.
Every override must include incident ticket, operator name, timestamp, and rollback commit.
Reconcile back to Git within same incident window.
