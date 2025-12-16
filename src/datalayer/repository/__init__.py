# Repository exports for Zinzino IoT Backend API

from ._base_repository import BaseRepository, AsyncBaseRepository
from ._repository_abc import RepositoryABC, AsyncRepositoryABC
from .zinzino_user_repository import ZinzinoUserRepository
from .profile_repository import UserProfileRepository
from .device_repository import DeviceRepository
from .device_state_repository import DeviceStateRepository
from .activity_repository import ActivityLogRepository
from .notification_repository import NotificationRepository
from .notification_settings_repository import NotificationSettingsRepository
from .sync_repository import SyncMetadataRepository

__all__ = [
    # Base repositories
    "BaseRepository",
    "AsyncBaseRepository",
    "RepositoryABC",
    "AsyncRepositoryABC",
    # Zinzino repositories
    "ZinzinoUserRepository",
    "UserProfileRepository",
    "DeviceRepository",
    "DeviceStateRepository",
    "ActivityLogRepository",
    "NotificationRepository",
    "NotificationSettingsRepository",
    "SyncMetadataRepository",
]
