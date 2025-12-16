"""
Notification settings repository for Zinzino IoT application.

This module provides repository methods for user notification preferences.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import NotificationSettings
from ._base_repository import AsyncBaseRepository


class NotificationSettingsRepository(AsyncBaseRepository[NotificationSettings]):
    """Repository for NotificationSettings model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, NotificationSettings)
    
    async def create_settings(self, settings_data: NotificationSettings) -> NotificationSettings:
        """Create notification settings for a user."""
        return await self.save(settings_data)
    
    async def get_by_user(self, user_id: str) -> Optional[NotificationSettings]:
        """Get notification settings by user ID."""
        return await self.get_by_id(user_id)
    
    async def update_settings(self, settings: NotificationSettings) -> NotificationSettings:
        """Update notification settings."""
        return await self.save(settings)
    
    async def update_push_token(
        self,
        user_id: str,
        push_token: str,
        push_platform: str
    ) -> bool:
        """Update push notification token and platform."""
        settings = await self.get_by_user(user_id)
        if settings:
            settings.push_token = push_token
            settings.push_platform = push_platform
            await self.save(settings)
            return True
        return False
    
    async def delete_settings(self, user_id: str) -> bool:
        """Delete notification settings."""
        return await self.delete_by_id(user_id)
