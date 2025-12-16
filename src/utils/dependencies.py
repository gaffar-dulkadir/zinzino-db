"""
FastAPI dependencies for Zinzino IoT application.

This module provides dependency injection functions for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from datalayer.database import get_postgres_session
from datalayer.repository.zinzino_user_repository import ZinzinoUserRepository
from datalayer.repository.device_repository import DeviceRepository
from datalayer.model.zinzino_models import User, Device
from .security import decode_token
from .exceptions import UnauthorizedError, AccountInactiveError, TokenExpiredError, InvalidTokenError


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session = Depends(get_postgres_session)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        session: Database session
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    try:
        # Decode the JWT token
        payload = decode_token(token)
        
        # Verify token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
        
        # Extract user ID from token
        user_id: str = payload.get("sub")
        if user_id is None:
            raise InvalidTokenError("Token missing user identifier")
        
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user_repo = ZinzinoUserRepository(session)
    user = await user_repo.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Dependency to get the current active user.
    
    Args:
        current_user: Current user from get_current_user
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Dependency to get the current verified user.
    
    Args:
        current_user: Current active user
        
    Returns:
        Current verified user
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email address not verified"
        )
    
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session = Depends(get_postgres_session)
) -> Optional[User]:
    """
    Dependency to optionally get the current user (doesn't raise error if not authenticated).
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        session: Database session
        
    Returns:
        Current user or None if not authenticated
    """
    if credentials is None:
        return None
    
    try:
        return get_current_user(credentials, session)
    except HTTPException:
        return None


async def get_current_device(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session = Depends(get_postgres_session)
) -> Device:
    """
    Dependency to get the current authenticated IoT device from JWT token.
    
    This is used for IoT device endpoints where the device itself is making the request
    (e.g., updating status, reporting state).
    
    Args:
        credentials: HTTP Bearer token credentials
        session: Database session
        
    Returns:
        Current authenticated device
        
    Raises:
        HTTPException: If token is invalid or device not found
    """
    token = credentials.credentials
    
    try:
        # Decode the JWT token
        payload = decode_token(token)
        
        # Verify token type (can be 'access' or 'device')
        token_type = payload.get("type")
        if token_type not in ["access", "device"]:
            raise InvalidTokenError("Invalid token type")
        
        # Extract device ID from token
        # For device tokens, device_id is in 'sub'
        # For user tokens, we need 'device_id' in payload
        device_id: str = payload.get("device_id") or payload.get("sub")
        if device_id is None:
            raise InvalidTokenError("Token missing device identifier")
        
    except JWTError as e:
        if "expired" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get device from database
    device_repo = DeviceRepository(session)
    device = await device_repo.get_by_id(device_id)
    
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify device is active
    if not device.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Device is inactive"
        )
    
    return device


async def verify_device_ownership(
    device_id: str,
    current_user: User = Depends(get_current_active_user),
    session = Depends(get_postgres_session)
) -> Device:
    """
    Dependency to verify that the current user owns the specified device.
    
    Args:
        device_id: Device UUID
        current_user: Current authenticated user
        session: Database session
        
    Returns:
        Device if owned by user
        
    Raises:
        HTTPException: If device not found or not owned by user
    """
    device_repo = DeviceRepository(session)
    device = await device_repo.get_by_id(device_id)
    
    if device is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if device.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this device"
        )
    
    return device
