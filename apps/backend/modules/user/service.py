"""
User Service

Business logic for user management including CRUD operations,
authentication, and authorization
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Session, select, func, or_
from fastapi import HTTPException, status
import logging

from modules.user.model import User, UserCreate, UserUpdate, UserResponse
from modules.user.utils import hash_password, verify_password


logger = logging.getLogger(__name__)


class UserService:
    """Service class for user-related business logic"""
    
    def __init__(self, session: Session):
        """
        Initialize UserService
        
        Args:
            session: Database session
        """
        self._session = session
        self._logger = logger
    
    # ============================================================================
    # HELPER METHODS - User Retrieval
    # ============================================================================
    
    def _get_user_by_id(self, user_id: int) -> User:
        """
        Retrieve user by ID or raise 404
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        user = self._session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found"
            )
        return user
    
    def _get_user_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve user by email
        
        Args:
            email: User email
            
        Returns:
            User object or None if not found
        """
        statement = select(User).where(User.email == email.lower())
        return self._session.exec(statement).first()
    
    # ============================================================================
    # HELPER METHODS - Validation
    # ============================================================================
    
    def _check_email_exists(self, email: str, exclude_user_id: Optional[int] = None) -> None:
        """
        Check if email already exists
        
        Args:
            email: Email to check
            exclude_user_id: Optional user ID to exclude from check (for updates)
            
        Raises:
            HTTPException: If email already exists
        """
        query = select(User).where(User.email == email.lower())
        
        if exclude_user_id:
            query = query.where(User.id != exclude_user_id)
        
        existing_user = self._session.exec(query).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
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
    
    def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If email already exists
        """
        # Check if email already exists
        self._check_email_exists(user_data.email)
        
        # Hash the password
        hashed_password = hash_password(user_data.password)
        
        # Create user instance
        db_user = User(
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        # Save to database
        self._session.add(db_user)
        self._session.commit()
        self._session.refresh(db_user)
        
        self._logger.info(f"Created user with ID: {db_user.id}, email: {db_user.email}")
        return db_user
    
    # ============================================================================
    # CRUD OPERATIONS - Read
    # ============================================================================
    
    def get_user_by_id(self, user_id: int) -> User:
        """
        Get user by ID
        
        Args:
            user_id: User ID
            
        Returns:
            User object
            
        Raises:
            HTTPException: If user not found
        """
        return self._get_user_by_id(user_id)
    
    def get_users(
        self,
        current_page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Get paginated list of users with optional filters
        
        Args:
            current_page: Page number
            page_size: Items per page
            search: Search term (searches name and email)
            is_active: Filter by active status
            
        Returns:
            Dictionary with users list and pagination metadata
        """
        # Build query
        query = select(User)
        
        # Apply filters
        if search:
            search_term = f"%{search.strip().lower()}%"
            query = query.where(
                or_(
                    func.lower(User.first_name).like(search_term),
                    func.lower(User.last_name).like(search_term),
                    func.lower(User.email).like(search_term)
                )
            )
        
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        
        # Order by created_at desc
        query = query.order_by(User.created_at.desc())
        
        # Get all users matching query
        all_users = self._session.exec(query).all()
        
        # Validate and calculate pagination
        current_page, page_size = self._validate_pagination_params(
            current_page, page_size
        )
        total_users = len(all_users)
        total_pages, current_page, start_index, end_index = self._calculate_pagination(
            total_users, current_page, page_size
        )
        
        # Get paginated users
        paginated_users = all_users[start_index:end_index]
        
        return {
            "users": paginated_users,
            "total_users": total_users,
            "total_pages": total_pages,
            "current_page": current_page,
            "page_size": page_size
        }
    
    # ============================================================================
    # CRUD OPERATIONS - Update
    # ============================================================================
    
    def update_user(
        self,
        user_id: int,
        user_data: UserUpdate
    ) -> User:
        """
        Update user information
        
        Args:
            user_id: User ID to update
            user_data: Update data
            
        Returns:
            Updated user object
            
        Raises:
            HTTPException: If user not found or email already exists
        """
        # Get the user
        user = self._get_user_by_id(user_id)
        
        # Check if email is being updated and if it already exists
        if user_data.email and user_data.email != user.email:
            self._check_email_exists(user_data.email, exclude_user_id=user_id)
        
        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        # Update timestamp
        user.updated_at = datetime.utcnow()
        
        # Save to database
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        
        self._logger.info(f"Updated user with ID: {user_id}")
        return user
    
    # ============================================================================
    # CRUD OPERATIONS - Delete
    # ============================================================================
    
    def delete_user(self, user_id: int) -> Dict[str, str]:
        """
        Delete a user (soft delete - mark as inactive)
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If user not found
        """
        user = self._get_user_by_id(user_id)
        
        # Soft delete - mark as inactive
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self._session.add(user)
        self._session.commit()
        
        self._logger.info(f"Deleted (deactivated) user with ID: {user_id}")
        return {"message": f"User with ID {user_id} deleted successfully"}
    
    def permanent_delete_user(self, user_id: int) -> Dict[str, str]:
        """
        Permanently delete a user from database
        
        Args:
            user_id: User ID to delete
            
        Returns:
            Success message
            
        Raises:
            HTTPException: If user not found
        """
        user = self._get_user_by_id(user_id)
        
        # Permanent delete
        self._session.delete(user)
        self._session.commit()
        
        self._logger.info(f"Permanently deleted user with ID: {user_id}")
        return {"message": f"User with ID {user_id} permanently deleted"}
    
    # ============================================================================
    # AUTHENTICATION OPERATIONS
    # ============================================================================
    
    def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password
        
        Args:
            email: User email
            password: Plain text password
            
        Returns:
            Authenticated user object
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = self._get_user_by_email(email)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is inactive"
            )
        
        self._logger.info(f"User authenticated: {user.email}")
        return user
    
    # ============================================================================
    # ADDITIONAL OPERATIONS
    # ============================================================================
    
    def activate_user(self, user_id: int) -> User:
        """
        Activate user account
        
        Args:
            user_id: User ID to activate
            
        Returns:
            Updated user object
        """
        user = self._get_user_by_id(user_id)
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        
        self._logger.info(f"Activated user with ID: {user_id}")
        return user
    
    def deactivate_user(self, user_id: int) -> User:
        """
        Deactivate user account
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            Updated user object
        """
        user = self._get_user_by_id(user_id)
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        
        self._logger.info(f"Deactivated user with ID: {user_id}")
        return user
    
    def verify_user_email(self, user_id: int) -> User:
        """
        Mark user email as verified
        
        Args:
            user_id: User ID
            
        Returns:
            Updated user object
        """
        user = self._get_user_by_id(user_id)
        user.is_verified = True
        user.updated_at = datetime.utcnow()
        
        self._session.add(user)
        self._session.commit()
        self._session.refresh(user)
        
        self._logger.info(f"Verified email for user with ID: {user_id}")
        return user

