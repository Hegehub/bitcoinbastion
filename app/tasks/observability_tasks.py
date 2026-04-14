from celery import shared_task


@shared_task(name="tasks.observability.provider_health")
def collect_provider_health_snapshots() -> str:
    return "provider health snapshots collected"
