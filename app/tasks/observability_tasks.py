from celery import shared_task


@shared_task(name="tasks.observability.provider_health")  # type: ignore[untyped-decorator]
def collect_provider_health_snapshots() -> str:
    return "provider health snapshots collected"
