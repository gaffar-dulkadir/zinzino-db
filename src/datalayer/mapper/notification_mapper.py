"""
Mappers for Notification entities (Notification, NotificationSettings) to DTOs.

This module provides conversion functions between SQLAlchemy models
and Pydantic DTOs for notification-related entities.
"""

from typing import Optional, List
from ..model.zinzino_models import Notification, NotificationSettings
from ..model.dto.notification_dto import (
    NotificationResponseDTO,
    NotificationSettingsResponseDTO
)


# ============================================================================
# Notification Mapper
# ============================================================================

class NotificationMapper:
    """Mapper for Notification model to DTOs."""

    @staticmethod
    def to_dto(notification: Optional[Notification]) -> Optional[NotificationResponseDTO]:
        """
        Convert Notification model to NotificationResponseDTO.

        Args:
            notification: Notification SQLAlchemy model instance

        Returns:
            NotificationResponseDTO or None if notification is None
        """
        if notification is None:
            return None

        return NotificationResponseDTO(
            notification_id=notification.notification_id,
            user_id=notification.user_id,
            device_id=notification.device_id,
            type=notification.type,
            title=notification.title,
            message=notification.message,
            is_read=notification.is_read,
            metadata=notification.metadata,
            created_at=notification.created_at,
            read_at=notification.read_at
        )

    @staticmethod
    def to_dto_list(notifications: List[Notification]) -> List[NotificationResponseDTO]:
        """
        Convert list of Notification models to list of DTOs.

        Args:
            notifications: List of Notification models

        Returns:
            List of NotificationResponseDTO
        """
        return [
            NotificationMapper.to_dto(notification)
            for notification in notifications
            if notification is not None
        ]


# ============================================================================
# Notification Settings Mapper
# ============================================================================

class NotificationSettingsMapper:
    """Mapper for NotificationSettings model to DTOs."""

    @staticmethod
    def to_dto(
        settings: Optional[NotificationSettings]
    ) -> Optional[NotificationSettingsResponseDTO]:
        """
        Convert NotificationSettings model to NotificationSettingsResponseDTO.

        Args:
            settings: NotificationSettings SQLAlchemy model instance

        Returns:
            NotificationSettingsResponseDTO or None if settings is None
        """
        if settings is None:
            return None

        return NotificationSettingsResponseDTO(
            user_id=settings.user_id,
            reminder_enabled=settings.reminder_enabled,
            reminder_time=settings.reminder_time,
            low_battery_enabled=settings.low_battery_enabled,
            low_supplement_enabled=settings.low_supplement_enabled,
            achievement_enabled=settings.achievement_enabled,
            push_token=settings.push_token,
            push_platform=settings.push_platform,
            updated_at=settings.updated_at
        )

    @staticmethod
    def to_dto_list(
        settings_list: List[NotificationSettings]
    ) -> List[NotificationSettingsResponseDTO]:
        """
        Convert list of NotificationSettings models to list of DTOs.

        Args:
            settings_list: List of NotificationSettings models

        Returns:
            List of NotificationSettingsResponseDTO
        """
        return [
            NotificationSettingsMapper.to_dto(settings)
            for settings in settings_list
            if settings is not None
        ]
