from app.tasks.celery_app import celery_app


@celery_app.task(name="delivery.publish")
def publish_signals_task() -> dict[str, int]:
    return {"published": 0}
