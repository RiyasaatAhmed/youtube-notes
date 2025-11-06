from fastapi import APIRouter, status, HTTPException
from google import genai
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable
import yt_dlp
from modules.notes.get_video_metadata import get_video_metadata

from core.config import settings

router = APIRouter(prefix="/api/notes", tags=["notes"])


def extract_video_id(youtube_url: str) -> str:
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'm\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    
    raise ValueError(f"Invalid YouTube URL: {youtube_url}")


@router.post(
    "/create-note",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Create a new note for a YouTube video"
)
def create_note(
    video_url: str,
):
    """
    Create a new note for a YouTube video
    
    This endpoint takes a YouTube video URL and uses Gemini AI to generate
    comprehensive notes including:
    - Video title and channel name
    - Key points and main topics
    - Timestamps for important sections
    - Summary of the content
    """
    # Get API key from settings
    api_key = settings.GEMINI_API_KEY
    model = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GEMINI_API_KEY is not configured"
        )
    
    # Extract video ID
    try:
        video_id = extract_video_id(video_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Fetch video metadata (title, channel)
    metadata = get_video_metadata(video_id)
    video_title = metadata['title']
    channel_name = metadata['channel']
    subtitle_text = metadata['subtitle_text']
    
    # Initialize Gemini client
    client = genai.Client(api_key=api_key)
    
    # Create comprehensive prompt for Gemini with actual subtitle text
    prompt = f"""You are an expert at analyzing YouTube video subtitle text and creating comprehensive, well-structured notes.

I have provided you with the actual video subtitle text below. Please analyze it and create detailed notes in JSON format.

VIDEO INFORMATION:
- Video Title: {video_title}
- Channel Name: {channel_name}
- Video URL: {video_url}

VIDEO SUBTITLE TEXT:
{subtitle_text}

Please provide your response as a valid JSON object with the following structure:
{{
    "video_title": "{video_title}",
    "channel_name": "{channel_name}",
    "summary": "A comprehensive summary of the video content in 2-3 paragraphs. This should cover the main topics, key concepts, and overall message of the video.",
    "key_points": [
        "Key point 1 - A clear and concise main point from the video",
        "Key point 2 - Another important point",
        "Key point 3 - Continue with 5-10 key points that capture the main topics and important information"
    ],
    "timestamps": [
        {{
            "time": "00:30",
            "description": "Brief description of what happens at this timestamp - important moments, topic changes, or key information"
        }},
        {{
            "time": "02:15",
            "description": "Another important timestamp with description"
        }}
    ]
}}

IMPORTANT INSTRUCTIONS:
1. Use the EXACT video title and channel name provided above - do NOT change them
2. Create a comprehensive summary (2-3 paragraphs) that captures the essence of the video based on the transcript
3. Identify 5-10 key points that represent the main topics and important information
4. Identify 3-7 important timestamps with brief descriptions of what happens at each moment
5. Timestamps should be in MM:SS format (e.g., "05:30", "12:45")
6. Only include timestamps for truly important moments (topic changes, key concepts, important information)
7. Ensure the response is valid JSON only - no markdown formatting, no code blocks, just pure JSON
8. If you cannot access the video content, return an error message in the JSON format

Return ONLY the JSON object, nothing else."""
    
    try:
        # Generate content with Gemini
        response = client.models.generate_content(
            model=model,
            contents=prompt
        )
        
        # Extract the response text
        response_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]
        response_text = response_text.strip()
        
        # Parse JSON response
        try:
            note_data = json.loads(response_text)
        except json.JSONDecodeError as e:
            # If JSON parsing fails, return the raw response for debugging
            return {
                "error": "Failed to parse Gemini response as JSON",
                "raw_response": response_text[:500],  # First 500 chars for debugging
                "parse_error": str(e)
            }
        
        # Return the note data
        return {
            "message": "Note created successfully",
            "video_url": video_url,
            "note": note_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate note: {str(e)}"
        )