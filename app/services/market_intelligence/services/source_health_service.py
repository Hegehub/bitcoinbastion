class SourceHealthService:
    def record_success(self, source_id: int) -> object:
        raise NotImplementedError

    def record_failure(self, source_id: int, error: str) -> object:
        raise NotImplementedError

    def calculate_health_score(self, success_count: int, failure_count: int) -> float:
        total = success_count + failure_count
        return 1.0 if total == 0 else max(0.0, min(1.0, success_count / total))
