"""
Device state repository for Zinzino IoT application.

This module provides repository methods for device state tracking.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import DeviceState
from ._base_repository import AsyncBaseRepository


class DeviceStateRepository(AsyncBaseRepository[DeviceState]):
    """Repository for DeviceState model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DeviceState)
    
    async def create_state(self, state_data: DeviceState) -> DeviceState:
        """Create a new device state record."""
        return await self.save(state_data)
    
    async def get_latest_state(self, device_id: str) -> Optional[DeviceState]:
        """Get the most recent state for a device."""
        stmt = select(DeviceState).where(
            DeviceState.device_id == device_id
        ).order_by(desc(DeviceState.timestamp)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_states_by_device(
        self,
        device_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[DeviceState]:
        """Get device states ordered by timestamp (newest first)."""
        stmt = select(DeviceState).where(
            DeviceState.device_id == device_id
        ).order_by(desc(DeviceState.timestamp)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_state_history(
        self,
        device_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[DeviceState]:
        """Get device state history within a date range."""
        stmt = select(DeviceState).where(DeviceState.device_id == device_id)
        
        if start_date:
            stmt = stmt.where(DeviceState.timestamp >= start_date)
        if end_date:
            stmt = stmt.where(DeviceState.timestamp <= end_date)
        
        stmt = stmt.order_by(desc(DeviceState.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_cup_placed_states(
        self,
        device_id: str,
        limit: int = 50
    ) -> List[DeviceState]:
        """Get states where cup was placed."""
        stmt = select(DeviceState).where(
            and_(
                DeviceState.device_id == device_id,
                DeviceState.cup_placed == True
            )
        ).order_by(desc(DeviceState.timestamp)).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def cleanup_old_states(self, days: int = 90) -> int:
        """Delete device states older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        stmt = select(DeviceState).where(DeviceState.timestamp < cutoff_date)
        result = await self.session.execute(stmt)
        states = result.scalars().all()
        
        count = 0
        for state in states:
            await self.session.delete(state)
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
