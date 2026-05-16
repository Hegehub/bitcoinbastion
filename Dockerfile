FROM python:3.12-slim

WORKDIR /code

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY pyproject.toml README.md /code/
COPY app /code/app
COPY alembic.ini /code/alembic.ini
COPY scripts /code/scripts

RUN pip install --no-cache-dir -e .

CMD ["bash", "scripts/start_api.sh"]
