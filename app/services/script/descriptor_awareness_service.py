from app.schemas.script import DescriptorAwarenessOut


class DescriptorAwarenessService:
    def evaluate(
        self,
        *,
        has_descriptor: bool,
        has_recovery_instructions: bool,
        has_backup_reference: bool,
        descriptor_age_days: int | None = None,
        script_type: str = "unknown",
        wallet_type: str = "single-sig",
        is_watch_only: bool = False,
        multisig_signer_count: int | None = None,
    ) -> DescriptorAwarenessOut:
        score = 0.0
        warnings: list[str] = []

        if has_descriptor:
            score += 0.34
        else:
            warnings.append("Descriptor reference missing; recovery path assumptions are weak.")

        if has_recovery_instructions:
            score += 0.22
        else:
            warnings.append("Recovery instructions missing; human dependency risk elevated.")

        if has_backup_reference:
            score += 0.2
        else:
            warnings.append(
                "Backup metadata reference missing; artifact completeness is incomplete."
            )

        freshness_band = "unknown"
        freshness_factor = 0.0
        if descriptor_age_days is None:
            warnings.append("Descriptor freshness is unknown; confidence is reduced.")
        elif descriptor_age_days <= 30:
            freshness_band = "fresh"
            freshness_factor = 1.0
            score += 0.16
        elif descriptor_age_days <= 90:
            freshness_band = "aging"
            freshness_factor = 0.65
            score += 0.09
            warnings.append("Descriptor reference is aging; schedule reverification.")
        else:
            freshness_band = "stale"
            freshness_factor = 0.25
            score += 0.02
            warnings.append("Descriptor reference is stale; readiness assumptions are degraded.")

        normalized_script = (script_type or "unknown").lower()
        script_compatibility = "unknown"
        if normalized_script in {"p2wpkh", "p2tr", "taproot", "p2wsh", "p2sh", "p2pkh"}:
            script_compatibility = "supported"
            score += 0.08
        else:
            warnings.append(
                "Script compatibility is unknown; descriptor assumptions are conservative."
            )

        multisig_completeness = "n/a"
        if "multi" in (wallet_type or "").lower() or normalized_script in {"p2wsh", "p2sh"}:
            multisig_completeness = "partial"
            if multisig_signer_count is not None and multisig_signer_count >= 2:
                multisig_completeness = "complete"
                score += 0.06
            else:
                warnings.append(
                    "Multisig descriptor completeness is partial; signer metadata is limited."
                )

        if is_watch_only and not has_descriptor:
            warnings.append(
                "Watch-only profile without descriptor reference lowers recoverability confidence."
            )

        score = round(max(0.0, min(1.0, score)), 3)
        assumption = "strong" if score >= 0.8 else "moderate" if score >= 0.5 else "weak"

        confidence = 0.78
        if not has_descriptor:
            confidence -= 0.18
        if descriptor_age_days is None:
            confidence -= 0.12
        elif descriptor_age_days > 90:
            confidence -= 0.16
        elif descriptor_age_days > 30:
            confidence -= 0.07
        if normalized_script == "unknown":
            confidence -= 0.08
        if is_watch_only and not has_descriptor:
            confidence -= 0.05
        confidence = round(max(0.2, min(0.92, confidence)), 3)

        return DescriptorAwarenessOut(
            has_descriptor=has_descriptor,
            has_recovery_instructions=has_recovery_instructions,
            has_backup_reference=has_backup_reference,
            completeness_score=score,
            recoverability_assumption=assumption,
            warnings=warnings,
            confidence=confidence,
            freshness={
                "source": "wallet_metadata",
                "state": "evaluated",
                "descriptor_age_days": descriptor_age_days,
                "freshness_band": freshness_band,
            },
            explainability={
                "weights": {
                    "descriptor_presence": 0.34,
                    "instruction_reference": 0.22,
                    "backup_reference": 0.2,
                    "descriptor_freshness": 0.16,
                    "script_compatibility": 0.08,
                    "multisig_completeness": 0.06,
                },
                "assumptions": {
                    "no_descriptor_upload_required": True,
                    "metadata_reference_only": True,
                    "script_validation_scope": "hint_only",
                },
                "signals": {
                    "freshness_factor": freshness_factor,
                    "script_compatibility": script_compatibility,
                    "watch_only": is_watch_only,
                    "multisig_completeness": multisig_completeness,
                    "multisig_signer_count": multisig_signer_count,
                },
            },
        )
