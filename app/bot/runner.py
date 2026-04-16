import asyncio

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from app.bot.handlers.access import is_admin_chat
from app.bot.handlers.commands import ADMIN_COMMANDS, HELP_TEXT, USER_COMMANDS
from app.bot.handlers.runtime_actions import (
    admin_jobs_message,
    admin_publish_message,
    admin_refresh_message,
    admin_reprocess_message,
    admin_sources_refresh_message,
    digest_message,
    fee_recommendation_message,
    latest_news_message,
    status_message,
    top_signals_message,
    wallet_health_message,
    watchlist_message,
)
from app.core.config import get_settings

settings = get_settings()


def _deny_admin(message: Message) -> bool:
    chat = message.chat
    chat_id = chat.id if chat else 0
    if is_admin_chat(chat_id, settings):
        return False
    return True


def _dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def start(message: Message) -> None:
        await message.answer("Bitcoin Bastion bot is online.")

    @dp.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(HELP_TEXT)

    @dp.message(Command("latest"))
    async def latest_handler(message: Message) -> None:
        await message.answer(await latest_news_message())

    @dp.message(Command("top"))
    async def top_handler(message: Message) -> None:
        await message.answer(await top_signals_message())

    @dp.message(Command("digest"))
    async def digest_handler(message: Message) -> None:
        await message.answer(await digest_message())

    @dp.message(Command("watchlist"))
    async def watchlist_handler(message: Message) -> None:
        await message.answer(await watchlist_message())

    @dp.message(Command("fees"))
    async def fees_handler(message: Message) -> None:
        await message.answer(await fee_recommendation_message())

    @dp.message(Command("wallet_health"))
    async def wallet_health_handler(message: Message) -> None:
        await message.answer(await wallet_health_message())

    @dp.message(Command("status"))
    async def status_handler(message: Message) -> None:
        await message.answer(await status_message())

    @dp.message(Command("admin_publish"))
    async def admin_publish_handler(message: Message) -> None:
        if _deny_admin(message):
            await message.answer("Access denied: admin chat is not authorized.")
            return
        await message.answer(await admin_publish_message())

    @dp.message(Command("admin_refresh"))
    async def admin_refresh_handler(message: Message) -> None:
        if _deny_admin(message):
            await message.answer("Access denied: admin chat is not authorized.")
            return
        await message.answer(await admin_refresh_message())

    @dp.message(Command("admin_reprocess"))
    async def admin_reprocess_handler(message: Message) -> None:
        if _deny_admin(message):
            await message.answer("Access denied: admin chat is not authorized.")
            return
        await message.answer(await admin_reprocess_message())

    @dp.message(Command("admin_sources"))
    async def admin_sources_handler(message: Message) -> None:
        if _deny_admin(message):
            await message.answer("Access denied: admin chat is not authorized.")
            return
        await message.answer(await admin_sources_refresh_message())

    @dp.message(Command("admin_jobs"))
    async def admin_jobs_handler(message: Message) -> None:
        if _deny_admin(message):
            await message.answer("Access denied: admin chat is not authorized.")
            return
        await message.answer(await admin_jobs_message())

    # Defensive invariant: help text should always include every routed command.
    assert set(USER_COMMANDS + ADMIN_COMMANDS).issubset(set(HELP_TEXT.splitlines()[1:]))

    return dp


async def run() -> None:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")

    bot = Bot(token=settings.telegram_bot_token)
    dp = _dispatcher()
    await dp.start_polling(bot)


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
