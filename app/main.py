from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_exception_handlers
from app.api.health_root import router as health_root_router
from app.api.middleware import (
    RateLimitMiddleware,
    RequestIDMiddleware,
    RequestSizeLimitMiddleware,
    SecurityHeadersMiddleware,
)
from app.api.openapi import apply_openapi_defaults
from app.api.v1.access import router as access_router
from app.api.v1.admin import router as admin_router
from app.api.v1.citadel import router as citadel_router
from app.api.v1.auth import router as auth_router
from app.api.v1.education import router as education_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.entities import router as entities_router
from app.api.v1.fees import router as fees_router
from app.api.v1.health import router as health_router
from app.api.v1.news import router as news_router
from app.api.v1.market_intelligence import router as market_intelligence_router
from app.api.v1.market_data import router as market_data_router
from app.api.v1.market import router as market_router
from app.api.v1.market_time_machine import router as market_time_machine_router
from app.api.v1.metrics_status import router as metrics_status_router
from app.api.v1.intelligence_timeline import router as intelligence_timeline_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.intelligence_signals import router as intelligence_signals_router
from app.api.v1.operator_signals import router as operator_signals_router
from app.api.v1.observability import router as observability_router
from app.api.v1.operations import router as operations_router
from app.api.v1.policy import router as policy_router
from app.api.v1.plugins import router as plugins_router
from app.api.v1.public import router as public_router
from app.api.v1.privacy import router as privacy_router
from app.api.v1.onchain import router as onchain_router
from app.api.v1.signals import router as signals_router
from app.api.v1.storage_status import router as storage_status_router
from app.api.v1.treasury import router as treasury_router
from app.api.v1.trace import router as trace_router
from app.api.v1.users import router as users_router
from app.web.routes_market import router as market_time_machine_web_router
from app.api.v1.wallet import router as wallet_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.ws import router as ws_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.telemetry import attach_metrics

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
attach_metrics(app)
register_exception_handlers(app)
apply_openapi_defaults(app)

app.include_router(health_root_router)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(access_router, prefix=settings.api_prefix)
app.include_router(news_router, prefix=settings.api_prefix)
app.include_router(market_intelligence_router, prefix=settings.api_prefix)
app.include_router(market_data_router, prefix=settings.api_prefix)
app.include_router(market_router, prefix=settings.api_prefix)
app.include_router(market_time_machine_router, prefix=settings.api_prefix)
app.include_router(metrics_status_router, prefix=settings.api_prefix)
app.include_router(intelligence_timeline_router, prefix=settings.api_prefix)
app.include_router(intelligence_router, prefix=settings.api_prefix)
app.include_router(signals_router, prefix=settings.api_prefix)
app.include_router(storage_status_router, prefix=settings.api_prefix)
app.include_router(intelligence_signals_router, prefix=settings.api_prefix)
app.include_router(operator_signals_router, prefix=settings.api_prefix)
app.include_router(onchain_router, prefix=settings.api_prefix)
app.include_router(entities_router, prefix=settings.api_prefix)
app.include_router(wallet_router, prefix=settings.api_prefix)
app.include_router(fees_router, prefix=settings.api_prefix)
app.include_router(treasury_router, prefix=settings.api_prefix)
app.include_router(admin_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(policy_router, prefix=settings.api_prefix)
app.include_router(plugins_router, prefix=settings.api_prefix)
app.include_router(privacy_router, prefix=settings.api_prefix)
app.include_router(education_router, prefix=settings.api_prefix)
app.include_router(evidence_router, prefix=settings.api_prefix)
app.include_router(observability_router, prefix=settings.api_prefix)
app.include_router(operations_router, prefix=settings.api_prefix)
app.include_router(citadel_router, prefix=settings.api_prefix)
app.include_router(trace_router, prefix=settings.api_prefix)
app.include_router(webhooks_router, prefix=settings.api_prefix)
app.include_router(ws_router, prefix=settings.api_prefix)

app.include_router(public_router, prefix=settings.api_prefix)
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")
app.include_router(market_time_machine_web_router)
