"""
Utils module for Zinzino IoT application.

This module provides utility functions for security, exceptions, and dependencies.
"""

from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token_hash,
    get_password_hash_context
)

from .exceptions import (
    ZinzinoException,
    ValidationError,
    NotFoundError,
    DuplicateError,
    UnauthorizedError,
    ForbiddenError,
    DeviceNotConnectedError,
    SyncConflictError,
    TokenExpiredError,
    InvalidTokenError,
    EmailAlreadyExistsError,
    DeviceAlreadyExistsError,
    InvalidCredentialsError,
    AccountInactiveError,
    EmailNotVerifiedError,
    PasswordResetTokenInvalidError,
    RateLimitExceededError
)

from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_current_verified_user,
    get_optional_current_user
)


__all__ = [
    # Security
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "generate_token_hash",
    "get_password_hash_context",
    
    # Exceptions
    "ZinzinoException",
    "ValidationError",
    "NotFoundError",
    "DuplicateError",
    "UnauthorizedError",
    "ForbiddenError",
    "DeviceNotConnectedError",
    "SyncConflictError",
    "TokenExpiredError",
    "InvalidTokenError",
    "EmailAlreadyExistsError",
    "DeviceAlreadyExistsError",
    "InvalidCredentialsError",
    "AccountInactiveError",
    "EmailNotVerifiedError",
    "PasswordResetTokenInvalidError",
    "RateLimitExceededError",
    
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_current_verified_user",
    "get_optional_current_user",
]
