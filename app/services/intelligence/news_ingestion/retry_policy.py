def is_retryable_status(status_code: int | None) -> bool:
    return status_code in {408, 425, 429, 500, 502, 503, 504}
