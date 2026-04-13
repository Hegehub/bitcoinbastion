from app.tasks.celery_app import celery_app


@celery_app.task(name="maintenance.cleanup")
def cleanup_task() -> dict[str, str]:
    return {"status": "ok"}
