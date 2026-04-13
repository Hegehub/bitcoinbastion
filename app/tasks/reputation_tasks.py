from celery import shared_task


@shared_task(name="tasks.reputation.refresh")
def refresh_source_reputation() -> str:
    return "source reputation refresh completed"
