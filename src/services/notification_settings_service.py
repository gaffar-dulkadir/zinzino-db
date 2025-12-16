"""
Notification settings service for Zinzino IoT application.

This module provides business logic for notification settings management.
"""

from typing import Optional
from datetime import time, datetime
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.model.zinzino_models import NotificationSettings
from datalayer.model.dto.notification_dto import (
    NotificationSettingsUpdateDTO, NotificationSettingsResponseDTO
)
from datalayer.repository.notification_settings_repository import NotificationSettingsRepository
from datalayer.mapper.notification_mapper import NotificationSettingsMapper
from utils.exceptions import NotFoundError, ValidationError


class NotificationSettingsService:
    """Service for handling notification settings operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.settings_repo = NotificationSettingsRepository(session)
        self.mapper = NotificationSettingsMapper()
    
    async def get_settings(self, user_id: str) -> NotificationSettingsResponseDTO:
        """
        Get notification settings for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Notification settings DTO
            
        Raises:
            NotFoundError: If settings not found (creates default if missing)
        """
        settings = await self.settings_repo.get_by_user(user_id)
        
        # Create default settings if not exists
        if not settings:
            settings = NotificationSettings(
                user_id=user_id,
                reminder_enabled=True,
                reminder_time=time(9, 0),  # 9:00 AM default
                low_battery_enabled=True,
                low_supplement_enabled=True,
                achievement_enabled=True,
                push_token=None,
                push_platform=None
            )
            settings = await self.settings_repo.create_settings(settings)
            await self.session.commit()
        
        return self.mapper.to_dto(settings)
    
    async def update_settings(
        self,
        user_id: str,
        data: NotificationSettingsUpdateDTO
    ) -> NotificationSettingsResponseDTO:
        """
        Update notification settings.
        
        Args:
            user_id: User UUID
            data: Settings update data
            
        Returns:
            Updated notification settings DTO
        """
        # Get or create settings
        settings = await self.settings_repo.get_by_user(user_id)
        
        if not settings:
            # Create new settings with provided data
            settings = NotificationSettings(
                user_id=user_id,
                reminder_enabled=data.reminder_enabled if data.reminder_enabled is not None else True,
                reminder_time=data.reminder_time if data.reminder_time is not None else time(9, 0),
                low_battery_enabled=data.low_battery_enabled if data.low_battery_enabled is not None else True,
                low_supplement_enabled=data.low_supplement_enabled if data.low_supplement_enabled is not None else True,
                achievement_enabled=data.achievement_enabled if data.achievement_enabled is not None else True,
                push_token=data.push_token,
                push_platform=data.push_platform
            )
            settings = await self.settings_repo.create_settings(settings)
        else:
            # Update existing settings
            if data.reminder_enabled is not None:
                settings.reminder_enabled = data.reminder_enabled
            
            if data.reminder_time is not None:
                settings.reminder_time = data.reminder_time
            
            if data.low_battery_enabled is not None:
                settings.low_battery_enabled = data.low_battery_enabled
            
            if data.low_supplement_enabled is not None:
                settings.low_supplement_enabled = data.low_supplement_enabled
            
            if data.achievement_enabled is not None:
                settings.achievement_enabled = data.achievement_enabled
            
            if data.push_token is not None:
                settings.push_token = data.push_token
            
            if data.push_platform is not None:
                settings.push_platform = data.push_platform
            
            settings.updated_at = datetime.utcnow()
            settings = await self.settings_repo.update_settings(settings)
        
        await self.session.commit()
        return self.mapper.to_dto(settings)
    
    async def update_push_token(
        self,
        user_id: str,
        token: str,
        platform: str
    ) -> NotificationSettingsResponseDTO:
        """
        Update push notification token.
        
        Args:
            user_id: User UUID
            token: Push notification token
            platform: Platform (ios or android)
            
        Returns:
            Updated notification settings DTO
            
        Raises:
            ValidationError: If platform is invalid
        """
        if platform not in ["ios", "android"]:
            raise ValidationError("Platform must be 'ios' or 'android'")
        
        # Get or create settings
        settings = await self.settings_repo.get_by_user(user_id)
        
        if not settings:
            # Create new settings with push token
            settings = NotificationSettings(
                user_id=user_id,
                reminder_enabled=True,
                reminder_time=time(9, 0),
                low_battery_enabled=True,
                low_supplement_enabled=True,
                achievement_enabled=True,
                push_token=token,
                push_platform=platform
            )
            settings = await self.settings_repo.create_settings(settings)
        else:
            # Update push token
            settings.push_token = token
            settings.push_platform = platform
            settings.updated_at = datetime.utcnow()
            settings = await self.settings_repo.update_settings(settings)
        
        await self.session.commit()
        return self.mapper.to_dto(settings)
    
    async def check_should_send_notification(
        self,
        user_id: str,
        notification_type: str
    ) -> bool:
        """
        Check if a notification type should be sent to user.
        
        Args:
            user_id: User UUID
            notification_type: Type of notification (reminder, low_battery, low_supplement, achievement)
            
        Returns:
            True if notification should be sent, False otherwise
        """
        settings = await self.settings_repo.get_by_user(user_id)
        
        if not settings:
            # Default to allowing all notifications if settings don't exist
            return True
        
        # Check setting based on notification type
        type_mapping = {
            "reminder": settings.reminder_enabled,
            "low_battery": settings.low_battery_enabled,
            "low_supplement": settings.low_supplement_enabled,
            "achievement": settings.achievement_enabled
        }
        
        return type_mapping.get(notification_type, True)
