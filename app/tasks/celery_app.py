from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("bitcoin_bastion", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    task_track_started=True,
    task_time_limit=120,
    task_soft_time_limit=90,
    imports=(
        "app.tasks.policy_tasks",
        "app.tasks.reputation_tasks",
        "app.tasks.observability_tasks",
        "app.tasks.digest_tasks",
        "app.tasks.treasury_tasks",
        "app.tasks.privacy_tasks",
        "app.tasks.wallet_tasks",
        "app.tasks.signal_tasks",
        "app.tasks.onchain_tasks",
        "app.tasks.delivery_tasks",
        "app.tasks.maintenance_tasks",
        "app.tasks.news_tasks",
        "app.tasks.mining_tasks",
    ),
)
