"""
Background task helpers for Zinzino IoT application.

This module provides utility functions for background tasks such as
scheduled notifications, cleanup operations, and periodic alerts.

Note: This module provides helper functions but does not implement
actual scheduling (APScheduler or similar would be needed for production).
"""

from typing import List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from datalayer.model.zinzino_models import (
    Device, Notification, NotificationSettings
)
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.notification_repository import NotificationRepository
from datalayer.repository.notification_settings_repository import NotificationSettingsRepository


# Battery and supplement thresholds
LOW_BATTERY_THRESHOLD = 20
LOW_SUPPLEMENT_THRESHOLD = 20


async def schedule_daily_reminders(session: AsyncSession) -> int:
    """
    Send daily supplement reminders to users who have them enabled.
    
    This function should be scheduled to run daily at appropriate times
    based on each user's reminder_time setting.
    
    Args:
        session: Database session
        
    Returns:
        Number of reminders sent
    """
    from services.notification_service import NotificationService
    
    settings_repo = NotificationSettingsRepository(session)
    notification_service = NotificationService(session)
    
    # Get all users with reminders enabled
    all_settings = await settings_repo.find_by(reminder_enabled=True)
    
    count = 0
    current_time = datetime.utcnow().time()
    
    for settings in all_settings:
        # Check if it's time to send reminder (within 1 hour window)
        reminder_time = settings.reminder_time
        time_diff = abs(
            (current_time.hour * 60 + current_time.minute) - 
            (reminder_time.hour * 60 + reminder_time.minute)
        )
        
        if time_diff <= 60:  # Within 1 hour
            try:
                await notification_service.send_reminder_notification(settings.user_id)
                count += 1
            except Exception:
                # Skip on error
                continue
    
    await session.commit()
    return count


async def cleanup_old_notifications(session: AsyncSession, days: int = 30) -> int:
    """
    Remove old read notifications to keep database clean.
    
    Args:
        session: Database session
        days: Number of days to keep (default: 30)
        
    Returns:
        Number of notifications deleted
    """
    notification_repo = NotificationRepository(session)
    
    # Get all read notifications older than specified days
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    stmt = select(Notification).where(
        and_(
            Notification.is_read == True,
            Notification.read_at < cutoff_date
        )
    )
    result = await session.execute(stmt)
    old_notifications = result.scalars().all()
    
    count = 0
    for notification in old_notifications:
        await notification_repo.delete(notification.notification_id)
        count += 1
    
    if count > 0:
        await session.commit()
    
    return count


async def check_battery_alerts(session: AsyncSession) -> int:
    """
    Check all devices for low battery and send alerts.
    
    Args:
        session: Database session
        
    Returns:
        Number of alerts sent
    """
    from services.notification_service import NotificationService
    
    device_repo = DeviceRepository(session)
    notification_service = NotificationService(session)
    
    # Get all active devices with low battery
    stmt = select(Device).where(
        and_(
            Device.is_active == True,
            Device.battery_level <= LOW_BATTERY_THRESHOLD
        )
    )
    result = await session.execute(stmt)
    low_battery_devices = result.scalars().all()
    
    count = 0
    for device in low_battery_devices:
        # Check if we already sent a recent alert (within last 24 hours)
        recent_alerts = await session.execute(
            select(Notification).where(
                and_(
                    Notification.device_id == device.device_id,
                    Notification.type == "low_battery",
                    Notification.created_at > datetime.utcnow() - timedelta(hours=24)
                )
            )
        )
        
        if recent_alerts.scalar_one_or_none():
            continue  # Already sent alert recently
        
        try:
            await notification_service.send_low_battery_alert(device.device_id)
            count += 1
        except Exception:
            # Skip on error (e.g., notifications disabled)
            continue
    
    await session.commit()
    return count


async def check_supplement_alerts(session: AsyncSession) -> int:
    """
    Check all devices for low supplement levels and send alerts.
    
    Args:
        session: Database session
        
    Returns:
        Number of alerts sent
    """
    from services.notification_service import NotificationService
    
    device_repo = DeviceRepository(session)
    notification_service = NotificationService(session)
    
    # Get all active devices with low supplement
    stmt = select(Device).where(
        and_(
            Device.is_active == True,
            Device.supplement_level <= LOW_SUPPLEMENT_THRESHOLD
        )
    )
    result = await session.execute(stmt)
    low_supplement_devices = result.scalars().all()
    
    count = 0
    for device in low_supplement_devices:
        # Check if we already sent a recent alert (within last 24 hours)
        recent_alerts = await session.execute(
            select(Notification).where(
                and_(
                    Notification.device_id == device.device_id,
                    Notification.type == "low_supplement",
                    Notification.created_at > datetime.utcnow() - timedelta(hours=24)
                )
            )
        )
        
        if recent_alerts.scalar_one_or_none():
            continue  # Already sent alert recently
        
        try:
            await notification_service.send_low_supplement_alert(device.device_id)
            count += 1
        except Exception:
            # Skip on error (e.g., notifications disabled)
            continue
    
    await session.commit()
    return count


async def check_achievement_milestones(session: AsyncSession, user_id: str) -> List[str]:
    """
    Check if user has reached any achievement milestones.
    
    This should be called after dose dispensing or other significant events.
    
    Args:
        session: Database session
        user_id: User UUID
        
    Returns:
        List of achieved milestone types
    """
    from datalayer.repository.activity_repository import ActivityLogRepository
    from services.notification_service import NotificationService
    
    activity_repo = ActivityLogRepository(session)
    notification_service = NotificationService(session)
    achievements = []
    
    # Get user's devices
    device_repo = DeviceRepository(session)
    devices = await device_repo.get_all_by_user(user_id, include_inactive=False)
    
    if not devices:
        return achievements
    
    # Calculate total doses
    total_doses = sum(d.total_doses_dispensed for d in devices)
    
    # Check dose milestones
    if total_doses == 1:
        achievements.append("first_dose")
        try:
            await notification_service.send_achievement_notification(
                user_id=user_id,
                achievement_type="first_dose",
                metadata={"total_doses": total_doses}
            )
        except Exception:
            pass
    elif total_doses == 100:
        achievements.append("100_doses")
        try:
            await notification_service.send_achievement_notification(
                user_id=user_id,
                achievement_type="100_doses",
                metadata={"total_doses": total_doses}
            )
        except Exception:
            pass
    
    # Check streak milestones (simplified - real implementation would track consecutive days)
    # For now, check if user has activity in last 7 or 30 days
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    for device in devices:
        logs_7_days = await activity_repo.get_by_date_range(
            device_id=device.device_id,
            start_date=seven_days_ago,
            limit=1000
        )
        
        # Check if there's at least one activity per day in last 7 days
        if len(logs_7_days) >= 7:
            if "7_day_streak" not in achievements:
                achievements.append("7_day_streak")
                try:
                    await notification_service.send_achievement_notification(
                        user_id=user_id,
                        achievement_type="7_day_streak",
                        metadata={"streak_days": 7}
                    )
                except Exception:
                    pass
        
        logs_30_days = await activity_repo.get_by_date_range(
            device_id=device.device_id,
            start_date=thirty_days_ago,
            limit=1000
        )
        
        # Check if there's at least one activity per day in last 30 days
        if len(logs_30_days) >= 30:
            if "30_day_streak" not in achievements:
                achievements.append("30_day_streak")
                try:
                    await notification_service.send_achievement_notification(
                        user_id=user_id,
                        achievement_type="30_day_streak",
                        metadata={"streak_days": 30}
                    )
                except Exception:
                    pass
    
    await session.commit()
    return achievements
