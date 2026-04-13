from app.tasks.celery_app import celery_app


@celery_app.task(name="onchain.fetch")
def fetch_onchain_task() -> dict[str, int]:
    return {"events": 0}
