"""
User Routes

API endpoints for user management and authentication
"""

from fastapi import APIRouter, Depends, Response, status, Request
from sqlmodel import Session
from typing import Optional, List

from database import get_session
from modules.user.model import (
    User,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin
)
from modules.user.service import UserService
from core.security import (
    get_current_user,
    get_current_active_user,
    create_access_token,
    create_refresh_token,
    set_auth_cookie,
    clear_auth_cookie
)
from pydantic import BaseModel


router = APIRouter(prefix="/api/users", tags=["users"])


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginResponse(BaseModel):
    """Login response model"""
    message: str
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserPagination(BaseModel):
    """User pagination response"""
    users: List[UserResponse]
    total_users: int
    total_pages: int
    current_page: int
    page_size: int


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_user_service(
    session: Session = Depends(get_session)
) -> UserService:
    """Dependency injection for UserService"""
    return UserService(session=session)


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email and password"
)
def register_user(
    response: Response,
    user_data: UserCreate,
    user_service: UserService = Depends(get_user_service)
):
    """
    Register a new user
    
    - **first_name**: User's first name
    - **last_name**: User's last name
    - **email**: Valid email address (will be lowercased)
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    
    Returns created user data and sets authentication cookie
    """
    # Create user
    user = user_service.create_user(user_data)
    
    # Create access token (sub must be string)
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set cookie
    set_auth_cookie(response, access_token)
    
    return user


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login user",
    description="Authenticate user with email and password"
)
def login_user(
    response: Response,
    login_data: UserLogin,
    user_service: UserService = Depends(get_user_service)
):
    """
    Login user with email and password
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT token and user data, sets authentication cookie
    """
    # Authenticate user
    user = user_service.authenticate_user(
        email=login_data.email,
        password=login_data.password
    )
    
    # Create tokens (sub must be string)
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Set cookie
    set_auth_cookie(response, access_token)
    
    return LoginResponse(
        message="Login successful",
        access_token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout current user and clear authentication cookie"
)
def logout_user(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Logout user
    
    Clears authentication cookie
    Requires authentication
    """
    clear_auth_cookie(response)
    return MessageResponse(message="Logout successful")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get current authenticated user information"
)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Requires authentication
    Returns user data for the currently logged-in user
    """
    return current_user


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
def refresh_access_token(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token
    
    Requires authentication
    Returns new access and refresh tokens
    """
    # Create new tokens (sub must be string)
    access_token = create_access_token(data={"sub": str(current_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(current_user.id)})
    
    # Set cookie
    set_auth_cookie(response, access_token)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(current_user)
    )


# ============================================================================
# USER CRUD ENDPOINTS - Read
# ============================================================================

@router.get(
    "/",
    response_model=UserPagination,
    summary="Get all users",
    description="Get paginated list of users with optional filters"
)
def get_users(
    current_page: int = 1,
    page_size: int = 10,
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get paginated list of users
    
    Requires authentication
    
    - **current_page**: Page number (default: 1)
    - **page_size**: Items per page (default: 10, max: 100)
    - **search**: Search term for name or email
    - **is_active**: Filter by active status
    """
    result = user_service.get_users(
        current_page=current_page,
        page_size=page_size,
        search=search,
        is_active=is_active
    )
    
    return UserPagination(**result)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get specific user information by ID"
)
def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get user by ID
    
    Requires authentication
    
    - **user_id**: User ID to retrieve
    """
    user = user_service.get_user_by_id(user_id)
    return user


# ============================================================================
# USER CRUD ENDPOINTS - Update
# ============================================================================

@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information"
)
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update user information
    
    Requires authentication
    Users can only update their own information
    
    - **user_id**: User ID to update
    - **user_data**: Fields to update (all optional)
    """
    # Check if user is updating their own data
    if current_user.id != user_id:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own information"
        )
    
    user = user_service.update_user(user_id, user_data)
    return user


@router.patch(
    "/{user_id}/activate",
    response_model=UserResponse,
    summary="Activate user",
    description="Activate user account"
)
def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Activate user account
    
    Requires authentication
    
    - **user_id**: User ID to activate
    """
    user = user_service.activate_user(user_id)
    return user


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate user",
    description="Deactivate user account"
)
def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Deactivate user account
    
    Requires authentication
    
    - **user_id**: User ID to deactivate
    """
    user = user_service.deactivate_user(user_id)
    return user


@router.patch(
    "/{user_id}/verify",
    response_model=UserResponse,
    summary="Verify user email",
    description="Mark user email as verified"
)
def verify_user_email(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Verify user email
    
    Requires authentication
    
    - **user_id**: User ID to verify
    """
    user = user_service.verify_user_email(user_id)
    return user


# ============================================================================
# USER CRUD ENDPOINTS - Delete
# ============================================================================

@router.delete(
    "/{user_id}",
    response_model=MessageResponse,
    summary="Delete user (soft delete)",
    description="Deactivate user account (soft delete)"
)
def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Delete user (soft delete)
    
    Requires authentication
    Marks user as inactive instead of permanently deleting
    
    - **user_id**: User ID to delete
    """
    result = user_service.delete_user(user_id)
    return MessageResponse(**result)


@router.delete(
    "/{user_id}/permanent",
    response_model=MessageResponse,
    summary="Permanently delete user",
    description="Permanently remove user from database"
)
def permanent_delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Permanently delete user
    
    Requires authentication
    WARNING: This action cannot be undone
    
    - **user_id**: User ID to permanently delete
    """
    result = user_service.permanent_delete_user(user_id)
    return MessageResponse(**result)

