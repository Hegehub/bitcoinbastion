from celery import shared_task


@shared_task(name="tasks.treasury.policy_scan")  # type: ignore[untyped-decorator]
def run_treasury_policy_scan() -> str:
    return "treasury policy scan completed"
