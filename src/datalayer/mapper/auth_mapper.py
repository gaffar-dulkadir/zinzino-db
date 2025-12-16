"""
Mappers for Auth entities (User, UserProfile) to DTOs.

This module provides conversion functions between SQLAlchemy models
and Pydantic DTOs for authentication-related entities.
"""

from typing import Optional, List
from ..model.zinzino_models import User, UserProfile
from ..model.dto.auth_dto import (
    UserResponseDTO,
    UserProfileResponseDTO
)


# ============================================================================
# User Profile Mapper
# ============================================================================

class UserProfileMapper:
    """Mapper for UserProfile model to DTOs."""

    @staticmethod
    def to_dto(profile: Optional[UserProfile]) -> Optional[UserProfileResponseDTO]:
        """
        Convert UserProfile model to UserProfileResponseDTO.

        Args:
            profile: UserProfile SQLAlchemy model instance

        Returns:
            UserProfileResponseDTO or None if profile is None
        """
        if profile is None:
            return None

        return UserProfileResponseDTO(
            user_id=profile.user_id,
            notification_enabled=profile.notification_enabled,
            theme_preference=profile.theme_preference,
            language=profile.language,
            timezone=profile.timezone,
            updated_at=profile.updated_at
        )

    @staticmethod
    def to_dto_list(profiles: List[UserProfile]) -> List[UserProfileResponseDTO]:
        """
        Convert list of UserProfile models to list of DTOs.

        Args:
            profiles: List of UserProfile models

        Returns:
            List of UserProfileResponseDTO
        """
        return [
            UserProfileMapper.to_dto(profile)
            for profile in profiles
            if profile is not None
        ]


# ============================================================================
# User Mapper
# ============================================================================

class UserMapper:
    """Mapper for User model to DTOs."""

    @staticmethod
    def to_dto(
        user: Optional[User],
        include_profile: bool = True
    ) -> Optional[UserResponseDTO]:
        """
        Convert User model to UserResponseDTO.

        Args:
            user: User SQLAlchemy model instance
            include_profile: Whether to include user profile in response

        Returns:
            UserResponseDTO or None if user is None
        """
        if user is None:
            return None

        # Convert profile if requested and available
        profile_dto = None
        if include_profile and hasattr(user, 'profile') and user.profile is not None:
            profile_dto = UserProfileMapper.to_dto(user.profile)

        return UserResponseDTO(
            user_id=user.user_id,
            email=user.email,
            full_name=user.full_name,
            phone=user.phone,
            profile_picture=user.profile_picture,
            is_verified=user.is_verified,
            is_active=user.is_active,
            oauth_provider=user.oauth_provider,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
            profile=profile_dto
        )

    @staticmethod
    def to_dto_list(
        users: List[User],
        include_profile: bool = True
    ) -> List[UserResponseDTO]:
        """
        Convert list of User models to list of DTOs.

        Args:
            users: List of User models
            include_profile: Whether to include user profiles in response

        Returns:
            List of UserResponseDTO
        """
        return [
            UserMapper.to_dto(user, include_profile=include_profile)
            for user in users
            if user is not None
        ]

    @staticmethod
    def to_dto_without_profile(user: Optional[User]) -> Optional[UserResponseDTO]:
        """
        Convert User model to UserResponseDTO without profile.

        Args:
            user: User SQLAlchemy model instance

        Returns:
            UserResponseDTO or None if user is None
        """
        return UserMapper.to_dto(user, include_profile=False)
