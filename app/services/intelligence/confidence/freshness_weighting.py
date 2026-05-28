def freshness_weight(minutes: int) -> float:
    if minutes <= 5:
        return 1.0
    if minutes <= 15:
        return 0.9
    if minutes <= 60:
        return 0.75
    if minutes <= 240:
        return 0.55
    if minutes <= 1440:
        return 0.35
    return 0.15
