from fastapi import FastAPI

from app.api.v1.health import router as health_router
from app.api.v1.news import router as news_router
from app.api.v1.signals import router as signals_router
from app.core.config import get_settings
from app.core.logging import configure_logging

configure_logging()
settings = get_settings()

app = FastAPI(title=settings.app_name)
app.include_router(health_router, prefix=settings.api_prefix)
app.include_router(news_router, prefix=settings.api_prefix)
app.include_router(signals_router, prefix=settings.api_prefix)
