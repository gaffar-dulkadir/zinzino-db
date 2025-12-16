"""
Authentication service for Zinzino IoT application.

This module provides business logic for user authentication, registration,
and token management.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from datalayer.model.zinzino_models import User, UserProfile
from datalayer.model.dto.auth_dto import (
    UserRegisterDTO, UserLoginDTO, GoogleAuthDTO, AppleAuthDTO,
    TokenResponseDTO, UserResponseDTO
)
from datalayer.repository.zinzino_user_repository import ZinzinoUserRepository
from datalayer.repository.profile_repository import UserProfileRepository
from utils.security import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    generate_token_hash, create_password_reset_token, decode_token
)
from utils.exceptions import (
    EmailAlreadyExistsError, InvalidCredentialsError, AccountInactiveError,
    NotFoundError, PasswordResetTokenInvalidError, InvalidTokenError
)
from config import Config


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = ZinzinoUserRepository(session)
        self.profile_repo = UserProfileRepository(session)
        self.config = Config()
    
    async def register(self, user_data: UserRegisterDTO) -> TokenResponseDTO:
        """
        Register a new user with email and password.
        
        Args:
            user_data: User registration data
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            EmailAlreadyExistsError: If email is already registered
        """
        # Check if email already exists
        existing_user = await self.user_repo.get_by_email(user_data.email)
        if existing_user:
            raise EmailAlreadyExistsError(user_data.email)
        
        # Create user
        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            full_name=user_data.full_name,
            phone=user_data.phone,
            oauth_provider="email",
            is_verified=False,
            is_active=True
        )
        
        user = await self.user_repo.create_user(user)
        
        # Create user profile
        profile = UserProfile(
            user_id=user.user_id,
            notification_enabled=True,
            theme_preference="dark",
            language=user_data.language or "tr",
            timezone=user_data.timezone or "Europe/Istanbul"
        )
        
        await self.profile_repo.create_profile(profile)
        await self.session.commit()
        
        # Generate tokens
        return await self._generate_token_response(user.user_id)
    
    async def login(self, credentials: UserLoginDTO) -> TokenResponseDTO:
        """
        Authenticate user with email and password.
        
        Args:
            credentials: User login credentials
            
        Returns:
            Token response with access and refresh tokens
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountInactiveError: If account is inactive
        """
        # Get user by email
        user = await self.user_repo.get_by_email(credentials.email)
        
        # Verify user exists and password is correct
        if not user or not user.password_hash:
            raise InvalidCredentialsError()
        
        if not verify_password(credentials.password, user.password_hash):
            raise InvalidCredentialsError()
        
        # Check if account is active
        if not user.is_active:
            raise AccountInactiveError()
        
        # Update last login
        await self.user_repo.update_last_login(user.user_id)
        await self.session.commit()
        
        # Generate tokens
        return await self._generate_token_response(user.user_id)
    
    async def google_auth(self, google_data: GoogleAuthDTO) -> TokenResponseDTO:
        """
        Authenticate or register user with Google OAuth.
        
        Args:
            google_data: Google authentication data
            
        Returns:
            Token response with access and refresh tokens
        """
        # TODO: Verify Google ID token
        # For now, we'll extract email from the token payload
        # In production, use google.oauth2 library to verify
        
        try:
            payload = decode_token(google_data.id_token)
            email = payload.get("email")
            google_id = payload.get("sub")
            
            if not email or not google_id:
                raise InvalidTokenError("Invalid Google token")
            
        except Exception:
            raise InvalidTokenError("Invalid Google token")
        
        # Check if user exists
        user = await self.user_repo.get_by_oauth("google", google_id)
        
        if not user:
            # Check by email
            user = await self.user_repo.get_by_email(email)
            
            if user:
                # Link Google account to existing user
                user.oauth_provider = "google"
                user.oauth_provider_id = google_id
                user = await self.user_repo.update_user(user)
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=google_data.full_name or email.split("@")[0],
                    profile_picture=google_data.profile_picture,
                    oauth_provider="google",
                    oauth_provider_id=google_id,
                    is_verified=True,  # Google emails are verified
                    is_active=True
                )
                user = await self.user_repo.create_user(user)
                
                # Create profile
                profile = UserProfile(
                    user_id=user.user_id,
                    notification_enabled=True,
                    theme_preference="dark",
                    language="tr",
                    timezone="Europe/Istanbul"
                )
                await self.profile_repo.create_profile(profile)
        
        # Update last login
        await self.user_repo.update_last_login(user.user_id)
        await self.session.commit()
        
        return await self._generate_token_response(user.user_id)
    
    async def apple_auth(self, apple_data: AppleAuthDTO) -> TokenResponseDTO:
        """
        Authenticate or register user with Apple OAuth.
        
        Args:
            apple_data: Apple authentication data
            
        Returns:
            Token response with access and refresh tokens
        """
        # TODO: Verify Apple ID token
        # For now, we'll extract data from the token
        # In production, verify using Apple's public keys
        
        try:
            payload = decode_token(apple_data.id_token)
            email = payload.get("email")
            apple_id = payload.get("sub")
            
            if not email or not apple_id:
                raise InvalidTokenError("Invalid Apple token")
            
        except Exception:
            raise InvalidTokenError("Invalid Apple token")
        
        # Check if user exists
        user = await self.user_repo.get_by_oauth("apple", apple_id)
        
        if not user:
            # Check by email
            user = await self.user_repo.get_by_email(email)
            
            if user:
                # Link Apple account to existing user
                user.oauth_provider = "apple"
                user.oauth_provider_id = apple_id
                user = await self.user_repo.update_user(user)
            else:
                # Create new user
                user = User(
                    email=email,
                    full_name=apple_data.full_name or email.split("@")[0],
                    oauth_provider="apple",
                    oauth_provider_id=apple_id,
                    is_verified=True,  # Apple emails are verified
                    is_active=True
                )
                user = await self.user_repo.create_user(user)
                
                # Create profile
                profile = UserProfile(
                    user_id=user.user_id,
                    notification_enabled=True,
                    theme_preference="dark",
                    language="tr",
                    timezone="Europe/Istanbul"
                )
                await self.profile_repo.create_profile(profile)
        
        # Update last login
        await self.user_repo.update_last_login(user.user_id)
        await self.session.commit()
        
        return await self._generate_token_response(user.user_id)
    
    async def refresh_token(self, refresh_token: str) -> TokenResponseDTO:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: JWT refresh token
            
        Returns:
            New token response
            
        Raises:
            InvalidTokenError: If token is invalid
        """
        try:
            payload = decode_token(refresh_token)
            
            if payload.get("type") != "refresh":
                raise InvalidTokenError("Invalid token type")
            
            user_id = payload.get("sub")
            if not user_id:
                raise InvalidTokenError("Token missing user identifier")
            
        except Exception as e:
            raise InvalidTokenError(str(e))
        
        # Verify refresh token in database
        token_hash = generate_token_hash(refresh_token)
        db_token = await self.user_repo.get_refresh_token(token_hash)
        
        if not db_token:
            raise InvalidTokenError("Token not found or revoked")
        
        # Verify user exists and is active
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")
        
        # Generate new tokens
        return await self._generate_token_response(user_id)
    
    async def forgot_password(self, email: str) -> bool:
        """
        Initiate password reset process.
        
        Args:
            email: User email address
            
        Returns:
            True if email was sent (always returns True for security)
        """
        user = await self.user_repo.get_by_email(email)
        
        if user and user.oauth_provider == "email":
            # Invalidate old tokens
            await self.user_repo.invalidate_old_reset_tokens(user.user_id)
            
            # Generate reset token
            token = create_password_reset_token(user.user_id)
            token_hash = generate_token_hash(token)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Save token
            await self.user_repo.create_password_reset_token(
                user.user_id, token_hash, expires_at
            )
            await self.session.commit()
            
            # TODO: Send email with reset link
            # send_password_reset_email(user.email, token)
        
        # Always return True for security (don't reveal if email exists)
        return True
    
    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            True if password was reset
            
        Raises:
            PasswordResetTokenInvalidError: If token is invalid or expired
        """
        token_hash = generate_token_hash(token)
        db_token = await self.user_repo.get_password_reset_token(token_hash)
        
        if not db_token:
            raise PasswordResetTokenInvalidError()
        
        # Get user
        user = await self.user_repo.get_by_id(db_token.user_id)
        if not user:
            raise PasswordResetTokenInvalidError()
        
        # Update password
        user.password_hash = hash_password(new_password)
        await self.user_repo.update_user(user)
        
        # Mark token as used
        await self.user_repo.use_password_reset_token(token_hash)
        
        # Revoke all refresh tokens
        await self.user_repo.revoke_all_user_tokens(user.user_id)
        
        await self.session.commit()
        return True
    
    async def verify_email(self, token: str) -> bool:
        """
        Verify user email address.
        
        Args:
            token: Email verification token
            
        Returns:
            True if email was verified
        """
        try:
            payload = decode_token(token)
            
            if payload.get("type") != "email_verification":
                return False
            
            user_id = payload.get("user_id")
            if not user_id:
                return False
            
            # Verify user email
            result = await self.user_repo.verify_email(user_id)
            await self.session.commit()
            return result
            
        except Exception:
            return False
    
    async def logout(self, user_id: str) -> bool:
        """
        Logout user by revoking all refresh tokens.
        
        Args:
            user_id: User ID
            
        Returns:
            True if logout was successful
        """
        await self.user_repo.revoke_all_user_tokens(user_id)
        await self.session.commit()
        return True
    
    async def _generate_token_response(self, user_id: str) -> TokenResponseDTO:
        """Generate access and refresh tokens for a user."""
        # Create access token
        access_token_data = {"sub": user_id}
        access_token = create_access_token(access_token_data)
        
        # Create refresh token
        refresh_token_data = {"sub": user_id}
        refresh_token = create_refresh_token(refresh_token_data)
        
        # Store refresh token hash
        token_hash = generate_token_hash(refresh_token)
        expires_at = datetime.utcnow() + timedelta(days=self.config.jwt_refresh_token_expire_days)
        await self.user_repo.create_refresh_token(user_id, token_hash, expires_at)
        
        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.config.jwt_access_token_expire_minutes * 60
        )
