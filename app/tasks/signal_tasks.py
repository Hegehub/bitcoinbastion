from app.tasks.celery_app import celery_app


@celery_app.task(name="signals.generate")
def generate_signals_task() -> dict[str, int]:
    return {"generated": 0}
