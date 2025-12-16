"""
Notification service for Zinzino IoT application.

This module provides business logic for notification management operations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from datalayer.model.zinzino_models import Notification, Device
from datalayer.model.dto.notification_dto import (
    NotificationCreateDTO, NotificationResponseDTO, NotificationFilterDTO,
    NotificationStatsDTO, NotificationBulkMarkReadDTO
)
from datalayer.repository.notification_repository import NotificationRepository
from datalayer.repository.notification_settings_repository import NotificationSettingsRepository
from datalayer.repository.device_repository import DeviceRepository
from datalayer.mapper.notification_mapper import NotificationMapper
from utils.exceptions import NotFoundError, ForbiddenError, ValidationError


class NotificationService:
    """Service for handling notification operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.notification_repo = NotificationRepository(session)
        self.settings_repo = NotificationSettingsRepository(session)
        self.device_repo = DeviceRepository(session)
        self.mapper = NotificationMapper()
    
    async def create_notification(
        self,
        user_id: str,
        data: NotificationCreateDTO
    ) -> NotificationResponseDTO:
        """
        Create a new notification.
        
        Args:
            user_id: User UUID (from auth)
            data: Notification creation data
            
        Returns:
            Created notification DTO
            
        Raises:
            ValidationError: If device_id is invalid
        """
        # Validate device if provided
        if data.device_id:
            device = await self.device_repo.get_by_id(data.device_id)
            if not device or device.user_id != user_id:
                raise ValidationError("Invalid device ID")
        
        # Create notification
        notification = Notification(
            user_id=user_id,
            device_id=data.device_id,
            type=data.type,
            title=data.title,
            message=data.message,
            metadata=data.metadata,
            is_read=False
        )
        
        notification = await self.notification_repo.create(notification)
        await self.session.commit()
        
        return self.mapper.to_dto(notification)
    
    async def get_user_notifications(
        self,
        user_id: str,
        filter_dto: NotificationFilterDTO
    ) -> dict:
        """
        Get user notifications with filtering and pagination.
        
        Args:
            user_id: User UUID
            filter_dto: Filter and pagination parameters
            
        Returns:
            Dictionary with notifications and pagination info
        """
        # Build query
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        # Apply filters
        if filter_dto.type:
            stmt = stmt.where(Notification.type == filter_dto.type)
        
        if filter_dto.is_read is not None:
            stmt = stmt.where(Notification.is_read == filter_dto.is_read)
        
        if filter_dto.device_id:
            stmt = stmt.where(Notification.device_id == filter_dto.device_id)
        
        # Get total count
        count_stmt = select(func.count()).select_from(stmt.subquery())
        result = await self.session.execute(count_stmt)
        total = result.scalar() or 0
        
        # Apply ordering and pagination
        stmt = stmt.order_by(Notification.created_at.desc())
        stmt = stmt.limit(filter_dto.limit).offset(filter_dto.offset)
        
        # Execute query
        result = await self.session.execute(stmt)
        notifications = result.scalars().all()
        
        return {
            "total": total,
            "limit": filter_dto.limit,
            "offset": filter_dto.offset,
            "notifications": self.mapper.to_dto_list(notifications)
        }
    
    async def get_notification(
        self,
        user_id: str,
        notification_id: str
    ) -> NotificationResponseDTO:
        """
        Get a specific notification.
        
        Args:
            user_id: User UUID
            notification_id: Notification UUID
            
        Returns:
            Notification DTO
            
        Raises:
            NotFoundError: If notification not found
            ForbiddenError: If user doesn't own the notification
        """
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        
        if notification.user_id != user_id:
            raise ForbiddenError("You do not have access to this notification")
        
        return self.mapper.to_dto(notification)
    
    async def mark_as_read(
        self,
        user_id: str,
        notification_id: str
    ) -> NotificationResponseDTO:
        """
        Mark a notification as read.
        
        Args:
            user_id: User UUID
            notification_id: Notification UUID
            
        Returns:
            Updated notification DTO
            
        Raises:
            NotFoundError: If notification not found
            ForbiddenError: If user doesn't own the notification
        """
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        
        if notification.user_id != user_id:
            raise ForbiddenError("You do not have access to this notification")
        
        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.notification_repo.save(notification)
            await self.session.commit()
        
        return self.mapper.to_dto(notification)
    
    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all user notifications as read.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of notifications marked as read
        """
        count = await self.notification_repo.mark_all_as_read(user_id)
        await self.session.commit()
        return count
    
    async def bulk_mark_as_read(
        self,
        user_id: str,
        notification_ids: List[str]
    ) -> int:
        """
        Mark multiple notifications as read.
        
        Args:
            user_id: User UUID
            notification_ids: List of notification UUIDs
            
        Returns:
            Number of notifications marked as read
        """
        count = 0
        now = datetime.utcnow()
        
        for notification_id in notification_ids:
            notification = await self.notification_repo.get_by_id(notification_id)
            if notification and notification.user_id == user_id and not notification.is_read:
                notification.is_read = True
                notification.read_at = now
                count += 1
        
        if count > 0:
            await self.session.commit()
        
        return count
    
    async def delete_notification(
        self,
        user_id: str,
        notification_id: str
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            user_id: User UUID
            notification_id: Notification UUID
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If notification not found
            ForbiddenError: If user doesn't own the notification
        """
        notification = await self.notification_repo.get_by_id(notification_id)
        
        if not notification:
            raise NotFoundError(f"Notification {notification_id} not found")
        
        if notification.user_id != user_id:
            raise ForbiddenError("You do not have access to this notification")
        
        result = await self.notification_repo.delete(notification_id)
        await self.session.commit()
        return result
    
    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications.
        
        Args:
            user_id: User UUID
            
        Returns:
            Number of unread notifications
        """
        return await self.notification_repo.get_unread_count(user_id)
    
    async def get_notification_stats(self, user_id: str) -> NotificationStatsDTO:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User UUID
            
        Returns:
            Notification statistics DTO
        """
        # Get all counts
        total_stmt = select(func.count(Notification.notification_id)).where(
            Notification.user_id == user_id
        )
        total_result = await self.session.execute(total_stmt)
        total_count = total_result.scalar() or 0
        
        unread_count = await self.get_unread_count(user_id)
        
        # Get counts by type
        reminder_stmt = select(func.count(Notification.notification_id)).where(
            and_(Notification.user_id == user_id, Notification.type == "reminder")
        )
        reminder_result = await self.session.execute(reminder_stmt)
        reminder_count = reminder_result.scalar() or 0
        
        battery_stmt = select(func.count(Notification.notification_id)).where(
            and_(Notification.user_id == user_id, Notification.type == "low_battery")
        )
        battery_result = await self.session.execute(battery_stmt)
        low_battery_count = battery_result.scalar() or 0
        
        supplement_stmt = select(func.count(Notification.notification_id)).where(
            and_(Notification.user_id == user_id, Notification.type == "low_supplement")
        )
        supplement_result = await self.session.execute(supplement_stmt)
        low_supplement_count = supplement_result.scalar() or 0
        
        achievement_stmt = select(func.count(Notification.notification_id)).where(
            and_(Notification.user_id == user_id, Notification.type == "achievement")
        )
        achievement_result = await self.session.execute(achievement_stmt)
        achievement_count = achievement_result.scalar() or 0
        
        return NotificationStatsDTO(
            total_count=total_count,
            unread_count=unread_count,
            reminder_count=reminder_count,
            low_battery_count=low_battery_count,
            low_supplement_count=low_supplement_count,
            achievement_count=achievement_count
        )
    
    async def send_low_battery_alert(self, device_id: str) -> NotificationResponseDTO:
        """
        Send low battery alert notification.
        
        Args:
            device_id: Device UUID
            
        Returns:
            Created notification DTO
            
        Raises:
            NotFoundError: If device not found
        """
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Check if user has this notification enabled
        settings = await self.settings_repo.get_by_user(device.user_id)
        if settings and not settings.low_battery_enabled:
            raise ValidationError("Low battery notifications are disabled")
        
        data = NotificationCreateDTO(
            user_id=device.user_id,
            device_id=device_id,
            type="low_battery",
            title="Low Battery Alert",
            message=f"Device '{device.device_name}' has low battery ({device.battery_level}%)",
            metadata={"battery_level": device.battery_level}
        )
        
        return await self.create_notification(device.user_id, data)
    
    async def send_low_supplement_alert(self, device_id: str) -> NotificationResponseDTO:
        """
        Send low supplement alert notification.
        
        Args:
            device_id: Device UUID
            
        Returns:
            Created notification DTO
            
        Raises:
            NotFoundError: If device not found
        """
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Check if user has this notification enabled
        settings = await self.settings_repo.get_by_user(device.user_id)
        if settings and not settings.low_supplement_enabled:
            raise ValidationError("Low supplement notifications are disabled")
        
        data = NotificationCreateDTO(
            user_id=device.user_id,
            device_id=device_id,
            type="low_supplement",
            title="Low Supplement Alert",
            message=f"Device '{device.device_name}' is running low on supplement ({device.supplement_level}%)",
            metadata={"supplement_level": device.supplement_level}
        )
        
        return await self.create_notification(device.user_id, data)
    
    async def send_reminder_notification(self, user_id: str) -> NotificationResponseDTO:
        """
        Send daily reminder notification.
        
        Args:
            user_id: User UUID
            
        Returns:
            Created notification DTO
        """
        # Check if user has reminders enabled
        settings = await self.settings_repo.get_by_user(user_id)
        if settings and not settings.reminder_enabled:
            raise ValidationError("Reminder notifications are disabled")
        
        data = NotificationCreateDTO(
            user_id=user_id,
            device_id=None,
            type="reminder",
            title="Daily Reminder",
            message="Don't forget to take your Zinzino supplement today!",
            metadata={"reminder_time": settings.reminder_time.isoformat() if settings else None}
        )
        
        return await self.create_notification(user_id, data)
    
    async def send_achievement_notification(
        self,
        user_id: str,
        achievement_type: str,
        metadata: Dict[str, Any]
    ) -> NotificationResponseDTO:
        """
        Send achievement notification.
        
        Args:
            user_id: User UUID
            achievement_type: Type of achievement (e.g., "7_day_streak")
            metadata: Additional achievement data
            
        Returns:
            Created notification DTO
        """
        # Check if user has achievement notifications enabled
        settings = await self.settings_repo.get_by_user(user_id)
        if settings and not settings.achievement_enabled:
            raise ValidationError("Achievement notifications are disabled")
        
        # Generate title and message based on achievement type
        titles = {
            "7_day_streak": "🎉 7 Day Streak!",
            "30_day_streak": "🏆 30 Day Streak!",
            "100_doses": "💯 100 Doses Milestone!",
            "first_dose": "🌟 First Dose Complete!"
        }
        
        messages = {
            "7_day_streak": "Congratulations! You've maintained a 7-day supplement streak!",
            "30_day_streak": "Amazing! You've reached a 30-day supplement streak!",
            "100_doses": "Incredible! You've taken 100 supplement doses!",
            "first_dose": "Great start! You've taken your first supplement dose!"
        }
        
        title = titles.get(achievement_type, "Achievement Unlocked!")
        message = messages.get(achievement_type, "You've unlocked a new achievement!")
        
        data = NotificationCreateDTO(
            user_id=user_id,
            device_id=None,
            type="achievement",
            title=title,
            message=message,
            metadata={"achievement_type": achievement_type, **metadata}
        )
        
        return await self.create_notification(user_id, data)
