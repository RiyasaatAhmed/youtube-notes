"""
Notes module

Handles note-related functionality including YouTube video processing,
AI-powered note generation, and note management.
"""

from .model import (
    Note,
    NoteBase,
    NoteCreate,
    NoteUpdate,
    NoteResponse
)
from .service import NoteService
from .route import router as notes_router

__all__ = [
    # Models
    "Note",
    "NoteBase",
    "NoteCreate",
    "NoteUpdate",
    "NoteResponse",
    
    # Service
    "NoteService",
    
    # Router
    "notes_router",
    
    # Utilities
    "extract_video_id",
    "validate_youtube_url",
    "get_video_metadata",
    "extract_audio_to_text",
]
