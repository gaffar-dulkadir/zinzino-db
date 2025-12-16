"""
Authentication and User DTOs for Zinzino IoT application.

This module contains Pydantic models for user registration, login, OAuth,
profile management, and password operations.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, computed_field
import re


# ============================================================================
# Base DTOs
# ============================================================================

class BaseDTO(BaseModel):
    """Base DTO with common configuration."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# ============================================================================
# User Registration & Login DTOs
# ============================================================================

class UserRegisterDTO(BaseDTO):
    """DTO for user registration with email/password."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="User password (min 8 characters)")
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number (optional)")
    language: Optional[str] = Field("tr", pattern="^(tr|en)$", description="Preferred language")
    timezone: Optional[str] = Field("Europe/Istanbul", max_length=50, description="User timezone")

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains at least one letter and one number."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided."""
        if v is not None:
            # Remove spaces and common separators
            cleaned = re.sub(r"[\s\-\(\)]", "", v)
            if not re.match(r"^\+?[0-9]{10,15}$", cleaned):
                raise ValueError("Invalid phone number format")
            return cleaned
        return v


class UserLoginDTO(BaseDTO):
    """DTO for user login with email/password."""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, max_length=128, description="User password")


# ============================================================================
# OAuth DTOs
# ============================================================================

class GoogleAuthDTO(BaseDTO):
    """DTO for Google OAuth authentication."""
    id_token: str = Field(..., description="Google ID token")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name from Google")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL from Google")


class AppleAuthDTO(BaseDTO):
    """DTO for Apple OAuth authentication."""
    id_token: str = Field(..., description="Apple ID token")
    authorization_code: str = Field(..., description="Apple authorization code")
    full_name: Optional[str] = Field(None, max_length=255, description="User's full name from Apple")
    

# ============================================================================
# Token DTOs
# ============================================================================

class TokenResponseDTO(BaseDTO):
    """DTO for authentication token response."""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")


class RefreshTokenDTO(BaseDTO):
    """DTO for token refresh request."""
    refresh_token: str = Field(..., description="JWT refresh token")


# ============================================================================
# User Response DTOs
# ============================================================================

class UserProfileResponseDTO(BaseDTO):
    """DTO for user profile response."""
    user_id: str = Field(..., description="User UUID")
    notification_enabled: bool = Field(default=True, description="Notifications enabled flag")
    theme_preference: str = Field(default="dark", description="UI theme preference")
    language: str = Field(default="tr", description="Preferred language")
    timezone: str = Field(default="Europe/Istanbul", description="User timezone")
    updated_at: datetime = Field(..., description="Profile last updated timestamp")


class UserResponseDTO(BaseDTO):
    """DTO for user response with profile information."""
    user_id: str = Field(..., description="User UUID")
    email: str = Field(..., description="User email address")
    full_name: str = Field(..., description="User's full name")
    phone: Optional[str] = Field(None, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    is_verified: bool = Field(default=False, description="Email verification status")
    is_active: bool = Field(default=True, description="Account active status")
    oauth_provider: Optional[str] = Field(None, description="OAuth provider")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Account last updated timestamp")
    profile: Optional[UserProfileResponseDTO] = Field(None, description="User profile settings")

    @computed_field
    @property
    def display_name(self) -> str:
        """Computed field for display name."""
        return self.full_name

    @computed_field
    @property
    def is_oauth_user(self) -> bool:
        """Check if user authenticated via OAuth."""
        return self.oauth_provider is not None and self.oauth_provider != "email"


# ============================================================================
# Profile Update DTOs
# ============================================================================

class UserProfileUpdateDTO(BaseDTO):
    """DTO for updating user profile information."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="User's full name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    profile_picture: Optional[str] = Field(None, description="Profile picture URL")
    notification_enabled: Optional[bool] = Field(None, description="Enable/disable notifications")
    theme_preference: Optional[str] = Field(None, pattern="^(dark|light|auto)$", description="UI theme")
    language: Optional[str] = Field(None, pattern="^(tr|en)$", description="Preferred language")
    timezone: Optional[str] = Field(None, max_length=50, description="User timezone")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format if provided."""
        if v is not None and v != "":
            cleaned = re.sub(r"[\s\-\(\)]", "", v)
            if not re.match(r"^\+?[0-9]{10,15}$", cleaned):
                raise ValueError("Invalid phone number format")
            return cleaned
        return v


# ============================================================================
# Password Management DTOs
# ============================================================================

class PasswordChangeDTO(BaseDTO):
    """DTO for password change (authenticated user)."""
    old_password: str = Field(..., min_length=1, max_length=128, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains at least one letter and one number."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    def model_post_init(self, __context) -> None:
        """Validate passwords match after model initialization."""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")


class PasswordResetRequestDTO(BaseDTO):
    """DTO for requesting password reset."""
    email: EmailStr = Field(..., description="User email address")


class PasswordResetConfirmDTO(BaseDTO):
    """DTO for confirming password reset with token."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Confirm new password")

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password contains at least one letter and one number."""
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("Password must contain at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        return v

    def model_post_init(self, __context) -> None:
        """Validate passwords match after model initialization."""
        if self.new_password != self.confirm_password:
            raise ValueError("Passwords do not match")


# ============================================================================
# Email Verification DTOs
# ============================================================================

class EmailVerificationRequestDTO(BaseDTO):
    """DTO for requesting email verification."""
    email: EmailStr = Field(..., description="User email address")


class EmailVerificationConfirmDTO(BaseDTO):
    """DTO for confirming email verification."""
    token: str = Field(..., description="Email verification token")
