"""
User profile repository for Zinzino IoT application.

This module provides repository methods for user profile operations.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import UserProfile
from ._base_repository import AsyncBaseRepository


class UserProfileRepository(AsyncBaseRepository[UserProfile]):
    """Repository for UserProfile model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserProfile)
    
    async def create_profile(self, profile_data: UserProfile) -> UserProfile:
        """Create a new user profile."""
        return await self.save(profile_data)
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """Get profile by user ID."""
        return await self.get_by_id(user_id)
    
    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """Update existing profile."""
        return await self.save(profile)
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile."""
        return await self.delete_by_id(user_id)
