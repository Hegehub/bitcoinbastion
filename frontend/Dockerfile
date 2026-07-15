FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    BB_API_BASE_URL=http://localhost:8000 \
    BB_PUBLIC_SITE_MODE=true \
    BB_ENABLE_TRACE=true \
    BB_ENABLE_MARKET=true \
    BB_ENABLE_TIME_MACHINE=true \
    BB_ENABLE_SOVEREIGN_GRID=true \
    BB_ENABLE_CONSOLE=true \
    BB_REQUEST_TIMEOUT_SECONDS=5 \
    BB_DEFAULT_LANGUAGE=en \
    BB_LOG_LEVEL=INFO

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY rxconfig.py README.md .env.example ./
COPY bastion_ui ./bastion_ui

RUN uv sync --frozen --no-dev

EXPOSE 3001
EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3001/', timeout=3)"

CMD ["uv", "run", "reflex", "run", "--env", "prod", "--frontend-port", "3001", "--backend-port", "8001", "--backend-host", "0.0.0.0"]
