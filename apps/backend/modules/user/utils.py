"""
User-related utility functions

Includes password hashing, verification, and other user management utilities
"""

import bcrypt


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password string
        
    Example:
        >>> hashed = hash_password("MySecurePassword123")
        >>> print(hashed)
        '$2b$12$...'
    """
    # Encode password to bytes
    password_bytes = password.encode('utf-8')
    
    # Generate salt and hash password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
        
    Example:
        >>> hashed = hash_password("MySecurePassword123")
        >>> verify_password("MySecurePassword123", hashed)
        True
        >>> verify_password("WrongPassword", hashed)
        False
    """
    # Encode both passwords to bytes
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Verify password
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_full_name(first_name: str, last_name: str) -> str:
    """
    Get user's full name from first and last name
    
    Args:
        first_name: User's first name
        last_name: User's last name
        
    Returns:
        Full name as a single string
        
    Example:
        >>> get_full_name("John", "Doe")
        'John Doe'
    """
    return f"{first_name} {last_name}".strip()

