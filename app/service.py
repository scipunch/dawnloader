import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from urllib.parse import urlparse

import instaloader
import yt_dlp
from result import Err, Ok, Result

log = logging.getLogger(__name__)


class MediaDownloaderError(Exception):
    pass


Url = str
MediaDownloader = Callable[[Url, Path], Awaitable[Result[None, MediaDownloaderError]]]


def get_platform_handler(url: str) -> MediaDownloader:
    """Return the appropriate download handler for the URL."""
    domain = urlparse(url).netloc.lower()

    if "youtube.com" in domain or "youtu.be" in domain:
        return download_youtube

    if "instagram.com" in domain:
        return download_instagram

    log.error("Unknown url [%s] format", url)
    raise ValueError


def is_media_url_supported(url: Url) -> bool:
    """Filter function to check if message contains valid YouTube or Instagram URL."""
    result = urlparse(url)
    if not all([result.scheme, result.netloc]):
        return False

    domain = result.netloc.lower().removeprefix("www.")
    return domain in ("youtube.com", "youtu.be", "instagram.com")


async def download_youtube(
    url: Url, target_dir: Path
) -> Result[None, MediaDownloaderError]:
    """Download video from YouTube."""

    opts = {
        "format": (
            "bestvideo[ext=mp4][filesize<50M]"
            "+bestaudio[ext=m4a]/best[ext=mp4][filesize<50M]/best"
        ),
        "merge_output_format": "mp4",
        "outtmpl": str(target_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ],
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.extract_info(url, download=True)
    except Exception:
        log.exception("Error downloading YouTube video")
        return Err(MediaDownloaderError())

    return Ok(None)


async def download_instagram(
    url: Url, target_dir: Path
) -> Result[None, MediaDownloaderError]:
    """Download media from Instagram."""
    instagram = instaloader.Instaloader()
    shortcode = url.split("/")[-2]
    post = instaloader.Post.from_shortcode(instagram.context, shortcode)

    log.info("Processing %s post from instagram", shortcode)

    status = instagram.download_post(post, target=target_dir)
    if not status:
        return Err(MediaDownloaderError())

    for path in target_dir.iterdir():
        if not path.name.endswith(".mp4"):
            path.unlink()

    return Ok(None)
