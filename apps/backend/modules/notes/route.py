"""
Notes Routes

API endpoints for notes management
"""

from fastapi import APIRouter, Depends, status
from sqlmodel import Session
from typing import Optional, List

from database import get_session
from modules.notes.model import (
    NoteCreate,
    NoteUpdate,
    NoteResponse
)
from modules.notes.service import NoteService
from modules.user.model import User
from core.security import get_current_active_user
from pydantic import BaseModel


router = APIRouter(prefix="/api/notes", tags=["notes"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class NotePagination(BaseModel):
    """Note pagination response"""
    notes: List[NoteResponse]
    total_notes: int
    total_pages: int
    current_page: int
    page_size: int


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_note_service(
    session: Session = Depends(get_session)
) -> NoteService:
    """Dependency injection for NoteService"""
    return NoteService(session=session)


# ============================================================================
# NOTES CRUD ENDPOINTS - Create
# ============================================================================

@router.post(
    "/",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note from YouTube video",
    description="Create a note by providing a YouTube video URL. The system will fetch the transcript and generate notes using AI."
)
def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_active_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Create a new note from YouTube video URL
    
    Requires authentication
    
    - **youtube_url**: Valid YouTube video URL
    
    The system will:
    1. Validate the YouTube URL
    2. Check for duplicate notes (same video for same user)
    3. Fetch video transcript
    4. Generate note content using AI (video title, channel name, summary, key points, timestamps)
    5. Save the note to your account
    
    Returns the created note with all generated content.
    """
    note = note_service.create_note(
        user_id=current_user.id,
        note_data=note_data
    )
    return note


# ============================================================================
# NOTES CRUD ENDPOINTS - Read
# ============================================================================

@router.get(
    "/",
    response_model=NotePagination,
    summary="Get all notes",
    description="Get paginated list of notes for the current user with optional search"
)
def get_notes(
    current_page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get paginated list of notes
    
    Requires authentication
    Only returns notes that belong to the current user
    
    - **current_page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **search**: Search term for title, channel, or summary
    """
    result = note_service.get_notes(
        user_id=current_user.id,
        current_page=current_page,
        page_size=page_size,
        search=search
    )
    
    return NotePagination(**result)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get note by ID",
    description="Get specific note information by ID"
)
def get_note_by_id(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Get note by ID
    
    Requires authentication
    Only returns note if it belongs to the current user
    
    - **note_id**: Note ID to retrieve
    """
    note = note_service.get_note_by_id(note_id, current_user.id)
    return note


# ============================================================================
# NOTES CRUD ENDPOINTS - Update
# ============================================================================

@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update note",
    description="Update note information"
)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_active_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Update note information
    
    Requires authentication
    Users can only update their own notes
    
    - **note_id**: Note ID to update
    - **note_data**: Fields to update (all optional):
      - video_title
      - channel_name
      - summary
      - key_points
      - timestamps
    """
    note = note_service.update_note(
        note_id=note_id,
        user_id=current_user.id,
        note_data=note_data
    )
    return note


# ============================================================================
# NOTES CRUD ENDPOINTS - Delete
# ============================================================================

@router.delete(
    "/{note_id}",
    response_model=MessageResponse,
    summary="Delete note",
    description="Delete a note permanently"
)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_active_user),
    note_service: NoteService = Depends(get_note_service)
):
    """
    Delete note
    
    Requires authentication
    Users can only delete their own notes
    WARNING: This action cannot be undone
    
    - **note_id**: Note ID to delete
    """
    result = note_service.delete_note(note_id, current_user.id)
    return MessageResponse(**result)