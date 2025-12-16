"""
Synchronization DTOs for Zinzino IoT application.

This module contains Pydantic models for full sync, delta sync, 
and synchronization metadata operations.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict, field_validator


# ============================================================================
# Base DTOs
# ============================================================================

class BaseDTO(BaseModel):
    """Base DTO with common configuration."""
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


# ============================================================================
# Device Info DTO
# ============================================================================

class DeviceInfoDTO(BaseDTO):
    """DTO for client device information."""
    platform: str = Field(..., pattern="^(ios|android|web)$", description="Platform type")
    app_version: str = Field(..., max_length=20, description="Application version")
    os_version: str = Field(..., max_length=50, description="Operating system version")
    device_model: Optional[str] = Field(None, max_length=100, description="Device model")


# ============================================================================
# Sync Metadata DTOs
# ============================================================================

class SyncMetadataDTO(BaseDTO):
    """DTO for sync metadata response."""
    sync_id: str = Field(..., description="Sync UUID")
    user_id: str = Field(..., description="User UUID")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Client device information")
    last_full_sync: Optional[datetime] = Field(None, description="Last full sync timestamp")
    last_delta_sync: Optional[datetime] = Field(None, description="Last delta sync timestamp")
    sync_status: Optional[str] = Field(
        None,
        pattern="^(success|partial|failed)$",
        description="Sync status"
    )
    created_at: datetime = Field(..., description="Sync record creation timestamp")

    @property
    def needs_full_sync(self) -> bool:
        """Check if full sync is needed."""
        if self.last_full_sync is None:
            return True
        # If last full sync was more than 7 days ago
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        last_sync = self.last_full_sync.replace(tzinfo=timezone.utc)
        return (now - last_sync) > timedelta(days=7)

    @property
    def last_sync_failed(self) -> bool:
        """Check if last sync failed."""
        return self.sync_status == "failed"


# ============================================================================
# Full Sync DTOs
# ============================================================================

class FullSyncRequestDTO(BaseDTO):
    """DTO for full synchronization request."""
    device_info: DeviceInfoDTO = Field(..., description="Client device information")
    include_deleted: bool = Field(default=False, description="Include soft-deleted records")


class DeviceSyncData(BaseDTO):
    """DTO for device data in sync response."""
    device_id: str = Field(..., description="Device UUID")
    device_name: str = Field(..., description="Device name")
    device_type: str = Field(..., description="Device type")
    mac_address: str = Field(..., description="MAC address")
    serial_number: str = Field(..., description="Serial number")
    location: Optional[str] = Field(None, description="Device location")
    battery_level: int = Field(..., description="Battery level")
    supplement_level: int = Field(..., description="Supplement level")
    is_connected: bool = Field(..., description="Connection status")
    firmware_version: Optional[str] = Field(None, description="Firmware version")
    total_doses_dispensed: int = Field(..., description="Total doses")
    last_sync: Optional[datetime] = Field(None, description="Last sync")
    is_active: bool = Field(..., description="Active status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")


class NotificationSyncData(BaseDTO):
    """DTO for notification data in sync response."""
    notification_id: str = Field(..., description="Notification UUID")
    device_id: Optional[str] = Field(None, description="Related device UUID")
    type: str = Field(..., description="Notification type")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    is_read: bool = Field(..., description="Read status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    read_at: Optional[datetime] = Field(None, description="Read timestamp")


class ActivityLogSyncData(BaseDTO):
    """DTO for activity log data in sync response."""
    log_id: str = Field(..., description="Log UUID")
    device_id: str = Field(..., description="Device UUID")
    action: str = Field(..., description="Action type")
    dose_amount: Optional[str] = Field(None, description="Dose amount")
    triggered_by: Optional[str] = Field(None, description="Trigger type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Metadata")
    timestamp: datetime = Field(..., description="Activity timestamp")


class FullSyncResponseDTO(BaseDTO):
    """DTO for full synchronization response."""
    sync_id: str = Field(..., description="Sync UUID")
    user_id: str = Field(..., description="User UUID")
    devices: List[DeviceSyncData] = Field(default_factory=list, description="All user devices")
    notifications: List[NotificationSyncData] = Field(default_factory=list, description="Recent notifications")
    activity_logs: List[ActivityLogSyncData] = Field(default_factory=list, description="Recent activity logs")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="Notification settings")
    user_profile: Optional[Dict[str, Any]] = Field(None, description="User profile")
    sync_timestamp: datetime = Field(..., description="Server sync timestamp")
    sync_status: str = Field(default="success", description="Sync status")

    @property
    def total_items(self) -> int:
        """Get total number of synchronized items."""
        return len(self.devices) + len(self.notifications) + len(self.activity_logs)

    @property
    def is_successful(self) -> bool:
        """Check if sync was successful."""
        return self.sync_status == "success"


# ============================================================================
# Delta Sync DTOs
# ============================================================================

class DeltaSyncRequestDTO(BaseDTO):
    """DTO for delta (incremental) synchronization request."""
    device_info: DeviceInfoDTO = Field(..., description="Client device information")
    last_sync_timestamp: datetime = Field(..., description="Client's last sync timestamp")
    client_changes: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        None,
        description="Client-side changes to push to server"
    )

    @field_validator("last_sync_timestamp")
    @classmethod
    def validate_sync_timestamp(cls, v: datetime) -> datetime:
        """Validate sync timestamp is not in the future."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if v.replace(tzinfo=timezone.utc) > now:
            raise ValueError("Sync timestamp cannot be in the future")
        return v


