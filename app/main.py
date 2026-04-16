from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.middleware import RateLimitMiddleware, RequestIDMiddleware
from app.api.v1.admin import router as admin_router
from app.api.v1.citadel import router as citadel_router
from app.api.v1.auth import router as auth_router
from app.api.v1.education import router as education_router
from app.api.v1.entities import router as entities_router
from app.api.v1.fees import router as fees_router
from app.api.v1.health import router as health_router
from app.api.v1.news import router as news_router
from app.api.v1.observability import router as observability_router
from app.api.v1.policy import router as policy_router
from app.api.v1.privacy import router as privacy_router
from app.api.v1.onchain import router as onchain_router
from app.api.v1.signals import router as signals_router
from app.api.v1.treasury import router as treasury_router
from app.api.v1.users import router as users_router
from app.api.v1.wallet import router as wallet_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import attach_metrics

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
attach_metrics(app)
register_exception_handlers(app)

app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(news_router, prefix=settings.api_prefix)
app.include_router(signals_router, prefix=settings.api_prefix)
app.include_router(onchain_router, prefix=settings.api_prefix)
app.include_router(entities_router, prefix=settings.api_prefix)
app.include_router(wallet_router, prefix=settings.api_prefix)
app.include_router(fees_router, prefix=settings.api_prefix)
app.include_router(treasury_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(policy_router, prefix=settings.api_prefix)
app.include_router(privacy_router, prefix=settings.api_prefix)
app.include_router(education_router, prefix=settings.api_prefix)
app.include_router(observability_router, prefix=settings.api_prefix)
app.include_router(citadel_router, prefix=settings.api_prefix)
