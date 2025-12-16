"""
Data Transfer Objects (DTOs) package.

This package contains all Pydantic models for request/response validation.
"""

# Auth DTOs
from .auth_dto import (
    UserRegisterDTO,
    UserLoginDTO,
    GoogleAuthDTO,
    AppleAuthDTO,
    TokenResponseDTO,
    RefreshTokenDTO,
    UserResponseDTO,
    UserProfileResponseDTO,
    UserProfileUpdateDTO,
    PasswordChangeDTO,
    PasswordResetRequestDTO,
    PasswordResetConfirmDTO,
    EmailVerificationRequestDTO,
    EmailVerificationConfirmDTO,
)

# Device DTOs
from .device_dto import (
    DeviceCreateDTO,
    DeviceUpdateDTO,
    DeviceResponseDTO,
    DeviceStateCreateDTO,
    DeviceStateResponseDTO,
    ActivityLogCreateDTO,
    ActivityLogResponseDTO,
    DeviceBulkUpdateDTO,
    ActivityLogBulkCreateDTO,
)

# Notification DTOs
from .notification_dto import (
    NotificationCreateDTO,
    NotificationUpdateDTO,
    NotificationResponseDTO,
    NotificationSettingsUpdateDTO,
    NotificationSettingsResponseDTO,
    NotificationFilterDTO,
    NotificationBulkMarkReadDTO,
    NotificationStatsDTO,
)

# Sync DTOs
from .sync_dto import (
    DeviceInfoDTO,
    SyncMetadataDTO,
    FullSyncRequestDTO,
    FullSyncResponseDTO,
    DeltaSyncRequestDTO,
    DeltaSyncResponseDTO,
    DeviceSyncData,
    NotificationSyncData,
    ActivityLogSyncData,
    SyncStatusDTO,
    SyncConflictDTO,
)

__all__ = [
    # Auth DTOs
    "UserRegisterDTO",
    "UserLoginDTO",
    "GoogleAuthDTO",
    "AppleAuthDTO",
    "TokenResponseDTO",
    "RefreshTokenDTO",
    "UserResponseDTO",
    "UserProfileResponseDTO",
    "UserProfileUpdateDTO",
    "PasswordChangeDTO",
    "PasswordResetRequestDTO",
    "PasswordResetConfirmDTO",
    "EmailVerificationRequestDTO",
    "EmailVerificationConfirmDTO",
    
    # Device DTOs
    "DeviceCreateDTO",
    "DeviceUpdateDTO",
    "DeviceResponseDTO",
    "DeviceStateCreateDTO",
    "DeviceStateResponseDTO",
    "ActivityLogCreateDTO",
    "ActivityLogResponseDTO",
    "DeviceBulkUpdateDTO",
    "ActivityLogBulkCreateDTO",
    
    # Notification DTOs
    "NotificationCreateDTO",
    "NotificationUpdateDTO",
    "NotificationResponseDTO",
    "NotificationSettingsUpdateDTO",
    "NotificationSettingsResponseDTO",
    "NotificationFilterDTO",
    "NotificationBulkMarkReadDTO",
    "NotificationStatsDTO",
    
    # Sync DTOs
    "DeviceInfoDTO",
    "SyncMetadataDTO",
    "FullSyncRequestDTO",
    "FullSyncResponseDTO",
    "DeltaSyncRequestDTO",
    "DeltaSyncResponseDTO",
    "DeviceSyncData",
    "NotificationSyncData",
    "ActivityLogSyncData",
    "SyncStatusDTO",
    "SyncConflictDTO",
]
