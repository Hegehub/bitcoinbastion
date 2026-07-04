from app.services.intelligence.timeline_hashing import build_event_hash


def dedup_key(
    event_type: str, event_time: str, title: str, related_ids: dict[str, int | None]
) -> str:
    return build_event_hash(
        {
            "event_type": event_type,
            "event_time": event_time,
            "title": title,
            "related_ids": related_ids,
        }
    )
