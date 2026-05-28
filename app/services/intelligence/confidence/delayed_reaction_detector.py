from dataclasses import dataclass


@dataclass
class DelayedReactionResult:
    detected: bool
    dominant_window: str
    confidence_adjustment: float
    explanation: str


class DelayedReactionDetector:
    def detect(self, minutes_to_move: int, multi_source_confirmed: bool, direction_match: bool) -> DelayedReactionResult:
        if minutes_to_move > 60 and multi_source_confirmed and direction_match:
            return DelayedReactionResult(True, "4h", 0.08, "Delayed reaction detected with later multi-source confirmation.")
        return DelayedReactionResult(False, "none", 0.0, "No strong delayed reaction pattern detected.")
