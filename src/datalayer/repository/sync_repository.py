"""
Sync metadata repository for Zinzino IoT application.

This module provides repository methods for synchronization tracking.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import SyncMetadata
from ._base_repository import AsyncBaseRepository


class SyncMetadataRepository(AsyncBaseRepository[SyncMetadata]):
    """Repository for SyncMetadata model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SyncMetadata)
    
    async def create_sync(self, sync_data: SyncMetadata) -> SyncMetadata:
        """Create a new sync metadata record."""
        return await self.save(sync_data)
    
    async def get_latest_sync(self, user_id: str) -> Optional[SyncMetadata]:
        """Get the most recent sync record for a user."""
        stmt = select(SyncMetadata).where(
            SyncMetadata.user_id == user_id
        ).order_by(desc(SyncMetadata.created_at)).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_user(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> List[SyncMetadata]:
        """Get sync history for a user."""
        stmt = select(SyncMetadata).where(
            SyncMetadata.user_id == user_id
        ).order_by(desc(SyncMetadata.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_sync_status(
        self,
        sync_id: str,
        status: str,
        last_full_sync: Optional[datetime] = None,
        last_delta_sync: Optional[datetime] = None
    ) -> bool:
        """Update sync metadata status."""
        sync = await self.get_by_id(sync_id)
        if sync:
            sync.sync_status = status
            if last_full_sync:
                sync.last_full_sync = last_full_sync
            if last_delta_sync:
                sync.last_delta_sync = last_delta_sync
            await self.save(sync)
            return True
        return False
    
    async def get_failed_syncs(self, user_id: Optional[str] = None) -> List[SyncMetadata]:
        """Get failed sync records."""
        if user_id:
            return await self.find_by(user_id=user_id, sync_status="failed")
        return await self.find_by(sync_status="failed")
