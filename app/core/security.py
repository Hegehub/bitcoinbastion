from datetime import UTC, datetime, timedelta
from typing import cast

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=['argon2'], deprecated='auto')

SECURITY_HEADERS = {
    'X-Frame-Options': 'DENY',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
    'Cross-Origin-Opener-Policy': 'same-origin',
    'Cross-Origin-Resource-Policy': 'same-origin',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
}

CSP_POLICY = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"


def hash_password(password: str) -> str:
    return cast(str, pwd_context.hash(password))


def verify_password(password: str, hashed_password: str) -> bool:
    return cast(bool, pwd_context.verify(password, hashed_password))


def create_access_token(subject: str, expires_minutes: int = 60) -> str:
    settings = get_settings()
    ttl_minutes = max(1, int(expires_minutes or settings.jwt_access_token_expires_minutes))
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=ttl_minutes)
    payload = {'sub': subject, 'exp': int(expires_at.timestamp()), 'iat': int(now.timestamp()), 'iss': settings.jwt_issuer}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return cast(str, token)
