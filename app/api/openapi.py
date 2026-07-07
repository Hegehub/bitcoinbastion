from typing import Any

from fastapi import FastAPI


PROOF_OF_ACCESS_HEADER_DESCRIPTION = (
    "Bitcoin Bastion uses Proof-of-Access authorization for protected APIs. "
    "Legacy email/password authentication is disabled. Provide X-Bastion-Session, "
    "X-Bastion-Timestamp, X-Bastion-Nonce, X-Bastion-Body-Hash, and "
    "X-Bastion-Signature for signed protected requests. Authorization: Bearer is not "
    "accepted as Proof-of-Access."
)


def apply_openapi_defaults(app: FastAPI) -> None:
    app.openapi_tags = [
        {"name": "public", "description": "Public presentation-safe endpoints"},
        {"name": "trace", "description": "Bastion Trace advisory endpoints"},
        {"name": "access", "description": PROOF_OF_ACCESS_HEADER_DESCRIPTION},
    ]
