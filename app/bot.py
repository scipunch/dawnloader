import logging
import tempfile
from pathlib import Path

from result import Err, Ok
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_helper import ApiTelegramException
from telebot.types import Message

from app import service

log = logging.getLogger(__name__)


def init(bot: AsyncTeleBot) -> None:
    @bot.message_handler(commands=["start", "help"])
    async def send_welcome(message: Message) -> None:
        """Handle /start and /help commands."""
        await bot.reply_to(
            message,
            "Send me a YouTube or Instagram link, and I'll download the media for you!",
        )

    @bot.message_handler(
        func=lambda m: m.text and service.is_media_url_supported(m.text)
    )
    async def handle_url(message: Message) -> None:
        """Handle YouTube and Instagram URLs."""
        assert message.text is not None
        url = message.text.strip()

        processing_msg = await bot.reply_to(message, "Processing your request...")

        media_downloader = service.get_platform_handler(url)

        with tempfile.TemporaryDirectory() as tmpdirname:
            download_dir = Path(tmpdirname)
            match await media_downloader(url, download_dir):
                case Err(_):
                    await bot.edit_message_text(
                        "Sorry, couldn't download the media. Please try again.",
                        message.chat.id,
                        processing_msg.message_id,
                    )
                case Ok(filepath):
                    for filepath in download_dir.iterdir():
                        try:
                            await _send_media(bot, message.chat.id, filepath)
                        except ApiTelegramException as e:
                            error_text: str
                            match e.error_code:
                                case 413:
                                    error_text = (
                                        "File is too big to send it"
                                        f" ({filepath.stat().st_size >> 20}MB / 50MB)"
                                    )
                                case _:
                                    error_text = "Unexpected telegram API error"
                                    log.exception(error_text)

                            await bot.reply_to(message, error_text)
                            break
                    await bot.delete_message(message.chat.id, processing_msg.message_id)

    @bot.message_handler()
    async def handle_invalid_message(message: Message) -> None:
        """Handle all other messages that don't match any other filters."""
        await bot.reply_to(message, "Please send a valid YouTube or Instagram link.")


async def _send_media(bot: AsyncTeleBot, chat_id: int, filepath: Path) -> None:
    """Send media file to user."""
    with filepath.open("rb") as file:
        if filepath.suffix.lower() in [".mp4", ".mov", ".avi"]:
            await bot.send_video(chat_id, file)
        else:
            await bot.send_photo(chat_id, file)
