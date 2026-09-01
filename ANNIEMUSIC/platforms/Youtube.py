import asyncio
import contextlib
import json
import os
import re
import time
import aiohttp
import shutil
from typing import Dict, List, Optional, Tuple, Union

import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch

from ANNIEMUSIC.utils.database import is_on_off
from ANNIEMUSIC.utils.errors import capture_internal_err
from ANNIEMUSIC.utils.formatters import time_to_seconds
from ANNIEMUSIC.utils.tuning import (
    YTDLP_TIMEOUT,
    YOUTUBE_META_MAX,
    YOUTUBE_META_TTL,
)
from ANNIEMUSIC import LOGGER


# ==========================================================
# ARTISTBOTS API CONFIGURATION
# ==========================================================

ARTISTBOTS_API_URL = "https://music.artistbots.workers.dev"
ARTISTBOTS_API_KEY = "ArtistbotsvsazvRw"

API_TIMEOUT = 300


# ==========================================================
# CACHE
# ==========================================================

_cache: Dict[str, Tuple[float, List[Dict]]] = {}
_cache_lock = asyncio.Lock()

_formats_cache: Dict[str, Tuple[float, List[Dict], str]] = {}
_formats_lock = asyncio.Lock()


# ==========================================================
# HELPERS
# ==========================================================

def extract_video_id(link: str) -> Optional[str]:
    """Extract YouTube video ID from URL or ID."""

    if not link:
        return None

    link = str(link).strip()

    if "v=" in link:
        video_id = link.split("v=", 1)[1].split("&", 1)[0]
        return video_id

    if "youtu.be/" in link:
        video_id = link.split("youtu.be/", 1)[1].split("?", 1)[0]
        return video_id.split("&", 1)[0]

    if "youtube.com/shorts/" in link:
        video_id = link.split("youtube.com/shorts/", 1)[1].split("?", 1)[0]
        return video_id.split("&", 1)[0]

    if "youtube.com/live/" in link:
        video_id = link.split("youtube.com/live/", 1)[1].split("?", 1)[0]
        return video_id.split("&", 1)[0]

    if re.fullmatch(r"[A-Za-z0-9_-]{11}", link):
        return link

    return None


def safe_filename(value: str) -> str:
    """Make filename safe."""

    return re.sub(r'[<>:"/\\|?*]', "_", value)


async def _exec_proc(*args: str) -> Tuple[bytes, bytes]:
    """Execute process."""

    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    try:
        return await asyncio.wait_for(
            proc.communicate(),
            timeout=YTDLP_TIMEOUT,
        )
    except asyncio.TimeoutError:
        with contextlib.suppress(Exception):
            proc.kill()

        return b"", b"timeout"


async def shell_cmd(cmd):
    """Execute shell command."""

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    out, errorz = await proc.communicate()

    if errorz:
        error_text = errorz.decode("utf-8", errors="ignore")

        if "unavailable videos are hidden" in error_text.lower():
            return out.decode("utf-8", errors="ignore")

        return error_text

    return out.decode("utf-8", errors="ignore")


# ==========================================================
# ARTISTBOTS API DOWNLOADER
# ==========================================================

