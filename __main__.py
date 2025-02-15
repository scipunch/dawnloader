import asyncio
import logging
import os

from telebot.async_telebot import AsyncTeleBot

from app import bot

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)


def main() -> None:
    """Start the bot."""
    log.info("Starting telegram bot...")

    telegram_bot = AsyncTeleBot(os.environ["BOT_TOKEN"])

    bot.init(telegram_bot)

    asyncio.run(telegram_bot.infinity_polling())


if __name__ == "__main__":
    main()
