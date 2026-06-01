class SourceReputationService:
    def update_reputation(self, source_id: int) -> object:
        raise NotImplementedError

    def adjust_first_mover_score(self, source_id: int, delta: float) -> object:
        raise NotImplementedError

    def adjust_false_positive_rate(self, source_id: int, delta: float) -> object:
        raise NotImplementedError
