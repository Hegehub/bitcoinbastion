from celery import shared_task


@shared_task(name="tasks.policy.enforcement")
def run_policy_enforcement_cycle() -> str:
    return "policy enforcement cycle completed"
