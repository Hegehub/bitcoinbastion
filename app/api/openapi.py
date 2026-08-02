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
        {
            "name": "wallet-auth",
            "description": (
                "Wallet-first authentication. Bastion never requests a Bitcoin seed or private "
                "key. Wallet signatures prove wallet control only; protected access requires a "
                "Device-bound PoP Session, entitlement, revocation checks, and Policy Engine allow."
            ),
        },
        {
            "name": "LNURL Auth",
            "description": "LNURL-auth proves control of a domain-specific Lightning linking key; it is not unrestricted Bastion access.",
        },
        {"name": "LNURL Pay", "description": "Invoice issuance is not settlement or entitlement issuance."},
        {"name": "LNURL Withdraw", "description": "Policy-gated, short-lived payout capabilities."},
    ]

    original_openapi = app.openapi

    def custom_openapi() -> dict[str, Any]:
        if app.openapi_schema:
            return app.openapi_schema
        schema = original_openapi()
        components = schema.setdefault("components", {})
        security_schemes = components.setdefault("securitySchemes", {})
        pop_session_scheme = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Session",
            "description": PROOF_OF_ACCESS_HEADER_DESCRIPTION,
        }
        request_signature_scheme = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Signature",
            "description": "Per-request Proof-of-Possession signature over method, path, body hash, timestamp, and nonce.",
        }
        security_schemes["BastionProofOfAccessSession"] = pop_session_scheme
        security_schemes["BastionProofOfAccessSignature"] = request_signature_scheme
        security_schemes["BastionPoPSession"] = pop_session_scheme
        security_schemes["BastionRequestSignature"] = request_signature_scheme
        security_schemes["BastionHumanIntentSignature"] = {
            "type": "apiKey",
            "in": "header",
            "name": "X-Bastion-Intent-Signature",
            "description": "Human Intent Signature for critical actions such as policy changes, exports, delegated access, and lockdown changes.",
        }
        security_schemes["BastionWalletPoPSession"] = {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Authorization: PoP sess_...; Bearer Access Passes are rejected.",
        }

        signing_parameters = [
            {
                "name": "X-Bastion-Session",
                "in": "header",
                "required": True,
                "schema": {"type": "string"},
                "description": "Short-lived Proof-of-Possession session token. Never an Access Pass bearer token.",
            },
            {
                "name": "X-Bastion-Timestamp",
                "in": "header",
                "required": False,
                "schema": {"type": "string", "format": "date-time"},
                "description": "Timestamp used in the signed request digest and freshness check.",
            },
            {
                "name": "X-Bastion-Nonce",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "Unique per-session nonce used to prevent replay.",
            },
            {
                "name": "X-Bastion-Body-Hash",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "SHA-256 hash of the canonical request body.",
            },
            {
                "name": "X-Bastion-Signature",
                "in": "header",
                "required": False,
                "schema": {"type": "string"},
                "description": "Signature over SHA256(method || path || body_hash || timestamp || nonce).",
            },
        ]
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
                        existing_parameters = operation.setdefault("parameters", [])
                        existing_names = {param.get("name") for param in existing_parameters if isinstance(param, dict)}
                        for parameter in signing_parameters:
                            if parameter["name"] not in existing_names:
                                existing_parameters.append(parameter)
            if path.startswith("/api/v1/access"):
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation.setdefault("tags", ["access"])
                        operation.setdefault("x-access-pass-is-bearer", False)
            if path.startswith("/api/v1/wallet-auth"):
                protected = not path.endswith(("/challenges", "/register", "/login", "/sessions", "/recovery/start"))
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation.setdefault("tags", ["wallet-auth"])
                        operation["x-wallet-signature-grants-access-alone"] = False
                        operation["x-bitcoin-seed-or-private-key-requested"] = False
                        if protected:
                            operation["security"] = [
                                {"BastionWalletPoPSession": []},
                                {"BastionRequestSignature": []},
                            ]
            if path.startswith("/v1/lnurl"):
                protocol_callback = "/callback" in path or "/verify/" in path
                protected = path.endswith("/auth/step-up") or path.endswith("/withdraw/requests")
                for operation in operations.values():
                    if isinstance(operation, dict):
                        operation["x-lnurl-protocol-response"] = protocol_callback
                        operation["x-lnurl-auth-grants-access-alone"] = False
                        operation["x-invoice-creation-means-settled"] = False
                        operation["x-bitcoin-seed-or-private-key-requested"] = False
                        if protected:
                            operation["security"] = [
                                {"BastionWalletPoPSession": []},
                                {"BastionRequestSignature": []},
                            ]
        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
