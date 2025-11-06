import requests
from fastapi import HTTPException, status
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError
from typing import Dict, Optional
import json

def _oembed_fallback(video_id: str) -> Dict[str, str]:
    """Simple oEmbed fallback — returns title and author if possible."""
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        resp = requests.get(oembed_url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", "Unknown Title"),
                "channel": data.get("author_name", "Unknown Channel"),
                "channel_id": "",
                "fallback": True,
            }
        # non-200 — return minimal info
        return {
            "title": "Unknown Title",
            "channel": "Unknown Channel",
            "channel_id": "",
            "fallback": True,
            "oembed_status": resp.status_code,
        }
    except Exception:
        return {
            "title": "Unknown Title",
            "channel": "Unknown Channel",
            "channel_id": "",
            "fallback": True,
        }

def get_video_metadata(video_id: str) -> dict:
    """
    Get video metadata (title, channel, channel_id) using yt-dlp.
    Falls back to YouTube oEmbed on format or extractor failures.
    """
    ydl_opts = {
        # don't print progress / keep quiet
        "quiet": True,
        "no_warnings": True,
        # Do not download; only extract info
        # (extract_info(download=False) also used below)
        "skip_download": True,
        # avoid postprocessors that might try to access formats
        "postprocessors": [],
        # try to make extraction resilient
        "noplaylist": True,
        # prefer best but keep default selection (explicit 'format' can cause requested-format errors)
        # "format": "best",  # avoid forcing a format unless you need it
        "nocheckcertificate": True,
        "ignoreerrors": False,
    }

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # download=False makes sure yt-dlp doesn't attempt to download media
            info = ydl.extract_info(url, download=False)
            # Extract keys safely
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader") or info.get("uploader_id") or info.get("artist") or "Unknown Channel"
            channel_id = info.get("channel_id", "") or info.get("uploader_id", "") or ""
            subtitles = info.get("subtitles", {})
            
            subtitle_url = subtitles[list(subtitles.keys())[0]][0]['url']

            response = requests.get(subtitle_url, timeout=10)
            response.raise_for_status()
            subtitle_content = response.text
            
            # Parse JSON and concatenate all text
            concatenated_text = ""
            try:
                subtitle_json = json.loads(subtitle_content)
                events = subtitle_json.get("events", [])
                
                for event in events:
                    segs = event.get("segs", [])
                    for seg in segs:
                        text = seg.get("utf8", "")
                        if text:
                            concatenated_text += text + " "
                
                # Clean up: remove extra spaces and newlines
                concatenated_text = " ".join(concatenated_text.split())
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                # If parsing fails, use raw content
                concatenated_text = subtitle_content
                 
            return {
                "title": title,
                "channel": uploader,
                "channel_id": channel_id,
                "subtitle_text": concatenated_text,  # All text concatenated together
            }

    except DownloadError as de:
        # Often includes messages like "Requested format is not available."
        # Try a lightweight fallback (oEmbed) before failing.
        fallback = _oembed_fallback(video_id)
        # include original error message to help debugging
        fallback["error"] = str(de)
        return fallback

    except ExtractorError as ee:
        # Extractor-level errors (e.g., geo-restrictions, account/age restrictions)
        # Try fallback
        fallback = _oembed_fallback(video_id)
        fallback["error"] = str(ee)
        return fallback

    except Exception as e:
        # Unknown/unexpected — return as HTTPException for your API
        # If you prefer to return fallback instead of raising, you can do that here.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch video metadata: {str(e)}"
        )
