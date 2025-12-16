"""
Notification repository for Zinzino IoT application.

This module provides repository methods for user notifications.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import Notification
from ._base_repository import AsyncBaseRepository


class NotificationRepository(AsyncBaseRepository[Notification]):
    """Repository for Notification model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)
    
    async def create(self, notification_data: Notification) -> Notification:
        """Create a new notification."""
        return await self.save(notification_data)
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user."""
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(desc(Notification.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_unread(self, user_id: str) -> List[Notification]:
        """Get unread notifications for a user."""
        return await self.get_by_user(user_id, unread_only=True)
    
    async def get_unread_count(self, user_id: str) -> int:
        """Get count of unread notifications for a user."""
        stmt = select(func.count(Notification.notification_id)).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def mark_as_read(self, notification_id: str) -> bool:
        """Mark a notification as read."""
        notification = await self.get_by_id(notification_id)
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.save(notification)
            return True
        return False
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """Mark all user notifications as read."""
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        
        count = 0
        now = datetime.utcnow()
        for notification in notifications:
            notification.is_read = True
            notification.read_at = now
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
    
    async def delete(self, notification_id: str) -> bool:
        """Delete a notification."""
        return await self.delete_by_id(notification_id)
    
    async def delete_read_notifications(self, user_id: str, days: int = 30) -> int:
        """Delete read notifications older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.is_read == True,
                Notification.read_at < cutoff_date
            )
        )
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            await self.session.delete(notification)
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
    
    async def get_by_device(
        self,
        device_id: str,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a specific device."""
        stmt = select(Notification).where(
            Notification.device_id == device_id
        ).order_by(desc(Notification.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_type(
        self,
        user_id: str,
        notification_type: str,
        limit: int = 20
    ) -> List[Notification]:
        """Get notifications by type for a user."""
        stmt = select(Notification).where(
            and_(
                Notification.user_id == user_id,
                Notification.type == notification_type
            )
        ).order_by(desc(Notification.created_at)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
