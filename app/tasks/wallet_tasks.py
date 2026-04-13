from celery import shared_task


@shared_task(name="tasks.wallet.health_refresh")
def refresh_wallet_health_reports() -> str:
    return "wallet health reports refreshed"
