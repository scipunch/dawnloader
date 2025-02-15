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
MediaDownloader = Callable[[Url], Awaitable[Result[Path, MediaDownloaderError]]]


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


async def download_youtube(url: Url) -> Result[Path, MediaDownloaderError]:
    """Download video from YouTube."""

    opts = {
        "format": (
            "bestvideo[ext=mp4][filesize<50M]"
            "+bestaudio[ext=m4a]/best[ext=mp4][filesize<50M]/best"
        ),
        "merge_output_format": "mp4",
        "outtmpl": "%(title)s.%(ext)s",
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
            info = ydl.extract_info(url, download=True)
            return Ok(Path(ydl.prepare_filename(info)))
    except Exception:
        log.exception("Error downloading YouTube video")
        return Err(MediaDownloaderError())


async def download_instagram(url: Url) -> Result[Path, MediaDownloaderError]:
    """Download media from Instagram."""
    instagram = instaloader.Instaloader()
    try:
        shortcode = url.split("/")[-2]
        post = instaloader.Post.from_shortcode(instagram.context, shortcode)

        download_dir = Path("instagram")
        download_dir.mkdir(exist_ok=True)
        log.info("Processing %s post from instagram", shortcode)

        if post.is_video:
            log.info("Downloading video from instagram")
            status = instagram.download_post(post, target=download_dir)
            if not status:
                return Err(MediaDownloaderError())

            return Ok(
                next(
                    path
                    for path in download_dir.iterdir()
                    if path.is_file() and path.name.endswith(".mp4")
                )
            )

        log.info("Downloading picture from instagram")
        download_path = download_dir / shortcode
        instagram.download_pic(
            filename=download_path, url=post.url, mtime=post.date_utc
        )
        return Ok(download_path.with_suffix(".jpg"))
    except Exception:
        log.exception("Error downloading Instagram content")
        return Err(MediaDownloaderError())
