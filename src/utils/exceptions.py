"""
Custom exceptions for Zinzino IoT application.

This module defines application-specific exceptions for better error handling.
"""

from typing import Optional, Any, Dict


class ZinzinoException(Exception):
    """Base exception for Zinzino application."""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ZinzinoException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, details=details)


class NotFoundError(ZinzinoException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        details = {"resource": resource} if resource else {}
        super().__init__(message, status_code=404, details=details)


class DuplicateError(ZinzinoException):
    """Raised when attempting to create a duplicate resource."""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=409, details=details)


class UnauthorizedError(ZinzinoException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401)


class ForbiddenError(ZinzinoException):
    """Raised when user lacks permission for an action."""
    
    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class DeviceNotConnectedError(ZinzinoException):
    """Raised when attempting operations on a disconnected device."""
    
    def __init__(self, message: str = "Device is not connected", device_id: Optional[str] = None):
        details = {"device_id": device_id} if device_id else {}
        super().__init__(message, status_code=503, details=details)


class SyncConflictError(ZinzinoException):
    """Raised when a synchronization conflict occurs."""
    
    def __init__(self, message: str = "Synchronization conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=409, details=details)


class TokenExpiredError(UnauthorizedError):
    """Raised when a token has expired."""
    
    def __init__(self, message: str = "Token has expired"):
        super().__init__(message)


class InvalidTokenError(UnauthorizedError):
    """Raised when a token is invalid."""
    
    def __init__(self, message: str = "Invalid token"):
        super().__init__(message)


class EmailAlreadyExistsError(DuplicateError):
    """Raised when attempting to register with an existing email."""
    
    def __init__(self, email: str):
        super().__init__(f"Email '{email}' is already registered", field="email")


class DeviceAlreadyExistsError(DuplicateError):
    """Raised when attempting to register a device that already exists."""
    
    def __init__(self, identifier: str):
        super().__init__(f"Device with identifier '{identifier}' already exists", field="device")


class InvalidCredentialsError(UnauthorizedError):
    """Raised when login credentials are invalid."""
    
    def __init__(self):
        super().__init__("Invalid email or password")


class AccountInactiveError(ForbiddenError):
    """Raised when attempting to access an inactive account."""
    
    def __init__(self):
        super().__init__("Account is inactive")


class EmailNotVerifiedError(ForbiddenError):
    """Raised when email verification is required."""
    
    def __init__(self):
        super().__init__("Email address not verified")


class PasswordResetTokenInvalidError(UnauthorizedError):
    """Raised when password reset token is invalid or expired."""
    
    def __init__(self):
        super().__init__("Password reset token is invalid or has expired")


class RateLimitExceededError(ZinzinoException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        details = {"retry_after": retry_after} if retry_after else {}
        super().__init__(message, status_code=429, details=details)
