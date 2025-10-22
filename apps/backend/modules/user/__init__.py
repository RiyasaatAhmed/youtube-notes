"""
User module

Handles user-related functionality including authentication,
registration, profile management, etc.
"""

from .model import (
    User,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin
)
from .utils import (
    hash_password,
    verify_password,
    get_full_name
)
from .service import UserService
from .route import router as user_router

__all__ = [
    # Models
    "User",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    
    # Service
    "UserService",
    
    # Router
    "user_router",
    
    # Utilities
    "hash_password",
    "verify_password",
    "get_full_name",
]

