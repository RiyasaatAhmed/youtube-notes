"""
Notes Service

Business logic for notes management including CRUD operations,
YouTube video processing, and Gemini AI integration
"""

import re
import os
import xml.etree.ElementTree as ET
from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
import logging
import json
from google import genai
from pytubefix import YouTube
from pytubefix.cli import on_progress
import requests
from pydub import AudioSegment
from deepgram import DeepgramClient


from modules.notes.model import Note, NoteCreate, NoteUpdate, NoteResponse
from core.config import settings


logger = logging.getLogger(__name__)


class NoteService:
    """Service class for note-related business logic"""
    
    def __init__(self, session: Session):
        """
        Initialize NoteService
        
        Args:
            session: Database session
        """
        self._session = session
        self._logger = logger
        
        self.gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self._deepgram_client = DeepgramClient(api_key=settings.DEEPGRAM_API_KEY)
    
    # ============================================================================
    # HELPER METHODS - Note Retrieval
    # ============================================================================
    
    def _get_note_by_id(self, note_id: int, user_id: int) -> Note:
        """
        Retrieve note by ID for a specific user or raise 404
        
        Args:
            note_id: Note ID
            user_id: User ID (to ensure user owns the note)
            
        Returns:
            Note object
            
        Raises:
            HTTPException: If note not found or user doesn't own it
        """
        note = self._session.get(Note, note_id)
        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Note with ID {note_id} not found"
            )
        
        # Check if user owns the note
        if note.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this note"
            )
        
        return note
    
    # ============================================================================
    # HELPER METHODS - Gemini AI Integration
    # ============================================================================
    
    def _generate_note_with_gemini(
        self, 
        subtitle_text: str, 
        video_url: str,
        video_title: str,
        channel_name: str
    ) -> Dict[str, Any]:
        """
        Generate note content using Google Gemini AI
        
        Args:
            subtitle_text: Video subtitle text
            video_url: YouTube video URL
            video_title: Video title
            channel_name: Channel name
            
        Returns:
            Dictionary with generated note data
            
        Raises:
            HTTPException: If Gemini API fails
        """
        try:
            # Escape variables that might contain special characters
            # Replace curly braces in subtitle_text to avoid format specifier errors
            safe_subtitle_text = str(subtitle_text).replace('{', '{{').replace('}', '}}')
            safe_video_title = str(video_title).replace('{', '{{').replace('}', '}}')
            safe_channel_name = str(channel_name).replace('{', '{{').replace('}', '}}')
            safe_video_url = str(video_url).replace('{', '{{').replace('}', '}}')
            
            # CRISP-E formatted prompt (Context → Role → Instructions → Style → Parameters → Examples)
            # NOTE: keep the f-string so variables are injected. Use double braces {{ }} for literal braces in JSON.
            prompt = f"""
                C — Context
                You will receive raw subtitle text and video metadata (title, channel, URL). Analyze the subtitle text deeply and extract structured, accurate, human-readable notes that allow a reader to understand what the video is about, its main ideas, and where important content appears. Use the subtitle text as the primary source. If you cannot detect the language confidently, default to the language of the subtitle text provided.

                INPUT (replace the placeholders before calling the model):
                - video_title: {safe_video_title}
                - channel_name: {safe_channel_name}
                - video_url: {safe_video_url}
                - subtitle_text: {safe_subtitle_text}

                R — Role
                Act as an expert note-taking assistant and world-class explainer who: distills long videos into clear notes, identifies key teaching points, extracts important quotes, and produces clean, valid JSON output with zero extra commentary.

                I — Instructions
                1. Use the EXACT video_title and channel_name provided above — do NOT change them.
                2. Detect the language of subtitle_text and produce every field text (summary, key_points, descriptions, quotes) in that detected language. Add a "language" field with an ISO 639-1 language code and the language name (e.g., "en - English").
                3. Return ONLY a single, valid JSON object (no markdown, no code fences, no extra commentary). Ensure the JSON is well-formed and escapes any characters necessary so it parses cleanly.
                4. Use the following JSON schema exactly (do not add extra top-level fields).
                5. Timestamps requirements:
                   - Provide between 3 and 7 timestamp entries (only truly important moments).
                   - Format: use MM:SS for videos under 1 hour; use HH:MM:SS for videos 1 hour or longer (if video length unknown, default to MM:SS).
                   - Timestamps must be sorted ascending.
                   - If an exact timestamp cannot be determined from subtitle_text, provide the nearest approximate timestamp and append " (approx)" to the time value.
                6. Key points requirements:
                   - Provide 5–10 items.
                   - Each key point should be a single sentence or phrase (5–25 words).
                   - Order by importance (most important first).
                7. Summary requirements:
                   - Main "summary" must be 2–3 paragraphs, each paragraph 2–4 sentences.
                   - Also include a "short_summary" (one sentence, max 30 words).
                8. Important quotes:
                   - Provide up to 3 quotes (if present in subtitles), include the exact quote and the timestamp.
                   - Preserve original punctuation and casing.
                9. JSON safety and validation:
                   - Ensure no trailing commas.
                   - Escape internal quotes and control characters so the JSON parses.
                   - Do not include any explanatory text outside the JSON object.
                10. If subtitle_text is empty or contains insufficient content, return a valid JSON object with empty arrays and brief explanatory fields in the same language.

                S — Style
                - All textual output must be in the detected language of the subtitle_text.
                - Preserve original wording and casing when extracting quotes.
                - Write summaries in a clear, professional, and informative tone.
                - Key points should be concise and actionable.
                - Timestamp descriptions should be brief (10-30 words) and descriptive.
                - Notes for reviewers should be helpful and constructive.

                P — Parameters (Hard constraints)
                - Output MUST be a single valid JSON object. No markdown, no code fences, no trailing commas.
                - Escape special characters to ensure JSON parses.
                - Timestamp format: MM:SS for videos < 1 hour; HH:MM:SS for videos ≥ 1 hour. If video length unknown, default to MM:SS.
                - Language: include a "language" field with ISO 639-1 code and language name (e.g., "en - English").
                - Keys and structure must follow the exact JSON schema below (do not add top-level fields):

                {{
                "video_title": "{safe_video_title}",
                "channel_name": "{safe_channel_name}",
                "video_url": "{safe_video_url}",
                "language": "xx - Language Name",
                "summary": "A comprehensive summary of the video content in 2-3 paragraphs. Cover the main topics, key concepts, and the overall message, using the subtitle_text as the source.",
                "short_summary": "A one-sentence summary (max 30 words) in the same language.",
                "key_points": [
                    "5-10 concise key points (each 5-25 words) that capture the main ideas; return exactly as many items as are needed between 5 and 10."
                ],
                "important_quotes": [
                    {{
                    "quote": "A short important quotation (up to 2 lines) from the subtitles (preserve original wording).",
                    "time": "MM:SS or HH:MM:SS if video ≥ 1 hour"
                    }}
                ],
                "timestamps": [
                    {{
                    "time": "MM:SS or HH:MM:SS if video ≥ 1 hour",
                    "description": "Brief description (10-30 words) of what happens at this timestamp — major topic change, key example, or critical fact."
                    }}
                ],
                "notes_for_reviewers": "Optional short suggestions (1-3 bullet-style sentences) about what to check in the transcript or where automatic subtitle errors may affect understanding."
                }}

                E — Examples
                Example 1 — Normal case:
                Input:
                video_title: "How Neural Networks Learn"
                channel_name: "AI Explained"
                video_url: "https://youtube.com/abc123"
                subtitle_text: "Today we learn how neural networks adjust weights... Backpropagation helps minimize loss..."

                Output:
                {{
                "video_title": "How Neural Networks Learn",
                "channel_name": "AI Explained",
                "video_url": "https://youtube.com/abc123",
                "language": "en - English",
                "summary": "The video explains how neural networks adjust weights using backpropagation. It covers the fundamental concepts of gradient descent and error minimization. The explanation provides clear insights into the learning mechanism of artificial intelligence systems.",
                "short_summary": "A clear introduction to how neural networks learn using backpropagation.",
                "key_points": [
                    "Neural networks improve by adjusting weights to reduce error.",
                    "Backpropagation calculates gradients to guide learning.",
                    "Gradient descent minimizes loss functions effectively."
                ],
                "important_quotes": [
                    {{
                    "quote": "Backpropagation is the learning engine of neural networks.",
                    "time": "00:45"
                    }}
                ],
                "timestamps": [
                    {{
                    "time": "00:10",
                    "description": "Introduction to neural networks and learning process."
                    }},
                    {{
                    "time": "00:45",
                    "description": "Explanation of backpropagation mechanism."
                    }}
                ],
                "notes_for_reviewers": "Verify auto-generated timestamps and quote extraction."
                }}

                Example 2 — Empty subtitle case:
                Input:
                video_title: "Sample Video"
                channel_name: "Sample Channel"
                video_url: "https://youtube.com/xyz789"
                subtitle_text: ""

                Output:
                {{
                "video_title": "Sample Video",
                "channel_name": "Sample Channel",
                "video_url": "https://youtube.com/xyz789",
                "language": "en - English",
                "summary": "",
                "short_summary": "",
                "key_points": [],
                "important_quotes": [],
                "timestamps": [],
                "notes_for_reviewers": "Insufficient subtitle text to extract notes."
                }}

                BEGIN analysis of the provided subtitle_text and produce the JSON output now.
                """
            
            # Generate content using Gemini
            response = self.gemini_client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            elif response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            # Parse JSON
            try:
                note_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                self._logger.error(f"Failed to parse Gemini response as JSON: {e}")
                self._logger.error(f"Response text: {response_text[:500]}")
                # Fallback: create a basic structure with valid required fields
                # Note: timestamps must have at least one entry to pass validation
                note_data = {
                    "video_title": video_title,
                    "channel_name": channel_name,
                    "summary": response_text[:1000] if len(response_text) > 1000 else response_text,
                    "key_points": ["Key point extracted from video"],
                    "timestamps": [
                        {
                            "time": "00:00",
                            "description": "Video content extracted (parsing failed, using fallback)"
                        }
                    ]
                }
            
            # Validate and structure the response
            key_points_list = note_data.get('key_points', [])
            timestamps_list = note_data.get('timestamps', [])
            
            result = {
                'video_title': note_data.get('video_title', video_title),
                'channel_name': note_data.get('channel_name', channel_name),
                'summary': note_data.get('summary', ''),
                'key_points': key_points_list if isinstance(key_points_list, list) else [],
                'timestamps': timestamps_list if isinstance(timestamps_list, list) else []
            }
            
            # Validate that all required fields have values
            missing_fields = []
            if not result['video_title'] or not str(result['video_title']).strip():
                missing_fields.append('video_title')
            if not result['channel_name'] or not str(result['channel_name']).strip():
                missing_fields.append('channel_name')
            if not result['summary'] or not str(result['summary']).strip():
                missing_fields.append('summary')
            
            # Check key_points (should be a non-empty list)
            if not result['key_points'] or not isinstance(result['key_points'], list) or len(result['key_points']) == 0:
                missing_fields.append('key_points')
            
            # Check timestamps (should be a non-empty list)
            if not result['timestamps'] or not isinstance(result['timestamps'], list) or len(result['timestamps']) == 0:
                missing_fields.append('timestamps')
            
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to generate complete note. Missing required fields: {', '.join(missing_fields)}. Please try again or choose a different video."
                )
            
            self._logger.info("Successfully generated note with Gemini AI")
            return result
            
        except Exception as e:
            self._logger.error(f"Error generating note with Gemini: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate note with AI: {str(e)}"
            )

    
    # ============================================================================
    # HELPER METHODS - Pagination
    # ============================================================================
    
    def _validate_pagination_params(
        self,
        current_page: int,
        page_size: int
    ) -> tuple[int, int]:
        """
        Validate and normalize pagination parameters
        
        Args:
            current_page: Page number
            page_size: Items per page
            
        Returns:
            Validated page and size
        """
        validated_page = max(1, current_page)
        validated_size = max(1, min(page_size, 100))  # Max 100 items per page
        return validated_page, validated_size
    
    def _calculate_pagination(
        self,
        total_items: int,
        current_page: int,
        page_size: int
    ) -> tuple[int, int, int, int]:
        """
        Calculate pagination metadata
        
        Args:
            total_items: Total number of items
            current_page: Current page number
            page_size: Items per page
            
        Returns:
            total_pages, adjusted_page, start_index, end_index
        """
        total_pages = max(1, (total_items + page_size - 1) // page_size)
        adjusted_page = min(current_page, total_pages)
        start_index = (adjusted_page - 1) * page_size
        end_index = start_index + page_size
        return total_pages, adjusted_page, start_index, end_index
    
    # ============================================================================
    # CRUD OPERATIONS - Create
    # ============================================================================
    
    def create_note(self, user_id: int, note_data: NoteCreate) -> Note:
        """
        Create a new note from YouTube video URL
        
        Args:
            user_id: User ID who owns the note
            note_data: Note creation data (YouTube URL)
            
        Returns:
            Created note object
            
        Raises:
            HTTPException: If URL is invalid, duplicate, or processing fails
        """
        # Check if the video is already in the database
        statement = select(Note).where(
            Note.user_id == user_id,
            Note.youtube_url == note_data.youtube_url
        )
        existing_note = self._session.exec(statement).first()
        if existing_note:
            # Return existing note instead of raising error
            self._logger.info(f"Note already exists for video {note_data.youtube_url}, returning existing note ID: {existing_note.id}")
            return existing_note
           
        try:            
            # Get video metadata
            self._logger.info(f"Fetching metadata for video: {note_data.youtube_url}")
            video = self.get_video_metadata_from_youtube_video_url(note_data.youtube_url)
            subtitle = video.get('caption', '')
            video_title = video.get('title', '')
            channel_name = video.get('channel_name', '')
            
            # If no subtitle text was extracted, raise error
            if not subtitle or not subtitle.strip():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No captions/subtitles available for this video. Please choose a video with captions."
                )
            
            # Generate note content with Gemini
            self._logger.info("Generating note content with Gemini AI")
            generated_data = self._generate_note_with_gemini(
                subtitle,
                note_data.youtube_url,
                video_title,
                channel_name
            )
            
            # Validate all required fields before creating note
            missing_fields = []
            if not generated_data.get('video_title') or not str(generated_data['video_title']).strip():
                missing_fields.append('video_title')
            if not generated_data.get('channel_name') or not str(generated_data['channel_name']).strip():
                missing_fields.append('channel_name')
            if not generated_data.get('summary') or not str(generated_data['summary']).strip():
                missing_fields.append('summary')
            
            # Validate key_points (should be a non-empty list)
            key_points = generated_data.get('key_points', [])
            if not key_points or not isinstance(key_points, list) or len(key_points) == 0:
                missing_fields.append('key_points')
            
            # Validate timestamps (should be a non-empty list)
            timestamps = generated_data.get('timestamps', [])
            if not timestamps or not isinstance(timestamps, list) or len(timestamps) == 0:
                missing_fields.append('timestamps')
            
            if missing_fields:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Cannot create note: Missing required fields ({', '.join(missing_fields)}). The AI was unable to generate complete note data. Please try again or choose a different video."
                )
            
            # Create note instance
            # Convert Python lists/dicts to JSON strings for database storage
            db_note = Note(
                user_id=user_id,
                youtube_url=note_data.youtube_url,
                video_title=generated_data['video_title'],
                channel_name=generated_data['channel_name'],
                summary=generated_data['summary'],
                key_points=json.dumps(generated_data['key_points']) if generated_data.get('key_points') else None,
                timestamps=json.dumps(generated_data['timestamps']) if generated_data.get('timestamps') else None,
                duration_in_seconds=video.get('duration_in_seconds'),
                thumbnail_url=video.get('thumbnail_url'),
                views=video.get('views'),
                likes=video.get('likes'),
                publish_date=video.get('publish_date')
            )
            
            # Save to database
            self._session.add(db_note)
            self._session.commit()
            self._session.refresh(db_note)
            
            self._logger.info(f"Created note with ID: {db_note.id} for user {user_id}")
            return db_note
            
        except HTTPException:
            raise
        except Exception as e:
            error_message = str(e)
            self._logger.error(f"Failed to create note: {error_message}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create note: {error_message}"
            )
    
    # ============================================================================
    # CRUD OPERATIONS - Read
    # ============================================================================
    
    def get_note_by_id(self, note_id: int, user_id: int) -> Note:
        """
        Get note by ID
        
        Args:
            note_id: Note ID
            user_id: User ID (to ensure user owns the note)
            
        Returns:
            Note object
            
        Raises:
            HTTPException: If note not found or user doesn't own it
        """
        return self._get_note_by_id(note_id, user_id)
    
    def get_notes(
        self,
        user_id: int,
        current_page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of notes for a user with optional search
        
        Args:
            user_id: User ID
            current_page: Page number
            page_size: Items per page
            search: Search term (searches title, channel, summary)
            
        Returns:
            Dictionary with notes list and pagination metadata
        """
        # Build query - only get notes for this user
        query = select(Note).where(Note.user_id == user_id)
        
        # Apply search filter
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(Note.video_title).like(search_term),
                    func.lower(Note.channel_name).like(search_term),
                    func.lower(Note.summary).like(search_term)
                )
            )
        
        # Order by created_at desc
        query = query.order_by(Note.created_at.desc())
        
        # Get all notes matching query
        all_notes = self._session.exec(query).all()
        
        # Validate and calculate pagination
        current_page, page_size = self._validate_pagination_params(
            current_page, page_size
        )
        total_notes = len(all_notes)
        total_pages, current_page, start_index, end_index = self._calculate_pagination(
            total_notes, current_page, page_size
        )
        
        # Get paginated notes
        paginated_notes = all_notes[start_index:end_index]
        
        return {
            "notes": paginated_notes,
            "total_notes": total_notes,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
    
    # ============================================================================
    # CRUD OPERATIONS - Update
    # ============================================================================
    
    def update_note(
        self,
        note_id: int,
        user_id: int,
        note_data: NoteUpdate
    ) -> Note:
        """
        Update note information
        
        Args:
            note_id: Note ID to update
            user_id: User ID (to ensure user owns the note)
            note_data: Update data
            
        Returns:
            Updated note object
            
        Raises:
            HTTPException: If note not found or user doesn't own it
        """
        # Get the note
        note = self._get_note_by_id(note_id, user_id)
        
        # Update fields
        update_data = note_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            # Convert Python lists/dicts to JSON strings for database storage
            if key in ('key_points', 'timestamps') and value is not None:
                setattr(note, key, json.dumps(value))
            else:
                setattr(note, key, value)
        
        # Update timestamp
        note.updated_at = datetime.utcnow()
        
        # Save to database
        self._session.add(note)
        self._session.commit()
        self._session.refresh(note)
        
        self._logger.info(f"Updated note with ID: {note_id}")
        return note
    
    # ============================================================================
    # CRUD OPERATIONS - Delete
    # ============================================================================
    
    def delete_note(self, note_id: int, user_id: int) -> Dict[str, str]:
        """
        Delete a note
        
        Args:
            note_id: Note ID to delete
            user_id: User ID (to ensure user owns the note)
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If note not found or user doesn't own it
        """
        note = self._get_note_by_id(note_id, user_id)
        
        # Delete note
        self._session.delete(note)
        self._session.commit()
        
        self._logger.info(f"Deleted note with ID: {note_id}")
        return {"message": f"Note with ID {note_id} deleted successfully"}
    
    
    # ============================================================================
    # HELPER METHODS - Get Audio from Video
    # ============================================================================
    
    def get_video_metadata_from_youtube_video_url(self, video_url: str) -> Dict[str, Any]:
        try:
            yt = YouTube(video_url, on_progress_callback = on_progress)
            if len(yt.captions.keys()) > 0:
                first_lang_code = list(yt.captions.keys())[0].code
                caption = yt.captions[first_lang_code]
                
                response = requests.get(
                    caption.url, 
                    timeout=10,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.youtube.com/"
                    }
                )
                response.raise_for_status()
                subtitle_content = self._extract_text_from_xml_transcript(response.text)
            else:
                subtitle_content = self._get_subtitle_from_audio(video_url)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download audio from YouTube video: {str(e)}"
            )
            
        return {
            "title": yt.title,
            "caption": subtitle_content,
            "channel_name": yt.author,
            "duration_in_seconds": yt.length,
            "thumbnail_url": yt.thumbnail_url,
            "views": yt.views,
            "likes": yt.likes,
            "publish_date": yt.publish_date,
            
        }
        
        
    def _extract_text_from_xml_transcript(self, xml_content: str) -> str:
        """
        Extract text content from XML transcript.
        
        Parses XML transcript and extracts all text from <text> tags,
        combining them into a single string.
        
        Args:
            xml_content: XML transcript content
            
        Returns:
            Extracted text content as a single string
        """
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Extract all text from <text> tags
            text_parts = []
            for text_elem in root.findall('.//text'):
                text_content = text_elem.text
                if text_content:
                    text_parts.append(text_content.strip())
            
            # Join all text parts with spaces
            extracted_text = " ".join(text_parts)
            
            # Clean up extra whitespace
            extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()
            
            return extracted_text
            
        except ET.ParseError as e:
            self._logger.warning(f"Failed to parse XML transcript, trying regex extraction: {str(e)}")
            # Fallback: Use regex to extract text if XML parsing fails
            text_pattern = r'<text[^>]*>([^<]+)</text>'
            matches = re.findall(text_pattern, xml_content)
            if matches:
                extracted_text = " ".join(match.strip() for match in matches)
                extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()
                return extracted_text
            else:
                # If regex also fails, return original content
                self._logger.error("Failed to extract text from transcript using both XML parsing and regex")
                return xml_content
        except Exception as e:
            self._logger.error(f"Unexpected error extracting text from XML: {str(e)}")
            return xml_content
    
    
    def _get_subtitle_from_audio(self, video_url: str) -> str:
        """
        Get subtitle from audio of a YouTube video
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Subtitle text
        """
        try:
            yt = YouTube(video_url, on_progress_callback=on_progress)

            # Get the backend directory path (parent of modules directory)
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            temp_audio_dir = os.path.join(backend_dir, 'temp_audio_files')
            audio_file_name = video_url.split("=")[-1] + ".wav"
            
            audio_file_path = os.path.join(temp_audio_dir, audio_file_name)
            
            # Create directory if it doesn't exist
            os.makedirs(temp_audio_dir, exist_ok=True)
            
            ys = yt.streams.get_audio_only()
            ys.download(output_path=temp_audio_dir)

            audio = AudioSegment.from_file(os.path.join(temp_audio_dir, ys.default_filename), format="m4a")
            audio.export(audio_file_path, format="wav")
            
            # delete the original m4a file
            os.remove(os.path.join(temp_audio_dir, ys.default_filename))
            
            # convert audio to text
            try:
                with open(audio_file_path, "rb") as audio_file:
                    response = self._deepgram_client.listen.v1.media.transcribe_file(
                        request=audio_file.read(),
                        model=settings.DEEPGRAM_MODEL,
                        smart_format=True,
                    )
                
                transcript = response.results.channels[0].alternatives[0].transcript
                os.remove(audio_file_path)
                return transcript

            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to convert audio to text: {str(e)}"
                )
  
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get subtitle from audio of YouTube video: {str(e)}"
            )

        
        

