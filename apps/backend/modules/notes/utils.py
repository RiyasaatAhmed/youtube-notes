"""
Notes-related utility functions

Includes YouTube URL validation, video metadata extraction, transcript fetching,
audio extraction, and speech-to-text conversion utilities
"""

import re
import json
import os
import tempfile
import requests
from typing import Optional, Dict
from fastapi import HTTPException, status
import yt_dlp
from yt_dlp.utils import DownloadError, ExtractorError
import speech_recognition as sr
from pydub import AudioSegment


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


# def extract_audio_to_text(youtube_url: str, video_id: str) -> str:
#     """
#     Extract audio from YouTube video and convert to text using SpeechRecognition.
    
#     This function is used as a fallback when subtitles are not available.
#     It downloads the audio, converts it to WAV format, and uses speech recognition
#     to extract the text content.
    
#     Args:
#         youtube_url: YouTube video URL
#         video_id: YouTube video ID
        
#     Returns:
#         Extracted text from audio
        
#     Raises:
#         HTTPException: If audio extraction or speech recognition fails
        
#     Note:
#         This process can be slow for long videos. Consider chunking long audio files.
#     """
#     temp_dir = None
#     audio_file = None
#     wav_file = None
    
#     try:
#         # Create temporary directory for audio files
#         temp_dir = tempfile.mkdtemp()
        
#         # Configure yt-dlp to download audio only
#         ydl_opts = {
#             'format': 'bestaudio/best',
#             'outtmpl': os.path.join(temp_dir, f'{video_id}.%(ext)s'),
#             'postprocessors': [{
#                 'key': 'FFmpegExtractAudio',
#                 'preferredcodec': 'wav',
#                 'preferredquality': '192',
#             }],
#             'quiet': True,
#             'no_warnings': True,
#             'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#             'referer': 'https://www.youtube.com/',
#         }
        
#         # Download audio
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             ydl.download([youtube_url])
        
#         # Find the downloaded WAV file
#         wav_file = os.path.join(temp_dir, f'{video_id}.wav')
#         if not os.path.exists(wav_file):
#             # Try to find any audio file in temp_dir
#             files = os.listdir(temp_dir)
#             audio_files = [f for f in files if f.endswith(('.wav', '.mp3', '.m4a', '.ogg'))]
#             if not audio_files:
#                 raise HTTPException(
#                     status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                     detail="Failed to download audio file from YouTube"
#                 )
#             # Convert to WAV if needed
#             audio_file = os.path.join(temp_dir, audio_files[0])
#             if not audio_file.endswith('.wav'):
#                 audio = AudioSegment.from_file(audio_file)
#                 wav_file = os.path.join(temp_dir, f'{video_id}.wav')
#                 audio.export(wav_file, format="wav")
#             else:
#                 wav_file = audio_file
        
#         # Initialize speech recognizer
#         recognizer = sr.Recognizer()
        
#         # Process audio file
#         # For long videos, we need to chunk the audio
#         audio = AudioSegment.from_wav(wav_file)
        
#         # SpeechRecognition has a limit, so we'll process in chunks
#         # Google's API has a limit of ~1 minute per request
#         chunk_duration_ms = 60000  # 60 seconds
#         all_text = []
        
#         for start_ms in range(0, len(audio), chunk_duration_ms):
#             end_ms = min(start_ms + chunk_duration_ms, len(audio))
#             chunk = audio[start_ms:end_ms]
            
#             # Export chunk to temporary WAV file
#             chunk_file = os.path.join(temp_dir, f'{video_id}_chunk_{start_ms}.wav')
#             chunk.export(chunk_file, format="wav")
            
#             try:
#                 # Recognize speech from chunk
#                 with sr.AudioFile(chunk_file) as source:
#                     # Adjust for ambient noise
#                     recognizer.adjust_for_ambient_noise(source, duration=0.5)
#                     audio_data = recognizer.record(source)
                
#                 # Use Google's speech recognition (free, no API key needed)
#                 try:
#                     text = recognizer.recognize_google(audio_data)
#                     if text.strip():
#                         all_text.append(text)
#                 except sr.UnknownValueError:
#                     # Could not understand audio, skip this chunk
#                     pass
#                 except sr.RequestError as e:
#                     # API unavailable or request failed
#                     raise HTTPException(
#                         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                         detail=f"Speech recognition service error: {str(e)}"
#                     )
#             finally:
#                 # Clean up chunk file
#                 if os.path.exists(chunk_file):
#                     os.remove(chunk_file)
        
#         # Combine all text chunks
#         final_text = " ".join(all_text)
        
#         if not final_text.strip():
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Could not extract text from audio. The audio may be unclear or contain no speech."
#             )
        
#         return final_text
        
#     except DownloadError as e:
#         print("Okay here",e)
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Failed to download audio from YouTube: {str(e)}"
#         )
#     except ExtractorError as e:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Failed to extract audio from YouTube: {str(e)}"
#         )
#     except Exception as e:
#         error_msg = str(e)
#         if isinstance(e, HTTPException):
#             raise
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to extract text from audio: {error_msg}"
#         )
#     finally:
#         # Clean up temporary files
#         if temp_dir and os.path.exists(temp_dir):
#             try:
#                 import shutil
#                 shutil.rmtree(temp_dir)
#             except Exception:
#                 pass



