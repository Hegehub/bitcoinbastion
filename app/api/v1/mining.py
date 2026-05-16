from fastapi import APIRouter

"""Mining API surface proposal (M0-02).

Endpoints are intentionally planning-only and return static capability metadata.
No mining runtime logic is implemented in this block.
"""

router = APIRouter(prefix="/mining", tags=["mining"])


@router.get("/capabilities")
def mining_capabilities() -> dict[str, object]:
    return {
        "status": "planned",
        "planned_endpoints": [
            "GET /api/v1/mining/scorecard",
            "GET /api/v1/mining/hashrate",
            "GET /api/v1/mining/pools",
            "GET /api/v1/mining/production",
            "GET /api/v1/mining/inclusion",
        ],
        "constraints": [
            "no_db_writes_in_m0",
            "preserve_modular_monolith_boundaries",
        ],
    }
