"""
Activity log repository for Zinzino IoT application.

This module provides repository methods for device activity logging.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import ActivityLog
from ._base_repository import AsyncBaseRepository


class ActivityLogRepository(AsyncBaseRepository[ActivityLog]):
    """Repository for ActivityLog model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ActivityLog)
    
    async def create_log(self, log_data: ActivityLog) -> ActivityLog:
        """Create a new activity log entry."""
        return await self.save(log_data)
    
    async def get_by_device(
        self,
        device_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activity logs for a specific device."""
        stmt = select(ActivityLog).where(
            ActivityLog.device_id == device_id
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ActivityLog]:
        """Get activity logs for a specific user."""
        stmt = select(ActivityLog).where(
            ActivityLog.user_id == user_id
        ).order_by(desc(ActivityLog.timestamp)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_by_date_range(
        self,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        action: Optional[str] = None,
        limit: int = 100
    ) -> List[ActivityLog]:
        """Get activity logs within a date range with optional filters."""
        stmt = select(ActivityLog)
        
        conditions = []
        if device_id:
            conditions.append(ActivityLog.device_id == device_id)
        if user_id:
            conditions.append(ActivityLog.user_id == user_id)
        if start_date:
            conditions.append(ActivityLog.timestamp >= start_date)
        if end_date:
            conditions.append(ActivityLog.timestamp <= end_date)
        if action:
            conditions.append(ActivityLog.action == action)
        
        if conditions:
            stmt = stmt.where(and_(*conditions))
        
        stmt = stmt.order_by(desc(ActivityLog.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_statistics(
        self,
        device_id: Optional[str] = None,
        user_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get activity statistics for a device or user."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = select(ActivityLog).where(ActivityLog.timestamp >= start_date)
        
        if device_id:
            stmt = stmt.where(ActivityLog.device_id == device_id)
        if user_id:
            stmt = stmt.where(ActivityLog.user_id == user_id)
        
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        # Calculate statistics
        total_activities = len(logs)
        dose_count = sum(1 for log in logs if log.action == "dose_dispensed")
        
        action_counts = {}
        for log in logs:
            action_counts[log.action] = action_counts.get(log.action, 0) + 1
        
        return {
            "total_activities": total_activities,
            "total_doses": dose_count,
            "action_breakdown": action_counts,
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": datetime.utcnow().isoformat()
        }
    
    async def get_recent_doses(
        self,
        device_id: str,
        limit: int = 10
    ) -> List[ActivityLog]:
        """Get recent dose dispensed activities for a device."""
        stmt = select(ActivityLog).where(
            and_(
                ActivityLog.device_id == device_id,
                ActivityLog.action == "dose_dispensed"
            )
        ).order_by(desc(ActivityLog.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_user_dose_count(
        self,
        user_id: str,
        start_date: Optional[datetime] = None
    ) -> int:
        """Get total dose count for a user."""
        stmt = select(func.count(ActivityLog.log_id)).where(
            and_(
                ActivityLog.user_id == user_id,
                ActivityLog.action == "dose_dispensed"
            )
        )
        
        if start_date:
            stmt = stmt.where(ActivityLog.timestamp >= start_date)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def cleanup_old_logs(self, days: int = 180) -> int:
        """Delete activity logs older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(ActivityLog).where(ActivityLog.timestamp < cutoff_date)
        result = await self.session.execute(stmt)
        logs = result.scalars().all()
        
        count = 0
        for log in logs:
            await self.session.delete(log)
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