class DeltaSyncResponseDTO(BaseDTO):
    """DTO for delta synchronization response."""
    sync_id: str = Field(..., description="Sync UUID")
    user_id: str = Field(..., description="User UUID")
    devices_updated: List[DeviceSyncData] = Field(default_factory=list, description="Updated devices")
    devices_deleted: List[str] = Field(default_factory=list, description="Deleted device IDs")
    notifications_new: List[NotificationSyncData] = Field(default_factory=list, description="New notifications")
    notifications_updated: List[NotificationSyncData] = Field(default_factory=list, description="Updated notifications")
    activity_logs_new: List[ActivityLogSyncData] = Field(default_factory=list, description="New activity logs")
    notification_settings_updated: Optional[Dict[str, Any]] = Field(None, description="Updated notification settings")
    user_profile_updated: Optional[Dict[str, Any]] = Field(None, description="Updated user profile")
    sync_timestamp: datetime = Field(..., description="Server sync timestamp")
    sync_status: str = Field(default="success", description="Sync status")
    conflicts: List[Dict[str, Any]] = Field(default_factory=list, description="Sync conflicts")

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return (
            len(self.devices_updated) > 0 or
            len(self.devices_deleted) > 0 or
            len(self.notifications_new) > 0 or
            len(self.notifications_updated) > 0 or
            len(self.activity_logs_new) > 0 or
            self.notification_settings_updated is not None or
            self.user_profile_updated is not None
        )

    @property
    def has_conflicts(self) -> bool:
        """Check if there are sync conflicts."""
        return len(self.conflicts) > 0

    @property
    def is_successful(self) -> bool:
        """Check if sync was successful."""
        return self.sync_status == "success"


# ============================================================================
# Sync Status DTOs
# ============================================================================

class SyncStatusDTO(BaseDTO):
    """DTO for checking sync status."""
    user_id: str = Field(..., description="User UUID")
    last_full_sync: Optional[datetime] = Field(None, description="Last full sync timestamp")
    last_delta_sync: Optional[datetime] = Field(None, description="Last delta sync timestamp")
    sync_status: Optional[str] = Field(None, description="Last sync status")
    needs_full_sync: bool = Field(..., description="Whether full sync is recommended")
    pending_changes: int = Field(default=0, ge=0, description="Number of pending changes")


class SyncConflictDTO(BaseDTO):
    """DTO for sync conflict information."""
    entity_type: str = Field(..., description="Entity type (device, notification, etc.)")
    entity_id: str = Field(..., description="Entity UUID")
    client_version: Dict[str, Any] = Field(..., description="Client version of data")
    server_version: Dict[str, Any] = Field(..., description="Server version of data")
    conflict_type: str = Field(..., description="Type of conflict")
    resolution: Optional[str] = Field(None, description="Suggested resolution")
