from dataclasses import dataclass


@dataclass
class SimilarityResult:
    is_exact_duplicate: bool
    is_near_duplicate: bool
    similarity_score: float
    reasons: list[str]
    confidence: float
