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

    original_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = original_openapi()
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        security_schemes["BastionProofOfAccessSession"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Session",
            "description": PROOF_OF_ACCESS_HEADER_DESCRIPTION,
        }
        security_schemes["BastionProofOfAccessSignature"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Signature",
            "description": "Per-request Proof-of-Possession signature over method, path, body hash, timestamp, and nonce.",
        }
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
