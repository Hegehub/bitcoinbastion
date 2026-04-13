from fastapi import FastAPI

from app.api.errors import register_exception_handlers
from app.api.middleware import RequestIDMiddleware
from app.api.v1.admin import router as admin_router
from app.api.v1.auth import router as auth_router
from app.api.v1.entities import router as entities_router
from app.api.v1.fees import router as fees_router
from app.api.v1.health import router as health_router
from app.api.v1.news import router as news_router
from app.api.v1.onchain import router as onchain_router
from app.api.v1.signals import router as signals_router
from app.api.v1.treasury import router as treasury_router
from app.api.v1.users import router as users_router
from app.api.v1.wallet import router as wallet_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(RequestIDMiddleware)
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
