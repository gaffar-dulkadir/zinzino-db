"""
Mappers package.

This package contains mapper classes for converting between
SQLAlchemy models and Pydantic DTOs.
"""

from .auth_mapper import (
    UserMapper,
    UserProfileMapper,
)

from .device_mapper import (
    DeviceMapper,
    DeviceStateMapper,
    ActivityLogMapper,
)

from .notification_mapper import (
    NotificationMapper,
    NotificationSettingsMapper,
)

from .sync_mapper import (
    SyncMetadataMapper,
)

__all__ = [
    # Auth mappers
    "UserMapper",
    "UserProfileMapper",
    
    # Device mappers
    "DeviceMapper",
    "DeviceStateMapper",
    "ActivityLogMapper",
    
    # Notification mappers
    "NotificationMapper",
    "NotificationSettingsMapper",
    
    # Sync mappers
    "SyncMetadataMapper",
]
