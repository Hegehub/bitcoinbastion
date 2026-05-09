from pydantic import BaseModel, Field


class MempoolSnapshot(BaseModel):
    backlog_tx_count: int = Field(ge=0)
    backlog_vbytes: int = Field(ge=0)
    median_fee_rate_sat_vb: float = Field(ge=0.0)
    high_priority_fee_rate_sat_vb: float = Field(ge=0.0)
    snapshot_age_seconds: int | None = Field(default=None, ge=0)


class MempoolStateOut(BaseModel):
    congestion_state: str
    tx_density: float = Field(ge=0.0)
    priority_bands: dict[str, float]
    confidence: float = Field(ge=0.0, le=1.0)
    freshness: dict[str, object]
    explainability: dict[str, object]


class MempoolAnalyzerService:
    def analyze(self, snapshot: MempoolSnapshot) -> MempoolStateOut:
        density = snapshot.backlog_vbytes / max(1.0, snapshot.backlog_tx_count)

        if snapshot.backlog_vbytes < 20_000_000 and snapshot.median_fee_rate_sat_vb < 5:
            congestion = "low"
        elif snapshot.backlog_vbytes < 60_000_000:
            congestion = "normal"
        elif snapshot.backlog_vbytes < 110_000_000:
            congestion = "elevated"
        elif snapshot.backlog_vbytes < 180_000_000:
            congestion = "congested"
        else:
            congestion = "extreme"

        low_band = max(1.0, snapshot.median_fee_rate_sat_vb * 0.75)
        medium_band = max(2.0, snapshot.median_fee_rate_sat_vb * 1.0)
        high_band = max(snapshot.high_priority_fee_rate_sat_vb, medium_band * 1.35)
        urgent_band = max(high_band * 1.25, snapshot.high_priority_fee_rate_sat_vb * 1.15)

        age = snapshot.snapshot_age_seconds
        freshness_band = "unknown"
        staleness_penalty = 0.0
        if age is not None:
            if age <= 30:
                freshness_band = "fresh"
            elif age <= 120:
                freshness_band = "recent"
                staleness_penalty = 0.05
            elif age <= 600:
                freshness_band = "stale"
                staleness_penalty = 0.14
            else:
                freshness_band = "very_stale"
                staleness_penalty = 0.25

        base_confidence = {
            "low": 0.82,
            "normal": 0.79,
            "elevated": 0.75,
            "congested": 0.71,
            "extreme": 0.67,
        }[congestion]
        confidence = max(0.35, min(0.92, base_confidence - staleness_penalty))

        return MempoolStateOut(
            congestion_state=congestion,
            tx_density=round(density, 2),
            priority_bands={
                "low": round(low_band, 2),
                "medium": round(medium_band, 2),
                "high": round(high_band, 2),
                "urgent": round(urgent_band, 2),
            },
            confidence=round(confidence, 3),
            freshness={
                "source": "mempool_snapshot",
                "source_type": "runtime",
                "provider_name": "unknown",
                "is_mock": False,
                "is_fallback": False,
                "backlog_vbytes": snapshot.backlog_vbytes,
                "snapshot_age_seconds": age,
                "freshness_band": freshness_band,
            },
            explainability={
                "density_formula": "backlog_vbytes / backlog_tx_count",
                "classification_thresholds_vbytes": {
                    "low_max": 20_000_000,
                    "normal_max": 60_000_000,
                    "elevated_max": 110_000_000,
                    "congested_max": 180_000_000,
                },
                "assumptions": [
                    "Fee bands are recommendations, not settlement guarantees.",
                    "Stale snapshots reduce confidence and should trigger refresh before execution.",
                ],
                "limitations": [
                    "Snapshot quality depends on upstream data source.",
                    "No direct provider attribution is available in this analyzer input.",
                ],
                "staleness_penalty": round(staleness_penalty, 3),
            },
        )
