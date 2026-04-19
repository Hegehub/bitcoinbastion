from app.schemas.script import DescriptorAwarenessOut


class DescriptorAwarenessService:
    def evaluate(
        self,
        *,
        has_descriptor: bool,
        has_recovery_instructions: bool,
        has_backup_reference: bool,
    ) -> DescriptorAwarenessOut:
        score = 0.0
        warnings: list[str] = []

        if has_descriptor:
            score += 0.4
        else:
            warnings.append("Descriptor reference missing; recovery path assumptions are weak.")

        if has_recovery_instructions:
            score += 0.35
        else:
            warnings.append("Recovery instructions missing; human dependency risk elevated.")

        if has_backup_reference:
            score += 0.25
        else:
            warnings.append("Backup metadata reference missing; artifact completeness is incomplete.")

        assumption = "strong" if score >= 0.8 else "moderate" if score >= 0.5 else "weak"

        return DescriptorAwarenessOut(
            has_descriptor=has_descriptor,
            has_recovery_instructions=has_recovery_instructions,
            has_backup_reference=has_backup_reference,
            completeness_score=round(score, 3),
            recoverability_assumption=assumption,
            warnings=warnings,
            confidence=0.76,
            freshness={"source": "wallet_metadata", "state": "evaluated"},
            explainability={
                "weights": {
                    "descriptor": 0.4,
                    "instructions": 0.35,
                    "backup_reference": 0.25,
                }
            },
        )
