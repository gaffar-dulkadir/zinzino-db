"""
User repository for Zinzino IoT application.

This module provides repository methods for user CRUD operations,
refresh tokens, and password reset tokens.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..model.zinzino_models import User, RefreshToken, PasswordResetToken
from ..model.dto.auth_dto import UserResponseDTO, UserRegisterDTO
from ..mapper.auth_mapper import UserMapper, UserProfileMapper
from ._base_repository import AsyncBaseRepository


class ZinzinoUserRepository(AsyncBaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, User)
        self.mapper = UserMapper()
    
    # ========================================================================
    # User CRUD Operations
    # ========================================================================
    
    async def create_user(self, user_data: User) -> User:
        """Create a new user."""
        return await self.save(user_data)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address."""
        return await self.find_one_by(email=email)
    
    async def get_by_oauth(self, provider: str, provider_id: str) -> Optional[User]:
        """Get user by OAuth provider and provider ID."""
        return await self.find_one_by(
            oauth_provider=provider,
            oauth_provider_id=provider_id
        )
    
    async def update_user(self, user: User) -> User:
        """Update existing user."""
        return await self.save(user)
    
    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login timestamp."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            await self.save(user)
            return True
        return False
    
    async def verify_email(self, user_id: str) -> bool:
        """Mark user's email as verified."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_verified = True
            await self.save(user)
            return True
        return False
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate user account."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = False
            await self.save(user)
            return True
        return False
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate user account."""
        user = await self.get_by_id(user_id)
        if user:
            user.is_active = True
            await self.save(user)
            return True
        return False
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account (soft delete by deactivating)."""
        return await self.deactivate_user(user_id)
    
    async def get_active_users(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[User]:
        """Get all active users."""
        return await self.find_by(is_active=True)
    
    async def search_users(self, query: str, limit: int = 20) -> List[User]:
        """Search users by email or full name."""
        stmt = select(User).where(
            or_(
                User.email.ilike(f"%{query}%"),
                User.full_name.ilike(f"%{query}%")
            )
        ).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    # ========================================================================
    # Refresh Token Operations
    # ========================================================================
    
    async def create_refresh_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> RefreshToken:
        """Create a new refresh token."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.session.add(refresh_token)
        await self.session.flush()
        return refresh_token
    
    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        """Get refresh token by hash."""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def revoke_refresh_token(self, token_hash: str) -> bool:
        """Revoke a refresh token."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        
        if token:
            token.revoked_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False
    
    async def revoke_all_user_tokens(self, user_id: str) -> int:
        """Revoke all refresh tokens for a user."""
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.revoked_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
    
    async def cleanup_expired_tokens(self) -> int:
        """Delete expired refresh tokens (cleanup task)."""
        stmt = select(RefreshToken).where(
            or_(
                RefreshToken.expires_at < datetime.utcnow(),
                RefreshToken.revoked_at.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            await self.session.delete(token)
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
    
    # ========================================================================
    # Password Reset Token Operations
    # ========================================================================
    
    async def create_password_reset_token(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime
    ) -> PasswordResetToken:
        """Create a password reset token."""
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        self.session.add(reset_token)
        await self.session.flush()
        return reset_token
    
    async def get_password_reset_token(self, token_hash: str) -> Optional[PasswordResetToken]:
        """Get valid password reset token by hash."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def use_password_reset_token(self, token_hash: str) -> bool:
        """Mark password reset token as used."""
        stmt = select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        token = result.scalar_one_or_none()
        
        if token:
            token.used_at = datetime.utcnow()
            await self.session.flush()
            return True
        return False
    
    async def invalidate_old_reset_tokens(self, user_id: str) -> int:
        """Invalidate all old password reset tokens for a user."""
        stmt = select(PasswordResetToken).where(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            token.used_at = datetime.utcnow()
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
    
    async def cleanup_expired_reset_tokens(self) -> int:
        """Delete expired password reset tokens (cleanup task)."""
        stmt = select(PasswordResetToken).where(
            or_(
                PasswordResetToken.expires_at < datetime.utcnow(),
                PasswordResetToken.used_at.isnot(None)
            )
        )
        result = await self.session.execute(stmt)
        tokens = result.scalars().all()
        
        count = 0
        for token in tokens:
            await self.session.delete(token)
            count += 1
        
        if count > 0:
            await self.session.flush()
        
        return count
