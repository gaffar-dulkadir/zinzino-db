"""
Security utilities for Zinzino IoT application.

This module provides password hashing and JWT token management.
"""

import hashlib
import secrets
import logging
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from passlib.context import CryptContext
from jose import JWTError, jwt

from config import Config


# Password hashing context (maintained for backward compatibility)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash_context() -> CryptContext:
    """Get the password hashing context."""
    return pwd_context


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with SHA-256 pre-hashing.
    
    This approach bypasses bcrypt's 72-byte limit by first hashing the
    password with SHA-256, which always produces a 32-byte output.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Hashing password. Original length: {len(password)}")
    
    # Pre-hash with SHA-256 to handle any length and bypass bcrypt's 72-byte limit
    pre_hashed = hashlib.sha256(password.encode('utf-8')).hexdigest().encode('utf-8')
    logger.info(f"Pre-hashed password (SHA-256) length: {len(pre_hashed)}")
    
    try:
        # Generate salt and hash the pre-hashed password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pre_hashed, salt)
        logger.info("Bcrypt hashing successful")
        return hashed.decode('utf-8')
    except Exception as e:
        logger.error(f"Bcrypt hashing failed: {str(e)}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash using SHA-256 pre-hashing.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    logger = logging.getLogger(__name__)
    try:
        # Pre-hash with SHA-256 to match the hashing process
        pre_hashed = hashlib.sha256(plain_password.encode('utf-8')).hexdigest().encode('utf-8')
        # Verify using bcrypt library directly
        return bcrypt.checkpw(pre_hashed, hashed_password.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification failed: {str(e)}")
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    config = Config()
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=config.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.jwt_secret_key,
        algorithm=config.jwt_algorithm
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Data to encode in the token
        
    Returns:
        Encoded JWT refresh token string
    """
    config = Config()
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(days=config.jwt_refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.jwt_secret_key,
        algorithm=config.jwt_algorithm
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: JWT token string to decode
        
    Returns:
        Decoded token payload
        
    Raises:
        JWTError: If token is invalid or expired
    """
    config = Config()
    
    try:
        payload = jwt.decode(
            token,
            config.jwt_secret_key,
            algorithms=[config.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")


def generate_token_hash(token: str) -> str:
    """
    Generate a hash of a token for storage.
    
    Args:
        token: Token to hash
        
    Returns:
        SHA256 hash of the token
    """
    return hashlib.sha256(token.encode()).hexdigest()


def generate_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        Random URL-safe token string
    """
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        Random URL-safe token string
    """
    return secrets.token_urlsafe(32)


def create_password_reset_token(user_id: str) -> str:
    """
    Create a JWT token for password reset.
    
    Args:
        user_id: User ID to encode in the token
        
    Returns:
        Encoded JWT token string
    """
    config = Config()
    expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry for reset tokens
    
    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "password_reset"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.jwt_secret_key,
        algorithm=config.jwt_algorithm
    )
    
    return encoded_jwt


def create_email_verification_token(user_id: str, email: str) -> str:
    """
    Create a JWT token for email verification.
    
    Args:
        user_id: User ID to encode in the token
        email: Email address to verify
        
    Returns:
        Encoded JWT token string
    """
    config = Config()
    expire = datetime.utcnow() + timedelta(days=7)  # 7 days expiry for verification
    
    to_encode = {
        "user_id": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "email_verification"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        config.jwt_secret_key,
        algorithm=config.jwt_algorithm
    )
    
    return encoded_jwt
