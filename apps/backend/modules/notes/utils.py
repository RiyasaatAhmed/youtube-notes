"""
Notes-related utility functions

Includes YouTube URL validation, video metadata extraction, transcript fetching,
and other utilities
"""

import re
import json
import requests
from typing import Optional, Dict
from fastapi import HTTPException, status
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError


def extract_video_id(youtube_url: str) -> str:
    """
    Extract video ID from YouTube URL
    
    Supports various YouTube URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    
    Args:
        youtube_url: YouTube video URL
        
    Returns:
        Video ID
        
    Raises:
        ValueError: If URL is invalid
        
    Example:
        >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)([a-zA-Z0-9_-]{11})',
        r'm\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Invalid YouTube URL: {youtube_url}")


def validate_youtube_url(youtube_url: str) -> bool:
    """
    Validate if the URL is a valid YouTube URL
    
    Args:
        youtube_url: URL to validate
        
    Returns:
        True if valid YouTube URL, False otherwise
        
    Example:
        >>> validate_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        True
        >>> validate_youtube_url("https://example.com")
        False
    """
    try:
        extract_video_id(youtube_url)
        return True
    except ValueError:
        return False


def _oembed_fallback(video_id: str) -> Dict[str, str]:
    """
    Simple oEmbed fallback — returns title and author if possible.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with title, channel, and fallback flag
    """
    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    
    try:
        resp = requests.get(oembed_url, timeout=6)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "title": data.get("title", "Unknown Title"),
                "channel": data.get("author_name", "Unknown Channel"),
                "channel_id": "",
                "subtitle_text": "",
                "fallback": True,
            }
        
        # Non-200 response
        return {
            "title": "Unknown Title",
            "channel": "Unknown Channel",
            "channel_id": "",
            "subtitle_text": "",
            "fallback": True,
            "oembed_status": resp.status_code,
        }
    except Exception:
        return {
            "title": "Unknown Title",
            "channel": "Unknown Channel",
            "channel_id": "",
            "subtitle_text": "",
            "fallback": True,
        }


def get_video_metadata(video_id: str) -> Dict[str, str]:
    """
    Get video metadata (title, channel, channel_id, subtitle_text) using yt-dlp.
    Falls back to YouTube oEmbed on format or extractor failures.
    
    Args:
        video_id: YouTube video ID
        
    Returns:
        Dictionary with title, channel, channel_id, and subtitle_text
        
    Raises:
        HTTPException: If metadata cannot be fetched
    """
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "postprocessors": [],
        "noplaylist": True,
        "extract_flat": False,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "referer": "https://www.youtube.com/",
    }

    url = f"https://www.youtube.com/watch?v={video_id}"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract keys safely
            title = info.get("title", "Unknown Title")
            uploader = info.get("uploader") or info.get("uploader_id") or info.get("artist") or "Unknown Channel"
            channel_id = info.get("channel_id", "") or info.get("uploader_id", "") or ""
            subtitles = info.get("subtitles", {})
            automatic_captions = info.get("automatic_captions", {})
            
            # Try to get subtitle URL safely
            subtitle_url = None
            concatenated_text = ""
            
            # Try manual subtitles first
            if subtitles:
                for lang_key in list(subtitles.keys()):
                    if subtitles[lang_key] and len(subtitles[lang_key]) > 0:
                        subtitle_url = subtitles[lang_key][0].get('url')
                        break
            
            # If no manual subtitles, try automatic captions
            if not subtitle_url and automatic_captions:
                for lang_key in list(automatic_captions.keys()):
                    if automatic_captions[lang_key] and len(automatic_captions[lang_key]) > 0:
                        subtitle_url = automatic_captions[lang_key][0].get('url')
                        break
            
            # Download and parse subtitle if URL is available
            if subtitle_url:
                try:
                    response = requests.get(
                        subtitle_url, 
                        timeout=10,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                            "Referer": "https://www.youtube.com/"
                        }
                    )
                    response.raise_for_status()
                    subtitle_content = response.text
                    
                    # Parse JSON and concatenate all text
                    try:
                        subtitle_json = json.loads(subtitle_content)
                        events = subtitle_json.get("events", [])
                        
                        text_segments = []
                        for event in events:
                            segs = event.get("segs", [])
                            for seg in segs:
                                text = seg.get("utf8", "")
                                if text and text.strip():
                                    text_segments.append(text.strip())
                        
                        # Join all segments and clean up
                        concatenated_text = " ".join(text_segments)
                        concatenated_text = " ".join(concatenated_text.split())
                        
                    except (json.JSONDecodeError, KeyError, TypeError):
                        # If parsing fails, use raw content
                        concatenated_text = subtitle_content
                        
                except requests.RequestException:
                    # If download fails, leave concatenated_text empty
                    concatenated_text = ""
                 
            return {
                "title": title,
                "channel": uploader,
                "channel_id": channel_id,
                "subtitle_text": concatenated_text,
            }

    except DownloadError as de:
        error_msg = str(de)
        if "403" in error_msg or "Forbidden" in error_msg or "format is not available" in error_msg:
            fallback = _oembed_fallback(video_id)
            fallback["subtitle_text"] = ""
            fallback["error"] = error_msg
            return fallback
        fallback = _oembed_fallback(video_id)
        fallback["subtitle_text"] = ""
        fallback["error"] = error_msg
        return fallback

    except ExtractorError as ee:
        fallback = _oembed_fallback(video_id)
        fallback["subtitle_text"] = ""
        fallback["error"] = str(ee)
        return fallback

    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "Forbidden" in error_msg:
            fallback = _oembed_fallback(video_id)
            fallback["subtitle_text"] = ""
            fallback["error"] = error_msg
            return fallback
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch video metadata: {error_msg}"
        )

