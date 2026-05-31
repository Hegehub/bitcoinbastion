from dataclasses import dataclass
from enum import StrEnum


class FetchPolicyName(StrEnum):
    FAST = "FAST"
    NORMAL = "NORMAL"
    SLOW = "SLOW"
    CONSERVATIVE = "CONSERVATIVE"


@dataclass(frozen=True)
class FetchPolicy:
    timeout_seconds: float
    max_retries: int
    backoff_base: float
    backoff_max: float
    respect_cache_headers: bool
    max_payload_mb: int


FETCH_POLICIES = {
    FetchPolicyName.FAST: FetchPolicy(5.0, 2, 0.5, 6.0, True, 2),
    FetchPolicyName.NORMAL: FetchPolicy(10.0, 3, 1.0, 12.0, True, 4),
    FetchPolicyName.SLOW: FetchPolicy(20.0, 4, 1.0, 20.0, True, 6),
    FetchPolicyName.CONSERVATIVE: FetchPolicy(30.0, 5, 2.0, 30.0, True, 8),
}
