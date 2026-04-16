from app.core.config import Settings


def parse_admin_chat_ids(raw: str) -> set[str]:
    return {item.strip() for item in raw.split(",") if item.strip()}


def is_admin_chat(chat_id: int | str, settings: Settings) -> bool:
    allowed = parse_admin_chat_ids(settings.admin_chat_ids)
    if not allowed:
        return False
    return str(chat_id) in allowed
