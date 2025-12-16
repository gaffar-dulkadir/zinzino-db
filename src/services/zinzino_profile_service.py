"""
Profile service for Zinzino IoT application.

This module provides business logic for user profile management.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.model.zinzino_models import User, UserProfile
from datalayer.model.dto.auth_dto import (
    UserProfileResponseDTO, UserProfileUpdateDTO, PasswordChangeDTO, UserResponseDTO
)
from datalayer.repository.zinzino_user_repository import ZinzinoUserRepository
from datalayer.repository.profile_repository import UserProfileRepository
from datalayer.mapper.auth_mapper import UserMapper
from utils.security import hash_password, verify_password
from utils.exceptions import NotFoundError, InvalidCredentialsError, ValidationError


class ProfileService:
    """Service for handling user profile operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = ZinzinoUserRepository(session)
        self.profile_repo = UserProfileRepository(session)
        self.mapper = UserMapper()
    
    async def get_profile(self, user_id: str) -> UserResponseDTO:
        """
        Get user profile information.
        
        Args:
            user_id: User ID
            
        Returns:
            User response with profile data
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", resource="user")
        
        # Ensure profile is loaded
        if not user.profile:
            # Create default profile if it doesn't exist
            profile = UserProfile(
                user_id=user_id,
                notification_enabled=True,
                theme_preference="dark",
                language="tr",
                timezone="Europe/Istanbul"
            )
            await self.profile_repo.create_profile(profile)
            await self.session.commit()
            user.profile = profile
        
        return self.mapper.to_user_response_dto(user)
    
    async def update_profile(
        self,
        user_id: str,
        data: UserProfileUpdateDTO
    ) -> UserResponseDTO:
        """
        Update user profile information.
        
        Args:
            user_id: User ID
            data: Profile update data
            
        Returns:
            Updated user response
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", resource="user")
        
        # Update user fields
        if data.full_name is not None:
            user.full_name = data.full_name
        if data.phone is not None:
            user.phone = data.phone
        if data.profile_picture is not None:
            user.profile_picture = data.profile_picture
        
        user = await self.user_repo.update_user(user)
        
        # Update profile fields
        profile = await self.profile_repo.get_by_user_id(user_id)
        if profile:
            if data.notification_enabled is not None:
                profile.notification_enabled = data.notification_enabled
            if data.theme_preference is not None:
                profile.theme_preference = data.theme_preference
            if data.language is not None:
                profile.language = data.language
            if data.timezone is not None:
                profile.timezone = data.timezone
            
            await self.profile_repo.update_profile(profile)
        
        await self.session.commit()
        
        # Reload user with profile
        user = await self.user_repo.get_by_id(user_id)
        return self.mapper.to_user_response_dto(user)
    
    async def upload_profile_picture(
        self,
        user_id: str,
        file_url: str
    ) -> str:
        """
        Update user profile picture.
        
        Args:
            user_id: User ID
            file_url: URL of uploaded file
            
        Returns:
            Updated profile picture URL
            
        Raises:
            NotFoundError: If user not found
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", resource="user")
        
        user.profile_picture = file_url
        await self.user_repo.update_user(user)
        await self.session.commit()
        
        return file_url
    
    async def change_password(
        self,
        user_id: str,
        data: PasswordChangeDTO
    ) -> bool:
        """
        Change user password.
        
        Args:
            user_id: User ID
            data: Password change data
            
        Returns:
            True if password was changed
            
        Raises:
            NotFoundError: If user not found
            InvalidCredentialsError: If old password is incorrect
            ValidationError: If user is OAuth user
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", resource="user")
        
        # Check if user is email/password user
        if user.oauth_provider != "email" or not user.password_hash:
            raise ValidationError("Cannot change password for OAuth users")
        
        # Verify old password
        if not verify_password(data.old_password, user.password_hash):
            raise InvalidCredentialsError()
        
        # Update password
        user.password_hash = hash_password(data.new_password)
        await self.user_repo.update_user(user)
        
        # Revoke all refresh tokens for security
        await self.user_repo.revoke_all_user_tokens(user_id)
        
        await self.session.commit()
        return True
    
    async def delete_account(
        self,
        user_id: str,
        password: Optional[str] = None
    ) -> bool:
        """
        Delete user account (soft delete).
        
        Args:
            user_id: User ID
            password: Password for verification (required for email users)
            
        Returns:
            True if account was deleted
            
        Raises:
            NotFoundError: If user not found
            InvalidCredentialsError: If password is incorrect
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User not found", resource="user")
        
        # Verify password for email users
        if user.oauth_provider == "email" and user.password_hash:
            if not password:
                raise ValidationError("Password required for account deletion")
            
            if not verify_password(password, user.password_hash):
                raise InvalidCredentialsError()
        
        # Soft delete (deactivate account)
        await self.user_repo.delete_user(user_id)
        
        # Revoke all tokens
        await self.user_repo.revoke_all_user_tokens(user_id)
        
        await self.session.commit()
        return True
