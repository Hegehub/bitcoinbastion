from app.bot.handlers.commands import ADMIN_COMMANDS, HELP_TEXT, USER_COMMANDS


def test_help_text_contains_spec_baseline_commands() -> None:
    lines = HELP_TEXT.splitlines()
    assert lines[0] == "Bitcoin Bastion commands:"

    commands = set(lines[1:])
    assert set(USER_COMMANDS).issubset(commands)
    assert set(ADMIN_COMMANDS).issubset(commands)


def test_help_text_has_no_duplicate_commands() -> None:
    listed_commands = HELP_TEXT.splitlines()[1:]
    assert len(listed_commands) == len(set(listed_commands))
