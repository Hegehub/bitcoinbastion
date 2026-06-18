FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml ./
RUN uv sync --no-dev

COPY . .

EXPOSE 3001
EXPOSE 8001

CMD ["uv", "run", "reflex", "run", "--env", "prod", "--frontend-port", "3001", "--backend-port", "8001"]
