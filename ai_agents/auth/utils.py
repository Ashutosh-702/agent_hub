"""Authentication utilities for password hashing and token generation."""

import uuid
import bcrypt
from datetime import datetime, timedelta


# Token expiration in days
TOKEN_EXPIRY_DAYS = 15


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against a hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Stored hash to verify against
        
    Returns:
        True if password matches hash
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


def generate_token() -> str:
    """
    Generate a secure random token using UUID v4.
    
    Returns:
        Token string (UUID format)
    """
    return str(uuid.uuid4())


def calculate_expiry() -> tuple[datetime, datetime]:
    """
    Calculate token creation and expiry timestamps.
    
    Returns:
        Tuple of (created_at, expires_at) datetimes
    """
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(days=TOKEN_EXPIRY_DAYS)
    return created_at, expires_at


def is_token_expired(expires_at: datetime) -> bool:
    """
    Check if a token has expired.
    
    Args:
        expires_at: Token expiration timestamp
        
    Returns:
        True if token has expired
    """
    return datetime.utcnow() > expires_at


def validate_email(email: str) -> bool:
    """
    Basic email validation.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid
    """
    if not email or '@' not in email:
        return False
    parts = email.split('@')
    if len(parts) != 2:
        return False
    local, domain = parts
    if not local or not domain or '.' not in domain:
        return False
    return True


def validate_password(password: str) -> tuple[bool, str]:
    """
    Validate password meets requirements.
    
    Requirements:
    - Minimum 4 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(password) < 4:
        return False, "Password must be at least 4 characters"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    return True, ""

