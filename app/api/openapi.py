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
        security_schemes["BastionHumanIntentSignature"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Intent-Signature",
            "description": "Human Intent Signature for critical actions such as policy changes, exports, delegated access, and lockdown changes.",
        }
        protected_prefixes = (
            "/api/v1/admin",
            "/api/v1/entities/watchlist",
            "/api/v1/metrics/",
            "/api/v1/observability",
            "/api/v1/operations",
            "/api/v1/operator",
            "/api/v1/plugins",
            "/api/v1/policy",
            "/api/v1/trace/business",
            "/api/v1/trace/enterprise",
            "/api/v1/treasury",
            "/api/v1/users",
            "/api/v1/wallet/profiles",
            "/api/v1/webhooks",
        )
        for path, operations in schema.get("paths", {}).items():
            if path.startswith(protected_prefixes):
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation.setdefault(
                            "security",
                            [
                                {"BastionProofOfAccessSession": []},
                                {"BastionProofOfAccessSignature": []},
                            ],
                        )
                        operation["x-proof-of-access-required"] = True
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
