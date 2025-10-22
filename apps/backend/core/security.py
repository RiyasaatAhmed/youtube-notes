"""
Security utilities for authentication and authorization

Handles JWT token creation, verification, and user authentication
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import HTTPException, status, Request, Depends, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from core.config import settings
from database import get_session
from modules.user.model import User

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Convert datetime to timestamp (required by JWT)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "access"
    })
    
    print(f"🔐 Creating access token with payload: {to_encode}")
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    print(f"✅ Access token created: {encoded_jwt[:20]}...")
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Convert datetime to timestamp (required by JWT)
    to_encode.update({
        "exp": int(expire.timestamp()),
        "iat": int(datetime.utcnow().timestamp()),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        print(f"🔍 Verifying token: {token[:20]}...")
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        print(f"✅ Token verified successfully. Payload: {payload}")
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.JWTClaimsError as e:
        print(f"❌ Invalid token claims: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        print(f"❌ Could not validate credentials: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract token from request (cookies or Authorization header)
    
    Args:
        request: FastAPI request object
        
    Returns:
        Token string or None if not found
    """
    # Try to get token from cookie first
    token = request.cookies.get(settings.COOKIE_NAME)
    if token:
        return token
    
    # Try to get token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    
    return None


def get_current_user_id(request: Request) -> int:
    """
    Get current user ID from token in request
    
    Args:
        request: FastAPI request object
        
    Returns:
        User ID
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    token = get_token_from_request(request)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = verify_token(token)
    user_id_str = payload.get("sub")
    
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Convert string user_id to integer
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token"
        )
    
    return user_id


async def get_current_user(
    request: Request,
    session: Session = Depends(get_session)
) -> User:
    """
    Get current authenticated user
    
    Dependency for protecting routes
    
    Args:
        request: FastAPI request object
        session: Database session
        
    Returns:
        Current user object
        
    Raises:
        HTTPException: If user not found or not authenticated
    """

    user_id = get_current_user_id(request)
    
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check)
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def set_auth_cookie(response: Response, token: str) -> None:
    """
    Set authentication cookie in response
    
    Args:
        response: FastAPI response object
        token: JWT token to store in cookie
    """
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=token,
        max_age=settings.COOKIE_MAX_AGE,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )


def clear_auth_cookie(response: Response) -> None:
    """
    Clear authentication cookie from response
    
    Args:
        response: FastAPI response object
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        httponly=settings.COOKIE_HTTPONLY,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE
    )

