from pydantic import BaseModel, Field


class MempoolSnapshot(BaseModel):
    backlog_tx_count: int = Field(ge=0)
    backlog_vbytes: int = Field(ge=0)
    median_fee_rate_sat_vb: float = Field(ge=0.0)
    high_priority_fee_rate_sat_vb: float = Field(ge=0.0)


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
        if snapshot.backlog_vbytes >= 120_000_000:
            congestion = "severe"
        elif snapshot.backlog_vbytes >= 60_000_000:
            congestion = "elevated"
        else:
            congestion = "normal"

        priority_bands = {
            "low": max(1.0, snapshot.median_fee_rate_sat_vb * 0.8),
            "medium": max(2.0, snapshot.median_fee_rate_sat_vb),
            "high": max(snapshot.high_priority_fee_rate_sat_vb, snapshot.median_fee_rate_sat_vb * 1.4),
        }

        return MempoolStateOut(
            congestion_state=congestion,
            tx_density=round(density, 2),
            priority_bands={k: round(v, 2) for k, v in priority_bands.items()},
            confidence=0.72,
            freshness={"source": "mempool_snapshot", "backlog_vbytes": snapshot.backlog_vbytes},
            explainability={
                "density_formula": "backlog_vbytes / backlog_tx_count",
                "severe_threshold_vbytes": 120_000_000,
                "elevated_threshold_vbytes": 60_000_000,
            },
        )
