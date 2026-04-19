from celery import shared_task


@shared_task(name="tasks.privacy.recompute")  # type: ignore[untyped-decorator]
def recompute_privacy_scores() -> str:
    return "privacy scores recomputed"
