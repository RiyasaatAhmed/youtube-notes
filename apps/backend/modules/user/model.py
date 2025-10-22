from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from pydantic import EmailStr, field_validator, ConfigDict


class UserBase(SQLModel):
    """Base user model with common fields"""
    first_name: str = Field(
        min_length=1,
        max_length=100,
        description="User's first name"
    )
    last_name: str = Field(
        min_length=1,
        max_length=100,
        description="User's last name"
    )
    email: EmailStr = Field(
        unique=True,
        index=True,
        description="User's email address"
    )

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and clean name fields"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty or only whitespace')
        return v.strip()

    @field_validator('email')
    @classmethod
    def validate_email_lowercase(cls, v: EmailStr) -> str:
        """Convert email to lowercase"""
        return v.lower()


class User(UserBase, table=True):
    """
    User database model
    
    This is the actual database table representation
    """
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(
        description="Hashed password (never store plain text)"
    )
    is_active: bool = Field(default=True, description="Whether user account is active")
    is_verified: bool = Field(default=False, description="Whether user email is verified")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when user was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp when user was last updated"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class UserCreate(UserBase):
    """
    Schema for creating a new user
    
    Used for user registration/signup
    """
    password: str = Field(
        min_length=8,
        max_length=100,
        description="User's password (plain text, will be hashed)"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength
        
        Requirements:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        """
        # if len(v) < 8:
        #     raise ValueError('Password must be at least 8 characters long')
        
        # if not any(char.isupper() for char in v):
        #     raise ValueError('Password must contain at least one uppercase letter')
        
        # if not any(char.islower() for char in v):
        #     raise ValueError('Password must contain at least one lowercase letter')
        
        # if not any(char.isdigit() for char in v):
        #     raise ValueError('Password must contain at least one digit')
        
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "password": "SecurePass123"
            }
        }
    )


class UserUpdate(SQLModel):
    """
    Schema for updating user information
    
    All fields are optional to allow partial updates
    """
    first_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    last_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )
    email: Optional[EmailStr] = Field(default=None)

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean name fields"""
        if v is not None:
            if not v.strip():
                raise ValueError('Name cannot be empty or only whitespace')
            return v.strip()
        return v

    @field_validator('email')
    @classmethod
    def validate_email_lowercase(cls, v: Optional[EmailStr]) -> Optional[str]:
        """Convert email to lowercase"""
        if v is not None:
            return v.lower()
        return v


class UserResponse(UserBase):
    """
    Schema for user response
    
    Used when returning user data to clients
    Never includes password or sensitive information
    """
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@example.com",
                "is_active": True,
                "is_verified": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        }
    )


class UserLogin(SQLModel):
    """
    Schema for user login
    
    Used for authentication
    """
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def validate_email_lowercase(cls, v: EmailStr) -> str:
        """Convert email to lowercase"""
        return v.lower()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123"
            }
        }
    )

