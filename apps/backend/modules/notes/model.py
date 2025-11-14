"""
Notes Model

Database models and Pydantic schemas for notes
"""

from datetime import datetime
from typing import Optional, Any
from sqlmodel import SQLModel, Field, Column
from sqlalchemy import Text
from pydantic import field_validator, ConfigDict
import json


class NoteBase(SQLModel):
    """Base note model with common fields"""
    youtube_url: str = Field(
        description="YouTube video URL"
    )
    video_title: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Title of the YouTube video"
    )
    channel_name: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Name of the YouTube channel"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Summary of the video content"
    )
    key_points: Optional[list[str]] = Field(
        default=None,
        description="Key points from the video"
    )
    timestamps: Optional[list[dict]] = Field(
        default=None,
        description="Important timestamps from the video"
    )
    duration_in_seconds: Optional[int] = Field(
        default=None,
        description="Duration of the video in seconds"
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL of the video thumbnail"
    )
    views: Optional[int] = Field(
        default=None,
        description="Number of views on the video"
    )
    likes: Optional[int] = Field(
        default=None,
        description="Number of likes on the video"
    )
    publish_date: Optional[datetime] = Field(
        default=None,
        description="Date when the video was published"
    )

    @field_validator('youtube_url')
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Validate YouTube URL format"""
        v = v.strip()
        if not v:
            raise ValueError('YouTube URL cannot be empty')
        
        # Check if it's a valid YouTube URL
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError('Invalid YouTube URL. Must be a valid YouTube link')
        
        return v


class Note(NoteBase, table=True):
    """
    Note database model
    
    This is the actual database table representation
    One user can have many notes (one-to-many relationship)
    """
    __tablename__ = "notes"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(
        foreign_key="users.id",
        description="ID of the user who owns this note"
    )
    # Override fields to store as JSON strings in database
    key_points: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Key points from the video (stored as JSON)"
    )
    timestamps: Optional[str] = Field(
        default=None,
        sa_column=Column(Text),
        description="Important timestamps from the video (stored as JSON)"
    )
    duration_in_seconds: Optional[int] = Field(
        default=None,
        description="Duration of the video in seconds"
    )
    thumbnail_url: Optional[str] = Field(
        default=None,
        max_length=500,
        description="URL of the video thumbnail"
    )
    views: Optional[int] = Field(
        default=None,
        description="Number of views on the video"
    )
    likes: Optional[int] = Field(
        default=None,
        description="Number of likes on the video"
    )
    publish_date: Optional[datetime] = Field(
        default=None,
        description="Date when the video was published"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when note was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when note was last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "video_title": "Example Video Title",
                "channel_name": "Example Channel",
                "summary": "This is a summary of the video content...",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "timestamps": [{"time": "00:30", "description": "Introduction"}],
                "duration_in_seconds": 3600,
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
                "views": 1000000,
                "likes": 50000,
                "publish_date": "2024-01-01T00:00:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class NoteCreate(SQLModel):
    """
    Schema for creating a new note
    
    Used when user submits a YouTube URL to create a note
    """
    youtube_url: str = Field(
        description="YouTube video URL"
    )

    @field_validator('youtube_url')
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        """Validate YouTube URL format"""
        v = v.strip()
        if not v:
            raise ValueError('YouTube URL cannot be empty')
        
        # Check if it's a valid YouTube URL
        youtube_domains = ['youtube.com', 'youtu.be', 'www.youtube.com', 'm.youtube.com']
        if not any(domain in v.lower() for domain in youtube_domains):
            raise ValueError('Invalid YouTube URL. Must be a valid YouTube link')
        
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            }
        }
    )


class NoteUpdate(SQLModel):
    """
    Schema for updating note information
    
    All fields are optional to allow partial updates
    """
    video_title: Optional[str] = Field(
        default=None,
        max_length=500
    )
    channel_name: Optional[str] = Field(
        default=None,
        max_length=200
    )
    summary: Optional[str] = Field(default=None)
    key_points: Optional[list[str]] = Field(default=None)
    timestamps: Optional[list[dict]] = Field(default=None)
    duration_in_seconds: Optional[int] = Field(default=None)
    thumbnail_url: Optional[str] = Field(default=None, max_length=500)
    views: Optional[int] = Field(default=None)
    likes: Optional[int] = Field(default=None)
    publish_date: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "video_title": "Updated Video Title",
                "summary": "Updated summary"
            }
        }
    )


class NoteResponse(NoteBase):
    """
    Schema for note response
    
    Used when returning note data to clients
    """
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    @field_validator('key_points', 'timestamps', mode='before')
    @classmethod
    def parse_json_fields(cls, v: Any) -> Any:
        """
        Parse JSON string to Python list/dict when loading from database
        
        If JSON parsing fails, returns empty list to maintain type contract
        (key_points expects list[str], timestamps expects list[dict])
        """
        if v is None:
            return None
        if isinstance(v, str):
            try:
                parsed = json.loads(v)
                # Ensure parsed value is the correct type
                if isinstance(parsed, list):
                    return parsed
                # If parsed value is not a list, return empty list to maintain type contract
                return []
            except (json.JSONDecodeError, TypeError):
                # JSON parsing failed - return empty list to maintain type contract
                # This prevents type validation errors when field expects list but receives string
                return []
        # If already a list/dict, return as-is
        if isinstance(v, list):
            return v
        # If not a list and not None, return empty list to maintain type contract
        return []

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "user_id": 1,
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "video_title": "Example Video Title",
                "channel_name": "Example Channel",
                "summary": "This is a summary of the video content...",
                "key_points": ["Point 1", "Point 2", "Point 3"],
                "timestamps": [{"time": "00:30", "description": "Introduction"}],
                "duration_in_seconds": 3600,
                "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
                "views": 1000000,
                "likes": 50000,
                "publish_date": "2024-01-01T00:00:00",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )

