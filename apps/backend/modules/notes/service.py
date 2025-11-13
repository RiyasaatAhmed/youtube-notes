"""
Notes Service

Business logic for notes management including CRUD operations,
YouTube video processing, and Gemini AI integration
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
import logging
import json
from google import genai

from modules.notes.model import Note, NoteCreate, NoteUpdate, NoteResponse
from modules.notes.utils import (
    extract_video_id,
    get_video_metadata,
    validate_youtube_url,
    extract_audio_to_text
)
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
        
        # Store Gemini API key for later use
        self._gemini_api_key = settings.GEMINI_API_KEY
        if not self._gemini_api_key:
            self._logger.warning("GEMINI_API_KEY not found in settings")
    
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
            # Create comprehensive prompt for Gemini
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
2. Create a comprehensive summary (2-3 paragraphs) that captures the essence of the video based on the subtitle text
3. Identify 5-10 key points that represent the main topics and important information
4. Identify 3-7 important timestamps with brief descriptions of what happens at each moment
5. Timestamps should be in MM:SS format (e.g., "05:30", "12:45")
6. Only include timestamps for truly important moments (topic changes, key concepts, important information)
7. Ensure the response is valid JSON only - no markdown formatting, no code blocks, just pure JSON

Return ONLY the JSON object, nothing else."""
            
            # Initialize Gemini client
            if not self._gemini_api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="GEMINI_API_KEY is not configured"
                )
            
            client = genai.Client(api_key=self._gemini_api_key)
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash-lite')
            
            # Generate content
            response = client.models.generate_content(
                model=model_name,
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
        # Validate YouTube URL
        if not validate_youtube_url(note_data.youtube_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid YouTube URL"
            )
        
        # Extract video ID
        try:
            video_id = extract_video_id(note_data.youtube_url)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Check for duplicate note (same video URL for same user)
        statement = select(Note).where(
            Note.user_id == user_id,
            Note.youtube_url == note_data.youtube_url
        )
        existing_note = self._session.exec(statement).first()
        if existing_note:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already have a note for this video. Please use the existing note or choose a different video."
            )
        
        try:
            # Fetch video metadata and subtitle
            self._logger.info(f"Fetching metadata for video: {note_data.youtube_url}")
            metadata = get_video_metadata(video_id)
            video_title = metadata['title']
            channel_name = metadata['channel']
            subtitle_text = metadata.get('subtitle_text', '')
            
            # If no subtitles available, try to extract text from audio
            if not subtitle_text:
                self._logger.info("No subtitles available, attempting to extract text from audio")
                try:
                    subtitle_text = extract_audio_to_text(note_data.youtube_url, video_id)
                    self._logger.info("Successfully extracted text from audio")
                except HTTPException as e:
                    # If audio extraction fails, raise the error
                    raise HTTPException(
                        status_code=e.status_code,
                        detail=f"This video does not have captions available and audio extraction failed: {e.detail}"
                    )
                except Exception as e:
                    self._logger.error(f"Audio extraction failed: {str(e)}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"This video does not have captions available and audio extraction failed: {str(e)}"
                    )
            
            # Generate note content with Gemini
            self._logger.info("Generating note content with Gemini AI")
            generated_data = self._generate_note_with_gemini(
                subtitle_text,
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
                timestamps=json.dumps(generated_data['timestamps']) if generated_data.get('timestamps') else None
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