async def artistbots_download(
    link: str,
    download_type: str,
) -> Optional[str]:
    """
    Download YouTube audio/video using ArtistBots API.

    download_type:
        audio -> MP3
        video -> MP4
    """

    video_id = extract_video_id(link)

    if not video_id:
        LOGGER("ANNIEMUSIC.platforms.Youtube").error(
            f"❌ Invalid YouTube video ID: {link}"
        )
        return None

    os.makedirs("downloads", exist_ok=True)

    if download_type == "video":
        extension = ".mp4"
    else:
        extension = ".mp3"

    file_path = os.path.join(
        "downloads",
        f"{video_id}{extension}",
    )

    # ------------------------------------------------------
    # Local cache
    # ------------------------------------------------------

    if os.path.exists(file_path):
        try:
            if os.path.getsize(file_path) > 10240:
                LOGGER("ANNIEMUSIC.platforms.Youtube").info(
                    f"✅ API cache found: {file_path}"
                )
                return file_path

            os.remove(file_path)

        except Exception:
            pass

    # ------------------------------------------------------
    # API request
    # ------------------------------------------------------

    endpoint = f"{ARTISTBOTS_API_URL.rstrip('/')}/download"

    params = {
        "url": video_id,
        "type": download_type,
        "api_key": ARTISTBOTS_API_KEY,
    }

    LOGGER("ANNIEMUSIC.platforms.Youtube").info(
        f"🚀 ArtistBots API -> {video_id} | {download_type}"
    )

    temp_path = f"{file_path}.part"

    try:

        timeout = aiohttp.ClientTimeout(
            total=API_TIMEOUT,
            connect=30,
            sock_read=API_TIMEOUT,
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                endpoint,
                params=params,
                allow_redirects=True,
            ) as response:

                LOGGER("ANNIEMUSIC.platforms.Youtube").info(
                    f"📡 API status: {response.status}"
                )

                if response.status != 200:

                    try:
                        error_text = await response.text()

                        LOGGER("ANNIEMUSIC.platforms.Youtube").error(
                            f"❌ ArtistBots API error "
                            f"{response.status}: "
                            f"{error_text[:500]}"
                        )

                    except Exception:
                        LOGGER("ANNIEMUSIC.platforms.Youtube").error(
                            f"❌ ArtistBots API returned HTTP "
                            f"{response.status}"
                        )

                    return None

                content_length = response.headers.get(
                    "Content-Length"
                )

                if content_length:
                    try:
                        size_mb = int(content_length) / (
                            1024 * 1024
                        )

                        LOGGER("ANNIEMUSIC.platforms.Youtube").info(
                            f"📦 API file size: {size_mb:.2f} MB"
                        )

                    except Exception:
                        pass

                # --------------------------------------------------
                # Download to temporary file
                # --------------------------------------------------

                downloaded = 0
                last_log = 0

                with open(temp_path, "wb") as file:

                    async for chunk in response.content.iter_chunked(
                        1024 * 64
                    ):

                        if not chunk:
                            continue

                        file.write(chunk)
                        downloaded += len(chunk)

                        # Log every 5 MB
                        if (
                            downloaded - last_log
                            >= 5 * 1024 * 1024
                        ):

                            mb = downloaded / (
                                1024 * 1024
                            )

                            if content_length:
                                try:
                                    total = int(
                                        content_length
                                    )

                                    percent = (
                                        downloaded / total
                                    ) * 100

                                    LOGGER(
                                        "ANNIEMUSIC.platforms.Youtube"
                                    ).info(
                                        f"📥 API download: "
                                        f"{mb:.1f} MB "
                                        f"({percent:.1f}%)"
                                    )

                                except Exception:
                                    LOGGER(
                                        "ANNIEMUSIC.platforms.Youtube"
                                    ).info(
                                        f"📥 API downloaded: "
                                        f"{mb:.1f} MB"
                                    )

                            else:
                                LOGGER(
                                    "ANNIEMUSIC.platforms.Youtube"
                                ).info(
                                    f"📥 API downloaded: "
                                    f"{mb:.1f} MB"
                                )

                            last_log = downloaded

                # --------------------------------------------------
                # Validate
                # --------------------------------------------------

                if not os.path.exists(temp_path):
                    LOGGER(
                        "ANNIEMUSIC.platforms.Youtube"
                    ).error(
                        "❌ API did not create a file"
                    )
                    return None

                file_size = os.path.getsize(temp_path)

                if file_size <= 10240:
                    LOGGER(
                        "ANNIEMUSIC.platforms.Youtube"
                    ).error(
                        f"❌ API file too small: {file_size} bytes"
                    )

                    with contextlib.suppress(Exception):
                        os.remove(temp_path)

                    return None

                # --------------------------------------------------
                # Rename temp -> final
                # --------------------------------------------------

                os.replace(
                    temp_path,
                    file_path,
                )

                final_mb = os.path.getsize(file_path) / (
                    1024 * 1024
                )

                LOGGER(
                    "ANNIEMUSIC.platforms.Youtube"
                ).info(
                    f"✅ ArtistBots API SUCCESS: "
                    f"{file_path} "
                    f"({final_mb:.2f} MB)"
                )

                return file_path

    except asyncio.TimeoutError:

        LOGGER(
            "ANNIEMUSIC.platforms.Youtube"
        ).error(
            f"⏰ ArtistBots API timeout: {video_id}"
        )

        return None

    except aiohttp.ClientError as e:

        LOGGER(
            "ANNIEMUSIC.platforms.Youtube"
        ).error(
            f"🌐 ArtistBots API connection error: {e}"
        )

        return None

    except Exception as e:

        LOGGER(
            "ANNIEMUSIC.platforms.Youtube"
        ).error(
            f"❌ ArtistBots API download failed: "
            f"{type(e).__name__}: {e}"
        )

        return None

    finally:

        if os.path.exists(temp_path):

            try:
                os.remove(temp_path)
            except Exception:
                pass