def extract_audio_to_text(youtube_url: str, video_id: str) -> str:
    """
    Extract audio from YouTube video and convert to text using SpeechRecognition.
    """
    temp_dir = None
    
    try:
        # Create temporary directory for audio files
        temp_dir = tempfile.mkdtemp()
        
        # Enhanced yt-dlp configuration to avoid 403 errors
        ydl_opts = {
            # Use formats that are less likely to be blocked
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, f'{video_id}.%(ext)s'),
            
            # Better anti-bot evasion
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'referer': 'https://www.youtube.com/',
            'cookiefile': None,
            
            # Throttle requests to avoid rate limiting
            'throttled_rate': '100K',
            'sleep_interval': 2,
            'max_sleep_interval': 5,
            
            # Retry settings
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'continue_dl': True,
            
            # Avoid HLS streams which often get 403 errors
            'extract_flat': False,
            'hls_prefer_native': False,
            'hls_use_mpegts': False,
            
            # Post-processing
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'postprocessor_args': [
                '-ar', '16000',  # Set sample rate for better speech recognition
            ],
            
            'quiet': False,
            'no_warnings': False,
        }
        
        # Try different format combinations if first attempt fails
        format_attempts = [
            'bestaudio[ext=m4a]/bestaudio/best',
            'worstaudio/worst',  # Sometimes lower quality streams are less protected
            'bestaudio/best',
        ]
        
        download_success = False
        last_error = None
        
        for format_attempt in format_attempts:
            if download_success:
                break
                
            ydl_opts['format'] = format_attempt
            print(f"Attempting download with format: {format_attempt}")
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info first
                    info_dict = ydl.extract_info(youtube_url, download=False)
                    
                    # Check available formats
                    available_formats = []
                    if 'formats' in info_dict:
                        for f in info_dict['formats']:
                            if f.get('audio_ext') != 'none':
                                available_formats.append(f"{f.get('format_id', 'N/A')} - {f.get('ext', 'N/A')} - {f.get('format_note', 'N/A')}")
                    
                    print(f"Available audio formats: {available_formats}")
                    
                    # Now download
                    ydl.download([youtube_url])
                    download_success = True
                    print("Download successful!")
                    
            except yt_dlp.DownloadError as e:
                last_error = e
                print(f"Download failed with format {format_attempt}: {e}")
                continue
            except Exception as e:
                last_error = e
                print(f"Unexpected error with format {format_attempt}: {e}")
                continue
        
        if not download_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"All download attempts failed. Last error: {str(last_error)}"
            )
        
        # Find the downloaded audio file
        files = os.listdir(temp_dir)
        audio_files = [f for f in files if f.endswith(('.wav', '.m4a', '.mp3', '.ogg', '.webm'))]
        
        if not audio_files:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No audio files were downloaded successfully"
            )
        
        audio_file_path = os.path.join(temp_dir, audio_files[0])
        
        # Convert to WAV if needed
        if not audio_file_path.endswith('.wav'):
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(audio_file_path)
                wav_file_path = os.path.join(temp_dir, f'{video_id}.wav')
                audio.export(wav_file_path, format="wav")
                audio_file_path = wav_file_path
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to convert audio to WAV: {str(e)}"
                )
        
        # Continue with your existing speech recognition code...
        recognizer = sr.Recognizer()
        
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_wav(audio_file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to load audio file: {str(e)}"
            )
        
        chunk_duration_ms = 59000
        all_text = []
        
        if len(audio) < 1000:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Audio is too short to process"
            )
        
        for start_ms in range(0, len(audio), chunk_duration_ms):
            end_ms = min(start_ms + chunk_duration_ms, len(audio))
            chunk = audio[start_ms:end_ms]
            
            if len(chunk) < 500:
                continue
                
            chunk_file = os.path.join(temp_dir, f'{video_id}_chunk_{start_ms}.wav')
            try:
                chunk.export(chunk_file, format="wav")
                
                if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) == 0:
                    continue
                
                try:
                    with sr.AudioFile(chunk_file) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.5)
                        audio_data = recognizer.record(source)
                    
                    try:
                        text = recognizer.recognize_google(audio_data)
                        if text.strip():
                            all_text.append(text)
                            print(f"Chunk {start_ms}-{end_ms}ms: {text[:100]}...")
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        print(f"Speech recognition API error: {e}")
                        continue
                        
                except Exception as e:
                    print(f"Error processing chunk {start_ms}-{end_ms}ms: {e}")
                    continue
                    
            finally:
                if os.path.exists(chunk_file):
                    try:
                        os.remove(chunk_file)
                    except:
                        pass
        
        final_text = " ".join(all_text)
        
        if not final_text.strip():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not extract text from audio."
            )
        
        print(f"Successfully extracted {len(all_text)} chunks of text")
        return final_text
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        print(f"Unexpected error in extract_audio_to_text: {error_msg}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text from audio: {error_msg}"
        )
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Warning: Could not clean up temp directory: {e}")