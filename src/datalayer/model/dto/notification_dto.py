"""
Notification and NotificationSettings DTOs for Zinzino IoT application.

This module contains Pydantic models for notifications and notification settings.
"""

from datetime import datetime, time
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Base DTOs
# ============================================================================

class BaseDTO(BaseModel):
    """Base DTO with common configuration."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# ============================================================================
# Notification DTOs
# ============================================================================

class NotificationCreateDTO(BaseDTO):
    """DTO for creating a notification."""
    user_id: str = Field(..., description="User UUID")
    device_id: Optional[str] = Field(None, description="Related device UUID (optional)")
    type: str = Field(
        ...,
        pattern="^(reminder|low_battery|low_supplement|achievement)$",
        description="Notification type"
    )
    title: str = Field(..., min_length=1, max_length=255, description="Notification title")
    message: str = Field(..., min_length=1, description="Notification message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional notification metadata")


class NotificationUpdateDTO(BaseDTO):
    """DTO for updating notification (mainly marking as read)."""
    is_read: bool = Field(..., description="Mark notification as read/unread")


class NotificationResponseDTO(BaseDTO):
    """DTO for notification response."""
    notification_id: str = Field(..., description="Notification UUID")
    user_id: str = Field(..., description="User UUID")
    device_id: Optional[str] = Field(None, description="Related device UUID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(..., description="Read status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="Notification creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")

    @property
    def is_unread(self) -> bool:
        """Check if notification is unread."""
        return not self.is_read

    @property
    def is_device_related(self) -> bool:
        """Check if notification is device-related."""
        return self.device_id is not None

    @property
    def age_in_days(self) -> int:
        """Get notification age in days."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        delta = now - self.created_at.replace(tzinfo=timezone.utc)
        return delta.days


# ============================================================================
# Notification Settings DTOs
# ============================================================================

class NotificationSettingsUpdateDTO(BaseDTO):
    """DTO for updating notification settings."""
    reminder_enabled: Optional[bool] = Field(None, description="Enable/disable reminder notifications")
    reminder_time: Optional[time] = Field(None, description="Daily reminder time")
    low_battery_enabled: Optional[bool] = Field(None, description="Enable/disable low battery notifications")
    low_supplement_enabled: Optional[bool] = Field(None, description="Enable/disable low supplement notifications")
    achievement_enabled: Optional[bool] = Field(None, description="Enable/disable achievement notifications")
    push_token: Optional[str] = Field(None, description="Push notification token")
    push_platform: Optional[str] = Field(
        None, 
        pattern="^(ios|android)$",
        description="Push platform (ios or android)"
    )

    @field_validator("push_token")
    @classmethod
    def validate_push_token(cls, v: Optional[str]) -> Optional[str]:
        """Validate push token is not empty if provided."""
        if v is not None and v.strip() == "":
            return None
        return v


class NotificationSettingsResponseDTO(BaseDTO):
    """DTO for notification settings response."""
    user_id: str = Field(..., description="User UUID")
    reminder_enabled: bool = Field(..., description="Reminder notifications enabled")
    reminder_time: time = Field(..., description="Daily reminder time")
    low_battery_enabled: bool = Field(..., description="Low battery notifications enabled")
    low_supplement_enabled: bool = Field(..., description="Low supplement notifications enabled")
    achievement_enabled: bool = Field(..., description="Achievement notifications enabled")
    push_token: Optional[str] = Field(None, description="Push notification token")
    push_platform: Optional[str] = Field(None, description="Push platform")
    updated_at: datetime = Field(..., description="Settings last updated timestamp")

    @property
    def has_push_configured(self) -> bool:
        """Check if push notifications are configured."""
        return self.push_token is not None and self.push_platform is not None

    @property
    def all_notifications_disabled(self) -> bool:
        """Check if all notification types are disabled."""
        return not any([
            self.reminder_enabled,
            self.low_battery_enabled,
            self.low_supplement_enabled,
            self.achievement_enabled
        ])


# ============================================================================
# Notification Query/Filter DTOs
# ============================================================================

class NotificationFilterDTO(BaseDTO):
    """DTO for filtering notifications."""
    type: Optional[str] = Field(
        None,
        pattern="^(reminder|low_battery|low_supplement|achievement)$",
        description="Filter by notification type"
    )
    is_read: Optional[bool] = Field(None, description="Filter by read status")
    device_id: Optional[str] = Field(None, description="Filter by device")
    limit: int = Field(default=50, ge=1, le=100, description="Maximum number of results")
    offset: int = Field(default=0, ge=0, description="Offset for pagination")


class NotificationBulkMarkReadDTO(BaseDTO):
    """DTO for bulk marking notifications as read."""
    notification_ids: list[str] = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="List of notification IDs to mark as read"
    )


class NotificationStatsDTO(BaseDTO):
    """DTO for notification statistics."""
    total_count: int = Field(..., ge=0, description="Total notification count")
    unread_count: int = Field(..., ge=0, description="Unread notification count")
    reminder_count: int = Field(..., ge=0, description="Reminder notification count")
    low_battery_count: int = Field(..., ge=0, description="Low battery notification count")
    low_supplement_count: int = Field(..., ge=0, description="Low supplement notification count")
    achievement_count: int = Field(..., ge=0, description="Achievement notification count")
