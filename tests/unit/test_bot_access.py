from app.bot.handlers.access import is_admin_chat, parse_admin_chat_ids
from app.core.config import Settings


def test_parse_admin_chat_ids_trims_and_ignores_empty() -> None:
    out = parse_admin_chat_ids(" 123,456 ,, 789 ")
    assert out == {"123", "456", "789"}


def test_is_admin_chat_uses_settings_allowlist() -> None:
    settings = Settings(ADMIN_CHAT_IDS="1001,1002")

    assert is_admin_chat(1001, settings) is True
    assert is_admin_chat("1002", settings) is True
    assert is_admin_chat(999, settings) is False
