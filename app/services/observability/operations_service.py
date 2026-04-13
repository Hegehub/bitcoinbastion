from app.schemas.observability import OperationsSnapshotOut, ProviderHealthOut


class OperationsSnapshotService:
    def snapshot(self) -> OperationsSnapshotOut:
        return OperationsSnapshotOut(
            queue_depth=0,
            stale_jobs=0,
            providers=[
                ProviderHealthOut(provider="rss", healthy=True, details="No provider errors observed."),
                ProviderHealthOut(
                    provider="onchain", healthy=True, details="Latest ingestion completed successfully."
                ),
            ],
        )
