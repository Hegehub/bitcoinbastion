USER_COMMANDS: tuple[str, ...] = (
    "/start",
    "/help",
    "/latest",
    "/top",
    "/digest",
    "/watchlist",
    "/fees",
    "/wallet_health",
    "/status",
)

ADMIN_COMMANDS: tuple[str, ...] = (
    "/admin_publish",
    "/admin_refresh",
    "/admin_reprocess",
    "/admin_sources",
    "/admin_jobs",
)


def _build_help_text() -> str:
    lines = ["Bitcoin Bastion commands:"]
    lines.extend(USER_COMMANDS)
    lines.extend(ADMIN_COMMANDS)
    return "\n".join(lines)


HELP_TEXT = _build_help_text()
