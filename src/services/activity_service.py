"""
Activity service for Zinzino IoT application.

This module provides business logic for activity log management and statistics.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.model.zinzino_models import ActivityLog
from datalayer.model.dto.device_dto import ActivityLogResponseDTO
from datalayer.repository.device_repository import DeviceRepository
from datalayer.repository.activity_repository import ActivityLogRepository
from datalayer.mapper.device_mapper import ActivityLogMapper
from utils.exceptions import NotFoundError, ForbiddenError, ValidationError


class ActivityService:
    """Service for handling activity log operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.device_repo = DeviceRepository(session)
        self.activity_repo = ActivityLogRepository(session)
        self.mapper = ActivityLogMapper()
    
    async def create_activity_log(
        self,
        device_id: str,
        user_id: str,
        action: str,
        dose_amount: Optional[str] = None,
        triggered_by: str = "automatic",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ActivityLogResponseDTO:
        """
        Create a new activity log entry.
        
        Args:
            device_id: Device UUID
            user_id: User UUID
            action: Action type (e.g., dose_dispensed, device_connected)
            dose_amount: Dose amount if applicable
            triggered_by: Trigger type (automatic, manual, scheduled)
            metadata: Additional metadata
            
        Returns:
            Activity log DTO
            
        Raises:
            NotFoundError: If device not found
            ValidationError: If data is invalid
        """
        # Verify device exists
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        # Validate triggered_by
        valid_triggers = ["automatic", "manual", "scheduled"]
        if triggered_by not in valid_triggers:
            raise ValidationError(f"Invalid trigger type. Must be one of: {', '.join(valid_triggers)}")
        
        # Create activity log
        log = ActivityLog(
            device_id=device_id,
            user_id=user_id,
            action=action,
            dose_amount=dose_amount,
            triggered_by=triggered_by,
            metadata=metadata,
            timestamp=datetime.utcnow()
        )
        
        log = await self.activity_repo.create_log(log)
        
        # If this is a dose dispensation, increment device count
        if action == "dose_dispensed":
            await self.device_repo.increment_dose_count(device_id)
        
        await self.session.commit()
        
        return self.mapper.to_dto(log)
    
    async def get_device_activities(
        self,
        user_id: str,
        device_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get activity logs for a specific device.
        
        Args:
            user_id: User UUID
            device_id: Device UUID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            Dictionary with activity data
            
        Raises:
            NotFoundError: If device not found
            ForbiddenError: If user doesn't own the device
        """
        # Verify device ownership
        device = await self.device_repo.get_by_id(device_id)
        if not device:
            raise NotFoundError(f"Device {device_id} not found")
        
        if device.user_id != user_id:
            raise ForbiddenError("You do not have access to this device")
        
        # Get activities
        activities = await self.activity_repo.get_by_date_range(
            device_id=device_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "device_id": device_id,
            "total_records": len(activities),
            "limit": limit,
            "offset": offset,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "activities": self.mapper.to_dto_list(activities)
        }
    
    async def get_user_activities(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """
        Get all activity logs for a user across all devices.
        
        Args:
            user_id: User UUID
            start_date: Start date for filtering
            end_date: End date for filtering
            limit: Maximum number of records
            offset: Number of records to skip
            
        Returns:
            Dictionary with activity data
        """
        activities = await self.activity_repo.get_by_date_range(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "total_records": len(activities),
            "limit": limit,
            "offset": offset,
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "activities": self.mapper.to_dto_list(activities)
        }
    
    async def get_activity_statistics(
        self,
        user_id: str,
        device_id: Optional[str] = None,
        period: str = "week"
    ) -> Dict[str, Any]:
        """
        Get activity statistics for a user or specific device.
        
        Args:
            user_id: User UUID
            device_id: Optional device UUID
            period: Period for statistics (day, week, month, year)
            
        Returns:
            Dictionary with statistics
            
        Raises:
            ForbiddenError: If user doesn't own the device
            ValidationError: If period is invalid
        """
        # Validate period
        period_days = {
            "day": 1,
            "week": 7,
            "month": 30,
            "year": 365
        }
        
        if period not in period_days:
            raise ValidationError(f"Invalid period. Must be one of: {', '.join(period_days.keys())}")
        
        days = period_days[period]
        
        # If device_id is specified, verify ownership
        if device_id:
            device = await self.device_repo.get_by_id(device_id)
            if not device:
                raise NotFoundError(f"Device {device_id} not found")
            
            if device.user_id != user_id:
                raise ForbiddenError("You do not have access to this device")
        
        # Get statistics from repository
        stats = await self.activity_repo.get_statistics(
            device_id=device_id,
            user_id=user_id if not device_id else None,
            days=days
        )
        
        # Calculate additional metrics
        daily_average = stats["total_doses"] / days if days > 0 else 0
        
        # Get last 7 days trend
        week_start = datetime.utcnow() - timedelta(days=7)
        week_activities = await self.activity_repo.get_by_date_range(
            device_id=device_id,
            user_id=user_id if not device_id else None,
            start_date=week_start,
            action="dose_dispensed"
        )
        weekly_total = len(week_activities)
        
        # Get last 30 days trend
        month_start = datetime.utcnow() - timedelta(days=30)
        month_activities = await self.activity_repo.get_by_date_range(
            device_id=device_id,
            user_id=user_id if not device_id else None,
            start_date=month_start,
            action="dose_dispensed"
        )
        monthly_total = len(month_activities)
        
        return {
            "period": period,
            "period_days": days,
            "total_activities": stats["total_activities"],
            "total_doses": stats["total_doses"],
            "daily_average": round(daily_average, 2),
            "weekly_total": weekly_total,
            "monthly_total": monthly_total,
            "action_breakdown": stats["action_breakdown"],
            "start_date": stats["start_date"],
            "end_date": stats["end_date"]
        }
    
    async def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete activity logs older than specified days.
        
        This is a maintenance task that should be run periodically.
        
        Args:
            days: Number of days to keep logs (default: 90)
            
        Returns:
            Number of logs deleted
        """
        if days < 30:
            raise ValidationError("Cannot delete logs newer than 30 days")
        
        count = await self.activity_repo.cleanup_old_logs(days)
        await self.session.commit()
        
        return count
