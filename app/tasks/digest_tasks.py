from celery import shared_task


@shared_task(name="tasks.digest.generate_daily")
def generate_daily_digest() -> str:
    return "daily digest generation queued"