# ==========================================================
# YOUTUBE SEARCH CACHE
# ==========================================================

@capture_internal_err
async def cached_youtube_search(
    query: str,
) -> List[Dict]:

    key = f"q:{query}"
    now = time.time()

    async with _cache_lock:

        if key in _cache:

            ts, val = _cache[key]

            if now - ts < YOUTUBE_META_TTL:
                return val

            _cache.pop(key, None)

        if len(_cache) > YOUTUBE_META_MAX:
            _cache.clear()

    try:

        data = await VideosSearch(
            query,
            limit=1,
        ).next()

        result = data.get(
            "result",
            [],
        )

    except Exception:

        result = []

    if result:

        async with _cache_lock:
            _cache[key] = (
                now,
                result,
            )

    return result


# ==========================================================
# YOUTUBE API CLASS
# ==========================================================

class YouTubeAPI:

    def __init__(self) -> None:

        self.base_url = (
            "https://www.youtube.com/watch?v="
        )

        self.playlist_url = (
            "https://youtube.com/playlist?list="
        )

        self.status = (
            "https://www.youtube.com/oembed?url="
        )

        self._url_pattern = re.compile(
            r"(?:youtube\.com|youtu\.be)"
        )

        self.reg = re.compile(
            r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])"
        )

    # ======================================================
    # LINK PREPARATION
    # ======================================================

    def _prepare_link(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> str:

        if isinstance(videoid, str) and videoid.strip():

            link = (
                self.base_url
                + videoid.strip()
            )

        if "youtu.be" in link:

            link = (
                self.base_url
                + link.split("/")[-1]
                .split("?")[0]
            )

        elif "youtube.com/shorts/" in link:

            link = (
                self.base_url
                + link.split("/")[-1]
                .split("?")[0]
            )

        elif "youtube.com/live/" in link:

            link = (
                self.base_url
                + link.split("/")[-1]
                .split("?")[0]
            )

        return link.split("&")[0]

    # ======================================================
    # URL
    # ======================================================

    @capture_internal_err
    async def url(
        self,
        message: Message,
    ) -> Optional[str]:

        msgs = [message]

        if message.reply_to_message:
            msgs.append(
                message.reply_to_message
            )

        for msg in msgs:

            text = (
                msg.text
                or msg.caption
                or ""
            )

            entities = (
                msg.entities
                or msg.caption_entities
                or []
            )

            for ent in entities:

                if ent.type == MessageEntityType.URL:

                    url = text[
                        ent.offset:
                        ent.offset + ent.length
                    ]

                    if self._url_pattern.search(url):
                        return url

                elif ent.type == MessageEntityType.TEXT_LINK:

                    url = ent.url

                    if self._url_pattern.search(url):
                        return url

        return None

    # ======================================================
    # EXISTS
    # ======================================================

    @capture_internal_err
    async def exists(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> bool:

        return bool(
            self._url_pattern.search(
                self._prepare_link(
                    link,
                    videoid,
                )
            )
        )

    # ======================================================
    # VIDEO INFO
    # ======================================================

    @capture_internal_err
    async def _fetch_video_info(
        self,
        query: str,
        *,
        use_cache: bool = True,
    ) -> Optional[Dict]:

        q = self._prepare_link(query)

        if use_cache and not q.startswith("http"):

            res = await cached_youtube_search(q)

            return (
                res[0]
                if res
                else None
            )

        data = await VideosSearch(
            q,
            limit=1,
        ).next()

        result = data.get(
            "result",
            [],
        )

        return (
            result[0]
            if result
            else None
        )

    # ======================================================
    # LIVE CHECK
    # ======================================================

    @capture_internal_err
    async def is_live(
        self,
        link: str,
    ) -> bool:

        prepared = self._prepare_link(link)

        stdout, _ = await _exec_proc(
            "yt-dlp",
            "--dump-json",
            prepared,
        )

        if not stdout:
            return False

        try:

            info = json.loads(
                stdout.decode(
                    "utf-8",
                    errors="ignore",
                )
            )

            return bool(
                info.get("is_live")
            )

        except Exception:
            return False

    # ======================================================
    # DETAILS
    # ======================================================

    @capture_internal_err
    async def details(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> Tuple[
        str,
        Optional[str],
        int,
        str,
        str,
    ]:

        info = await self._fetch_video_info(
            self._prepare_link(
                link,
                videoid,
            )
        )

        if not info:
            raise ValueError(
                "Video not found"
            )

        dt = info.get("duration")

        ds = (
            int(time_to_seconds(dt))
            if dt
            else 0
        )

        thumb = (
            info.get("thumbnail")
            or info.get(
                "thumbnails",
                [{}],
            )[0].get(
                "url",
                "",
            )
        ).split("?")[0]

        return (
            info.get("title", ""),
            dt,
            ds,
            thumb,
            info.get("id", ""),
        )

    # ======================================================
    # TITLE
    # ======================================================

    @capture_internal_err
    async def title(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> str:

        info = await self._fetch_video_info(
            self._prepare_link(
                link,
                videoid,
            )
        )

        return (
            info.get("title", "")
            if info
            else ""
        )

    # ======================================================
    # DURATION
    # ======================================================

    @capture_internal_err
    async def duration(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> Optional[str]:

        info = await self._fetch_video_info(
            self._prepare_link(
                link,
                videoid,
            )
        )

        return (
            info.get("duration")
            if info
            else None
        )

    # ======================================================
    # THUMBNAIL
    # ======================================================

    @capture_internal_err
    async def thumbnail(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> str:

        info = await self._fetch_video_info(
            self._prepare_link(
                link,
                videoid,
            )
        )

        if not info:
            return ""

        thumb = (
            info.get("thumbnail")
            or info.get(
                "thumbnails",
                [{}],
            )[0].get(
                "url",
                "",
            )
        )

        return (
            thumb.split("?")[0]
            if thumb
            else ""
        )

    # ======================================================
    # VIDEO
    # ======================================================

    @capture_internal_err
    async def video(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> Tuple[int, str]:

        link = self._prepare_link(
            link,
            videoid,
        )

        result = await artistbots_download(
            link,
            "video",
        )

        if result:
            return (
                1,
                result,
            )

        return (
            0,
            "ArtistBots API video download failed",
        )

    # ======================================================
    # PLAYLIST
    # ======================================================

    @capture_internal_err
    async def playlist(
        self,
        link: str,
        limit: int,
        user_id,
        videoid: Union[str, bool, None] = None,
    ) -> List[str]:

        if videoid:

            link = (
                self.playlist_url
                + str(videoid)
            )

        link = link.split("&")[0]

        playlist = await shell_cmd(
            f"yt-dlp -i "
            f"--get-id "
            f"--flat-playlist "
            f"--playlist-end {limit} "
            f"--skip-download "
            f"\"{link}\""
        )

        try:

            items = [
                key
                for key in playlist.split("\n")
                if key
            ]

        except Exception:

            items = []

        return items

    # ======================================================
    # TRACK
    # ======================================================

    @capture_internal_err
    async def track(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> Tuple[Dict, str]:

        info = await self._fetch_video_info(
            self._prepare_link(
                link,
                videoid,
            )
        )

        if not info:
            raise ValueError(
                "Track not found"
            )

        thumb = (
            info.get("thumbnail")
            or info.get(
                "thumbnails",
                [{}],
            )[0].get(
                "url",
                "",
            )
        ).split("?")[0]

        details = {

            "title": info.get(
                "title",
                "",
            ),

            "link": info.get(
                "webpage_url",
                self._prepare_link(
                    link,
                    videoid,
                ),
            ),

            "vidid": info.get(
                "id",
                "",
            ),

            "duration_min": (
                info.get("duration")
                if isinstance(
                    info.get("duration"),
                    str,
                )
                else None
            ),

            "thumb": thumb,
        }

        return (
            details,
            info.get(
                "id",
                "",
            ),
        )

    # ======================================================
    # FORMATS
    # ======================================================

    @capture_internal_err
    async def formats(
        self,
        link: str,
        videoid: Union[str, bool, None] = None,
    ) -> Tuple[
        List[Dict],
        str,
    ]:

        link = self._prepare_link(
            link,
            videoid,
        )

        key = f"f:{link}"
        now = time.time()

        async with _formats_lock:

            cached = _formats_cache.get(key)

            if cached and (
                now - cached[0]
                < YOUTUBE_META_TTL
            ):

                return (
                    cached[1],
                    cached[2],
                )

        out: List[Dict] = []

        try:

            opts = {
                "quiet": True,
                "no_warnings": True,
                "noplaylist": True,
            }

            with yt_dlp.YoutubeDL(
                opts
            ) as ydl:

                info = ydl.extract_info(
                    link,
                    download=False,
                )

                for fmt in info.get(
                    "formats",
                    [],
                ):

                    if "dash" in str(
                        fmt.get(
                            "format",
                            "",
                        )
                    ).lower():
                        continue

                    size = (
                        fmt.get("filesize")
                        or fmt.get(
                            "filesize_approx"
                        )
                    )

                    if not size:
                        continue

                    if not all(
                        k in fmt
                        for k in (
                            "format",
                            "format_id",
                            "ext",
                            "format_note",
                        )
                    ):
                        continue

                    out.append({

                        "format": fmt[
                            "format"
                        ],

                        "filesize": size,

                        "format_id": fmt[
                            "format_id"
                        ],

                        "ext": fmt[
                            "ext"
                        ],

                        "format_note": fmt[
                            "format_note"
                        ],

                        "yturl": link,
                    })

        except Exception as e:

            LOGGER(
                "ANNIEMUSIC.platforms.Youtube"
            ).warning(
                f"⚠️ Format extraction failed: {e}"
            )

        async with _formats_lock:

            if len(_formats_cache) > YOUTUBE_META_MAX:
                _formats_cache.clear()

            _formats_cache[key] = (
                now,
                out,
                link,
            )

        return (
            out,
            link,
        )

    # ======================================================
    # SLIDER
    # ======================================================

    @capture_internal_err
    async def slider(
        self,
        link: str,
        query_type: int,
        videoid: Union[str, bool, None] = None,
    ) -> Tuple[
        str,
        Optional[str],
        str,
        str,
    ]:

        data = await VideosSearch(
            self._prepare_link(
                link,
                videoid,
            ),
            limit=10,
        ).next()

        results = data.get(
            "result",
            [],
        )

        if (
            not results
            or query_type >= len(results)
        ):

            raise IndexError(
                f"Query type index "
                f"{query_type} out of range "
                f"(found {len(results)} results)"
            )

        r = results[query_type]

        return (

            r.get(
                "title",
                "",
            ),

            r.get(
                "duration"
            ),

            r.get(
                "thumbnails",
                [{}],
            )[0].get(
                "url",
                "",
            ).split("?")[0],

            r.get(
                "id",
                "",
            ),
        )

    # ======================================================
    # MAIN DOWNLOAD
    # ======================================================

    @capture_internal_err
    async def download(
        self,
        link: str,
        mystic,
        *,
        video: Union[
            bool,
            str,
            None,
        ] = None,
        videoid: Union[
            str,
            bool,
            None,
        ] = None,
        songaudio: Union[
            bool,
            str,
            None,
        ] = None,
        songvideo: Union[
            bool,
            str,
            None,
        ] = None,
        format_id: Union[
            bool,
            str,
            None,
        ] = None,
        title: Union[
            bool,
            str,
            None,
        ] = None,
    ) -> Union[
        Tuple[str, Optional[bool]],
        Tuple[None, None],
    ]:

        link = self._prepare_link(
            link,
            videoid,
        )

        video_id = extract_video_id(
            link
        )

        if not video_id:

            LOGGER(
                "ANNIEMUSIC.platforms.Youtube"
            ).error(
                f"❌ Invalid video ID: {link}"
            )

            return (
                None,
                None,
            )

        # ==================================================
        # VIDEO
        # ==================================================

        if songvideo or video:

            LOGGER(
                "ANNIEMUSIC.platforms.Youtube"
            ).info(
                f"🎬 ArtistBots API video: "
                f"{video_id}"
            )

            result = await artistbots_download(
                link,
                "video",
            )

            if result:

                LOGGER(
                    "ANNIEMUSIC.platforms.Youtube"
                ).info(
                    f"✅ Video API success: "
                    f"{result}"
                )

                return (
                    result,
                    True,
                )

            LOGGER(
                "ANNIEMUSIC.platforms.Youtube"
            ).error(
                "❌ ArtistBots API video failed"
            )

            return (
                None,
                None,
            )

        # ==================================================
        # AUDIO
        # ==================================================

        LOGGER(
            "ANNIEMUSIC.platforms.Youtube"
        ).info(
            f"🎵 ArtistBots API audio: "
            f"{video_id}"
        )

        result = await artistbots_download(
            link,
            "audio",
        )

        if result:

            LOGGER(
                "ANNIEMUSIC.platforms.Youtube"
            ).info(
                f"✅ Audio API success: "
                f"{result}"
            )

            return (
                result,
                True,
            )

        LOGGER(
            "ANNIEMUSIC.platforms.Youtube"
        ).error(
            "❌ ArtistBots API audio failed"
        )

        return (
            None,
            None,
        )


# ==========================================================
# GLOBAL INSTANCE
# ==========================================================

YouTube = YouTubeAPI()
