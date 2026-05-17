from app.tasks.celery_app import celery_app


def test_mining_task_is_discoverable_by_worker_import_registry() -> None:
    celery_app.loader.import_default_modules()
    assert "tasks.mining.refresh_stratum_v2_capabilities" in celery_app.tasks
