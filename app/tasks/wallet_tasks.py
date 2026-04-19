from celery import shared_task


@shared_task(name="tasks.wallet.health_refresh")  # type: ignore[untyped-decorator]
def refresh_wallet_health_reports() -> str:
    return "wallet health reports refreshed"
