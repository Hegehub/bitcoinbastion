from typing import NoReturn

SECURITY_HEADERS = {
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
}

CSP_POLICY = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"


def _legacy_auth_disabled() -> NoReturn:
    from app.core.exceptions import AppError

    raise AppError(
        message="Legacy email/password authentication is disabled. Use Bastion Proof-of-Access.",
        status_code=410,
        code="legacy_auth_disabled",
    )


def hash_password(password: str) -> str:
    """Disabled legacy password hashing helper retained for import stability."""
    _ = password
    _legacy_auth_disabled()


def verify_password(password: str, hashed_password: str) -> bool:
    """Disabled legacy password verifier retained for import stability."""
    _ = (password, hashed_password)
    _legacy_auth_disabled()


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    """Disabled legacy JWT issuer retained for import stability."""
    _ = (subject, expires_minutes)
    from app.core.exceptions import AppError

    raise AppError(
        message="Legacy bearer-token authentication is disabled. Use Bastion Proof-of-Access.",
        status_code=410,
        code="legacy_auth_disabled",
    )
